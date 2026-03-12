# Project State

## Phase
MVP implementation in progress (Task 4 complete).

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

## Not Started
- Slack app setup and event handling.
- Notion ingestion and indexing pipeline.
- ACL-aware retrieval filtering.
- Slack response formatting.
- End-to-end orchestration.

## Current Risks
- Need validated list of root page IDs for initial policies.
- Need Google OU path verification against real user set.

## Next Session Entry Point
1. Validate Notion root page IDs for `HR` and `Development`.
2. Finalize `configs/access_policies.yaml` values.
3. Execute Task 5 (`app/retrieval.py`, `tests/test_retrieval.py`) with TDD.
