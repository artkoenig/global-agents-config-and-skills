# CONTEXT.md Format

## Structure

```md
# {Name of the context}

{One to two sentences describing what this context is about and why it exists.}

## Language / Glossary

**{Primary Term}**:
{One to two sentences precisely describing the term.}
_Avoid_: {Imprecise Alternative 1}, {Imprecise Alternative 2}

**{Another Term}**:
{One to two sentences precisely describing this term.}
_Avoid_: {Synonym to exclude}
```

## Rules

- **Be opinionated.** If multiple words exist for the same concept, pick the best one and list the others under `_Avoid_`.
- **Keep definitions short.** Maximum one or two sentences. Define what it IS, not what it does.
- **Only include terms specific to the context of this project.** General programming concepts (timeouts, error types, helper patterns) do not belong here, even if the project uses them extensively. Before adding a term, ask yourself: Is this a concept unique to this context, or a general programming concept? Only the former belongs here.
- **Group terms under subheadings** if natural clusters form. If all terms belong to a single cohesive area, a flat list is fine.

## Repositories with Single vs. Multiple Contexts

**Single Context (most repos):** A `CONTEXT.md` in the project root.

**Multiple Contexts:** A `CONTEXT-MAP.md` in the project root lists the contexts, where they are located, and how they relate to each other:

```md
# Context Map

## Contexts

- [{Context A}](./src/{context-a}/CONTEXT.md) — {Brief description of Context A}
- [{Context B}](./src/{context-b}/CONTEXT.md) — {Brief description of Context B}

## Relationships

- **{Context A} → {Context B}**: {Relationship / Event flow from Context A to Context B}
- **{Context A} ↔ {Context B}**: {Shared types / contracts}
```

The skill infers which structure applies:

- If a `CONTEXT-MAP.md` exists, read it to find the contexts.
- If only a `CONTEXT.md` exists in the root, it is a single context.
- If neither exists, lazily create a `CONTEXT.md` in the root as soon as the first term is clarified.

If multiple contexts exist, infer which context the current topic relates to. If it is unclear, ask.
