from dotenv import load_dotenv
from fastmcp import FastMCP
from pydantic import BaseModel

load_dotenv()

mcp = FastMCP("tests-triaging-assistant")
