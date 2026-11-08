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
| [E01-S01](../60-prüfung/E01-S01-pta-designmodell.md) | PTA-Designmodell: Farben, Schriften, Maße, Varianten | in Prüfung |
| [E01-S02](../60-prüfung/E01-S02-vorlagen-einbetten.md) | Vorlagen bereinigen und als Paketdaten einbetten | in Prüfung |
| [E01-S03](../55-in-arbeit/docs-2/E01-S03-schriften-fuer-pdf-und-svg.md) | Schriften für PDF und SVG: Selawik (OFL) gebündelt, Segoe UI aus dem System, wenn vorhanden; Georgia-Ersatz | in Bearbeitung (docs-2) |
| [E01-S04](E01-S04-logos-als-svg-und-png.md) | Logos als SVG/PNG für PDF und SVG-Ausgabe, aus den EMF der Vorlagen gewandelt | Entwurf |

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

> (2026-11-06) Nicht bekannt — die Standards sind nur, was in `source-templates/` steht.

2. Sollen BPS und DATIS (Gruppenvorlage) später eigene Varianten mit eigenem Logo bekommen, oder
   bleibt es bei der einen BPS-PTA-DATIS-Word-Vorlage?

> (2026-11-06) BPS-PTA-DATIS wird keine wählbare Variante; die Vorlage bleibt nur in
> `source-templates/` als Referenz.

## Notizen

