# Architecture

## Components

- **Bot** (`app/bot.py`): Slack Socket Mode handler. Receives DM, resolves user email → OU, searches, filters by ACL, reranks, sends to LLM, responds with answer + citations.
- **QuestionHandler** (`app/bot.py`): Testable core logic extracted from Slack handler. Orchestrates identity → ACL → search → rerank → LLM pipeline.
- **Identity Resolver** (`app/identity.py`): Resolves corporate email to Google OU path via injected DirectoryClient.
- **Google Client** (`app/google_client.py`): Real Google Admin SDK client implementing DirectoryClient protocol.
- **Policy Engine** (`app/policy.py`): Deterministic allow/deny evaluator. Root-level only (allow_ou + allow_users). No deny rules.
- **Config** (`app/config.py`): YAML config loader with OU group resolution and UUID validation.
- **Vector Store** (`app/vector_store.py`): ChromaDB wrapper. BGE-M3 embeddings, batch upsert, search with prefix handling.
- **Reranker** (`app/reranker.py`): BGE Reranker cross-encoder. Re-scores top-20 search results to top-5.
- **LLM** (`app/llm.py`): Claude Haiku integration with XML-fenced prompt, citation numbering, and prompt injection mitigation.
- **Crawler** (`app/notion_crawler.py`): Recursive Notion page fetcher. Handles toggles, callouts, columns, child pages, databases. Retry with backoff, max depth limit.
- **Sync** (`sync.py`): Orchestrates crawl → chunk → embed → upsert. File lock, incremental sync by last_edited_time, stale chunk cleanup.

## Request Flow

```
Slack DM → Socket Mode
  → resolve Slack user email (users_info API)
  → Google Directory (email → OU path)
  → ACL: evaluate which roots user can access
  → ChromaDB vector search (top-20 candidates)
  → ACL filter: keep only chunks from allowed roots
  → BGE Reranker: re-score → top-5
  → Build numbered context [1], [2], ...
  → Claude Haiku: generate answer with source references
  → Format: answer + clickable Notion source links
  → Respond in Slack DM
```

## Sync Flow

```
Cron / manual → sync.py
  → file lock (prevent concurrent runs)
  → for each root in config:
    → crawl pages (recursive, with nested block extraction)
    → or query database (for database-type roots)
    → filter by last_edited_time (incremental)
    → delete stale chunks
    → chunk text (with overlap)
    → prefix with page title
    → batch upsert to ChromaDB (500 per batch)
  → save sync timestamp
```

## Security

- **Deny-by-default**: no allow = no access
- **Allow-only ACL**: no deny rules (simpler to audit)
- **Root-level filtering**: chunks filtered by root_id before LLM sees them
- **Prompt injection mitigation**: XML fencing + tag escaping + system prompt instruction
- **Error leak prevention**: generic errors to users, details logged server-side
- **Rate limiting**: 10 requests/min per user
- **Event dedup**: thread-safe dedup of Slack retries
- **Concurrent sync protection**: file lock
