---
inclusion: false
---

# Version Support Strategy

This document defines decision rules for processing version support tickets. Follow these patterns when analyzing Jira tickets requesting connector version support.

## Decision Matrix by Tool

Use this lookup table to determine support strategy and infrastructure actions:

### GitLab Issues
- **Major**: Support=Test All, Infra=New Instance
- **Minor**: Support=Always Claim, Infra=Upgrade Latest Minor
- **Patch**: Support=Always Claim, Infra=None

### TestRail  
- **Major**: Support=Test All, Infra=New Instance
- **Minor**: Support=Test All, Infra=New Instance
- **Patch**: Support=Always Claim, Infra=None

### Digital.ai Agility
- **Major**: Support=Test Some (Update Existing), Infra=Upgrade on EOL
- **Minor**: Support=Always Claim (if OnDemand ≥ version), Infra=New Instance
- **Patch**: Support=Always Claim, Infra=None

### Broadcom Clarity
- **Major**: Support=Test All, Infra=New Instance
- **Minor**: Support=Test All (Update Existing), Infra=Upgrade Latest Minor
- **Patch**: Support=Always Claim, Infra=None

## Infrastructure Action Templates

### New Instance Required
Add this comment: "Please create a Samanage ticket to provision a new instance for [Connector Name] version [Version Number]"

### Upgrade Existing Instance  
Add this comment: "Please create a Samanage ticket to upgrade the existing instance to [Connector Name] version [Version Number]"

## Required Comment Template

Always use this exact format for Jira comments:

```
## Version Support Strategy Analysis

**Tool**: [Tool Name]
**Current Version Tested**: [Current Version from fixtures]
**Requested Version**: [New Version]
**Version Change Type**: [Major/Minor/Patch]

**Support Strategy**: [Test All/Test Some/Always Claim Support]
**Infrastructure Action**: [New Instance/Upgrade/None]

**Samanage Ticket Required**: [Yes/No]
[If Yes, include infrastructure template above]

**Recommendation**: [Accept/Requires Testing/Infrastructure Setup Needed]
```

## Processing Workflow

Follow this exact sequence for each ticket:

1. **Parse ticket summary** to extract tool name and requested version
2. **Look up current version** from fixture files in the codebase
3. **Classify version change** as Major (X.0.0), Minor (0.X.0), or Patch (0.0.X)
4. **Apply decision matrix** from tool-specific rules above
5. **Add strategy comment** using the required template
6. **Take action**: Accept ticket

## Automation Decision Rules

### Immediately Accept (use `ticket.accepted`)
- **All patch versions** (0.0.X changes) for any tool
- **Minor versions** for GitLab Issues (Always Claim policy)
- **Minor versions** for Digital.ai Agility when OnDemand instance ≥ requested version

### Requires Infrastructure Setup (use `ticket.accepted`)
- **Major versions** requiring "New Instance"
- **Minor versions** requiring "Upgrade Latest Minor" or "New Instance"

### Requires Testing (use `ticket.accepted`) 
- **Major versions** with "Test All" strategy (GitLab Issues, TestRail, Broadcom Clarity)
- **Minor versions** with "Test All" strategy (TestRail, Broadcom Clarity)
- **Major versions** with "Test Some" strategy (Digital.ai Agility)

## MCP Tool Integration Pattern

Use this sequence with version support assistant tools:

1. `mcp_version_support_assistant_ticketfetch` - Get "To Triage" tickets
2. For each ticket: Apply decision matrix and add comment using `mcp_version_support_assistant_ticketcomment`
3. For auto-accept tickets: Use `mcp_version_support_assistant_ticketaccepted`
4. For configuration changes: Use `mcp_version_support_assistant_gerritcreate_pr`

## Key Patterns for AI Assistant

- **Always comment first** before accepting any ticket
- **Use exact template format** for consistency
- **Check fixture files** to determine current tested versions
- **Parse version numbers** correctly (semantic versioning: MAJOR.MINOR.PATCH)
- **Match tool names** case-insensitively from ticket summaries
- **Include Samanage instructions** when infrastructure actions are required