Status: ready-for-agent
Type: fix
Blocked by: None

## Description
Ein Worktree wird als eigene, von einem Commit abzweigende Kopie des Repos
angelegt und sieht daher nur committete Historie — keine uncommitteten
Änderungen im ursprünglichen Checkout. Wenn nach `decompose.md` neue
Child-Issues unter `docs/issues/` angelegt, aber noch nicht committet wurden,
und direkt danach `implement.md`s "Parallel Dispatch" `issue-implementer`
Subagenten in eigene Worktrees spawnt, kann keiner dieser Subagenten seine
eigene `issue.md` lesen — sie existiert nur im Hauptcheckout, uncommitted.

`implement.md` (Section A, Parallel Dispatch) soll vor Schritt 3 "Dispatch"
einen expliziten Schritt bekommen: der aktuelle Stand des main-issue-Branches
(inklusive der neu angelegten Issue-Dokumentation unter `docs/issues/`) muss
eingecheckt sein, bevor Worktrees für `issue-implementer` gespawnt werden.
Da dies im Checkout des Nutzers passiert, gilt AGENTS.md's Regel "nie
automatisch committen" weiterhin — der Schritt fragt also nach Bestätigung
bzw. hält fest, dass ohne diesen Commit die Worktrees nicht funktionieren.

Zusätzlich soll `decompose.md`s Handoff-Abschnitt (Schritt 6) einen Verweis
auf diese Voraussetzung bekommen, damit der Zusammenhang beim Übergang von
Decompose zu Implement sichtbar ist.

## Acceptance Criteria
- [ ] `implement.md` (Section A) enthält vor Schritt 3 "Dispatch" einen
      Schritt, der das Committen des main-issue-Branch-Standes (inkl.
      `docs/issues/`) vor dem Worktree-Spawn verlangt.
- [ ] Dieser Schritt respektiert AGENTS.md's "nie automatisch committen"-Regel
      (fragt nach oder macht die Voraussetzung explizit, statt selbst zu
      committen).
- [ ] `decompose.md`s Handoff-Abschnitt (Schritt 6) verweist auf diese
      Voraussetzung.
- [ ] Bestehende Tests/Selftest der issue-tracker-Engine bleiben grün.

## Comments
