#!/usr/bin/env python3
"""
EC2 Today's Access Report
- Queries CloudTrail for SSH/SSM/Console login events that happened TODAY
- Queries CloudWatch NetworkPacketsIn for significant traffic TODAY
- Shows which EC2 instances were accessed today, by whom, and how
"""

import boto3
import json
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# Start of today (UTC)
NOW      = datetime.now(timezone.utc)
TODAY_START = NOW.replace(hour=0, minute=0, second=0, microsecond=0)

BACKGROUND_PACKETS_PER_DAY = 2_000   # below this = ARP / health-check noise

_SSH_SSM_EVENTS = {
    "SendSSHPublicKey",                    # EC2 Instance Connect
    "StartSession",                        # SSM Session Manager
    "ResumeSession",
    "StartPortForwardingSession",
    "StartPortForwardingSessionToRemoteHost",
}

_CONSOLE_EVENTS = {
    "ConsoleLogin",                        # AWS Console login (not instance-specific)
}


def get_tag(tags, key, default="N/A"):
    if not tags:
        return default
    for t in tags:
        if t.get("Key", "").lower() == key.lower():
            return t.get("Value", default)
    return default


def cloudtrail_today(region: str) -> dict:
    """
    Return { instance_id: [event_record, …] } for SSH/SSM events that happened
    since midnight UTC today in this region.
    """
    ct = boto3.client("cloudtrail", region_name=region)
    accesses: dict[str, list] = {}

    for event_name in _SSH_SSM_EVENTS:
        try:
            paginator = ct.get_paginator("lookup_events")
            pages = paginator.paginate(
                LookupAttributes=[{"AttributeKey": "EventName",
                                   "AttributeValue": event_name}],
                StartTime=TODAY_START,
                EndTime=NOW,
            )
            for page in pages:
                for event in page.get("Events", []):
                    event_time = event.get("EventTime")
                    if not event_time:
                        continue

                    user       = "unknown"
                    source_ip  = "unknown"
                    found_iids: set[str] = set()

                    raw = event.get("CloudTrailEvent", "")
                    if raw:
                        try:
                            payload   = json.loads(raw)
                            source_ip = payload.get("sourceIPAddress", "unknown")
                            identity  = payload.get("userIdentity", {})
                            user = (
                                identity.get("userName")
                                or identity.get("sessionContext", {})
                                          .get("sessionIssuer", {}).get("userName")
                                or identity.get("arn", "unknown").split("/")[-1]
                            )
                            req = payload.get("requestParameters") or {}
                            iid = req.get("instanceId") or req.get("target", "").split("/")[0]
                            if iid and iid.startswith("i-"):
                                found_iids.add(iid)
                        except Exception:
                            pass

                    for res in event.get("Resources", []):
                        if res.get("ResourceType") == "AWS::EC2::Instance":
                            found_iids.add(res["ResourceName"])

                    for iid in found_iids:
                        accesses.setdefault(iid, []).append({
                            "time":      event_time,
                            "event":     event_name,
                            "user":      user,
                            "source_ip": source_ip,
                        })
        except Exception as ex:
            pass   # CloudTrail may not be enabled / accessible

    return accesses


def cw_network_today(cw_client, instance_id: str) -> int | None:
    """
    Return the NetworkPacketsIn count for today (period = since midnight UTC).
    Returns None if no data.
    """
    try:
        resp = cw_client.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="NetworkPacketsIn",
            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
            StartTime=TODAY_START,
            EndTime=NOW,
            Period=int((NOW - TODAY_START).total_seconds()) or 3600,
            Statistics=["Sum"],
        )
        dps = resp.get("Datapoints", [])
        if not dps:
            return None
        return int(sum(d["Sum"] for d in dps))
    except Exception:
        return None


def scan_region(region: str) -> list[dict]:
    """Return list of instance access records for today in this region."""
    results = []
    try:
        session = boto3.session.Session(region_name=region)
        ec2 = session.client("ec2")
        cw  = session.client("cloudwatch")

        # ── Fetch CloudTrail events once ──────────────────────────────────────
        ct_accesses = cloudtrail_today(region)

        # ── Describe running + stopped instances ──────────────────────────────
        paginator = ec2.get_paginator("describe_instances")
        all_instances = []
        for page in paginator.paginate(
            Filters=[{"Name": "instance-state-name", "Values": ["running", "stopped"]}]
        ):
            for res in page.get("Reservations", []):
                all_instances.extend(res.get("Instances", []))

        for inst in all_instances:
            iid   = inst["InstanceId"]
            tags  = inst.get("Tags", [])
            name  = get_tag(tags, "Name", iid)
            itype = inst.get("InstanceType", "?")
            state = inst["State"]["Name"]

            owner_keys = ["Owner", "owner", "Contact", "contact",
                          "Email", "email", "CreatedBy", "created-by", "Team", "team"]
            owner = "N/A"
            for k in owner_keys:
                v = get_tag(tags, k)
                if v != "N/A":
                    owner = f"{k}={v}"
                    break

            ct_events = ct_accesses.get(iid, [])

            # Network packets today (only for running instances)
            net_pkts = None
            if state == "running":
                net_pkts = cw_network_today(cw, iid)

            accessed_today = bool(ct_events) or (net_pkts is not None and net_pkts > BACKGROUND_PACKETS_PER_DAY)

            if accessed_today:
                results.append({
                    "region":     region,
                    "id":         iid,
                    "name":       name,
                    "type":       itype,
                    "state":      state,
                    "owner":      owner,
                    "ct_events":  sorted(ct_events, key=lambda e: e["time"]),
                    "net_pkts_today": net_pkts,
                })

    except Exception as ex:
        print(f"  ⚠️  {region}: {ex}")

    return results


def main():
    print(f"\n{'='*80}")
    print(f"  EC2 INSTANCES ACCESSED TODAY  –  {NOW.strftime('%Y-%m-%d')} UTC")
    print(f"  Window: {TODAY_START.strftime('%H:%M')} → {NOW.strftime('%H:%M')} UTC")
    print(f"{'='*80}\n")

    # Discover enabled regions
    try:
        ec2_meta = boto3.client("ec2", region_name="us-east-1")
        regions = [r["RegionName"]
                   for r in ec2_meta.describe_regions(AllRegions=False)["Regions"]]
    except Exception as ex:
        print(f"⚠️  Could not list regions ({ex}); falling back to common regions.")
        regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]

    print(f"Scanning {len(regions)} regions in parallel …\n")

    all_accessed: list[dict] = []
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = {pool.submit(scan_region, r): r for r in regions}
        done = 0
        for future in as_completed(futures):
            done += 1
            r = futures[future]
            hits = future.result()
            all_accessed.extend(hits)
            print(f"  [{done:>2}/{len(regions)}] {r:<22} {len(hits)} instance(s) accessed today")

    print()

    if not all_accessed:
        print("  ✅  No EC2 instances show evidence of human access today.\n")
        return

    print(f"{'─'*80}")
    print(f"  🔔  {len(all_accessed)} INSTANCE(S) ACCESSED TODAY")
    print(f"{'─'*80}\n")

    for rec in sorted(all_accessed, key=lambda x: x["region"]):
        print(f"  {rec['id']}  [{rec['state'].upper()}]  {rec['type']}  |  {rec['region']}")
        print(f"    Name  : {rec['name']}")
        print(f"    Owner : {rec['owner']}")

        if rec["ct_events"]:
            print(f"    CloudTrail SSH/SSM events today:")
            for ev in rec["ct_events"]:
                ts = ev["time"].strftime("%H:%M:%S UTC") if hasattr(ev["time"], "strftime") else str(ev["time"])
                print(f"      • {ts}  {ev['event']}  by {ev['user']}  from {ev['source_ip']}")
        else:
            print(f"    CloudTrail SSH/SSM events today: none recorded")

        if rec["net_pkts_today"] is not None:
            pkts = rec["net_pkts_today"]
            flag = "  ← real traffic" if pkts > BACKGROUND_PACKETS_PER_DAY else "  (background noise)"
            print(f"    NetworkPacketsIn today : {pkts:,}{flag}")

        print()

    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()

