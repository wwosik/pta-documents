# E16-S04 Backup-Folien und Anhang

> Status: Entwurf
> Epic: [E16 Schulung und Zielgruppen](E16-schulung-und-zielgruppen.md)

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
