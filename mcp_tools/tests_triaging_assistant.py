from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("tests-triaging-assistant")

# -----------------------------
# Schemas
# -----------------------------

# -----------------------------
# MCP Tool Implementation
# -----------------------------

# -----------------------------
# Entry Point
# -----------------------------
if __name__ == "__main__":
    mcp.run()
