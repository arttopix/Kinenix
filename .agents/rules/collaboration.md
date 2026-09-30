# Developer Collaboration & Agent Rules

This document outlines interaction rules and working protocols between the AI Developer Agent and the human developer.

---

## 1. Blueprint First

- Present a clear blueprint, design overview, or architectural explanation to the user before executing extensive code modifications.
- Confirm critical assumptions when requirements are open or ambiguous.

---

## 2. Command Execution Safety

- Clearly explain the intent and potential impact of terminal or shell commands before running destructive or state-altering commands.
- Ensure commands operate strictly within the workspace boundaries.

---

## 3. Continuous Documentation & Rule Maintenance

- When new patterns, architectural choices, or conventions are agreed upon, immediately update the relevant document inside `.agents/rules/`.
- Ensure all technical documentation accurately reflects the current state of the codebase.

---

## 4. Git Operation Boundaries (No Autonomous Commit/Push)

- The AI Agent must **NEVER** run `git commit` or `git push` on its own.
- Always stop and wait for explicit user command before performing any commit or push actions.
