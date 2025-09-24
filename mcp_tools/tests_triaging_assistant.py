import datetime
import os

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP
from pydantic import BaseModel

load_dotenv()

mcp = FastMCP("tests-triaging-assistant")

# -----------------------------
# Schemas
# -----------------------------

class JenkinsBuildFetchInput(BaseModel):
    job_name: str = "connector-leankit"   # <-- default set here

class JenkinsBuild(BaseModel):
    job: str
    buildNumber: int
    status: str
    url: str

class FailedTest(BaseModel):
    api: str
    error_details: str
    stack_trace: str
    standard_output: str
    frequency_rule: str = "daily"

class TicketFetchInput(BaseModel):
    type: str = "Build Issue"
    component: str = "Planview AgilePlace"
    limit: int = 100

class BuildIssueCreateInput(BaseModel):
    component: str = "Planview AgilePlace"
    label: str = "Denim"
    title: str
    sample_builds: str = ""
    first_seen: str = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000-0700")
    frequency: str = "Occasionally"
    last_seen: str = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000-0700")
    tests_affected: str = ""
    failure_message: str = ""
    stacktrace: str = ""

class BuildIssueUpdateInput(BaseModel):
    issue_id: str
    status: str = None
    last_seen: str = None

# -----------------------------
# MCP Tool Implementation
# -----------------------------
@mcp.tool("fetch_build_with_failures")
def fetch_build_with_failures(input: JenkinsBuildFetchInput) -> dict:
    """
    Fetch the latest Jenkins build and extract failed test details with error_details, stack_trace, and standard_output.
    """
    job_name = input.job_name
    jenkins_user = os.getenv("JENKINS_USER")
    jenkins_token = os.getenv("JENKINS_TOKEN")
    base_url = "https://ci-comp.tasktop.com"

    if not all([jenkins_user, jenkins_token]):
        raise ValueError("JENKINS_USER or JENKINS_TOKEN missing in .env")

    try:
        with httpx.Client(auth=(jenkins_user, jenkins_token)) as client:
            # Get latest build info first
            build_api = f"{base_url}/job/{job_name}/lastBuild/api/json"
            response = client.get(build_api)
            response.raise_for_status()
            build_info = response.json()

            build_number = build_info.get("number")
            status = build_info.get("result")

            if status == "SUCCESS":
                return {
                    "job": job_name,
                    "buildNumber": build_number,
                    "status": status,
                    "failed_tests": [],
                    "message": "Build passed - no failures to report"
                }

            # Get test report using correct format
            test_url = f"{base_url}/job/connector-leankit/4307/testReport/api/json"
            test_response = client.get(test_url)

            if test_response.status_code != 200:
                return {
                    "job": job_name,
                    "buildNumber": build_number,
                    "status": status,
                    "failed_tests": [],
                    "message": "No test report available"
                }

            report = test_response.json()
            failed_tests = []

            for suite in report.get("suites", []):
                for case in suite.get("cases", []):
                    if case.get("status") != "PASSED":
                        error_details = case.get("errorDetails", "")
                        stack_trace = case.get("errorStackTrace", "")

                        # Skip infrastructure failures (no error details or stack trace)
                        if not error_details and not stack_trace:
                            continue

                        failed_tests.append({
                            "api": case.get("className", ""),
                            "error_details": error_details,
                            "stack_trace": stack_trace,
                            "standard_output": case.get("stdout", "")
                        })

            return {
                "job": job_name,
                "buildNumber": build_number,
                "status": status,
                "failed_tests": failed_tests,
                "total_failures": len(failed_tests)
            }

    except httpx.RequestError as e:
        raise RuntimeError(f"Failed to fetch Jenkins data: {e}")

@mcp.tool("build_issues.fetch")
async def fetch_build_issues():
    JIRA_URL = os.getenv("JIRA_URL")
    JIRA_USER = os.getenv("JIRA_USER")
    JIRA_TOKEN = os.getenv("JIRA_TOKEN")

    if not all([JIRA_URL, JIRA_USER, JIRA_TOKEN]):
        raise RuntimeError("Missing Jira credentials in .env")

    jql = f'type = "Build Issue" AND component = "Planview AgilePlace" ORDER BY created DESC'
    url = f"{JIRA_URL}/rest/api/3/search/jql"

    async with httpx.AsyncClient(auth=(JIRA_USER, JIRA_TOKEN)) as client:
        resp = await client.get(url, params={
            "jql": jql,
            "maxResults": 50,
            "fields": "key,summary,status,assignee,created,customfield_17545,customfield_17737,customfield_17736"
        })
        resp.raise_for_status()
        data = resp.json()

    issues = []
    for issue in data.get("issues", []):
        issues.append({
            "key": issue["key"],
            "title": issue["fields"]["summary"],
            "description": issue["fields"].get("customfield_17545"),
            "status": issue["fields"]["status"]["name"],
            "created": issue["fields"]["created"],
            "last_seen": issue["fields"].get("customfield_17737"),
            "frequency": (
                issue["fields"]["customfield_17736"]["value"]
                if issue["fields"].get("customfield_17736") else None
            )
        })

    return issues

@mcp.tool("build_issues.create")
async def create_build_issue(input: BuildIssueCreateInput):
    """
    Create a new Build Issue in Jira with template-based description
    """
    JIRA_URL = os.getenv("JIRA_URL")
    JIRA_USER = os.getenv("JIRA_USER")
    JIRA_TOKEN = os.getenv("JIRA_TOKEN")

    if not all([JIRA_URL, JIRA_USER, JIRA_TOKEN]):
        raise RuntimeError("Missing Jira credentials in .env")

    # Build the description template
    description = {
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "heading", "attrs": {"level": 1}, "content": [{"type": "text", "text": "Summary"}]},
            {
                "type": "bulletList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [
                            {"type": "paragraph", "content": [{"type": "text", "text": "Sample Builds", "marks": [{"type": "strong"}]}]},
                            {"type": "bulletList", "content": [{"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": input.sample_builds}]}]}]}
                        ]
                    },
                    {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "First Seen On", "marks": [{"type": "strong"}]}, {"type": "text", "text": f": {input.first_seen}"}]}]},
                    {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Frequency", "marks": [{"type": "strong"}]}, {"type": "text", "text": f": {input.frequency}"}]}]},
                    {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Last Seen On", "marks": [{"type": "strong"}]}, {"type": "text", "text": f": {input.last_seen}"}]}]}
                ]
            },
            {"type": "heading", "attrs": {"level": 1}, "content": [{"type": "text", "text": "Error Details"}]},
            {"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "Tests Affected"}]},
            {"type": "paragraph", "content": [{"type": "text", "text": input.tests_affected}]},
            {"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "Failure / Message"}]},
            {"type": "paragraph", "content": [{"type": "text", "text": input.failure_message, "marks": [{"type": "code"}]}]},
            {"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "Stacktrace"}]},
            {"type": "codeBlock", "attrs": {"language": "java"}, "content": [{"type": "text", "text": input.stacktrace}]}
        ]
    }

    # Create issue payload
    payload = {
        "fields": {
            "project": {"key": "CON"},
            "summary": input.title,
            "issuetype": {"name": "Build Issue"},
            "components": [{"name": input.component}],
            "labels": [input.label],
            "customfield_17545": description,
            "customfield_17737": input.last_seen,
            "customfield_17736": {"value": input.frequency} if input.frequency else None
        }
    }

    # Remove None values
    payload["fields"] = {k: v for k, v in payload["fields"].items() if v is not None}

    url = f"{JIRA_URL}/rest/api/3/issue"

    async with httpx.AsyncClient(auth=(JIRA_USER, JIRA_TOKEN)) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    return {
        "success": True,
        "issue_key": data["key"],
        "issue_id": data["id"]
    }

@mcp.tool("update_jira_build_issue")
async def update_jira_build_issue(input: BuildIssueUpdateInput):
    """
    Update ticket status and last seen date. Only updates provided fields.
    """
    JIRA_URL = os.getenv("JIRA_URL")
    JIRA_USER = os.getenv("JIRA_USER")
    JIRA_TOKEN = os.getenv("JIRA_TOKEN")

    if not all([JIRA_URL, JIRA_USER, JIRA_TOKEN]):
        raise RuntimeError("Missing Jira credentials in .env")

    async with httpx.AsyncClient(auth=(JIRA_USER, JIRA_TOKEN)) as client:
        # Build payload with only provided fields
        payload = {"fields": {}}

        # Update last seen if provided
        if input.last_seen is not None:
            payload["fields"]["customfield_17737"] = input.last_seen

        # Update fields if any are provided
        if payload["fields"]:
            url = f"{JIRA_URL}/rest/api/3/issue/{input.issue_id}"
            resp = await client.put(url, json=payload)
            resp.raise_for_status()

        # Handle status transition if provided
        status_updated = None
        if input.status is not None:
            try:
                # Get available transitions
                trans_url = f"{JIRA_URL}/rest/api/3/issue/{input.issue_id}/transitions"
                trans_resp = await client.get(trans_url)
                trans_resp.raise_for_status()
                transitions = trans_resp.json()["transitions"]

                # Find matching transition
                transition_id = None
                for trans in transitions:
                    if trans["to"]["name"].lower() == input.status.lower():
                        transition_id = trans["id"]
                        break

                if transition_id:
                    # Execute transition
                    trans_payload = {"transition": {"id": transition_id}}
                    await client.post(trans_url, json=trans_payload)
                    status_updated = input.status
            except:
                pass  # Status transition failed

    return {
        "success": True,
        "issue_id": input.issue_id,
        "last_seen_updated": input.last_seen if input.last_seen is not None else "not updated",
        "status_updated": status_updated if status_updated else "not updated"
    }


# -----------------------------
# Entry Point
# -----------------------------
if __name__ == "__main__":
    mcp.run()
