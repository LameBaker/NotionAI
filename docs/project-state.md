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

## Current Sprint: Spike Tasks
- [x] Task 1: contract baseline fixtures/tests
- [x] Task 2: Google Directory connectivity + OU verification
- [ ] Task 3: Notion root ID/payload verification
- [ ] Task 4: mismatch triage + go/no-go recommendation

## Not Started
- Slack app setup and event handling
- Notion ingestion and indexing pipeline
- Vector DB / retrieval backend
- Deployment / infrastructure

## Backlog
- P0: Confirm Notion root page IDs (HR, Development). Confirm Google OU paths for pilot users.
- P1: Notion ingestion pipeline. ACL-aware retrieval. Slack message handling.
- P2: Audit logs. Operator runbook for ACL tags in Notion.

## Risks
- Need Notion integration token and root page IDs for HR and Development
- Runtime integrations (Slack transport, Notion crawling, production retrieval) are pending
