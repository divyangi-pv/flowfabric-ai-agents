# FlowFabric AI Agents

This project contains **MCP (Model Context Protocol) tools** to help automate various workflows:

- **version-support-assistant**: Automate version support triaging
- **tests-triaging-assistant**: Handle nightly test results
- **release-signoff-assistant**: Manage release sign-off workflows

---

## 🐍 Install Python

1. **Check if Python is installed**
   ```bash
   python3 --version
   ```
   or on Windows:
   ```powershell
   python --version
   ```

2. **If not installed:**
    - **macOS** → Install via [python.org](https://www.python.org/downloads/) or Homebrew:
      ```bash
      brew install python@3.10
      ```
    - **Ubuntu/Debian**:
      ```bash
      sudo apt-get install python3.10 python3.10-venv python3-pip
      ```
    - **Windows** → Download from [python.org](https://www.python.org/downloads/windows/)  
      ✅ During installation, check **“Add Python to PATH”**.

> Recommended: **Python 3.10 or newer**

---

## 🚀 Setup Project

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/divyangi-pv/flowfabric-ai-agents.git
cd flowfabric-ai-agents

# Remove the existing broken venv
rm -rf venv

# Create a new virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Verify it's working
which python3
which pip3

# Install requirements
pip3 install --upgrade --force-reinstall -r requirements.txt
```

---

## ⚙️ Environment Variables

Copy the example file and update it with your credentials:

```bash
cp .env.example .env
```

Example `.env` file:
```env
# Jira Configuration (Required for Version Support Assistant)
JIRA_URL=https://yourcompany.atlassian.net
JIRA_USER=your_email@example.com
JIRA_TOKEN=your_api_token
```

### Getting Your Jira API Token

1. Log in to Jira and go to **Account Settings** → **Security**
2. Click **"Create and manage API tokens"**
3. Click **"Create API token"** and give it a name
4. **Copy the token** (shown only once) and add it to your `.env` file

⚠️ **Security Note**: Never commit your `.env` file to version control. It's already included in `.gitignore`.

---

## ▶️ Run MCP Server

Start the MCP server:

```bash
python3 run_server.py
```

Expected output:
```
[MCP] Server 'flowfabric-ai-agents' started (listening on stdio)
```

Now your MCP tools are available to assistants like **Amazon Q Chat in IntelliJ** or **GitHub Copilot**.

## 🔧 Available Tools

### Version Support Assistant
- `ticket.fetch` - Fetch version support tickets from Jira
- `ticket.comment` - Add comments to Jira tickets
- `ticket.accepted` - Update ticket status to Accepted
- `gerrit.create_pr` - Create Gerrit pull requests

### Tests Triaging Assistant
- 
- 

### Release Signoff Assistant
- `fetch_release_signoff_tickets` - Fetch release sign-off tickets from Jira
- `fetch_ticket` - Get specific ticket details by key
- `fetch_previous_version_ticket` - Find previous version ticket for comparison
- `update_ticket_with_previous_versions` - Update ticket with previous connector/SDK versions
- `get_commits_between_tags` - Get commits between previous and current version tags
- `update_ticket_with_task_urls` - Add related task URLs to release ticket
- `update_ticket_status` - Mark ticket as Done with Denim label

---

## 🧪 Running Tests

We use **pytest** for testing.

Run all tests:
```bash
pytest -v
```

Run specific test suites:
```bash
# Version Support Assistant tests (17 tests)
pytest tests/test_version_support.py -v

# Release Signoff Assistant tests (7 test classes)
pytest tests/test_release_signoff.py -v
```

### Test Coverage
- **Version Support Assistant**: Jira ticket operations, Gerrit PR creation, status updates
- **Release Signoff Assistant**: Version extraction, ticket fetching, Git commit analysis, workflow automation

In IntelliJ:
- Mark `tests/` as *Test Sources Root*.
- Right-click → `Run 'pytest in tests/'`.

---

## 🔧 Troubleshooting

### Common Issues

#### "Missing Jira credentials in .env"
- Ensure your `.env` file contains `JIRA_URL`, `JIRA_USER`, and `JIRA_TOKEN`
- Verify the API token is valid and hasn't expired
- Check that the Jira URL includes `https://` and the full domain

#### "Module not found" errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### MCP Server not responding
```bash
# Restart the server
python3 run_server.py

# Check for error messages in the output
```

#### Git/Gerrit push failures
- Verify SSH keys are configured for Gerrit access
- Ensure you have push permissions to the target branch
- Check that you're in a Git repository with staged changes

### Getting Help

- **Version Support Assistant**: See [detailed documentation](docs/version-support-assistant.md) for comprehensive troubleshooting
- **General Issues**: Check the project's issue tracker
- **Configuration**: Review the `.env.example` file for required variables

---
