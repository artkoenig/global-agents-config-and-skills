Status: ready-for-agent
Type: feature
Blocked by: None

## Description

Führt den Zustand `superseded` vollständig ein — im Automaten und in jeder
Dokumentoberfläche, die den Automaten beschreibt.

Bewusst **nicht** weiter geteilt: Automat und Dokumentation getrennt zu mergen
hinterließe den Tracker zwischenzeitlich in einem Zustand, in dem sein Code und
seine Beschreibung einander widersprechen. Für ein Werkzeug, dessen Verhalten
Agenten aus eben dieser Beschreibung ableiten, ist das kein zulässiger
Zwischenstand.

### Verhalten

Der Zustand `superseded` schließt ein Issue, das nie implementiert wird — weil
es durch ein anderes ersetzt wurde, weil eine Anforderung entfiel oder weil es
sich als Duplikat erwies. Welcher Fall vorlag, geht aus der Pflicht-Begründung
hervor, nicht aus dem Zustandsnamen.

- Erreichbar aus `needs-triage`, `needs-info`, `ready-for-agent` und `claimed`.
- Nicht erreichbar aus `resolved`.
- Rückweg nach `needs-triage`.
- Der Übergang verlangt eine Begründung. Ohne sie wird er abgelehnt. Die
  Begründung wird als Kommentar am Issue festgehalten, damit sie dort steht,
  wo auch jede andere Notiz zum Issue steht.
- `superseded` zählt als geschlossen: ein `superseded` Blocker gibt seine
  Abhängigen frei, ein `superseded` Kind-Issue hindert sein Haupt-Issue nicht
  am Auflösen.

### Betroffene Stellen

Im Code drei Annahmen der Form „geschlossen bedeutet `resolved`": die
Zustandsliste samt Übergangstabelle, die Blocker-Prüfung und die Prüfung
offener Kind-Issues beim Auflösen. Statt die Zeichenkette `resolved` an drei
Stellen zu einer Aufzählung zu erweitern, ist ein benanntes Prädikat für
„geschlossen" einzuführen — sonst wiederholt sich beim nächsten terminalen
Zustand dieselbe Suche.

In der Dokumentation: die Zustandsreferenz, das Issue-Format, die
Skill-Beschreibung, die drei Arbeitsabläufe (Zerlegen, Implementieren,
Auflösen), die Repository-Übersicht, der `issue-implementer`-Agent, die
Spezifikations-Skill sowie die Evals des Trackers.

## Acceptance Criteria
- [ ] `superseded` ist aus jedem offenen Zustand erreichbar, aus `resolved`
      nicht; der Rückweg führt nach `needs-triage`
- [ ] Ein Übergang nach `superseded` ohne Begründung wird mit verständlicher
      Meldung abgelehnt
- [ ] Die Begründung erscheint als Kommentar am Issue
- [ ] Ein `superseded` Blocker gibt seine Abhängigen frei — belegt durch einen
      Testfall
- [ ] Ein Haupt-Issue lässt sich auflösen, wenn seine offenen Kind-Issues
      `superseded` sind — belegt durch einen Testfall
- [ ] „Geschlossen" ist im Code an genau einer Stelle definiert, nicht dreimal
      als Vergleich gegen eine Zeichenkette
- [ ] Alle zehn Dokumentoberflächen beschreiben den Zustand einschließlich der
      Begründungspflicht; keine nennt mehr fünf Zustände
- [ ] Die Evals des Trackers decken den neuen Zustand ab
- [ ] Der eingebaute `selftest` und die deterministischen Prüfungen des
      Repositorys laufen grün
- [ ] Das Verhalten der bestehenden fünf Zustände ist unverändert

## Comments
