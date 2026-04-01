# Roadmap

## Done
- MVP bot with full pipeline (search → ACL → rerank → AI → answer)
- 15 Notion spaces + 2 databases indexed
- BGE-M3 + BGE Reranker + hybrid search + query rewriting
- OU-based boost + archive/department penalties
- Parent-child chunks + chunk overlap
- Citations + "Show full text" modal
- Semantic cache (OU-scoped)
- Feedback buttons, status command, conversation follow-ups
- Channel @mention support
- Parallel sync (3 workers)
- Docker + docker-compose
- Security: prompt injection fencing, rate limiting, dedup, error leak prevention
- 35 tests, 4 rounds of code review

## If Resuming: Quality Improvements
- True incremental sync (Notion Search API filter, skip unchanged pages)
- Fine-tune embeddings with real user queries (need 500+ pairs)
- Image support (extract image URLs, show in Slack)
- Better search for vague queries

## If Resuming: Operations
- Cron setup for sync
- Monitoring/alerting
- Hand off to DevOps

## Parked (may not be needed if migrating to ClickUp)
- Notion webhooks for real-time sync
- Release Notes database indexing (check with Sasha Kozhevnikov)
- Slack Canvas integration
