# Project State

## Phase
External connectivity spike — валидация реальных данных Google/Notion перед runtime wiring.

## What's Done
- Бизнес-логика (7 модулей): config, models, policy, identity, notion_source, retrieval, slack_adapter, service
- Интеграционные адаптеры (6 модулей): integration_config, slack_runtime, google_adapter, notion_adapter, ingestion, local_flow
- Обработка ошибок адаптеров
- 47 тестов проходят (`pytest -v`)
- Spike Task 1: contract baseline тесты
- Spike Task 2: Google Directory check — `o.nikitin@overgear.com` → `/Development` (работает)
- Spike Task 3: Notion root IDs подтверждены:
  - HR: `6fc13a2a-a763-441c-8a99-a6c3fabe9a2b`
  - Development: `81c090a3-eb85-44e5-bae3-c0f16e8d0cea`

## Current Sprint: Spike Tasks
- [x] Task 1: contract baseline fixtures/tests
- [x] Task 2: Google Directory connectivity + OU verification
- [x] Task 3: Notion root ID/payload verification
- [ ] Task 4: mismatch triage + go/no-go recommendation

## Not Started
- Slack app setup and event handling
- Notion ingestion and indexing pipeline
- Vector DB / retrieval backend
- LLM integration (Claude API)
- Deployment / infrastructure

## Backlog
- P1: Notion ingestion pipeline. ACL-aware retrieval. Slack message handling.
- P2: Audit logs. Operator runbook for ACL tags in Notion.

## Risks
- ACL tag properties (`acl_restricted`, `acl_allow_ou`, `acl_allow_users`) not yet created in Notion — warning, not blocker for MVP
- Runtime integrations (Slack transport, Notion crawling, production retrieval) are pending
