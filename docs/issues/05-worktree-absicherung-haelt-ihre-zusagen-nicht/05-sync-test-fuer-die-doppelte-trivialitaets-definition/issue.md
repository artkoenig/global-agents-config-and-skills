Status: ready-for-agent
Type: fix
Blocked by: None

## Description

`TRIVIAL_EXTENSIONS` (die Definition, welche Datei-Endungen als trivial
gelten) existiert zweimal: autoritativ in `scripts/git_workflow_rules.py` und
als Kopie in `worktree_guard.py` (Repo-Kopie + Asset). Die Kopie ist laut
Docstring „kept in sync by hand" — nichts prüft das. Driften die beiden,
entscheiden Pre-Edit-Gate (Guard) und Pre-Push-Gate (Hook) unterschiedlich,
was eine triviale Änderung ist.

Ein Cross-Repo-Import ist für den in Fremd-Repos installierten Guard bewusst
unmöglich (der Hook ist self-contained). Innerhalb **dieses** Repos kann ein
Unit-Test die Gleichheit aber deterministisch erzwingen — analog zu
`test_hook_asset_sync.py`, das bereits Repo-Kopie und Asset aneinander bindet.

Gleiches gilt für `PROTECTED_BRANCHES`, falls auch dort beide Module eine
eigene Kopie halten — prüfen und, wenn ja, mit absichern.

## Acceptance Criteria
- [ ] Ein deterministischer Test schlägt fehl, sobald `TRIVIAL_EXTENSIONS` in `git_workflow_rules.py` und `worktree_guard.py` (Asset) voneinander abweichen
- [ ] Weitere von Hand synchronisierte Konstanten zwischen den beiden Modulen sind identifiziert und gleich abgesichert oder als nicht vorhanden belegt
- [ ] Der Test läuft im bestehenden Suite-Discovery-Lauf (`python3 -m unittest discover -s scripts`) mit

## Comments
