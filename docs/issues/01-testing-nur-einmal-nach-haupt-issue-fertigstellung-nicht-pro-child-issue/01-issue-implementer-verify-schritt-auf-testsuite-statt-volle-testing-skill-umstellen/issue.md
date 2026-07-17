Status: ready-for-agent
Type: fix
Blocked by: None

## Description
`agents/issue-implementer/agent.md` Schritt 3 "Verify" ruft aktuell die volle
`testing`-Skill (Drei-Achsen: Standards, Spec, Tests) für jedes einzelne
Child-Issue auf. Das soll entfallen — pro Child-Issue läuft künftig nur noch
die reine Testsuite, delegiert an den `test-runner` Subagenten (statt inline
oder über die volle `testing`-Skill). Die volle Drei-Achsen-`testing`-Skill
bleibt exklusiv dem Main-Issue vorbehalten (unverändert, siehe
`resolve.md`).

Der Report-Abschnitt von `issue-implementer` ist entsprechend anzupassen: statt
"pass/fail per axis" wird nur noch das Testsuite-Ergebnis (grün/rot)
berichtet. Die Acceptance-Criteria-Tabelle bleibt bestehen, wird aber vom
Implementer selbst anhand des eigenen Issues bewertet, nicht mehr automatisch
von Axis B (Spec-Reviewer) geprüft — dieses automatische Spec-Review
verschiebt sich vollständig auf den einmaligen Main-Issue-Testlauf.

`skills/issue-tracker/workflows/resolve.md` Schritt 2 enthält die inzwischen
falsche Aussage "Child-issues skip this step: issue-implementer's own Verify
step already ran the same three-axis testing skill against that single
vertical slice during implementation." Diese Formulierung ist zu korrigieren,
damit sie das neue Verhalten beschreibt (Child-Issues laufen nie mit der
vollen testing-Skill, nur mit der reinen Testsuite).

## Acceptance Criteria
- [ ] `issue-implementer`s Verify-Schritt ruft `/testing` nicht mehr auf,
      sondern delegiert an `test-runner` und lässt nur die Testsuite laufen.
- [ ] Der Report-Abschnitt von `issue-implementer` spiegelt das neue Verhalten
      wider (kein Standards-/Spec-Achsen-Ergebnis mehr pro Child-Issue).
- [ ] `resolve.md` Schritt 2 beschreibt korrekt, dass Child-Issues nie die
      volle `testing`-Skill laufen lassen (nur Testsuite via `test-runner`),
      und dass die volle Skill weiterhin genau einmal, beim Main-Issue, läuft.
- [ ] Bestehende Tests/Selftest der issue-tracker-Engine bleiben grün.

## Comments
