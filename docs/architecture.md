# Architecture

## Components
- Identity Resolver (`app/identity.py`): resolves Google `orgUnitPath` from corporate email via injected directory client.
- Policy Engine (`app/policy.py`): deterministic allow/deny evaluator with root rules plus page-level ACL overrides.
- Notion Metadata Parser (`app/notion_source.py`): parses raw Notion-like payloads into metadata (page linkage, title/path, edit time, ACL tags).
- Retriever Filter (`app/retrieval.py`): filters chunks by authorized page IDs before context assembly.
- Slack Response Adapter (`app/slack_adapter.py`): transport-agnostic response formatter with safe source metadata fields only.
- Service Orchestrator (`app/service.py`): dependency-injected flow that wires identity, policy, retrieval, and formatter.
- Integration Config Loader (`app/integration_config.py`): env-only integration config parsing and explicit required validation.
- Slack Runtime Boundary (`app/slack_runtime.py`): converts Slack-like events to service request shape and service response to Slack-sendable payload.
- Google Adapter Boundary (`app/google_adapter.py`): maps Google Admin SDK-like payloads to identity directory contract and maps transient failures.
- Notion Adapter Boundary (`app/notion_adapter.py`): fetches raw page-like payloads from injected Notion-like client and maps transient failures.
- Ingestion Entrypoint (`app/ingestion.py`): parses raw page payloads into metadata and records deterministic parse failures.
- Local Flow Composer (`app/local_flow.py`): deterministic SDK-free local end-to-end composition of runtime boundary and service.

## Security Invariant
Unauthorized content must never enter prompt context.

## Access Evaluation Order
1. Resolve user email and OU.
2. Evaluate page access from root policy plus page-level overrides (`acl_restricted`, `acl_allow_ou`, `acl_allow_users`).
3. Build `allowed_page_ids`.
4. Filter retrieval results to authorized chunks only.
5. Assemble answer context from authorized chunks only.
6. Format response with safe source metadata (`title`, `path`, `last_edited_time`, `page_id`).

## Adapter Failure Handling
- Slack malformed/unsupported events are converted to safe empty payload in local flow.
- Google and Notion transient boundary failures are mapped to explicit adapter errors.
- Local flow returns safe empty payload for adapter-boundary failures to avoid leakage.

## Current Implementation Gaps
- No runtime/server wiring yet (Slack events, background workers, deployment).
- No real Notion crawling/pagination pipeline yet.
- No real vector database integration yet (in-memory retrieval model for MVP logic tests).
