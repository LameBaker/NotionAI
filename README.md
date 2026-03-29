# NotionAI

Slack Q&A assistant over Notion with OU-based access control.

## Current Status
- Core domain and integration boundary layers are implemented and covered by tests.
- External connectivity spike is in progress:
  - Spike Task 1 completed (placeholder contract baseline + notes).
  - Spike Task 2 started and blocked (Google credentials not configured in session).
- Admin preparation checklist from the latest advisory message is not yet completed (credentials and pilot IDs still pending).

## Key Docs
- Execution rules: `EXECUTION_RULES.md`
- Design: `docs/plans/2026-03-12-notion-slack-qa-design.md`
- MVP implementation plan: `docs/plans/2026-03-12-notionai-mvp-implementation.md`
- Integration layer plan: `docs/plans/2026-03-12-notionai-integration-layer-implementation.md`
- External connectivity spike plan: `docs/plans/2026-03-12-notionai-external-connectivity-spike.md`
- Spike notes: `docs/spike/2026-03-12-external-connectivity-notes.md`
- Architecture: `docs/architecture.md`
- Project context: `PROJECT_CONTEXT.md`
- Project state: `PROJECT_STATE.md`
- Task tracking: `tasks/backlog.md`, `tasks/current_iteration.md`

## What Is Implemented
- ACL core: config loading, OU/user policy evaluation, deny-by-default behavior.
- Parsing and ingestion primitives: Notion metadata parser, ingestion entrypoint, deterministic failure capture.
- Retrieval safety: authorized chunk filtering before context assembly.
- Formatting/orchestration: transport-agnostic response formatter, service orchestration, local flow boundary.
- Integration boundaries: Slack runtime boundary, Google adapter, Notion adapter, integration config loader.
- Failure-handling safeguards for malformed events and transient adapter errors.

## Test Status
- Last recorded full run: `45 passed` (`.venv/bin/pytest -v`) during integration Task 7.

## Next Practical Steps
- Provide Google credentials and delegation inputs for spike scripts.
- Validate real Google OU outputs for pilot users.
- Validate real Notion root page IDs for `HR` and `Development`.
- Complete spike mismatch triage and go/no-go decision before runtime wiring.
