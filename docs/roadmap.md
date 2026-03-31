# Roadmap

## Done
- MVP bot: Slack DM → Google OU → ACL → vector search → rerank → Claude → answer
- 15 Notion spaces + 2 databases indexed (1553 pages, 7000+ chunks)
- BGE-M3 embeddings + BGE Reranker
- Hybrid search (vector + BM25 + RRF fusion)
- Query rewriting via LLM
- Citations with Notion links
- Chunk overlap 10%
- Security: prompt injection fencing, rate limiting, event dedup, error leak prevention
- 4 rounds of code review, 31 tests

## Next: User Testing
- Launch bot for 2-3 pilot users
- Collect feedback on answer quality
- Fix issues based on real queries

## Next: Operations (DevOps)
- Cron setup for sync (every 30-60 min)
- Docker container for deployment
- Logging/monitoring dashboard

## Future (after real usage data)
- Parent-child chunk retrieval (small for search, large for context)
- Overgear abbreviation dictionary
- Semantic caching for frequent questions
- Fine-tune embeddings with real user queries (need 500+ pairs)
- Slack @mention in channels (needs ACL strategy for public answers)
- Notion webhooks for real-time sync (when API exits beta)
- Database indexing for Release Notes (check with Sasha Kozhevnikov first)
