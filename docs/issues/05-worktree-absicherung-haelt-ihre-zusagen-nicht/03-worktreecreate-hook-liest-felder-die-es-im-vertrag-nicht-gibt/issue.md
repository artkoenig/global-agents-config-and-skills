Status: ready-for-agent
Type: fix
Blocked by: None

## Description

`worktree-create.sh` (Repo-Kopie `.claude/hooks/` und Asset in
`skills/cloud-session-bootstrap/assets/`) liest aus dem stdin-JSON die Felder
`worktree_name` und `base_ref`. Laut offizieller Hook-Doku
(https://code.claude.com/docs/en/hooks.md, Abschnitt "WorktreeCreate input")
erhält der Hook neben den Standardfeldern aber nur **`name`**:

```json
{"session_id": "...", "cwd": "...", "hook_event_name": "WorktreeCreate", "name": "feature-auth"}
```

`jq -r` liefert für fehlende Felder den String `"null"`, der Hook führt also
`git worktree add .worktrees/null null` aus — die Ref `null` existiert nicht,
der Befehl schlägt fehl. Wegen `set -euo pipefail` endet das Skript mit
Fehlercode, und die Doku sagt: jeder Fehlercode bricht die Worktree-Erstellung
ab. Folge in der Praxis (2026-07-21): Cloud-/Hintergrund-Sessions, die beim
Start in einen Worktree isoliert werden, konnten nicht mehr starten — das war
der Grund für den Revert von PR #14 (PR #15).

Weitere Doku-Befunde, die der Fix berücksichtigen muss:

- **Basis-Ref wählt der Hook selbst.** `worktree.baseRef` wird dem Hook nicht
  übergeben; ein WorktreeCreate-Hook ersetzt die native Logik vollständig.
  `git worktree add <pfad>` ohne Commit-ish brancht von HEAD — das entspricht
  genau dem gewollten `"head"`-Verhalten aus AGENTS.md.
- **Pfad-Regeln.** Der ausgegebene Pfad muss die letzte nicht-leere
  stdout-Zeile sein; sonstige Ausgabe nach stderr. Claude Code lehnt absolute
  Pfade mit `.`/`..`-Segmenten ab sowie Pfade, die unterhalb der Repo-Wurzel
  durch einen Symlink führen — der Hook muss einen normalisierten Pfad liefern.
- **Kein `.worktreeinclude`.** Ein konfigurierter Hook ersetzt auch das
  Kopieren git-ignorierter Dateien; für dieses Setup ist das akzeptabel und
  braucht keine Nachbildung.

## Acceptance Criteria
- [ ] Der Hook liest das dokumentierte Feld `name`; `worktree_name`/`base_ref` kommen nicht mehr vor
- [ ] Der Hook brancht von HEAD (Verhalten von `git worktree add <pfad>` ohne Ref), gemäß der `"head"`-Semantik aus AGENTS.md
- [ ] Gefüttert mit dem dokumentierten Input-JSON erzeugt der Hook einen Worktree unter `.worktrees/<name>` und gibt dessen Pfad als letzte stdout-Zeile aus
- [ ] Repo-Kopie und Skill-Asset bleiben byte-identisch (bestehender Sync-Test bleibt grün)
- [ ] Ein deterministischer Test ruft den Hook mit dem dokumentierten Input-JSON auf (nicht mit den alten Fantasie-Feldern) und deckt den HEAD-Branch-Fall ab
- [ ] `test_worktree_create.py` und SKILL.md widersprechen dem korrigierten Vertrag nirgends mehr

## Comments
