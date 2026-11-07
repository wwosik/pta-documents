# E08-S01 Hinweise aus der Erzeugung

> Status: in Prüfung
> Epic: [E08 Rückmeldung an den Schreiber und KI-Anbindung](../50-entwurf/E08-rueckmeldung-und-ki-anbindung.md)
> Milestone: [M02 Rückmeldung und Folien-Syntax](../50-entwurf/M02-rueckmeldung-und-folien-syntax.md)

## Zusammenfassung

`generate()` gibt ein `GenerationResult` zurück: die Zahl der Folien oder Seiten und die
Hinweise, was der Generator umgehen musste — Folie geteilt, HTML weggelassen, Diagramm nicht
gezeichnet, Bild stark vergrößert, Zeichen nicht in der Schrift. Das Werkzeug `generate` zeigt sie
nach jeder Datei, damit der Schreiber (oft eine KI) die nächste Fassung ohne Hinweise schreibt.

## Kontext

- vt-tools-libs: `DocumentGeneration/GenerationResult.cs` (144 Zeilen): `GenerationNote(Code,
  Line, Message)`, `GenerationNoteCodes` (`slide-split`, `slide-overfull`, `character-missing`,
  `raw-html`, `code-not-drawn`, `image-enlarged`), `GenerationResult` (`Notes`, `Slides`,
  `Pages`, `ToString()` als Markdown-Liste `- line 12: …`), Sammler `GenerationNotes` (jeder
  Hinweis einmal, nach Zeile sortiert; `Characters()` sucht Zeichen außerhalb der Schrift je einmal
  an ihrer ersten Zeile). Erzeugt werden sie in `Pptx/DeckWriter.Fitting.cs` (Teilen, übervoll),
  `DeckWriter.cs` Z. 1227 (Bild vergrößert), `CodeBlockRenderer.cs` Z. 153 (nicht gezeichnet),
  `Pdf/MarkdownParser.cs` Z. 227 und `Html/HtmlDeckGenerator.cs` Z. 105 (HTML).
- Hier: `PptxGenerator.generate` und `DocxGenerator.generate` geben `None` zurück.
  `generation/pptx/fitting.py` teilt Text, Tabellen und Code auf Fortsetzungsfolien („(Forts.)"),
  ohne das zu melden; `html_inline`/`html_block` werden in `pptx/parser.py` Z. 357 und
  `docx/writer.py` Z. 500 als Text geschrieben (`ki-anleitung.md`: „Kein HTML (wird als Text
  gezeigt)"); Bildplatzhalter beschneiden Bilder, ohne Rückmeldung; `fence`-Blöcke in `mermaid`
  oder `chart` werden als Code gezeigt.
- `tools/generate/generate.py` druckt `wrote <datei>` bzw. `ERROR <datei>: <grund>`.
- Die Folien-Zeile eines Blocks kennt der `DeckParser` über `token.map` und `body_line`
  (Front-Matter-Versatz) — dieselbe Rechnung wie die Fehlermeldungen.

## Vorgeschlagener Ansatz

1. **Modell** in `generation/common/result.py`: `GenerationNote(code: str, line: int | None,
   message: str)` (frozen dataclass, `__str__` → `line 12: message`), Konstanten in
   `NoteCodes` (`SLIDE_SPLIT`, `SLIDE_OVERFULL`, `IMAGE_CROPPED`, `IMAGE_ENLARGED`, `RAW_HTML`,
   `CODE_NOT_DRAWN`, `CHARACTER_MISSING`, `NOTES_DROPPED` für E09-S01 in Word), `GenerationResult(notes,
   slides, pages)` mit `__str__` als Markdown-Liste bzw. `No notes.`; Sammler `Notes` mit `add(code,
   line, message)` (Duplikate verwerfen, am Ende nach Zeile sortieren) und `characters(markdown,
   line_offset, in_text, in_code, effect)` als Port für E05-S04.
2. **PPTX:** `DeckWriter` bekommt einen `Notes`-Sammler; `fitting`-Aufrufe melden
   `slide-split` („The slide "Kosten" has too much for one slide and continues on 2 more. Split it
   in the Markdown or shorten it.") und `slide-overfull` (Tabelle/Code passen auch bei 12 pt nicht
   auf eine Folie); `visuals.py` meldet `image-cropped`, wenn der Platzhalter mehr als ein Viertel
   der Bildfläche abschneidet („… is cropped to the placeholder; crop it yourself or choose the
   layout 'Titel und Bild 01'"), und `image-enlarged` ab dem Doppelten der natürlichen Größe
   (Pixel aus `ImageInfo`). `DeckParser` meldet `raw-html` und lässt HTML **weg** (Änderung wie
   vt-tools-libs Plan 00015; `ki-anleitung.md` anpassen) und `code-not-drawn` für `fence`-Sprachen
   aus `KNOWN_GRAPHIC_LANGUAGES = ("mermaid", "chart", "financial-chart")` ohne Renderer (die
   Schnittstelle kommt mit E02-S04; bis dahin ist jeder solche Block ein Hinweis).
3. **DOCX:** dasselbe für `raw-html`, `code-not-drawn`, `image-enlarged` (Bild breiter als der
   Satzspiegel bei weniger als 96 dpi); `notes-dropped` für `::: notes` (E09-S01). `pages` bleibt
   `None` — Word zählt erst beim Öffnen.
4. **Rückgabe:** `generate(...) -> GenerationResult` in beiden Generatoren; `slides` aus
   `len(presentation.slides)`. Aufrufer, die den Wert ignorieren, laufen unverändert.
5. **Werkzeug `generate`:** nach `wrote <datei>` jede Note als `  - line 12: …`; `--strict`
   (Frage 1 des Epics) macht Hinweise zum Exit-Code 1. `generate-samples` ebenso.
6. **Dokumentation:** `docs/verwendung.md` (Rückgabe, Codes), `docs/anleitung.md` Abschnitt 8
   („Hinweise sind keine Fehler, aber …"), `docs/ki-anleitung.md` Regel 3 („Hinweise lesen, das
   Markdown so ändern, dass keine mehr kommen; `(Forts.)`-Folien sind fast immer ein Zeichen für zu
   viel Inhalt"). Die Authoring Guides (E02-S05) bekommen den Abschnitt „Hinweise, die
   zurückkommen können" mit der Liste der Codes.
7. **Tests:** `tests/generation/pptx/test_notes.py` und `tests/generation/docx/test_notes.py`
   (Port von `GenerationNoteTests.cs` beider Pakete in vt-tools-libs): übervolle Folie → genau ein
   `slide-split` mit der Zeile des `##`; HTML → `raw-html` mit Zeile; `mermaid` ohne Renderer →
   `code-not-drawn`; Zeilen stimmen auch mit Front Matter; Duplikate einmal; `samples/gsb` und
   `samples/funktionen` erzeugen ohne Hinweise (E08-S03 verschärft das).

## Akzeptanzkriterien

- [x] `DocxGenerator.generate` und `PptxGenerator.generate` geben ein `GenerationResult` zurück;
      `str(result)` ist die Markdown-Liste der Hinweise.
- [x] Geteilte und übervolle Folien, weggelassenes HTML, nicht gezeichnete Grafikblöcke und
      beschnittene oder stark vergrößerte Bilder ergeben je einen Hinweis mit richtiger Zeile.
- [x] `./run.sh generate` zeigt die Hinweise unter der Datei; `--strict` setzt den Exit-Code.
- [x] `samples/` erzeugt ohne Hinweise; die Rundreise-Tests bleiben grün.
- [x] `ki-anleitung.md`, `anleitung.md`, `verwendung.md` beschreiben Hinweise und Codes.

## Offene Fragen

1. Rohes HTML weglassen (wie vt-tools-libs) oder weiter als Text zeigen und nur melden? Vorschlag:
   weglassen — als Text ist es immer falsch.

> (2026-11-07) Weglassen und melden.
2. Soll der Hinweis `image-cropped` kommen, wenn der PTA-Bildplatzhalter beschneidet? Beschneiden
   ist dort gewollt; der Hinweis wäre nur bei starkem Verlust (> 25 %) sinnvoll.

> (2026-11-07) Nur bei starkem Verlust (> 25 %).

## Notizen

- E09-S01 (Sprechernotizen), E05-S04 (fehlende Zeichen) und E06 (Renderer) liefern weitere
  Codes; die Liste in `NoteCodes` wächst mit, die Guides nennen jeden.

## Implementierungsnotizen

Umgesetzt am 2026-11-07 von `docs-2`.

**Was entstand**

- `generation/common/result.py`: `GenerationNote` (frozen, `__str__` → `line 12: …`),
  `GenerationResult(notes, slides, pages)` (frozen; `__str__` Markdown-Liste bzw. `No notes.`,
  `codes()`), `NoteCodes` (acht Codes + `ALL`), Sammler `Notes` (`add`, `to_tuple`, `len`,
  `characters` als Port für E05-S04). `GenerationNote`, `GenerationResult`, `NoteCodes` sind auch
  aus `pta_documents` importierbar.
- `generation/common/html.py` (Kommentar, `<br>`, Checkbox, `note_raw_html`) und
  `generation/common/code_blocks.py` (`KNOWN_GRAPHIC_LANGUAGES`, `fence_language`,
  `note_not_drawn`).
- `markdown/parser.py`: `html: True`; neu `child_lines(inline, offset)` für die Zeile eines
  Inline-Kindes (zählt Umbrüche im Absatz).
- PPTX: `DeckParser` und `DeckWriter` bekommen den Sammler; Meldungen `slide-split`
  (Text-, Tabellen-, Code- und Bildreihen-Teilung, Zeile des `##`), `slide-overfull` (Textteil
  passt bei 12 pt nicht, Tabelle/Code passt nicht in den Platz), `image-cropped` (> 25 %
  Flächenverlust im Platzhalter, aus `crop_*` von python-pptx), `image-enlarged` (> 2× der Pixel
  bei 96 dpi, im Platzhalter und in Bildreihen), `raw-html`, `code-not-drawn`. `Image` im Modell
  hat jetzt `line`. `generate()` gibt `GenerationResult(slides=len(presentation.slides))` zurück.
- DOCX: `BodyWriter` meldet `raw-html` (Block, inline, in Tabellen, Listen, Fußnoten),
  `code-not-drawn`, `image-enlarged`; `generate()` gibt `GenerationResult()` mit `pages=None`.
- Werkzeuge: `generate` zeigt Hinweise als `  - line 12: …` unter `wrote …`, `--strict` setzt bei
  Hinweisen Exit-Code 1; `generate-samples` zeigt sie ebenso und endet bei Hinweisen mit 1.
- Tests: `tests/generation/common/test_result.py`, `tests/generation/{pptx,docx}/test_notes.py`
  (156 → 178 Tests), inkl. „Beispiele erzeugen ohne Hinweise".
- Doku: `docs/verwendung.md` (neuer Abschnitt „Hinweise" mit Code-Tabelle), `docs/anleitung.md`
  Abschnitt 8, `docs/ki-anleitung.md` Regel 3, HTML-Zeile, Bildregel, Python-Beispiel,
  Checkliste. Gedächtnis ergänzt.

**Entscheidungen und Abweichungen**

- Rohes HTML wird weggelassen und gemeldet (Antwort Frage 1). Dafür ist im gemeinsamen Parser
  HTML eingeschaltet. Ausnahmen ohne Hinweis: HTML-Kommentare (wie vt-tools-libs), die Checkbox
  des Tasklist-Plugins und **`<br>` als Zeilenumbruch** — die eigenen Konverter schreiben `<br>`
  in Tabellenzellen; ohne diese Ausnahme ergäbe jede Rundreise Hinweise und verlöre Umbrüche.
  Text wie `<Kunde>` gilt für markdown-it als HTML und fällt jetzt mit Hinweis weg (vorher als
  Text gezeigt).
- Mehrere HTML-Stücke derselben Zeile ergeben einen Hinweis (gleicher Code, Zeile, Text).
- Hinweistexte wie in vt-tools-libs; `slide-split` mit dem Satz der Story („Split it in the
  Markdown or shorten it."). vt-tools-libs' `scale=1` im Bildtitel gibt es hier nicht; der
  Hinweis rät nur zu einem größeren Bild.
- **Warnung:** `image-enlarged` in Word nicht wörtlich wie im Plan („breiter als der Satzspiegel
  bei weniger als 96 dpi"), sondern mit derselben Schwelle wie PPTX: gemeldet, wenn das Bild mehr
  als doppelt so groß erscheint wie seine Pixel bei 96 dpi (effektiv unter 48 dpi). Die
  wörtliche Regel hätte jedes 72-dpi-Bildschirmfoto gemeldet bzw. war widersprüchlich (ein
  Bild breiter als der Satzspiegel wird verkleinert, nicht vergrößert). Vorsichtig = weniger
  Fehlalarme, gleiche Bedeutung in beiden Formaten.
- `notes-dropped` ist nur als Code angelegt; erzeugt wird er mit E09-S01 (dort in den Notizen
  vermerkt), weil `::: notes` erst mit dem Container-Plugin (E02-S02/E09-S01) erkannt wird.
- `character-missing`/`Notes.characters` ist portiert und getestet, wird aber erst mit E05-S04
  (PDF) aufgerufen (dort vermerkt). Statt `AuthoringGuides.Symbols` nimmt es `alternatives`.
- `code-not-drawn` kommt für jeden `mermaid`/`chart`/`financial-chart`-Block, da es noch keinen
  Renderer gibt; E02-S04 muss den Aufruf hinter die Renderer setzen (dort vermerkt).
- `slide-overfull` und `slide-split` können für dieselbe Folie zusammen kommen (wie
  vt-tools-libs). Benannte Layouts (`{layout="…"}`) werden nicht gefittet und melden nichts.
- **Warnung:** Damit `samples/` ohne Hinweise erzeugt (Akzeptanzkriterium), wurde
  `samples/funktionen/funktionen-praesentation.md` geändert: die Folie mit 22 Punkten ist auf 12
  gekürzt („Viel Text wird verkleinert"), die 14-zeilige Tabelle auf 9 Zeilen („Längere
  Tabelle"); beide Demos der „(Forts.)"-Teilung entfallen damit. Die Bilder `diagramm.png` und
  `banner.png` verloren im Bildplatzhalter 29 % bzw. 40 %; neu sind `diagramm-folie.png` und
  `banner-folie.png` (dieselben selbst erzeugten Bilder, oben/unten mit Rand- bzw.
  Verlaufszeilen auf die Platzhalter-Proportionen 1,14:1 bzw. 2,38:1 erweitert), die die
  Präsentation nun verwendet. README der Beispiele angepasst.

**Prüfpunkte**

- `./run.sh generate samples/funktionen --out documents/x` ohne Hinweise; ein Markdown mit
  zu voller Folie, `<div>` und `mermaid` zeigt drei Hinweise, `--strict` endet mit 1.
- Wortlaut der Hinweise (englisch, wie die Fehlermeldungen) ansehen.
- Neue Folienbilder in `.tmp/samples/funktionen/funktionen-praesentation.pptx` ansehen.

**Offene Punkte**

- Authoring Guides (E02-S05) bekommen den Abschnitt „Hinweise, die zurückkommen können" (dort
  vermerkt). PDF-Hinweise folgen mit E05 (E05-S01/E05-S04).
