# NotionAI MVP Design (Single Slack Bot + OU-based ACL)

## Goal

Reduce Notion seat costs by keeping writers in Notion and moving read access to Slack Q&A via one bot, while preserving access boundaries based on Google Workspace OU.

## Scope (MVP)

- One Slack bot for internal Q&A.
- Knowledge source: Notion content from selected roots.
- Access control source: Google Workspace OU (from user email).
- Pilot roots:
  - `HR`: open for all employees.
  - `Development`: open only for Development OU.
- Output format in Slack:
  - Answer text.
  - Source metadata only (title, path, last_edited, page_id).
  - No requirement to open Notion links.

## Non-goals (MVP)

- Full automatic import of existing Notion sharing settings into ACL.
- Public read-only viewer of full pages.
- Multi-integration token routing (future option).

## Identity and Access Model

## Identity source

1. Slack event provides `slack_user_id`.
2. Slack API resolves corporate email.
3. Google Admin SDK resolves user `orgUnitPath`.

Access decisions are made by OU path and optional per-user email allows.

## ACL model

Default policy is deny:

- If a page does not match any allow rule, access is denied.

Policy layers:

1. Root policy in `access_policies.yaml` (base visibility for each root tree).
2. Optional page-level tags in Notion (override behavior).

### Root policy semantics

Each configured root defines:

- `name`
- `page_id`
- `allow_ou` (list of OU paths)
- `allow_users` (list of emails)

No `deny` rules in MVP.

### Page override semantics

Notion page tags/properties:

- `acl_restricted=true`:
  - Switch page subtree to strict allowlist mode (ignore inherited allows except explicit allow tags on this node/subtree).
- `acl_allow_ou`:
  - Add allowed OU for this page/subtree.
- `acl_allow_users`:
  - Add allowed users (corporate emails) for this page/subtree.

Key behavior:

- No tag means inherit root/base behavior.
- `acl_allow_*` alone expands access relative to inherited access.
- `acl_restricted=true` narrows access and requires explicit allows.

## OU matching

- Match by prefix to support hierarchy.
- Example: allow `"/Development"` grants access to `"/Development/QA"` and `"/Development/Backend"`.
- Root OU (all employees) can be represented as `"/"` or a top-level company OU path depending on actual Google OU tree.

## Data Flow

1. Ingestion job pulls Notion pages under configured roots.
2. Content is chunked and stored with metadata:
  - `page_id`, `parent_id`, `title`, `path`, `last_edited_time`, ACL-relevant tags.
3. User asks a question in Slack.
4. Service resolves user email and OU.
5. Policy engine computes allowed page set.
6. Retrieval runs only on allowed chunks.
7. LLM produces answer from filtered context.
8. Bot responds with answer and source metadata.

Important security property:

- Unauthorized chunks must be filtered before prompt assembly.
- Model never receives forbidden text.

## Config Draft

`access_policies.yaml` (draft):

```yaml
default: deny_all

roots:
  - name: HR
    page_id: "NOTION_PAGE_ID_HR"
    allow_ou:
      - "/"
    allow_users: []

  - name: Development
    page_id: "NOTION_PAGE_ID_DEVELOPMENT"
    allow_ou:
      - "/Development"
    allow_users: []
```

`groups_map.yaml` is not required in MVP if OU is used directly. Add later only if business aliases are needed.

## Operational Process

To avoid manual overhead:

- Base access changes happen rarely in `access_policies.yaml` (root-level).
- Local exceptions are handled in Notion via `acl_restricted` and `acl_allow_*`.
- Team maintains a short runbook for how to set tags on restricted pages.

## Risks and Mitigations

1. Risk: drift between Notion UI permissions and bot ACL.
   - Mitigation: treat bot ACL as explicit source for bot visibility; validate sensitive sections during rollout.
2. Risk: incorrect OU path assumptions.
   - Mitigation: log resolved OU per request in audit logs (without content) and test with known users.
3. Risk: retrieval leak due to missing filter.
   - Mitigation: enforce ACL filter server-side before vector search/post-filter; add tests for deny-by-default.

## Migration Path to Multi-integration Mode

Keep Notion connector behind interface:

- `NotionSource.fetch_pages(root_ids, auth_context)`

Later, switch auth context to route by role/token set. Slack API, policy engine, retrieval pipeline, and prompting stay unchanged.

## Acceptance Criteria (MVP)

1. User from Development OU can get answers from `Development` and `HR` roots when allowed by tags.
2. User outside Development OU cannot retrieve Development-only pages.
3. `acl_restricted=true` on an HR subpage effectively narrows access.
4. `acl_allow_users` grants access to explicitly listed corporate emails.
5. All access denials are silent in answer content (no leaked snippets), with internal audit logging.
