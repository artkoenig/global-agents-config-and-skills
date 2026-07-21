Status: claimed
Type: fix
Blocked by: [06]

## Description

Beobachtetes Symptom (mehrfach, zuletzt 2026-07-21 in diesem Repo): ein
Haupt-Issue erreicht sein Abschluss-Gate — alle Kind-Issues geschlossen,
Verifikation grün — und der Pull Request wird trotzdem nicht angelegt; die
Session hält an und fragt.

Zwei Regelstellen erzeugen den Konflikt:

1. **`resolve.md` Schritt 4** (issue-tracker-Skill): „For a resolved
   **child**-issue in the user's checkout, report it and let the user decide
   when to commit." Beim **letzten** Kind-Issue eines Haupt-Issues erzwingt
   dieser Satz einen Halt unmittelbar vor dem Gate: ohne den Commit der
   Kind-Auflösung kann das Haupt-Issue nicht `resolved` werden, also feuert
   die automatische Push+PR-Regel nie — obwohl sie genau dafür existiert,
   AFK durchzulaufen.
2. **AGENTS.md „Commits & pushes"**: „Never commit or push automatically —
   only when I explicitly ask" steht als erste, absolute Regel; die
   Gate-Ausnahme ist ein Nebensatz. In der Abwägung gewinnt das Verbot, und
   die Session fragt statt zu handeln.

Gewolltes Verhalten (vom Maintainer bestätigt): Sobald das letzte Kind-Issue
geschlossen und die Vier-Achsen-Verifikation grün ist, ist
Kind-Commit → Haupt-Issue `resolved` → Commit → Push → PR **eine
ununterbrochene Sequenz ohne Rückfrage**. Ein Halt ist nur gerechtfertigt,
wenn die Verifikation blockierende Funde liefert oder eine echte
Scope-Entscheidung offen ist.

Zu ändern: `resolve.md` (Schritt 4: Ausnahme für das letzte Kind-Issue,
Schritt 5 ggf. schärfen) und AGENTS.md (Gate-Ausnahme als eigenständige,
gleichrangige Regel formulieren statt als Nebensatz). Reine Doku-Änderung.
Blockiert durch 06, weil beide dieselbe AGENTS.md-Sektion anfassen.

## Acceptance Criteria
- [ ] `resolve.md` verlangt beim letzten Kind-Issue eines Haupt-Issues keinen Nutzer-Halt mehr vor dem Commit
- [ ] Die Sequenz „letztes Kind zu → testing grün → Haupt-Issue resolved → Commit → Push → PR" ist in resolve.md und AGENTS.md als ununterbrochen und rückfragefrei beschrieben
- [ ] Die zulässigen Haltegründe (blockierende Funde, offene Scope-Entscheidung) sind explizit benannt
- [ ] AGENTS.md formuliert die Gate-Ausnahme gleichrangig zum „Never commit"-Verbot, sodass kein Widerspruch mehr besteht

## Comments
