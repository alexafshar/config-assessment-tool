from __future__ import annotations

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
    await engine.run()
    output_dir = _repo_root() / "output" / job_file
    return {
        "status": "completed",
        "job_file": job_file,
        "thresholds_file": thresholds_file,
        "output_dir": str(output_dir),
    }


if __name__ == "__main__":
    mcp.run()

