# NotionAI

Slack Q&A assistant over Notion with OU-based access control.

## Problem

Notion costs are high because many users only read content. Goal: keep writers in Notion, deliver read access through Slack Q&A bot with ACL filtering based on Google Workspace OU.

## Current Status

- Core domain and integration boundary layers implemented (47 tests passing).
- External connectivity spike in progress — validating real Google/Notion data before runtime wiring.
- Spike Task 2 ready to execute (Google Directory check).

## Quick Start

```bash
# Setup
python -m venv .venv
.venv/bin/pip install -r requirements.txt  # when added

# Run tests
pytest -v
```

## Architecture

See `docs/architecture.md` for component details.

**Security invariant:** Unauthorized content must never enter LLM prompt context.

**Access evaluation order:**
1. Resolve user email and OU from Google Directory
2. Evaluate page access from root policy + page-level overrides
3. Filter retrieval results to authorized chunks only
4. Assemble answer context from authorized chunks only

## Key Docs

- `docs/architecture.md` — component architecture
- `docs/decisions.md` — architectural decisions log
- `docs/project-state.md` — current project state
- `docs/roadmap.md` — development roadmap
- `docs/plans/` — iteration plans
- `tasks/` — iteration tracking
