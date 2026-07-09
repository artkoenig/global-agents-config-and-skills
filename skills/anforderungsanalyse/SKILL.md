---
name: anforderungsanalyse
description: Führt die Anforderungsanalyse für das aktive Feature durch, definiert Test-Schnittstellen (Seams), vervollständigt das Feature-PRD und bricht es in lokale Issues auf.
user-invocable: false
---

# Anforderungsanalyse

Verwende diesen Skill, um das aktive Feature im Detail zu analysieren und in implementierbare, testbare Aufgaben (Issues) zu zerlegen.

## Ablauf

### 1. Aktives Feature bestimmen
- Versuche, das aktive Feature aus dem aktuellen Gesprächskontext zu ermitteln.
- Falls dies unklar ist, lies die Datei `.scratch/active-feature.txt` im Projekt-Root aus, um den Feature-Slug zu erhalten.
- Falls die Datei nicht existiert oder leer ist, frage den Benutzer nach dem Slug des Features, das analysiert werden soll, und lege die Datei `.scratch/active-feature.txt` mit diesem Slug an.

### 2. Kontext- & Codebase-Analyse
- Untersuche den aktuellen Stand des Codes bezüglich der Anforderungen. Verwende die im Projekt vorhandenen Domänendokumente (z. B. `CONTEXT.md`) und respektiere existierende Architekturentscheidungen (ADRs).
- Identifiziere betroffene Klassen, Interfaces, APIs, Datenmodelle oder UI-Komponenten.

### 3. Grilling-Session & Aktives Domain-Modeling (das "grill-with-docs"-Prinzip)
- Befrage den Benutzer unnachgiebig zu allen Aspekten des Plans, der Anforderungen und des Designs, um ein gemeinsames Verständnis zu erzielen.
- Gehe jeden Zweig des Design-Baums durch und löse Abhängigkeiten zwischen Entscheidungen nacheinander auf.
- Stelle Fragen **einzeln nacheinander** und liefere für jede Frage direkt deine **empfohlene Antwort** mit. Warte auf das Feedback des Benutzers zu jeder Frage, bevor du fortfährst. (Mehrere Fragen auf einmal zu stellen ist verwirrend).
- Falls Fakten direkt durch Erkundung der Codebase ermittelt werden können, recherchiere diese selbstständig, statt den Benutzer danach zu fragen. Die *Entscheidungen* liegen jedoch beim Benutzer – präsentiere sie ihm einzeln.
- Betreibe **aktives Domain-Modeling**:
  - Nutze und schärfe das Domänenmodell (Glossar in `CONTEXT.md` / `CONTEXT-MAP.md` und ADRs in `docs/adr/`) während des Designs.
  - Wenn der Benutzer Begriffe verwendet, die im Widerspruch zum bestehenden Glossar in `CONTEXT.md` stehen, weise sofort darauf hin ("Das Glossar definiert 'X' als Y, aber du scheinst Z zu meinen – welches ist korrekt?").
  - Hinterfrage vage oder überladene Begriffe und schlage präzise Bezeichnungen vor (z. B. "Du sagst 'Konto' – meinst du den Kunden oder den Benutzer?").
  - Diskutiere konkrete Szenarien und prüfe sie gegen den Code, um Widersprüche aufzudecken.
  - Sobald ein Begriff geklärt ist, aktualisiere die Datei `CONTEXT.md` direkt inline (unter Verwendung des Formats in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md)). Die Datei `CONTEXT.md` sollte frei von Implementierungsdetails sein (nur ein reines Glossar).
  - Propose/erzeuge ADRs unter `docs/adr/` (unter Verwendung des Formats in [ADR-FORMAT.md](./ADR-FORMAT.md)) sparsam und nur, wenn alle drei Kriterien erfüllt sind:
    1. Die Entscheidung ist schwer rückgängig zu machen.
    2. Die Entscheidung ist überraschend für zukünftige Leser ohne Kontext.
    3. Die Entscheidung resultiert aus einem echten Trade-off (echten Alternativen).
- Fahre erst fort, wenn der Benutzer bestätigt hat, dass ein gemeinsames Verständnis des Modells und des Designs erreicht wurde.

### 4. Test-Schnittstellen (Seams) definieren
- Plane, an welchen öffentlichen Schnittstellen (Seams) das Feature getestet werden soll. Bevorzuge bereits existierende Schnittstellen und halte die Anzahl neuer Schnittstellen so gering wie möglich.
- Präsentiere die vorgeschlagenen Schnittstellen dem Benutzer im Chat zur Freigabe. Schreibe keine Tests, bevor die Test-Schnittstellen abgestimmt sind.

### 5. Feature-PRD vervollständigen
- Synthetisiere die Erkenntnisse aus der Diskussion und der Codebase-Analyse und vervollständige die Datei `.scratch/<feature-slug>/PRD.md` (z. B. Problemstellung, Lösung, User Stories, technische Entscheidungen wie Datenstrukturen oder API-Verträge, sowie die Test-Schnittstellen).
- Führe hierfür **kein** erneutes Interview mit dem Benutzer durch – nutze stattdessen das bereits bekannte Wissen, welches in Schritt 3 erarbeitet wurde.

### 6. In vertikale Issues zerlegen (Tracer Bullets)
- Brich das Feature in unabhängig voneinander bearbeitbare Aufgaben (Issues) auf.
- Nutze das Prinzip der **vertikalen Slices (Tracer Bullets)**: Jede Aufgabe schneidet durch alle betroffenen Schichten (z. B. Schema, API, UI, Tests) und liefert ein minimales, eigenständig demonstrierbares und verifizierbares Verhalten. Prefactoring-Aufgaben sollten als erste Issues definiert werden.
- Präsentiere die Liste der Issues dem Benutzer im Chat. Zeige für jedes Issue:
  - **Titel**: Ein kurzer, prägnanter Name
  - **Blockiert durch**: Andere Issues, die zuvor abgeschlossen sein müssen
  - **User Stories**: Welche User Story(s) hiermit abgedeckt wird (werden)
- Frage den Benutzer:
  - Passt die Granularität?
  - Stimmen die Abhängigkeiten?
  - Sollen Aufgaben zusammengelegt oder weiter aufgeteilt werden?
- Sobald der Benutzer die Zerlegung freigibt, erstelle für jedes Issue eine Datei unter `.scratch/<feature-slug>/issues/NN-<slug>.md` (nummeriert ab `01`), unter Verwendung der folgenden Struktur:
  ```markdown
  Status: ready-for-agent
  Type: task
  Blocked by: [Liste von NN, oder "None"]

  ## Parent
  Verweis auf die Feature-PRD: `.scratch/<feature-slug>/PRD.md`

  ## Was zu bauen ist
  [Kurze, präzise Beschreibung des End-to-End-Verhaltens. Vermeide konkrete Dateipfade, da diese schnell veralten.]

  ## Akzeptanzkriterien
  - [ ] Kriterium 1
  - [ ] Kriterium 2

  ## Comments
  *Hier können Feedback und Notizen während der Umsetzung angehängt werden.*
  ```

### 7. Fertigstellung (Handoff)
- Erzeuge keinen Implementierungsplan (implementation_plan.md) und schreibe keinen Code. Starte keinesfalls mit der Implementierung.
- Informiere den Benutzer darüber, dass die Anforderungsanalyse abgeschlossen ist.
- Weise den Nutzer darauf hin, dass er nun den Befehl `/alles-umsetzen` ausführen kann, um mit der Umsetzung des Features/CRs zu beginnen.

