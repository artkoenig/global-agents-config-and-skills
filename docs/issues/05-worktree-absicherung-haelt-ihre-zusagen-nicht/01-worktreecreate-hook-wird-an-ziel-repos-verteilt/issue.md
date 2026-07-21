Status: ready-for-agent
Type: fix
Blocked by: None

## Description

Der `WorktreeCreate`-Hook, der native Worktree-Pfade nach `.worktrees/<name>`
umleitet, existiert nur in der settings.json dieses Config-Repos. Die
settings.json-Vorlage im `cloud-session-bootstrap`-Skill enthält ihn nicht, also
bekommt ihn kein eingerichtetes Repo — obwohl AGENTS.md das zusagt.

Folge: Worktrees, die über die nativen Pfade entstehen (`EnterWorktree`,
`--worktree`, `isolation: worktree`), landen in `.claude/worktrees/` statt in
`.worktrees/`. Das umgeht die Konvention und den zugehörigen
`.gitignore`-Eintrag.

Zu klären ist dabei, ob die Hook-Definition dupliziert oder aus einer Quelle
bezogen wird — sie steht heute wörtlich in der settings.json dieses Repos und
würde als zweite Kopie in der Skill-Vorlage genau die Drift erzeugen, gegen die
der Skill sonst prüft.

## Acceptance Criteria
- [ ] Ein neu eingerichtetes Repo erhält den `WorktreeCreate`-Hook
- [ ] Ein bereits eingerichtetes Repo mit veralteter settings.json bekommt ihn beim nächsten Bootstrap-Lauf nachgetragen
- [ ] Die Drift-Prüfung des Skills erkennt einen fehlenden oder abweichenden `WorktreeCreate`-Hook
- [ ] Die Hook-Definition existiert nicht als zweite, unabhängig pflegbare Kopie
- [ ] Ein Worktree, der über die nativen Pfade entsteht, landet nachweislich unter `.worktrees/`

## Comments
