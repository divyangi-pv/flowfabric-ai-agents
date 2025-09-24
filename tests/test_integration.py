"""
Integration tests for version support assistant.
These tests can optionally run against live Jira connections when credentials are available.
"""
import pytest
import os
import subprocess
from unittest.mock import patch, MagicMock
from mcp_tools.version_support_assistant import (
    fetch_tickets, add_comment, accept_ticket, create_gerrit_pr,
    TicketFetchInput, CommentInput, StatusUpdateInput, GerritPRInput
)


def has_jira_credentials():
    """Check if Jira credentials are available in environment."""
    return all([
        os.getenv("JIRA_URL"),
        os.getenv("JIRA_USER"),
        os.getenv("JIRA_TOKEN")
    ])


@pytest.mark.integration
class TestIntegrationWithMocks:
    """Integration tests using mocked external dependencies."""
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_complete_ticket_workflow_mocked(self, mock_client_class, mock_env_vars):
        """Test complete workflow from fetch to comment to status update."""
        # Setup mock responses for different API calls
        mock_client = mock_client_class.return_value.__aenter__.return_value
        
        # Mock fetch response
        fetch_response = {
            "issues": [{
                "key": "CON-12345",
                "fields": {
                    "summary": "Integration test ticket",
                    "status": {"name": "To Triage"},
                    "assignee": {"displayName": "Test User"},
                    "created": "2024-01-15T10:30:00.000+0000",
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Release Information: https://test.com/release"}]
                        }]
                    }
                }
            }]
        }
        
        # Mock comment response
        comment_response = {"id": "10001"}
        
        # Configure mock client to return different responses based on HTTP method
        def mock_request(*args, **kwargs):
            mock_response = type('MockResponse', (), {})()
            if args[0] == 'get' or (hasattr(args[0], 'method') and args[0].method == 'GET'):
                mock_response.json = lambda: fetch_response
            else:  # POST requests
                mock_response.json = lambda: comment_response
            mock_response.raise_for_status = lambda: None
            return mock_response
        
        mock_client.get.side_effect = lambda *args, **kwargs: mock_request('get', *args, **kwargs)
        mock_client.post.side_effect = lambda *args, **kwargs: mock_request('post', *args, **kwargs)
        
        # Step 1: Fetch tickets
        fetch_input = TicketFetchInput(limit=1)
        fetch_result = await fetch_tickets(fetch_input)
        
        assert len(fetch_result.tickets) == 1
        ticket = fetch_result.tickets[0]
        assert ticket.id == "CON-12345"
        assert ticket.releaseNotes == "https://test.com/release"
        
        # Step 2: Add comment
        comment_input = CommentInput(ticket_id=ticket.id, comment="Processing this ticket")
        comment_result = await add_comment(comment_input)
        
        assert comment_result.success is True
        assert comment_result.comment_id == "10001"
        
        # Step 3: Update status
        status_input = StatusUpdateInput(ticket_id=ticket.id)
        status_result = await accept_ticket(status_input)
        
        assert status_result.success is True
        
        # Verify all API calls were made
        assert mock_client.get.called
        assert mock_client.post.call_count == 2  # comment + status update
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    @patch('httpx.AsyncClient')
    async def test_ticket_to_gerrit_workflow_mocked(self, mock_client_class, mock_subprocess, mock_env_vars):
        """Test workflow from ticket fetch to Gerrit PR creation."""
        # Setup HTTP mock
        mock_client = mock_client_class.return_value.__aenter__.return_value
        fetch_response = {
            "issues": [{
                "key": "CON-12345",
                "fields": {
                    "summary": "Fix critical bug",
                    "status": {"name": "To Triage"},
                    "assignee": None,
                    "created": "2024-01-15T10:30:00.000+0000",
                    "description": None
                }
            }]
        }
        
        mock_response = type('MockResponse', (), {})()
        mock_response.json = lambda: fetch_response
        mock_response.raise_for_status = lambda: None
        mock_client.get.return_value = mock_response
        
        # Setup subprocess mock
        mock_subprocess.side_effect = [
            type('Result', (), {'returncode': 0})(),  # git add
            type('Result', (), {'returncode': 0})(),  # git commit
            type('Result', (), {'returncode': 0, 'stderr': 'remote: Change-Id: I1234567890abcdef'})()  # git push
        ]
        
        # Step 1: Fetch ticket
        fetch_input = TicketFetchInput(limit=1)
        fetch_result = await fetch_tickets(fetch_input)
        
        ticket = fetch_result.tickets[0]
        
        # Step 2: Create Gerrit PR
        gerrit_input = GerritPRInput(
            ticket_id=ticket.id,
            description=f"Fix for {ticket.summary}"
        )
        gerrit_result = await create_gerrit_pr(gerrit_input)
        
        assert gerrit_result.success is True
        assert gerrit_result.change_id == "I1234567890abcdef"
        
        # Verify git commands were called
        assert mock_subprocess.call_count == 3


@pytest.mark.integration
@pytest.mark.slow
class TestLiveIntegration:
    """Integration tests that can run against live Jira (when credentials available)."""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not has_jira_credentials(), reason="Jira credentials not available")
    async def test_fetch_tickets_live(self):
        """Test fetching tickets from live Jira instance."""
        # This test will only run if credentials are available
        input_data = TicketFetchInput(limit=1)
        
        try:
            result = await fetch_tickets(input_data)
            # Basic validation - we can't predict exact content
            assert isinstance(result.tickets, list)
            # If tickets exist, validate structure
            if result.tickets:
                ticket = result.tickets[0]
                assert hasattr(ticket, 'id')
                assert hasattr(ticket, 'summary')
                assert hasattr(ticket, 'status')
        except Exception as e:
            pytest.fail(f"Live Jira test failed: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not has_jira_credentials(), reason="Jira credentials not available")
    async def test_invalid_ticket_comment_live(self):
        """Test adding comment to non-existent ticket on live Jira."""
        input_data = CommentInput(ticket_id="INVALID-99999", comment="Test comment")
        
        result = await add_comment(input_data)
        
        # Should fail gracefully
        assert result.success is False
        assert result.error is not None
        assert result.comment_id is None


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Integration tests focused on error handling scenarios."""
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_network_timeout_handling(self, mock_client_class, mock_env_vars):
        """Test handling of network timeouts."""
        import httpx
        
        mock_client = mock_client_class.return_value.__aenter__.return_value
        mock_client.get.side_effect = httpx.TimeoutException("Request timed out")
        
        input_data = TicketFetchInput()
        
        with pytest.raises(httpx.TimeoutException):
            await fetch_tickets(input_data)
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_authentication_failure_handling(self, mock_client_class, mock_env_vars):
        """Test handling of authentication failures."""
        import httpx
        
        mock_client = mock_client_class.return_value.__aenter__.return_value
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized", 
            request=MagicMock(),
            response=MagicMock(status_code=401)
        )
        mock_client.get.return_value = mock_response
        
        input_data = TicketFetchInput()
        
        with pytest.raises(httpx.HTTPStatusError):
            await fetch_tickets(input_data)
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_malformed_api_response_handling(self, mock_client_class, mock_env_vars):
        """Test handling of malformed API responses."""
        mock_client = mock_client_class.return_value.__aenter__.return_value
        mock_response = type('MockResponse', (), {})()
        mock_response.json = lambda: {"unexpected": "format"}  # Missing 'issues' key
        mock_response.raise_for_status = lambda: None
        mock_client.get.return_value = mock_response
        
        input_data = TicketFetchInput()
        
        result = await fetch_tickets(input_data)
        
        # Should handle gracefully and return empty list
        assert len(result.tickets) == 0
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_git_repository_not_found(self, mock_subprocess):
        """Test handling when git repository is not found."""
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            128, ["git", "add", "."], stderr="fatal: not a git repository"
        )
        
        input_data = GerritPRInput(
            ticket_id="CON-12345",
            description="Test fix",
            repo_path="/nonexistent/path"
        )
        
        result = await create_gerrit_pr(input_data)
        
        assert result.success is False
        assert "not a git repository" in result.error
    
    @pytest.mark.asyncio
    async def test_missing_environment_variables_integration(self):
        """Test integration behavior with missing environment variables."""
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            # Test fetch_tickets
            with pytest.raises(RuntimeError, match="Missing Jira credentials"):
                await fetch_tickets(TicketFetchInput())
            
            # Test add_comment
            result = await add_comment(CommentInput(ticket_id="CON-123", comment="test"))
            assert result.success is False
            assert "Missing Jira credentials" in result.error
            
            # Test accept_ticket
            result = await accept_ticket(StatusUpdateInput(ticket_id="CON-123"))
            assert result.success is False
            assert "Missing Jira credentials" in result.error