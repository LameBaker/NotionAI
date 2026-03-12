# NotionAI External Connectivity Spike Plan

**Goal:** Prove or disprove external-system assumptions before runtime rollout.

**Scope:**
- Google Admin SDK access for user identity and `orgUnitPath`
- Notion API access for pilot root pages and page payload shapes
- Compatibility of real payloads with existing adapters/core contracts

**Out of Scope:**
- Slack runtime/server wiring
- Vector DB/retrieval backend
- Deployment/infrastructure automation

## Success Outputs (Required Artifacts)
- Verified Google OU examples (email -> `orgUnitPath`) for pilot users
- Verified Notion root page IDs for `HR` and `Development`
- Sample sanitized payload shapes from Google and Notion responses
- Explicit mismatch list against current contracts (`app/google_adapter.py`, `app/notion_adapter.py`, `app/notion_source.py`, `app/identity.py`)

## Task 1: Prepare spike harness and fixtures (TDD where possible)

**Files:**
- Create: `tests/spike/test_external_payload_contracts.py`
- Create: `docs/spike/2026-03-12-external-connectivity-notes.md`

1. Write failing fixture-driven tests for expected contract fields/shapes using representative sanitized payloads.
2. Add placeholder fixture examples from current assumptions; keep tests strict but minimal.
3. Run:
```bash
pytest tests/spike/test_external_payload_contracts.py -v
```
Expected: initial RED until fixtures/expectations are aligned.
4. Update fixture expectations to current contract baseline (no production code changes in this task).
5. Re-run same test to GREEN and capture baseline assumptions in spike notes.

## Task 2: Validate Google Admin SDK connectivity and OU assumptions (manual + reproducible script)

**Files:**
- Create: `scripts/spike/check_google_directory.py`
- Modify: `docs/spike/2026-03-12-external-connectivity-notes.md`

1. Add a small script that performs read-only user lookups for a provided email list and prints sanitized results (`primaryEmail`, `orgUnitPath` only).
2. Execute script manually against pilot users (no writes).
3. Record in notes:
- successful/failed lookups
- verified OU examples
- auth/connectivity errors (if any)
- payload shape deviations from adapter assumptions
4. If deviations exist, add failing spike test cases in `tests/spike/test_external_payload_contracts.py` (do not patch product code in spike).

## Task 3: Validate Notion API connectivity and pilot root IDs (manual + reproducible script)

**Files:**
- Create: `scripts/spike/check_notion_roots.py`
- Modify: `docs/spike/2026-03-12-external-connectivity-notes.md`

1. Add read-only script to fetch page payload samples for configured root IDs.
2. Verify candidate `HR` and `Development` root page IDs and record confirmed values.
3. Capture sanitized sample payload shapes relevant to current parser/adapter contracts.
4. Record errors and shape mismatches (missing fields, type differences, ACL property variability).
5. Add/adjust spike tests to codify discovered shape mismatches where appropriate.

## Task 4: Contract mismatch triage and go/no-go summary

**Files:**
- Modify: `docs/spike/2026-03-12-external-connectivity-notes.md`
- Modify: `PROJECT_STATE.md`
- Modify: `tasks/current_iteration.md`

1. Summarize compatibility status by boundary:
- Google adapter contract compatibility
- Notion adapter/parser contract compatibility
- Identity OU handling compatibility
2. Produce explicit mismatch list with severity:
- blocker (must fix before runtime wiring)
- warning (can proceed with caution)
3. Provide go/no-go recommendation for starting runtime wiring.
4. Update project state and iteration file with spike results and next concrete action.

## Verification Commands
- Contract tests only:
```bash
pytest tests/spike/test_external_payload_contracts.py -v
```
- Full suite smoke check (optional after spike artifacts stabilize):
```bash
pytest -v
```

## Stop Conditions
Stop spike execution and report immediately if:
- Google/Notion credentials are unavailable or invalid
- API access is denied for pilot scopes
- Root page IDs cannot be validated
- payload mismatches indicate current ACL guarantees are unsafe without code changes
