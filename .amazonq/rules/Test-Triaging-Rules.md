# Build Triaging Rules

## Rule 1: Validate Build Status
- Check whether the **last Jenkins build** has passed.
- If the build failed → return error: `"Build failed. Triaging cannot proceed."`
- If passed → proceed to test failure analysis.

---

## Rule 2: Group Jenkins Test Failures
- Collect all Jenkins test failures.
- Group failures based on:
    - **Error Message**
    - **Stack Trace**
    - **Standard Output**

---

## Rule 3: Compare with Jira Issues
- Fetch all existing Jira issues related to build failures.
- Match grouped Jenkins failures against existing Jira tickets.

---

## Rule 4: Update Existing Tickets
- If a corresponding Jira ticket **already exists**:
    - Update the **last seen date** to the today's date.

---

## Rule 5: Create New Tickets
- If no corresponding Jira ticket exists:
    - Create a **new Jira ticket** using the build issue template (see Rule 8).
    - Only one ticket per grouped issue.
    - If a similar issue already exists:
        - Update the **description** of the existing ticket instead of creating a new one.

---

## Rule 6: Handle Done Tickets
- If a Jira ticket is marked as **Done** but the same issue reoccurs in Jenkins:
    - Change ticket status to **Triage**
    - Update **last seen date** to the current date.

---

## Rule 7: Ticket Creation Format
- **Title Format**:  
  `<Component-Name> - One line summary about failure`
- **Test Affected Format**:  
  `Testcase with Fixture name and AC`  
  Example:  
  `com.tasktop.connector.leankit.auth.AuthenticationTest.validateUserCredentials[Agile Place - OAuth 2.0 - Story, ACs=12.1.1, 12.1.2]`
- **Failure Message**:  
  Exact grouped error details from Jenkins result.
- **Stack Trace**:  
  Stack trace from Jenkins result.

---

## Rule 8: Add Ticket Comments
- On every **newly created Jira ticket**, add a comment with:
    - **Failed API** with response message and error code (from standard output)
    - **Possible reason** for the failure
    - **Possible solutions** for the failure
