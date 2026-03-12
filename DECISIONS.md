# Decisions

## 2026-03-12

### D-001: Single Slack Bot for MVP
Use one Slack bot with internal ACL filtering.

### D-002: OU-Based Access Source
Use Google Workspace OU (`orgUnitPath`) as primary access signal.

### D-003: Deny-by-Default
When no allow rule matches, access is denied.

### D-004: Hybrid ACL Management
Use root policies in YAML and page-level Notion tags for local overrides.

### D-005: Pilot Roots
Pilot with `HR` and `Development` roots.
