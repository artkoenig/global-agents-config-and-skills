Status: ready-for-agent
Type: fix
Blocked by: None

## Description
Heute ruft `issue-implementer` in seinem Verify-Schritt (Schritt 3,
`agents/issue-implementer/agent.md`) nach **jedem** Child-Issue die volle
`testing`-Skill (Drei-Achsen-Verifikation: Standards, Spec, Tests) auf. Das
widerspricht bereits dem, was `skills/issue-tracker/workflows/resolve.md`
(Schritt 2) selbst dokumentiert: "run the `testing` skill ... once per
main-issue, not per child-issue." Diese Inkonsistenz zwischen dokumentiertem
Anspruch und tatsächlichem Verhalten wird hiermit aufgelöst.

Ziel: Die volle `testing`-Skill (Standards + Spec + Tests) läuft künftig genau
einmal — beim Main-Issue, kurz bevor es auf `resolved` gesetzt wird (wie
bereits in `resolve.md` beschrieben) — und nicht mehr nach jedem einzelnen
Child-Issue/Sibling.

Offene Designfrage, die vor der Umsetzung zu klären ist: Soll
`issue-implementer` pro Child-Issue weiterhin wenigstens die reine
Testsuite laufen lassen (leichte Absicherung, kein Standards-/Spec-Review),
oder komplett auf jede Verifikation verzichten und alles dem Main-Issue-Gate
überlassen?

## Acceptance Criteria
- [ ] `issue-implementer`s Verify-Schritt ruft die volle `/testing`-Skill nicht
      mehr pro Child-Issue auf.
- [ ] Die volle `/testing`-Skill läuft weiterhin genau einmal pro Main-Issue,
      unmittelbar vor `resolved` (unverändert ggü. heute).
- [ ] `resolve.md`s Beschreibung des Verify-Schritts von `issue-implementer`
      ist an das neue Verhalten angepasst (keine veraltete Referenz auf "skips
      this step because issue-implementer already ran testing").
- [ ] Bestehende Verweise/Doku (implement.md, agent.md-Report-Abschnitt) sind
      konsistent mit dem neuen Verhalten.
- [ ] Bevor Child-Issues in Worktrees implementiert werden, ist der aktuelle
      Stand (inkl. der neu angelegten Issue-Dokumentation unter docs/issues/)
      im main-issue-Branch eingecheckt, damit jedes Worktree (das von diesem
      Branch-HEAD abzweigt) auf seine eigene issue.md zugreifen kann. Dieser
      Schritt ist in implement.md (Parallel Dispatch, vor Schritt 3
      "Dispatch") dokumentiert.

## Comments
