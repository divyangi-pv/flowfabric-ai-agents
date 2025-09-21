import httpx
import os
from urllib.parse import quote
from dotenv import load_dotenv
from fastmcp import FastMCP
from pydantic import BaseModel

load_dotenv()

mcp = FastMCP("version-support-assistant")


# -----------------------------
# Schemas
# -----------------------------
class TicketFetchInput(BaseModel):
    type: str = "Version Support"   # <-- default set here
    status: str = "To Triage"   # <-- default set here
    limit: int = 100


class TicketOutput(BaseModel):
    id: str
    summary: str
    status: str
    assignee: str | None
    created: str


class TicketFetchOutput(BaseModel):
    tickets: list[TicketOutput]


# -----------------------------
# MCP Tool Implementation
# -----------------------------
@mcp.tool("ticket.fetch")
async def fetch_tickets(input: TicketFetchInput) -> TicketFetchOutput:
    """
    Fetch version support tickets from Jira based on type and status.
    Requires JIRA_URL, JIRA_USER, JIRA_TOKEN in environment.
    """
    JIRA_URL = os.getenv("JIRA_URL")
    JIRA_USER = os.getenv("JIRA_USER")
    JIRA_TOKEN = os.getenv("JIRA_TOKEN")

    if not all([JIRA_URL, JIRA_USER, JIRA_TOKEN]):
        raise RuntimeError("Missing Jira credentials in .env")

    jql = f'project = "CON" AND type = "{input.type}" AND status = "{input.status}" ORDER BY created DESC'
    url = f"{JIRA_URL}/rest/api/3/search/jql"

    async with httpx.AsyncClient(auth=(JIRA_USER, JIRA_TOKEN)) as client:
        resp = await client.get(url, params={
            "jql": jql, 
            "maxResults": input.limit,
            "fields": "key,summary,status,assignee,created"
        })
        resp.raise_for_status()
        data = resp.json()

    tickets = [
        TicketOutput(
            id=issue["key"],
            summary=issue["fields"]["summary"],
            status=issue["fields"]["status"]["name"],
            assignee=(issue["fields"]["assignee"]["displayName"]
                      if issue["fields"].get("assignee") else None),
            created=issue["fields"]["created"]
        )
        for issue in data.get("issues", [])
    ]

    return TicketFetchOutput(tickets=tickets)


# -----------------------------
# Entry Point
# -----------------------------
if __name__ == "__main__":
    mcp.run()
