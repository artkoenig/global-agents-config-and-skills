Status: resolved
Type: fix
Blocked by: None

## Description

`worktree_guard.py` verweigert die Auflösung eines Merge-Konflikts im
Hauptcheckout — also genau die Tätigkeit, die AGENTS.md dort ausdrücklich
vorschreibt. Der Guard sieht mehrere geänderte Dateien und schließt auf eine
unerlaubte Direktänderung; dass ein Merge läuft, kann er nicht erkennen.

Das ist kein Randfall: sobald zwei Child-Branches dieselben Dateien anfassen,
entstehen zwangsläufig mehrere konfliktbehaftete Dateien im Hauptcheckout. Der
einzige heutige Ausweg ist der Bypass-Marker — er schaltet den Guard aber für
die **gesamte** restliche Sitzung ab, nicht nur für die Auflösung.

Ein Merge-Zustand ist zuverlässig erkennbar (`MERGE_HEAD` im Git-Verzeichnis).
Denkbar ist, in diesem Zustand genau die Dateien zuzulassen, die Git selbst als
konfliktbehaftet führt — der Guard bliebe damit für alles andere scharf.

**Zweiter Teil.** Beim Setzen des Markers zeigte sich eine Falle: ein `git add
-A` während der Konfliktauflösung nimmt `.claude/.worktree-bypass` mit in den
Commit. Eingecheckt würde die Datei den Guard dauerhaft und in jedem Checkout
deaktivieren — ein stiller, dauerhafter Verlust der Absicherung durch einen
Routinebefehl. Die Datei ist in keinem `.gitignore` erfasst.

## Acceptance Criteria
- [ ] Während eines laufenden Merges lässt der Guard die Bearbeitung der konfliktbehafteten Dateien zu
- [ ] Außerhalb eines Merges bleibt sein Verhalten unverändert
- [ ] Auch im Merge-Zustand bleiben Dateien blockiert, die nicht zum Konflikt gehören
- [ ] Der Bypass-Marker kann nicht versehentlich eingecheckt werden
- [ ] Beides ist durch deterministische Tests abgedeckt

## Comments
- worktree_guard.py erkennt den Merge-Zustand (git diff --diff-filter=U) und laesst die von Git als konfliktbehaftet gefuehrten Dateien im Hauptcheckout zu; alles andere bleibt auch waehrend des Merges blockiert, ausserhalb unveraendert. Bypass-Marker: in dieser .gitignore erfasst, und der Bootstrap-Skill (Schritt 5b) traegt den Eintrag in Ziel-Repos nach, sodass git add -A ihn nicht eincheckt. Tests: Merge-Ausnahme (Unit + echter Merge-Konflikt) und check-ignore.
