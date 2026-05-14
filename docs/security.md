# Agent Smith Security Rules

Smith is designed to supervise automation systems safely. It must start with narrow permissions and grow only through explicit policy decisions.

---

## Core Rules

Smith must not:

1. Store secrets in GitHub.
2. Send secrets over Telegram.
3. Expose raw credentials in logs.
4. Delete files.
5. Publish content.
6. Send final deliverables.
7. Alter credentials.
8. Alter database schema without approved migrations.
9. Bypass human approval.
10. Execute disabled or deprecated tools.
11. Run experimental tools unless explicitly enabled.
12. Treat LLM output as permission authority.

---

## Telegram Access

Smith should only respond to allowlisted Telegram user IDs.

Unknown users should be rejected and logged without revealing system details.

---

## Permission Levels

```text
0 = Read-only observer
1 = Operator assistant
2 = Safe automation agent
3 = Production supervisor
4 = Development assistant
```

Smith v1 should default to level 0.

---

## Action Principle

All future action support should follow this pattern:

```text
request
→ authenticate
→ resolve context
→ check permission level
→ check action policy
→ ask for confirmation if required
→ execute safe action
→ record audit log
```

No action should be added without matching tests and audit logging.
