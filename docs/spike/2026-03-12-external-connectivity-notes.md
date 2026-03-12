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

## Pending for Later Spike Tasks
- Real Google OU samples (email -> `orgUnitPath`) validation.
- Real Notion pilot root IDs (`HR`, `Development`) validation.
- Mismatch capture versus current adapter/parser contracts.
