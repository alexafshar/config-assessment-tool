
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import sys

async def main():
    server_params = StdioServerParameters(
        command="python3",
        args=["mcp_server.py"], # This assumes mcp_server.py is in the CWD
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List jobs to ensure connection
            print("Listing jobs...")
            result = await session.call_tool("list_jobs", arguments={})
            print(f"Jobs content: {result.content}")

            # Use the partial name that the user provided
            job_name = "appd-cs-global"
            print(f"\nRunning assessment for partial job name '{job_name}'...")

            try:
                # The MCP call tool method is expected to return a result object
                # If my fix is correct, this should NOT return "Error: Job file ... not found" immediately
                # It might start the Engine, which could fail or succeed.
                # However, calling Engine takes time.
                # Let's just check if it finds the file by seeing if it passes the initial check.

                # I will pass a fake job name just to see the error message first.
                bad_job = "this-job-does-not-exist"
                print(f"Testing bad job name {bad_job}...")
                bad_result = await session.call_tool("run_assessment", arguments={"job_file": bad_job})
                print(f"Bad job result: {bad_result.content[0].text}")

                # Now the real test.
                # Since Engine execution takes time and might fail, I am mostly interested if it finds the file.
                # But I can't easily mock Engine within this stdio setup without running it.
                # However, if it proceeds to Engine, it will print some logs.
                # Let's run it.

                # Wait, Engine execution is blocking in mcp_server.py currently.
                # await engine.run()

                print(f"Testing partial job name {job_name}...")
                # This might take a while, so I will rely on logs or just trust my code change for now.
                # But let me try anyway to ensure no immediate crash.
                good_result = await session.call_tool("run_assessment", arguments={"job_file": job_name})

                print("Good job result content types:")
                for content in good_result.content:
                    print(f"- {content.type}")
                    if content.type == "text":
                         print(f"  Text: {content.text[:100]}...")

            except Exception as e:
                print(f"Caught exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())

