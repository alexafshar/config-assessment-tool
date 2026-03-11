import asyncio
import sys
import base64
import json
import httpx
import pandas as pd
import io

# Import configuration directly from your file
import properties

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncAzureOpenAI
import mcp.types as types

# Create a mapping of tools available in the server
async def list_tools_schema(session):
    tools_response = await session.list_tools()
    tools_schema = []
    for tool in tools_response.tools:
        tools_schema.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        })
    return tools_schema

# Helper to get the Bearer token using credentials in properties.py
async def get_circuit_token():
    print(f"🔑 Authenticating with {properties.OAUTH_ENDPOINT}...")
    async with httpx.AsyncClient() as client:
        payload = {
            "grant_type": "client_credentials",
            "client_id": properties.CIRCUIT_LLM_API_CLIENT_ID,
            "client_secret": properties.CIRCUIT_LLM_API_CLIENT_SECRET,
        }
        try:
            response = await client.post(properties.OAUTH_ENDPOINT, data=payload)
            response.raise_for_status()
            token = response.json().get("access_token")
            return token
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            sys.exit(1)

async def run_client():
    # 1. Start the local MCP Server (mcp_server.py)
    server_params = StdioServerParameters(
        command="python3",
        args=["mcp_server.py"], # Assumes mcp_server.py is in the current directory
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize connection to MCP server
            await session.initialize()

            # 2. Get Tools from MCP Server
            tools = await list_tools_schema(session)
            print(f"\nConnected to MCP Server. Found tools: {[t['function']['name'] for t in tools]}")

            # 3. Authenticate with CIRCUIT
            token = await get_circuit_token()

            # 4. Configure LLM Client (using properties)
            aclient = AsyncAzureOpenAI(
                azure_endpoint=properties.CIRCUIT_LLM_API_ENDPOINT,
                api_version=properties.CIRCUIT_LLM_API_VERSION,
                api_key=token,
                # Inject Client ID header as required by some internal gateways
                default_headers={"client-id": properties.CIRCUIT_LLM_API_CLIENT_ID}
            )

            messages = [
                {"role": "system", "content": """You are the Network Assessment Assistant.
Your Goal: Run assessments and answer questions based on the generated Excel reports.

CRITICAL INSTRUCTION - READ CAREFULLY:
The output of 'run_assessment' is a text-converted Excel report that appears in history starting with: "[System: Uploaded Excel file content]".
Once this content is in the chat history, YOU HAVE THE DATA.
DO NOT run the 'run_assessment' tool again to answer follow-up questions about the same job.
1. SEARCH HISTORY: Look for "[System: Uploaded Excel file content]".
2. USE CONTEXT: Read that existing text to answer the user.
3. EXCEPTION: Only run the tool if the user asks for a *new* job name or explicitly commands a "re-run" or "update"."""}
            ]

            print("\n💬 Entering chat mode with CIRCUIT. Type 'quit' to exit.")

            while True:
                user_input = input("\nUser: ")
                if user_input.lower() in ["quit", "exit"]:
                    break

                messages.append({"role": "user", "content": user_input})

                # Call LLM
                response = await aclient.chat.completions.create(
                    model=properties.CIRCUIT_LLM_API_MODEL_NAME,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    # Pass the App Key in the user field for tracking/auth requirements
                    user=f'{{"appkey": "{properties.CIRCUIT_LLM_API_APP_KEY}"}}'
                )

                choice = response.choices[0]
                message = choice.message
                messages.append(message)

                # If LLM wants to use a tool
                if message.tool_calls:
                    print(f"🤖  LLM requested tool execution...")

                    for tool_call in message.tool_calls:
                        func_name = tool_call.function.name
                        func_args = json.loads(tool_call.function.arguments)


                        # Execute tool on MCP Server
                        print(f"   > Start Running {func_name} with {func_args}")
                        result = await session.call_tool(func_name, arguments=func_args)
                        print(f"   > Finished Running {func_name}")

                        # Process results
                        tool_output_text = ""
                        for content in result.content:
                            if content.type == "text":
                                tool_output_text += content.text
                            elif content.type == "resource":
                                # Handle embedded Excel file
                                resource = content.resource
                                print(f"   > Received file resource: {resource.mimeType}")
                                if "spreadsheet" in resource.mimeType or "excel" in resource.mimeType:
                                    # Decode and read summary with pandas
                                    try:
                                        file_bytes = base64.b64decode(resource.blob)
                                        # Parse filename from URI or use default
                                        report_filename = str(resource.uri).split("/")[-1] if hasattr(resource, 'uri') and resource.uri else "report.xlsx"

                                        # Save to disk
                                        with open(report_filename, "wb") as f:
                                            f.write(file_bytes)
                                        print(f"   > Saved report to: {report_filename}")

                                        df_dict = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None)
                                        summary = "Excel Report Summary:\n"
                                        for sheet_name, df in df_dict.items():
                                            if not df.empty:
                                                summary += f"\nSheet: {sheet_name}\n"
                                                summary += df.to_markdown(index=False)

                                        tool_output_text += f"\n[System: Uploaded Excel file content]\n{summary}"
                                        tool_output_text += "\n\n[System Message: The data above is the complete report. Use this data to answer all follow-up questions about this job. Do not re-run the tool.]"
                                    except Exception as e:
                                        print(f"   > Error reading excel: {e}")
                                        tool_output_text += f"[System: Error reading excel bytes: {e}]"
                                else:
                                    print(f"   > Binary file received (mime: {resource.mimeType})")
                                    tool_output_text += f"[System: Binary file received: {resource.mimeType}]"

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_output_text or "Tool executed successfully."
                        })

                    # Get final response from LLM after tool outputs
                    final_response = await aclient.chat.completions.create(
                        model=properties.CIRCUIT_LLM_API_MODEL_NAME,
                        messages=messages,
                        user=f'{{"appkey": "{properties.CIRCUIT_LLM_API_APP_KEY}"}}'
                    )
                    final_text = final_response.choices[0].message.content
                    print(f"CIRCUIT: {final_text}")
                    messages.append(final_response.choices[0].message)

                else:
                    print(f"CIRCUIT: {message.content}")

if __name__ == "__main__":
    asyncio.run(run_client())

