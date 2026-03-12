# Project State

## Phase
Integration layer implementation in progress (Task 1 complete).

## Completed
- Agreed architecture for single-bot MVP.
- Agreed ACL semantics:
  - default deny
  - root allow policies
  - optional Notion page overrides
- Created repository planning scaffold.
- Implemented runtime skeleton for Task 1:
  - typed policy models in `app/models.py`
  - YAML config loader with deny-by-default validation in `app/config.py`
  - config tests in `tests/test_config.py` (passing)
- Implemented ACL policy evaluator for Task 2:
  - deterministic allow/deny evaluation in `app/policy.py`
  - policy behavior tests in `tests/test_policy.py` (passing)
- Implemented Google OU resolver for Task 3:
  - client-agnostic resolver interface in `app/identity.py`
  - org unit path normalization and corporate-email-only lookup
  - identity tests in `tests/test_identity.py` (passing)
- Implemented Notion metadata parsing for Task 4:
  - raw-payload metadata parser in `app/notion_source.py`
  - extracted MVP fields: page id, parent linkage, title, path, last edited time, and ACL tags
  - safe ACL defaults when properties are absent
  - tests in `tests/test_notion_source.py` (passing)
- Implemented ACL-aware retrieval filtering for Task 5:
  - in-memory chunk model in `app/retrieval.py`
  - deterministic filtering by allowed page ids before context assembly
  - explicit deny-by-default behavior when allowed set is empty
  - tests in `tests/test_retrieval.py` (passing)
- Implemented Slack response formatting for Task 6:
  - transport-agnostic formatter in `app/slack_adapter.py`
  - output includes answer text and safe source metadata only
  - unsafe/raw fields are dropped from source items
  - tests in `tests/test_slack_adapter.py` (passing)
- Implemented service orchestration for Task 7:
  - dependency-injected orchestrator in `app/service.py`
  - wired identity resolution, ACL evaluation, retrieval filtering/context assembly, and response formatting
  - returns safe empty response shape when no authorized chunks remain
  - tests in `tests/test_service.py` (passing)
- Completed Task 8 verification and sync:
  - focused command passes: `tests/test_config.py tests/test_policy.py tests/test_identity.py tests/test_notion_source.py tests/test_retrieval.py tests/test_slack_adapter.py tests/test_service.py`
  - full suite passes: `pytest -v`
  - architecture, decisions, and iteration/state docs refreshed
- Created next-phase integration plan:
  - `docs/plans/2026-03-12-notionai-integration-layer-implementation.md`
  - task-by-task TDD sequence for Slack runtime, Google adapter, Notion adapter/ingestion, config/env, local flow, and failure handling
- Completed integration Task 1:
  - added env-only integration config loader in `app/integration_config.py`
  - explicit required env validation outside local mode
  - safe minimal local-mode defaults (empty tokens/ids)
  - tests in `tests/test_integration_config.py` (passing)

## Not Started
- Slack app setup and event handling.
- Notion ingestion and indexing pipeline.

## Current Risks
- Need validated list of root page IDs for initial policies.
- Need Google OU path verification against real user set.
- Runtime integrations (Slack transport, Notion crawling, production retrieval backend) are still pending.

## Next Session Entry Point
1. Execute Task 2 from `docs/plans/2026-03-12-notionai-integration-layer-implementation.md`.
2. Continue integration tasks sequentially with TDD and ACL-safety checks.
3. Keep runtime wiring transport-adapter-only (no production deployment scope).
