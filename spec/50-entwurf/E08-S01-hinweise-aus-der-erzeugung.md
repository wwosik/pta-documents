# E08-S01 Hinweise aus der Erzeugung

> Status: Entwurf
> Epic: [E08 Rückmeldung an den Schreiber und KI-Anbindung](E08-rueckmeldung-und-ki-anbindung.md)

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
5. **Werkzeug `generate`:** nach `wrote <datei>` jede Note als `  - line 12: …`; `--streng`
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

- [ ] `DocxGenerator.generate` und `PptxGenerator.generate` geben ein `GenerationResult` zurück;
      `str(result)` ist die Markdown-Liste der Hinweise.
- [ ] Geteilte und übervolle Folien, weggelassenes HTML, nicht gezeichnete Grafikblöcke und
      beschnittene oder stark vergrößerte Bilder ergeben je einen Hinweis mit richtiger Zeile.
- [ ] `./run.sh generate` zeigt die Hinweise unter der Datei; `--streng` setzt den Exit-Code.
- [ ] `samples/` erzeugt ohne Hinweise; die Rundreise-Tests bleiben grün.
- [ ] `ki-anleitung.md`, `anleitung.md`, `verwendung.md` beschreiben Hinweise und Codes.

## Offene Fragen

1. Rohes HTML weglassen (wie vt-tools-libs) oder weiter als Text zeigen und nur melden? Vorschlag:
   weglassen — als Text ist es immer falsch.

>

2. Soll der Hinweis `image-cropped` kommen, wenn der PTA-Bildplatzhalter beschneidet? Beschneiden
   ist dort gewollt; der Hinweis wäre nur bei starkem Verlust (> 25 %) sinnvoll.

>

## Notizen

- E09-S01 (Sprechernotizen), E05-S04 (fehlende Zeichen) und E06 (Renderer) liefern weitere
  Codes; die Liste in `NoteCodes` wächst mit, die Guides nennen jeden.
