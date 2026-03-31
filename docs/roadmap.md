# Roadmap

## Done
- MVP bot: Slack DM → Google OU → ACL → vector search → rerank → Claude → answer
- 15 Notion spaces + 2 databases indexed (1553 pages, 7000+ chunks)
- BGE-M3 embeddings + BGE Reranker
- Citations with Notion links
- Security: prompt injection fencing, rate limiting, event dedup, error leak prevention

## Next: Quality Improvements
- Hybrid search (BGE-M3 sparse + dense + RRF fusion)
- Query expansion/rewriting via LLM
- Parent-child chunk retrieval (small for search, large for context)
- Overgear abbreviation dictionary

## Next: Operations
- Cron setup for sync (every 30-60 min)
- Docker container for deployment
- Logging/monitoring dashboard
- Hand off to DevOps

## Future
- Slack @mention in channels (needs ACL strategy for public answers)
- Semantic caching for frequent questions
- Fine-tune embeddings with real user queries (need 500+ pairs)
- Notion webhooks for real-time sync (when API exits beta)
- Database indexing for Release Notes (check with Sasha Kozhevnikov first)
