# global-agents-config-and-skills

Artjom König's global Claude Code configuration and personal skills. This
repository serves three roles:

1. **Global agent instructions** — `AGENTS.md` (symlinked as `~/.claude/CLAUDE.md`).
2. **Personal skills** — `skills/` (symlinked as `~/.claude/skills/`), so they
   load as personal-level skills on this machine.
3. **A Claude Code plugin marketplace** — so the same skills can be installed in
   environments that do *not* have this machine's `~/.claude/`, most importantly
   **cloud sessions**, teammates' machines, and CI.

## The marketplace

`.claude-plugin/marketplace.json` declares this repo as a marketplace named
`artkoenig`. It exposes one plugin, `artkoenig-skills`, whose root is the repo
root (`source: "./"`); the plugin bundles the entire `skills/` directory.

A "marketplace" is **not** a public app store — it is just a git repo Claude Code
can read plugin definitions from. This repo is **private**, so the skills stay
private. Visibility is governed solely by the git repo's visibility, never by
being a marketplace.

## Using the skills in a cloud session (or any machine without `~/.claude/`)

The local symlink into `~/.claude/skills/` does not exist in a fresh
environment, so install the plugin instead:

```
/plugin marketplace add artkoenig/global-agents-config-and-skills
/plugin install artkoenig-skills@artkoenig
```

Because the repo is private, the environment must be authenticated to GitHub with
access to it (the same access it uses to clone your working repo).

To make a project pull the plugin automatically, reference the marketplace in the
project's committed `.claude/settings.json` and enable the plugin there. The exact
setting keys and the `/plugin` flow are best confirmed in an interactive session.

### Note: instructions do not travel with the plugin

The plugin ships **skills only**. The global rules in `AGENTS.md` (e.g. "start a
new project with `grill-me-for-spec`") are not injected by installing the plugin.
The engineering-principle skills still auto-trigger via their own descriptions,
but any project-specific workflow rules you rely on should be added to that
project's `CLAUDE.md` / `AGENTS.md` separately.
