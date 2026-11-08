# E16-S03 Teilnehmerhandout

> Status: in Prüfung
> Epic: [E16 Schulung und Zielgruppen](../50-entwurf/E16-schulung-und-zielgruppen.md)
> Milestone: [M04 Präsentieren und Schulung](../50-entwurf/M04-praesentieren-und-schulung.md)

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
- [x] Trainerfassung zeigt Sprechernotizen und Zeiten; Teilnehmerfassung Linien.
- [x] Ohne Extra `preview` entsteht ein Text-Handout mit Hinweis statt eines Fehlers.

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

## Implementierungsnotizen

Umgesetzt am 2026-11-08 (docs-2), ohne Zwischenprüfung.

### Entscheidungen

- **Modul** `src/pta_documents/handout/handout.py` (öffentlich über `pta_documents.handout`):
  `build_handout(document, pictures, options) -> Handout` (Markdown mit den Folienbildern als
  Ressourcen, Fassung, Layout, Hinweise), `write_handout(handout, output) -> GenerationResult`
  (DOCX-Generator mit `docx_options()`), `slide_pictures(document, audience)` (HTML-Deck derselben
  Fassung → `render_deck`), `HandoutLayout` (2, 3, 6), `HandoutOptions(layout, audience)`.
- **Woher die Folien kommen:** aus der im Speicher erzeugten **PPTX** der Fassung, gelesen mit
  python-pptx (Layoutname, Titel, Text, Sprechernotizen), nicht aus dem Markdown. So stimmen
  Foliennummern, geteilte Folien („Forts."), Kapitel und die „Geplant"-Notiz der Trainerfassung
  (E16-S02) mit Deck und Vorschau überein, ohne den Folienparser nachzubauen.
- **Kein zweiter Word-Writer:** Das Handout ist Markdown für den DOCX-Generator. Was Markdown
  allein nicht ausdrücken konnte, sind zwei **DOCX-Optionen nur über die API** (kein
  Front-Matter-Schlüssel, Standard unverändert): `DocxOptions.figure_numbers=False`
  (Beschriftung „Folie 3: Titel" in „Beschriftung" ohne Zähler, Frage 2) und
  `side_by_side_columns=True` (`::: columns` als Tabelle ohne Linien im Stil „Bildreihe", Bild
  links, Notizen bzw. Linien rechts; `BodyWriter.cell`/`blocks()` schreiben Absätze und Tabellen
  in die Zelle). Nur `---` trennt dort Spalten, `***` bleibt eine Linie.
- **Linien zum Schreiben** sind `***` (horizontale Linie = „Standard"-Absatz mit Rahmenlinie
  unten, wie im Plan).
- **Layouts** (Frage 1): 2 = `quer`, Bild links (7,7 cm), sechs Linien bzw. Notizen rechts;
  3 = `hoch`, Bild (7,1 cm), darunter zwei Linien bzw. Notizen; 6 = `hoch`, zwei Bilder (6,7 cm)
  als Bildreihe, darunter zwei Linien bzw. die Notizen beider Folien („**Folie 5:**" davor).
  Standard ist **3** (der Plan nannte keinen; PowerPoints übliches Handout mit Linien).
- **Maße** (`geometry`) aus Seite und Absatzformaten der Vorlage (`design.word_styles`): je Seite
  Platz für eine „Überschrift 1" und 18 pt Reserve, der Rest durch 2 bzw. 3 Zeilen ergibt Bild,
  Beschriftung und Linien. Die Bilder werden auf 300 dpi bei dieser Breite verkleinert, bekommen
  einen dünnen grauen Rahmen (Folien sind weiß auf weißem Papier) und so viele dpi, dass ihre
  natürliche Größe die Breite ist — der DOCX-Generator übernimmt sie unverändert.
- **Aufbau:** Deckblatt aus dem Front Matter der Präsentation (`titel`, sonst Titel der PPTX;
  `untertitel`, `autor`, `ort`, `datum`, `sprache`, `kennzeichnung`, sonst `intern` für
  intern/trainer), die Titelfolie klein (6 cm) **nach** dem Deckblatt, dann der Zeitplan
  (`**Zeitplan**` + `Schedule.to_markdown()`) oder `inhaltsverzeichnis: ja`, je Trennfolie `#`
  und die Trennfolie selbst als Folie, die Abschlussfolie klein am Ende.
- **Fassungen:** wie `generate` — `--audience`, sonst `fassung:`, sonst `kunde`; Dateiname
  `<name>-handout.docx`, `-handout-intern.docx`, `-handout-trainer.docx`. Nur die Trainerfassung
  zeigt Notizen und die Backup-Folien (E16-S04, Plan Punkt 1).
- **Text-Handout** ohne Vorschau: `**Folie n: Titel**`, Absätze und Listen der Folie
  (Agendapunkte als Liste, Subheadline fett), Notizen als Zitat (vom Folientext abgesetzt) bzw.
  Linien; Hinweis `handout-without-pictures` (neu in `NoteCodes`) und im Werkzeug die Zeile
  `no slide pictures for …`.
- **Werkzeug** `tools/handout/handout.py`: `--layout`, `--audience`, `--out`, `--markdown`
  (Markdown `<name>-handout.md` und Bilder `<name>-handout/` daneben), `--strict`; Exit-Codes wie
  `preview` (1 Fehler, 2 falsche Schalter).
- **`./run.sh preview --audience kunde|intern|trainer`** ergänzt (Offener Punkt aus E10-S02);
  andere Fassungen als `kunde` landen in `vorschau/<name>-intern/` bzw. `…-trainer/`.

### Abweichungen

- `build_handout(document, pictures, options)` statt `build_handout(deck_markdown, images,
  schedule, options)`: den Zeitplan holt die Funktion selbst (`deck_schedule` der Fassung).
- Kein `##` je Folie: Titel und Nummer stehen in der Beschriftung „Folie n: Titel"; eine
  Überschrift je Folie hätte die Seitenaufteilung 2/3/6 zerstört und das Inhaltsverzeichnis
  aufgebläht.
- Die Titelfolie steht klein **nach** dem Deckblatt, nicht im Deckblatt (das Deckblatt der
  Vorlage hat keinen Bildplatz; dafür hätte der DOCX-Generator geändert werden müssen).
- Layout 2 und 6 sind Tabellen mit **zwei** Spalten (Bild | Notizen bzw. Bild | Bild), Layout 3
  hat keine Tabelle (Bild und Linien untereinander) — der Plan nannte „1/1/2 Spalten".
- Vorschau im Maßstab 1 (1600 px) statt `--scale 2`: bei höchstens 7,7 cm Breite sind das über
  500 dpi; die Bilder werden ohnehin auf 300 dpi verkleinert (69 Folien ≈ 6 MB statt ≈ 14 MB).
- Meldungen englisch wie bei den übrigen Werkzeugen und Hinweisen („The handout shows the text
  of each slide instead of its picture. …") statt „Für Folienbilder das Extra 'preview'
  installieren".
- Die Rundreise-Erwartung heißt `tests/handout/samples/handout.roundtrip.expected.md`; der
  DOCX-Konverter liest die Spalten-Tabelle wie eine Bildreihe (Bilder, dann Absätze), Linien und
  Listenzeichen der Notizen gehen dabei verloren.

### Warnungen

- **Warnung:** Ob 2/3/6 Folien wirklich je eine Seite füllen, ist **nicht** in Word geprüft
  (hier kein Word und kein LibreOffice). Die Maße sind aus den Formatvorlagen geschätzt
  (Zeilenhöhe Segoe UI 1,33 × Schriftgröße) und mit Reserve gerechnet. Beginnen zwei Kapitel auf
  derselben Seite, trägt sie eine Folie weniger; lange Notizen in der Trainerfassung verlängern
  Seiten. Deshalb sind die Akzeptanzkriterien 1 und 2 offen gelassen.
- **Warnung:** Kein Hinweis im Dokument selbst, wenn die Bilder fehlen (vorsichtigste Wahl: ein
  Entwickler-Hinweis gehört nicht in ein Teilnehmer-Handout); er steht nur in der Ausgabe des
  Werkzeugs bzw. in `Handout.notes`.
- **Warnung:** Das mit `--markdown` abgelegte Markdown ergibt mit `./run.sh generate --docx`
  **nicht** dasselbe Handout: die beiden DOCX-Optionen gibt es nur über die API, `generate`
  setzt Bild und Notizen untereinander und nummeriert die Beschriftungen. Ein Front-Matter-
  Schalter dafür hätte neue, in `samples/funktionen` vorzuführende Schlüssel bedeutet.
- **Warnung:** Folientext und Notizen kommen als reiner Text (fett/kursiv, Links und Code gehen
  verloren); Tabellen einer Folie im Text-Handout als „Zelle · Zelle".
- **Warnung:** Die Kundenfassung des Handouts lässt das Backup weg, die Kundenfassung des Decks
  (E16-S04) behält es — so verlangt es der Plan; wer Backup-Folien im Teilnehmer-Handout will,
  braucht `--audience trainer` (mit Notizen).
- **Warnung:** Der Zeitplan steht auch im Kunden-Handout (Plan Punkt 4), mit leerer Spalte
  „Notizen".
- **Warnung:** `./run.sh preview` legt Präsentationen mit `fassung: trainer` (z. B.
  `samples/funktionen/zeitplan-praesentation.md`) jetzt unter `vorschau/<name>-trainer/` ab statt
  unter `vorschau/<name>/` — gleich benannt wie die Dateien von `generate`.

### Prüfpunkte

- `./run.sh handout samples/funktionen/funktionen-praesentation.md --layout 2|3|6` und
  `./run.sh handout samples/funktionen/zeitplan-praesentation.md` (Trainerfassung) in Word
  öffnen: öffnet ohne Reparatur (AK 1), 2/3/6 Folien je Seite, Querformat bei 2 (AK 2),
  Beschriftungen „Folie n: Titel" ohne Nummer, Linien zum Schreiben, Notizen mit „Geplant: …"
  (AK 3). Exemplare nach den Tests in `.tmp/review/handout/` (mit Browser auch je Layout).
- Ein Handout drucken: Bilder scharf, Rahmen sichtbar, Linienabstand zum Schreiben brauchbar.
- Ohne Playwright (`.venv` ohne Extra `preview`): `./run.sh handout …` schreibt das Text-Handout
  und meldet `no slide pictures` (AK 4; im Test über einen Ersatz von `slide_pictures` geprüft).
- Tests: `tests/handout/test_handout.py`, `tests/generation/docx/test_handout_options.py`,
  `tests/preview/test_preview_tool.py` (`--audience`).

### Offene Punkte

- Seitenumbrüche je 2/3/6 Folien erzwingen (z. B. eine Seitenumbruch-Syntax im
  DOCX-Generator), falls die Prüfung in Word zeigt, dass die geschätzten Maße nicht reichen.
- Ein Front-Matter-Schalter für die beiden DOCX-Optionen, damit das `--markdown`-Ergebnis mit
  `generate` dasselbe Handout ergibt.
- Formatierung (fett, kursiv) der Folientexte im Text-Handout.
