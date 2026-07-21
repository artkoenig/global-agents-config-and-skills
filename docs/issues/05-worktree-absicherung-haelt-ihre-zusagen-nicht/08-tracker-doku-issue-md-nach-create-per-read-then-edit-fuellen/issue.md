Status: resolved
Type: fix
Blocked by: None

## Description

Beobachtete Reibung (army_builder-Session, 2026-07-21): Nach
`tracker.py create` will der Agent die frisch erzeugte `issue.md` per `Write`
mit der Beschreibung füllen und scheitert an der Harness-Regel „File has not
been read yet" — `Write` überschreibt nur Dateien, die in der Session bereits
gelesen wurden. Der Agent muss auf Read-then-Edit/Write ausweichen und
verliert einen Versuch.

Die Tracker-Doku, die Agents in Ziel-Repos anleitet, erwähnt das nirgends.
Betroffene Stellen im issue-tracker-Skill dieses Repos:

- die in `tracker.py` eingebettete Vorlage (`TRACKER_DOC`), die `init` als
  `docs/agents/issue-tracker.md` in Ziel-Repos schreibt,
- `workflows/decompose.md`, wo das Befüllen der Kind-Issue-Beschreibungen
  beschrieben ist.

Ein Satz an diesen Stellen genügt: nach `create` die erzeugte `issue.md`
erst lesen, dann per Edit/Write befüllen.

## Acceptance Criteria
- [x] Die von `init` geschriebene Tracker-Doku weist auf Read-then-Edit für frisch erzeugte issue.md-Dateien hin
- [x] `decompose.md` enthält denselben Hinweis an der Stelle, die das Befüllen beschreibt
- [x] `tracker.py selftest` und die deterministische Suite bleiben grün

## Comments
- Behoben (Merge a7bb6c6): Hinweis in TRACKER_DOC (tracker.py) und decompose.md Schritt 4. Dieses Repo selbst hat kein docs/agents/ — Ziel-Repos erhalten den Text beim naechsten init.
