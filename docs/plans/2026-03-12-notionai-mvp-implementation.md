# NotionAI MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build MVP of a single Slack Q&A bot over Notion with OU-based ACL and deny-by-default filtering.

**Architecture:** Implement a small service with integration adapters (Slack, Google Admin SDK, Notion), a deterministic policy engine, ACL-aware retrieval, and response formatting with source metadata. Keep policy data in YAML root rules plus optional Notion page-level ACL tags.

**Tech Stack:** Python service, pytest, Slack SDK, Google Admin SDK client, Notion API client, vector store (to be chosen during execution).

---

### Task 1: Bootstrap runtime skeleton

**Files:**
- Create: `app/__init__.py`
- Create: `app/config.py`
- Create: `app/models.py`
- Create: `tests/test_config.py`

**Step 1: Write the failing test**
Add config-load tests for `configs/access_policies.yaml` and deny-by-default requirement.

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_config.py -v`
Expected: FAIL due to missing module/functions.

**Step 3: Write minimal implementation**
Implement typed config loader and validation checks.

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_config.py -v`
Expected: PASS.

**Step 5: Commit**
Run:
```bash
git add app/__init__.py app/config.py app/models.py tests/test_config.py
git commit -m "feat: add config loader and validation"
```

### Task 2: Implement ACL policy evaluator

**Files:**
- Create: `app/policy.py`
- Create: `tests/test_policy.py`

**Step 1: Write the failing test**
Cover cases:
- root allow by OU prefix
- root allow by user email
- deny when unmatched
- `acl_restricted` requiring explicit allows
- `acl_allow_*` expansion without restricted mode

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_policy.py -v`
Expected: FAIL.

**Step 3: Write minimal implementation**
Implement deterministic evaluator with documented precedence.

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_policy.py -v`
Expected: PASS.

**Step 5: Commit**
Run:
```bash
git add app/policy.py tests/test_policy.py
git commit -m "feat: add acl policy evaluator"
```

### Task 3: Add Google OU resolver

**Files:**
- Create: `app/identity.py`
- Create: `tests/test_identity.py`

**Step 1: Write the failing test**
Mock Google Admin SDK response and validate `orgUnitPath` extraction by email.

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_identity.py -v`
Expected: FAIL.

**Step 3: Write minimal implementation**
Add resolver interface + SDK-backed implementation + test double support.

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_identity.py -v`
Expected: PASS.

**Step 5: Commit**
Run:
```bash
git add app/identity.py tests/test_identity.py
git commit -m "feat: add google ou resolver"
```

### Task 4: Add Notion ingestion metadata model

**Files:**
- Create: `app/notion_source.py`
- Create: `tests/test_notion_source.py`

**Step 1: Write the failing test**
Validate extraction of:
- page id
- parent linkage/path
- last edited time
- ACL tags (`acl_restricted`, `acl_allow_ou`, `acl_allow_users`)

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_notion_source.py -v`
Expected: FAIL.

**Step 3: Write minimal implementation**
Implement parser/adapters from Notion API payload to internal page model.

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_notion_source.py -v`
Expected: PASS.

**Step 5: Commit**
Run:
```bash
git add app/notion_source.py tests/test_notion_source.py
git commit -m "feat: add notion ingestion metadata parsing"
```

### Task 5: Add ACL-aware retrieval filter

**Files:**
- Create: `app/retrieval.py`
- Create: `tests/test_retrieval.py`

**Step 1: Write the failing test**
Ensure unauthorized chunks are excluded before context assembly.

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_retrieval.py -v`
Expected: FAIL.

**Step 3: Write minimal implementation**
Implement retrieval wrapper that intersects search results with allowed pages.

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_retrieval.py -v`
Expected: PASS.

**Step 5: Commit**
Run:
```bash
git add app/retrieval.py tests/test_retrieval.py
git commit -m "feat: add acl-aware retrieval filtering"
```

### Task 6: Add Slack response formatter

**Files:**
- Create: `app/slack_adapter.py`
- Create: `tests/test_slack_adapter.py`

**Step 1: Write the failing test**
Validate response includes:
- answer text
- source metadata (title/path/last_edited/page_id)
- no raw unauthorized references

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_slack_adapter.py -v`
Expected: FAIL.

**Step 3: Write minimal implementation**
Implement message formatting contract for Slack blocks/text.

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_slack_adapter.py -v`
Expected: PASS.

**Step 5: Commit**
Run:
```bash
git add app/slack_adapter.py tests/test_slack_adapter.py
git commit -m "feat: add slack response formatting"
```

### Task 7: Wire end-to-end orchestration

**Files:**
- Create: `app/service.py`
- Create: `tests/test_service.py`
- Modify: `PROJECT_STATE.md`

**Step 1: Write the failing test**
Test end-to-end flow:
- Slack user -> email -> OU
- ACL compute
- retrieval filter
- answer output with metadata

**Step 2: Run test to verify it fails**
Run: `pytest tests/test_service.py -v`
Expected: FAIL.

**Step 3: Write minimal implementation**
Implement orchestrator using previously built interfaces.

**Step 4: Run test to verify it passes**
Run: `pytest tests/test_service.py -v`
Expected: PASS.

**Step 5: Commit**
Run:
```bash
git add app/service.py tests/test_service.py PROJECT_STATE.md
git commit -m "feat: wire mvp service orchestration"
```

### Task 8: Final verification and docs sync

**Files:**
- Modify: `docs/architecture.md`
- Modify: `DECISIONS.md`
- Modify: `tasks/current_iteration.md`
- Modify: `PROJECT_STATE.md`

**Step 1: Run focused tests**
Run:
```bash
pytest tests/test_config.py tests/test_policy.py tests/test_identity.py tests/test_notion_source.py tests/test_retrieval.py tests/test_slack_adapter.py tests/test_service.py -v
```
Expected: PASS.

**Step 2: Run full test suite**
Run: `pytest -v`
Expected: PASS.

**Step 3: Sync docs/state**
Update docs and task status to reflect implemented behavior and known gaps.

**Step 4: Commit**
Run:
```bash
git add docs/architecture.md DECISIONS.md tasks/current_iteration.md PROJECT_STATE.md
git commit -m "docs: finalize mvp implementation status"
```
