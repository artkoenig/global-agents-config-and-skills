---
name: testen
description: Führt abschließende Tests und Typprüfungen für das aktive Feature aus und startet einen lokalen Zwei-Achsen-Code-Review (Standards vs. Spezifikation).
user-invocable: false
---

# Testen und Verifizieren

Verwende diesen Skill, um die Umsetzung eines Features final abzusichern, die gesamte lokale Testsuite durchlaufen zu lassen und einen Code-Review durchzuführen.

## Ablauf

### 1. Aktives Feature bestimmen
- Versuche, das aktive Feature aus dem aktuellen Gesprächskontext zu ermitteln.
- Falls unklar, lies die Datei `.scratch/active-feature.txt` im Projekt-Root aus.
- Falls die Datei nicht existiert oder leer ist, frage den Benutzer nach dem Namen des Features (`<feature-slug>`).

### 2. Lokale Testsuite & Typprüfung ausführen
- Ermittle den Testbefehl:
  - Lies `.scratch/test-command.txt` aus.
  - Falls nicht vorhanden, analysiere die Dateien im Projekt-Root (z. B. Vorhandensein von `package.json` -> `npm test` oder `vitest`; `Cargo.toml` -> `cargo test`; `requirements.txt` -> `pytest`).
  - Wenn nicht eindeutig ermittelbar, frage den Benutzer einmalig nach dem Testbefehl und speichere ihn in `.scratch/test-command.txt`.
- Führe den Testbefehl aus und stelle sicher, dass **alle** Tests des Projekts erfolgreich durchlaufen (grün sind).
- Führe etwaige Typprüfungen (z. B. `tsc` bei TypeScript) oder Linter aus, um syntaktische und typbezogene Fehler auszuschließen.

### 3. Zwei-Achsen-Code-Review
Führe ein Review der Änderungen durch, die im Rahmen des Features vorgenommen wurden. 

- **Ermittlung des Diff-Basispunkts**:
  - Prüfe, ob der Branch `feature/<feature-slug>` existiert und du diesen als deinen aktuellen Branch ausgecheckt hast. Wechsle, falls nötig, dorthin. Wenn das nicht möglich ist, brich den Skill ab und gib eine Fehlermeldung aus.
  - Ermittle die Merge-Base der aktuellen Änderungen gegen die Haupt-Branch (standardmäßig `main` oder `master` via `git merge-base main HEAD`). Falls `main`/`master` nicht existieren oder unklar sind, frage den Benutzer nach dem Vergleichs-Branch oder -Commit.
  - Führe `git diff <merge-base>...HEAD` aus, um die Änderungen zu erfassen.

Spawne zwei parallele Sub-Agenten, um den Diff unabhängig voneinander auf zwei Achsen zu prüfen:

#### Achse A: Standards (Coding-Guidelines & Code-Smells)
Der Standards-Sub-Agent prüft den Diff gegen die im Repository dokumentierten Richtlinien (z. B. `CODING_STANDARDS.md` oder `CONTRIBUTING.md`) sowie gegen die folgenden Heuristiken für Code-Smells:
- **Mysterious Name**: Unklare Funktions-, Variablen- oder Typnamen.
- **Duplicated Code**: Identische oder sehr ähnliche Logikstrukturen in mehreren Zeilen/Dateien.
- **Feature Envy**: Eine Methode greift mehr auf Daten eines anderen Objekts als auf eigene zu.
- **Data Clumps**: Gruppen von Datenfeldern, die immer zusammen auftauchen (wollen evtl. ein eigener Typ sein).
- **Primitive Obsession**: Nutzung von Primitiven anstelle eines eigenen Typs für Domänenkonzepte.
- **Divergent Change**: Eine Datei/Klasse wird aus vielen verschiedenen Gründen modifiziert.
- **Shotgun Surgery**: Eine logische Änderung erzwingt verstreute Anpassungen in vielen Dateien.
- **Speculative Generality**: Abstrakte Klassen, Parameter oder Hooks, die für die aktuelle Spezifikation nicht benötigt werden.

*Regeln für Standards*: Lokale Repo-Dokumente überschreiben die Smell-Heuristiken. Linter-Regeln, die bereits automatisch validiert wurden, werden übersprungen.

#### Achse B: Spezifikation (Spec)
Der Spec-Sub-Agent gleicht den Diff mit der Feature-PRD unter `.scratch/<feature-slug>/PRD.md` ab:
- **Fehlende Anforderungen**: Welche im PRD beschriebenen Anforderungen wurden nicht oder nur unvollständig umgesetzt?
- **Scope Creep**: Welche Änderungen wurden implementiert, nach denen das PRD überhaupt nicht verlangt hat?
- **Fehlerhafte Logik**: Wo sieht die Umsetzung fehlerhaft oder abweichend von den Spezifikationen aus?

#### Zusammenführung
- Präsentiere die Berichte beider Sub-Agenten getrennt voneinander unter den Überschriften `## Standards` und `## Spezifikation`. 
- Fasse das Ergebnis in einer Zeile zusammen (Anzahl der Funde pro Achse sowie die kritischste Anmerkung pro Achse).

### 4. Abschluss
- Frage den Nutzer, ob er die empfohlenen Änderungen und Refactorings vornehmen möchte.
- Wenn ja, führe die Änderungen und Refactorings durch und committe sie. Führe `/testing` nochmal mit dem neuen Stand aus.
- Wenn nein, oder wenn keine Änderungen empfohlen werden UND alle issues von diesem Feature den Status `resolved` haben, lösche die `.scratch/active-feature.txt` und merge den Feature-Branch in den Haupt-Branch.