import asyncio
import os
import subprocess
import sys
import json
import uuid

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

    process.terminate()
    print("Test complete")

if __name__ == "__main__":
    asyncio.run(run_client())

