Status: resolved
Type: feature
Blocked by: None

## Description
# PRD: Lokale Doku-Konsistenzprüfung als vierte testing-Achse

## Problem Statement / Bug Description
Die `testing`-Skill verifiziert Änderungen heute über drei Achsen (Standards,
Specification, Tests), aber keine davon prüft, ob Dokumentation (`CLAUDE.md`,
`README*`, alles unter `docs/**`) nach einer Änderung noch zum Code-Stand passt.
Bisher übernahm ein GitHub-Actions-Workflow (`doc-drift-check.yml` im
army_builder-Repo) diese Aufgabe projektspezifisch nach jedem Push auf `main` -
und ist zudem aktuell defekt, weil `claude-code-action@v1` den Event-Typ `push`
nicht unterstützt ("Unsupported event type: push"). Der Nutzer möchte diesen
Mechanismus nicht als GitHub Action, sondern lokal, generisch für alle seine
Projekte, als Teil dieser (globalen) `testing`-Skill.

## Solution
Eine vierte, verpflichtende Achse **D - Docs** wird der `testing`-Skill
hinzugefügt, analog zu den bestehenden drei Achsen als eigener read-only
Subagent (`docs-reviewer`). Sie beantwortet: "Ist die Dokumentation noch
konsistent mit dem, was sich gerade geändert hat?" Scope ist der Diff seit dem
Merge-Base (wie Axis B `spec-reviewer`), nicht der ganze Code-Stand. Sie prüft
generisch `CLAUDE.md` (Repo-Root), alle `README*`-Dateien und alles unter
`docs/**` (inklusive z.B. eines lokalen Issue-Trackers unter `docs/issues/**`,
falls vorhanden) gegen den Diff und meldet gefundenen Drift als Findings - sie
korrigiert nichts selbst, konsistent mit dem read-only-Muster von Standards und
Specification.

Der army_builder-seitige Aufräumschritt (defekten `doc-drift-check.yml`
entfernen, ADR 0007 aktualisieren) ist **nicht** Teil dieses main-issues - siehe
Out of Scope.

## User Stories / Requirements
1. Als Entwickler, der `/testing` vor einem PR laufen lässt, will ich, dass
   Doku-Drift gegen `CLAUDE.md`/`docs/**`/`README*` automatisch mitgeprüft
   wird, damit veraltete Doku nicht unbemerkt einreißt.
2. Als Entwickler will ich, dass die Docs-Achse bei jedem `testing`-Lauf
   verpflichtend mitläuft (wie Standards/Tests), nicht optional wie
   Specification, weil Doku-Konsistenz keine Ausnahme kennen soll.
3. Als Entwickler will ich, dass der Scope auf den Diff seit Merge-Base
   begrenzt ist, damit die Kosten proportional zur geprüften Änderung bleiben.
4. Als Nutzer mehrerer Projekte will ich, dass diese Achse generisch
   funktioniert (keine army_builder-Spezifika wie `vite.config.js`
   hartkodiert), damit sie in jedem Repo sinnvoll läuft, auch ohne
   `docs/`-Ordner oder `CLAUDE.md`.

## Technical Decisions
- Affected Modules:
  - `skills/testing/SKILL.md` - Aufnahme von Axis D in die Dispatch-Tabelle
    und den "immer laufen"-Satz (Zeile 33 nennt aktuell nur A und C).
  - Neue Subagent-Definition `agents/docs-reviewer/agent.md` (Frontmatter
    `model: sonnet`, `tools: Read, Glob, Grep, Bash`, read-only), modelliert
    nach `agents/spec-reviewer/agent.md`s "Step 1: Determine the diff base"
    (`git merge-base <main_branch> HEAD` / `git diff <merge-base>`).
- Technical Clarifications / Architectural Decisions:
  - Sprache des Berichts: **Deutsch** (bewusste Abweichung von den englischen
    Berichten der anderen drei Achsen - explizite Nutzerentscheidung).
  - Mandatory statt optional: Axis D läuft immer, meldet aber sauber "keine
    Doku im Scope gefunden", wenn ein Repo weder `CLAUDE.md` noch `docs/`
    noch `README*` hat.
  - Doku-Scope-Default: `CLAUDE.md` (Root) + `README*` (Root) + alles unter
    `docs/**` rekursiv, ohne Ausnahmen (auch generierte/Tracker-verwaltete
    Unterordner wie `docs/issues/**` zählen dazu - explizite
    Nutzerentscheidung).
- API Contracts / Data Models:
  - Bericht-Format wie die anderen Achsen: Überschrift `## Docs`, Findings mit
    `datei:zeile` + Ein-Zeilen-Begründung, abschließende Ein-Zeilen-Summary.

## Testing Decisions
- Modules to Test: `skills/testing/SKILL.md` (Dispatch), `agents/docs-reviewer/agent.md` (Scope/Verhalten).
- Test Interfaces (Seams):
  1. **`testing`-Skill-Lauf als Hauptseam**: Lauf auf einem Branch mit gezielt
     eingebautem Doku-Drift muss eine `## Docs`-Sektion mit dem Fund liefern;
     ein Lauf mit konsistenter Doku muss "nichts gefunden" liefern.
  2. **Verpflichtende Einbindung**: Axis D wird bei jedem `testing`-Lauf
     mitdispatcht, nicht nur bei vorhandener Spec-Quelle.

## Out of Scope
- Ein formales Behavioral Eval in der `self-test`-Skill - explizit nicht
  gewollt; Verifikation erfolgt manuell über die beiden Seams oben.
- Projektspezifische Scope-Erweiterung via Konventionsdatei (analog
  `test-command.txt`) - der generische Default-Scope (`CLAUDE.md`, `README*`,
  `docs/**`) reicht vorerst; kann bei Bedarf später nachgezogen werden.
- Entfernen von `.github/workflows/doc-drift-check.yml` und Aktualisierung von
  ADR 0007 im army_builder-Repo - gehört dorthin, nicht in dieses (globale)
  main-issue.
- Automatisches Fixen von Doku-Drift (nur Melden, kein Auto-Fix) - Abkehr vom
  Verhalten des alten GitHub-Workflows.
- Ein zusätzlicher lokaler Git-Hook für kontinuierliche Post-Merge-Prüfung -
  die Achse läuft ausschließlich on-demand über `/testing`.
- Migration/Anpassung bestehender Projekte, die den alten GitHub-Workflow
  nutzen (das betrifft nur army_builder und wird dort separat behandelt).

## Acceptance Criteria
- [ ]

## Comments
- Beide Child-Issues implementiert: docs-reviewer Subagent (agents/docs-reviewer/agent.md) + verpflichtende Einbindung als Axis D in skills/testing/SKILL.md. Deterministische Tests gruen (21/21).
- testing (4 Achsen) gruen nach drei Iterationen: Terminologie-Fix in docs-reviewer/agent.md, README.md-Update, und Revert eines unrelated AGENTS.md/tracker-bootstrap Scope-Creeps (Spec-Achse fand das). Finaler Diff: agents/docs-reviewer/agent.md (neu), skills/testing/SKILL.md, README.md.
