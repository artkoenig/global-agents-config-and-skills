---
name: neues-projekt
description: Initialisiert ein neues lokales Projekt, fragt nach der Vision/Beschreibung, klärt den Scope und legt die projektweite PRD.md sowie lokale Issue-Tracking-Strukturen an.
disable-model-invocation: true
---

# Neues Projekt initialisieren

Verwende diesen Skill, um ein neues Projekt auf deinem lokalen Rechner aufzusetzen.

## Ablauf

### 1. Projekt-Metadaten erheben
- Frage den Benutzer interaktiv nach dem **Namen** des Projekts.
- Frage nach einer kurzen **Beschreibung** der Vision und des Hauptziels des Projekts.
- Führe ein kurzes Interview zum **Scope** (Was soll das Projekt können? Was ist out of scope / nicht im Leistungsumfang?).

### 2. Git initialisieren
- Prüfe im aktuellen Arbeitsverzeichnis, ob bereits ein Git-Repository existiert (z. B. via `git status` oder Vorhandensein von `.git`).
- Falls nicht, initialisiere es durch Ausführen von `git init`.

### 3. Verzeichnisstruktur & Konfigurationen anlegen
- Erstelle das Verzeichnis `.scratch/` im Projekt-Root-Verzeichnis.
- Konfiguriere das lokale Issue-Tracking automatisch und geräuschlos, indem du folgende Konfigurationsdateien erstellst:
  
  - **`docs/agents/issue-tracker.md`**:
    ```markdown
    # Issue tracker: Local Markdown
    Issues und PRDs für dieses Repo liegen als Markdown-Dateien unter `.scratch/`.
    ```
    
  - **`docs/agents/triage-labels.md`**:
    ```markdown
    # Triage label vocabulary
    - `needs-triage` — Zur Evaluierung durch den Maintainer
    - `needs-info` — Wartet auf Rückmeldung
    - `ready-for-agent` — Vollständig spezifiziert, bereit zur automatischen Umsetzung (AFK)
    - `claimed` — In Bearbeitung durch den Agenten
    - `resolved` — Erfolgreich umgesetzt und gelöst
    ```
    
  - **`docs/agents/domain.md`**:
    ```markdown
    # Domain docs layout
    Single-context Layout. Die Domänenbeschreibung liegt in `CONTEXT.md` am Projekt-Root.
    ```

- Suche im Projekt-Root nach `CLAUDE.md` oder `AGENTS.md`. 
  - Wenn eine davon existiert, füge die Sektion `## Agent skills` (falls nicht vorhanden) darin ein oder aktualisiere sie.
  - Wenn keine von beiden existiert, frage den Benutzer kurz, welche Datei erstellt werden soll, und erstelle sie.
  
  Füge folgenden Block ein:
  ```markdown
  ## Agent skills

  ### Issue tracker
  Lokales Markdown-Tracking unter `.scratch/`. Siehe `docs/agents/issue-tracker.md`.

  ### Triage labels
  Lokale Status-Labels. Siehe `docs/agents/triage-labels.md`.

  ### Domain docs
  Single-context Layout. Siehe `docs/agents/domain.md`.
  ```

### 4. Projekt-PRD erstellen
- Erstelle eine initiale `PRD.md` direkt im Hauptverzeichnis des Projekts (Projekt-Root) mit folgendem Aufbau:
  ```markdown
  # PRD: [Projektname]

  ## Vision & Beschreibung
  [Hier die erfasste Vision/Beschreibung einfügen]

  ## Scope
  [Zusammenfassung der Scope-Entscheidungen]

  ## Change Requests
  *Change Requests werden durch den Befehl `/change-request` automatisch hier eingetragen.*
  ```

### 5. Fertigstellung (Handoff)
- Informiere den Benutzer darüber, dass das Projekt erfolgreich für den lokalen Workflow initialisiert wurde.
- Weise ihn darauf hin, dass er nun den Befehl `/change-request` aufrufen kann, um den ersten Change Request anzulegen.
