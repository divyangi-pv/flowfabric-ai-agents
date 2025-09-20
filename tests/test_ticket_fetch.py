import os
import pytest
import httpx
from mcp_tools.ticket_fetch_mcp import fetch_tickets, TicketFetchInput

# --------------------------
# Unit test (mocked Jira API)
# --------------------------
@pytest.mark.asyncio
async def test_fetch_tickets(monkeypatch):
    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "issues": [
                    {
                        "key": "SUP-123",
                        "fields": {
                            "summary": "Add support for Jira v15",
                            "status": {"name": "New"},
                            "assignee": None,
                            "created": "2025-09-19T10:30:00.000Z"
                        }
                    }
                ]
            }

    class MockClient:
        async def __aenter__(self): return self
        async def __aexit__(self, exc_type, exc_val, exc_tb): pass
        async def get(self, url, params=None): return MockResponse()

    monkeypatch.setattr("httpx.AsyncClient", lambda *a, **kw: MockClient())

    input_data = TicketFetchInput(type="version_support", status="New", limit=1)
    result = await fetch_tickets(input_data)

    # Check attributes
    assert len(result.tickets) == 1
    assert result.tickets[0].id == "SUP-123"

    # ✅ Optional: Pydantic v2 serialization check
    ticket_dict = result.tickets[0].model_dump()
    assert ticket_dict["summary"] == "Add support for Jira v15"
    assert ticket_dict["status"] == "New"
    assert ticket_dict["assignee"] is None


# --------------------------
# Live Jira connection test
# --------------------------
@pytest.mark.asyncio
async def test_jira_connection():
    jira_url = os.getenv("JIRA_URL")
    jira_user = os.getenv("JIRA_USER")
    jira_token = os.getenv("JIRA_TOKEN")

    if not all([jira_url, jira_user, jira_token]):
        pytest.skip("Skipping live Jira test (missing env vars)")

    url = f"{jira_url}/rest/api/2/myself"

    async with httpx.AsyncClient(auth=(jira_user, jira_token)) as client:
        resp = await client.get(url)
        if resp.status_code == 401:
            pytest.fail("Jira authentication failed. Check JIRA_USER (email) and JIRA_TOKEN (API token).")
        resp.raise_for_status()
        data = resp.json()
        assert "displayName" in data
