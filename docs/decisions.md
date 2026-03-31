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

### D-006: In-Memory-First Retrieval Contract
Use a minimal in-memory retrieval chunk model during MVP implementation to validate ACL filtering behavior before adding a vector DB.

### D-007: Transport-Agnostic Slack Formatting
Keep Slack response formatting SDK-free and return a simple payload contract so message transport can be added later without changing core logic.

### D-008: Service Orchestration by Dependency Injection
Wire identity, policy, retrieval, and formatter through injected collaborators for deterministic unit tests and minimal runtime coupling.

### D-009: SDK-Free Adapter Boundaries in Integration Phase
Implement Slack/Google/Notion boundaries as thin adapter layers over injected client interfaces before adding real SDK/runtime wiring.

### D-010: Deterministic Ingestion Failure Recording
Ingestion entrypoint must skip malformed payloads safely and return deterministic failure records for testable behavior.

### D-011: Safe Empty Local Flow Fallback
Local flow converts malformed Slack input and adapter-boundary failures to an explicit safe empty payload shape.

## 2026-03-29

### D-012: ChromaDB as MVP Vector Store
Use ChromaDB (embedded, local storage) for MVP. Zero infrastructure — runs in-process, data in local directory. Sufficient for pilot scale (~50 users, ~200 pages). **DevOps note:** перед production-деплоем оценить замену на managed решение (Qdrant Cloud, pgvector, etc.) в зависимости от нагрузки и требований к persistence.

### D-013: Claude Haiku as Default LLM
Use Claude API (Haiku model) as default LLM for answer generation. Abstraction layer позволяет заменить на другой LLM. Cost: ~$0.25/1M input tokens, ~$5-15/month at pilot scale.

### D-014: Local-First Development
MVP разрабатывается и тестируется локально (python main.py). После валидации — передаётся DevOps для деплоя. Без Docker/serverless на этапе MVP.

### D-015: Cron-Based Notion Sync
Notion crawl по расписанию (раз в 30-60 мин). Задержка приемлема для корпоративной wiki. **Future improvement:** перейти на Notion webhooks (event-driven sync) когда API выйдет из беты — уменьшит задержку и нагрузку.

### D-016: Slack Socket Mode
Используем Socket Mode (WebSocket) — не нужен публичный URL, работает за NAT, проще деплой. **DevOps note:** при необходимости можно переключить на HTTP Events API, если потребуется балансировка или multiple instances.

### D-017: Allow-Only ACL (no deny rules)
Только явный allow, без deny-правил. Как в AD best practice — если OU нет в allow-списке, доступа нет. Outsource/Outstaff не добавляются в allow = заблокированы автоматически. Это проще аудитить и отлаживать.

### D-018: OU Groups in Config (alias reuse)
Конфиг поддерживает именованные группы OU (`groups.all_internal`) для переиспользования. 15 из 17 spaces доступны всем внутренним — ссылаются на одну группу вместо дублирования списка.

### D-019: DM-Only Bot for MVP
Бот отвечает только в личных сообщениях (DM). Ответ видит только тот кто спросил — безопасно для ACL. **Future improvement:** добавить @mention в каналах (ответ в треде), но требует предварительной проработки: ответ в публичном канале виден всем, а права у пользователей разные — нужна стратегия (отвечать только на "общедоступные" данные? или отправлять ACL-ответ в DM вместо канала?).

## 2026-03-31

### D-020: BGE-M3 Embedding Model
Выбрана BGE-M3 (BAAI/bge-m3, 568M params) — лучшая multilingual модель для русского текста по бенчмаркам 2025 (ruMTEB, Dialogue IR). Поддерживает dense + sparse retrieval из одной модели.

### D-021: BGE Reranker Cross-Encoder
Добавлен BGE Reranker v2-m3 как второй этап поиска: top-20 из vector search → rerank → top-5 для LLM. Доказанный прирост +15-40% accuracy. Proven combo с BGE-M3 на русских бенчмарках.

### D-022: Root-Level ACL Only (no page-level)
Убраны неиспользуемые параметры page-level ACL из policy.py. Доступ определяется только на уровне root spaces. Проще, прозрачнее, нет ложного чувства безопасности от мёртвого кода.

### D-023: Prompt Injection Mitigation
XML-fencing (`<context>`, `<user_question>`) + экранирование закрывающих тегов + инструкция в system prompt не выполнять команды из user_question. Generic error messages (без деталей exceptions) для пользователей.

### D-024: Citations in Answers
Ответы содержат кликабельные ссылки на страницы Notion. Контекст пронумерован [1], [2], ... — LLM ссылается на номера. Повышает доверие и верифицируемость.
