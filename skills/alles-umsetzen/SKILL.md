---
name: alles-umsetzen
description: Geht selbständig alle Stories/Features nacheinander durch und implementiert und testet die offenen Features mithilfe von Sub-Agenten.
disable-model-invocation: true
---

# Alles umsetzen (Automated Feature Implementation Loop)

Verwende diesen Skill, um alle offenen Features des Projekts vollautomatisch nacheinander zu analysieren, zu implementieren und zu testen. Dieser Skill delegiert die Arbeit für jedes Feature/Issue an spezialisierte Sub-Agenten, die die vorhandenen Skills (`anforderungsanalyse`, `umsetzung` und `testen`) ausführen.

## Ablauf

### 1. Features/Stories ermitteln
- Lies die globale Projekt-PRD (typischerweise `PRD.md` im Projekt-Root-Verzeichnis) aus.
- Analysiere die Sektion `## Features`, um alle verlinkten Features und deren zugehörige Pfade (z. B. `.scratch/<feature-slug>/PRD.md`) zu extrahieren.
- Falls die globale `PRD.md` nicht existiert oder keine Einträge enthält, suche nach Unterverzeichnissen im Ordner `.scratch/`, um die Feature-Slugs zu bestimmen.

### 2. Offene Features bestimmen
Iteriere durch alle gefundenen Feature-Slugs und bestimme deren Status:
- Scanne das Verzeichnis `.scratch/<feature-slug>/issues/` nach Markdown-Dateien der Form `NN-<slug>.md`.
- Ein Feature gilt als **offen** (bzw. unvollständig), wenn mindestens ein Issue existiert, dessen Status nicht `Status: resolved` ist (z. B. `Status: ready-for-agent` oder `Status: claimed`).
- Ein Feature gilt als **abgeschlossen**, wenn alle definierten Issues den Status `Status: resolved` aufweisen. Features ohne Issues werden übersprungen, da davon ausgegangen wird, dass die Anforderungsanalyse bereits Issues erstellt hat.

### 3. Features nacheinander umsetzen
Gehe alle offenen Features der Reihe nach durch. Führe für jedes offene Feature die folgenden Schritte vollautomatisch aus:

#### Schritt A: Feature aktivieren & Branch vorbereiten
- Schreibe den aktuellen Feature-Slug in die Datei `.scratch/active-feature.txt` im Projekt-Root.
- Stelle sicher, dass der Git-Branch für das Feature existiert und aktiv ist. Der Branch-Name folgt dem Muster `feature/<feature-slug>`. Falls der Branch nicht existiert, lege ihn an und checke ihn aus.

#### Schritt B: Sub-Agenten für Umsetzung & Testen spawnen
- Spawne einen Sub-Agenten für das aktive Feature. Der Sub-Agent erhält den Auftrag:
  1. **Umsetzung**: Führe den Skill `/umsetzung` aus. Gehe alle offenen Issues des Features nacheinander durch und setze sie mittels TDD (Red-Green-Refactor) um, bis alle Issues den Status `Status: resolved` haben.
  2. **Testen**: Führe anschließend direkt den Skill `/testen` aus (komplette Testsuite ausführen, Typprüfung/Linter, Zwei-Achsen-Code-Review Standards vs. Spezifikation).
- Wenn der Sub-Agent Fehler meldet oder nicht weiterkommt, unterbrich den Durchlauf und informiere den Benutzer.
- Stelle sicher dass der Hauptbranch ausgecheckt und sauber ist

### 4. Fertigstellung (Handoff)
- Sobald alle offenen Features abgearbeitet wurden, präsentiere dem Benutzer eine Zusammenfassung der durchgeführten Arbeiten:
  - Liste aller erfolgreich umgesetzten Features.
  - Status der Git-Repository (aktueller Branch, sauberes Working Directory).
  - Bestätigung, dass die gesamte Testsuite grün ist.
