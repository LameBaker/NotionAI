# Project State

## Phase
MVP bot working — first end-to-end test passed.

## What's Done
- Бизнес-логика (7 модулей) + интеграционные адаптеры (6 модулей)
- 57 тестов проходят (`pytest -v`)
- Spike complete: Google Directory + Notion root IDs verified
- **MVP bot working:**
  - Slack Socket Mode (DM-only)
  - Google Directory → OU resolution
  - ChromaDB vector search (390 chunks indexed from HR + Development)
  - ACL filtering by root_id
  - Claude Haiku answer generation
  - First successful answer in Slack (2026-03-29)

## Known Issues (next session)
- Crawler не раскрывает toggle/callout/column блоки — теряется контент внутри них
- Embeddings (default mini-LM) плохо работают с русским — ищет не самые релевантные чанки
- Только 2 root'а в конфиге (HR, Development) — нужно добавить остальные 15
- Нет логирования — непонятно что бот ищет и фильтрует

## Backlog
- P0: Fix crawler nested blocks. Improve Russian embeddings. Add remaining roots.
- P1: Logging/observability. Incremental sync (by last_edited_time).
- P2: Audit logs. Operator runbook. Docker/deployment.

## How to Run
```bash
# Sync Notion → ChromaDB
.venv/bin/python sync.py

# Start bot
.venv/bin/python main.py
```
