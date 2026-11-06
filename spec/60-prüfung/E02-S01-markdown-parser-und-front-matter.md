# E02-S01 Markdown-Parser und Front Matter

> Status: in Prüfung
> Epic: [E02 Markdown-Grundlagen der Generatoren](../50-entwurf/E02-markdown-grundlagen.md)
> Milestone: [M01 PTA-Dokumente aus Markdown](../50-entwurf/M01-pta-dokumente-aus-markdown.md)

## Zusammenfassung

Das gemeinsame Eingangsformat der Generatoren: ein `MarkdownDocument` (Text + Ressourcen +
Metadaten), ein Parser auf markdown-it-py mit den Erweiterungen, die DocLibs über Markdig nutzt,
und das Front Matter.

## Kontext

DocLibs: `MarkdownDocument`/`DocumentResource` (`DocumentConversions`), `FrontMatter.cs`
(209 Zeilen), Markdig-Pipeline in `MarkdownParser.cs` (PDF) und `DeckParser.cs` (PPTX). Bilder
kommen als Ressourcen im Dokument, nie von der Platte.

## Vorgeschlagener Ansatz

1. `pta_documents.markdown`: `MarkdownDocument(text, resources, metadata)`,
   `DocumentResource(name, content: bytes, content_type)`, `find_resource(reference)`.
2. `pta_documents.errors.DocumentConversionError(reason, format)`.
3. Parser-Fabrik auf markdown-it-py (`commonmark` + Tabellen + Durchstreichen) mit
   mdit-py-plugins: Fußnoten, Aufgabenlisten, Definitionslisten; Zeilennummern der Blöcke
   werden mitgeführt (für Fehlermeldungen `line`).
4. Front Matter nach DocLibs-Regeln portieren (Beginn in Zeile 1, `---`/`...`, Kommentare,
   Anführungszeichen, Groß/Klein egal, Duplikate/Unbekanntes werfen) — inklusive der Tests.
5. Tests: Front-Matter-Fälle aus DocLibs übernehmen; Parser-Rauchtests.

## Akzeptanzkriterien

- [x] Alle Front-Matter-Testfälle von DocLibs laufen sinngemäß grün.
- [x] Ein Markdown mit Tabellen, Listen, Bildern, Code, Links und Fußnoten wird in einen
      Token-Strom mit Zeilennummern zerlegt.
- [x] Unbekannte Front-Matter-Schlüssel werfen `DocumentConversionError` mit Liste der gültigen.

## Offene Fragen

1. Sprache der Front-Matter-Schlüssel?

> (2026-11-06) Deutsch, siehe E02.

## Notizen


## Implementierungsnotizen

- `pta_documents.markdown`: `MarkdownDocument(text, resources, metadata)`,
  `DocumentResource(path, content_type, content)`, `find_resource()` (normalisiert `./`, `\` und
  %-Escapes wie DocLibs), `MetadataKeys` mit den DocLibs-Schlüsseln (`title`, `author`,
  `pageCount`, `slideCount`, `skippedImages`), `content_type_of()`. Das Feld heißt `path` wie in
  DocLibs (der Plan nannte es `name`).
- `DocumentConversionError` liegt seit T01-S01 in `pta_documents.errors`.
- **Front Matter** (`markdown/front_matter.py`): Leseregeln 1:1 aus DocLibs. Statt des
  generischen `Apply(...)` mit Brand-Wechsel gibt es einfache Bausteine, die die Generatoren
  zusammensetzen: `get`, `check_keys(valid, allow_status)`, `boolean` (`ja`/`nein`), `one_of`,
  `date` (`JJJJ-MM-TT` oder `TT.MM.JJJJ`) und `status_labels` (`status.<kategorie>: A; B`).
  Die Kategorien bleiben englisch (`success`, `warning`, `danger`, `info`, `neutral`), weil sie
  die Namen der Markdown-Klassen sind (`[Wort]{.success}`).
- Schlüsselkonstanten in `Keys` (deutsch): `vorlage`, `titel`, `untertitel`, `autor`, `ort`,
  `datum`, `firma`, `sprache`, `inhaltsverzeichnis`, `fusszeile`, `titelfolie`, `status.`.
  Schlüssel bestehen wie in DocLibs nur aus ASCII-Buchstaben, Ziffern und Punkten — daher
  `fusszeile`, nicht `fußzeile`.
- **Parser** (`markdown/parser.py`): markdown-it-py `commonmark` + `table` + `strikethrough`,
  Plugins Fußnoten, Aufgabenlisten, Definitionslisten; HTML ist abgeschaltet (wird als Text
  gelesen). `line_of(token, offset)` rechnet die Zeile im Original inklusive Front Matter.
- Die DocLibs-Testfälle für das Lesen sind übernommen; die `Apply`-Fälle sind durch Tests der
  neuen Bausteine ersetzt.
