
try:
    import mcp.types
    print("mcp.types found:", dir(mcp.types))

    # Try common types
    if hasattr(mcp.types, 'TextContent'):
        print("TextContent found")
    if hasattr(mcp.types, 'EmbeddedResource'):
        print("EmbeddedResource found")
    if hasattr(mcp.types, 'ImageContent'):
        print("ImageContent found")

except ImportError as e:
    print(f"mcp.types not found: {e}")
    try:
        import mcp
        print("mcp found:", dir(mcp))
    except Exception as e2:
        print(f"mcp library error: {e2}")

