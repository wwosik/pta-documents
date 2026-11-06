# E02-S01 Markdown-Parser und Front Matter

> Status: Entwurf
> Epic: [E02 Markdown-Grundlagen der Generatoren](E02-markdown-grundlagen.md)
> Milestone: [M01 PTA-Dokumente aus Markdown](M01-pta-dokumente-aus-markdown.md)

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

- [ ] Alle Front-Matter-Testfälle von DocLibs laufen sinngemäß grün.
- [ ] Ein Markdown mit Tabellen, Listen, Bildern, Code, Links und Fußnoten wird in einen
      Token-Strom mit Zeilennummern zerlegt.
- [ ] Unbekannte Front-Matter-Schlüssel werfen `DocumentConversionError` mit Liste der gültigen.

## Offene Fragen

1. Sprache der Front-Matter-Schlüssel?

> (2026-11-06) Deutsch, siehe E02.

## Notizen

