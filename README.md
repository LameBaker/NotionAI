# NotionAI

Slack Q&A bot over corporate Notion wiki with Google Workspace OU-based access control. Uses BGE-M3 embeddings, ChromaDB vector search with reranking, and Claude AI for answer generation.

## Why

Notion costs are high because many employees only read content. This bot delivers read access through Slack DM — employees ask questions, bot answers from Notion data. Each employee sees only what their department is authorized to access.

## Features

- **AI-powered answers** — Claude Haiku generates answers from Notion content, not just links
- **Access control** — Google Workspace OU determines who sees what (deny-by-default, allow-only)
- **Semantic search** — BGE-M3 multilingual embeddings + ChromaDB vector store
- **Reranking** — BGE Reranker cross-encoder re-scores results for better relevance
- **Citations** — answers include clickable Notion page links
- **15 Notion spaces** indexed (1500+ pages, 7000+ chunks)
- **Rate limiting** — per-user protection against API cost abuse
- **Incremental sync** — only re-indexes changed pages

## Architecture

```
User DM → Slack (Socket Mode) → Google Directory (email → OU)
→ Vector search (ChromaDB, top-20) → ACL filter (by root_id)
→ Rerank (BGE Reranker, top-5) → Claude Haiku → Answer + Sources
```

Separate sync process crawls Notion pages on schedule and indexes them into ChromaDB.

## Quick Start

### Prerequisites

- Python 3.12+
- Slack App with Socket Mode (Bot Token + App Token)
- Anthropic API key
- Notion Internal Integration token
- Google Service Account with Directory API access

### Setup

```bash
# Install Python (via asdf)
asdf install python 3.12.9
asdf set python 3.12.9

# Create venv and install deps
python -m venv .venv
.venv/bin/pip install -r requirements.txt

# Configure
cp .env.example .env  # fill in tokens
```

### .env

```
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
ANTHROPIC_API_KEY=sk-ant-...
NOTION_TOKEN=ntn_...
GOOGLE_APPLICATION_CREDENTIALS=credentials/service-account.json
GOOGLE_ADMIN_SUBJECT=admin@yourdomain.com
```

### Run

```bash
# First time: full sync (~1 hour for large workspaces)
.venv/bin/python sync.py --full

# Start bot
.venv/bin/python main.py

# Subsequent syncs (incremental, minutes)
.venv/bin/python sync.py
```

### Tests

```bash
.venv/bin/pytest -v
```

## Access Control

Access is configured in `configs/access_policies.yaml`:

```yaml
default: deny_all

groups:
  all_internal:
    - "/Department1"
    - "/Department2"

roots:
  - name: HR
    page_id: "uuid-here"
    allow_ou_group: all_internal  # everyone sees HR

  - name: Development
    page_id: "uuid-here"
    allow_ou: ["/Development", "/Product"]  # only these OUs
```

- **Deny-by-default** — if your OU is not in the allow list, no access
- **Allow-only** — no deny rules, simpler to audit
- **OU groups** — reusable named groups to avoid duplication
- **Hierarchical matching** — `/Development` matches `/Development/Backend`, `/Development/QA`, etc.

## Project Structure

```
main.py                 # Bot entrypoint
sync.py                 # Notion sync entrypoint
app/
  bot.py                # Slack handler + QuestionHandler
  llm.py                # Claude AI integration
  vector_store.py       # ChromaDB wrapper
  reranker.py           # BGE Reranker cross-encoder
  notion_crawler.py     # Recursive page crawler + chunker
  google_client.py      # Google Admin SDK client
  identity.py           # Email → OU resolver
  policy.py             # ACL evaluator
  config.py             # YAML config loader
  models.py             # Data models
  env.py                # Environment config
  ou_utils.py           # OU path normalization
  retrieval.py          # RetrievalChunk model
configs/
  access_policies.yaml  # ACL configuration
tests/                  # pytest tests
scripts/                # Utility scripts
docs/                   # Documentation
```

## Key Docs

- `docs/specs/2026-03-29-mvp-bot-design.md` — design spec
- `docs/decisions.md` — architectural decisions (D-001 through D-019)
- `docs/project-state.md` — current project state
- `docs/research-2026-03-31-rag-improvements.md` — RAG quality research
