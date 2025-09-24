"""
Unit tests for Pydantic data models validation and serialization.
"""
import pytest
from pydantic import ValidationError
from mcp_tools.version_support_assistant import (
    TicketFetchInput, TicketOutput, TicketFetchOutput,
    CommentInput, CommentOutput,
    StatusUpdateInput, StatusUpdateOutput,
    GerritPRInput, GerritPROutput
)


class TestTicketFetchInput:
    """Test TicketFetchInput model validation."""
    
    def test_default_values(self):
        """Test default values are set correctly."""
        input_data = TicketFetchInput()
        assert input_data.type == "Version Support"
        assert input_data.status == "To Triage"
        assert input_data.limit == 100
    
    def test_custom_values(self):
        """Test custom values override defaults."""
        input_data = TicketFetchInput(
            type="Bug",
            status="In Progress",
            limit=50
        )
        assert input_data.type == "Bug"
        assert input_data.status == "In Progress"
        assert input_data.limit == 50
    
    def test_invalid_limit_type(self):
        """Test validation error for invalid limit type."""
        with pytest.raises(ValidationError):
            TicketFetchInput(limit="invalid")


class TestTicketOutput:
    """Test TicketOutput model validation."""
    
    def test_valid_ticket_with_all_fields(self):
        """Test valid ticket with all fields populated."""
        ticket = TicketOutput(
            id="CON-12345",
            summary="Test ticket",
            status="To Triage",
            assignee="John Doe",
            created="2024-01-15T10:30:00.000+0000",
            releaseNotes="https://example.com/release"
        )
        assert ticket.id == "CON-12345"
        assert ticket.summary == "Test ticket"
        assert ticket.status == "To Triage"
        assert ticket.assignee == "John Doe"
        assert ticket.created == "2024-01-15T10:30:00.000+0000"
        assert ticket.releaseNotes == "https://example.com/release"
    
    def test_valid_ticket_with_none_fields(self):
        """Test valid ticket with optional fields as None."""
        ticket = TicketOutput(
            id="CON-12345",
            summary="Test ticket",
            status="To Triage",
            assignee=None,
            created="2024-01-15T10:30:00.000+0000",
            releaseNotes=None
        )
        assert ticket.assignee is None
        assert ticket.releaseNotes is None
    
    def test_missing_required_fields(self):
        """Test validation error for missing required fields."""
        with pytest.raises(ValidationError):
            TicketOutput(summary="Test ticket")


class TestTicketFetchOutput:
    """Test TicketFetchOutput model validation."""
    
    def test_empty_tickets_list(self):
        """Test valid output with empty tickets list."""
        output = TicketFetchOutput(tickets=[])
        assert output.tickets == []
    
    def test_tickets_list_with_data(self):
        """Test valid output with ticket data."""
        ticket = TicketOutput(
            id="CON-12345",
            summary="Test ticket",
            status="To Triage",
            assignee=None,
            created="2024-01-15T10:30:00.000+0000",
            releaseNotes=None
        )
        output = TicketFetchOutput(tickets=[ticket])
        assert len(output.tickets) == 1
        assert output.tickets[0].id == "CON-12345"


class TestCommentInput:
    """Test CommentInput model validation."""
    
    def test_valid_comment_input(self):
        """Test valid comment input."""
        comment_input = CommentInput(
            ticket_id="CON-12345",
            comment="This is a test comment"
        )
        assert comment_input.ticket_id == "CON-12345"
        assert comment_input.comment == "This is a test comment"
    
    def test_missing_required_fields(self):
        """Test validation error for missing required fields."""
        with pytest.raises(ValidationError):
            CommentInput(ticket_id="CON-12345")
        
        with pytest.raises(ValidationError):
            CommentInput(comment="Test comment")


class TestCommentOutput:
    """Test CommentOutput model validation."""
    
    def test_successful_comment_output(self):
        """Test successful comment output."""
        output = CommentOutput(success=True, comment_id="10001")
        assert output.success is True
        assert output.comment_id == "10001"
        assert output.error is None
    
    def test_failed_comment_output(self):
        """Test failed comment output."""
        output = CommentOutput(success=False, error="API error")
        assert output.success is False
        assert output.comment_id is None
        assert output.error == "API error"


class TestStatusUpdateInput:
    """Test StatusUpdateInput model validation."""
    
    def test_valid_status_update_input(self):
        """Test valid status update input."""
        input_data = StatusUpdateInput(ticket_id="CON-12345")
        assert input_data.ticket_id == "CON-12345"
    
    def test_missing_ticket_id(self):
        """Test validation error for missing ticket ID."""
        with pytest.raises(ValidationError):
            StatusUpdateInput()


class TestStatusUpdateOutput:
    """Test StatusUpdateOutput model validation."""
    
    def test_successful_status_update(self):
        """Test successful status update output."""
        output = StatusUpdateOutput(success=True)
        assert output.success is True
        assert output.error is None
    
    def test_failed_status_update(self):
        """Test failed status update output."""
        output = StatusUpdateOutput(success=False, error="Transition not allowed")
        assert output.success is False
        assert output.error == "Transition not allowed"


class TestGerritPRInput:
    """Test GerritPRInput model validation."""
    
    def test_valid_gerrit_input_with_defaults(self):
        """Test valid Gerrit input with default values."""
        input_data = GerritPRInput(
            ticket_id="CON-12345",
            description="Fix version support issue"
        )
        assert input_data.ticket_id == "CON-12345"
        assert input_data.description == "Fix version support issue"
        assert input_data.branch == "master"
        assert input_data.repo_path == "."
    
    def test_valid_gerrit_input_custom_values(self):
        """Test valid Gerrit input with custom values."""
        input_data = GerritPRInput(
            ticket_id="CON-12345",
            description="Fix version support issue",
            branch="develop",
            repo_path="/path/to/repo"
        )
        assert input_data.branch == "develop"
        assert input_data.repo_path == "/path/to/repo"
    
    def test_missing_required_fields(self):
        """Test validation error for missing required fields."""
        with pytest.raises(ValidationError):
            GerritPRInput(description="Fix issue")
        
        with pytest.raises(ValidationError):
            GerritPRInput(ticket_id="CON-12345")


class TestGerritPROutput:
    """Test GerritPROutput model validation."""
    
    def test_successful_gerrit_output(self):
        """Test successful Gerrit PR output."""
        output = GerritPROutput(success=True, change_id="I1234567890abcdef")
        assert output.success is True
        assert output.change_id == "I1234567890abcdef"
        assert output.error is None
    
    def test_failed_gerrit_output(self):
        """Test failed Gerrit PR output."""
        output = GerritPROutput(success=False, error="Git push failed")
        assert output.success is False
        assert output.change_id is None
        assert output.error == "Git push failed"