# Execution Rules

## Purpose
Single source of truth for coding-session behavior in this repository.

## Mandatory Session Start
1. Read this file first.
2. Read `AGENTS.md`.
3. Read `.codex/BOOTSTRAP.md`.
4. Read `PROJECT_CONTEXT.md` and `PROJECT_STATE.md`.
5. Read the target plan in `docs/plans/`.

## Global Constraints
- Implementation language: Python.
- Follow plan scope strictly (one task at a time unless explicitly expanded).
- TDD required: failing test first, then minimal implementation.
- Keep changes minimal and focused.
- Do not implement future tasks early.

## Definition of Completion Per Task
- Target test(s) added and passing.
- No unrelated refactors.
- `PROJECT_STATE.md` updated with current progress.
- `tasks/current_iteration.md` updated with task status.
- Final report includes changed files, test commands/results, blockers.

## Safety Rules
- Preserve deny-by-default ACL behavior.
- Unauthorized content must never be included in LLM context.
- Corporate email is the canonical user identifier for `acl_allow_users`.
