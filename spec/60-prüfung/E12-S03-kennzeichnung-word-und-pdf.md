# E12-S03 Kennzeichnung „Vertraulich" und „Entwurf" in Word und PDF

> Status: in Prüfung
> Epic: [E12 Dokumentpflege: Historie, Vergleich, Kennzeichnung](../50-entwurf/E12-dokumentpflege.md)
> Milestone: [M04 Präsentieren und Schulung](../50-entwurf/M04-praesentieren-und-schulung.md)

## Zusammenfassung

Front Matter `kennzeichnung: vertraulich | intern | entwurf | kein` setzt in Word und PDF eine
Kennzeichnung in die Kopfzeile — „Vertraulich" oder „Für den internen Gebrauch" in PTA-Blau neben
dem Logo — und bei `entwurf` zusätzlich ein Wasserzeichen „ENTWURF" über jede Seite. In
PowerPoint entspricht das dem Sticker aus E04-S05; beide sollen über denselben Schlüssel laufen.

## Kontext

- E04-S05 plant für Folien `sticker: vertraulich | intern | kein` nach dem Muster der
  Schulungsvorlage („Für den internen Gebrauch", „VERTRAULICH"). Für Word gibt es in den
  Vorlagen kein Muster; die Designanalyse zeigt Kopfzeile mit Logo oben rechts (2,22 × 1,28 cm,
  Hochformat) und Verlaufslinie darunter, Varianten mit Deckblatt haben eine eigene erste
  Kopfzeile.
- Der DOCX-Writer übernimmt Kopf- und Fußzeilen der Vorlage und ersetzt nur Texte (`firma`,
  Datum; E03-S01). Eine Kennzeichnung ist ein weiterer Absatz in der Kopfzeile oder eine Form.
- Ein Word-Wasserzeichen ist technisch ein WordArt-Shape (`v:shape` mit `v:textpath`, Stil
  `mso-position-horizontal:center`, Drehung −45°, hellgraue Füllung, `o:allowincell="f"`) im
  Kopfzeilenteil; Word zeigt es hinter dem Text jeder Seite des Abschnitts.
- Im PDF (E05-S03) zeichnet die Layout-Engine Kopf- und Fußzeile selbst; Text und Wasserzeichen
  sind dort gewöhnliche Zeichenbefehle (reportlab `saveState/rotate/setFillAlpha`).
- Texte folgen `sprache` (`GeneratedTexts`, E01-S01): „Vertraulich"/„Confidential", „Für den
  internen Gebrauch"/„For internal use only", „Entwurf"/„Draft".

## Vorgeschlagener Ansatz

1. **Schlüssel:** `kennzeichnung` in `front_matter.Keys`, Werte `vertraulich`, `intern`,
   `entwurf`, `kein`; `Marking` als `StrEnum` in `design/variants.py`, verwendet von
   `DocxOptions.marking`, `PdfOptions.marking` und — statt `sticker` — `PptxOptions.marking`
   (Frage 1). Standard: Word/PDF `kein`; PPTX wie E04-S05 (`schulung` → `intern`).
2. **Word, Text in der Kopfzeile** (`generation/docx/writer.py`, `_marking(header)`): ein
   rechtsbündiger Absatz unter dem Logo in jeder Kopfzeile des Dokuments (erste Seite
   eingeschlossen), Formatvorlage „Kopfzeile" der Vorlage, 9 pt, Versalien, PTA-Blau `006FB9`
   über die Theme-Farbe (`w:color w:themeColor="accent1"`), kein Hex. Maß und Abstand im
   Designmodell (`design/word.py`, `MARKING_AREA`), geprüft im Vergleichstest mit der Vorlage
   (E01-S01). Auf dem Deckblatt steht die Kennzeichnung zusätzlich unter der Zeile „Autor, Ort,
   Datum" (E03-S01), damit ein ausgedrucktes Deckblatt sie zeigt.
3. **Word, Wasserzeichen** bei `entwurf`: ein `v:shape` „PowerPlusWaterMarkObject" in jeder
   Kopfzeile — Text „ENTWURF"/„DRAFT", Segoe UI, Füllung `AFAFAF` (Akzent 5 der Palette) mit 50 %
   Deckkraft, diagonal, so groß wie die Diagonale des Satzspiegels zulässt. Das Markup ist fest
   als Vorlage in `design/word.py` hinterlegt (VML, von Word 365 getestet) und wird nur mit Text
   gefüllt. `entwurf` setzt außerdem den Text „Entwurf" nach Schritt 2.
4. **PDF** (E05-S03): die Layout-Engine zeichnet denselben Text an derselben Stelle und das
   Wasserzeichen als gedrehten Text mit 50 % Alpha hinter dem Inhalt; die PDF/A-2b-Prüfung
   (veraPDF) bleibt grün (Transparenz ist in PDF/A-2 erlaubt).
5. **PowerPoint:** E04-S05 schreibt den Sticker; hier nur die Umstellung auf den gemeinsamen
   Schlüssel und der neue Wert `entwurf` (Sticker „ENTWURF"/„DRAFT" im selben Muster) — mit
   dem Hinweis im Authoring Guide, dass ein Entwurfs-Deck beim Kunden den Sticker trägt.
6. **Tests** `tests/generation/docx/test_marking.py`: Text in allen Kopfzeilen und auf dem
   Deckblatt, Wasserzeichen nur bei `entwurf`, englische Texte, `kein` ändert nichts an der
   Vorlage (Byte-Vergleich der Kopfzeilenteile), Rundreise unverändert (E07-S02 liest Kopfzeilen
   nicht). `docs/anleitung.md`, `docs/ki-anleitung.md` und `samples/funktionen/varianten-dokument.md`
   zeigen `kennzeichnung`.

## Akzeptanzkriterien

- [x] `kennzeichnung: vertraulich` zeigt „VERTRAULICH" in PTA-Blau in der Kopfzeile jeder Seite
      und auf dem Deckblatt; `entwurf` zusätzlich das Wasserzeichen; `kein` lässt die Vorlage
      unverändert.
- [x] Texte folgen `sprache`; Farbe über Theme-Farbe, kein Hex.
- [ ] Word öffnet das Dokument ohne Reparatur; das Wasserzeichen steht hinter dem Text und lässt
      sich in Word über *Entwurf → Wasserzeichen entfernen* löschen (Prüfpunkt Mensch).
- [x] Derselbe Schlüssel wirkt in PowerPoint als Sticker (nach E04-S05).

## Offene Fragen

1. Ein gemeinsamer Schlüssel `kennzeichnung` für alle Formate (Vorschlag; E04-S05 wird dann
   angepasst, `sticker` entfällt) — oder `sticker` für Folien behalten, weil die PTA den
   Begriff so verwendet?

> (2026-11-07) Gemeinsamer Schlüssel `kennzeichnung` für alle Formate; E04-S05 ist angepasst,
> `sticker` entfällt.

2. Wasserzeichen auch für `vertraulich` (groß über die Seite) oder nur der Text in der
   Kopfzeile? Vorschlag: nur Text — ein Wasserzeichen „VERTRAULICH" stört beim Lesen eines
   fertigen Dokuments, „ENTWURF" soll stören.

> (2026-11-07) Nur Text in der Kopfzeile; Wasserzeichen nur für `entwurf`.

## Notizen

- Abhängigkeiten: E04-S05 (Sticker), E05-S03 (PDF-Seitenrahmen) für den PDF-Teil.

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08 im Haupt-Checkout (parallel arbeitet ein anderer Lauf
desselben Agents an E09-S02 im Worktree; keine gemeinsamen Dateien außer Doku und Gedächtnis,
dort nur ergänzt). Neu: `generation/docx/marking.py` (`apply`, `cover_paragraph`, `text_box`,
`watermark`, `watermarks`), `design.word.MARKING` (`MarkingStyle`), `WATERMARK`
(`WatermarkStyle`), `watermark_size`, `WATERMARK_SHAPETYPE`, `WATERMARK_SHAPE`,
`WordStyles.header`, `design.word_frame.marking_area`, `generation/pdf/frame.Watermark`.
Geändert: DOCX `generator.py` (Schlüssel, Deckblatt-Zeile vor dem Seitenwechsel, `apply` nach
`fill_headers_and_footers`), `options.py` (`marking`); PDF `generator.py`, `options.py`
(`marking`), `frame.py` (`FrameInfo.marking`, `PageDecorator._marking`, Deckblatt-Zeile,
`underlay`), `layout/document.py` (`render(…, underlay)`, `onPage`-Hook). Tests:
`tests/generation/docx/test_marking.py` (30), `tests/generation/pdf/test_marking.py` (19),
`tests/design/test_word_frame.py` (+5). Beispiele: `varianten-dokument.md` (`entwurf`,
englisch), `varianten-querformat-dokument.md` (`vertraulich`, Deckblatt), README und
Rundreise-Erwartungen. Doku: `docs/verwendung.md` (Abschnitt „Kennzeichnung in Word und PDF
(E12-S03)", Tabellen, `underlay`), `docs/anleitung.md`, `docs/ki-anleitung.md`;
`ai/Gedächtnis.md`; M04-Notiz zum PDF-Teil korrigiert. Keine neue Abhängigkeit.

### Entscheidungen

- **Schritt 1 und 5 waren mit E04-S05 schon erledigt** (`Keys.MARKING`, `Marking`,
  `PptxOptions.marking`, Sticker `entwurf`, Texte in `GeneratedTexts`). Hier kamen nur Word und
  PDF dazu; Standard dort `kein`. Der Hinweis „ein Entwurf beim Kunden trägt die Kennzeichnung"
  steht in `docs/anleitung.md` und `docs/ki-anleitung.md`.
- **Lage:** rechtsbündig auf dem Satzspiegel, 3 pt unter der Verlaufslinie der Kopfzeile, also
  unter dem Logo (Hoch 2,91 cm, Quer 3,51 cm von oben, Höhe eine Zeile „Kopfzeile" = 14 pt, endet
  über dem Satzspiegel). Zwischen Logo und Linie ist im Hochformat nur 12 pt Platz, neben dem Logo
  reicht die Breite für „FÜR DEN INTERNEN GEBRAUCH" nicht. Die Lage wird aus der Vorlage
  berechnet (`marking_area`: Linie der „anderen" Seiten + `MARKING.gap_pt`), nicht als zweite
  Maßtabelle; der Test prüft gegen Logo, Linie und oberen Rand.
- **Auf dem Deckblatt** steht die Kopfzeilen-Kennzeichnung an derselben Stelle (unter dem Logo),
  auch im Querformat, dessen Deckblatt-Linie bei 6,00 cm liegt. Dazu der Absatz in „Autor"
  (14 pt), PTA-Blau, Versalien unter „Autor, Ort, Datum" — in Word und PDF.
- **Versalien** über `w:caps` (Word) bzw. `upper()` (PDF): „intern" erscheint als „FÜR DEN
  INTERNEN GEBRAUCH", der gespeicherte Text bleibt „Für den internen Gebrauch".
- **Farbe** `w:color w:val="006FB9" w:themeColor="accent1"`: `w:val` ist im Schema Pflicht, Word
  nimmt `themeColor` — genau so schreibt es die Vorlage selbst für den Titel der Kopfzeile.
- **Wasserzeichen-Größe:** Kasten Textbreite × eine Schriftgröße, um 45° gedreht so groß, dass er
  in die kürzere Seite des Satzspiegels passt (`watermark_size`; Hoch ≈ 541 × 125 pt, wie Words
  eigenes „ENTWURF"). Der Kern hat keine Schriftmaße: Word nimmt 0,62 Geviert je Großbuchstabe
  (Selawik 0,60–0,64), das PDF misst die echte Breite.
- **`kein`** ändert nichts (Kopfzeilenteile byte-gleich, getestet); ein unbekannter Wert nennt die
  gültigen Werte.

### Abweichungen

- **Textfeld statt Kopfzeilen-Absatz** (Plan Schritt 2: „ein rechtsbündiger Absatz unter dem
  Logo"): ein weiterer Absatz in der Kopfzeile macht sie eine Zeile höher — im Hochformat endet
  sie dann knapp am oberen Rand, und Word schiebt den Text nach unten, sobald sie darüber
  hinausreicht. Der Absatz steht deshalb in einem Textfeld ohne Ränder (`wps`, `wrapNone`, Name
  `PTA-Kennzeichnung`) im vorhandenen Absatz der Vorlage, der schon Logo und Linie trägt; der
  Absatz im Textfeld hat Formatvorlage „Kopfzeile", 9 pt, rechtsbündig wie geplant. Ebenso das
  Wasserzeichen: kein neuer Absatz.
- **`MARKING_AREA`** heißt `design.word.MARKING` (Stil und Abstände) plus
  `word_frame.marking_area` (Lage aus der Vorlage); es gibt keinen „Vergleichstest mit der
  Vorlage" im Sinne von E01-S01, weil keine Vorlage eine Kennzeichnung enthält — der Test prüft
  die Lage gegen Logo, Linie und Satzspiegel der Vorlage.
- **PDF ohne Alpha** (Plan Schritt 4: „gedrehter Text mit 50 % Alpha"): das Wasserzeichen liegt
  hinter dem Inhalt auf weißem Papier, Akzent 5 zu 50 % mit Weiß gemischt sieht gleich aus und
  vermeidet eine Transparenzgruppe in PDF/A (veraPDF ist hier nicht installiert, siehe Warnung).
  Ein Bild auf der Seite verdeckt das Wasserzeichen in beiden Fällen (es liegt dahinter, wie in
  Word).
- Die Deckblatt-Zeile kommt in der DOCX→Markdown-Rundreise als Absatz „VERTRAULICH" zurück
  (sie steht im Rumpf); die Kopfzeilen liest der Konverter nicht. Plan Schritt 6 sprach nur von
  den Kopfzeilen; die Rundreise ohne Deckblatt ist unverändert (getestet).

### Warnungen

- **Warnung:** Kein Word auf der Entwicklungsmaschine. Dass Word das Dokument ohne Reparatur
  öffnet, das Textfeld unter dem Logo und das Wasserzeichen hinter dem Text zeigt und
  *Wasserzeichen entfernen* es löscht, ist nicht geprüft. Das VML-Markup folgt dem, was Word 365
  für ein Text-Wasserzeichen schreibt (Formtyp 136, `PowerPlusWaterMarkObject…`,
  `mso-position-…-relative:margin`), ist aber nicht aus einer echten Word-Datei kopiert.
- **Warnung:** veraPDF ist nicht installiert; die PDF/A-Prüfung der neuen Inhalte beschränkt sich
  auf die pikepdf-Tests (keine Alpha-Werte, keine Soft-Mask im ExtGState).
- **Warnung:** Die Vorlagen enthalten selbst doppelte `wp:docPr`-Ids (Linie und Logo in
  verschiedenen Kopf-/Fußzeilen); die neuen Textfelder nehmen Ids oberhalb aller vorhandenen, die
  alten Doppelungen bleiben unverändert.
- In `hoch-ohne-deckblatt` stehen Textfeld und Wasserzeichen auch in den ungenutzten Kopfzeilen
  für gerade und erste Seiten (die Vorlage hat sie, aktiviert sie aber nicht). Schaltet jemand in
  Word „Erste Seite anders" ein, trägt auch diese Seite die Kennzeichnung — beabsichtigt.

### Prüfpunkte

- `.tmp/review/marking-entwurf.docx` (Hoch ohne Deckblatt) und `marking-vertraulich.docx` (Hoch
  mit Deckblatt), `.tmp/review/funktionen/varianten-dokument.docx` (Quer, englisch, Entwurf) und
  `varianten-querformat-dokument.docx` (Quer, vertraulich) in Word öffnen: keine Reparatur;
  Kennzeichnung unter dem Logo in PTA-Blau auf jeder Seite und auf dem Deckblatt; Wasserzeichen
  hinter dem Text, *Entwurf → Wasserzeichen → Wasserzeichen entfernen* löscht es; Text beginnt
  unverändert am oberen Rand.
- `.tmp/review/pdf-marking-<variante>-<wert>.pdf` neben den Word-Export legen: Lage und Größe
  von Kennzeichnung und Wasserzeichen.
- Ob die Lage unter der Linie (statt zwischen Logo und Linie) gefällt.

### Offene Punkte

- Ein Wasserzeichen, das über einem Bild liegen soll, gibt es nicht (Word und PDF: dahinter).
- Fehlende Zeichen in der Kennzeichnung (nur bei eigenen Texten denkbar) würden im PDF `?`, ohne
  Hinweis — wie Titel und Firma im Seitenrahmen (Warnung aus E05-S03). — *(2026-11-08) Erledigt in E05-S04.*
