import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from llm import get_llm
from langgraph.prebuilt import create_react_agent
#
# Configure the client to connect to your local MCP server
# Ensure the 'url' matches where your MCP server is listening.
mcp_client = MultiServerMCPClient(
    {
        "my_test_mcp_server": {
            "transport": "streamable_http",
            "url": "http://localhost:8006/mcp"
        }
    }
)


async def main():
    try:
        print("Attempting to load tools from http://localhost:8006...")
        # If the client exposes a synchronous property you could alternatively use:
        # mcp_tools = mcp_client.tools
        mcp_tools = await mcp_client.get_tools()

        if mcp_tools:
            print(f"\nSuccessfully discovered {len(mcp_tools)} tool(s):")
            for tool in mcp_tools:
                print(f"- Name: {tool.name}")
                print(f"  Description: {tool.description}")
                print(f"  Args Schema: {tool.args_schema}")
                print("-" * 20)
        else:
            print("\nNo tools discovered from the MCP server. Check your server's tool exposure.")
        llm = get_llm()
        agent = create_react_agent(
            llm,
            mcp_tools
        )

        # Example 1: Weather alerts
        weather_response = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "Weather alerts for CA"}]}
        )
        print(weather_response['messages'][-1].content)

        # Example 2: Today's weather
        weather_response = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "Today's weather in San Jose"}]}
        )
        print(weather_response['messages'][-1].content)

    except Exception as e:
        print(f"\nError connecting to or loading tools from MCP server: {e}")
        print("Please ensure your MCP server is running on http://localhost:8006 and exposing tools correctly.")


if __name__ == "__main__":
    asyncio.run(main())