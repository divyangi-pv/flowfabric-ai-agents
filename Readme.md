# Version Support MCP Tools

This project contains **MCP (Model Context Protocol) tools** to help automate **version support triaging**.  
The first tool implemented is **`ticket.fetch`**, which fetches new version support tickets from Jira/ServiceNow.

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
git clone <repo-url>
cd version-support-mcp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

# Install dependencies (pinned for compatibility)
pip install --upgrade --force-reinstall -r requirements.txt
```

---

## ⚙️ Environment Variables

Copy the example file and update it with your Jira credentials:

```bash
cp .env.example .env
```

Example `.env` file:
```env
JIRA_URL=https://yourcompany.atlassian.net
JIRA_USER=your_email@example.com
JIRA_TOKEN=your_api_token
```

---

## ▶️ Run MCP Server

Start the MCP server:

```bash
python3 run_server.py
```

Expected output:
```
[MCP] Server 'version-support-assistant' started (listening on stdio)
```

Now your MCP tools are available to assistants like **Amazon Q Chat in IntelliJ** or **GitHub Copilot**.

---

## 🧪 Running Tests

We use **pytest** for testing.

Run all tests:
```bash
pytest -v
```

In IntelliJ:
- Mark `tests/` as *Test Sources Root*.
- Right-click → `Run 'pytest in tests/'`.

---
