# Project State

## Phase
External connectivity spike execution (Task 1 complete, Task 2 blocked by missing credentials).

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
- Completed integration Task 2:
  - added SDK-free Slack runtime boundary in `app/slack_runtime.py`
  - converts Slack-like events to service request shape and service response to Slack-sendable payload
  - explicitly rejects malformed and unsupported events
  - tests in `tests/test_slack_runtime.py` (passing)
- Completed integration Task 3:
  - added thin Google Admin adapter boundary in `app/google_adapter.py`
  - maps SDK-like user payload to identity directory contract
  - returns `None` for user-not-found and maps transient client failures to `GoogleAdapterError`
  - tests in `tests/test_google_adapter.py` (passing)
- Completed integration Task 4:
  - added thin Notion API adapter boundary in `app/notion_adapter.py`
  - added ingestion entrypoint in `app/ingestion.py` that parses raw payloads via `parse_notion_page_metadata`
  - malformed/non-mapping payloads and missing page IDs are skipped safely with deterministic failure records
  - tests in `tests/test_notion_adapter.py` and `tests/test_ingestion.py` (passing)
- Completed integration Task 5:
  - added deterministic local flow composer in `app/local_flow.py`
  - composes Slack runtime boundary and service orchestration without duplicating business logic
  - validated authorized flow and safe empty-response flow when no authorized chunks remain
  - tests in `tests/test_local_flow.py` (passing)
- Completed integration Task 6:
  - added adapter failure tests in `tests/test_integration_failures.py`
  - validated explicit transient error mapping in Google and Notion adapter boundaries
  - added local-flow safe fallback to empty payload for malformed Slack events and adapter-boundary failures
  - tests in `tests/test_integration_failures.py` (passing)
- Completed integration Task 7 verification and sync:
  - focused integration command passes:
    `tests/test_integration_config.py tests/test_slack_runtime.py tests/test_google_adapter.py tests/test_notion_adapter.py tests/test_ingestion.py tests/test_local_flow.py tests/test_integration_failures.py`
  - full test suite passes: `pytest -v`
  - architecture and decisions synced to integration layer state
- Created external connectivity spike plan:
  - `docs/plans/2026-03-12-notionai-external-connectivity-spike.md`
  - defines read-only Google/Notion validation steps and required artifacts for contract verification
- Completed spike Task 1:
  - added placeholder contract baseline tests in `tests/spike/test_external_payload_contracts.py`
  - created spike notes in `docs/spike/2026-03-12-external-connectivity-notes.md`
  - baseline assumptions now captured explicitly for Google/Notion payload shapes
- Started spike Task 2 and created script:
  - added read-only script `scripts/spike/check_google_directory.py`
  - execution blocked before API calls due to missing credential configuration
  - blocker captured in spike notes

## Not Started
- Spike Task 3: Notion root ID/payload validation against real API data.
- Spike Task 4: mismatch triage and go/no-go recommendation.
- Slack app setup and event handling.
- Notion ingestion and indexing pipeline.

## Current Risks
- Need validated list of root page IDs for initial policies.
- Need Google OU path verification against real user set.
- Google credential/delegation setup for read-only directory checks is incomplete in this environment.
- Admin preparation checklist from the latest advisory step has not been executed yet.
- Runtime integrations (Slack transport, Notion crawling, production retrieval backend) are still pending.

## Next Session Entry Point
1. Finish Google spike Task 2 after providing credentials/delegation inputs.
2. Execute spike Task 3 for Notion root ID and payload validation.
3. Execute spike Task 4 mismatch triage and publish go/no-go recommendation before runtime wiring.
