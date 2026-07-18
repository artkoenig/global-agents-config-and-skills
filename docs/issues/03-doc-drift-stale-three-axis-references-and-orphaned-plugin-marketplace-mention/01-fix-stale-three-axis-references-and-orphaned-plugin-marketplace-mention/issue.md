Status: ready-for-agent
Type: fix
Blocked by: None

## Description
Every doc describing this repo's own verification model says "four-axis"
consistently (matching `agents/docs-reviewer/agent.md` and
`skills/testing/SKILL.md`, which already got it right when the fourth axis
was added), and `skills/testing/SKILL.md`'s subagent-location description
matches how subagents are actually loaded (a direct git-clone-and-symlink
hook) instead of describing a defunct plugin-marketplace install.

Files to update:
- `agents/standards-reviewer/agent.md` — "three-axis" → "four-axis"
- `agents/spec-reviewer/agent.md` — "three-axis" → "four-axis"
- `agents/test-runner/agent.md` — "three-axis" → "four-axis"
- `agents/issue-implementer/agent.md` — 3 occurrences of "three-axis" → "four-axis"
- `skills/issue-tracker/workflows/resolve.md` — 2 occurrences of "three-axis" → "four-axis"
- `skills/testing/SKILL.md` — rewrite the subagent-location paragraph to drop
  the `artkoenig-skills` bundle name and "the plugin is installed" phrasing;
  describe the actual mechanism (subagents loaded via
  `cloud-session-bootstrap`'s git-clone-and-symlink hook)

## Acceptance Criteria
- [ ] A repo-wide grep for "three-axis" returns no hits describing this repo's own verification model (historical/changelog mentions, if any, are out of scope)
- [ ] `skills/testing/SKILL.md` no longer references the `artkoenig-skills` bundle name or a plugin-marketplace install path
- [ ] A repo-wide grep for "plugin is installed" and "artkoenig-skills" returns no remaining stale hits
- [ ] `python3 -m unittest discover -s scripts -p 'test_*.py'` still passes (doc-only change, no behavior expected to break)

## Comments
