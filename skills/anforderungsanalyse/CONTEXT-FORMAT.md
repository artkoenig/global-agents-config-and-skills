# CONTEXT.md-Format

## Struktur

```md
# {Name des Kontextes}

{Ein bis zwei Sätze Beschreibung, worum es in diesem Kontext geht und warum er existiert.}

## Sprache / Glossar

**{Hauptbegriff} ({Englische Übersetzung - optional})**:
{Ein bis zwei Sätze präzise Beschreibung des Begriffs.}
_Vermeiden_: {Ungenaue Alternative 1}, {Ungenaue Alternative 2}

**{Weiterer Begriff}**:
{Ein bis zwei Sätze präzise Beschreibung dieses Begriffs.}
_Vermeiden_: {Auszuschließendes Synonym}
```

## Regeln

- **Sei meinungsstark (opinionated).** Wenn mehrere Wörter für dasselbe Konzept existieren, wähle das beste aus und liste die anderen unter `_Vermeiden_` auf.
- **Halte Definitionen kurz.** Maximal ein oder zwei Sätze. Definiere, was es IST, nicht, was es tut.
- **Nimm nur Begriffe auf, die spezifisch für den Kontext dieses Projekts sind.** Allgemeine Programmierkonzepte (Timeouts, Fehlertypen, Hilfsmuster) gehören hier nicht hinein, selbst wenn das Projekt sie ausgiebig nutzt. Bevor du einen Begriff hinzufügst, frage dich: Ist dies ein Konzept, das einzigartig für diesen Kontext ist, oder ein allgemeines Programmierkonzept? Nur Ersteres gehört hierhin.
- **Gruppiere Begriffe unter Zwischenüberschriften**, wenn sich natürliche Cluster bilden. Wenn alle Begriffe zu einem einzigen zusammenhängenden Bereich gehören, ist eine flache Liste in Ordnung.

## Repositories mit einem vs. mehreren Kontexten

**Einzelner Kontext (die meisten Repos):** Eine `CONTEXT.md` im Projekt-Root.

**Mehrere Kontexte:** Eine `CONTEXT-MAP.md` im Projekt-Root listet die Kontexte auf, wo sie liegen und wie sie zueinander in Beziehung stehen:

```md
# Context Map (Kontext-Landkarte)

## Kontexte

- [{Kontext A}](./src/{kontext-a}/CONTEXT.md) — {Kurze Beschreibung von Kontext A}
- [{Kontext B}](./src/{kontext-b}/CONTEXT.md) — {Kurze Beschreibung von Kontext B}

## Beziehungen

- **{Kontext A} → {Kontext B}**: {Beziehung / Event-Fluss von Kontext A zu Kontext B}
- **{Kontext A} ↔ {Kontext B}**: {Gemeinsam genutzte Typen / Verträge}
```

Der Skill leitet ab, welche Struktur zutrifft:

- Wenn eine `CONTEXT-MAP.md` existiert, lies sie aus, um die Kontexte zu finden.
- Wenn nur eine `CONTEXT.md` im Root existiert, handelt es sich um einen einzelnen Kontext.
- Wenn keine von beiden existiert, erstelle lazily (träge) eine `CONTEXT.md` im Root, sobald der erste Begriff geklärt ist.

Wenn mehrere Kontexte existieren, leite ab, auf welchen Kontext sich das aktuelle Thema bezieht. Wenn es unklar ist, frage nach.
