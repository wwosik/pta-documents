# E16-S03 Teilnehmerhandout

> Status: Entwurf
> Epic: [E16 Schulung und Zielgruppen](E16-schulung-und-zielgruppen.md)

## Zusammenfassung

`./run.sh handout documents/<thema>` macht aus einer Präsentation ein Word-Dokument auf der
PTA-Vorlage: je Folie das Folienbild und daneben oder darunter die Sprechernotizen
(Trainerfassung) oder Linien für eigene Notizen (Teilnehmerfassung), gegliedert nach den
Trennfolien, mit Deckblatt aus dem Front Matter und dem Zeitplan vorn.

## Kontext

- Keine Vorlage in DocLibs oder vt-tools-libs. PowerPoints eigener Handout-Export ist nicht im
  PTA-Word-Design und nicht ohne Office verfügbar.
- Folienbilder liefert E10-S02 (`render_deck`, Playwright, Extra `preview`, 1600 × 900 px, Builds
  im Endzustand); ohne das Extra gibt es keine Bilder. Word-Generator E03 (Vorlagen `hoch`,
  `quer`, je mit/ohne Deckblatt; Bilder in Satzspiegelbreite mit Beschriftung; Tabellenformat
  „PTA"). Sprechernotizen E09-S01, Fassungen E16-S01, Zeitplan E16-S02.
- `run.sh` führt `tools/<name>/<name>.py` als Verb aus; Verben englisch (Entscheidung
  2026-11-07).

## Vorgeschlagener Ansatz

1. **Modul** `src/pta_documents/handout/handout.py`: `build_handout(deck_markdown, images,
   schedule, options) -> MarkdownDocument` erzeugt **Markdown** für den DOCX-Generator (kein
   zweiter Word-Writer): Front Matter aus der Präsentation übernommen (`titel`, `untertitel`,
   `autor`, `ort`, `datum`, `kennzeichnung`), `vorlage: quer` für 2 Folien je Seite, `hoch` für 3
   und 6; Kapitel aus den Trennfolien als `#`, je Folie `##` mit dem Folientitel, dann das
   Folienbild als Tabelle ohne Rahmen (Bild links, rechts Notizen oder Linien — bei 6 je Seite
   drei Zeilen à zwei Bilder, Linien darunter). Titel- und Abschlussfolie erscheinen klein im
   Deckblatt bzw. am Ende; Backup-Folien (E16-S04) nur beim Trainer.
2. **Bilder:** `DocumentResource` je Folie aus `render_deck` (PNG, `--scale 2` für Druck); Breite
   so, dass 2/3/6 Folien eine Seite füllen (Maße aus dem Designmodell E01-S01). Ohne Extra
   `preview`: Text-Handout — Folientitel, Einleitungstext und Aufzählung der Folie als Text,
   darunter Notizen oder Linien — mit Hinweis „Für Folienbilder das Extra 'preview' installieren".
3. **Fassungen:** `--audience trainer` setzt Sprechernotizen (E09-S01) und Zeitnotizen
   (E16-S02) neben die Folien; `kunde`/`intern` setzen Notizlinien (Absätze mit unterer
   Rahmenlinie, Formatvorlage „Standard"; Zahl der Linien aus der verfügbaren Höhe). Die Fassung
   filtert auch die Folien (E16-S01).
4. **Zeitplan vorn:** gibt es Dauern (E16-S02), steht die Zeitplantabelle nach dem Deckblatt;
   sonst das Inhaltsverzeichnis der Kapitel (`inhaltsverzeichnis: ja`).
5. **Werkzeug** `tools/handout/handout.py`: `./run.sh handout <praesentation.md|ordner>
   [--layout 2|3|6] [--audience …] [--out …]`; schreibt `<name>-handout.docx` bzw.
   `<name>-handout-trainer.docx`; gibt Hinweise aus (E08-S01) und meldet, wenn Bilder fehlen.
6. **Tests** `tests/handout/test_handout.py`: ohne Extra Text-Handout mit allen Folientiteln und
   so vielen Linienabsätzen wie erwartet; mit Extra (skip sonst) so viele Bilder wie Folien, 2/3/6
   je Seite als Tabellen mit 1/1/2 Spalten; Trainerfassung enthält jede Notiz; Rundreise des
   Handouts durch den DOCX-Konverter (E07-S02) als `handout.roundtrip.expected.md`.
7. **Doku:** `anleitung.md` §5 (Handout), `ki-anleitung.md` (empfiehlt `handout --audience
   trainer` als Kontrolle, ob Notizen zu jeder Folie da sind).

## Akzeptanzkriterien

- [ ] `handout` erzeugt ein Word-Dokument auf der PTA-Vorlage, das Word ohne Reparatur öffnet,
      mit Deckblatt, Kapiteln, einem Bild je Folie und Notizen oder Linien.
- [ ] `--layout 2|3|6` füllt die Seiten wie angegeben; Querformat bei 2.
- [ ] Trainerfassung zeigt Sprechernotizen und Zeiten; Teilnehmerfassung Linien.
- [ ] Ohne Extra `preview` entsteht ein Text-Handout mit Hinweis statt eines Fehlers.

## Offene Fragen

1. Bild und Notizen **nebeneinander** (Querformat, wie PowerPoints „Notizenseiten") oder Bild
   oben, Notizen darunter (Hochformat, mehr Platz für Text)? Vorschlag: nebeneinander bei 2 je
   Seite, untereinander bei 3 und 6.

> (2026-11-07) Nebeneinander bei 2 je Seite, untereinander bei 3 und 6.

2. Soll das Handout die **Foliennummer** am Bild zeigen („Folie 12"), damit Teilnehmer
   mitblättern können? Vorschlag: ja, als Beschriftung „Folie n: Titel" (Formatvorlage
   „Beschriftung", ohne Abbildungszähler).

> (2026-11-07) Ja, „Folie n: Titel“ in „Beschriftung“ ohne Zähler.

## Notizen

- Das Handout entsteht als Markdown und geht durch den normalen DOCX-Generator; damit gelten
  alle Regeln von E03 und jede Verbesserung dort kommt dem Handout zugute. Das Markdown wird mit
  `--markdown` daneben abgelegt, wenn jemand es von Hand weiterbearbeiten will.
