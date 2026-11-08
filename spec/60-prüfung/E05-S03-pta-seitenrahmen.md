# E05-S03 PTA-Seitenrahmen

> Status: in Prüfung
> Epic: [E05 PDF-Generator im PTA-Design](../50-entwurf/E05-pdf-generator.md)
> Milestone: [M05 PDF](../50-entwurf/M05-pdf.md)

## Zusammenfassung

Was um den Inhalt herum auf jeder PDF-Seite steht, wie in den PTA-Word-Vorlagen: Deckblatt,
Inhaltsverzeichnis, Kopfzeile mit Logo und Verlaufslinie, Fußzeile mit Firma, Stand und
Seitenzahl — für alle vier Varianten (`hoch`, `hoch-ohne-deckblatt`, `quer`,
`quer-ohne-deckblatt`).

## Kontext

- DocLibs zeichnet einen generischen Rahmen: `LayoutEngine.Cover` (Titel 30 pt bei 28 % der
  Seitenhöhe, Brand-Grafiken) und `LayoutEngine.Decorate` (Titel und Logo oben, Fußtext, Datum,
  „n / m"). Beides wird für die PTA neu gebaut; übernommen wird nur das Vorgehen: Kopf und Fuß in
  einem Durchgang nach dem Layout, wenn die Seitenzahl feststeht.
- Werte: Designanalyse, *Kopf- und Fußzeile* und *Deckblatt*. In den Vorlagen (`header1.xml`,
  `header2.xml`, `footer1.xml`) stehen sie als verankerte Grafiken: Logo Hoch 2,22 × 1,28 cm,
  1,09 cm von oben, rechts am Satzspiegel; Quer 3,01 × 1,73 cm bei 24,49/1,05 cm; Linie Hoch
  16,6 cm bei 2,20/2,80 cm, über der Fußzeile bei 28,20 cm; Quer 25,3 cm bei 3,40 cm bzw.
  19,20 cm; erste Seite von `quer` mit Linie bei 6,00 cm. Verlauf `accent1` → `accent3` (53 %) →
  `accent3` mit Alpha 0, Strich aus `lnRef idx="1"` des Themes.
- Der DOCX-Generator (E03-S01, `generation/docx/generator.py`) legt Texte und Front Matter fest:
  Deckblatt „Titel / Untertitel / Autor, Ort, Datum", „Inhalt"/„Contents", Fußzeile „PTA
  IT-Beratung" (`firma`), „Stand:"/„As of:" mit `datum` oder heute, „Seite"/„Page".

## Vorgeschlagener Ansatz

1. `src/pta_documents/design/word_frame.py`: liest je `WordVariant` aus der eingebetteten Vorlage
   Seitengröße, Ränder, Kopf-/Fußzeilenabstand (`w:sectPr`), die Anker von Logo und Linien
   (`wp:anchor` mit `positionH`/`positionV`/`extent`), Breite der Kopfzeilentabelle (11,5 bzw.
   17,5 cm) und die Spalten der Fußzeilentabelle → `PageFrame` (frozen dataclass, Punkte). Tests
   vergleichen mit den Werten oben. So gibt es keine zweite Wertetabelle im PDF-Code.
2. `generation/pdf/frame.py`: `decorate(pages, frame, info, texts)` statt `Decorate`:
   - **Kopfzeile** (Folgeseiten): Titel fett PTA-Blau, darunter Untertitel, „Kopfzeile" 10 pt,
     in der Breite der Kopfzeilentabelle, zu lange Texte mit „…" gekürzt (`Fit` aus DocLibs);
     Logo oben rechts; Verlaufslinie über die Satzspiegelbreite.
   - **Fußzeile**: Verlaufslinie, darunter drei gleiche Spalten (Quer: plus schmale leere vierte)
     in 6,5 pt — links Firma fett PTA-Blau, Mitte „Stand: TT.MM.JJJJ", rechts „Seite **n** | m"
     mit fetter Seitenzahl in PTA-Blau.
   - **Erste Seite** der Varianten mit Deckblatt: nur Logo und Linie (Quer: Linie bei 6,00 cm),
     keine Fußzeile — wie die erste Kopfzeile der Vorlage.
3. **Verlaufslinie** als lineare Schattierung (reportlab `linearGradient`) PTA-Blau →
   Hellblau bei 53 % → Weiß. Das transparente Ende wird gegen Weiß gemischt, weil die Seite weiß
   ist; das sieht gleich aus und braucht keine Soft-Mask.
4. **Logo** aus E01-S04 (aus dem EMF der Vorlage gewandelt), an Ankerposition und -größe;
   eingebettet einmal und auf jeder Seite verwendet.
5. **Deckblatt** (`hoch`, `quer`): „Titel" 34 pt fett PTA-Blau, „Untertitel" 22 pt, „Autor"
   14 pt mit „Autor, Ort, Datum" (Datum nur, wenn angegeben) — im Fluss ab dem oberen Rand, mit
   den Abständen der Formatvorlagen (E05-S02, Schritt 1), danach Seitenwechsel. Ohne `titel` in
   einer Variante mit Deckblatt derselbe Fehler wie im DOCX.
6. **Inhaltsverzeichnis** (`inhaltsverzeichnis: ja`): nach dem Deckblatt „Inhalt" in
   „Zwischenüberschrift", Einträge der Ebenen 1 und 2 (wie `TOC \o "1-2"`) in „Verzeichnis 1/2"
   mit Nummer, Text, Seitenzahl rechts (Ebene 2 mit Punkt-Füllzeichen) und Link auf die
   Überschrift; danach Seitenwechsel. Weil das Verzeichnis selbst Seiten belegt, läuft das Layout
   zweimal: erst zum Zählen der Verzeichnisseiten, dann endgültig.
7. Metadaten: Titel, Betreff (= Untertitel), Autor in Info-Dictionary und XMP (E05-S01).
8. Tests `tests/generation/pdf/test_frame.py` für alle vier Varianten: Seitengröße und
   Ausrichtung, Logo- und Linienposition, Kopfzeilentext ab Seite 2, Fußzeilentexte „PTA
   IT-Beratung", „Stand: 06.11.2026", „Seite 2 | 3" (pdfplumber), keine Fußzeile auf dem
   Deckblatt, `firma`, `sprache: en`, Verzeichnis mit richtigen Seitenzahlen und Links.
   Dateien nach `.tmp/review/frame-<variante>.pdf`.

## Akzeptanzkriterien

- [x] Jede Variante hat das Seitenformat, den Satzspiegel, die Kopf- und Fußzeile der
      zugehörigen Word-Vorlage; die Werte werden aus der Vorlage gelesen.
- [ ] Neben ein aus Word exportiertes DOCX derselben Variante gelegt, stimmen Logo, Linien,
      Kopf- und Fußzeile in Lage, Größe, Schrift und Farbe überein (Prüfpunkt für den Menschen).
- [x] Varianten mit Deckblatt haben auf Seite 1 nur Logo und Linie und keine Fußzeile.
- [x] „Seite n | m" zählt alle Seiten, das Deckblatt eingeschlossen, wie Word.
- [x] Das Inhaltsverzeichnis nennt die richtigen Seiten und verlinkt sie.

## Offene Fragen

1. Logo im PDF: als Vektor (aus dem EMF gewandelte Pfade, scharf in jedem Zoom) oder als
   hochaufgelöstes PNG (≥ 600 dpi)? Vorschlag: Vektor, wenn E01-S04 ein sauberes SVG liefert.

> (2026-11-07) Vektor.

## Notizen

- Abhängig von E05-S02 (Layout, Formatvorlagen-Leser) und E01-S04 (Logo).
- Die Seitenzählung „Seite n | m" entspricht den Word-Feldern `PAGE`/`NUMPAGES`; Word zählt das
  Deckblatt mit.

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08 (Worktree auf Basis des Claim-Commits `acffc50`; ein
vorheriger Lauf war mitten in der Arbeit abgebrochen, seine Änderungen an `design/word.py`,
`design/word_styles.py` und `generation/docx/generator.py` wurden geprüft und übernommen —
`COMPANY_PLACEHOLDER`, `WordDesign.paragraph_ids`, `color_of`, `is_on` —, nur das Umbenennen von
`_page` in `page_setup` wurde zurückgenommen, weil nichts es braucht).

Neu: `src/pta_documents/design/word_frame.py` (`read`, `PageFrame`, `PageKind`, `Band`,
`FrameTable`/`FrameRow`/`FrameCell`/`FrameParagraph`, `FrameField`, `Box`, `FrameRule`,
`GradientStop`, `body_top`, `band_height`, `row_height`, `header_top`, `footer_bottom`) und
`src/pta_documents/generation/pdf/frame.py` (`FrameInfo`, `lay_out`, `front_matter`, `cover`,
`contents`, `ContentsEntry`, `PageDecorator`, `fit`). Geändert: `generation/pdf/generator.py`
(ruft `frame.lay_out` mit `FrameInfo` aus Front Matter und Metadaten), `generation/pdf/options.py`
(Docstrings), `generation/pdf/layout/document.py` (`render(…, first_top_pt)` mit eigener erster
`PageTemplate`, `RenderedPdf.heading_pages` aus `afterFlowable`), `layout/flowables.py`
(`Outline.heading/number/text/anchor`), `layout/story.py` (füllt sie), `layout/__init__.py`
(Docstring). Tests: `tests/design/test_word_frame.py` (28), `tests/generation/pdf/test_frame.py`
(33, alle vier Varianten; Ansicht `.tmp/review/frame-<variante>.pdf`),
`tests/generation/pdf/support.py` (`type_area`, `body_texts`: Text des Satzspiegels ohne Kopf
und Fuß); `test_generator.py` und `test_pdfa.py` lesen jetzt nur den Satzspiegel, der Test
„Text kommt zurück" prüft zusätzlich das Deckblatt. Doku: `docs/verwendung.md` (neuer Abschnitt
„PTA-Seitenrahmen im PDF (E05-S03)", Stand, Front Matter, Aufbau, Layout-Engine),
`docs/anleitung.md`, `ai/Gedächtnis.md` (neuer Eintrag, PDF-Generator und Überblick
korrigiert). Keine neue Abhängigkeit.

### Entscheidungen

- **Alles aus der Vorlage** (Punkt 1): Logo, Linien, Kopf- und Fußzeilentabelle, Zellbreiten,
  Ausrichtung, Schriftgröße, fett, Farbe, Zeilenabstand und Abstände liest `word_frame` aus den
  Kopf-/Fußzeilenteilen, die der letzte `w:sectPr` referenziert (`default`, und `first` nur mit
  `w:titlePg`). Welches Feld ein Absatz ist, verrät der Platzhaltertext der Vorlage. Senkrecht
  rechnet der Rahmen wie Word: die Kopfzeile beginnt im Kopfzeilenabstand und fließt nach unten,
  die Fußzeile endet im Fußzeilenabstand über dem Seitenrand; Zeilen mit „genau"-Höhe
  zentrieren ihren Inhalt (`w:vAlign`). Text sitzt am Fuß seiner Zeile (die zusätzliche Höhe von
  „mindestens" liegt darüber).
- **Linie** als mit einem Rechteck in Strichbreite (0,5 pt aus `lnStyleLst`) geclippte axiale
  Schattierung; das transparente Ende wird gegen Weiß gemischt (Plan Punkt 3).
- **Logo** als Vektor (Antwort auf Frage 1) aus `design.logos.shapes(Logo.WORD)`, einmal als
  Form-XObject `PTALogo` eingebettet und auf jeder Seite per `doForm` gezeichnet.
- **Zwei und mehr Durchgänge:** `lay_out` rendert, bis Seitenzahl und Seiten der Überschriften
  sich nicht mehr ändern (meist zwei Durchgänge, höchstens `MAX_PASSES` = 4). Die Seitenzahlen
  des Verzeichnisses haben eine feste Spalte (Breite „0000"), damit sie den Umbruch nicht
  ändern. Hinweise werden in jedem Durchgang in denselben `Notes`-Sammler geschrieben, der
  doppelte Einträge verwirft.
- **„Stand:"** ist `datum`, sonst der Tag von `PdfOptions.created`, sonst heute — so bleiben
  Dateien mit gleichem `created` byte-gleich (Word schreibt den Tag der Erzeugung).
- **Kopfzeile ohne Untertitel:** der Untertitel-Absatz fällt weg (wie der DOCX-Generator ihn
  löscht), der Titel steht allein mittig. Ein leerer Titel (Vorlage ohne Deckblatt, kein `titel`)
  lässt den Absatz leer stehen, wie im DOCX.
- **Inhaltsverzeichnis** aus `Story.outline` (Überschrift 1 und 2 mit Anker), Seiten aus
  `afterFlowable` des Dokuments; Einträge als eigenes Flowable `ContentsEntry` (Nummer im
  hängenden Einzug von „Verzeichnis 1/2", Text als Absatz, Seitenzahl rechts auf der letzten
  Zeile, Punkte bei Ebene 2, ein Link über den ganzen Eintrag). Ohne Deckblatt steht das
  Verzeichnis am Anfang, wie im DOCX.
- Metadaten (Punkt 7): Titel, Betreff = Untertitel und Autor waren schon im Info-Dictionary und
  XMP (E05-S01); unverändert.

### Abweichungen

- **Deckblatt nicht ab dem oberen Rand** (Plan Punkt 5): die erste Kopfzeile von `hoch`/`quer`
  ist ein leerer Absatz mit 200/150 pt Abstand danach, und Word beginnt den Text darunter. Damit
  das PDF neben dem Word-Export gleich aussieht (Akzeptanzkriterium 2), beginnt das Deckblatt bei
  `word_frame.body_top` (`hoch` 8,50 cm, `quer` 6,79 cm, unter der Linie bei 6,00 cm).
- **Fußzeile Quer:** die Vorlage hat drei gleiche Spalten (6,99 cm) und eine schmale vierte
  (4,34 cm); die dritte ist leer, „Seite n | m" steht rechtsbündig in der vierten — nicht „drei
  Spalten plus leere vierte" wie im Plan. In Quer steht „Stand:" links in seiner Spalte, in Hoch
  mittig. Gezeichnet wird, was die Vorlage sagt.
- **„Seite n | m"** ist in der Vorlage als Ganzes fett in PTA-Blau (nicht nur die Seitenzahl);
  so übernommen.
- Das Layout läuft bis zur Stabilität statt fest zweimal (Plan Punkt 6).
- Test-Dateiname wie geplant (`tests/generation/pdf/test_frame.py`); zusätzlich
  `tests/design/test_word_frame.py` für die gelesenen Werte.

### Warnungen

- **veraPDF** ist hier nicht installiert: dass Schattierung und Form-XObject PDF/A-2b-konform
  sind, prüfen nur die pikepdf-Tests (Struktur, Schriften, OutputIntent). Erwartet wird kein
  Problem (DeviceRGB mit sRGB-OutputIntent, keine Transparenz), aber ein veraPDF-Lauf steht aus.
- **Fehlende Zeichen in Titel, Untertitel, Firma** werden in Kopf-/Fußzeile und Deckblatt `?`,
  aber ohne Hinweis `character-missing` — `Notes.characters` prüft nur den Rumpf. Vorsichtig
  gelassen, weil die Zeilennummer eines Front-Matter-Werts nicht aus `Notes.characters` kommt.
- **DOCX, Querformat:** der Kopfzeilenabsatz des Untertitels enthält in der Vorlage nach einem
  Zeilenumbruch den Mustertext „Gerne auch zweizeilig möglich"; der DOCX-Generator (E03-S01)
  ersetzt nur den Platzhalter und lässt den Mustertext stehen. Das PDF zeigt ihn nicht. Nicht
  hier behoben (Code einer anderen Story), siehe Offene Punkte.
- **Verzeichnis Ebene 1 ohne Punkte** nach dem Plan; Word setzt beim Aktualisieren des Feldes
  womöglich auch auf Ebene 1 Punkte (die Vorlage definiert den Tabstopp nur in „Verzeichnis 2").
- Die Grundlinien in Kopf- und Fußzeile sind nachgerechnet (Zeilenhöhe nach Word, Unterlänge aus
  reportlabs Schriftmetrik), nicht gemessen — ein Abgleich mit einem Word-Export steht aus.

### Prüfpunkte

- `./run.sh test tests/generation/pdf tests/design/test_word_frame.py`, dann
  `.tmp/review/frame-hoch.pdf`, `frame-hoch-ohne-deckblatt.pdf`, `frame-quer.pdf`,
  `frame-quer-ohne-deckblatt.pdf` neben ein aus Word exportiertes DOCX derselben Variante legen:
  Logo, Linien (Lage, Länge, Verlauf), Kopfzeile (Titel fett blau, Untertitel, „…"), Fußzeile
  (Firma, Stand, Seite), Deckblatt (Lage des Titels), Inhaltsverzeichnis (Einzüge, Punkte,
  Seitenzahlen, Klick springt zur Überschrift).
- `.tmp/review/pdf-gsb-bericht.pdf` (Beispiel mit Deckblatt und Verzeichnis) und
  `pdf-varianten-querformat-dokument.pdf`.

### Offene Punkte

- **E12-S03** (Kennzeichnung „Vertraulich"/„Entwurf"): nicht Teil dieser Story — E12-S03 ist
  noch `Entwurf`, der Schlüssel `kennzeichnung` existiert nicht, und der PDF-Teil gehört laut
  ihrem Plan zu E12-S03 selbst („Abhängigkeiten: … E05-S03 für den PDF-Teil"). Ansatzpunkt:
  `PageDecorator` (Text neben dem Logo) und für das Wasserzeichen ein Hook am **Anfang** der
  Seite (`onPage`), weil `decorate` am Seitenende über dem Inhalt zeichnet.
- DOCX-Mustertext „Gerne auch zweizeilig möglich" im Querformat (siehe Warnung) — eigene
  Korrektur in `fill_headers_and_footers`.
- Eine Fußzeile, die über den unteren Rand hinausreicht, schiebt den Text in Word nach oben;
  das modelliert `word_frame` nicht (die Vorlagen brauchen es nicht: 19 pt < unterer Rand).
- Silbentrennung, `replace_unsupported`, Grafiken: E05-S04 bzw. Warnung aus E05-S02. —
  *(2026-11-08) `replace_unsupported` (auch für Deckblatt, Kopf- und Fußzeile) und Grafiken
  erledigt in E05-S04; Silbentrennung bleibt offen.*
