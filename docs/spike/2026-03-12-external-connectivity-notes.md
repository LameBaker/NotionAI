# External Connectivity Spike Notes (2026-03-12)

## Task 1 Baseline Assumptions (Sanitized Placeholders)

### Google identity payload assumptions
- Directory payload includes `primaryEmail` and `orgUnitPath` string fields.
- `orgUnitPath` example baseline: `/Development`.
- Corporate email lookup key remains full email address (example: `engineer@example.com`).
- Missing user behavior is handled separately (`None`) and is not part of this fixture set.

### Notion page payload assumptions
- Raw page payload includes top-level fields: `id`, `parent`, `path`, `last_edited_time`, `properties`.
- Parent linkage can be carried via `parent.page_id`.
- Title is represented by a Notion-like title property with `plain_text` fragments.
- ACL fields can appear as:
  - `acl_restricted`: checkbox-like dict with boolean value
  - `acl_allow_ou`: multi-select names
  - `acl_allow_users`: rich-text CSV-like text

### Contract-validation intent
- Fixtures are sanitized placeholders only (no real tenant data).
- This baseline is used to detect contract drift when real Google/Notion payload checks begin in later spike tasks.
- No production module behavior changed in Task 1.

## Task 2 Execution (Google Directory Read-Only Check) — COMPLETE

### Script
- `scripts/spike/check_google_directory.py`

### Verified result (2026-03-29)
```json
{"orgUnitPath": "/Development", "primaryEmail": "o.nikitin@overgear.com", "status": "ok"}
```

### Credentials used
- SA: `credentials/service-account.json` (copied from RWSSO project)
- Admin subject: `no-reply-svc@overgear.com`
- Scope: `admin.directory.user.readonly` via Domain-Wide Delegation

### Contract compatibility
- `primaryEmail` and `orgUnitPath` fields present — matches `app/google_adapter.py` contract
- `orgUnitPath` format `/Development` — matches `app/identity.py` normalization logic
- No mismatches found

## Task 3 Execution (Notion Root ID Validation) — COMPLETE

### Verified root page IDs (2026-03-29)

| Root | Page ID | Verified |
|------|---------|----------|
| HR | `6fc13a2a-a763-441c-8a99-a6c3fabe9a2b` | Top-level page, contains HR content (вакансии, гайды, процессы) |
| Development | `81c090a3-eb85-44e5-bae3-c0f16e8d0cea` | Top-level page, contains dev content (roadmaps, standards, teams) |

### Payload shape observations
- Pages have `properties` with `title` field
- Parent linkage: both are top-level (empty ancestor-path)
- Child pages linked via `<page url="...">` blocks
- No ACL tags (`acl_restricted`, `acl_allow_ou`, `acl_allow_users`) observed on root pages — these will need to be added as Notion page properties for per-page overrides
- Database entries (e.g. Infrastructure) appear as `<database>` blocks with `data-source-url`

### Contract compatibility notes
- `id` field present — matches contract
- `properties.title` present — matches `app/notion_source.py` parser
- `parent` linkage model differs: Notion API uses `parent.page_id`, but root pages have no parent — handled correctly by parser defaults
- ACL property fields not yet created in Notion — need to add these properties to pages that require per-page overrides (not a blocker for MVP, root-level policies cover pilot)
- `last_edited_time` available in metadata — matches contract

### Mismatch: no ACL properties yet
- **Severity: warning** (not blocker)
- Root-level YAML policies handle pilot access (HR=all, Development=/Development OU)
- Per-page ACL overrides (`acl_restricted`, `acl_allow_ou`, `acl_allow_users`) need to be created as Notion properties later, when page-level exceptions are needed
