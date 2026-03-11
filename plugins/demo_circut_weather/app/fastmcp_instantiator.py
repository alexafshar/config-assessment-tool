from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server for tools (SSE)
mcp_application = FastMCP("server", stateless_http=True)

# Import tool modules so their @mcp_application.tool() decorators execute
# and register tools with the FastMCP instance. Add additional tool modules
# here as they are created.
try:
	import weather  # noqa: F401  (imported for side effects)
except Exception as _e:  # pragma: no cover - defensive logging hook
	# If this import fails, the server will start but no tools will be registered.
	# You can log or raise here if strict behavior is desired.
	pass