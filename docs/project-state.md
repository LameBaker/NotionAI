# Project State

## Phase
MVP complete. Sync running overnight with BGE-M3. Ready for user testing.

## What's Done
- Slack bot (Socket Mode, DM-only) with full pipeline
- Google Directory OU resolution
- BGE-M3 embeddings (best for Russian per 2025 benchmarks)
- ChromaDB vector search (search_ef=50, batch upsert)
- BGE Reranker cross-encoder (top-20 → top-5)
- Claude Haiku answer generation with XML prompt fencing
- Citations with clickable Notion page links
- ACL: allow-only, OU groups, deny-by-default
- 15 root pages + 2 databases in config
- Recursive crawler (toggles, callouts, columns, child pages, databases)
- Chunk overlap 10%
- Incremental sync with stale chunk cleanup
- Rate limiting (10 req/min per user)
- Thread-safe event deduplication
- Graceful shutdown (signal handling)
- File lock for concurrent sync protection
- 31 tests, 4 rounds of code review
- **Stats: 1553 pages, ~7000 chunks**

## Known Limitations
- ~0.2% pages inaccessible (Notion "unlinked from parent" + "Only people invited")
- Incremental sync still does full crawl (saves embedding cost, not API calls)
- No page-level ACL (root-level only) — by design, see D-017

## How to Run
```bash
# Full sync (first time, ~1 hour)
.venv/bin/python sync.py --full

# Incremental sync
.venv/bin/python sync.py

# Start bot
.venv/bin/python main.py

# Tests
.venv/bin/pytest -v

# Check access gaps
PYTHONPATH=. .venv/bin/python scripts/check_access_gaps.py
```
