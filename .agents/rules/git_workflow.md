# Git Workflow & Commit Guidelines

This document establishes Git branch naming conventions, commit message standards, and repository hygiene for **kinenix**.

---

## 1. Commit Message Convention

Adopt Conventional Commits format for all commit messages. Emojis in commit messages are strictly prohibited.

### Format
```text
<type>(<scope>): <short description in present tense>

[optional body explaining rationale]
```

### Supported Types
- `feat`: A new feature or capability (e.g., `feat(kinenix-core): add support for subflow calls`)
- `fix`: A bug fix (e.g., `fix(engine): resolve variable resolution for nested objects`)
- `docs`: Documentation updates (e.g., `docs(rules): split rules into modular files`)
- `refactor`: Code changes that neither fix a bug nor add a feature
- `test`: Adding or correcting tests (e.g., `test(core): add unit tests for excel action`)
- `perf`: Code changes that improve performance
- `chore`: Build process, dependency updates, or auxiliary tool changes

---

## 2. Branch Naming Conventions

- `main`: Stable, release-ready branch.
- `develop`: Primary integration branch for active development.
- `feature/<short-description>`: New features or components (e.g., `feature/tauri-canvas`).
- `bugfix/<short-description>`: Fixes for non-critical bugs.
- `hotfix/<short-description>`: Urgent production fixes branched directly off `main`.

---

## 3. Commit and Repository Hygiene

- **Atomic Commits:** Keep commits focused on a single logical change. Do not bundle unrelated modifications across different modules into a single commit.
- **Excluded Artifacts:** Never commit temporary files, credentials, local virtual environments, or run outputs:
  - Python virtual environments (`.venv/`, `env/`)
  - Python cache directories (`__pycache__/`, `*.pyc`)
  - Execution run artifacts (`logs/*.json`, screenshots, error dumps)
  - Test caches (`.pytest_cache/`)
  - Sensitive environment variable files (`.env`, `.env.local`)

---

## 4. Strict Commit & Push Authorization Rule (No Autonomous Git Actions)

- **Explicit User Command Mandatory:** The AI Agent is strictly prohibited from executing `git commit` or `git push` autonomously.
- **Wait for Instructions:** Even if tests pass, features are complete, or files are staged, the agent must summarize the work and **WAIT** for explicit user instructions (e.g. *"commit"*, *"push"*, *"commit ขึ้น branch นี้"*) before running any commit or push command.
- **No Unsolicited Pushes:** Never push to any remote branch without direct, unambiguous user authorization.
