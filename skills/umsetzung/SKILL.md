---
name: umsetzung
description: Setzt die offenen Issues des aktiven Features nacheinander mittels TDD (Test-Driven Development) an den vereinbarten Test-Seams um.
user-invocable: false
---

# Umsetzung (Implementation)

Verwende diesen Skill, um die Issues des aktiven Features schrittweise abzuarbeiten.

## Ablauf

### 1. Aktives Feature bestimmen
- Versuche, das aktive Feature aus dem aktuellen Gesprächskontext zu ermitteln.
- Falls unklar, lies die Datei `.scratch/active-feature.txt` im Projekt-Root aus.
- Falls die Datei nicht existiert oder leer ist, frage den Benutzer nach dem Slug des Features.

### 2. Nächstes unblockiertes Issue finden
- Scanne das Verzeichnis `.scratch/<feature-slug>/issues/` nach Dateien:
    - Finde das erste offene Issue (nummeriert ab `01`), das:
        - Den Status `Status: ready-for-agent` aufweist.
    - Nicht blockiert ist (d. h. alle in `Blocked by:` aufgeführten Issues haben den Status `Status: resolved`, oder es gibt keine Blocker).
    - Ändere den Status des gewählten Issues in der entsprechenden Markdown-Datei auf `Status: claimed`.
    - Präsentiere dem Benutzer das ausgewählte Issue und dessen Akzeptanzkriterien im Chat.
    - Stoppe das Scannen und ignoriere alle anderen Issues.
- Bei folgenden Implementierung setzt du nur das um was, in dem gefunden Issue beschrieben wurde. Kein vorgriffe auf die noch nicht implementierten Issues in diesem Ticket    

### 3. TDD-Zyklus (Test-Driven Development) durchführen
Falls noch nicht geschehen, erzeuge einen Branch für das Issue mit dem namen `feature/<feature-slug>` bzw. checke diesen Branch aus, falls er schon existiert. Setze das Issue schrittweise in kleinen Einheiten mittels TDD (Red-Green-Refactor) um. Führe für jeden TDD-Schritt Folgendes durch:

1. **Rot-Phase (Red)**:
   - Schreibe einen fehlschlagenden Test an der vereinbarten Test-Schnittstelle (Seam), der das gewünschte Verhalten überprüft.
   - Der Test muss eine sinnvolle Behauptung (Assertion) aufstellen. Erwartete Werte müssen aus unabhängigen Quellen (Literal, worked example, Spec) stammen, nicht aus der Implementierung selbst (keine tautologischen Tests).
   - Führe den Test aus und verifiziere, dass er rot (fehlgeschlagen) ist.
   
2. **Grün-Phase (Green)**:
   - Schreibe Code (halte dich strikt an die Richtlinien in `CODE_GUIDLINES.md`, um den fehlschlagenden Test grün (erfolgreich) zu machen. Vermeide spekulative Erweiterungen oder das Vorgreifen auf zukünftige Aufgaben.
   - Führe den Test erneut aus und verifiziere, dass er grün ist.
   
3. **Refactoring-Phase**:
   - Nach erfolgreichem Testlauf kann der Code aufgeräumt werden. (Hinweis: Größeres architektonisches Refactoring oder Code-Reviews finden außerhalb dieser Schleife in der Testphase statt).

*Ermittlung des Testbefehls*:
- Lies `.scratch/test-command.txt` aus.
- Falls nicht vorhanden, analysiere das Projekt-Root (z. B. `package.json` -> `npm test` oder `vitest`; `Cargo.toml` -> `cargo test`; `requirements.txt` -> `pytest`).
- Wenn nicht eindeutig ermittelbar, frage den Benutzer einmalig nach dem Befehl, führe ihn aus und speichere ihn in `.scratch/test-command.txt`.

### 4. Issue auflösen
- Sobald alle Akzeptanzkriterien des Issues erfüllt sind und alle Tests erfolgreich durchlaufen, aktualisiere die Issue-Datei:
  - Setze den Status auf `Status: resolved`.
  - Hänge eine kurze Zusammenfassung der Lösung unter der Überschrift `## Answer` (oder `## Lösung`) an.
- Mache einen Git-Commit für das gelöste Issue auf dem lokalen Branch.

### 5. Fertigstellung (Handoff)
- Gib dem Nutzer eine kurze Zusammenfassung der gemachten Änderungen und den Status der Git-Repository.
