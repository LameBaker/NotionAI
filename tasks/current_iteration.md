# Current Iteration

## Objective
Prepare and execute an external connectivity spike to validate Google/Notion real-world assumptions before runtime wiring.

## Tasks
- [x] Finalize MVP architecture and ACL model.
- [x] Write design document in `docs/plans/`.
- [ ] Validate real Notion root IDs for `HR` and `Development`.
- [ ] Validate Google OU paths for pilot users.
- [ ] Create implementation plan file for coding session.
- [x] Implement Task 1 runtime skeleton (`app/__init__.py`, `app/config.py`, `app/models.py`, `tests/test_config.py`).
- [x] Implement Task 2 ACL policy evaluator (`app/policy.py`, `tests/test_policy.py`).
- [x] Implement Task 3 Google OU resolver (`app/identity.py`, `tests/test_identity.py`).
- [x] Implement Task 4 Notion metadata parsing (`app/notion_source.py`, `tests/test_notion_source.py`).
- [x] Implement Task 5 ACL-aware retrieval filtering (`app/retrieval.py`, `tests/test_retrieval.py`).
- [x] Implement Task 6 Slack response formatting (`app/slack_adapter.py`, `tests/test_slack_adapter.py`).
- [x] Implement Task 7 service orchestration (`app/service.py`, `tests/test_service.py`).
- [x] Run Task 8 focused verification command.
- [x] Run Task 8 full test suite.
- [x] Sync docs/state (`docs/architecture.md`, `DECISIONS.md`, `tasks/current_iteration.md`, `PROJECT_STATE.md`).
- [x] Create integration layer implementation plan (`docs/plans/2026-03-12-notionai-integration-layer-implementation.md`).
- [x] Implement Task 1 integration config/env loader (`app/integration_config.py`, `tests/test_integration_config.py`).
- [x] Implement Task 2 Slack runtime adapter boundary (`app/slack_runtime.py`, `tests/test_slack_runtime.py`).
- [x] Implement Task 3 Google adapter boundary (`app/google_adapter.py`, `tests/test_google_adapter.py`).
- [x] Implement Task 4 Notion adapter and ingestion entrypoint (`app/notion_adapter.py`, `app/ingestion.py`, `tests/test_notion_adapter.py`, `tests/test_ingestion.py`).
- [x] Implement Task 5 local integration flow (`app/local_flow.py`, `tests/test_local_flow.py`).
- [x] Implement Task 6 adapter failure handling (`tests/test_integration_failures.py`, updates to adapter boundaries/local flow).
- [x] Run Task 7 focused integration verification command.
- [x] Run Task 7 full test suite.
- [x] Sync docs/state (`docs/architecture.md`, `DECISIONS.md`, `tasks/current_iteration.md`, `PROJECT_STATE.md`).
- [x] Create external connectivity spike plan (`docs/plans/2026-03-12-notionai-external-connectivity-spike.md`).
- [ ] Execute spike Task 1 (contract fixtures/tests + notes scaffold).
- [ ] Execute spike Task 2 (Google connectivity + OU verification artifacts).
- [ ] Execute spike Task 3 (Notion root ID/payload verification artifacts).
- [ ] Execute spike Task 4 (mismatch triage + go/no-go summary).

## Exit Criteria
- Verified OU examples are captured.
- Verified Notion root page IDs are captured.
- Sanitized payload samples and contract mismatches are documented.
- Go/no-go recommendation for runtime wiring is documented.
