Status: resolved
Type: feature
Blocked by: None

## Description

**Befund:** `init` schreibt die Tracker-Dokumentation nach
`docs/agents/issue-tracker.md` eines Zielprojekts nur dann, wenn dort noch
keine Datei liegt. Eine vorhandene wird stillschweigend übersprungen.

Für eine erstmalige Einrichtung ist das richtig — es schützt lokale
Anpassungen. Für ein bereits eingerichtetes Repository bedeutet es jedoch:
**jede künftige Änderung am Zustandsmodell erreicht es nie.** Der in
Kind-Issue 01 eingeführte Zustand `superseded` wäre in jedem heute bereits
initialisierten Projekt dauerhaft unsichtbar — der dort arbeitende Agent liest
weiterhin von fünf Zuständen und würde den sechsten nicht verwenden.

Das ist Doku-Drift mit Verhaltenswirkung, nicht bloß eine veraltete Datei: die
Beschreibung *ist* die Anleitung, aus der ein Agent sein Vorgehen ableitet.

**Vorgeschlagene Behebung:** `init` erneuert die Datei, wenn sie von der
aktuellen Vorlage abweicht, statt sie zu überspringen. Da die Datei erklärtes
Erzeugnis des Trackers ist und keine Stelle zum Anpassen vorsieht, ist ein
Überschreiben vertretbar — es muss aber erkennbar sein, damit eine dennoch
vorgenommene lokale Änderung nicht unbemerkt verschwindet. `init` meldet
deshalb, dass es erneuert hat.

Der Vorgang muss idempotent bleiben: ein zweiter Lauf ohne Vorlagenänderung
darf nichts schreiben und nichts melden.

## Acceptance Criteria
- [ ] `init` erneuert eine von der Vorlage abweichende
      `docs/agents/issue-tracker.md` statt sie zu überspringen
- [ ] Die Erneuerung wird gemeldet, sodass sie im Protokoll sichtbar ist
- [ ] Ein erneuter Lauf ohne Vorlagenänderung schreibt nichts und meldet nichts
- [ ] Die übrigen von `init` angelegten Dateien behalten ihr bisheriges
      Verhalten
- [ ] Testfälle decken beide Fälle ab: abweichende Datei wird erneuert,
      übereinstimmende bleibt unberührt
- [ ] Der eingebaute `selftest` und die deterministischen Prüfungen des
      Repositorys laufen grün

## Comments

Unabhängig von Kind-Issue 01 sinnvoll — der Befund besteht auch ohne den neuen
Zustand. Er wird gemeinsam bearbeitet, weil ohne ihn die Erweiterung aus 01
bestehende Repositories nicht erreicht.
- init erneuert docs/agents/issue-tracker.md, sobald sie von der Vorlage abweicht, und meldet die Erneuerung; eine uebereinstimmende Datei wird nicht angefasst. Die uebrigen von init angelegten Dateien behalten ihr Verhalten (_write_if_absent).
