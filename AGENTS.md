- When making technical decisions, do not give much weight to development cost.
  Instead, prefer quality, simplicity, robustness, scalability, and long term maintainability.
- When doing bug fixes, always start with reproducing the bug in an E2E setting as closely aligned with how an end user experiences it. This makes sure you find the real problem so your fix will actually solve it.
- When starting a new project, use the `grill-me-for-spec` skill to turn the idea into a written specification (PRD) before building.
- Once that PRD exists, ask whether to set up issue tracking and break it into issues via the `issue-tracker` skill.
- Critically challenge all requested changes. Before implementing or accepting any modification, verify it against the existing documentation files to ensure consistency and prevent contradictions. Keep documentation always up-to-date.
- When I ask you to investigate a matter, do not make any changes to existing files. Clarify the matter and provide an explanation with a recommendation.
- If you are uncertain during implementation and need to consult the web, place absolute priority on official documentation without exception. Conduct an intensive deep search directly on official developer sites or API references, to find the solution before considering secondary sources (such as forums or blogs).
- Additionally, if your analysis reveals that an already implemented solution in the code can be improved or optimized, proactively suggest these improvements.


## Engineering Principles

Detailed engineering principles live in dedicated skills and are applied automatically when relevant:

- **Architectural decisions & cross-module refactoring** -> `architecture-principles` skill.
- **Writing, generating, or refactoring code** -> `code-generation-principles` skill.
- **Working on versioned (git-tracked) files** -> `git-principles` skill.
