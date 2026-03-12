# Architecture

## Components
- Identity Resolver (`app/identity.py`): resolves Google `orgUnitPath` from corporate email via injected directory client.
- Policy Engine (`app/policy.py`): deterministic allow/deny evaluator with root rules plus page-level ACL overrides.
- Notion Metadata Parser (`app/notion_source.py`): parses raw Notion-like payloads into metadata (page linkage, title/path, edit time, ACL tags).
- Retriever Filter (`app/retrieval.py`): filters chunks by authorized page IDs before context assembly.
- Slack Response Adapter (`app/slack_adapter.py`): transport-agnostic response formatter with safe source metadata fields only.
- Service Orchestrator (`app/service.py`): dependency-injected flow that wires identity, policy, retrieval, and formatter.

## Security Invariant
Unauthorized content must never enter prompt context.

## Access Evaluation Order
1. Resolve user email and OU.
2. Evaluate page access from root policy plus page-level overrides (`acl_restricted`, `acl_allow_ou`, `acl_allow_users`).
3. Build `allowed_page_ids`.
4. Filter retrieval results to authorized chunks only.
5. Assemble answer context from authorized chunks only.
6. Format response with safe source metadata (`title`, `path`, `last_edited_time`, `page_id`).

## Current Implementation Gaps
- No runtime/server wiring yet (Slack events, background workers, deployment).
- No real Notion crawling/pagination pipeline yet.
- No real vector database integration yet (in-memory retrieval model for MVP logic tests).
