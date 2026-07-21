Status: resolved
Type: fix
Blocked by: None

## Description

AGENTS.md („Worktree Isolation") schreibt für direktes Arbeiten
`git worktree add .worktrees/<slug> <branch>` vor. Für den Branch der
laufenden Session schlägt das **immer** fehl: git verweigert einen Worktree
für einen bereits ausgecheckten Branch („fatal: '<branch>' is already checked
out"). Agents laufen wiederholt hinein und improvisieren dann — beobachtet am
2026-07-21 in einer army_builder-Session (Ausweg über `git worktree add -b
issue/...`) und in einer Session dieses Repos (Ausweg über `git worktree add
.worktrees/<slug>` ohne Branch-Argument mit anschließendem Merge zurück).

Das funktionierende Muster ist das des `WorktreeCreate`-Hooks: Worktree ohne
Branch-Argument anlegen (`git worktree add .worktrees/<slug>` brancht von
HEAD auf einen neuen Branch), dort arbeiten und committen, im Hauptcheckout
zurück in den Session-Branch mergen, Worktree und Hilfs-Branch entfernen —
identisch zum Ablauf eines Kind-Issue-Worktrees.

Betroffen sind die Stellen in AGENTS.md, die das Kommando mit `<branch>`
nennen (Abschnitt „Worktree Isolation", Aufzählung „Working directly" und die
Layout-Beschreibung). Reine Doku-Änderung, kein Code.

## Acceptance Criteria
- [x] AGENTS.md nennt kein `git worktree add` mit dem bereits ausgecheckten Session-Branch als Argument mehr
- [x] Das beschriebene Muster (von HEAD branchen, zurückmergen, aufräumen) ist an allen betroffenen Stellen konsistent
- [x] Die Beschreibung deckt sich mit dem Verhalten des `WorktreeCreate`-Hooks (branchen von HEAD)

## Comments
- Behoben: AGENTS.md 'Working directly' beschreibt jetzt das branchlose Muster (von HEAD, zurueckmergen); die Layout-Stelle nannte es bereits korrekt.
