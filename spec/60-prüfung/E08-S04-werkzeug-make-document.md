# E08-S04 Werkzeug `make_document` für KI-Hosts

> Status: in Prüfung — reaktiviert 2026-11-08 auf Wunsch des Menschen
> Epic: [E08 Rückmeldung an den Schreiber und KI-Anbindung](../50-entwurf/E08-rueckmeldung-und-ki-anbindung.md)

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

- [x] `describe` liefert Name, Beschreibung, JSON Schema und Guide passend zu den angebotenen
      Formaten; nicht angebotene Formate fehlen in Enum und Guide.
- [x] `run` erzeugt die Datei und gibt Format, Dateiname, Content-Type und `GenerationResult`
      zurück; falsche Argumente und Markdown-Fehler ergeben Meldungen für das Modell.
- [x] `reply` hat für Erfolg und Fehler je eine feste JSON-Form, die ein Test festhält.
- [x] Kein Import eines KI-SDK in `pta_documents`.

## Offene Fragen

1. Soll `vorlage` ein Parameter sein, obwohl das Front Matter es auch kann? Vorschlag: ja, ein
   Enum hilft dem Modell mehr als Prosa; Front Matter gewinnt.

> (2026-11-07) Ja (Vorschlag angenommen; Story bleibt zurückgestellt).

2. Gibt es einen Host, der das braucht (Epic-Frage 2)? Ohne ihn bleibt die Story liegen.

> (2026-11-07) Nein, die KI arbeitet im Klon mit `run.sh`. Zurückgestellt.

## Notizen

- Für Claude Code im Klon ist `docs/ki-anleitung.md` weiter der Weg; diese Story richtet sich an
  Anwendungen, die die Bibliothek importieren.

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08.

### Gebaut

- `src/pta_documents/tool/options.py`: `ToolOptions(docx, pptx, pdf, name="make_document",
  host_notes=None)`; ohne Format oder mit einem Namen außerhalb von `^[A-Za-z0-9_-]{1,64}$`
  (was Anthropic und OpenAI annehmen) `ValueError`. `formats` in der Reihenfolge docx, pptx, pdf.
- `src/pta_documents/tool/tool.py`: `describe` → `ToolDescription(name, description,
  parameters_schema, guide)`; `schema` (JSON Schema 2020-12 als `dict`: `markdown`, `format`,
  `vorlage`, `dateiname`, `additionalProperties: false`, `format` Pflicht bei mehreren Formaten);
  `run` → `ToolRun(format, file_name, content_type, result)`; `reply(run, link)` und
  `reply(error)`; `file_name`; `ToolArgumentError(ValueError)` für falsche Argumente.
- `src/pta_documents/tool/combined_guide.py`: ein Format = der Guide seines Generators; mehrere =
  die erzeugten Guides zusammengeführt (Abschnitte an `##` außerhalb von Codeblöcken, darin
  Absätze, Listenpunkte, Tabellenzeilen und Codeblöcke per `difflib`; Gemeinsames einmal,
  Eigenes mit „Nur …“ markiert; Tabellenzeilen mit gleicher erster Zelle eine Zeile mit den
  Werten je Format — so steht das Front Matter je Schlüssel; `### Hinweise` der Dokumente trifft
  `## Hinweise` von PowerPoint). Vorne `## Formate`, hinten `## In dieser Anwendung`.
- `tests/tool/test_tool.py` (60 Tests): Schema gültig (`Draft202012Validator.check_schema`) und
  Enums je Formatauswahl (alle sieben), Schema nimmt Aufrufe an bzw. lehnt ab, Guide je Format
  gleich dem des Generators, keine doppelten Abschnitte, Wortgrenze, nicht angebotene Formate
  fehlen, Host-Notizen, `run` je Format, Vorlage als Vorgabe und Vorrang des Front Matter,
  falsche Argumente mit Meldung, Dateinamen, beide Antwortformen wortgleich, Fehler des Hosts
  werden weitergeworfen, kein KI-SDK in `src/`. Schreibt `.tmp/review/make_document.md`.
- `pyproject.toml`: `jsonschema>=4.18` (MIT) in `dev`; eine Lock-Datei gibt es nicht.
- `docs/verwendung.md`: neuer Abschnitt „Werkzeug `make_document` für KI-Hosts (E08-S04)“ mit
  Anbindung an Anthropic (`input_schema`) und OpenAI (`parameters`); `ai/Gedächtnis.md`.

### Entscheidungen

- Parameternamen deutsch wie das Front Matter (`vorlage`, `dateiname`), `markdown`/`format` wie
  vorgeschlagen; Beschreibung, Schema-Texte und Guide deutsch, Meldungen an das Modell englisch wie
  alle Fehler der Bibliothek.
- `vorlage` ist **ein** Enum über alle angebotenen Formate (Word/PDF und PowerPoint haben
  verschiedene Namen); `run` prüft, ob die Vorlage zum gewählten Format passt. Ein vom Format
  abhängiges Enum (`if`/`then`) nehmen nicht alle Hosts an.
- `run` nimmt die Argumente als JSON-Text (OpenAI) **oder** als schon gelesenes `dict`
  (Anthropic). `null` und leere Werte freiwilliger Parameter gelten als nicht angegeben.
- Die Antwort hat immer alle Schlüssel: `{"file", "format", "slides", "pages", "notes"}`,
  `slides`/`pages` `null`, wo das Format nichts zählt (die Story nannte `"slides"|null`; `pages`
  für das PDF ist aus vt-tools-libs übernommen).

### Warnungen

- **Warnung:** Die Grenze „Guide < 4 000 Wörter“ ist mit allen drei Formaten nicht zu halten,
  ohne Inhalt zu streichen: PowerPoint allein hat ~3 200 Wörter (`guides.words`), Word ~2 500,
  und was ein Bericht anders macht als eine Präsentation (Vorlagen, Gliederung, Inhalte-Tabelle,
  Front-Matter-Werte, Fehler, Beispiel) sind weitere ~1 100. Der kombinierte Guide hat mit allen
  drei Formaten ~4 400, Word + PowerPoint ~4 130, PowerPoint + PDF ~4 140, Word + PDF ~2 600.
  Gewählt: nichts streichen, Testgrenze 4 500 (`GUIDE_LIMIT`). Wer kürzen will, kürzt die Guides
  der Generatoren selbst.
- **Warnung:** Der kombinierte Guide übernimmt Sätze, die nur im Klon gelten (`./run.sh check`
  bei `pruefung`, `--html` im PowerPoint-Guide, `./run.sh handout`) — sie stehen so in den Guides
  der Generatoren. Für einen Host sind sie harmlos, aber ohne Nutzen; nicht gefiltert, weil das
  Text der Generator-Guides nach Muster verändern hieße.
- **Warnung:** Das HTML-Deck (E10-S01) bietet das Werkzeug nicht an — die Story nennt nur
  `docx`/`pptx`/`pdf`.
- Offener Prüfpunkt: die Anbindung an ein echtes Modell (Anthropic, OpenAI) ist nicht ausprobiert;
  die Beispiele in `docs/verwendung.md` folgen den dokumentierten Formen der APIs.
