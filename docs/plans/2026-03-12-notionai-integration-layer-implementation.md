# NotionAI Integration Layer Implementation Plan

**Goal:** Integrate runtime adapters around the existing MVP core without changing core ACL/domain guarantees.

**Scope:**
- Slack runtime adapter
- Google Admin SDK adapter
- Notion API adapter + ingestion entrypoint
- Integration config/env handling
- Minimal local end-to-end execution flow
- Adapter boundary and failure-handling tests

**Out of Scope:**
- Production deployment
- Background worker scaling/perf tuning
- Infrastructure automation

## Guardrails
- Keep transport adapters separate from domain logic (`app/service.py`, `app/policy.py`, etc.).
- ACL filtering must remain before context assembly.
- Unauthorized content must never enter answer context.
- Preserve deny-by-default when identity/policy/metadata is missing or ambiguous.
- Use TDD for every task (failing test first).

---

### Task 1: Add integration config/env loader

**Files:**
- Create: `app/integration_config.py`
- Create: `tests/test_integration_config.py`

**Step 1: Write failing tests**
Cover:
- required env values for Slack, Google Workspace, Notion
- explicit validation errors for missing values
- optional local-mode defaults (safe values only)

**Step 2: Verify RED**
Run:
```bash
pytest tests/test_integration_config.py -v
```
Expected: FAIL.

**Step 3: Minimal implementation**
Implement typed config object + env parsing + validation.

**Step 4: Verify GREEN**
Run:
```bash
pytest tests/test_integration_config.py -v
```
Expected: PASS.

**Step 5: Commit**
```bash
git add app/integration_config.py tests/test_integration_config.py
git commit -m "feat: add integration config env loader"
```

---

### Task 2: Add Slack runtime adapter boundary

**Files:**
- Create: `app/slack_runtime.py`
- Create: `tests/test_slack_runtime.py`

**Step 1: Write failing tests**
Cover:
- conversion from Slack-like event payload to service request input (`user_email`, `question`)
- conversion from service response payload to Slack-sendable payload structure
- rejection/ignore behavior for malformed or unsupported events

**Step 2: Verify RED**
Run:
```bash
pytest tests/test_slack_runtime.py -v
```
Expected: FAIL.

**Step 3: Minimal implementation**
Implement SDK-free runtime adapter contract with injectable send/lookup functions.

**Step 4: Verify GREEN**
Run:
```bash
pytest tests/test_slack_runtime.py -v
```
Expected: PASS.

**Step 5: Commit**
```bash
git add app/slack_runtime.py tests/test_slack_runtime.py
git commit -m "feat: add slack runtime adapter boundary"
```

---

### Task 3: Add Google Admin SDK adapter boundary

**Files:**
- Create: `app/google_adapter.py`
- Create: `tests/test_google_adapter.py`

**Step 1: Write failing tests**
Cover:
- adapter maps SDK-like user payload to directory client contract used by `app/identity.py`
- user-not-found behavior returns `None`
- adapter error mapping for transient SDK failures

**Step 2: Verify RED**
Run:
```bash
pytest tests/test_google_adapter.py -v
```
Expected: FAIL.

**Step 3: Minimal implementation**
Implement small adapter with injected SDK client interface.

**Step 4: Verify GREEN**
Run:
```bash
pytest tests/test_google_adapter.py -v
```
Expected: PASS.

**Step 5: Commit**
```bash
git add app/google_adapter.py tests/test_google_adapter.py
git commit -m "feat: add google admin adapter boundary"
```

---

### Task 4: Add Notion API adapter and ingestion entrypoint

**Files:**
- Create: `app/notion_adapter.py`
- Create: `app/ingestion.py`
- Create: `tests/test_notion_adapter.py`
- Create: `tests/test_ingestion.py`

**Step 1: Write failing tests**
Cover:
- adapter fetches page-like payloads through injected Notion client interface
- ingestion entrypoint converts raw payloads through `parse_notion_page_metadata`
- ingestion excludes malformed pages safely and records parse failures

**Step 2: Verify RED**
Run:
```bash
pytest tests/test_notion_adapter.py tests/test_ingestion.py -v
```
Expected: FAIL.

**Step 3: Minimal implementation**
Implement adapter + ingestion entrypoint without crawling/pagination complexity.

**Step 4: Verify GREEN**
Run:
```bash
pytest tests/test_notion_adapter.py tests/test_ingestion.py -v
```
Expected: PASS.

**Step 5: Commit**
```bash
git add app/notion_adapter.py app/ingestion.py tests/test_notion_adapter.py tests/test_ingestion.py
git commit -m "feat: add notion adapter and ingestion entrypoint"
```

---

### Task 5: Add local integration flow wiring

**Files:**
- Create: `app/local_flow.py`
- Create: `tests/test_local_flow.py`

**Step 1: Write failing tests**
Cover local end-to-end flow:
- simulated Slack input
- identity resolution via Google adapter boundary
- ACL-aware service call
- safe response output shape

Also assert:
- unauthorized retrieval chunks are absent from context/sources
- empty authorized set returns safe empty answer shape

**Step 2: Verify RED**
Run:
```bash
pytest tests/test_local_flow.py -v
```
Expected: FAIL.

**Step 3: Minimal implementation**
Implement deterministic local runner that composes existing core modules + adapter interfaces.

**Step 4: Verify GREEN**
Run:
```bash
pytest tests/test_local_flow.py -v
```
Expected: PASS.

**Step 5: Commit**
```bash
git add app/local_flow.py tests/test_local_flow.py
git commit -m "feat: add local integration execution flow"
```

---

### Task 6: Add adapter failure-handling coverage

**Files:**
- Create: `tests/test_integration_failures.py`
- Modify: `app/slack_runtime.py`
- Modify: `app/google_adapter.py`
- Modify: `app/notion_adapter.py`
- Modify: `app/local_flow.py`

**Step 1: Write failing tests**
Cover:
- Slack malformed event handling
- Google adapter timeout/error mapping
- Notion adapter transient failure handling
- local flow fallback behavior that preserves deny-by-default and avoids data leakage

**Step 2: Verify RED**
Run:
```bash
pytest tests/test_integration_failures.py -v
```
Expected: FAIL.

**Step 3: Minimal implementation**
Implement explicit error paths with safe outputs and no unauthorized context assembly.

**Step 4: Verify GREEN**
Run:
```bash
pytest tests/test_integration_failures.py -v
```
Expected: PASS.

**Step 5: Commit**
```bash
git add tests/test_integration_failures.py app/slack_runtime.py app/google_adapter.py app/notion_adapter.py app/local_flow.py
git commit -m "feat: add integration failure handling safeguards"
```

---

### Task 7: Final verification and docs sync for integration slice

**Files:**
- Modify: `docs/architecture.md`
- Modify: `DECISIONS.md`
- Modify: `tasks/current_iteration.md`
- Modify: `PROJECT_STATE.md`

**Step 1: Run focused integration tests**
Run:
```bash
pytest tests/test_integration_config.py tests/test_slack_runtime.py tests/test_google_adapter.py tests/test_notion_adapter.py tests/test_ingestion.py tests/test_local_flow.py tests/test_integration_failures.py -v
```
Expected: PASS.

**Step 2: Run full test suite**
Run:
```bash
pytest -v
```
Expected: PASS.

**Step 3: Sync docs/state**
Document:
- adapter boundaries
- preserved ACL invariants
- known integration gaps that remain out of scope

**Step 4: Commit**
```bash
git add docs/architecture.md DECISIONS.md tasks/current_iteration.md PROJECT_STATE.md
git commit -m "docs: finalize integration layer implementation status"
```
