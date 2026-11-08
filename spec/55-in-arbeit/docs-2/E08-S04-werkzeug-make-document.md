# E08-S04 Werkzeug `make_document` für KI-Hosts

> Status: in Bearbeitung (docs-2) — reaktiviert 2026-11-08 auf Wunsch des Menschen
> Epic: [E08 Rückmeldung an den Schreiber und KI-Anbindung](../../50-entwurf/E08-rueckmeldung-und-ki-anbindung.md)

## Zusammenfassung

Ein Modul `pta_documents.tool`, das einem KI-Host (Chat-Assistent, Agent-Framework) die
Generatoren als **ein** Werkzeug anbietet: `describe(options)` liefert Name, Beschreibung,
Parameter als JSON Schema und den Authoring Guide für die angebotenen Formate; `run(arguments,
output, options, resources)` führt einen Aufruf aus; `reply(run, link)` und `reply(error)`
antworten dem Modell in einer festen JSON-Form mit den Hinweisen aus E08-S01. Unabhängig von jedem
KI-SDK.

## Kontext

- vt-tools-libs: `DocumentGeneration.Tools` (`DocumentTool.cs` 294 Zeilen, `CombinedGuide.cs`,
  `DocumentToolOptions.cs`, `DocumentToolDescription.cs`; `docs/VtToolsLibs.DocumentGeneration.Tools.md`):
  Parameter `markdown` (Pflicht), `format` (Enum der angebotenen Formate, Pflicht bei mehreren),
  `template` (Enum der Brand-Namen), `fileName`; Antwort `{"file", "format", "slides"|"pages",
  "notes": [{"code","line","message"}]}` bzw. `{"error": "…"}`; falsche Argumente sind
  `ArgumentException` mit einer Meldung für das Modell; der kombinierte Guide sagt alles einmal
  (Formate, Deck-Abschnitte, PDF, Renderer, Front Matter je Format, Zeichen, Fehler, Beispiel,
  Host-Notizen unter `## In this app`), ~3 200 Wörter.
- Hier: Generatoren mit `generate(document, output, options)`; Guides aus E02-S05/E03-S05/E04-S06/
  E05-S05; `docs/ki-anleitung.md` ist heute der Weg für eine KI, die im Klon arbeitet. Ein Host,
  der die Bibliothek einbindet (etwa ein interner Assistent), müsste Schema und Guide selbst
  zusammenbauen.

## Vorgeschlagener Ansatz

1. **`src/pta_documents/tool/`** (ohne Abhängigkeit zu einem SDK):
   - `ToolOptions(docx: DocxOptions | None, pptx: PptxOptions | None, pdf: PdfOptions | None,
     name="make_document", host_notes: str | None)` — `None` heißt: Format nicht angeboten;
     mindestens eins.
   - `describe(options) -> ToolDescription(name, description, parameters_schema, guide)`:
     Beschreibung ein Absatz (< 1 000 Zeichen, deutsch: „Erzeugt ein Word-Dokument, eine
     PowerPoint-Präsentation oder ein PDF im PTA-Design aus Markdown …"); Schema mit `markdown`,
     `format` (Enum `docx`/`pptx`/`pdf`), `vorlage` (Enum der Varianten des gewählten Formats —
     Frage 1), `dateiname` (ohne Endung); keine weiteren Eigenschaften.
   - `run(arguments: str, output: BinaryIO, options, resources=()) -> ToolRun(format, file_name,
     content_type, result)`: JSON lesen, prüfen (Meldung für das Modell: „The parameter 'format'
     is 'html'; expected 'docx', 'pptx' or 'pdf'."), `vorlage` als Front-Matter-Vorgabe anwenden
     (Front Matter im Markdown gewinnt), Generator aufrufen; Dateiname von unzulässigen Zeichen
     befreien, Standard `dokument`.
   - `reply(run, link) -> str` und `reply(error) -> str`: `{"file", "format", "slides"|null,
     "notes": [...]}` bzw. `{"error": "…"}` für `DocumentConversionError` und `ValueError`; andere
     Ausnahmen sind Fehler des Hosts und werden weitergereicht.
2. **Kombinierter Guide** `tool/combined_guide.py`: aus den Guides der angebotenen Formate einer,
   der jeden Abschnitt einmal nennt — Formate, Bericht (Word/PDF: `#` ist Kapitel), Präsentation
   (`#` ist Titel/Trennfolie), Layouts, Renderer, Front Matter je Schlüssel mit „nur Word" /
   „nur PowerPoint", Fehler, Hinweise (E08-S01), Beispiel, Host-Notizen unter `## In dieser
   Anwendung`. Abschnittsteilung über die `##`-Überschriften der Guides wie `CombinedGuide.Sections`.
3. **Beispiel-Anbindung** in `docs/verwendung.md`: Anthropic-SDK (`tools[].input_schema`) und
   OpenAI (`parameters`) nehmen `parameters_schema` unverändert; Guide in den System-Prompt.
4. **Tests** `tests/tool/test_tool.py` (Port von `DocumentToolTests.cs`): Schema gültig
   (`jsonschema` nur als Testabhängigkeit), Enums entsprechen den Optionen, `run` mit jedem Format,
   falsche Argumente mit Meldung, `reply` beider Arten, Guide < 4 000 Wörter und ohne doppelte
   Abschnitte; `.tmp/review/make_document.md` zeigt Beschreibung, Schema und Guide.

## Akzeptanzkriterien

- [ ] `describe` liefert Name, Beschreibung, JSON Schema und Guide passend zu den angebotenen
      Formaten; nicht angebotene Formate fehlen in Enum und Guide.
- [ ] `run` erzeugt die Datei und gibt Format, Dateiname, Content-Type und `GenerationResult`
      zurück; falsche Argumente und Markdown-Fehler ergeben Meldungen für das Modell.
- [ ] `reply` hat für Erfolg und Fehler je eine feste JSON-Form, die ein Test festhält.
- [ ] Kein Import eines KI-SDK in `pta_documents`.

## Offene Fragen

1. Soll `vorlage` ein Parameter sein, obwohl das Front Matter es auch kann? Vorschlag: ja, ein
   Enum hilft dem Modell mehr als Prosa; Front Matter gewinnt.

> (2026-11-07) Ja (Vorschlag angenommen; Story bleibt zurückgestellt).

2. Gibt es einen Host, der das braucht (Epic-Frage 2)? Ohne ihn bleibt die Story liegen.

> (2026-11-07) Nein, die KI arbeitet im Klon mit `run.sh`. Zurückgestellt.

## Notizen

- Für Claude Code im Klon ist `docs/ki-anleitung.md` weiter der Weg; diese Story richtet sich an
  Anwendungen, die die Bibliothek importieren.
