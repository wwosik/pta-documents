# E05-S02 Layout-Engine portieren

> Status: Entwurf
> Epic: [E05 PDF-Generator im PTA-Design](E05-pdf-generator.md)
> Milestone: [M05 PDF](M05-pdf.md)

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
