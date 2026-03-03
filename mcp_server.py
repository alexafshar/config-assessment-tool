from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

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
) -> dict:
    initLogging(debug)
    engine = Engine(job_file, thresholds_file, concurrent_connections, username, password, auth_method)
    try:
        await engine.run()
    except SystemExit:
        pass  # Engine calls sys.exit(0) on success, which we want to ignore in server mode
    output_dir = _repo_root() / "output" / job_file

    # Find the generated report
    report_file = next(output_dir.glob("*ConfigurationAnalysisReport.xlsx"), None)
    file_data = None
    file_name = None
    if report_file:
        file_name = report_file.name
        with open(report_file, "rb") as f:
            file_data = base64.b64encode(f.read()).decode("utf-8")

    return {
        "status": "completed",
        "job_file": job_file,
        "thresholds_file": thresholds_file,
        "output_dir": str(output_dir),
        "file_name": file_name,
        "file_content": file_data,
    }


if __name__ == "__main__":
    mcp.run()
