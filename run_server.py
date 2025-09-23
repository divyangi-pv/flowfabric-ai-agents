"""
Entry point for running the MCP server.
This file imports all MCP tools and starts the FastMCP server.
"""

from mcp_tools.version_support_assistant import mcp as version_support_mcp
from mcp_tools.tests_triaging_assistant import mcp as tests_triaging_mcp
from mcp_tools.release_signoff_assistant import mcp as release_signoff_mcp
from fastmcp import FastMCP

# Create a combined MCP server
combined_mcp = FastMCP("flowfabric-ai-agents")

# Register tools from all MCP instances
for tool_name, tool_func in version_support_mcp._tools.items():
    combined_mcp._tools[tool_name] = tool_func

for tool_name, tool_func in tests_triaging_mcp._tools.items():
    combined_mcp._tools[tool_name] = tool_func

for tool_name, tool_func in release_signoff_mcp._tools.items():
    combined_mcp._tools[tool_name] = tool_func

if __name__ == "__main__":
    # Start the combined MCP server on stdio
    combined_mcp.run()
