import asyncio
import os
import subprocess
import sys
import json
import uuid
import base64

# Path to the server script
SERVER_SCRIPT = os.path.join(os.path.dirname(__file__), "mcp_server.py")

async def run_client():
    # Start the server process
    process = await asyncio.create_subprocess_exec(
        sys.executable, SERVER_SCRIPT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=sys.stderr
    )

    print(f"Started server with PID {process.pid}")

    async def read_response():
        line = await process.stdout.readline()
        if not line:
            return None
        return json.loads(line.decode())

    async def send_request(method, params=None):
        request_id = str(uuid.uuid4())
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }
        process.stdin.write(json.dumps(request).encode() + b"\n")
        await process.stdin.drain()
        return request_id

    # 1. Initialize
    print("Sending initialize request...")
    req_id = await send_request("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "test-client", "version": "1.0"}
    })

    response = await read_response()
    print(f"Initialize response: {json.dumps(response, indent=2)}")

    # 2. Initialized notification
    process.stdin.write(json.dumps({
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }).encode() + b"\n")
    await process.stdin.drain()

    # 3. List Tools
    print("Listing tools...")
    req_id = await send_request("tools/list")

    response = await read_response()
    print(f"Tools list response: {json.dumps(response, indent=2)}")

    # 4. Call list_jobs tool
    print("Calling list_jobs tool...")
    req_id = await send_request("tools/call", {
        "name": "list_jobs",
        "arguments": {}
    })

    response = await read_response()
    print(f"Call tool response: {json.dumps(response, indent=2)}")

    # 5. Call run_assessment tool
    print("Calling run_assessment tool...")
    req_id = await send_request("tools/call", {
        "name": "run_assessment",
        "arguments": {
            "job_file": "DefaultJob",
            "debug": False
        }
    })

    response = await read_response()
    print(f"Call run_assessment response: {json.dumps(response, indent=2)}")

    # Extract and save the file
    if response and "result" in response and "content" in response["result"]:
        for content_block in response["result"]["content"]:
            if content_block.get("type") == "resource":
                resource = content_block.get("resource", {})
                if "blob" in resource:
                    file_name = resource.get("uri", "report.xlsx").split("/")[-1]
                    file_data = base64.b64decode(resource["blob"])

                    download_dir = os.path.join(os.path.dirname(__file__), "Downloads")
                    os.makedirs(download_dir, exist_ok=True)
                    file_path = os.path.join(download_dir, file_name)

                    with open(file_path, "wb") as f:
                        f.write(file_data)
                    print(f"Saved resource to {file_path}")

    # 6. Call run_assessment with partial name (testing fix)
    print("Calling run_assessment tool with partial name 'appd-cs-global'...")
    req_id = await send_request("tools/call", {
        "name": "run_assessment",
        "arguments": {
            "job_file": "appd-cs-global",
            "debug": False
        }
    })

    response = await read_response()
    print(f"Call run_assessment (partial name) response: {json.dumps(response, indent=2)}")

    if response and "result" in response and "content" in response["result"]:
         for content_block in response["result"]["content"]:
             if content_block.get("type") == "resource":
                 resource = content_block.get("resource", {})
                 # Handle resource saving similarly... (reusing existing logic maybe or just printing confirmation)
                 print(f"Received resource from partial job text: {resource.get('uri')}")

    process.terminate()
    print("Test complete")

if __name__ == "__main__":
    asyncio.run(run_client())
