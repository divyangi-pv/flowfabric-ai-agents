"""
Entry point for running the MCP server.
This file imports all MCP tools and starts the FastMCP server.
"""

from mcp_tools.ticket_fetch_mcp import mcp

if __name__ == "__main__":
    # Start the MCP server on stdio
    mcp.run()
