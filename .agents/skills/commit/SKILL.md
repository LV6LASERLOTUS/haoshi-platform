---
name: commit
description: Stage changes, review diffs, and write a conventional commit message
---

# Git Commit Workflow

When this skill is invoked:

1. Run `git status` and `git diff` to inspect current code modifications.
2. Draft a clear, concise commit message following the Conventional Commits specification (e.g., `feat: ...`, `fix: ...`, `refactor: ...`).
3. Present the proposed commit message to me for approval before executing `git commit -m "..."`. Do not auto-push unless explicitly requested.
