"""
Unit tests for MCP tool functions with mocking.
"""
import pytest
import subprocess
from unittest.mock import patch, AsyncMock, MagicMock
import httpx
from mcp_tools.version_support_assistant import (
    fetch_tickets, add_comment, accept_ticket, create_gerrit_pr,
    TicketFetchInput, CommentInput, StatusUpdateInput, GerritPRInput
)


@pytest.mark.unit
class TestFetchTickets:
    """Test fetch_tickets MCP tool function."""
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_fetch_tickets_success(self, mock_client_class, mock_env_vars, sample_jira_response):
        """Test successful ticket fetching."""
        # Setup mock client
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = sample_jira_response
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Test input
        input_data = TicketFetchInput()
        
        # Execute
        result = await fetch_tickets(input_data)
        
        # Verify
        assert len(result.tickets) == 2
        assert result.tickets[0].id == "CON-12345"
        assert result.tickets[0].summary == "Test version support ticket"
        assert result.tickets[0].status == "To Triage"
        assert result.tickets[0].assignee == "John Doe"
        assert result.tickets[0].releaseNotes == "https://example.com/release-notes"
        
        assert result.tickets[1].id == "CON-12346"
        assert result.tickets[1].assignee is None
        assert result.tickets[1].releaseNotes is None
        
        # Verify API call
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "jql" in call_args[1]["params"]
        assert call_args[1]["params"]["maxResults"] == 100
    
    @pytest.mark.asyncio
    async def test_fetch_tickets_missing_credentials(self, mock_env_vars_missing):
        """Test fetch_tickets with missing credentials."""
        input_data = TicketFetchInput()
        
        with pytest.raises(RuntimeError, match="Missing Jira credentials"):
            await fetch_tickets(input_data)
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_fetch_tickets_api_error(self, mock_client_class, mock_env_vars):
        """Test fetch_tickets with API error."""
        # Setup mock client to raise HTTP error
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=MagicMock(), response=MagicMock()
        )
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        input_data = TicketFetchInput()
        
        with pytest.raises(httpx.HTTPStatusError):
            await fetch_tickets(input_data)
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_fetch_tickets_custom_parameters(self, mock_client_class, mock_env_vars):
        """Test fetch_tickets with custom parameters."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"issues": []}
        mock_client.get.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        input_data = TicketFetchInput(type="Bug", status="In Progress", limit=50)
        
        result = await fetch_tickets(input_data)
        
        # Verify custom parameters were used
        call_args = mock_client.get.call_args
        jql = call_args[1]["params"]["jql"]
        assert 'type = "Bug"' in jql
        assert 'status = "In Progress"' in jql
        assert call_args[1]["params"]["maxResults"] == 50


@pytest.mark.unit
class TestAddComment:
    """Test add_comment MCP tool function."""
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_add_comment_success(self, mock_client_class, mock_env_vars, sample_comment_response):
        """Test successful comment addition."""
        # Setup mock client
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = sample_comment_response
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        input_data = CommentInput(ticket_id="CON-12345", comment="Test comment")
        
        result = await add_comment(input_data)
        
        assert result.success is True
        assert result.comment_id == "10001"
        assert result.error is None
        
        # Verify API call
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "CON-12345" in call_args[0][0]  # URL contains ticket ID
        assert "Test comment" in str(call_args[1]["json"])  # Payload contains comment
    
    @pytest.mark.asyncio
    async def test_add_comment_missing_credentials(self, mock_env_vars_missing):
        """Test add_comment with missing credentials."""
        input_data = CommentInput(ticket_id="CON-12345", comment="Test comment")
        
        result = await add_comment(input_data)
        
        assert result.success is False
        assert "Missing Jira credentials" in result.error
        assert result.comment_id is None
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_add_comment_api_error(self, mock_client_class, mock_env_vars):
        """Test add_comment with API error."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "403 Forbidden", request=MagicMock(), response=MagicMock()
        )
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        input_data = CommentInput(ticket_id="CON-12345", comment="Test comment")
        
        result = await add_comment(input_data)
        
        assert result.success is False
        assert result.error is not None
        assert result.comment_id is None


@pytest.mark.unit
class TestAcceptTicket:
    """Test accept_ticket MCP tool function."""
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_accept_ticket_success(self, mock_client_class, mock_env_vars):
        """Test successful ticket status update."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        input_data = StatusUpdateInput(ticket_id="CON-12345")
        
        result = await accept_ticket(input_data)
        
        assert result.success is True
        assert result.error is None
        
        # Verify API call
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert "CON-12345" in call_args[0][0]  # URL contains ticket ID
        assert call_args[1]["json"]["transition"]["id"] == "71"
    
    @pytest.mark.asyncio
    async def test_accept_ticket_missing_credentials(self, mock_env_vars_missing):
        """Test accept_ticket with missing credentials."""
        input_data = StatusUpdateInput(ticket_id="CON-12345")
        
        result = await accept_ticket(input_data)
        
        assert result.success is False
        assert "Missing Jira credentials" in result.error
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_accept_ticket_api_error(self, mock_client_class, mock_env_vars):
        """Test accept_ticket with API error."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400 Bad Request", request=MagicMock(), response=MagicMock()
        )
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        input_data = StatusUpdateInput(ticket_id="CON-12345")
        
        result = await accept_ticket(input_data)
        
        assert result.success is False
        assert result.error is not None


@pytest.mark.unit
class TestCreateGerritPR:
    """Test create_gerrit_pr MCP tool function."""
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_create_gerrit_pr_success(self, mock_subprocess):
        """Test successful Gerrit PR creation."""
        # Setup mock subprocess calls
        mock_results = [
            MagicMock(returncode=0),  # git add
            MagicMock(returncode=0),  # git commit
            MagicMock(returncode=0, stderr="remote: Change-Id: I1234567890abcdef")  # git push
        ]
        mock_subprocess.side_effect = mock_results
        
        input_data = GerritPRInput(
            ticket_id="CON-12345",
            description="Fix version support issue"
        )
        
        result = await create_gerrit_pr(input_data)
        
        assert result.success is True
        assert result.change_id == "I1234567890abcdef"
        assert result.error is None
        
        # Verify subprocess calls
        assert mock_subprocess.call_count == 3
        
        # Verify git add call
        add_call = mock_subprocess.call_args_list[0]
        assert add_call[0][0] == ["git", "add", "."]
        
        # Verify git commit call
        commit_call = mock_subprocess.call_args_list[1]
        assert commit_call[0][0][0:3] == ["git", "commit", "-m"]
        commit_msg = commit_call[0][0][3]
        assert "CON-12345" in commit_msg
        assert "Fix version support issue" in commit_msg
        assert "Task-Url: https://tasktop.atlassian.net/browse/CON-12345" in commit_msg
        
        # Verify git push call
        push_call = mock_subprocess.call_args_list[2]
        assert push_call[0][0] == ["git", "push", "origin", "HEAD:refs/for/master%wip"]
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_create_gerrit_pr_custom_branch_and_path(self, mock_subprocess):
        """Test Gerrit PR creation with custom branch and repo path."""
        mock_results = [
            MagicMock(returncode=0),
            MagicMock(returncode=0),
            MagicMock(returncode=0, stderr="remote: Change-Id: I9876543210fedcba")
        ]
        mock_subprocess.side_effect = mock_results
        
        input_data = GerritPRInput(
            ticket_id="CON-12345",
            description="Fix version support issue",
            branch="develop",
            repo_path="/custom/path"
        )
        
        result = await create_gerrit_pr(input_data)
        
        assert result.success is True
        assert result.change_id == "I9876543210fedcba"
        
        # Verify custom repo path was used
        for call in mock_subprocess.call_args_list:
            assert call[1]["cwd"] == "/custom/path"
        
        # Verify custom branch was used
        push_call = mock_subprocess.call_args_list[2]
        assert push_call[0][0] == ["git", "push", "origin", "HEAD:refs/for/develop%wip"]
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_create_gerrit_pr_git_add_failure(self, mock_subprocess):
        """Test Gerrit PR creation with git add failure."""
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            1, ["git", "add", "."], stderr="fatal: not a git repository"
        )
        
        input_data = GerritPRInput(
            ticket_id="CON-12345",
            description="Fix version support issue"
        )
        
        result = await create_gerrit_pr(input_data)
        
        assert result.success is False
        assert "Git command failed" in result.error
        assert result.change_id is None
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_create_gerrit_pr_git_commit_failure(self, mock_subprocess):
        """Test Gerrit PR creation with git commit failure."""
        mock_results = [
            MagicMock(returncode=0),  # git add succeeds
            subprocess.CalledProcessError(1, ["git", "commit"], stderr="nothing to commit")
        ]
        mock_subprocess.side_effect = mock_results
        
        input_data = GerritPRInput(
            ticket_id="CON-12345",
            description="Fix version support issue"
        )
        
        result = await create_gerrit_pr(input_data)
        
        assert result.success is False
        assert "Git command failed" in result.error
        assert result.change_id is None
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_create_gerrit_pr_git_push_failure(self, mock_subprocess):
        """Test Gerrit PR creation with git push failure."""
        mock_results = [
            MagicMock(returncode=0),  # git add
            MagicMock(returncode=0),  # git commit
            subprocess.CalledProcessError(1, ["git", "push"], stderr="Permission denied")
        ]
        mock_subprocess.side_effect = mock_results
        
        input_data = GerritPRInput(
            ticket_id="CON-12345",
            description="Fix version support issue"
        )
        
        result = await create_gerrit_pr(input_data)
        
        assert result.success is False
        assert "Git command failed" in result.error
        assert result.change_id is None
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_create_gerrit_pr_no_change_id_in_output(self, mock_subprocess):
        """Test Gerrit PR creation when Change-Id is not found in output."""
        mock_results = [
            MagicMock(returncode=0),
            MagicMock(returncode=0),
            MagicMock(returncode=0, stderr="remote: some other output")
        ]
        mock_subprocess.side_effect = mock_results
        
        input_data = GerritPRInput(
            ticket_id="CON-12345",
            description="Fix version support issue"
        )
        
        result = await create_gerrit_pr(input_data)
        
        assert result.success is True
        assert result.change_id is None  # No Change-Id found
        assert result.error is None
    
    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_create_gerrit_pr_unexpected_exception(self, mock_subprocess):
        """Test Gerrit PR creation with unexpected exception."""
        mock_subprocess.side_effect = Exception("Unexpected error")
        
        input_data = GerritPRInput(
            ticket_id="CON-12345",
            description="Fix version support issue"
        )
        
        result = await create_gerrit_pr(input_data)
        
        assert result.success is False
        assert "Unexpected error" in result.error
        assert result.change_id is None