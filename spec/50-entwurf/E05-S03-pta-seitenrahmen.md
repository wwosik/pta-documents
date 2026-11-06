# E05-S03 PTA-Seitenrahmen

> Status: Entwurf
> Epic: [E05 PDF-Generator im PTA-Design](E05-pdf-generator.md)

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

- [ ] Jede Variante hat das Seitenformat, den Satzspiegel, die Kopf- und Fußzeile der
      zugehörigen Word-Vorlage; die Werte werden aus der Vorlage gelesen.
- [ ] Neben ein aus Word exportiertes DOCX derselben Variante gelegt, stimmen Logo, Linien,
      Kopf- und Fußzeile in Lage, Größe, Schrift und Farbe überein (Prüfpunkt für den Menschen).
- [ ] Varianten mit Deckblatt haben auf Seite 1 nur Logo und Linie und keine Fußzeile.
- [ ] „Seite n | m" zählt alle Seiten, das Deckblatt eingeschlossen, wie Word.
- [ ] Das Inhaltsverzeichnis nennt die richtigen Seiten und verlinkt sie.

## Offene Fragen

1. Logo im PDF: als Vektor (aus dem EMF gewandelte Pfade, scharf in jedem Zoom) oder als
   hochaufgelöstes PNG (≥ 600 dpi)? Vorschlag: Vektor, wenn E01-S04 ein sauberes SVG liefert.

>

## Notizen

- Abhängig von E05-S02 (Layout, Formatvorlagen-Leser) und E01-S04 (Logo).
- Die Seitenzählung „Seite n | m" entspricht den Word-Feldern `PAGE`/`NUMPAGES`; Word zählt das
  Deckblatt mit.
