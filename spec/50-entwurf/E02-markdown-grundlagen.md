# E02 Markdown-Grundlagen der Generatoren

> Status: Entwurf

## Ziel

Was alle drei Generatoren (DOCX, PPTX, PDF) teilen, einmal in Python: das Lesen von Markdown samt
Front Matter und Folien-Syntax, das Zeichenmodell für Diagramme und Charts, die Schnittstellen für
Code-Block-Renderer und Bildkonverter und die Authoring Guides.

## Motivation

In DocLibs liegt das im Paket `DocumentGeneration` (~2 600 Zeilen). Ohne Brand-System schrumpft es
deutlich: `Brand`, `BrandPack`, `BrandRegistry`, `ResolvedBrand` entfallen (siehe
[Portierungsanalyse](../10-analysen/2026-11-06%20portierung-doclibs-python.md)); ihre Rolle
übernimmt das feste PTA-Designmodell aus [E01](E01-pta-design.md).

## Scope

| Story | Inhalt | Status |
| ----- | ------ | ------ |
| [E02-S01](../60-prüfung/E02-S01-markdown-parser-und-front-matter.md) | `MarkdownDocument`, Parser (markdown-it-py), Front Matter, Fehlerklasse | in Prüfung |
| [E02-S02](../60-prüfung/E02-S02-folien-syntax.md) | Folien-Syntax: Heading-Attribute, `:::`-Container, Alerts, `==mark==`, `[Wörter]{.success}`, Status-Labels | in Prüfung |
| [E02-S03](E02-S03-zeichenmodell-und-svg.md) | Zeichenmodell `Drawing` und SVG-Ausgabe mit Tooltips | Entwurf |
| [E02-S04](../60-prüfung/E02-S04-code-block-renderer-und-bildkonverter.md) | Code-Block-Renderer und Bildkonverter (Schnittstellen, Fehlerweitergabe) | in Prüfung |
| [E02-S05](E02-S05-authoring-guides.md) | Authoring Guides (Markdown-Beschreibung für Schreiber, aus den Optionen erzeugt) | Entwurf |

## Bereichsweite Entscheidungen

- Front Matter bleibt die flache YAML-Teilmenge von DocLibs (kein echtes YAML, keine
  Verschachtelung); unbekannte Schlüssel und Werte werfen mit Liste der gültigen.
- Front Matter wählt **keinen Brand** mehr, sondern die Variante der PTA-Vorlage
  (`vorlage:` — Namen siehe E01-S01) und nennt nie einen Dateipfad.
- **Front-Matter-Schlüssel und -Werte sind deutsch** (Entscheidung 2026-11-06): `vorlage`,
  `titel`, `untertitel`, `autor`, `ort`, `datum`, `firma`, `sprache`, `inhaltsverzeichnis`,
  `fusszeile`, `status.<kategorie>`; Wahrheitswerte `ja`/`nein`. Die Markdown-Syntax selbst
  (Container `cards`, Klassen `.dark`, `.success`, Alerts `[!NOTE]`) bleibt wie in DocLibs, weil
  sie Syntax und keine Einstellung ist.
- Ein Fehler in einem Dokument ist immer eine `DocumentConversionError` mit `reason` und Format.

## Akzeptanz

Die Generatoren E03–E05 nutzen ausschließlich diese Bausteine zum Lesen von Markdown.

## Offene Fragen

1. Sollen die Front-Matter-Schlüssel englisch bleiben (`title`, `author`, `template`) wie in
   DocLibs, oder deutsch (`titel`, `autor`, `vorlage`)? Vorschlag: englisch, wie Code.

> (2026-11-06) Deutsch.

## Notizen

