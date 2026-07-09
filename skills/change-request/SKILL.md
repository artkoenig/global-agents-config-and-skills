---
name: change-request
description: Erstellt einen neuen Change Request (Feature oder Bug) im Projekt, fügt ihn zur globalen PRD.md hinzu und bereitet den lokalen Workspace unter .scratch/ vor.
disable-model-invocation: true
---

# Change Request hinzufügen

Verwende diesen Skill, um dem Projekt einen neuen Change Request (Feature oder Bug) hinzuzufügen.

## Ablauf

### 1. Change-Request-Informationen abfragen
- Frage den Benutzer interaktiv nach dem **Namen des Change Requests**, dem **Typ (Feature oder Bug)** und einer kurzen **Beschreibung/Zweck**.
- **Klären bei Bugs**: Falls es sich beim Change Request um einen Bug handelt, frage den Benutzer interaktiv nach dem **aktuellen Verhalten** (Ist-Zustand) und dem **erwarteten Verhalten** (Soll-Zustand), um den Fehler genau zu klären.
- Generiere aus dem Namen automatisch einen URL- und ordnerkonformen **Change-Request-Slug** (z. B. `authentifizierung` oder `daten-export`, Kleinbuchstaben, Bindestriche statt Leerzeichen, Umlaute umwandeln).
- **Existenz- und Statusprüfung**:
  - Prüfe, ob der Change Request bereits existiert. Ein Change Request gilt als existierend, wenn entweder ein Eintrag in der globalen `PRD.md` unter `## Features` oder `## Change Requests` vorhanden ist oder das Verzeichnis `.scratch/<change-request-slug>/` existiert.
  - Falls der Change Request existiert, bestimme seinen aktuellen Status:
    - **Umgesetzt**: Alle im Verzeichnis `.scratch/<change-request-slug>/issues/` befindlichen Issues weisen den Status `Status: resolved` auf.
    - **Geplant**: Das Verzeichnis `.scratch/<change-request-slug>/` existiert, aber es gibt noch offene/nicht aufgelöste Issues oder es wurden noch keine Issues angelegt.
  - Wenn der Change Request bereits geplant oder umgesetzt wurde, informiere den Benutzer über den gefundenen Status und frage ihn interaktiv, wie verfahren werden soll (z. B. einen anderen Namen/Slug wählen, den bestehenden Workspace überschreiben oder den Vorgang abbrechen).

### 2. Globale PRD.md aktualisieren
- Suche die projektweite `PRD.md` im Projekt-Root.
- Trage den neuen Change Request in der Haupt-`PRD.md` unter der Sektion `## Features` bzw. `## Change Requests` als Listenpunkt ein:
  ```markdown
  - [Change Request Name](.scratch/<change-request-slug>/PRD.md): [Kurze Beschreibung]
  ```

### 3. Change-Request-Workspace anlegen
- Erstelle das Verzeichnis `.scratch/<change-request-slug>/` sowie das Unterverzeichnis `.scratch/<change-request-slug>/issues/`.
- Schreibe den aktuellen Slug in die Statusdatei `.scratch/active-feature.txt` (überschreibe eventuell vorhandene alte Slugs):
  ```
  <change-request-slug>
  ```
- Erstelle eine PRD-Vorlage unter `.scratch/<change-request-slug>/PRD.md` mit folgenden Sektionen (passe die Beschreibung an, falls es ein Bug ist):
  ```markdown
  # PRD: [Change Request Name]

  ## Problemstellung / Bug-Beschreibung
  [Hier beschreiben, welches Problem der Benutzer hat oder wie sich der Bug äußert. Falls Bug: Aktuelles Verhalten vs. Erwartetes Verhalten dokumentieren]

  ## Lösung
  [Die vorgeschlagene Lösung aus Benutzersicht]

  ## User Stories / Anforderungen
  1. Als ein <Akteur>, möchte ich <Feature>, um <Nutzen> zu haben.

  ## Technische Entscheidungen
  - Betroffene Module:
  - Technische Klärungen/Architekturentscheidungen:
  - API-Verträge / Datenmodelle:

  ## Test-Entscheidungen
  - Zu testende Module:
  - Test-Schnittstellen (Seams):

  ## Out of Scope
  - [Dinge, die nicht Teil dieses Change Requests sind]
  ```

### 4. Fertigstellung (Handoff)
- Erzeuge keinen Implementierungsplan (implementation_plan.md) und schreibe keinen Code. Starte keinesfalls mit der Implementierung.
- Bestätige dem Benutzer, dass der Workspace für den Change Request `<change-request-slug>` erfolgreich angelegt wurde.
- mache automatisch mit Skill `/anforderungsanalyse` weiter
