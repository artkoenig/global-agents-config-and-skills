Status: resolved
Type: feature
Blocked by: None

## Description

### Anlass

Der Zustandsautomat kennt heute keinen Weg, ein Issue zu schließen, das nie
implementiert wird. Die einzige terminale Station ist `resolved`, und dorthin
führt ausschließlich der Weg über `ready-for-agent → claimed`.

Der Anlass war konkret: In einem Projekt gingen drei bestehende Issues
inhaltlich in zwei neu angelegten auf. Sie zu schließen war nicht möglich —
`needs-triage → resolved` wird zu Recht abgelehnt. Der einzige verfügbare Weg
hätte sie fälschlich als *implementiert* verbucht. Sie blieben deshalb offen
stehen, mit einem Verweis-Kommentar als Behelf.

Dasselbe Bedürfnis entsteht, wenn ein Issue durch einen gemergten Pull Request
hinfällig wird, wenn eine Anforderung entfällt, oder wenn zwei Issues sich als
Duplikate erweisen.

### Entwurfsentscheidungen

- **Ein Zustand, nicht zwei.** `superseded` deckt sowohl „durch ein anderes
  Issue ersetzt" als auch „schlicht hinfällig" ab. Welcher Fall vorlag, sagt
  die Begründung, nicht der Zustandsname.
- **Begründung ist Pflicht.** Der Übergang nach `superseded` verlangt einen
  Begründungstext, der als Kommentar am Issue festgehalten wird. Ohne ihn
  verschwände ein Issue stillschweigend — genau das, was der Automat sonst
  überall verhindert.
- **Erreichbar aus jedem offenen Zustand:** `needs-triage`, `needs-info`,
  `ready-for-agent` und `claimed`. Auch laufende Arbeit kann hinfällig werden.
- **Nicht erreichbar aus `resolved`.** Erledigte Arbeit wird nicht nachträglich
  ungeschehen gemacht; das verfälschte die Historie.
- **Rückweg `superseded → needs-triage`**, symmetrisch zum Wiedereröffnen von
  `resolved`. Ein Issue kann sich als doch noch nötig erweisen.
- **`superseded` zählt als geschlossen.** Ein `superseded` Blocker gibt seine
  Abhängigen frei, und ein `superseded` Kind-Issue hindert sein Haupt-Issue
  nicht am Auflösen. Beides ist zwingend: andernfalls blockierte ein niemals
  zu implementierendes Issue seine Nachbarn auf ewig.

### Umfang

Die Annahme „geschlossen bedeutet `resolved`" steckt an drei Stellen im Code
(Zustandsliste und Übergangstabelle, die Blocker-Prüfung, die Prüfung offener
Kind-Issues beim Auflösen) sowie in zehn Dokumentoberflächen: der
Zustandsreferenz, dem Issue-Format, der Skill-Beschreibung, den drei
Arbeitsabläufen, der Repository-Übersicht, dem `issue-implementer`-Agenten, der
Spezifikations-Skill und den Evals des Trackers.

Hinzu kommt ein bei der Analyse entdeckter Nebenbefund, der eigenes Gewicht
hat: `init` schreibt die Tracker-Dokumentation in ein Zielprojekt nur, wenn
dort noch keine liegt. Jedes bereits initialisierte Repository behielte
deshalb dauerhaft die alte Zustandsbeschreibung — der neue Zustand käme dort
nie an. Das ist als Kind-Issue 02 erfasst.

## Acceptance Criteria
- [ ] Alle Kind-Issues sind resolved
- [ ] Die deterministischen Prüfungen des Repositorys laufen grün
      (`python3 -m unittest discover -s scripts -p 'test_*.py'`)
- [ ] Der eingebaute `selftest` des Trackers läuft grün
- [ ] Keine Verhaltensänderung an den bestehenden fünf Zuständen

## Comments
- Vier-Achsen-Verifikation: Standards 9 Befunde (alle vorbestehend, keiner blockierend), Spezifikation ohne Befund, Tests gruen (42 Unittests + selftest), Dokumentation 2 Funde. Beide Docs-Funde behoben (AGENTS.md, PRD.md: PR-Gate nannte resolved statt geschlossen). Die vorbestehenden Standards-Befunde werden als eigenes Haupt-Issue erfasst.
