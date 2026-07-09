# ADR-Format

ADRs liegen in `docs/adr/` und verwenden eine fortlaufende Nummerierung: `0001-slug.md`, `0002-slug.md` usw.

Erstelle das Verzeichnis `docs/adr/` lazily (träge) — erst dann, wenn die erste Architekturentscheidung (ADR) tatsächlich benötigt wird.

## Vorlage

```md
# {Kurzer Titel der Entscheidung}

{1-3 Sätze: Was ist der Kontext, was haben wir entschieden und warum.}
```

Das ist alles. Eine ADR kann aus einem einzigen Absatz bestehen. Der Wert liegt darin zu dokumentieren, *dass* eine Entscheidung getroffen wurde und *warum* — nicht im Ausfüllen von Abschnitten.

## Optionale Abschnitte

Füge diese nur hinzu, wenn sie einen echten Mehrwert bieten. Die meisten ADRs benötigen sie nicht.

- **Status** Frontmatter (`proposed | accepted | deprecated | superseded by ADR-NNNN`) — nützlich, wenn Entscheidungen später überarbeitet werden
- **Betrachtete Optionen (Considered Options)** — nur, wenn die verworfenen Alternativen erinnerungswürdig sind
- **Auswirkungen (Consequences)** — nur, wenn nicht offensichtliche Folgeeffekte hervorgehoben werden müssen

## Nummerierung

Durchsuche `docs/adr/` nach der höchsten existierenden Nummer und erhöhe sie um eins.

## Wann eine ADR angeboten werden sollte

Alle drei der folgenden Kriterien müssen erfüllt sein:

1. **Schwer umkehrbar** — die Kosten, die Entscheidung später zu ändern, sind signifikant.
2. **Überraschend ohne Kontext** — ein zukünftiger Leser wird sich den Code ansehen und sich fragen: "Warum um alles in der Welt haben sie das so gemacht?"
3. **Ergebnis eines echten Abwägens (Trade-off)** — es gab echte Alternativen und man hat sich aus bestimmten Gründen für eine entschieden.

Wenn eine Entscheidung leicht rückgängig zu machen ist, überspringe sie — du wirst sie im Zweifel einfach rückgängig machen. Wenn sie nicht überraschend ist, wird sich niemand fragen warum. Wenn es keine echte Alternative gab, gibt es nichts zu dokumentieren außer "wir haben das Offensichtliche getan".

### Was sich qualifiziert

- **Architektonische Struktur.** Z. B. Monorepo vs. Multi-Repo, Trennung von Schreib- und Lesemodell (CQRS) oder Schichtenarchitektur.
- **Integrationsmuster zwischen Kontexten.** Z. B. asynchrone Event-getriebene Kommunikation vs. synchrone API-Aufrufe.
- **Technologieentscheidungen mit Lock-in-Effekt.** Auswahl von Systemkomponenten wie Datenbanktechnologien, Message-Brokern, Authentifizierungs-Providern oder Deployment-Plattformen.
- **Grenz- und Scope-Entscheidungen.** Festlegung von Datenhoheiten (z. B. welcher Kontext bestimmte Stammdaten besitzt und wie andere Kontexte darauf verweisen).
- **Bewusste Abweichungen vom Standardweg.** Wenn eine unübliche Entscheidung getroffen wird (z. B. Verzicht auf ein bestimmtes Framework oder eine Bibliothek aus spezifischen Gründen), um zu verhindern, dass zukünftige Entwickler dies als "Fehler" ansehen und rückgängig machen.
- **Nicht direkt im Code sichtbare Einschränkungen.** Vorgaben durch Compliance, regulatorische Anforderungen oder vertragliche Zusicherungen (z. B. maximale Latenzzeiten).
- **Verworfene Alternativen bei nicht offensichtlichen Entscheidungen.** Wenn eine valide Alternative intensiv diskutiert, aber schlussendlich abgelehnt wurde, um zu verhindern, dass die Diskussion in Zukunft erneut geführt werden muss.
