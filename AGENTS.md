- When making technical decisions, do not give much weight to development cost.
  Instead, prefer quality, simplicity, robustness, scalability, and long term maintainability.
- When doing bug fixes, always start with reproducing the bug in an E2E setting as closely aligned with how an end user experiences it. This makes sure you find the real problem so your fix will actually solve it.
- When starting a new project, use the `grill-me-for-spec` skill to turn the idea into a written specification (PRD) before building.
- Critically challenge all requested changes. Before implementing or accepting any modification, verify it against the existing documentation files to ensure consistency and prevent contradictions. Keep documentation always up-to-date.
- When I ask you to investigate a matter, do not make any changes to existing files. Clarify the matter and provide an explanation with a recommendation.

## Engineering Principles

Detailed engineering principles live in dedicated skills and are applied automatically when relevant:

- **Architectural decisions & cross-module refactoring** -> `architecture-principles` skill.
- **Writing, generating, or refactoring code** -> `code-generation-principles` skill.
- **Working on versioned (git-tracked) files** -> `git-principles` skill.
