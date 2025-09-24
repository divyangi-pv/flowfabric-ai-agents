"""
Pytest configuration and shared fixtures for version support assistant tests.
"""
import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch
import httpx


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    env_vars = {
        "JIRA_URL": "https://test.atlassian.net",
        "JIRA_USER": "test_user",
        "JIRA_TOKEN": "test_token"
    }
    with patch.dict(os.environ, env_vars):
        yield env_vars


@pytest.fixture
def mock_env_vars_missing():
    """Mock missing environment variables for testing error conditions."""
    # Clear any existing env vars
    with patch.dict(os.environ, {}, clear=True):
        yield


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient for API testing."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_client.get.return_value = mock_response
    mock_client.post.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    return mock_client, mock_response


@pytest.fixture
def sample_jira_response():
    """Sample Jira API response for testing."""
    return {
        "issues": [
            {
                "key": "CON-12345",
                "fields": {
                    "summary": "Test version support ticket",
                    "status": {"name": "To Triage"},
                    "assignee": {"displayName": "John Doe"},
                    "created": "2024-01-15T10:30:00.000+0000",
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {"type": "text", "text": "Release Information: https://example.com/release-notes"}
                                ]
                            }
                        ]
                    }
                }
            },
            {
                "key": "CON-12346",
                "fields": {
                    "summary": "Another test ticket",
                    "status": {"name": "To Triage"},
                    "assignee": None,
                    "created": "2024-01-16T11:30:00.000+0000",
                    "description": None
                }
            }
        ]
    }


@pytest.fixture
def sample_comment_response():
    """Sample Jira comment API response."""
    return {
        "id": "10001",
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Test comment"}
                    ]
                }
            ]
        }
    }


@pytest.fixture
def mock_subprocess():
    """Mock subprocess for Git operations testing."""
    with patch('subprocess.run') as mock_run:
        # Default successful run
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = "remote: Change-Id: I1234567890abcdef"
        mock_run.return_value = mock_result
        yield mock_run