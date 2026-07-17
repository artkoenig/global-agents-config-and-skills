Status: ready-for-agent
Type: feature
Blocked by: [01]

## Description
`skills/testing/SKILL.md` bindet den neuen `docs-reviewer` als vierte,
**verpflichtende** Achse D - Docs ein, analog zu Axis A (Standards) und Axis C
(Tests) - nicht optional wie Axis B (Specification).

Änderungen:
- Dispatch-Tabelle (`## The axis subagents`) um Zeile `D | Docs |
  docs-reviewer | der Diff | sonnet` erweitern.
- Den "Always run"-Satz in Schritt 1 (aktuell nur Axis A und C) um Axis D
  erweitern.
- Konsolidierung (Schritt 2) um die `## Docs`-Sektion des Subagenten ergänzen,
  inklusive Nennung in der Ein-Zeilen-Summary.
- Die einleitende Beschreibung ("three-axis verification") auf vier Achsen
  aktualisieren (Skill-Name/Frontmatter-`description` bleibt ansonsten
  unangetastet, sofern kein Widerspruch entsteht).

## Acceptance Criteria
- [ ] Ein `/testing`-Lauf auf einem Branch mit gezielt eingebautem Doku-Drift
      liefert im konsolidierten Bericht eine `## Docs`-Sektion mit dem Fund.
- [ ] Ein `/testing`-Lauf mit konsistenter Doku liefert eine `## Docs`-Sektion
      mit "nichts gefunden" - die Achse wird trotzdem immer angestoßen, nicht
      übersprungen.
- [ ] Axis D wird bei jedem `/testing`-Lauf mitdispatcht, unabhängig davon, ob
      eine Spec-Quelle für Axis B vorhanden ist.
- [ ] `SKILL.md` beschreibt konsistent vier statt drei Achsen (keine
      verbliebenen Stellen, die noch "three-axis" behaupten, ohne Docs zu
      erwähnen).

## Comments
