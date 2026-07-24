# PRD: Testbarer Workflow für AGENTS.md, Skills & Subagents

> Diese PRD ersetzt die vorherige, verworfene Fassung vollständig. Sie hält den
> in dieser Session neu spezifizierten Workflow fest. Die begleitenden sechs
> Sequenzdiagramme sind die visuelle Referenz zu diesem Dokument (Abb. 1–6).

## Problem Statement

`AGENTS.md` und die Skills/Subagents dieses Repos steuern, wie Claude Code in
jedem eigenen Repository arbeitet — Branch-Benennung, kein direkter Push auf
`main`, kein Agent als Commit-Co-Author, Worktree-Isolation, Delegation an
Subagenten, das Lesen der Engineering-Prinzipien vor dem Coden, die
Nachfragepflicht bei Issue-Tracking. **Keine** dieser Regeln wird heute
automatisch verifiziert. Sie können still verwässern oder schlicht vergessen
werden, ohne Signal — bis die Folge (ein schlechter Commit, eine übersprungene
Delegation, eine nicht gestellte Rückfrage) bereits eingetreten ist.

Zusätzlich ist die Issue-Logik heute lose: Issues verschachteln sich, jedes
Blatt-Issue kann einen eigenen Branch und PR bekommen, und Issue-Tracking ist
optional. Das erschwert eine klare 1:1-Zuordnung zwischen einer Arbeitseinheit
und einem Branch/PR und damit auch die Testbarkeit der Branch-Regeln.

`skill-creator` besitzt bereits einen Eval-Mechanismus (`evals/evals.json`,
`agents/grader.md`, `references/schemas.md`), aber nur für den interaktiven
Autoren-Workflow eines einzelnen Skills. Er hat keinen unbeaufsichtigten,
automatisch ausgelösten Modus, deckt Subagenten und AGENTS.md-Regeln nicht ab,
und seine `evals/`-Verzeichnisse sind vom Packaging ausgeschlossen
(`ROOT_EXCLUDE_DIRS = {"evals"}`) — also als Wegwerf-Gerüst behandelt statt als
committeter, dauerhaft vorhandener Teil des Repos.

## Solution (Überblick)

Der Workflow wird umgebaut und durchgängig testbar gemacht. Zwei orthogonale
Änderungen:

1. **Umbau der Issue-/Branch-Logik.** Genau eine Arbeitseinheit = ein
   Top-Level-Issue („Haupt-Issue") = ein Branch `issue/<slug>` = ein Pull
   Request (und, nur lokal, = ein Worktree). Mehrere Haupt-Issues laufen lokal
   **gleichzeitig**, jedes in einer eigenen Claude-Code-Session in einem eigenen
   Worktree unter `.worktrees/`. Kind-Issues eines Haupt-Issues werden
   **innerhalb** seiner Session **sequenziell, eines nach dem anderen** in
   Abhängigkeitsreihenfolge direkt auf dem Haupt-Issue-Branch implementiert
   (issue-implementer, ohne eigenen Worktree, kein Merge) — nie parallel.
   Cloud-Sessions (`CLAUDE_CODE_REMOTE=true`) arbeiten ganz ohne Worktree
   direkt im eigenen geklonten Repository, das die Kapselung bereits
   garantiert; der `worktree_guard.py` ist dort ein No-op.

2. **Selbst-testender Regelapparat.** Jede Regel wird einem von zwei
   Teststilen zugeordnet:
   - **Deterministische, git-zustandsbasierte Checks** — für Regeln, deren
     Einhaltung vollständig aus dem fertigen Branch-/Commit-Zustand ablesbar
     ist (Branch-Pattern, kein `main`-Push, kein Co-Author-Trailer,
     Trivial-Kriterium). Reine Python-Funktionen, `unittest`, kein LLM, kein
     Netz, keine Flakiness.
   - **Lokale, `claude -p`-getriebene Behavioral Evals** — für Regeln, die nur
     als Instruktion an das Gesprächsverhalten des LLM existieren
     (Engineering-Prinzipien-Trigger, Delegationspolitik, Nachfragepflicht),
     und zum Bewerten, ob Skills/Subagenten sich wie dokumentiert verhalten.
     Format `evals.json` (Szenario-`prompt` + `expectations` in Prosa),
     Bewertung durch einen LLM-Richter-Subagenten (verallgemeinert aus
     skill-creators `grader.md`). Läuft vollständig gegen die eigene
     authentifizierte `claude`-CLI-Sitzung; kein separater API-Key, keine
     Cloud-CI.

Beide Stile hängen an **einem** versionierten, selbst-aktivierenden
`pre-push`-Hook (`core.hooksPath`) und sind zusätzlich manuell aufrufbar. Ein
Fehlschlag eines Checks **blockt den Push hart**; `git push --no-verify` bleibt
der bewusste, standardmäßige Override.

## Workflow-Phasen

Die bestehenden Phasen bleiben: **Idee → Spec/PRD → Issues → Implementierung →
Verifikation**. Geändert wird die Issue-/Branch-Logik dazwischen.

| Phase | Skill/Subagent | Diagramm |
| :--- | :--- | :--- |
| Idee → PRD | `grill-me-for-spec` | Abb. 1 |
| PRD → Haupt-Issue + Kind-Issues | `issue-tracker` | Abb. 1 |
| Mehrere Haupt-Issues lokal parallel | (mehrere Sessions, Worktrees) | Abb. 2 |
| Kind-Issues umsetzen, 1 PR | `issue-implementer` × N | Abb. 3 |
| Triviale Ausnahme | (kein Issue nötig) | Abb. 4 |
| Push-Verifikation | `pre-push` + `workflow-evals` | Abb. 5 |
| Regel-Selbstprüfung | `workflow-evals` | Abb. 6 |

## User Stories / Requirements

### Issue-/Branch-Logik

1. Als Maintainer entsteht jeder Branch aus genau einem Top-Level-Issue und
   heißt `issue/<slug>`. `issue/<slug>` ist das **einzige** gültige
   Branch-Pattern; die Präfixe `feature|fix|refactor|chore` entfallen. Die
   Kategorie wandert in ein `type`-Feld der `issue.md`
   (`feature|fix|refactor|chore`).
2. Als Maintainer ist Issue-Tracking für **jede** nicht-triviale Codeänderung
   verpflichtend — das PRD wird immer in ein Haupt-Issue plus Kind-Issues
   zerlegt, ohne vorherige Nachfrage.
3. Als Maintainer gilt genau **1 Haupt-Issue = 1 Branch = 1 Pull Request**
   (und, nur in lokalen Sessions, = 1 Worktree). Der PR wird erst eröffnet,
   wenn alle Kind-Issues geschlossen sind — `resolved`, oder `superseded` für
   ein nie umgesetztes Kind-Issue.
4. Als Maintainer kann ich **mehrere Haupt-Issues gleichzeitig lokal**
   bearbeiten: jedes in einem eigenen Worktree unter `.worktrees/`, gefahren
   von einer eigenen, unabhängigen Claude-Code-Session. Es gibt keine
   gemeinsame orchestrierende Instanz zwischen ihnen; nur das geteilte `.git`
   verbindet sie. `.worktrees/` ist in `.gitignore` eingetragen. In
   **Cloud-Sessions** (`CLAUDE_CODE_REMOTE=true`) entfällt der Worktree ganz:
   die Session läuft im eigenen geklonten Repository, das die Kapselung
   garantiert, und arbeitet direkt auf dem `issue/<slug>`-Branch.
5. Als Maintainer werden Kind-Issues eines Haupt-Issues **innerhalb** seiner
   Session **sequenziell, eines nach dem anderen** in Abhängigkeitsreihenfolge
   (aus `tracker.py`, numerische Präfixordnung) direkt auf dem
   Haupt-Issue-Branch implementiert — nie parallel. Der issue-implementer läuft
   **ohne eigenen Worktree**: er editiert den Arbeitsbaum der Session in-place
   und übergibt jede Scheibe **uncommitted** zurück. Es gibt keinen
   Kind-Worktree und keinen Kind-Branch zum Mergen.
6. Als Maintainer darf eine **triviale** Änderung ohne Haupt-Issue passieren.
   Trivial ist deterministisch definiert: **genau 1 geänderte Datei UND
   (≤ 1 geänderte Zeile ODER Dateiendung ∈ {`.md`, `.json`, `.yaml`, `.yml`,
   `.txt`})**. Sie läuft auf dem aktuell ausgecheckten Branch mit — niemals
   direkt auf `main`.

### Deterministische Durchsetzung

7. Als Maintainer wird jeder Branch-Name gegen `^issue/[a-z0-9-]+$` geprüft.
8. Als Maintainer wird jeder Push, dessen Ziel-Ref `main` ist, abgelehnt —
   `main` wird nur über einen GitHub-PR-Merge aktualisiert, nie durch lokalen
   Push. (Push-Ziel-basiert, nicht Commit-Form-basiert.)
9. Als Maintainer wird jeder Commit im gepushten Bereich abgelehnt, dessen
   Nachricht einen `Co-Authored-By:`-Trailer enthält (kein Allow-List,
   Single-Maintainer-Repo).
10. Als Maintainer sind die Regeln 7–9 durch einen `pre-push`-Hook durchgesetzt,
    der ohne manuelles Setup pro Clone aktiv ist: der bestehende
    `cloud-session-bootstrap`-`SessionStart`-Hook setzt zusätzlich
    `core.hooksPath`, falls nicht bereits konfiguriert. Der Hook gilt
    automatisch für alle Worktrees, da diese sich ein `.git` teilen.
11. Als Maintainer kann ich die Regeln 7–9 jederzeit auch manuell ausführen,
    nicht nur beim Push, über dasselbe Skript, das der Hook aufruft.
12. Als Maintainer laufen die deterministischen Checks (7–9) in **jedem**
    eigenen Repo (via `cloud-session-bootstrap`), die langsamen Behavioral
    Evals nur beim Push **dieses** Config-Repos.

### Behavioral Evals

13. Als Maintainer bleiben der `engineering-principles`-Trigger, die
    Subagent-Delegationspolitik und die Nachfragepflicht in AGENTS.md in voller
    Stärke, jeweils durch einen Behavioral Eval abgesichert, der ein
    Test-Szenario spawnt und das Transkript gegen explizite Erwartungen
    bewertet.
14. Als Maintainer laufen Behavioral Evals vollständig lokal über meinen eigenen
    `claude`-CLI-Login — kein API-Key, kein CI-Secret, kein Cloud-Runner.
15. Als Maintainer läuft jeder Testfall isoliert in einem **Sandbox-Worktree /
    Tempdir**, damit der Test-Subagent keine echten Seiteneffekte auslöst.
16. Als Maintainer blockt ein fehlgeschlagener Behavioral Eval den Push genau
    wie ein fehlgeschlagener deterministischer Check, mit `--no-verify` als
    Override.
17. Als Maintainer läuft bei jedem Push die **volle** Suite, unabhängig davon,
    welche Dateien geändert wurden — keine Diff-basierte Auswahl.
18. Als Maintainer teilen sich Skills, Subagenten und AGENTS.md-Regeln **ein**
    Eval-Format und **einen** Runner. Ablage kolokiert:
    - Skills: `skills/<name>/evals/evals.json`
    - Subagenten: `agents/<name>/agent.md` + `agents/<name>/evals/evals.json`
      (Umstellung von flachen `agents/<name>.md`; offiziell unterstützt, da
      Claude Code `.claude/agents/` rekursiv scannt und Identität allein aus
      dem `name`-Frontmatter zieht)
    - AGENTS.md-Regeln: `evals/agents-md/<rule-slug>/evals.json`
19. Als Maintainer entwirft Claude bei jeder Regel-/Skill-Änderung passende
    Testfälle (Szenario + erwartetes Verhalten) und legt sie mir zur Freigabe
    vor; erst nach Freigabe werden sie committet und Teil der Suite.
20. Als Maintainer schließt `skill-creator/scripts/package_skill.py` `evals/`
    nicht mehr vom Packaging aus — in diesem Repo müssen Evals committet und
    dauerhaft vorhanden sein.

### Umfang dieser PRD

21. Scope ist die Infrastruktur plus **ein** ausgearbeitetes Beispiel je
    Kategorie: die deterministischen Checker (Regeln 7–9 + Trivial-Kriterium)
    vollständig gebaut und getestet; je ein echter Behavioral Eval für einen
    Skill (`issue-tracker`), einen Subagenten (`test-runner`) und eine
    AGENTS.md-Regel (Nachfragepflicht). Volle Eval-Abdeckung der übrigen Skills,
    Subagenten und AGENTS.md-Regeln ist Folgearbeit, als eigene Issues getrackt.

## Technical Decisions

### Skill-/Subagent-Set (6 Skills)

Fünf bestehende Skill-Namen bleiben, Inhalt wird neu geschrieben; ein neuer Skill
kommt hinzu:

1. `grill-me-for-spec` — erzeugt PRD, legt danach ohne Nachfrage das Haupt-Issue
   an (inkl. `type`-Feld).
2. `issue-tracker` — neue 1:1-Logik (Haupt-Issue ↔ Branch ↔ PR; Worktree nur
   lokal), Kind-Issues **sequenziell** in Abhängigkeitsreihenfolge direkt auf
   dem Haupt-Issue-Branch (kein Kind-Worktree, kein Merge), Trivial-Ausnahme.
3. `engineering-principles` — inhaltlich unverändert, bekommt Behavioral Eval.
4. `testing` — unverändert (Produktcode-Verifikation, getrennt vom
   Regel-Test-Framework).
5. `cloud-session-bootstrap` — erweitert: setzt `core.hooksPath` und installiert
   die deterministischen `pre-push`-Checks in jedem eigenen Repo.
6. `workflow-evals` (**neu**) — das Regel-Test-Framework: deterministische
   Checker + headless Eval-Runner + der verallgemeinerte Richter-Prompt
   (umgezogen aus `skill-creator/agents/grader.md`, da er nun Skills UND
   Subagenten UND AGENTS.md-Regeln bewertet).

### Betroffene Module / Orte

- `AGENTS.md` — „Git & Version Control" und „Worktree Isolation" neu gefasst
  (einziges Branch-Pattern `issue/<slug>`, verpflichtendes Issue-Tracking,
  Trivial-Ausnahme, `.worktrees/`-Layout, Worktree-Struktur einstufig und
  **nur lokal** — Cloud-Sessions ohne Worktree, Guard dort No-op);
  „Cloud Session Bootstrap Trigger" erweitert (setzt `core.hooksPath`);
  Engineering-Prinzipien-Trigger, Delegation und Nachfragepflicht bleiben und
  werden je an einen Behavioral Eval gekoppelt.
- Neu `scripts/git_workflow_rules.py` (reine Funktionen) + `unittest`-Tests.
- Neu versioniertes `.githooks/pre-push`, aktiviert via
  `git config core.hooksPath .githooks`.
- `skills/cloud-session-bootstrap/` — Hook-Skript erweitert (`core.hooksPath`
  + deterministische Checks), plus fixture-basierter Test.
- `agents/*.md` → `agents/<name>/agent.md` + `agents/<name>/evals/evals.json`.
- Neu `evals/agents-md/<rule-slug>/evals.json` für die drei AGENTS.md-Regeln.
- `skills/skill-creator/scripts/package_skill.py` — `evals` aus
  `ROOT_EXCLUDE_DIRS` entfernen.
- Neu `scripts/run_behavioral_eval.py` — der Eval-Runner.
- `.gitignore` — `.worktrees/` ergänzen.

### Architekturentscheidungen

- **Arbeitseinheit = Haupt-Issue = Git-Branch = Worktree = PR.** Streng 1:1.
- **`main`-Schutz ist push-ziel-basiert**, nicht commit-form-basiert: jeder Push
  auf `main` wird abgelehnt, ohne „direkt" von „Merge" zu unterscheiden.
- **Co-Author-Erkennung ohne Allow-List**: jeder `Co-Authored-By:`-Trailer
  failed.
- **Warum ein neuer Runner-Skript nötig ist:** skill-creators bestehender
  Grading-Flow (Executor-Subagent → `grader.md` → `grading.json`) wird heute von
  einer **laufenden** Claude-Code-Session über das Agent/Task-Tool orchestriert.
  Dieses Tool existiert außerhalb einer Session nicht und kann daher aus einem
  reinen `pre-push`-Shell-Hook nicht aufgerufen werden.
  `scripts/run_behavioral_eval.py` verkettet stattdessen zwei synchrone
  `claude -p`-Subprozessaufrufe (dasselbe Muster wie skill-creators
  `run_eval.py`, das headless funktioniert): erst läuft der Szenario-`prompt`
  und erzeugt ein Transkript, dann läuft ein zweiter `claude -p` mit
  `grader.md`s Grading-Instruktionen plus Transkript und `expectations` und
  schreibt `grading.json`. Exit ≠ 0, wenn `summary.pass_rate < 1.0`.
- **Evals blockend, `--no-verify` als sanktionierter Override** — konsistent mit
  den deterministischen Regeln, kein Sonder-Mechanismus.
- **Volle Suite pro Push** — kein Diff-basiertes Auswählen.
- **Eval-Geltungsbereich ohne Config-Repo-Erkennung:** Der Hook ruft immer
  beide Stufen auf. Der Eval-Schritt läuft über alle vorhandenen
  `evals.json`-Dateien; nur dieses Repo enthält welche, in anderen Repos ist der
  Schritt ein No-Op. So braucht es keine „ist das das Config-Repo?"-Logik.
- **Die Runner-Plumbing ist unabhängig von echten LLM-Calls testbar:**
  Subprozess-Orchestrierung und JSON-Parsing in `run_behavioral_eval.py` werden
  mit gemockten `claude -p`-Calls unit-getestet.

### API-Verträge / Datenmodelle

- `evals.json` — gleiche Form wie skill-creators Schema
  (`references/schemas.md`):
  `{"evals": [{"id", "prompt", "expected_output", "expectations": [...]}]}`.
  Der identifizierende Top-Level-Schlüssel variiert je Ort: `skill_name`,
  `agent_name` bzw. `rule_id`.
- `grading.json` — unverändert aus skill-creators Schema;
  `run_behavioral_eval.py` schreibt dieselbe Struktur.

## Testing Decisions

- **Zu testende Module:**
  - `scripts/git_workflow_rules.py` (Branch-Name, `main`-Push, Co-Author,
    Trivial-Kriterium).
  - `.githooks/pre-push` (Integration: dogfood gegen den eigenen Branch-/
    Commit-Zustand dieses Repos).
  - `cloud-session-bootstrap`s Hook-Skript (fixture-basiert).
  - `scripts/run_behavioral_eval.py` (Unit mit gemocktem `claude -p`; plus je
    ein echter End-to-End-Lauf pro Beispiel).

- **Test-Interfaces (Seams):**
  1. **Git-Workflow-Regeln** — reine Funktionen `is_valid_branch_name(name)`,
     `is_protected_ref(ref)`, `commit_has_agent_coauthor(message)`,
     `is_trivial_change(files, added_lines)` in
     `scripts/git_workflow_rules.py`, direkt per `unittest` testbar.
  2. **Bootstrap-Hook** — Dateisystem-Effekt gegen ein Fixture-Repo geprüft.
  3. **Behavioral Evals** — das `evals.json`-Format und die
     `run_behavioral_eval.py`-CLI; interne Logik unit-getestet mit gemockten
     Calls, drei Beispiele zusätzlich end-to-end.

## Offene Punkte (in der Zerlegung zu klären)

- **Kind-Worktrees entfallen.** Kind-Issues werden sequenziell direkt auf dem
  Haupt-Issue-Branch implementiert; es gibt keinen Kind-Worktree mehr, also auch
  keine Verschachtelungsfrage. Für Haupt-Issue-Worktrees gilt weiterhin: flach
  gegen das gemeinsame `.git` registrieren, keine `.worktrees/.worktrees/`.
- **Pass-Schwelle** der Evals: Vorschlag `pass_rate == 1.0` erforderlich; ob
  einzelne Evals eine abweichende Schwelle deklarieren dürfen, offen.
- **Manuelle Aufrufschnittstelle** (Regel 11): CLI-Name/Flags des Skripts.

## Out of Scope

- GitHub Actions oder jede Cloud-CI — abgelehnt; alles lokal via `pre-push`
  oder manuell.
- Volle Eval-Abdeckung über die drei Beispiele hinaus — Folge-Issues.
- Automatischer Test für Worktree-Isolation — bleibt untestete Guidance in
  AGENTS.md (keine Artefakt-Spur).
- Die ungruppierten Regeln am Anfang von `AGENTS.md` (Entwicklungskosten,
  E2E-Bug-Repro, kritisches Hinterfragen, „nur untersuchen", offizielle Docs,
  kurze Antworten) — nicht Teil dieser Runde, bleiben unverändert und
  untestbar.
- Diff-basierte / geänderte-Datei-Eval-Auswahl — jede Eval läuft bei jedem
  Push.
- Retry-/Mehrheits-Voting zur Stabilisierung nicht-deterministischer Bewertung
  — ein einzelner Grading-Pass, `--no-verify` als Antwort auf gelegentliche
  False Negatives.
```
