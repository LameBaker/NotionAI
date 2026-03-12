# Architecture

## Components
- Slack Adapter: receives user questions and returns answers.
- Identity Resolver: maps Slack user email to Google OU.
- Policy Engine: evaluates root rules and page-level overrides.
- Notion Ingestion: fetches and chunks source pages.
- Retriever: runs search with ACL filtering.
- Answer Engine: builds answer from authorized context only.

## Security Invariant
Unauthorized content must never enter prompt context.

## Access Evaluation Order
1. Resolve user email and OU.
2. Resolve page policy from root + overrides.
3. Allow only if at least one allow rule matches.
4. Otherwise deny.
