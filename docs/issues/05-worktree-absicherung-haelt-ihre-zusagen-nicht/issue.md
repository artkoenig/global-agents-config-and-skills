Status: claimed
Type: fix
Blocked by: None

## Description

Beide Teile der Worktree-Absicherung sagen in AGENTS.md etwas zu, das sie in den
eingerichteten Repos nicht einlösen. Aufgefallen am 2026-07-21 während einer
Sitzung in `army_builder`.

**Problem 1 — der `WorktreeCreate`-Hook wird nie verteilt.**
AGENTS.md sagt, ein `WorktreeCreate`-Hook in `.claude/settings.json` leite
Claude Codes native Worktree-Pfade nach `.worktrees/<name>` um, damit jeder
Worktree in der Konvention dieses Repos landet. Der Hook existiert aber nur in
der settings.json **dieses** Config-Repos. Der `cloud-session-bootstrap`-Skill,
der die Ziel-Repos einrichtet, kennt ihn nicht: seine settings.json-Vorlage
enthält `PreToolUse` und `worktree.baseRef`, aber keinen `WorktreeCreate`.

Empirisch bestätigt: in `army_builder` sind vier `issue-implementer`-Worktrees
unter `.claude/worktrees/agent-*` gelandet statt unter `.worktrees/`. Die
Aussage in AGENTS.md gilt damit nur für dieses Repo selbst, nicht für die, die
es einrichtet.

**Problem 2 — der Guard blockiert die Auflösung eines Merge-Konflikts.**
AGENTS.md schreibt den Merge der Child-Branches ausdrücklich im Hauptcheckout
vor („the merge step back in the main checkout"). Genau dort greift
`worktree_guard.py` und verweigert die Auflösung: er sieht mehrere geänderte
Dateien im Hauptcheckout und wertet das als unerlaubte Direktänderung. Den
Merge-Zustand kennt er nicht.

Der Konflikt ist strukturell, nicht zufällig — ein nicht-trivialer Merge
zwischen zwei Child-Branches führt zwangsläufig zu mehreren konfliktbehafteten
Dateien im Hauptcheckout. Der einzige Ausweg war der Bypass-Marker, also die
vollständige Abschaltung des Guards für die restliche Sitzung; damit verliert
auch alles Nachfolgende seinen Schutz.

Beim Setzen des Markers trat zusätzlich eine Falle zutage: ein `git add -A` im
Zuge der Konfliktauflösung nimmt `.claude/.worktree-bypass` mit in den Commit.
Im Repo eingecheckt würde die Datei den Guard dauerhaft und für jeden Checkout
deaktivieren. Sie ist in keinem `.gitignore` erfasst.

## Acceptance Criteria
- [ ] Beide Zusagen aus AGENTS.md werden in eingerichteten Repos tatsächlich eingelöst
- [ ] Der Stand ist in AGENTS.md und im `cloud-session-bootstrap`-Skill konsistent beschrieben
- [ ] Die deterministischen Selbsttests decken beide Punkte ab

## Comments
