# NotionAI — Slack Q&A бот над Notion с контролем доступа

## Что это

Slack-бот, который отвечает на вопросы сотрудников по данным из Notion. Доступ контролируется через Google Workspace OU — каждый видит только то, что ему положено. Цель: сократить расходы на Notion, убрав read-only пользователей из лицензий.

## Правила

- Язык кода: Python
- TDD: сначала тест, потом реализация
- Deny-by-default: если нет явного разрешения — доступ запрещён
- Неавторизованный контент НИКОГДА не попадает в контекст LLM
- Одна задача за раз, минимальные изменения
- После каждой задачи обновлять `docs/project-state.md`
- Preserve deny-by-default ACL behavior
- Corporate email — канонический идентификатор для `acl_allow_users`

## Ключевые решения

- Один Slack-бот на всех (ACL-фильтрация внутри)
- Google OU (`orgUnitPath`) — основной сигнал доступа
- Корпоративный email — уникальный идентификатор пользователя
- YAML-политики + page-level Notion-теги для переопределений
- Адаптеры без SDK (тонкие границы для тестируемости)
- Решения фиксируются в `docs/decisions.md`

## Текущее состояние

**Фаза:** External connectivity spike — валидация реальных данных Google/Notion перед подключением к API.

**Готово:**
- Вся бизнес-логика (7 модулей): config, policy, identity, notion_source, retrieval, slack_adapter, service
- Все интеграционные адаптеры (6 модулей): integration_config, slack_runtime, google_adapter, notion_adapter, ingestion, local_flow
- Обработка ошибок адаптеров
- Spike Task 1 (contract baseline tests)
- Все тесты проходят: `pytest -v` (47 passed)

**Заблокировано:**
- Spike Task 2: скрипт `scripts/spike/check_google_directory.py` готов, credentials доступны из RWSSO
- Spike Task 3: валидация Notion root page IDs (HR, Development)
- Spike Task 4: go/no-go решение

## Структура

```
app/                    # Бизнес-логика и адаптеры
  config.py             # YAML config loader
  models.py             # Typed policy models
  policy.py             # ACL evaluator (deny-by-default)
  identity.py           # Google OU resolver
  notion_source.py      # Notion metadata parser
  retrieval.py          # ACL-aware chunk filtering
  slack_adapter.py      # Response formatter
  service.py            # Orchestrator (DI)
  integration_config.py # Env-based config
  slack_runtime.py      # Slack event boundary
  google_adapter.py     # Google Admin adapter
  notion_adapter.py     # Notion API adapter
  ingestion.py          # Notion ingestion entrypoint
  local_flow.py         # Local integration composer
tests/                  # Тесты (pytest)
  spike/                # Spike contract tests
scripts/spike/          # Read-only validation scripts
docs/
  architecture.md       # Архитектура компонентов
  plans/                # Планы итераций
  spike/                # Spike notes
  decisions.md          # Архитектурные решения
  project-state.md      # Текущее состояние проекта
  roadmap.md            # Дорожная карта
configs/                # YAML policy configs
```

## Команды

```bash
# Все тесты
pytest -v

# Конкретный модуль
pytest tests/test_policy.py -v

# Spike тесты
pytest tests/spike/ -v

# Spike Task 2: Google Directory check
GOOGLE_APPLICATION_CREDENTIALS=credentials/service-account.json \
GOOGLE_SPIKE_ADMIN_SUBJECT=no-reply-svc@overgear.com \
.venv/bin/python scripts/spike/check_google_directory.py --emails oleg@overgear.com
```

## Что читать при старте сессии

1. Этот файл
2. `docs/project-state.md` — текущее состояние
3. `docs/plans/2026-03-12-notionai-external-connectivity-spike.md` — план спайка
4. `docs/spike/2026-03-12-external-connectivity-notes.md` — заметки спайка

## Контекст проекта Overgear

- Владелец: Олег Никитин (сисадмин Overgear)
- Linear: задача SAD-5 "Создать MVP проект по экономии Notion"
- Google Workspace: домен overgear.com
- Notion: корпоративный, нужны root page IDs для HR и Development

## Google Credentials (из RWSSO)

Service Account уже настроен для другого проекта (SSO Proxy для VPN) и подходит для spike:
- **SA file:** `credentials/service-account.json`
- **SA email:** `remnawave-admin-sdk@overgear-vpn.iam.gserviceaccount.com`
- **Admin subject:** `no-reply-svc@overgear.com`
- **Scope:** `admin.directory.user.readonly` — уже делегирован через Domain-Wide Delegation
- **Client ID:** `111795272679880716178`

Эти credentials read-only и безопасны для spike-валидации.
