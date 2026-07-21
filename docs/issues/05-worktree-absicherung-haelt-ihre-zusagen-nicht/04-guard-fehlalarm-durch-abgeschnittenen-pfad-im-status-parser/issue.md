Status: resolved
Type: fix
Blocked by: None

## Description

`worktree_guard.py` (Repo-Kopie `.claude/hooks/` und Asset in
`skills/cloud-session-bootstrap/assets/`) parst `git status --porcelain`
fehlerhaft: `_run_git` gibt `result.stdout.strip()` zurück und strippt damit
das führende Leerzeichen der **ersten** Ausgabezeile. Beginnt die erste Zeile
mit einem Leerzeichen — der Normalfall ` M datei` einer unstaged geänderten
Datei — verschiebt sich das `line[3:]`-Slicing in `_dirty_files` um ein
Zeichen und schneidet das erste Zeichen des Pfads ab.

Reproduziert (2026-07-21): eine einzige unstaged geänderte Datei
`docs/adr/0001-test.md` wird als `ocs/adr/0001-test.md` geparst. Der Guard
zählt sie dann doppelt — einmal als Phantomdatei `ocs/...`, einmal als die
eigentlich editierte Datei — und verweigert eine echt triviale
Ein-Datei-Änderung mit „would not be the only dirty file". Genau dieser
Fehlalarm wurde am selben Tag in einer army_builder-Session beobachtet
(Doppelzählung mit `ocs/adr/...`).

Ursache exakt: `_run_git` (`worktree_guard.py`, `stdout.strip()`) ist für
Ein-Wert-Ausgaben wie `rev-parse` richtig, für die zeilenweise geparste
`status --porcelain`-Ausgabe falsch. Der Fix darf das Verhalten der übrigen
Aufrufer nicht ändern.

## Acceptance Criteria
- [x] Eine unstaged geänderte Datei an erster Stelle der Porcelain-Ausgabe wird mit vollem Pfad geparst
- [x] Der Reproduktionsfall (einzige dirty Datei ` M docs/adr/x.md`, Edit ebendieser Datei) wird erlaubt
- [x] Die übrigen `_run_git`-Aufrufer (`rev-parse`, `symbolic-ref`, `diff`) verhalten sich unverändert
- [x] Ein deterministischer Regressionstest deckt den Fall ab (erste Zeile mit führendem Leerzeichen)
- [x] Repo-Kopie und Skill-Asset bleiben byte-identisch (Sync-Test bleibt grün)

## Comments
- Behoben (Merge 7c696d5): _run_git mit strip-Parameter, Porcelain-Aufruf strippt nicht mehr global; zwei Regressionstests. Der Fehler trat waehrend der Umsetzung zweimal live in dieser Session auf (docs/issues- und skills-Pfade als ocs/kills geparst).
