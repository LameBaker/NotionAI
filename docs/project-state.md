# Project State

## Phase
MVP bot working — all 15 roots indexed, testing and improving quality.

## What's Done
- Slack bot (Socket Mode, DM-only) — working
- Google Directory OU resolution — working
- ChromaDB vector search with multilingual embeddings (paraphrase-multilingual-MiniLM-L12-v2)
- ACL filtering by root_id (allow-only, OU groups)
- Claude Haiku answer generation
- 15 root pages + 2 databases in config (13 page roots + Infrastructure DB + Docs DB)
- Recursive crawler: toggles, callouts, columns, child pages inside nested blocks
- Section path tracking (heading hierarchy)
- Incremental sync (`sync.py` / `sync.py --full`)
- Page deduplication in crawler
- Retry + timeout handling for Notion API
- Access gaps checker script (`scripts/check_access_gaps.py`)
- 57 tests passing
- **Stats: 1553 pages, 7200 chunks indexed**

## Known Issues
- ~0.2% pages inaccessible (Notion "unlinked from parent" + "Only people invited") — not fixable without manual Share
- Infrastructure database returns 0 pages (needs manual Share in Notion)
- Embeddings quality: multilingual MiniLM decent but not perfect for Russian semantic search
- No logging in bot (hard to debug what chunks were found/filtered)

## Comparison with Misha's Bot
- Analyzed at ~/Code/notion-kb-bot-test-main/
- His: Node.js, keyword search, no AI, job title ACL (101 manual mappings)
- Ours: Python, semantic search + Claude AI, Google OU ACL (automatic)
- Key learning: his section_path tracking (adopted), database indexing (adopted)

## How to Run
```bash
# Full sync (first time, ~1 hour)
.venv/bin/python sync.py --full

# Incremental sync (subsequent, ~1-2 min)
.venv/bin/python sync.py

# Start bot
.venv/bin/python main.py

# Check access gaps
PYTHONPATH=. .venv/bin/python scripts/check_access_gaps.py
```
