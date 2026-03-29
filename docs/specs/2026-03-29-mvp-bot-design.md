# NotionAI MVP Bot — Design Spec

## Overview
Slack-бот, который отвечает на вопросы сотрудников по данным из Notion с контролем доступа через Google Workspace OU. DM-only для MVP.

## Architecture

Two processes:
1. **Slack Bot** — listens for DM messages, processes questions, responds
2. **Notion Sync** — cron job (every 30-60 min), crawls Notion, updates ChromaDB

### Request Flow
```
User DM → Slack Socket Mode → resolve Slack user email
→ Google Directory (email → OU path)
→ vector search (ChromaDB, top-k relevant chunks)
→ ACL filter (allow-only, per-root OU policies)
→ Claude Haiku (filtered chunks + question → answer)
→ respond in DM
```

### Notion Sync Flow
```
Cron trigger → fetch all pages under each configured root (recursive)
→ extract text content → split into chunks
→ generate embeddings → upsert into ChromaDB (metadata: root_id, page_id, title, path)
```

## ACL Model

### Principles
- **Deny-by-default**: if user's OU is not in allow list → no access
- **Allow-only**: no deny rules. Outsource/Outstaff simply not listed = blocked
- **OU groups**: named groups for reuse (e.g. `all_internal`)
- **Hierarchical OU matching**: `/Development` matches `/Development/Devs`, `/Development/QA`, etc.

### Config Structure (access_policies.yaml)
```yaml
default: deny_all

groups:
  all_internal:
    - "/Boosting Supply"
    - "/Currency supply"
    - "/Customer Care & Support"
    - "/Development"
    - "/Game performance"
    - "/Management"
    - "/Product"
    - "/Sales"
    - "/Service"

roots:
  - name: HR
    page_id: "6fc13a2a-a763-441c-8a99-a6c3fabe9a2b"
    allow_ou_group: all_internal

  - name: Development
    page_id: "81c090a3-eb85-44e5-bae3-c0f16e8d0cea"
    allow_ou: ["/Development", "/Product"]

  - name: Currency Supply
    page_id: "TBD"
    allow_ou: ["/Currency supply"]

  - name: Marketing
    page_id: "TBD"
    allow_ou_group: all_internal

  - name: Content
    page_id: "TBD"
    allow_ou_group: all_internal

  - name: Gameleads
    page_id: "TBD"
    allow_ou_group: all_internal

  - name: Sales
    page_id: "TBD"
    allow_ou_group: all_internal

  - name: Customer Care
    page_id: "TBD"
    allow_ou_group: all_internal

  - name: Green Team
    page_id: "TBD"
    allow_ou_group: all_internal

  - name: Docs
    page_id: "TBD"
    allow_ou_group: all_internal

  - name: Operations
    page_id: "TBD"
    allow_ou_group: all_internal

  - name: Release Notes
    page_id: "TBD"
    allow_ou_group: all_internal

  - name: Knowledge Base
    page_id: "TBD"
    allow_ou_group: all_internal

  - name: Business processes
    page_id: "TBD"
    allow_ou_group: all_internal

  - name: Salesforce
    page_id: "TBD"
    allow_ou_group: all_internal
```

Note: "Расписание звонков" and "Архив" excluded from MVP — low value for Q&A.

### Google OU Tree (Overgear)
```
Overgear Limited/
├── Boosting Supply/ (Supply - Black team, Supply - Green team)
├── Currency supply/ (ARPG GDKP, Classic Currency, Retail currency)
├── Customer Care & Support/ (Customer Care, Support)
├── Development/ (Devs, QA, SA)
├── Game performance/ (Content, Game leads, Marketing)
├── Management/ (Finance, HR)
├── Outsource          ← NOT in any allow list = blocked
├── Outstaff           ← NOT in any allow list = blocked
├── Product/ (Analytics, Design, Product Managers)
├── Sales/ (Boosting sales, Currency sales)
└── Service
```

### Notion Spaces → Access Mapping
| Space | Access Model | Notion Group with Full Access |
|-------|-------------|------|
| HR | all_internal | individual users |
| Development | /Development, /Product | Development (+QA), Product |
| Marketing | all_internal | Content, Management, Marketing |
| Content | all_internal | Content |
| Gameleads | all_internal | Gameleads |
| Sales | all_internal | individual users |
| Customer Care | all_internal | Customer Care |
| Green Team | all_internal | People in General |
| Currency Supply | /Currency supply | individual users |
| Docs | all_internal | Everyone at Overgear |
| Operations | all_internal | Everyone at Overgear |
| Release Notes | all_internal | individual users |
| Knowledge Base | all_internal | Everyone at Overgear |
| Business processes | all_internal | Everyone at Overgear |
| Salesforce | all_internal | Everyone at Overgear |

## Tech Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| Slack | slack-bolt (Python), Socket Mode | DM-only for MVP |
| LLM | Claude API (Haiku) | Abstraction layer for swapping |
| Vector DB | ChromaDB (embedded) | Local storage, zero infrastructure |
| Embeddings | TBD (OpenAI or sentence-transformers) | |
| Google Directory | google-api-python-client | Already working (spike verified) |
| Notion API | notion-client or raw HTTP | |
| Config | YAML | access_policies.yaml |

## Environment Variables (.env)
```
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
ANTHROPIC_API_KEY=sk-ant-...
NOTION_TOKEN=ntn_...
GOOGLE_APPLICATION_CREDENTIALS=credentials/service-account.json
GOOGLE_ADMIN_SUBJECT=no-reply-svc@overgear.com
```

## File Structure (new/modified)
```
main.py                 # Slack bot entrypoint
sync.py                 # Notion sync entrypoint (cron)
app/
  llm.py                # LLM abstraction + Claude implementation
  embeddings.py         # Embedding generation
  vector_store.py       # ChromaDB wrapper
  notion_crawler.py     # Recursive page fetcher + chunker
  config.py             # Updated: support for groups + allow_ou_group
  policy.py             # Updated: resolve group references
  models.py             # Updated: OU group model
configs/
  access_policies.yaml  # Updated: full config with all roots + groups
.env                    # Tokens (gitignored)
```

## Decisions Log Reference
- D-012: ChromaDB as MVP Vector Store
- D-013: Claude Haiku as Default LLM
- D-014: Local-First Development
- D-015: Cron-Based Notion Sync (future: webhooks)
- D-016: Slack Socket Mode (future: HTTP Events API)
- D-017: Allow-Only ACL (no deny rules)
- D-018: OU Groups in Config
- D-019: DM-Only Bot (future: channel @mention with ACL strategy)

## Future Improvements
- Slack @mention in channels (needs ACL strategy for public responses)
- Notion webhooks (when API exits beta)
- Replace ChromaDB with managed solution (DevOps decision)
- Docker / production deployment (DevOps)
- Embeddings model selection optimization
