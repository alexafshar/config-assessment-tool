from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Optional, Union

import mcp.types as types
from mcp.server.fastmcp import FastMCP

from backend.core.Engine import Engine
from backend.util.logging_utils import initLogging

mcp = FastMCP("config-assessment-tool")


def _repo_root() -> Path:
    return Path(__file__).resolve().parent


def _jobs_dir() -> Path:
    return _repo_root() / "input" / "jobs"


@mcp.tool()
def list_jobs() -> list[str]:
    jobs_dir = _jobs_dir()
    if not jobs_dir.exists():
        return []
    return sorted(job_file.stem for job_file in jobs_dir.glob("*.json"))


@mcp.tool()
async def run_assessment(
    job_file: str = "DefaultJob",
    thresholds_file: str = "DefaultThresholds",
    debug: bool = False,
    concurrent_connections: Optional[int] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    auth_method: Optional[str] = None,
) -> list[Union[types.TextContent, types.EmbeddedResource]]:
    initLogging(debug)

    # Ensure job files exist before initializing Engine to prevent SystemExit crash
    jobs_dir = _jobs_dir()
    target_job_file = jobs_dir / f"{job_file}.json"
    if not target_job_file.exists():
        return [types.TextContent(
            type="text",
            text=f"Error: Job file '{job_file}' not found at {target_job_file}. Please check the job name."
        )]

    engine = Engine(job_file, thresholds_file, concurrent_connections, username, password, auth_method)
    try:
        await engine.run()
    except SystemExit:
        pass  # Engine calls sys.exit(0) on success, which we want to ignore in server mode
    output_dir = _repo_root() / "output" / job_file

    # Find the generated report
    report_file = next(output_dir.glob("*ConfigurationAnalysisReport.xlsx"), None)

    content_list = []

    # Add text summary
    summary = {
        "status": "completed",
        "job_file": job_file,
        "thresholds_file": thresholds_file,
        "output_dir": str(output_dir)
    }
    content_list.append(types.TextContent(
        type="text",
        text=json.dumps(summary, indent=2)
    ))

    # Add file resource if it exists
    if report_file:
        with open(report_file, "rb") as f:
            file_data = base64.b64encode(f.read()).decode("utf-8")

        content_list.append(types.EmbeddedResource(
            type="resource",
            resource=types.BlobResourceContents(
                uri=f"file:///{report_file.name}",
                mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                blob=file_data
            )
        ))

    return content_list


if __name__ == "__main__":
    mcp.run()
