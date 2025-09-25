import os
import requests
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("release-signoff-assistant")

# -----------------------------
# Schemas
# -----------------------------

class FetchReleaseTicketsRequest(BaseModel):
    status: Optional[str] = None
    limit: Optional[int] = 50
    hours_back: Optional[int] = None

class FetchTicketRequest(BaseModel):
    ticket_key: str

class FetchPreviousVersionTicketRequest(BaseModel):
    current_version: str

class UpdateTicketWithPreviousVersionsRequest(BaseModel):
    current_version: str

class GetCommitsBetweenTagsRequest(BaseModel):
    current_version: str

class UpdateTicketWithTaskUrlsRequest(BaseModel):
    current_version: str

class UpdateTicketStatusRequest(BaseModel):
    ticket_key: str
    status: str = "Approved"
    label: str = "Denim"

# -----------------------------
# Jira Client
# -----------------------------

class JiraClient:
    def __init__(self):
        self.base_url = os.getenv('JIRA_URL')
        self.username = os.getenv('JIRA_USER')
        self.token = os.getenv('JIRA_TOKEN')

        if not all([self.base_url, self.username, self.token]):
            raise ValueError("Missing Jira credentials. Please set JIRA_URL, JIRA_USER, and JIRA_TOKEN in .env")

    def search_tickets(self, jql: str, max_results: int = 50) -> Dict[str, Any]:
        """Search Jira tickets using JQL"""
        url = f"{self.base_url}/rest/api/3/search/jql"

        params = {
            'jql': jql,
            'maxResults': max_results,
            'fields': 'key,summary,status,created,description,assignee,reporter,fixVersions'
        }

        response = requests.get(
            url,
            params=params,
            auth=(self.username, self.token),
            headers={'Accept': 'application/json'}
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Jira API error: {response.status_code} - {response.text}")

    def get_ticket(self, ticket_key: str) -> Dict[str, Any]:
        """Get a specific ticket by key"""
        url = f"{self.base_url}/rest/api/3/issue/{ticket_key}"

        params = {
            'fields': 'key,summary,status,created,description,assignee,reporter,fixVersions'
        }

        response = requests.get(
            url,
            params=params,
            auth=(self.username, self.token),
            headers={'Accept': 'application/json'}
        )

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Jira API error: {response.status_code} - {response.text}")

    def update_ticket(self, ticket_key: str, description: Dict[str, Any] = None, status: str = None, labels: List[str] = None, assignee: str = None) -> Dict[str, Any]:
        """Update a ticket's description, status, labels, and assignee"""
        url = f"{self.base_url}/rest/api/3/issue/{ticket_key}"

        # Build fields payload
        fields = {}
        if description:
            fields["description"] = description
        if labels:
            fields["labels"] = labels
        if assignee:
            fields["assignee"] = {"emailAddress": assignee}

        # Update fields if any
        if fields:
            payload = {"fields": fields}
            response = requests.put(
                url,
                json=payload,
                auth=(self.username, self.token),
                headers={'Accept': 'application/json', 'Content-Type': 'application/json'}
            )

            if response.status_code != 204:
                raise Exception(f"Jira field update error: {response.status_code} - {response.text}")

        # Handle status transition if requested
        if status:
            transitions_url = f"{url}/transitions"

            # Get available transitions
            trans_response = requests.get(
                transitions_url,
                auth=(self.username, self.token),
                headers={'Accept': 'application/json'}
            )

            if trans_response.status_code != 200:
                raise Exception(f"Failed to get transitions: {trans_response.status_code}")

            transitions = trans_response.json().get('transitions', [])

            # Find transition ID
            transition_id = None
            for transition in transitions:
                if transition['to']['name'].lower() == status.lower():
                    transition_id = transition['id']
                    break

            if not transition_id:
                available = [t['to']['name'] for t in transitions]
                raise Exception(f"No transition to {status}. Available: {available}")

            # Execute transition
            transition_payload = {"transition": {"id": transition_id}}
            trans_exec_response = requests.post(
                transitions_url,
                json=transition_payload,
                auth=(self.username, self.token),
                headers={'Accept': 'application/json', 'Content-Type': 'application/json'}
            )

            if trans_exec_response.status_code != 204:
                raise Exception(f"Transition failed: {trans_exec_response.status_code}")

        return {'success': True}

# -----------------------------
# Helper Functions
# -----------------------------

def extract_versions_from_description(description: Any) -> Dict[str, str]:
    """Extract connector, SDK, and platform versions from ticket description"""
    versions = {
        'current_connector_version': None,
        'current_sdk_version': None,
        'current_platform_version': None
    }

    if not description or not isinstance(description, dict):
        return versions

    # Navigate through the description structure to find version info
    content = description.get('content', [])
    for paragraph in content:
        if paragraph.get('type') == 'paragraph':
            paragraph_content = paragraph.get('content', [])
            
            # Look through all text elements in this paragraph
            for i, item in enumerate(paragraph_content):
                if item.get('type') == 'text':
                    text = item.get('text', '').strip()
                    marks = item.get('marks', [])
                    
                    # Check if this is a version number (has code formatting and looks like a version)
                    if any(mark.get('type') == 'code' for mark in marks) and '.' in text and len(text) > 10:
                        # Look backwards to see what this version is for
                        for j in range(i - 1, -1, -1):
                            prev_item = paragraph_content[j]
                            if prev_item.get('type') == 'text':
                                prev_text = prev_item.get('text', '').strip()
                                if 'Platform Version' in prev_text:
                                    versions['current_platform_version'] = text
                                    break
                                elif 'Current Connector Version' in prev_text:
                                    versions['current_connector_version'] = text
                                    break
                                elif 'Current SDK Version' in prev_text:
                                    versions['current_sdk_version'] = text
                                    break
                                elif 'Previous Connector Version' in prev_text:
                                    if not versions['current_connector_version']:
                                        versions['current_connector_version'] = text
                                    break
                                elif 'Previous SDK Version' in prev_text:
                                    if not versions['current_sdk_version']:
                                        versions['current_sdk_version'] = text
                                    break

    return versions


# -----------------------------
# MCP Tool Implementation
# -----------------------------

@mcp.tool()
def fetch_release_signoff_tickets(request: FetchReleaseTicketsRequest) -> Dict[str, Any]:
    """
    Fetch release sign-off tickets from Jira.

    Args:
        status: Filter by ticket status (optional)
        limit: Maximum number of tickets to return (default: 50)
        hours_back: Only fetch tickets created in the last N hours (optional)

    Returns:
        Dictionary containing the fetched tickets and metadata
    """
    try:
        jira_client = JiraClient()

        # Build JQL query for Release Sign-Off tickets
        jql_parts = ['issuetype = "Release Sign-Off"']

        # Add status filter if provided
        if request.status:
            jql_parts.append(f'status = "{request.status}"')

        # Add time filter if provided
        if request.hours_back:
            from datetime import datetime, timedelta
            cutoff_time = datetime.now() - timedelta(hours=request.hours_back)
            cutoff_str = cutoff_time.strftime('%Y-%m-%d %H:%M')
            jql_parts.append(f'created >= "{cutoff_str}"')

        # Order by created date (newest first)
        jql = ' AND '.join(jql_parts) + ' ORDER BY created DESC'

        # Search tickets
        result = jira_client.search_tickets(jql, request.limit)

        # Format response
        tickets = []
        for issue in result.get('issues', []):
            ticket = {
                'key': issue['key'],
                'summary': issue['fields']['summary'],
                'status': issue['fields']['status']['name'],
                'created': issue['fields']['created'],
                'description': issue['fields'].get('description', ''),
                'assignee': issue['fields']['assignee']['displayName'] if issue['fields'].get('assignee') else None,
                'reporter': issue['fields']['reporter']['displayName'] if issue['fields'].get('reporter') else None,
                'fixVersions': [v['name'] for v in issue['fields'].get('fixVersions', [])]
            }
            tickets.append(ticket)

        return {
            'success': True,
            'total': result.get('total', 0),
            'returned': len(tickets),
            'tickets': tickets,
            'query': jql
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'tickets': []
        }

@mcp.tool()
def fetch_ticket(request: FetchTicketRequest) -> Dict[str, Any]:
    """
    Fetch a specific ticket by its key.

    Args:
        ticket_key: The Jira ticket key (e.g., CON-25671)

    Returns:
        Dictionary containing the ticket details
    """
    try:
        jira_client = JiraClient()

        # Get the specific ticket
        issue = jira_client.get_ticket(request.ticket_key)

        # Format response
        ticket = {
            'key': issue['key'],
            'summary': issue['fields']['summary'],
            'status': issue['fields']['status']['name'],
            'created': issue['fields']['created'],
            'description': issue['fields'].get('description', ''),
            'assignee': issue['fields']['assignee']['displayName'] if issue['fields'].get('assignee') else None,
            'reporter': issue['fields']['reporter']['displayName'] if issue['fields'].get('reporter') else None,
            'fixVersions': [v['name'] for v in issue['fields'].get('fixVersions', [])]
        }

        return {
            'success': True,
            'ticket': ticket
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'ticket': None
        }

@mcp.tool()
def fetch_previous_version_ticket(request: FetchPreviousVersionTicketRequest) -> Dict[str, Any]:
    """
    Fetch release sign-off ticket for the previous version.

    Args:
        current_version: Current version (e.g., "25.3.4") to find previous version ticket

    Returns:
        Dictionary containing the previous version ticket details
    """
    try:
        # Calculate previous version
        version_parts = request.current_version.split('.')
        if len(version_parts) >= 3:
            patch_version = int(version_parts[2]) - 1
            if patch_version >= 0:
                previous_version = f"{version_parts[0]}.{version_parts[1]}.{patch_version}"
            else:
                return {
                    'success': False,
                    'error': 'Cannot calculate previous version: patch version would be negative',
                    'ticket': None
                }
        else:
            return {
                'success': False,
                'error': 'Invalid version format. Expected format: X.Y.Z',
                'ticket': None
            }

        jira_client = JiraClient()

        # Build JQL query for Release Sign-Off tickets with previous version and Approved status
        jql = f'issuetype = "Release Sign-Off" AND fixVersion = "{previous_version}" AND status = "Approved" ORDER BY created DESC'

        # Search tickets
        result = jira_client.search_tickets(jql, 1)

        if result.get('issues'):
            issue = result['issues'][0]
            description = issue['fields'].get('description', '')
            versions = extract_versions_from_description(description)

            ticket = {
                'key': issue['key'],
                'summary': issue['fields']['summary'],
                'status': issue['fields']['status']['name'],
                'created': issue['fields']['created'],
                'description': description,
                'assignee': issue['fields']['assignee']['displayName'] if issue['fields'].get('assignee') else None,
                'reporter': issue['fields']['reporter']['displayName'] if issue['fields'].get('reporter') else None,
                'fixVersions': [v['name'] for v in issue['fields'].get('fixVersions', [])]
            }

            return {
                'success': True,
                'previous_version': previous_version,
                'ticket': ticket,
                'current_connector_version': versions['current_connector_version'],
                'current_sdk_version': versions['current_sdk_version']
            }
        else:
            return {
                'success': False,
                'error': f'No release sign-off ticket found for version {previous_version}',
                'previous_version': previous_version,
                'ticket': None
            }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'ticket': None
        }

@mcp.tool()
def update_ticket_with_previous_versions(request: UpdateTicketWithPreviousVersionsRequest) -> Dict[str, Any]:
    """
    Update current release sign-off ticket with previous connector and SDK versions.

    Args:
        current_version: Current version (e.g., "25.3.4") to find and update the ticket

    Returns:
        Dictionary containing the update result
    """
    try:
        jira_client = JiraClient()

        # Find current version ticket
        jql = f'issuetype = "Release Sign-Off" AND fixVersion = "{request.current_version}" ORDER BY created DESC'
        result = jira_client.search_tickets(jql, 1)

        if not result.get('issues'):
            return {
                'success': False,
                'error': f'No release sign-off ticket found for version {request.current_version}'
            }

        current_ticket = result['issues'][0]
        current_key = current_ticket['key']
        current_description = current_ticket['fields'].get('description', {})

        # Get previous version info
        version_parts = request.current_version.split('.')
        if len(version_parts) >= 3:
            patch_version = int(version_parts[2]) - 1
            if patch_version >= 0:
                previous_version = f"{version_parts[0]}.{version_parts[1]}.{patch_version}"
            else:
                return {
                    'success': False,
                    'error': 'Cannot calculate previous version: patch version would be negative'
                }
        else:
            return {
                'success': False,
                'error': 'Invalid version format. Expected format: X.Y.Z'
            }

        # Get previous version ticket
        prev_jql = f'issuetype = "Release Sign-Off" AND fixVersion = "{previous_version}" AND status = "Approved" ORDER BY created DESC'
        prev_result = jira_client.search_tickets(prev_jql, 1)

        if not prev_result.get('issues'):
            return {
                'success': False,
                'error': f'No approved release sign-off ticket found for previous version {previous_version}'
            }

        prev_issue = prev_result['issues'][0]
        prev_description = prev_issue['fields'].get('description', '')
        versions = extract_versions_from_description(prev_description)

        if not versions['current_connector_version'] or not versions['current_sdk_version']:
            return {
                'success': False,
                'error': 'Could not extract connector and SDK versions from previous ticket'
            }

        # Create new paragraph with previous versions
        new_paragraph = {
            "type": "paragraph",
            "content": [
                {"type": "hardBreak"},
                {"type": "text", "text": "Previous Connector Version: ", "marks": [{"type": "strong"}]},
                {"type": "text", "text": versions['current_connector_version'], "marks": [{"type": "code"}]},
                {"type": "hardBreak"},
                {"type": "text", "text": "Previous SDK Version: ", "marks": [{"type": "strong"}]},
                {"type": "text", "text": versions['current_sdk_version'], "marks": [{"type": "code"}]}
            ]
        }

        # Update description
        if isinstance(current_description, dict) and 'content' in current_description:
            current_description['content'].append(new_paragraph)
        else:
            current_description = {
                "type": "doc",
                "version": 1,
                "content": [new_paragraph]
            }

        # Update the ticket
        jira_client.update_ticket(current_key, current_description)

        return {
            'success': True,
            'ticket_key': current_key,
            'previous_version': previous_version,
            'added_connector_version': versions['current_connector_version'],
            'added_sdk_version': versions['current_sdk_version']
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@mcp.tool()
def get_commits_between_tags(request: GetCommitsBetweenTagsRequest) -> Dict[str, Any]:
    """
    Get list of commits between previous connector tag and platform version tag.

    Args:
        current_version: Current version (e.g., "25.3.4") to determine branch and tags

    Returns:
        Dictionary containing the commit list and metadata
    """
    try:
        jira_client = JiraClient()

        # Get current version ticket to extract platform version
        jql = f'issuetype = "Release Sign-Off" AND fixVersion = "{request.current_version}" ORDER BY created DESC'
        result = jira_client.search_tickets(jql, 1)

        if not result.get('issues'):
            return {
                'success': False,
                'error': f'No release sign-off ticket found for version {request.current_version}'
            }

        current_ticket = result['issues'][0]
        current_description = current_ticket['fields'].get('description', '')
        current_versions = extract_versions_from_description(current_description)

        if not current_versions['current_platform_version']:
            return {
                'success': False,
                'error': 'Could not extract platform version from current ticket'
            }

        # Get previous version ticket to extract connector version
        version_parts = request.current_version.split('.')
        if len(version_parts) >= 3:
            patch_version = int(version_parts[2]) - 1
            if patch_version >= 0:
                previous_version = f"{version_parts[0]}.{version_parts[1]}.{patch_version}"
            else:
                return {
                    'success': False,
                    'error': 'Cannot calculate previous version: patch version would be negative'
                }
        else:
            return {
                'success': False,
                'error': 'Invalid version format. Expected format: X.Y.Z'
            }

        prev_jql = f'issuetype = "Release Sign-Off" AND fixVersion = "{previous_version}" AND status = "Approved" ORDER BY created DESC'
        prev_result = jira_client.search_tickets(prev_jql, 1)

        if not prev_result.get('issues'):
            return {
                'success': False,
                'error': f'No approved release sign-off ticket found for previous version {previous_version}'
            }

        prev_issue = prev_result['issues'][0]
        prev_description = prev_issue['fields'].get('description', '')
        prev_versions = extract_versions_from_description(prev_description)

        if not prev_versions['current_connector_version']:
            return {
                'success': False,
                'error': 'Could not extract connector version from previous ticket'
            }

        # Determine Git branch (e.g., 25.3.x from 25.3.4)
        git_branch = f"{version_parts[0]}.{version_parts[1]}.x"

        # Git repository URL with credentials
        git_username = os.getenv('GIT_USER_NAME', 'divyangi.mayank')
        git_password = os.getenv('GIT_PASSWORD')

        if not git_password:
            return {
                'success': False,
                'error': 'Git password not found in environment variables. Please set GIT_PASSWORD in .env'
            }

        # URL encode the password to handle special characters
        import urllib.parse
        encoded_password = urllib.parse.quote(git_password, safe='')
        git_repo = f"https://{git_username}:{encoded_password}@review.tasktop.com/a/com.tasktop.connector.git"

        # Use Gerrit REST API with timeout and fallback
        import urllib.parse

        git_username = os.getenv('GIT_USER_NAME', 'divyangi.mayank')
        git_password = os.getenv('GIT_PASSWORD')

        try:
            # Use Gitiles API for commit log
            gitiles_url = f"https://review.tasktop.com/a/plugins/gitiles/com.tasktop.connector/+log/{prev_versions['current_connector_version']}..{current_versions['current_platform_version']}"

            params = {'format': 'JSON'}

            response = requests.get(
                gitiles_url,
                params=params,
                auth=(git_username, git_password),
                headers={'Accept': 'application/json'},
                timeout=10
            )

            if response.status_code != 200:
                raise Exception(f'Gitiles API error: {response.status_code}')

            # Parse Gitiles JSON response
            response_text = response.text
            if response_text.startswith(")]}'\n"):
                response_text = response_text[5:]

            import json
            commit_data = json.loads(response_text)

            # Extract commits from Gitiles response
            commits = []
            if 'log' in commit_data:
                for commit in commit_data['log']:
                    message = commit.get('message', '').split('\n')[0]

                    # Extract task ID from commit message (e.g., CON-25522)
                    import re
                    task_match = re.search(r'(CON-\d+)', message)
                    task_url = None
                    if task_match:
                        task_id = task_match.group(1)
                        task_url = f'https://tasktop.atlassian.net/browse/{task_id}'

                    commits.append({
                        'hash': commit.get('commit', '')[:8],
                        'message': message,
                        'task_url': task_url
                    })

        except Exception as api_error:
            # Fallback: Return structure with error info
            return {
                'success': False,
                'error': f'Unable to fetch commits from Gitiles: {str(api_error)}',
                'git_branch': git_branch,
                'previous_connector_tag': prev_versions['current_connector_version'],
                'platform_tag': current_versions['current_platform_version'],
                'note': 'Gitiles API access required for commit details',
                'gitiles_url': f"https://review.tasktop.com/a/plugins/gitiles/com.tasktop.connector/+log/{prev_versions['current_connector_version']}..{current_versions['current_platform_version']}?format=JSON"
            }

        return {
            'success': True,
            'git_branch': git_branch,
            'previous_connector_tag': prev_versions['current_connector_version'],
            'platform_tag': current_versions['current_platform_version'],
            'commit_count': len(commits),
            'commits': commits,
            'jira_base_url': 'https://tasktop.atlassian.net/browse/'
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@mcp.tool()
def update_ticket_with_task_urls(request: UpdateTicketWithTaskUrlsRequest) -> Dict[str, Any]:
    """
    Update current release sign-off ticket with related task URLs from commits.

    Args:
        current_version: Current version (e.g., "25.3.4") to find and update the ticket

    Returns:
        Dictionary containing the update result
    """

    jira_client = JiraClient()

    try:
        # Get commits between tags first
        commits_request = GetCommitsBetweenTagsRequest(current_version=request.current_version)
        commits_result = get_commits_between_tags(commits_request)

        if not commits_result.get('success'):
            return {
                'success': False,
                'error': f'Failed to get commits: {commits_result.get("error")}'
            }

        # Extract task URLs and check their status
        task_urls = []
        incomplete_tasks = []

        for commit in commits_result.get('commits', []):
            if commit.get('task_url'):
                task_urls.append(commit['task_url'])

                # Check task status
                task_id = commit['task_url'].split('/')[-1]
                try:
                    task_ticket = jira_client.get_ticket(task_id)
                    task_status = task_ticket['fields']['status']['name']

                    if task_status.lower() not in ['done', 'closed', 'resolved', 'complete', 'completed']:
                        incomplete_tasks.append({
                            'task_id': task_id,
                            'status': task_status,
                            'url': commit['task_url']
                        })
                except Exception as e:
                    incomplete_tasks.append({
                        'task_id': task_id,
                        'status': 'ERROR',
                        'url': commit['task_url'],
                        'error': str(e)
                    })

        if not task_urls:
            return {
                'success': False,
                'error': 'No task URLs found in commits'
            }

        # Get current ticket
        jira_client = JiraClient()
        jql = f'issuetype = "Release Sign-Off" AND fixVersion = "{request.current_version}" ORDER BY created DESC'
        result = jira_client.search_tickets(jql, 1)

        if not result.get('issues'):
            return {
                'success': False,
                'error': f'No release sign-off ticket found for version {request.current_version}'
            }

        current_ticket = result['issues'][0]
        current_key = current_ticket['key']
        current_description = current_ticket['fields'].get('description', {})

        # Create related tickets section
        related_tickets_content = [
            {"type": "hardBreak"},
            {"type": "text", "text": "Related tickets:", "marks": [{"type": "strong"}]},
            {"type": "hardBreak"}
        ]

        # Add each task URL as Jira inline link
        for task_url in task_urls:
            task_id = task_url.split('/')[-1]  # Extract CON-XXXXX from URL
            related_tickets_content.extend([
                {"type": "text", "text": "• "},
                {"type": "inlineCard", "attrs": {"url": task_url}},
                {"type": "text", "text": " "},
                {"type": "hardBreak"}
            ])

        new_paragraph = {
            "type": "paragraph",
            "content": related_tickets_content
        }

        # Update description
        if isinstance(current_description, dict) and 'content' in current_description:
            current_description['content'].append(new_paragraph)
        else:
            current_description = {
                "type": "doc",
                "version": 1,
                "content": [new_paragraph]
            }

        # Update the ticket with description
        if incomplete_tasks:
            # Set to In Progress if tasks are not done
            jira_client.update_ticket(current_key, current_description, status='In Progress')

            return {
                'success': True,
                'ticket_key': current_key,
                'status_set': 'In Progress',
                'reason': 'Some related tasks are not completed',
                'task_urls_added': task_urls,
                'task_count': len(task_urls),
                'incomplete_tasks': incomplete_tasks,
                'warning': f'{len(incomplete_tasks)} tasks are not in Done status'
            }
        else:
            # All tasks are done, just update description
            jira_client.update_ticket(current_key, current_description)

            return {
                'success': True,
                'ticket_key': current_key,
                'task_urls_added': task_urls,
                'task_count': len(task_urls),
                'all_tasks_done': True
            }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@mcp.tool()
def update_ticket_status(request: UpdateTicketStatusRequest) -> Dict[str, Any]:
    """
    Update ticket status to Approved and set label to Denim.

    Args:
        ticket_key: Jira ticket key (e.g., CON-25671)
        status: Target status (default: Approved)
        label: Label to add (default: Denim)

    Returns:
        Dictionary containing the update result
    """
    try:
        jira_client = JiraClient()

        # Get available transitions
        transitions_url = f"{jira_client.base_url}/rest/api/3/issue/{request.ticket_key}/transitions"

        response = requests.get(
            transitions_url,
            auth=(jira_client.username, jira_client.token),
            headers={'Accept': 'application/json'}
        )

        if response.status_code != 200:
            return {
                'success': False,
                'error': f'Failed to get transitions: {response.status_code} - {response.text}'
            }

        transitions = response.json().get('transitions', [])

        # Find transition to target status
        target_transition_id = None
        for transition in transitions:
            if transition['to']['name'].lower() == request.status.lower():
                target_transition_id = transition['id']
                break

        if not target_transition_id:
            available_statuses = [t['to']['name'] for t in transitions]
            return {
                'success': False,
                'error': f'No transition to {request.status} found. Available: {available_statuses}'
            }

        # Update label first
        update_url = f"{jira_client.base_url}/rest/api/3/issue/{request.ticket_key}"

        label_payload = {
            "fields": {
                "labels": [request.label]
            }
        }

        label_response = requests.put(
            update_url,
            json=label_payload,
            auth=(jira_client.username, jira_client.token),
            headers={'Accept': 'application/json', 'Content-Type': 'application/json'}
        )

        # Transition to target status
        transition_payload = {
            "transition": {
                "id": target_transition_id
            }
        }

        transition_response = requests.post(
            transitions_url,
            json=transition_payload,
            auth=(jira_client.username, jira_client.token),
            headers={'Accept': 'application/json', 'Content-Type': 'application/json'}
        )

        return {
            'success': True,
            'ticket_key': request.ticket_key,
            'status_updated': request.status,
            'label_added': request.label,
            'transition_id': target_transition_id,
            'label_update_status': label_response.status_code,
            'transition_status': transition_response.status_code
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# -----------------------------
# Entry Point
# -----------------------------
if __name__ == "__main__":
    mcp.run()