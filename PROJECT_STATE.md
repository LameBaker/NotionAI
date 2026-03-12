# Project State

## Phase
MVP implementation in progress (Task 1 complete).

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

## Not Started
- Slack app setup and event handling.
- Notion ingestion and indexing pipeline.
- Google OU resolver.
- Notion metadata parsing.
- ACL-aware retrieval filtering.
- Slack response formatting.
- End-to-end orchestration.

## Current Risks
- Need validated list of root page IDs for initial policies.
- Need Google OU path verification against real user set.

## Next Session Entry Point
1. Validate Notion root page IDs for `HR` and `Development`.
2. Finalize `configs/access_policies.yaml` values.
3. Execute Task 3 (`app/identity.py`, `tests/test_identity.py`) with TDD.
