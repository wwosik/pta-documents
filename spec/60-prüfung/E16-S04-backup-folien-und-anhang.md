# E16-S04 Backup-Folien und Anhang

> Status: in Prüfung
> Epic: [E16 Schulung und Zielgruppen](../50-entwurf/E16-schulung-und-zielgruppen.md)
> Milestone: [M04 Präsentieren und Schulung](../50-entwurf/M04-praesentieren-und-schulung.md)

## Zusammenfassung

`# Backup {.backup}` in einer Präsentation: alles danach steht **hinter** der Abschlussfolie, ohne
Kapitelnummer und ohne Agenda-Eintrag, eingeleitet von einer Trennfolie „Backup". In Word und PDF
macht `# Anhang {.appendix}` die folgenden Kapitel zu Anhängen A, B, C mit eigener Nummerierung,
die das Inhaltsverzeichnis zeigt.

## Kontext

- Keine Vorlage in DocLibs oder vt-tools-libs; dort steht die Abschlussfolie (`{.closing}`)
  zwingend am Ende. Heute: `generation/pptx/parser.py` zählt `self.chapters` je `#` und baut
  `ChapterSlide(title, line, number, layout)`; `{.closing}` verlangt, dass nichts folgt (E04-S01).
  Word: `#`–`###` sind „Überschrift 1–3", nummeriert über die Nummerierung der PTA-Vorlage
  (`design/word.py`, E03-S02); das Inhaltsverzeichnis ist ein `TOC`-Feld (E03-S01).
- Agenda nur ausdrücklich (`{.agenda}`, E04-S04): Kapitel hinter `{.backup}` dürfen dort nicht
  auftauchen, auch nicht in den Uhrzeiten (E16-S02).
- Die PTA-Word-Vorlagen haben keine Formatvorlage für Anhangsüberschriften; die Nummerierung
  „A, B, C" muss als eigene Nummerierungsinstanz (`w:num` mit `w:lvlOverride`/`w:startOverride`
  und `w:numFmt upperLetter` auf Ebene 1, `A.1` auf Ebene 2) an „Überschrift 1–3" gehängt
  werden, damit Word sie beim Bearbeiten fortführt.

## Vorgeschlagener Ansatz

1. **Syntax** (E02-S02): Heading-Attribute `.backup` (nur PPTX/HTML, nur `#`) und `.appendix`
   (nur DOCX/PDF, nur `#`), je höchstens einmal im Dokument; `{.closing}` darf danach nicht mehr
   kommen, `{.backup}` darf vor oder nach `{.closing}` stehen (vorher: der Generator sortiert die
   Abschlussfolie davor). Im jeweils anderen Format wird das Attribut ignoriert (Word kennt kein
   Backup, Folien keinen Anhang) — kein Fehler, ein Hinweis `attribute-ignored` (E08-S01).
2. **PPTX:** `DeckParser` markiert ab `{.backup}` alle Folien `backup=True`; Kapitel danach
   zählen nicht in `chapters`; `DeckWriter` schreibt die Folien nach der Abschlussfolie, davor
   eine `Trennfolie` mit dem Titel des Backup-`#` ohne Nummer (Nummernplatzhalter leer); die
   Folien bekommen die Fußzeile „Backup" statt „PTA – <Titel>" (Frage 1). Agenda (E04-S04) und
   Zeitplan (E16-S02) überspringen sie; die Fassung `kunde` (E16-S01) behält sie (Frage 2).
3. **HTML** (E10-S01): gleiche Reihenfolge; die Fortschrittsanzeige endet bei der Abschlussfolie,
   Backup-Folien liegen „dahinter" (Tastatur erreicht sie, Fortschrittsbalken bleibt voll).
4. **DOCX:** ab `{.appendix}` wechselt `generation/docx/writer.py` die Nummerierung: neue
   `w:num`-Instanz mit `upperLetter` auf Ebene 1 (`A`, `B`), `A.1`/`A.1.1` darunter, an dieselben
   Formatvorlagen „Überschrift 1–3" gebunden (über `w:numPr` der Absätze, nicht über den Stil);
   die Überschrift mit `{.appendix}` selbst wird eine unnummerierte „Überschrift 1" („Anhang")
   oder entfällt, wenn ihr Text leer ist (Frage 3). Abbildungen und Tabellen zählen weiter
   durch (Frage 4). Das Inhaltsverzeichnis zeigt die Anhänge, weil es dieselben Stile nimmt;
   Querverweise (E13-S02) geben „Anhang B" aus.
5. **PDF** (E05-S02): dieselbe Nummerierungslogik im Layout; Lesezeichen „A Glossar".
6. **Konverter:** PPTX → Markdown (E07-S03) erkennt Folien nach der Abschlussfolie und schreibt
   `# <Titel> {.backup}` vor sie; DOCX → Markdown (E07-S02) schreibt `{.appendix}` an die erste
   Überschrift mit Buchstabennummerierung, damit die Rundreise stabil ist.
7. **Tests:** Reihenfolge der Folien, Kapitelnummern ohne Backup, Agenda ohne Backup-Kapitel,
   Nummerierung `A`, `A.1`, `B` im DOCX-XML und nach dem Rücklesen, zwei `{.backup}` werfen,
   `{.closing}` nach `{.backup}` wirft. `samples/funktionen` zeigt beides.

## Akzeptanzkriterien

- [ ] Folien hinter `# … {.backup}` stehen nach der Abschlussfolie mit Trennfolie ohne Nummer;
      Kapitelnummern, Agenda und Zeitplan sind davon unberührt.
- [ ] Kapitel hinter `# … {.appendix}` heißen in Word A, B, C (A.1 …), Word führt die Zählung beim
      Einfügen weiterer Anhänge fort; das Inhaltsverzeichnis zeigt sie.
- [ ] Rundreise in beiden Formaten gibt die Attribute wieder.
- [ ] Falsche Reihenfolge und doppelte Attribute werfen mit Zeile.

## Offene Fragen

1. Fußzeile der Backup-Folien: „Backup", „PTA – <Titel> · Backup" oder unverändert? Vorschlag:
   „PTA – <Titel> · Backup", damit die Folie als Teil des Decks erkennbar bleibt.

> (2026-11-07) „PTA – <Titel> · Backup“.

2. Sollen Backup-Folien in der Kundenfassung (E16-S01) enthalten sein? Vorschlag: ja — Backup ist
   Vorrat, nicht intern; wer sie ausschließen will, markiert sie `{.internal}`.

> (2026-11-07) Ja; wer sie ausschließen will, markiert `{.internal}`.

3. `# Anhang {.appendix}` als eigene unnummerierte Überschrift ausgeben oder nur als Schalter
   verstehen (erste Anhangsüberschrift ist dann `# Glossar {.appendix}` = „A Glossar")?
   Vorschlag: Schalter — die Überschrift ist der erste Anhang.

> (2026-11-07) Schalter — die Überschrift ist der erste Anhang.

4. Abbildungen und Tabellen im Anhang: weiter durchzählen (Abbildung 12) oder je Anhang neu
   (Abbildung A-1)? Vorschlag: durchzählen — einfacher, und Word macht es ohne Zutun so.

> (2026-11-07) Durchzählen.

## Notizen

- `.appendix` hängt an der Nummerierung aus E03-S02; wird dort die Nummerierung der Vorlage
  verändert, muss die Anhangs-Instanz nachgezogen werden (Test im Vergleich mit der Vorlage,
  E01-S01).

## Implementierungsnotizen

Umgesetzt am 2026-11-08 (docs-2), ohne Zwischenprüfung.

### Entscheidungen

- **Syntax:** `.backup` und `.appendix` sind Felder von `HeadingAttributes`
  (`heading_attributes.split`/`check_level`: nur `#`). Die Regeln für das ganze Dokument prüft
  `generation/common/backup.check` aus `layout_syntax.check` — in **allen** Formaten gleich, Fehler
  mit `Line N: `: jedes Attribut höchstens einmal, nicht an Überschriften in Containern,
  `{.closing}` nach `{.backup}` ist ein Fehler.
- **PPTX:** `DeckParser` setzt ab `# … {.backup}` `Slide.backup` (kw-only) auf jeder Folie;
  `ChapterSlide.number` ist dort `None` (kein Zähler, Nummernplatzhalter fällt weg). Die
  Backup-Überschrift wird nie zur Titelfolie. Die Agenda (`KindReader.chapters`) endet vor
  `{.backup}`. `DeckWriter.add_footer` hängt `design.slides.BACKUP_FOOTER_SUFFIX` („ · Backup")
  an (Frage 1). Die Trennfolie des Backups heißt `Backup` (`p:cSld/@name`,
  `BACKUP_SLIDE_NAME`).
- **Wo das Backup beginnt**, entscheidet für HTML-Deck, `check` und PPTX-Konverter eine Funktion,
  `design.slides.backup_start`: die Folie namens `Backup`, sonst die erste Folie hinter der
  Abschlussfolie (so erkennt der Konverter auch in PowerPoint angehängte Folien).
- **HTML:** Backup-Folien ohne `data-chapter` und nicht in der Kapitelanzeige; `data-config`
  bekommt `mainSlides` (nur mit Backup), `deck.js` rechnet den Fortschritt bis dahin.
- **`check`:** `DeckStats.backup` zählt die Backup-Folien; Wörter, Inhaltsfolien und Minuten
  zählen sie nicht (Backup wird nicht vorgetragen). Die erste Zeile endet dann auf
  `…, 4 backup`, ohne Backup bleibt sie wie bisher.
- **Kundenfassung** behält das Backup (Frage 2); `.backup`/`.appendix` zusammen mit `.internal` an
  derselben Überschrift ist ein Fehler (siehe Warnungen).
- **Word:** Ab `{.appendix}` bekommen Überschrift 1–3 ein eigenes `w:numPr` auf eine neue
  Nummerierung (`BodyWriter._appendix_num`): eine Kopie der Überschriften-`abstractNum` der
  Vorlage mit `upperLetter` auf Ebene 1, ohne `w:pStyle`-Bindung, mit eigener `w:nsid`, dazu eine
  `w:num`-Instanz. Die `lvlText` der Vorlage (`%1.%2`) ergeben von selbst `A.1`, `A.1.1`. Die
  Überschrift mit dem Attribut ist der erste Anhang (Frage 3); Abbildungen und Tabellen zählen
  durch (Frage 4). Die Word-Agenda ohne Liste endet vor dem Anhang.
- **PDF:** `StoryBuilder.heading` zählt ab `{.appendix}` neu und schreibt die erste Stelle als
  Buchstaben (`backup.letters`, wie Word: Z, AA, BB); Inhaltsverzeichnis und Lesezeichen zeigen
  „A Glossar".
- **Hinweis** `attribute-ignored` (`NoteCodes.ATTRIBUTE_IGNORED`): `{.appendix}` auf Folien,
  `{.backup}` in Word und PDF (`backup.note_ignored`); beide an einer Überschrift sind erlaubt.
- **Konverter:** PPTX schreibt `# <Titel> {.backup}` für die Trennfolie bzw. `# Backup {.backup}`
  vor die erste Backup-Folie, die keine Trennfolie ist; DOCX hängt `{.appendix}` an die erste
  „Überschrift 1", deren `numId` auf Ebene 1 `upperLetter` zählt.
- **Beispiele:** `funktionen-praesentation.md` endet mit `# Backup {.backup}` und einer Folie,
  `funktionen-bericht.md` mit `# Glossar {.appendix}` und `# Quellen`; `test_funktionen.py`
  verlangt `{.appendix}` nur im Bericht, `{.backup}` nur im Deck.

### Abweichungen

- Die Anhangsnummerierung ist eine **eigene `abstractNum`** (Kopie) statt einer `w:num` mit
  `w:lvlOverride`/`w:lvl`: Überschreibungen ganzer Ebenen lesen nicht alle Programme (z. B.
  LibreOffice) zuverlässig; die Kopie wirkt überall gleich.
- Plan Punkt 1 erlaubt `{.backup}` vor **oder** nach `{.closing}` (der Generator sortiere die
  Abschlussfolie davor), Punkt 7 verlangt „`{.closing}` nach `{.backup}` wirft". Umgesetzt ist
  Punkt 7: die Abschlussfolie muss vor dem Backup stehen; umsortiert wird nichts. Die
  Folienreihenfolge entspricht damit immer der Quelle.
- Querverweise „Anhang B" (E13-S02) gibt es noch nicht; sie folgen mit E13-S02.
- Der PPTX-Konverter schreibt alle übrigen Folien weiter als `##` (auch die Abschlussfolie ohne
  `{.closing}`), wie bisher; nur das Backup kommt als `#` zurück.

### Warnungen

- **Warnung:** `{.backup}`/`{.appendix}` mit `.internal` an derselben Überschrift ist ein Fehler.
  Ohne die Überschrift wären die Kapitel danach in der Kundenfassung gewöhnliche Kapitel (mit
  Nummer, in der Agenda, vor der Abschlussfolie). Der Plan regelt den Fall nicht; vorsichtige
  Wahl. Wer das Backup intern halten will, markiert die Folien danach `{.internal}`.
- **Warnung:** `{.backup}` und `{.appendix}` gelten auch im jeweils anderen Format für die
  Fehlerprüfung (doppelt, Reihenfolge mit `{.closing}`), obwohl sie dort ignoriert werden — damit
  alle Formate dieselben Fehler ablehnen (Grundsatz von `layout_syntax`).
- **Warnung:** Ein Deck ohne Abschlussfolie darf ein Backup haben (es steht am Ende); der Plan
  setzt eine Abschlussfolie voraus, verbietet das Fehlen aber nicht.
- **Warnung:** In Word zählt ein Anhang nur weiter, wenn die neue Überschrift das `w:numPr` des
  Anhangs trägt (kopiert oder mit Enter aus einer Anhangsüberschrift fortgesetzt). Wird ein Absatz
  neu mit „Überschrift 1" formatiert, zählt er in der Hauptnummerierung (die Vorlage hat keine
  Anhangs-Formatvorlage; eine eigene anzulegen sah der Plan nicht vor).
- **Warnung:** Folien, die jemand in PowerPoint hinter die Abschlussfolie setzt, liest der
  Konverter als Backup (`# Backup {.backup}` davor) — auch wenn sie nie als Backup gemeint waren.

### Prüfpunkte

- `./run.sh generate samples/funktionen/funktionen-praesentation.md` (auch `--html`): Trennfolie
  „Backup" ohne Nummer hinter „Vielen Dank!", Fußzeile „PTA – … · Backup", Agenda ohne Backup;
  im HTML-Deck ist der Fortschrittsbalken auf der Abschlussfolie voll. In PowerPoint öffnen (hier
  kein Office vorhanden).
- `./run.sh generate samples/funktionen/funktionen-bericht.md` (auch `--pdf`): Kapitel „A Glossar",
  „A.1 Begriffe", „B Quellen"; in Word das Inhaltsverzeichnis aktualisieren und einen Anhang
  kopieren — er muss als „C" weiterzählen.
- `./run.sh check samples/funktionen` zeigt „…, 2 backup".
- Tests: `tests/generation/common/test_backup.py` (Reihenfolge, Nummern, Agenda, Fußzeile,
  Kundenfassung, HTML, `check`, Rundreisen, Nummerierung im XML, PDF-Text und Lesezeichen,
  Hinweise, Fehler in allen drei Formaten).

### Offene Punkte

- Querverweise auf Anhänge („Anhang B") mit E13-S02.
- Der PDF-Konverter erkennt Anhänge nicht (`A Glossar` bleibt Überschriftentext); der Plan
  verlangt die Rundreise nur für PPTX und DOCX.
- E16-S02 (Zeitplan, parallel in Arbeit) muss das Backup aus dem Zeitplan und der Agenda mit
  Uhrzeiten heraushalten — `Slide.backup` bzw. `KindReader.chapters` endet schon vor dem Backup.
