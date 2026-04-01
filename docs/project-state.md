# Project State

## Phase
Feature-complete MVP. Paused — company may migrate from Notion to ClickUp.

## What's Built
- Slack bot (Socket Mode, DM + channel @mention)
- Google Directory OU resolution (with retry)
- BGE-M3 embeddings + BGE Reranker cross-encoder
- Hybrid search (vector + BM25 + RRF fusion)
- Query rewriting (abbreviation expansion + LLM)
- OU-based reranker boost (department content prioritized)
- Archive/other-department penalty in ranking
- Parent-child chunks (300 char search → 1500 char LLM context)
- Chunk overlap 10%
- Citations with clickable Notion links
- "Show full text" button → Slack modal with live Notion content
- Semantic cache (OU-scoped, 1 hour TTL)
- Feedback buttons (👍👎)
- Status command
- Conversation follow-ups
- Claude Haiku with XML prompt fencing (prompt injection mitigation)
- Rate limiting (10 req/min per user)
- Thread-safe event deduplication
- Graceful shutdown (signal handling)
- Parallel sync (3 workers)
- File lock for concurrent sync protection
- Docker + docker-compose
- 35 tests, 4 rounds of code review
- **Stats: 1553 pages, 26,204 chunks, 15 roots + 2 databases**

## How to Resume
```bash
# Start bot (models download on first run ~3GB)
.venv/bin/python main.py

# Full resync (if data is stale, ~1 hour)
.venv/bin/python sync.py --full

# Incremental sync
.venv/bin/python sync.py

# Tests
.venv/bin/pytest -v
```

## Known Limitations
- ~0.2% Notion pages inaccessible ("unlinked from parent" permissions)
- Incremental sync still does full crawl (saves embedding cost, not API calls)
- No page-level ACL (root-level only)
- No image support in bot responses
- Search quality varies — general queries work well, very specific ones may miss
