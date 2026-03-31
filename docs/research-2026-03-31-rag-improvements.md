# RAG Quality Research (2026-03-31)

## Current Stack (validated)
- Embeddings: BGE-M3 (best for Russian per 2025 benchmarks)
- Vector DB: ChromaDB (correct for <1M chunks)
- LLM: Claude Haiku 4.5 (cost-effective for 50 users)

## DO NOW — expected +30-50% answer quality
1. **Hybrid search** (BGE-M3 sparse + dense + RRF) — +20-35% retrieval accuracy
2. **Reranking** (BGE Reranker after initial search) — +15-40% accuracy
3. **Citations** (Notion page links in answers) — essential for user trust

## DO LATER — after launch, based on real usage
- Parent-child chunk retrieval
- Query expansion/rewriting via LLM
- Semantic caching for frequent questions
- Fine-tune embeddings with real query-answer pairs (need 500+ pairs)
- Overgear abbreviation dictionary

## SKIP — overkill for our scale
- Graph RAG (not needed for wiki Q&A)
- Agentic RAG (single-turn queries)
- Matryoshka embeddings (7K chunks = instant search)
- Model changes (BGE-M3 + Haiku confirmed optimal)
