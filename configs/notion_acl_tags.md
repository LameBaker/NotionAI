# Notion ACL Tags (MVP)

## Purpose
Define optional page-level overrides on top of root policies.

## Supported Tags/Properties
- `acl_restricted=true`
- `acl_allow_ou`
- `acl_allow_users`

## Semantics
- No tags: inherit root policy.
- `acl_allow_*` without `acl_restricted`: expand access relative to inherited access.
- `acl_restricted=true`: page/subtree requires explicit allow via `acl_allow_ou` and/or `acl_allow_users`.

## Examples
- Restrict one HR page to HR only:
  - `acl_restricted=true`
  - `acl_allow_ou=/HR`

- Allow one extra person on a restricted page:
  - `acl_allow_users=user@company.com`
