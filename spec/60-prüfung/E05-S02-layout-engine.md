# E05-S02 Layout-Engine portieren

> Status: in Prüfung
> Epic: [E05 PDF-Generator im PTA-Design](../50-entwurf/E05-pdf-generator.md)
> Milestone: [M05 PDF](../50-entwurf/M05-pdf.md)

## Zusammenfassung

Die Layout-Engine von DocLibs in Python: Markdown wird zu einem Blockmodell, das Blockmodell zu
Seiten mit Absätzen, Listen, Tabellen, Bildern, Code, Seitenumbruchregeln, Lesezeichen und Links —
in den Formatvorlagen der PTA-Word-Vorlage statt in DocLibs' eigenen Größen.

## Kontext

- DocLibs: `MarkdownParser.cs` (406 Zeilen, Markdig → `DocumentModel`), `DocumentModel.cs` (67),
  `LayoutEngine.cs` (1 213: Zeilenumbruch, Seitenumbruch, Listen, Tabellen mit wiederholtem
  Kopf, Bilder, Bildreihen, Zitate, Code, Lesezeichen, Anker, Kopf/Fuß), Tests `LayoutTests.cs`
  (428, 25 Fälle) und `PdfGeneratorTests.cs`, Beispiele `report.md`, `long.md`.
- DocLibs hat feste Größen (`BodySize` 10,5, `HeadingSizes` 20/16/13,5 …, Seitenrand 20 mm). Für
  die PTA gelten die Formatvorlagen der Word-Vorlage (Designanalyse, *Formatvorlagen*); laut E05
  werden sie aus der Vorlage gelesen, nicht im PDF-Code wiederholt.
- Der DOCX-Generator (E03-S02, `generation/docx/writer.py`) legt die Zuordnung Markdown →
  Formatvorlage fest; das PDF folgt ihr.

## Vorgeschlagener Ansatz

1. `src/pta_documents/design/word_styles.py`: liest aus `styles.xml` der eingebetteten
   Word-Vorlage je benötigter Formatvorlage (`STYLES` aus `design/word.py`) Größe, fett,
   Versalien, Farbe, Abstand vor/nach, Zeilenabstand „mindestens", Einzug/hängend und „mit
   nächstem Absatz zusammen" — mit Vererbung über `basedOn` und Theme-Farben. Ein Test vergleicht
   mit der Tabelle der Designanalyse.
2. `generation/pdf/model.py`: Port von `DocumentModel.cs` (`TextRun` mit `RunStyle`,
   `HeadingBlock`, `ParagraphBlock` mit Formatvorlage, `ListBlock`, `CodeBlock`, `QuoteBlock`,
   `TableBlock`, `ImageBlock`, `ImageRowBlock`, `RuleBlock`, `CaptionBlock`); `Cover` entfällt
   (Deckblatt aus dem Front Matter, E05-S03).
3. `generation/pdf/parser.py`: Port von `MarkdownParser.cs` auf die Token von
   `markdown/parser.py`. Zuordnung wie im DOCX: `#`–`###` nummerierte Überschriften 1–3
   (`1`, `1.1`, `1.1.1`, hängender Einzug aus der Vorlage), tiefere → „Zwischenüberschrift"
   (Versalien, ohne Nummer); Absatz nur aus `**…**` → „Standard fett"; `Tabelle: …` nach einer
   Tabelle → „Tabelle n: …", Bild allein im Absatz mit Titel/Alt-Text → „Abbildung n: …"
   (`GeneratedTexts`); Aufgaben- und Definitionslisten wie im DOCX. Die gemeinsamen Erkennungen
   wandern aus `docx/writer.py` nach `generation/common/` (`_only_strong`, Beschriftungspräfix).
   Anker GitHub-artig aus dem Überschriftentext (`markdown/anchors.py`, neu).
4. `generation/pdf/layout.py`: Port von `LayoutEngine.cs` über `FontMetrics` (E05-S01), Verhalten
   1:1: gieriger Umbruch an Leerzeichen, zu lange Wörter zeichenweise; Überschriften bleiben beim
   Anfang des Folgenden (Ketten, `KeepHeight`); Absätze lassen nie eine einzelne Zeile auf einer
   Seite (`KeepLines`); Listenzeichen wandern mit der ersten Zeile; Tabellen mit Spaltenbreiten
   nach längstem Wort, wiederholtem Kopf und geteilten Überlangzeilen; Bilder in 96 DPI
   (0,75 pt/px), nur verkleinert, `"scale=0.5"` im Titel; Bildreihen in gleich breiten Zellen;
   zu hohe Bilder werden verkleinert, um mit ihrer Überschrift auf eine Seite zu passen.
5. PTA-Abweichungen in `layout.py`:
   - Größen, Abstände, Farben aus Schritt 1; Satzspiegel aus `w:sectPr` der Variante (Hoch
     2,20/3,50/2,20/2,00 cm, Quer 2,20/4,20/2,20/2,50 cm).
   - `#` beginnt **keine** neue Seite (die Vorlage hat dort keinen Seitenumbruch).
   - Aufzählungszeichen als Vektor: Ebene 1 ■ in PTA-Blau, Ebene 2/3 ― in Schwarz, Einzüge
     0,6/1,2/1,8 cm; nummerierte Listen `1.` (Einzug wie „Listenabsatz").
   - Tabellen im Stil `PTA`: Kopf `006FB9` mit weißer Schrift, nur waagerechte Linien 0,5 pt
     `AFAFAF`, Zellenränder links/rechts 0; Titel „Standard fett" darüber wird mit der Tabelle
     zusammengehalten.
   - Code Consolas-Ersatz 9 pt auf `E6E6E6` (`word.CODE`), Zitat eingerückt um 1,25 cm
     (`word.QUOTE_INDENT_CM`), Linie `---` in `GREY_MID`, Links `004676` unterstrichen.
6. Lesezeichen für Überschriften 1–3 mit ihrer Nummer; interne Links `[x](#anker)` springen auf
   die Überschrift, externe brauchen eine absolute URL (sonst Text, wie DocLibs).
7. Tests `tests/generation/pdf/test_layout.py` mit erfundenen Breiten (wie DocLibs) — die
   25 Fälle aus `LayoutTests.cs` ohne die Deckblatt-, Zeichen- und Zeichnungsfälle (E05-S03,
   E05-S04) — und `test_generator.py`: `report.md` und `long.md` aus DocLibs (um PTA-Fälle
   ergänzt) → PDF → `PdfConverter` (E07-S04) → `*.roundtrip.expected.md`; Dateien nach
   `.tmp/review/`.

## Akzeptanzkriterien

- [ ] Schriftgrößen, Abstände und Farben jedes Blocks entsprechen der Formatvorlage, die das
      DOCX für denselben Block verwendet; Werte stammen aus der Vorlage, nicht aus Konstanten.
- [ ] Überschriften sind nummeriert wie im DOCX und stehen nie allein am Seitenende.
- [ ] Kein Absatz lässt eine einzelne Zeile oben oder unten auf einer Seite.
- [ ] Lange Tabellen wiederholen ihren Kopf auf jeder Seite.
- [ ] Bilder werden nie geteilt und nur verkleinert.
- [ ] Lesezeichen folgen den Überschriften 1–3; interne und externe Links funktionieren.
- [ ] Die Rundreise-Tests für `report.md` und `long.md` sind grün.

## Offene Fragen

1. Fußnoten: Word setzt sie an den Seitenfuß. Vorschlag für das PDF: ebenfalls am Fuß der Seite
   mit dem Verweis (8 pt „Fußnotentext", Trennlinie), oder einfacher gesammelt am Ende des
   Dokuments?

> (2026-11-07) Am Fuß der Seite, wie Word.

## Notizen

- Größter Brocken des Epics (~1 200 Zeilen C#). Rundreise-Tests setzen E07-S04 voraus; bis dahin
  prüfen die Tests das Layout am Seitenmodell.
- Kopf- und Fußzeile, Deckblatt und Inhaltsverzeichnis kommen in E05-S03; die Engine lässt dafür
  wie DocLibs `Decorate` einen Durchgang nach dem Layout, wenn die Seitenzahl feststeht.
- (E17-S02, docs-2) Der PDF-Teil von E17-S02 kommt hierher: `generation/pdf/hyphenation.py` mit
  **pyphen** im Extra `pdf` (Tri-Lizenz, MPL-Wahl in `pyproject.toml` kommentieren und in
  `docs/verwendung.md` nennen); Trennung nur an pyphen-Trennstellen, wenn sonst mehr als ein
  Fünftel der Zeile leer bliebe, mind. 2 Zeichen davor/3 danach, nie in Code/Links/letztem Wort
  eines Absatzes/über Seitenwechsel, Bindestrich-Wörter nur am Bindestrich; Front Matter
  `blocksatz: ja|nein` (Standard nein) und `silbentrennung: ja|nein` (Standard ja), Tests
  `tests/generation/pdf/test_hyphenation.py`. Dazu `PdfOptions.typography`/`highlight` und die
  Front-Matter-Schlüssel `typografie`/`syntaxhervorhebung` (`Keys.TYPOGRAPHY`/`HIGHLIGHT`),
  `markdown.typography.typeset(tokens, language)` nach `layout_syntax.check` aufrufen (Status-
  Labels mit `typeset_text` setzen), und Code farbig in Mono über
  `generation.common.code_highlight.highlight_fence` (Spans mit `CodeSpan.look`: Farbe, fett,
  kursiv; `None` = Textfarbe).

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08, parallel zu E05-S01 (eigener Worktree; E05-S01 lag beim
Umsetzen noch nicht vor). Neu: `design/word_styles.py` (Formatvorlagen, Nummerierung,
Tabellenvorlage `PTA`, Satzspiegel aus der Vorlage), `markdown/anchors.py` (GitHub-Anker),
`generation/common/block_shapes.py` (gemeinsame Erkennungen von DOCX und PDF: `only_strong`,
`only_images`, `is_table_caption`, `is_figure_caption`, `strip_caption_prefix` — aus
`docx/writer.py` herausgezogen, der Writer nutzt sie jetzt), das Unterpaket
`generation/pdf/layout/` (`__init__.py` mit `layout`, `fonts.py`, `styles.py`, `inline.py`,
`flowables.py`, `story.py`, `document.py`), in `design/fonts/truetype.py` `slanted`,
`with_aliases` und `FontInfo.line_units`/`line_height`. Tests: `tests/design/test_word_styles.py`,
`tests/markdown/test_anchors.py`, `tests/generation/common/test_block_shapes.py`,
`tests/design/test_fonts.py` (+2), `tests/generation/pdf/layout/` (`test_layout.py` mit den
Fällen aus `LayoutTests.cs`, `test_story.py`, `test_fonts.py`, `test_samples.py` mit `report.md`
— um PTA-Fälle ergänzt — und `long.md` aus vt-tools-libs, dazu `diagram.png`; Ansicht
`.tmp/review/pdf-layout-report.pdf` und `pdf-layout-long.pdf`). Doku: `docs/verwendung.md`
(neuer Abschnitt „PDF-Layout-Engine (E05-S02)"), `ai/Gedächtnis.md` (neuer Eintrag, U+00A0
korrigiert). Keine neue Abhängigkeit (reportlab, fontTools, pikepdf, pdfplumber sind schon im
Extra `pdf`).

**Schnittstelle für den Generator (E05-S01):**

```python
from pta_documents.generation.pdf.layout import LayoutSettings, PdfInfo, layout

result = layout(
    tokens,  # Rumpf nach layout_syntax.check(…, DocumentFormat.PDF, …) und ggf. typeset
    document,  # MarkdownDocument (Bilder aus resources)
    LayoutSettings(
        variant,
        language,
        fonts,
        justify,
        highlight,
        image_converters,
        code_block_renderers,
        line_offset,
        status_labels,
    ),
    notes,
    PdfInfo(title, author, subject, language),
    decorate=None,  # E05-S03: Kopf-/Fußzeile je Seite
)
result.content  # PDF-Bytes von reportlab, noch kein PDF/A → Nachlauf von E05-S01
result.pages  # → GenerationResult.pages
```

Die Einbindung in `PdfGenerator.generate` geschieht bei der Zusammenführung mit E05-S01.

### Entscheidungen

- **Platypus statt eigener Seitenmodell-Engine.** Die Engine baut reportlab-Flowables und lässt
  reportlabs Platypus umbrechen; DocLibs' Regeln sind dort nachgebaut: gieriger Umbruch an
  Leerzeichen, zu lange Wörter zeichenweise (`splitLongWords`, Code mit `wordWrap="CJK"`),
  `allowWidows=0`/`allowOrphans=0` (nie eine einzelne Zeile), `KeepWithStart` vor jeder Folge
  von Überschriften (DocLibs `KeepHeight`: Überschriften + zwei Zeilen eines Absatzes bzw. Kopf
  und erste Zeile einer Tabelle bzw. das ganze Bild), Listenzeichen gehören zum ersten
  Absatzteil (`PtaParagraph.marker`), `Table(repeatRows, splitByRow, splitInRow)`, Bilder als
  unteilbare `Image`-Flowables. Grund: der Auftrag nannte Flowables als Schnittstelle, und
  E05-S01 baut gleichzeitig `fonts.py`/`page_model.py`/`renderer.py` — eine zweite
  Seitenmodell-Engine hätte dessen Dateien doppelt angelegt.
- **Abstände addieren sich** (Abstand nach + Abstand vor) wie in Word:
  `Frame(…, overlapAttachedSpace=0)`; reportlab nähme sonst nur den größeren.
- **Zeilenhöhe:** „mindestens" = max(Wert der Vorlage, einfache Zeile); „einfach" =
  Windows-Ascent + -Descent der verwendeten Schrift (Selawik/Segoe UI 1,33 × Größe, Inconsolata
  1,46, Consolas ≈ 1,17), wie Word sie misst.
- **Überschriften-Nummern** im hängenden Einzug aus `numbering.xml` (Ebene 1/2: 1,25 cm,
  Ebene 3: 1,70 cm), in Farbe und Schnitt der Überschrift; Lesezeichen „1.2 Titel"; eine
  übersprungene Ebene (`#` → `###`) zählt wie Word mit 0 („2.0.1") und hängt im
  Lesezeichenbaum nur eine Ebene tiefer.
- **Listen wie im DOCX:** jede Liste beginnt bei 1 (`3.` im Markdown wird `1.`), die äußere
  Liste bestimmt die Vorlage, Unterlisten nehmen deren Ebenen 2/3 (eine nummerierte Liste zeigt
  in Ebene 2 ■ — so definiert „Listenabsatz" sie). Quadrat 0,45 × Größe, Strich 0,75 × Größe,
  beide gezeichnet.
- **Aufgabenlisten:** das Kästchen ☐/☒ ersetzt das Listenzeichen (Selawik hat die Zeichen
  nicht; im DOCX steht es hinter dem ■).
- **Tabellen:** Zellabstand oben = Abstand vor von „Standard" (6 pt), unten = Abstand nach der
  Tabellenvorlage (0 pt), Zeilenabstand einfach, Kopf nicht fett (wie die Vorlage);
  Spaltenbreiten nach der Regel von `text_metrics.column_widths`, aber mit echten
  Schriftbreiten.
- **Synthetische Kursive** als schräggestellte Kopie der Schriftdatei (`truetype.slanted`, 12°,
  zusammengesetzte Glyphen zerlegt, Hinting entfernt, PostScript-Name `…-Slanted`), weil
  reportlabs Absätze keine Textmatrix je Wort kennen. Inconsolata bleibt in Kursiv aufrecht.
- **Fehlende Leerzeichen-Glyphen:** U+00A0, U+202F, U+2011 bekommen beim Registrieren die
  Glyphe von Leerzeichen bzw. Bindestrich (`truetype.with_aliases`); ihr Umbruchverhalten
  bleibt. Alles Weitere (`replace_unsupported`) ist E05-S04.
- **Fußnoten am Seitenfuß** (Antwort auf Frage 1): `FootnoteAnchor` vor dem Absatz reserviert
  den Platz unten (`frame._y1p`), die Seite zeichnet sie über dem unteren Rand unter einer
  2-Zoll-Linie in „Fußnotentext". Jeder Verweis bekommt die nächste Nummer (wie im DOCX).
- **Seitenrahmen später:** `decorate(canvas, seite, seitenzahl)` am Ende jeder Seite; mit
  `decorate` setzt `layout` zweimal (erst zählen). Deckblatt und Inhaltsverzeichnis können über
  `build_story` + eigene Flowables + `render` dazukommen (E05-S03).
- **Container und Alerts** schlicht wie im DOCX: Inhalt als normale Blöcke, Überschriften darin
  „Standard fett", `::: notes` weg (Hinweis `notes-dropped`), Alerts/Fazit/Kommentar als graue
  Box mit Linie links nach `word.NOTE`/`NOTE_IMPORTANT`. Folienarten (`{.agenda}` …) werden
  noch als gewöhnliche Überschriften gesetzt.
- **Bilder:** immer 96 dpi wie DocLibs (das DOCX liest die dpi des PNG); `"scale=x"` im Titel,
  der Rest des Titels (sonst der Alt-Text) wird die Beschriftung.
- **Determinismus:** `invariant=1` (feste Zeitstempel und ID); Zeitstempel der Metadaten und
  PDF/A setzt E05-S01 im Nachlauf.

### Abweichungen

- **Kein Dreiklang `model.py`/`parser.py`/`layout.py`** (Plan Punkte 2–4): Blockmodell und
  Layout fallen in `layout/story.py` zusammen (Token → Flowable); `DocumentModel.cs` hat kein
  Gegenstück. Seitenmodell und `FontMetrics` von E05-S01 werden nicht benutzt; Breiten misst
  reportlab mit denselben Dateien.
- **Schriftregistrierung doppelt:** `layout/fonts.py` registriert die Schriften selbst (gleiches
  Namensschema `PTA-<sha8>` wie in E05-S01 geplant). Bei der Zusammenführung eine der beiden
  Stellen streichen.
- **Tests mit echten PDFs** statt erfundener Breiten: die Fälle von `LayoutTests.cs` bauen ein
  PDF und lesen es mit pdfplumber/pikepdf zurück; die Seitenumbruch-Fälle schieben den Inhalt
  mit einem Abstandsbild in 4–5-pt-Schritten über das Seitenende. Die Rundreise-Tests
  (`*.roundtrip.expected.md`) fehlen, weil der PDF-Konverter (E07-S04) noch nicht existiert.
- `generation/pdf/` hat **kein `__init__.py`** (Namespace-Paket), damit es nicht mit dem
  `__init__.py` von E05-S01 (Hinweis auf das Extra) kollidiert.

### Warnungen

- **Silbentrennung (pyphen) nicht umgesetzt** (Notiz aus E17-S02): pyphen steht unter
  GPL/LGPL/MPL; die Vorgabe für M02–M06 erlaubt nur MIT/BSD/Apache/OFL. Vorsichtigste Wahl:
  keine Abhängigkeit, keine Trennung. Blocksatz ist als `LayoutSettings.justify` da; die
  Front-Matter-Schlüssel `blocksatz`/`silbentrennung`/`typografie`/`syntaxhervorhebung` und
  `PdfOptions.typography`/`highlight` gehören zum Generator (E05-S01). Der Mensch muss
  entscheiden, ob pyphen (MPL) doch erlaubt ist.
- **Fußnoten:** passt eine Fußnote mit dem Anfang ihres Absatzes nicht mehr auf die Seite,
  wandern beide; wird der Absatz danach geteilt und liegt der Verweis im zweiten Teil, steht die
  Fußnote eine Seite zu früh. Word würde die Fußnote fortsetzen; das gibt es hier nicht.
  Fußnoten in Tabellenzellen stehen auf der Seite, auf der die Tabelle beginnt.
- **Code mit Inconsolata** hat eine höhere einfache Zeile (1,46) als Consolas (≈ 1,17): ohne
  Consolas im System laufen Codeblöcke im PDF etwas höher als im DOCX. Kursiver Code bleibt
  aufrecht.
- **Bildreihen** werden als Tabelle ohne Linien gesetzt und höchstens 50 % der Satzspiegelhöhe
  hoch; nach einer Überschrift werden sie nicht eigens verkleinert.
- **Zwischenüberschriften** (Ebene 4–6) bekommen einen Anker für Links, aber kein Lesezeichen
  (wie Word, das sie nicht ins Verzeichnis nimmt).
- **Prozessweite Schriftliste:** reportlab kennt nur eine globale Schriftliste; die Namen aus
  dem Inhalts-Hash machen sie ergebnisneutral, der `functools.cache` für vorbereitete Dateien
  (Alias, Schrägstellung) hängt nur von den Bytes ab.

### Prüfpunkte

- `.tmp/review/pdf-layout-report.pdf` und `pdf-layout-long.pdf` (aus `./run.sh test
  tests/generation/pdf`) neben ein DOCX desselben Markdowns legen: Größen, Farben, Abstände,
  Nummern, Einzüge, Tabellenstil, Kursive (schräg), Fußnote am Seitenfuß, Lesezeichenleiste
  beim Öffnen.
- Ob die addierten Abstände dem Word-Export entsprechen — auf einem Rechner mit Word prüfen.
- `./run.sh test tests/generation/pdf tests/design/test_word_styles.py`.

### Offene Punkte

- **Einbindung in `PdfGenerator`** bei der Zusammenführung mit E05-S01: Aufruf wie oben,
  `GenerationResult.pages = result.pages`, `PdfInfo` aus Front Matter/Metadaten, Typografie vor
  `layout`, eine der beiden Schriftregistrierungen streichen, `generation/pdf/__init__.py` von
  E05-S01 übernehmen.
- **Rundreise-Tests** für `report.md`/`long.md` mit dem PDF-Konverter (E07-S04).
- **E05-S03:** Kopf-/Fußzeile über `decorate`, Deckblatt und Inhaltsverzeichnis vor die Story;
  bei den Varianten mit Deckblatt hat die erste Seite eigene Ränder.
- **E05-S04:** Folien-Syntax als Boxen/Spalten, Charts/Zeichnungen (bis dahin Code mit
  `code-not-drawn`), `replace_unsupported`.
- Silbentrennung (siehe Warnung).

### Zusammenführung mit E05-S01 (2026-11-08)

E05-S01 und E05-S02 wurden parallel in getrennten Worktrees umgesetzt und danach gemeinsam nach
`main` gebracht (Merge-Commits, dann ein Commit „E05-S01/E05-S02: Layout-Engine in den
PDF-Generator eingebunden"). Vereinheitlicht:

- `PdfGenerator.generate` ruft für den Rumpf die Layout-Engine aus E05-S02 auf
  (`layout.layout(tokens, document, LayoutSettings, notes, PdfInfo)`) und schickt
  `result.content` durch den PDF/A-2b-Schritt aus E05-S01 (`pdfa.to_pdfa`);
  `GenerationResult.pages` kommt aus der Engine. Davor wie im DOCX:
  `layout_syntax.check(…, today)`, `generated_images.add_generated` (QR-Codes), `typeset`.
- Front Matter: `typografie` und `syntaxhervorhebung` stehen jetzt in `VALID_KEYS`, in
  `PdfOptions` (`typography`, `highlight`) und in `apply_front_matter`; `VALID_KEYS` ist damit
  gleich dem des DOCX-Generators. Status-Labels werden wie im DOCX mitgesetzt.
- Ränder und Seitengröße kommen aus der Vorlage (`design.word_styles`), nicht mehr aus
  Konstanten.
- **Eine** Schriftregistrierung (`layout/fonts.register`, `PTA-<sha8>`), **ein** `PdfInfo`
  (`metadata.py`, mit Standardwerten; die Engine nimmt es auch für reportlab).
- Fehlende Zeichen werden jetzt in der Engine `?` (`PdfFonts.shown`, aufgerufen in
  `InlineWriter.text`; Text: Regular und Bold, Code: Mono; die Aliase U+00A0/U+202F/U+2011
  zählen als vorhanden) — dieselbe Regel wie `Notes.characters` im Generator.
- QR-Codes sind im PDF 3 cm breit (mal `scale`) wie in Word; `::: timeline` und `::: gantt`
  zeigen ihren Inhalt mit `code-not-drawn` bis E05-S04 (beide kamen nach den Claims mit E11-S04
  bzw. E15-S01 auf `main`).
- Ein leeres Dokument ergibt wie bisher eine leere Seite (die Engine baut dann einen leeren
  Spacer).

Entfernt (nichts nutzt es mehr; Stand in Commit 175e572): `simple_layout.py` (Zwischenlayout),
`body.py` (`BodySource`/`BodyLayout`, die Naht `generator.BODY_LAYOUT`), `page_model.py` und
`renderer.py` (eigenes Seitenmodell und Zeichner — die Engine setzt mit Platypus direkt auf den
Canvas), `fonts.py` aus E05-S01 (`FontMetrics`, zweite Registrierung). E05-S03 braucht sie
nicht (Seitenrahmen über `layout(…, decorate=…)`), E05-S04 zeichnet Zeichnungen als eigene
Flowables auf dem reportlab-Canvas; das Malen von Pfaden mit Kurven und Strichmustern aus dem
alten `renderer.py` kann dort aus der Git-Geschichte übernommen werden. `test_renderer.py` wurde
zu `test_pdfa.py`: dieselben Prüfungen (PDF/A-Metadaten, OutputIntent, eingebettete Schriften,
>255 Zeichen, lange Titel, Lesezeichen, Links, Bilder einmal, Byte-Gleichheit, veraPDF) laufen
jetzt über den Generator mit Markdown; der Naht-Test entfiel. Neu: Tests für Typografie,
Hervorhebung, QR-Größe, Zeitstrahl-Hinweis, fehlende Zeichen im Code und alle Word-Beispiele in
`samples/` als PDF (nur `code-not-drawn` erlaubt).
