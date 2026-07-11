# ADR Format

ADRs are located in `docs/adr/` and use sequential numbering: `0001-slug.md`, `0002-slug.md`, etc.

Create the `docs/adr/` directory lazily — only when the first Architectural Decision Record (ADR) is actually needed.

## Template

```md
# {Short title of the decision}

{1-3 sentences: What is the context, what did we decide and why.}
```

That's it. An ADR can consist of a single paragraph. The value lies in documenting *that* a decision was made and *why* — not in filling out sections.

## Optional Sections

Only add these if they provide real value. Most ADRs don't need them.

- **Status** Frontmatter (`proposed | accepted | deprecated | superseded by ADR-NNNN`) — useful if decisions are revised later
- **Considered Options** — only if the rejected alternatives are worth remembering
- **Consequences** — only if non-obvious follow-up effects need to be highlighted

## Numbering

Search `docs/adr/` for the highest existing number and increment it by one.

## When to propose an ADR

All three of the following criteria must be met:

1. **Hard to reverse** — the cost of changing the decision later is significant.
2. **Surprising without context** — a future reader will look at the code and wonder, "Why on earth did they do it this way?"
3. **Result of a real trade-off** — there were genuine alternatives and one was chosen for specific reasons.

If a decision is easy to reverse, skip it — you'll simply reverse it if in doubt. If it's not surprising, no one will wonder why. If there was no real alternative, there is nothing to document other than "we did the obvious thing".

### What qualifies

- **Architectural structure.** E.g., Monorepo vs. Multi-repo, separation of read and write model (CQRS), or layered architecture.
- **Integration patterns between contexts.** E.g., asynchronous event-driven communication vs. synchronous API calls.
- **Technology decisions with lock-in effect.** Selection of system components like database technologies, message brokers, authentication providers, or deployment platforms.
- **Boundary and scope decisions.** Definition of data sovereignty (e.g., which context owns certain master data and how other contexts reference it).
- **Conscious deviations from the standard path.** When an unusual decision is made (e.g., foregoing a specific framework or library for specific reasons) to prevent future developers from viewing this as an "error" and reverting it.
- **Constraints not directly visible in the code.** Requirements from compliance, regulatory demands, or contractual assurances (e.g., maximum latency times).
- **Rejected alternatives for non-obvious decisions.** When a valid alternative was intensely discussed but ultimately rejected, to prevent the discussion from having to be repeated in the future.
