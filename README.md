# NotionAI

Planning-first repository for building a Slack Q&A assistant over Notion with OU-based access control.

## Current Status
- Architecture and ACL model are defined.
- Project is scaffolded for execution in a separate coding session.
- No product runtime implementation yet.

## Key Docs
- Execution rules: `EXECUTION_RULES.md`
- Design: `docs/plans/2026-03-12-notion-slack-qa-design.md`
- Architecture: `docs/architecture.md`
- Project context: `PROJECT_CONTEXT.md`
- Project state: `PROJECT_STATE.md`
- Task tracking: `tasks/backlog.md`, `tasks/current_iteration.md`

## Principles
- Single Slack bot.
- OU-based access control from Google Workspace.
- Deny-by-default.
- Filter unauthorized content before LLM prompt assembly.
