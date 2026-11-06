# E01 PTA-Design als einziges Design

> Status: Entwurf

## Ziel

Die Generatoren kennen genau ein Design: das der PTA, wie es die Vorlagen in `source-templates/`
festlegen. An die Stelle von `Brand.Neutral`, Brand-Packs, eingebautem Folienmaster und
Liberation-Standardschriften aus DocLibs treten die PTA-Vorlagen selbst und ein kleines
Designmodell für das, was die Generatoren selbst zeichnen.

## Motivation

Siehe [Designanalyse](../10-analysen/2026-11-06%20pta-designstandards.md) und
[Portierungsanalyse](../10-analysen/2026-11-06%20portierung-doclibs-python.md). Ein Dokument aus
diesem Paket soll von einem von Hand erstellten PTA-Dokument nicht zu unterscheiden sein.

## Scope

| Story | Inhalt | Status |
| ----- | ------ | ------ |
| [E01-S01](E01-S01-pta-designmodell.md) | PTA-Designmodell: Farben, Schriften, Maße, Varianten | Entwurf |
| [E01-S02](E01-S02-vorlagen-einbetten.md) | Vorlagen bereinigen und als Paketdaten einbetten | Entwurf |
| E01-S03 | Schriften für PDF und SVG (Selawik/Segoe UI, Georgia-Ersatz) | noch nicht ausgearbeitet |
| E01-S04 | Logos als SVG/PNG für PDF und SVG-Ausgabe | noch nicht ausgearbeitet |

## Bereichsweite Entscheidungen

- **Keine Standardvorlagen, kein Brand-System.** Es gibt keinen neutralen Brand, keine
  Brand-Packs, kein `template: <brand>` im Front Matter und keine fremden Vorlagen
  (`CustomTemplateOptions` entfällt).
- **Die Vorlage ist die Quelle der Wahrheit.** Werte, die in einer Vorlage stehen (Formatvorlagen,
  Layouts, Theme), werden nicht im Code wiederholt, sondern gelesen; das Designmodell enthält nur,
  was keine Vorlage trägt (z. B. Folientabellen, Fazit-Box, PDF-Seitenaufbau), und Tests prüfen
  es gegen die Vorlagen.
- Word und PowerPoint haben **eigene Regeln** (Textfarbe, Tabellenkopf, Aufzählungszeichen,
  Fußzeile); jeder Generator folgt der seines Formats, PDF folgt Word.
- `source-templates/` bleibt unverändert; neue Fassungen der Vorlagen von der PTA ersetzen die
  Dateien dort, die Paketdaten werden daraus neu erzeugt.

## Akzeptanz

Im Code gibt es keine Farb- oder Schriftangabe, die nicht in der Designanalyse steht, und keinen
Pfad, über den ein anderes Design eingeschleust werden kann.

## Offene Fragen

1. Gibt es bei der PTA ein Corporate-Design-Handbuch (Logo-Schutzzonen, Mindestgrößen,
   Farbwerte in CMYK), das über die Vorlagen hinausgeht?

>

2. Sollen BPS und DATIS (Gruppenvorlage) später eigene Varianten mit eigenem Logo bekommen, oder
   bleibt es bei der einen BPS-PTA-DATIS-Word-Vorlage?

>

## Notizen

