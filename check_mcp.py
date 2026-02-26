try:
    from mcp.server.fastmcp import FastMCP
    print("FastMCP found")
except ImportError:
    print("FastMCP NOT found")
    try:
        import mcp.server
        print("mcp.server found", dir(mcp.server))
    except ImportError:
        print("mcp.server NOT found")

