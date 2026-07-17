Status: ready-for-agent
Type: feature
Blocked by: None

## Description
Ein neuer read-only Subagent `docs-reviewer` (`agents/docs-reviewer/agent.md`,
Frontmatter `model: sonnet`, `tools: Read, Glob, Grep, Bash`), modelliert nach
`agents/spec-reviewer/agent.md`. Er beantwortet "Ist die Dokumentation noch
konsistent mit dem, was sich gerade geändert hat?" für den **Diff seit
Merge-Base** (`git merge-base <main_branch> HEAD` / `git diff <merge-base>`),
nicht für den ganzen Code-Stand.

Geprüfter Scope, generisch für jedes Repo: `CLAUDE.md` (Repo-Root), alle
`README*`-Dateien (Repo-Root) und alles unter `docs/**` rekursiv (ohne
Ausnahmen, auch generierte/Tracker-verwaltete Unterordner wie `docs/issues/**`
zählen dazu). Existiert nichts davon in einem Repo, meldet der Subagent sauber
"nichts im Scope gefunden" statt eines Fehlers.

Er meldet gefundenen Drift als Findings (`datei:zeile` + Ein-Zeilen-Begründung)
unter der Überschrift `## Docs`, mit abschließender Ein-Zeilen-Summary - auf
**Deutsch** (bewusste Abweichung von den englischen Berichten der anderen drei
Achsen). Er korrigiert nichts selbst, rein lesend wie `standards-reviewer` und
`spec-reviewer`.

Ist eigenständig aufrufbar, unabhängig von der `testing`-Skill-Einbindung (die
folgt in einem eigenen Issue).

## Acceptance Criteria
- [ ] `agents/docs-reviewer/agent.md` existiert mit Frontmatter `model: sonnet`,
      `tools: Read, Glob, Grep, Bash`, passender `description`.
- [ ] Direkt aufgerufen auf einem Diff mit gezielt eingebautem Doku-Drift (z.B.
      `CLAUDE.md` beschreibt Verhalten, das der Diff gerade ändert) liefert der
      Subagent einen `## Docs`-Bericht mit dem Fund (`datei:zeile` +
      Begründung).
- [ ] Direkt aufgerufen auf einem Diff mit konsistenter Doku liefert er
      "nichts gefunden" statt erfundener Findings.
- [ ] Aufgerufen in einem Repo ohne `CLAUDE.md`/`docs/`/`README*` meldet er
      sauber "nichts im Scope gefunden" statt eines Fehlers.
- [ ] Bericht ist auf Deutsch, ändert keine Dateien (rein lesend).

## Comments
