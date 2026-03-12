# AGENTS.md

## Mission
Build `NotionAI`: a Slack Q&A assistant over Notion content with strict access control based on Google Workspace OU.

## Current Phase
This repository currently prioritizes planning, architecture, and scaffolding. Product implementation is expected in a separate execution session.

## Core Constraints
- Use one Slack bot for all users.
- Use Google Workspace OU as the primary access signal.
- Apply `deny-by-default` ACL.
- Never send unauthorized Notion content to the LLM prompt.

## Required Workflow
1. Read `EXECUTION_RULES.md` first.
2. Read `PROJECT_CONTEXT.md`, `PROJECT_STATE.md`, and latest file in `docs/plans/`.
3. If task is multi-step, update `tasks/current_iteration.md` before coding.
4. Keep decisions in `DECISIONS.md`.
5. Keep backlog updates in `tasks/backlog.md`.

## Documentation Rules
- Every architectural change must update `docs/architecture.md`.
- Every accepted tradeoff must be added to `DECISIONS.md`.
- Every implementation session should end with `PROJECT_STATE.md` refresh.

## Safety Rules
- ACL filtering must happen before retrieval context is assembled.
- Default access is deny when policy data is missing or ambiguous.
- Use corporate email as unique user key for per-user exceptions.
