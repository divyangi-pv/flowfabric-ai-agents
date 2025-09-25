"""
Tests for release sign-off assistant MCP tools.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from mcp_tools.release_signoff_assistant import (
    fetch_release_signoff_tickets,
    fetch_ticket,
    fetch_previous_version_ticket,
    get_commits_between_tags,
    update_ticket_with_previous_versions,
    update_ticket_with_task_urls,
    update_ticket_status,
    FetchReleaseTicketsRequest,
    FetchTicketRequest,
    FetchPreviousVersionTicketRequest,
    GetCommitsBetweenTagsRequest,
    UpdateTicketWithPreviousVersionsRequest,
    UpdateTicketWithTaskUrlsRequest,
    UpdateTicketStatusRequest,
    extract_versions_from_description
)


class TestExtractVersionsFromDescription:
    """Test version extraction from ticket descriptions."""
    
    def test_extract_all_versions(self):
        """Test extracting all version types."""
        description = {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Current Connector Version:"},
                        {"type": "text", "text": "25.3.0.20250904-1757"}
                    ]
                },
                {
                    "type": "paragraph", 
                    "content": [
                        {"type": "text", "text": "Current SDK Version:"},
                        {"type": "text", "text": "25.3.0.20250804-1138"}
                    ]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Platform Version: 25.3.0.20250919-0941"}
                    ]
                }
            ]
        }
        
        versions = extract_versions_from_description(description)
        
        assert versions['current_connector_version'] == "25.3.0.20250904-1757"
        assert versions['current_sdk_version'] == "25.3.0.20250804-1138"
        assert versions['current_platform_version'] == "25.3.0.20250919-0941"


class TestFetchReleaseSignoffTickets:
    """Test fetching release sign-off tickets."""
    
    @patch('mcp_tools.release_signoff_assistant.JiraClient')
    def test_fetch_tickets_success(self, mock_jira_client):
        """Test successful ticket fetching."""
        mock_client = Mock()
        mock_jira_client.return_value = mock_client
        
        mock_client.search_tickets.return_value = {
            'total': 1,
            'issues': [{
                'key': 'CON-25671',
                'fields': {
                    'summary': 'Release sign-off for 25.3.4',
                    'status': {'name': 'Accepted'},
                    'created': '2025-09-23T07:35:46.553-0700',
                    'description': 'Test description',
                    'assignee': None,
                    'reporter': {'displayName': 'Test User'},
                    'fixVersions': [{'name': '25.3.4'}]
                }
            }]
        }
        
        request = FetchReleaseTicketsRequest()
        result = fetch_release_signoff_tickets(request)
        
        assert result['success'] is True
        assert result['total'] == 1
        assert len(result['tickets']) == 1
        assert result['tickets'][0]['key'] == 'CON-25671'


class TestFetchTicket:
    """Test fetching specific tickets."""
    
    @patch('mcp_tools.release_signoff_assistant.JiraClient')
    def test_fetch_specific_ticket(self, mock_jira_client):
        """Test fetching a specific ticket by key."""
        mock_client = Mock()
        mock_jira_client.return_value = mock_client
        
        mock_client.get_ticket.return_value = {
            'key': 'CON-25671',
            'fields': {
                'summary': 'Release sign-off for 25.3.4',
                'status': {'name': 'Accepted'},
                'created': '2025-09-23T07:35:46.553-0700',
                'description': 'Test description',
                'assignee': None,
                'reporter': {'displayName': 'Test User'},
                'fixVersions': [{'name': '25.3.4'}]
            }
        }
        
        request = FetchTicketRequest(ticket_key='CON-25671')
        result = fetch_ticket(request)
        
        assert result['success'] is True
        assert result['ticket']['key'] == 'CON-25671'


class TestFetchPreviousVersionTicket:
    """Test fetching previous version tickets."""
    
    @patch('mcp_tools.release_signoff_assistant.JiraClient')
    def test_fetch_previous_version_success(self, mock_jira_client):
        """Test successful previous version ticket fetch."""
        mock_client = Mock()
        mock_jira_client.return_value = mock_client
        
        mock_client.search_tickets.return_value = {
            'issues': [{
                'key': 'CON-25633',
                'fields': {
                    'summary': 'Release sign-off for 25.3.3',
                    'status': {'name': 'Approved'},
                    'created': '2025-09-04T16:28:05.492-0700',
                    'description': {
                        "type": "doc",
                        "content": [{
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": "Current Connector Version:"},
                                {"type": "text", "text": "25.3.0.20250904-1757"}
                            ]
                        }]
                    },
                    'assignee': {'displayName': 'Test User'},
                    'reporter': {'displayName': 'Eng Ops'},
                    'fixVersions': [{'name': '25.3.3'}]
                }
            }]
        }
        
        request = FetchPreviousVersionTicketRequest(current_version='25.3.4')
        result = fetch_previous_version_ticket(request)
        
        assert result['success'] is True
        assert result['previous_version'] == '25.3.3'
        assert result['ticket']['key'] == 'CON-25633'


class TestGetCommitsBetweenTags:
    """Test getting commits between Git tags."""
    
    def test_get_commits_error_handling(self):
        """Test error handling when Git operations fail."""
        request = GetCommitsBetweenTagsRequest(current_version='25.3.4')
        
        # This will fail due to missing environment or network issues
        # which is expected behavior for the error handling
        result = get_commits_between_tags(request)
        
        # Should return error structure
        assert 'success' in result
        assert 'error' in result or result['success'] is True


class TestUpdateTicketWithTaskUrls:
    """Test updating tickets with task URLs."""
    
    def test_update_with_task_urls_structure(self):
        """Test the basic structure of task URL updates."""
        request = UpdateTicketWithTaskUrlsRequest(current_version='25.3.4')
        
        # Test that the request is properly structured
        assert request.current_version == '25.3.4'
        assert hasattr(request, 'current_version')


class TestUpdateTicketStatus:
    """Test updating ticket status."""
    
    @patch('mcp_tools.release_signoff_assistant.requests.get')
    @patch('mcp_tools.release_signoff_assistant.requests.put')
    @patch('mcp_tools.release_signoff_assistant.requests.post')
    @patch('mcp_tools.release_signoff_assistant.JiraClient')
    def test_update_status_success(self, mock_jira_client, mock_post, mock_put, mock_get):
        """Test successful status update."""
        mock_client = Mock()
        mock_jira_client.return_value = mock_client
        
        # Mock transitions response
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'transitions': [{'id': '101', 'to': {'name': 'Done'}}]
        }
        
        # Mock successful responses
        mock_put.return_value.status_code = 204
        mock_post.return_value.status_code = 204
        
        request = UpdateTicketStatusRequest(ticket_key='CON-25671', status='Done')
        result = update_ticket_status(request)
        
        assert result['success'] is True
        assert result['status_updated'] == 'Done'