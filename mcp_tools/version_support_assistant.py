import httpx
import os
import subprocess
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
    releaseNotes: str | None


class TicketFetchOutput(BaseModel):
    tickets: list[TicketOutput]


class CommentInput(BaseModel):
    ticket_id: str
    comment: str


class CommentOutput(BaseModel):
    success: bool
    comment_id: str | None = None
    error: str | None = None


class StatusUpdateInput(BaseModel):
    ticket_id: str


class StatusUpdateOutput(BaseModel):
    success: bool
    error: str | None = None


class GerritPRInput(BaseModel):
    ticket_id: str
    description: str
    branch: str = "master"
    repo_path: str = "."


class GerritPROutput(BaseModel):
    success: bool
    change_id: str | None = None
    pr_url: str | None = None
    error: str | None = None

# -----------------------------
# Helper Functions
# -----------------------------
def extract_text_from_description(desc):
    """Extract only the release notes URL from Jira description"""
    if not desc:
        return None
    
    def extract_from_content(content_list):
        text_parts = []
        for item in content_list:
            if item.get("type") == "text":
                text_parts.append(item.get("text", ""))
            elif item.get("type") == "paragraph" and "content" in item:
                text_parts.extend(extract_from_content(item["content"]))
        return text_parts
    
    full_text = ""
    if isinstance(desc, dict) and "content" in desc:
        text_parts = extract_from_content(desc["content"])
        full_text = "".join(text_parts).strip()
    elif isinstance(desc, str):
        full_text = desc
    else:
        return None
    
    # Extract URL after "Release Information:"
    if "Release Information:" in full_text:
        parts = full_text.split("Release Information:", 1)
        if len(parts) > 1:
            url_part = parts[1].strip().split()[0]  # Get first word after colon
            return url_part
    
    return None

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
            "fields": "key,summary,status,assignee,created,description"
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
            releaseNotes=extract_text_from_description(issue["fields"].get("description")),
            created=issue["fields"]["created"]
        )
        for issue in data.get("issues", [])
    ]

    return TicketFetchOutput(tickets=tickets)


@mcp.tool("ticket.comment")
async def add_comment(input: CommentInput) -> CommentOutput:
    """
    Add a comment to a Jira ticket.
    Requires JIRA_URL, JIRA_USER, JIRA_TOKEN in environment.
    """
    JIRA_URL = os.getenv("JIRA_URL")
    JIRA_USER = os.getenv("JIRA_USER")
    JIRA_TOKEN = os.getenv("JIRA_TOKEN")

    if not all([JIRA_URL, JIRA_USER, JIRA_TOKEN]):
        return CommentOutput(success=False, error="Missing Jira credentials in .env")

    url = f"{JIRA_URL}/rest/api/3/issue/{input.ticket_id}/comment"
    payload = {"body": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": input.comment}]}]}}

    try:
        async with httpx.AsyncClient(auth=(JIRA_USER, JIRA_TOKEN)) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return CommentOutput(success=True, comment_id=data.get("id"))
    except Exception as e:
        return CommentOutput(success=False, error=str(e))


@mcp.tool("ticket.accepted")
async def accept_ticket(input: StatusUpdateInput) -> StatusUpdateOutput:
    """
    Update Jira ticket status to Accepted.
    Requires JIRA_URL, JIRA_USER, JIRA_TOKEN in environment.
    """
    JIRA_URL = os.getenv("JIRA_URL")
    JIRA_USER = os.getenv("JIRA_USER")
    JIRA_TOKEN = os.getenv("JIRA_TOKEN")

    if not all([JIRA_URL, JIRA_USER, JIRA_TOKEN]):
        return StatusUpdateOutput(success=False, error="Missing Jira credentials in .env")

    url = f"{JIRA_URL}/rest/api/3/issue/{input.ticket_id}/transitions"
    payload = {"transition": {"id": "71"}}

    try:
        async with httpx.AsyncClient(auth=(JIRA_USER, JIRA_TOKEN)) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return StatusUpdateOutput(success=True)
    except Exception as e:
        return StatusUpdateOutput(success=False, error=str(e))


@mcp.tool("gerrit.create_pr")
async def create_gerrit_pr(input: GerritPRInput) -> GerritPROutput:
    """
    Commit changes, push to Gerrit, and create PR.
    Requires git and gerrit setup in the repository.
    """
    try:
        # Add all changes
        subprocess.run(["git", "add", "."], cwd=input.repo_path, check=True)
        
        # Format commit message
        commit_msg = f"{input.ticket_id} : {input.description}\n\nTask-Url: https://tasktop.atlassian.net/browse/{input.ticket_id}"
        
        # Commit with formatted message
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=input.repo_path, check=True)
        
        # Push to Gerrit for review with WIP flag
        result = subprocess.run(
            ["git", "push", "origin", f"HEAD:refs/for/{input.branch}%wip"],
            cwd=input.repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Extract change ID and URL from output
        change_id = None
        pr_url = None
        for line in result.stderr.split("\n"):
            if "remote:" in line and "https://" in line:
                pr_url = line.split("remote:")[1].strip()
            elif "Change-Id:" in line:
                change_id = line.split("Change-Id:")[1].strip()
        
        return GerritPROutput(success=True, change_id=change_id, pr_url=pr_url)
    
    except subprocess.CalledProcessError as e:
        return GerritPROutput(success=False, error=f"Git command failed: {e.stderr}")
    except Exception as e:
        return GerritPROutput(success=False, error=str(e))


# -----------------------------
# Entry Point
# -----------------------------
if __name__ == "__main__":
    mcp.run()
