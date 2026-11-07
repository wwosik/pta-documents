# E03-S03 Folien-Syntax in Word

> Status: in Prüfung
> Epic: [E03 DOCX-Generator auf den PTA-Word-Vorlagen](../50-entwurf/E03-docx-generator.md)
> Milestone: [M02 Rückmeldung und Folien-Syntax](../50-entwurf/M02-rueckmeldung-und-folien-syntax.md)

## Zusammenfassung

Markdown, das für Folien geschrieben ist (Container, Alerts, `==Markierung==`, farbige Wörter,
Status-Labels, Bildreihen), ergibt auch ein ordentliches PTA-Word-Dokument: schlicht dargestellt
wie im PDF von DocLibs, aber über Formatvorlagen statt Direktformatierung.

## Kontext

- DocLibs zeigt Folien-Syntax im PDF „plainly" (`docs/…Pdf.md`, Abschnitt *Slide layouts*):
  Heading-Attribute geprüft und verworfen, Container zeigen ihren Inhalt als normale Blöcke,
  Alerts sind Zitate mit fetter Art am Anfang, `==x==` fett, Tags und Labels bleiben Code,
  `[Wörter]{.success}` fett in der Statusfarbe, Bildreihen nebeneinander.
- Lesen und Prüfen kommt aus E02-S02 (`layout_syntax`, `heading_attributes`, `coloured_words`,
  `layout_tokens`); `status.<kategorie>` ist im DOCX-Front-Matter schon erlaubt (E03-S01).
- `generation/docx/writer.py` (`BodyWriter`, 793 Zeilen) überspringt unbekannte Token; mehrere
  Bilder in einem Absatz werden heute untereinander gesetzt. Akzeptanz E03-S02: keine
  Direktformatierung von Schrift, Größe, Farbe außer Code — daran hält sich diese Story.

## Vorgeschlagener Ansatz

1. **Heading-Attribute:** geprüft (E02-S02) und entfernt; `kicker`, `.dark`, `layout`,
   `.closing` haben in Word keine Wirkung. `#` bleibt „Überschrift 1".
2. **Container** (`cards`, `rows`, `panel`, `statement`, `columns` und die PTA-Ergänzungen aus
   E04-S03): Inhalt als normale Blöcke. Abweichend vom PDF in DocLibs wird ein `###` in
   `::: cards` **nicht** „Überschrift 3" (sonst Nummer und Verzeichniseintrag je Karte), sondern
   `Standard fett`, ebenso eine Kennzahl `**26 Tabellen**`; `::: columns` setzt die Teile
   nacheinander, die `---` dazwischen entfallen; der erste Absatz von `::: statement` wird
   `Standard fett`; Fazit-Box und Kommentarbox werden Hinweise wie in Schritt 3.
3. **Alerts:** zwei neue Absatzvorlagen, angelegt wie `Code`/`Zitat` (E03-S02), auf Basis von
   `Standard`: `Hinweis` (linke Linie 3 pt PTA-Blau, Fläche `E6E6E6`) für `NOTE`/`TIP` und
   `Hinweis wichtig` (linke Linie 3 pt Gelb `FDDC35`, Fläche `E6E6E6`) für `IMPORTANT`,
   `WARNING`, `CAUTION`. Der erste Absatz beginnt mit der Art in Fett: „Hinweis", „Tipp",
   „Wichtig", „Warnung", „Vorsicht" bzw. mit `sprache: en` „Note", „Tip", „Important",
   „Warning", „Caution" (neu in `design.variants.GeneratedTexts`).
4. **`==Markierung==`:** neue Zeichenvorlage `Markierung` mit Zeichenschattierung `FDDC35` (exakt
   PTA-Gelb; Words Textmarker kennt nur `FFFF00`). Eine Tabellenzeile, deren erste Zelle ganz
   markiert ist, bekommt die Zellschattierung `FDDC35` — Tabellenzellen sind Direktformat am
   Tabellenobjekt, nicht am Text.
5. **Farbige Wörter** `[Wörter]{.success}`: fünf Zeichenvorlagen „Status Erfolg", „Status
   Warnung", „Status Gefahr", „Status Info", „Status Neutral" (fett, Farbe aus
   `design.colors.STATUS_COLORS`), über `coloured_words.apply` auf die Runs eines Absatzes.
6. **Status-Labels:** Eine Tabellenzelle aus genau einem Code-Span, dessen Text im Front Matter
   einer Kategorie zugeordnet ist, wird in der Status-Zeichenvorlage dieser Kategorie gesetzt
   (ohne Consolas); nicht zugeordnete Code-Zellen bleiben Code — anders als auf Folien, wo sie
   neutral werden, weil Word keine „Flow-Folie" kennt. Tags (Absatz aus Code-Spans) bleiben Code.
7. **Bildreihen:** ein Absatz aus ≥ 2 Bildern wird eine rahmenlose Tabelle über die
   Satzspiegelbreite mit gleich breiten Zellen (mehr als vier → weitere Zeilen, wie
   `MAX_PICTURES_PER_ROW` der Folien); jedes Bild auf seine Zelle verkleinert, darunter in der
   Zelle „Abbildung n: …" nach der Regel von E03-S02 (Titel, sonst Alt-Text). Die Tabelle nutzt
   eine neue Tabellenvorlage `Bildreihe` ohne Linien statt `PTA` und hält ihre Zeilen zusammen.
8. **Konverter (E07-S02):** liest die neuen Vorlagen wie `Standard`, damit die Rundreise stabil
   bleibt; `Hinweis …` wird wieder ein Zitat.
9. **Tests:** `layouts.md` (deutsch, aus E02-S02) → DOCX in `hoch` und `quer`, Rundreise gegen
   `layouts-hoch.roundtrip.expected.md`; Stilprüfung je Block (welche Vorlage); keine
   Direktformatierung von Schrift/Größe/Farbe in Runs; Bildreihe mit 2 und 5 Bildern;
   `sprache: en` für die Alert-Wörter. Ergebnis zum Ansehen nach `.tmp/review/layouts-hoch.docx`.

## Akzeptanzkriterien

- [x] Das Folienbeispiel `layouts.md` ergibt ein DOCX ohne Fehler, das Word ohne Reparatur öffnet.
- [x] Alerts, Markierungen, farbige Wörter und Status-Labels stehen in eigenen Formatvorlagen;
      in den Runs gibt es weiterhin keine direkte Schrift-, Größen- oder Farbangabe außer Code.
- [x] Mehrere Bilder in einem Absatz stehen nebeneinander, jedes mit seiner Beschriftung.
- [x] Fehler in der Folien-Syntax melden dasselbe wie im PPTX (E02-S02).

## Offene Fragen

1. Sollen `::: cards` und `::: columns` in Word **nebeneinander** stehen (rahmenlose Tabelle wie
   bei Bildreihen), oder nacheinander wie im PDF von DocLibs (Vorschlag; liest sich in Word
   besser und bleibt einfach zu bearbeiten)?

> (2026-11-07) Nacheinander.

## Notizen

- (2026-11-07, E04-S04) `{.agenda}`, `{.interim}`, `{.quote}`, `{.contact}` sind registriert
  (`HeadingAttributes.kind`); Word entfernt sie heute nur und zeigt Überschrift und Inhalt
  normal (eine Agenda ohne Liste bleibt in Word leer).

## Implementierungsnotizen

- **Umgesetzt** in `generation/docx/writer.py` (`layout_container`, `note_box`, `slide_kind`,
  `chapters`, `picture_row`, Zeichenvorlagen in `_run`, Status-Labels und markierte Zeilen in
  `table_block`), Namen und Maße in `design/word.py` (`STYLES.note`, `note_important`, `mark`,
  `picture_row`, `status`; `NOTE`, `NOTE_IMPORTANT`, `MARK_COLOR`, `PICTURES_PER_ROW` =
  `slides.MAX_PICTURES_PER_ROW`, `PICTURE_GAP_CM`, `CONTACT_PHOTO_CM`, `TABLE_BASE_STYLE`),
  Wörter in `design.variants.GeneratedTexts` (`note` … `caution`, `conclusion`, `comment`,
  `alert(kind)`), Rückweg in `conversions/docx.py` (`NOTE_STYLES`, `_note`,
  `_render_picture_row`).
- Tests: `tests/generation/docx/test_layouts.py` (Rundreise `layouts.md` hoch und quer gegen
  `layouts-hoch/quer.roundtrip.expected.md`, Vorlage je Block, keine Direktformatierung,
  Vorlagen-XML, markierte Zeile, Status-Labels, englische Alert-Wörter, Bildreihe mit 2 und 5
  Bildern, Folienarten). Zum Ansehen: `.tmp/review/layouts-hoch.docx`, `layouts-quer.docx`,
  `bildreihe-2.docx`, `bildreihe-5.docx`.
- `test_layout_syntax.docx_runs` zählt jetzt auch Fett aus der Zeichenvorlage (farbige Wörter
  sind nicht mehr direkt fett) — keine Abschwächung, die Prüfung „fett" bleibt.
- Alerts: die Art steht fett mit Doppelpunkt am Anfang („**Hinweis:** …"); Listen, Code und
  Tabellen in einem Alert behalten ihre eigene Vorlage (nur Absätze werden „Hinweis").
- Der Konverter macht aus „Hinweis …" wieder `> [!KIND]`, wenn der Absatz mit einem Alert-Wort
  beginnt; Fazit- und Kommentarbox werden schlichte Zitate (`> **Fazit:** …`), mehrere Absätze
  eines Alerts getrennte Zitate. Status- und Markierungsvorlagen werden als Text gelesen.
- **Warnung:** Nicht nur in `::: cards`, sondern in **jedem** Container werden Überschriften
  „Standard fett" (Begründung der Story gilt ebenso, z. B. `### …` in `::: panel dark`).
- **Warnung:** Die Folienarten (in der Story nur als Notiz offen) habe ich so gelöst: `{.agenda}`
  bleibt „Überschrift 2" mit der Liste; ohne Liste werden die **folgenden** `#`-Kapitel (ohne
  `{.closing}`) eine nummerierte Liste (in PowerPoint alle Kapitel nach dem Titel — Word hat
  keinen Titel-`#`); keine Kapitel → nichts, kein Fehler. `{.interim}` → „Standard fett" (keine
  Überschrift, kein Verzeichniseintrag). `{.quote}` → Zitat und Quelle als „Zitat".
  `{.contact}` → „Überschrift 2", `###` je Person „Standard fett", Foto ohne Beschriftung
  höchstens 3 cm breit, Zeilenumbrüche bleiben Umbrüche, E-Mail ohne Link.
- **Warnung:** Die Aufbaufehler der Folien (Agenda > 8 Punkte, Inhalt unter `{.interim}`,
  Fazit-Box zu lang, Karte ohne `###` …) meldet weiterhin nur PowerPoint; Word meldet genau die
  Fehler von `layout_syntax.check` (Akzeptanzkriterium 4, E02-S02).
- Bildreihe: Bilder links in der Zelle, Zellen mit den Standard-Zellrändern von „Normal Table",
  `cantSplit` je Zeile und „Absatz nicht vom nächsten trennen" für alle Absätze außer der
  letzten Zeile. Ein einzelnes Bild bleibt eine Abbildung wie bisher.
- Hinweis-Vorlagen: Linie `w:sz=24` (3 pt), Abstand 6 pt, Einzug links 6 pt, Fläche
  `GREY_LIGHT`; aufeinanderfolgende Absätze bilden in Word einen Kasten.
- **Prüfpunkte:** `.tmp/review/layouts-hoch.docx` in Word öffnen (keine Reparaturmeldung —
  auf der Entwicklungsmaschine gibt es kein Word/LibreOffice); Aussehen von Hinweis-Linie und
  Fläche, Bildreihe, Markierung in Tabellenzellen (Zellschattierung plus Zeichenschattierung,
  gleiche Farbe).
- PDF: die Story betrifft nur Word; die schlichte PDF-Darstellung bleibt E05-S04.
