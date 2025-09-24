# Version Support Assistant - MCP Tools Documentation

The Version Support Assistant provides four MCP tools to automate Jira ticket management and Gerrit integration for version support workflows.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [MCP Tools](#mcp-tools)
  - [ticket.fetch](#ticketfetch)
  - [ticket.comment](#ticketcomment)
  - [ticket.accepted](#ticketaccepted)
  - [gerrit.create_pr](#gerritcreate_pr)
- [Error Handling](#error-handling)
- [Troubleshooting](#troubleshooting)

## Overview

The Version Support Assistant streamlines the version support ticket triaging workflow by providing automated interactions with Jira and Gerrit. It enables AI assistants to:

- Fetch and filter version support tickets from Jira
- Add comments to tickets for communication and updates
- Update ticket status to move them through the workflow
- Create Gerrit pull requests with properly formatted commit messages

## Prerequisites

### Software Requirements

- Python 3.10 or newer
- Git configured with authentication
- Access to Jira instance with API token
- Gerrit repository access (for PR creation)

### Python Dependencies

The following packages are required (installed via `requirements.txt`):

```
fastmcp>=0.2.0
httpx>=0.25.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Jira Configuration
JIRA_URL=https://yourcompany.atlassian.net
JIRA_USER=your_email@example.com
JIRA_TOKEN=your_api_token
```

### Jira API Token Setup

1. **Log in to Jira** using your web browser
2. **Go to Account Settings** → Click your profile picture → "Account settings"
3. **Navigate to Security** → Click "Security" in the left sidebar
4. **Create API Token** → Click "Create and manage API tokens"
5. **Generate Token** → Click "Create API token"
6. **Name your token** (e.g., "MCP Version Support Assistant")
7. **Copy the token** and add it to your `.env` file as `JIRA_TOKEN`

⚠️ **Important**: API tokens are only shown once. Store it securely in your `.env` file.

### Git/Gerrit Configuration

Ensure Git is configured with your credentials:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@company.com"
```

For Gerrit, ensure you have:
- SSH keys configured for your Gerrit instance
- Proper repository access permissions
- Gerrit remote configured in your repository

## MCP Tools

### ticket.fetch

Fetches version support tickets from Jira based on specified criteria.

#### Parameters

```typescript
interface TicketFetchInput {
  type?: string;    // Default: "Version Support"
  status?: string;  // Default: "To Triage"  
  limit?: number;   // Default: 100
}
```

#### Response

```typescript
interface TicketFetchOutput {
  tickets: TicketOutput[];
}

interface TicketOutput {
  id: string;              // Jira ticket key (e.g., "CON-12345")
  summary: string;         // Ticket title/summary
  status: string;          // Current status name
  assignee: string | null; // Assignee display name or null
  created: string;         // ISO timestamp of creation
  releaseNotes: string | null; // Extracted release notes URL or null
}
```

#### Usage Examples

**Fetch default tickets (Version Support, To Triage, limit 100):**
```json
{
  "type": "Version Support",
  "status": "To Triage",
  "limit": 100
}
```

**Fetch specific ticket type with custom limit:**
```json
{
  "type": "Bug",
  "status": "In Progress", 
  "limit": 50
}
```

**Fetch all tickets of a type:**
```json
{
  "type": "Version Support",
  "status": "To Triage",
  "limit": 1000
}
```

#### Example Response

```json
{
  "tickets": [
    {
      "id": "CON-12345",
      "summary": "Support for version 2.1.0 in production environment",
      "status": "To Triage",
      "assignee": "John Doe",
      "created": "2024-01-15T10:30:00.000Z",
      "releaseNotes": "https://docs.company.com/releases/v2.1.0"
    },
    {
      "id": "CON-12346", 
      "summary": "Version compatibility issue with legacy systems",
      "status": "To Triage",
      "assignee": null,
      "created": "2024-01-14T14:22:00.000Z",
      "releaseNotes": null
    }
  ]
}
```

### ticket.comment

Adds a comment to a specified Jira ticket.

#### Parameters

```typescript
interface CommentInput {
  ticket_id: string;  // Jira ticket key (e.g., "CON-12345")
  comment: string;    // Comment text to add
}
```

#### Response

```typescript
interface CommentOutput {
  success: boolean;
  comment_id?: string;  // Jira comment ID if successful
  error?: string;       // Error message if failed
}
```

#### Usage Examples

**Add status update comment:**
```json
{
  "ticket_id": "CON-12345",
  "comment": "Ticket has been reviewed and approved for version 2.1.0 deployment. Moving to implementation phase."
}
```

**Add technical details:**
```json
{
  "ticket_id": "CON-12346",
  "comment": "Technical analysis complete. Compatibility issues identified with legacy API endpoints. Recommended approach: implement backward compatibility layer."
}
```

#### Example Responses

**Success:**
```json
{
  "success": true,
  "comment_id": "10001"
}
```

**Error:**
```json
{
  "success": false,
  "error": "Issue does not exist or you do not have permission to see it."
}
```

### ticket.accepted

Updates a Jira ticket status to "Accepted" by triggering the appropriate workflow transition.

#### Parameters

```typescript
interface StatusUpdateInput {
  ticket_id: string;  // Jira ticket key (e.g., "CON-12345")
}
```

#### Response

```typescript
interface StatusUpdateOutput {
  success: boolean;
  error?: string;  // Error message if failed
}
```

#### Usage Examples

**Accept a triaged ticket:**
```json
{
  "ticket_id": "CON-12345"
}
```

#### Example Responses

**Success:**
```json
{
  "success": true
}
```

**Error:**
```json
{
  "success": false,
  "error": "Transition 'Accept' is not available for this issue."
}
```

### gerrit.create_pr

Creates a Gerrit pull request by committing staged changes and pushing to Gerrit for review.

#### Parameters

```typescript
interface GerritPRInput {
  ticket_id: string;     // Jira ticket key for commit message
  description: string;   // Description of changes
  branch?: string;       // Target branch (default: "master")
  repo_path?: string;    // Repository path (default: ".")
}
```

#### Response

```typescript
interface GerritPROutput {
  success: boolean;
  change_id?: string;  // Gerrit Change-Id if successful
  error?: string;      // Error message if failed
}
```

#### Usage Examples

**Create PR for version support fix:**
```json
{
  "ticket_id": "CON-12345",
  "description": "Add backward compatibility layer for legacy API endpoints",
  "branch": "develop",
  "repo_path": "/path/to/repository"
}
```

**Create PR in current directory:**
```json
{
  "ticket_id": "CON-12346", 
  "description": "Update version validation logic for 2.1.0 support"
}
```

#### Commit Message Format

The tool automatically formats commit messages as:

```
CON-12345 : Add backward compatibility layer for legacy API endpoints

Task-Url: https://tasktop.atlassian.net/browse/CON-12345
```

#### Example Responses

**Success:**
```json
{
  "success": true,
  "change_id": "I1234567890abcdef1234567890abcdef12345678"
}
```

**Error:**
```json
{
  "success": false,
  "error": "Git command failed: fatal: remote origin already exists."
}
```

## Error Handling

### Common Error Categories

#### Configuration Errors

**Missing Environment Variables:**
- **Error**: `"Missing Jira credentials in .env"`
- **Solution**: Ensure `JIRA_URL`, `JIRA_USER`, and `JIRA_TOKEN` are set in `.env` file

#### Authentication Errors

**Invalid Jira Credentials:**
- **Error**: `"401 Unauthorized"`
- **Solution**: Verify API token is valid and user has proper permissions

**Expired API Token:**
- **Error**: `"401 Unauthorized"` 
- **Solution**: Generate new API token in Jira account settings

#### API Errors

**Ticket Not Found:**
- **Error**: `"Issue does not exist or you do not have permission to see it"`
- **Solution**: Verify ticket ID exists and user has view permissions

**Invalid Transition:**
- **Error**: `"Transition 'Accept' is not available for this issue"`
- **Solution**: Check ticket's current status allows the transition

#### Git/Gerrit Errors

**Repository Not Found:**
- **Error**: `"Git command failed: fatal: not a git repository"`
- **Solution**: Ensure command is run from within a Git repository

**Push Permission Denied:**
- **Error**: `"Git command failed: Permission denied (publickey)"`
- **Solution**: Verify SSH keys are configured for Gerrit access

**No Changes to Commit:**
- **Error**: `"Git command failed: nothing to commit, working tree clean"`
- **Solution**: Stage changes before creating PR

### Error Response Format

All tools return errors in a consistent format:

```json
{
  "success": false,
  "error": "Descriptive error message"
}
```

Error messages are designed to be:
- **Descriptive**: Clearly explain what went wrong
- **Actionable**: Provide guidance on how to resolve the issue
- **Secure**: Don't expose sensitive information like tokens or passwords

## Troubleshooting

### Setup Issues

#### "Module not found" errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### Environment variables not loading
```bash
# Verify .env file exists and has correct format
cat .env

# Check file permissions
ls -la .env
```

### Jira Integration Issues

#### API Token Authentication Fails

1. **Verify token validity**:
   ```bash
   curl -u your_email@example.com:your_api_token \
     https://yourcompany.atlassian.net/rest/api/3/myself
   ```

2. **Check token permissions**: Ensure the token has appropriate project access

3. **Verify Jira URL format**: Should include `https://` and full domain

#### JQL Query Issues

- **Invalid project key**: Verify project exists and you have access
- **Invalid field names**: Check Jira field configuration
- **Permission errors**: Ensure user can view tickets in the project

### Git/Gerrit Integration Issues

#### SSH Key Problems

1. **Test SSH connection**:
   ```bash
   ssh -T git@your-gerrit-server.com
   ```

2. **Add SSH key to agent**:
   ```bash
   ssh-add ~/.ssh/id_rsa
   ```

#### Gerrit Push Issues

1. **Verify remote configuration**:
   ```bash
   git remote -v
   ```

2. **Check branch permissions**: Ensure you can push to target branch

3. **Verify Change-Id hook**: Gerrit requires Change-Id in commit messages

#### Repository State Issues

1. **Check working directory status**:
   ```bash
   git status
   ```

2. **Verify staged changes**:
   ```bash
   git diff --cached
   ```

### Performance Issues

#### Slow Ticket Fetching

- **Reduce limit parameter**: Use smaller values for faster responses
- **Optimize JQL queries**: Add more specific filters
- **Check Jira instance performance**: Contact Jira administrators

#### Network Timeouts

- **Check network connectivity**: Verify access to Jira and Gerrit
- **Increase timeout values**: Modify httpx client configuration
- **Use VPN if required**: Some corporate networks require VPN access

### Debugging Tips

#### Enable Verbose Logging

Add logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Test Individual Components

1. **Test Jira connection**:
   ```python
   import httpx
   import os
   from dotenv import load_dotenv
   
   load_dotenv()
   auth = (os.getenv("JIRA_USER"), os.getenv("JIRA_TOKEN"))
   
   with httpx.Client(auth=auth) as client:
       resp = client.get(f"{os.getenv('JIRA_URL')}/rest/api/3/myself")
       print(resp.status_code, resp.json())
   ```

2. **Test Git operations**:
   ```bash
   git add .
   git commit -m "Test commit"
   git log --oneline -1
   ```

#### Common Resolution Steps

1. **Restart MCP server** after configuration changes
2. **Clear Python cache**: `rm -rf __pycache__`
3. **Recreate virtual environment** if dependency issues persist
4. **Check system resources**: Ensure adequate memory and disk space
5. **Verify network connectivity** to external services

For additional support, check the project's issue tracker or contact the development team.