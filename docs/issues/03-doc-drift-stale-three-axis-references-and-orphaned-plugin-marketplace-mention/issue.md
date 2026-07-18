Status: needs-triage
Type: fix
Blocked by: None

## Description
Found during a self-test run (standards-reviewer-style code-health review). Two independent doc-drift issues in this repo's own agent/skill docs:

1. **Stale "three-axis" references after `docs-reviewer` (Axis D) was added.** `agents/docs-reviewer/agent.md:3` and `skills/testing/SKILL.md` correctly say "four-axis," but these still say "three-axis":
   - `agents/standards-reviewer/agent.md:3`
   - `agents/spec-reviewer/agent.md:3`
   - `agents/test-runner/agent.md:3`
   - `agents/issue-implementer/agent.md:64,67,109` ("not the full three-axis `testing` skill")
   - `skills/issue-tracker/workflows/resolve.md:22,33`

   Notably, `docs/issues/02-lokale-doku-konsistenzpruefung-als-vierte-testing-achse/02-docs-achse-verpflichtend-in-testing-skill-verankern/issue.md` is `Status: resolved` and its acceptance criteria explicitly claim "Alle 'three-axis'-Stellen auf vier Achsen aktualisiert" (all "three-axis" spots updated to four axes) — that was not actually done for the files above.

2. **Orphaned reference to a defunct plugin architecture.** `skills/testing/SKILL.md:50-52` still says the axis subagents are "defined in `agents/` at the repository root of the `artkoenig-skills` bundle... or under the `artkoenig-skills:` prefix where the plugin is installed." This repo is actually named `global-agents-config-and-skills` (`README.md:1`), and per `skills/cloud-session-bootstrap/SKILL.md:9` / `assets/session-start.sh`, there is no plugin marketplace anymore — subagents load via a direct git-clone-and-symlink hook, not a plugin install.

Both are doc-only corrections; no code behavior changes.

## Acceptance Criteria
- [ ] Every remaining "three-axis" mention describing this repo's own verification model is updated to "four-axis" (the five locations listed above, plus any others a repo-wide grep for "three-axis" turns up)
- [ ] `skills/testing/SKILL.md:50-52`'s subagent-location description no longer references the `artkoenig-skills` bundle name or a plugin-marketplace install path; it describes the actual git-clone-and-symlink mechanism
- [ ] A repo-wide grep for "three-axis" and for "plugin is installed"/"artkoenig-skills" returns no remaining stale hits outside of historical/changelog context

## Comments
