# E04-S04 Weitere Layouts: Agenda, Zwischenfazit, Zitat, Kontakt, Diagramme

> Status: in Prüfung
> Epic: [E04 PPTX-Generator auf der PTA-PowerPoint-Vorlage](../50-entwurf/E04-pptx-generator.md)
> Milestone: [M02 Rückmeldung und Folien-Syntax](../50-entwurf/M02-rueckmeldung-und-folien-syntax.md)

## Zusammenfassung

Die PTA-Layouts, die DocLibs nicht kennt, werden aus Markdown erreichbar — mit eigener Syntax statt
nur über `layout="…"`: Agenda (nur ausdrücklich), Zwischenfazit, Zitat, Kontakt (1–5 Personen) und
die vier Diagramm-Layouts, die Charts aus `chart`-Blöcken in ihren Diagrammplatzhalter setzen.

## Kontext

- Platzhalter (idx) laut Inventar der Basisvorlage:

  | Layout | Platzhalter |
  | ------ | ----------- |
  | `Agenda (kurz)` (≤ 4) | Nummern 14/16/18/20 („0X", 32 pt), Texte 15/17/19/21, Trennlinien 30–32 (Deko „x") |
  | `Agenda (lang)` (≤ 8) | Nummern 14–28 gerade, Texte 15–29 ungerade, Linien 30–36 |
  | `Zwischenfazit 01`/`02` | nur Titel 0 (32 pt Light, zentriert, „kann mehrere Zeilen lang sein") |
  | `Zitat 01`/`02` | nur Titel 0 (Georgia kursiv 48 pt, weiß) |
  | `Kontakt 01`–`05` | je Person Bild, Name, Funktion, E-Mail, Telefon: 34/14/35/36/38, dann 39/40–43, 44/45–48, 49/50–53, 54/55–58 |
  | `Kontakt mit Text` | Bild 34, Name 14, Funktion 35, E-Mail 36, Telefon 38, Text 37 |
  | `Titel und Diagramm` | Diagrammtitel 12, Einheit 13, Diagramm 15, Quelle 14 |
  | `Titel und zwei Diagramme` | links 12/13/15/14, rechts 16/17/19/18 |
  | `Titel, Diagramm und Text` / `Titel, Text und Diagramm` | Diagrammblock 12/13/15/14, Text 16 |

- E04-S01 kann jedes Layout schon mit `layout="…"` wählen und verteilt Text an `---`; das reicht
  für Agenda-Nummern, Kontaktzeilen und Diagrammplatzhalter nicht. Entscheidung 2026-11-06: keine
  automatische Agenda. Namen der Klassen: E02-S02, Frage 1.
- Charts (`ChartGraphic`) kommen aus E06-S01; das Chart-XML schreibt E06-S01, hier wird es in den
  Diagrammplatzhalter gesetzt.

## Vorgeschlagener Ansatz

1. **Attribute** in `heading_attributes.py` registrieren (gilt damit auch für DOCX/PDF, E02-S02):
   `.agenda`, `.interim`, `.quote`, `.contact` auf `##`; einzeln, nicht zusammen mit `.dark`,
   `kicker` oder Flow-Inhalt. `layout="…"` darf das Schwesterlayout wählen
   (`{.interim layout="Zwischenfazit 02"}`), ein fremdes Layout ist ein Fehler.
2. **Agenda** `## Agenda {.agenda}` mit genau einer Liste: ≤ 4 Punkte → `Agenda (kurz)`, 5–8 →
   `Agenda (lang)`, mehr → Fehler mit Hinweis auf zwei Agendafolien. Nummern „01" … automatisch;
   ungenutzte Nummer-/Textpaare und die Trennlinien unter dem letzten Punkt werden entfernt.
3. **Zwischenfazit** `## Die Migration ist ohne Ausfall möglich {.interim}`: Überschrift in den
   Titelplatzhalter von `Zwischenfazit 01`; Inhalt darunter ist ein Fehler.
4. **Zitat** `## Wer misst, misst Mist {.quote}`: Überschrift in den Titel von `Zitat 01`
   (`Zitat 02` über `layout`); Quellenangabe siehe Frage 2.
5. **Kontakt** `## Ihre Ansprechpartner {.contact}` mit einem `###` je Person (1–5): darunter
   ein Bild (Foto), dann Zeilen für Funktion, E-Mail (enthält `@`, wird `mailto:`-Link) und
   Telefon (beginnt mit `+` oder Ziffer) — Reihenfolge der Zeilen egal, Zuordnung nach Muster,
   Doppeltes ist ein Fehler. n Personen → `Kontakt 0n`; genau eine Person plus weiterer Text
   (Absatz oder Liste nach den Kontaktzeilen) → `Kontakt mit Text`. Ohne Foto wird der
   Bildplatzhalter entfernt (keine graue Fläche).
6. **Diagramm-Layouts:** E06-S01 (Schritt 3, Frage 3) schlägt vor, sie dort mit dem Folien-Chart
   umzusetzen. Wird das angenommen, entfällt dieser Schritt hier bis auf die Namen und idx in
   `design/slides.py`; sonst gilt hier: automatisch für `##`-Folien ohne andere Layout-Syntax —
   genau ein Chart → `Titel und Diagramm`; zwei (auch in `::: columns`) → `Titel und zwei
   Diagramme`; Chart und Text → `Titel, Diagramm und Text` bzw. `Titel, Text und Diagramm` nach
   Reihenfolge; `title` → Diagrammtitel, `unit` → Werteinheit, `source` → Quellenangabe, leere
   Platzhalter entfallen, der Titel steht nicht zusätzlich im Chart. Charts mit Tabelle oder
   Bildern und Zeichnungen (Formengruppe aus E06-S02) bleiben auf `Nur Titel`.
7. **Parser/Modell:** `AgendaSlide`, `InterimSlide`, `QuoteSlide`, `ContactSlide(persons, text)`,
   `ChartSlide(charts, text, text_first)` in `model.py`; Writer-Methoden in `writer.py`; alle
   Layoutnamen und Platzhalter-idx in `design/slides.py` (`Layouts`, `Placeholders`), geprüft vom
   Vergleichstest gegen die Vorlage (E01-S01).
8. **Tests:** je Layout Platzhalterbelegung und Fehlerfälle (Agenda mit 9 Punkten, Kontakt mit 6
   Personen, Inhalt unter Zwischenfazit, `.quote` mit `.dark`); Rundreise eines Beispiels
   `layouts-pta.md`; Ansicht `.tmp/review/layouts-pta.pptx`.

## Akzeptanzkriterien

- [x] Agenda, Zwischenfazit, Zitat und Kontakt 01–05/mit Text entstehen aus Markdown, ohne dass
      der Schreiber Layoutnamen oder Platzhalter kennt.
- [x] Ein Chart steht im Diagrammplatzhalter seines Layouts mit Titel, Einheit und Quelle in den
      Platzhaltern der Vorlage (umgesetzt hier oder in E06-S01, siehe Schritt 6).
- [x] Ohne `.agenda` entsteht nie eine Agendafolie.

## Offene Fragen

1. Soll `## Agenda {.agenda}` **ohne** Liste die Kapitel des Decks (die `#`-Überschriften nach
   dem Titel) als Agendapunkte übernehmen? Die Agenda bleibt ausdrücklich angefordert, aber der
   Schreiber muss die Kapitel nicht doppelt pflegen.

> (2026-11-07) Ja.

2. Zitat-Layouts haben nur einen Platzhalter. Wohin mit der Quelle („— Name, Funktion")?
   Vorschlag: ein Absatz unter der Überschrift wird zweiter Absatz im selben Platzhalter, 24 pt
   Segoe UI Light, nicht kursiv. Alternative: keine Quelle zulassen.

> (2026-11-07) Zweiter Absatz im selben Platzhalter, 24 pt Segoe UI Light, nicht kursiv.

## Notizen

- Abhängigkeiten: E02-S02 (Attribute), E04-S03 (Flow-Erkennung), für Schritt 6 E02-S04 und E06-S01.
- (2026-11-07, E02-S04) Einstieg in PPTX: `DeckParser._block` (Fall `fence`) ruft `self._draw`
  → `code_blocks.draw`, das heute für `DrawingGraphic`/`ChartGraphic` wirft; `ImageGraphic`
  wird ein `Images`-Visual mit dem Info-String als Alt-Text. `CodeBlockRequest.dark` kommt aus
  `DeckParser.dark` (`{.dark}` des laufenden `##`).

## Implementierungsnotizen

- **Attribute:** `heading_attributes.py` kennt `.agenda`, `.interim`, `.quote`, `.contact` als
  `HeadingAttributes.kind` (`SLIDE_KINDS`, `VALID`, `VALID_ON_SLIDE` ergänzt). `check_level`
  (alle Formate) lehnt sie auf `#`, zu zweit und mit `.dark`/`kicker` ab; Flow-Inhalt und
  fremde Layouts lehnt der PPTX-Parser ab (Aufbaufehler wie bei E04-S03 nur in PowerPoint).
- **Code:** Lesen in `generation/pptx/kind_parser.py` (`KindReader`), Schreiben in
  `generation/pptx/kinds.py`; Modell `AgendaSlide`, `InterimSlide`, `QuoteSlide`, `Person`,
  `ContactSlide`, `Chart`, `ChartSlide` in `model.py`; Layoutnamen, idx, `KIND_LAYOUTS`,
  `CONTACT_LAYOUTS`, Grenzen und Quellen-Schrift in `design/slides.py` (vom Vergleichstest gegen
  alle vier PowerPoint-Vorlagen geprüft). `DeckParser.image()` ist neu (Bild eines
  Inline-Kinds, konvertiert).
- **Agenda:** Liste → Punkte; ohne Inhalt (Frage 1) die `#`-Überschriften nach dem ersten
  `#`, ohne `{.closing}`. `layout="Agenda (kurz)"` mit mehr als vier Punkten ist ein Fehler.
  Ein Punkt ist genau ein Absatz (keine Unterlisten).
- **Zitat** (Frage 2): Quelle als zweiter Absatz im Titelplatzhalter, `sz=2400`, `i=0`,
  `a:latin` Segoe UI Light (fette Wörter behalten Segoe UI).
- **Kontakt:** Die Kontaktzeilen sind die Zeilen des **ersten** Absatzes unter `###`, der nicht
  nur ein Foto ist (Foto als eigener Absatz davor oder als Zeile im selben Absatz); alles danach
  ist Text (`Kontakt mit Text`). `layout="Kontakt 0m"` ist erlaubt, wenn m ≥ Personen und kein
  Text. Fehlt einer Person etwas (auch das Foto), entfällt der Platzhalter über `finish`.
- **Diagramme (Schritt 6):** E06-S01 Frage 3 („Ja") verlegt die Diagrammlayouts nach E06-S01.
  Auf Wunsch des Auftrags ist trotzdem die **Platzierung** hier umgesetzt, damit E06-S01 nur noch
  Renderer und Stil liefert: PPTX holt Fences über `code_blocks.render_graphic` (neu, neben
  `draw` und `unsupported`), `ChartGraphic` → `Chart` → `ChartSlide` mit Layoutwahl nach Schritt 6,
  `kinds.write_chart_slide` füllt 12/13/14 bzw. 16/17/18 und setzt den Chart über
  `generation/pptx/chart.insert_chart` (python-pptx, Reihenfarben aus `ChartSpec.colors`).
  `ChartSpec.source` ist neu. Mit `layout="…"` geht ein Chart in den nächsten Diagramm-
  platzhalter (Chart-Titel dann im Diagramm). Getestet mit einem Test-Renderer
  (`tests/generation/pptx/test_kinds.py`).
- **Warnung:** Es gibt noch keinen `chart`-Renderer (E06-S01); ohne ihn bleibt ein
  `chart`-Block Code mit `code-not-drawn`. Der PTA-Diagrammstil (Lücke 60 %, Achsen 14 pt,
  Achsenlinie 0,5 pt) fehlt in `chart.py` und folgt mit E06-S01.
- **Warnung:** Zeichnungen (`DrawingGraphic`) werfen in PowerPoint weiter „does not support
  yet" (Zeichenmodell E02-S03, Formengruppen E06-S02/E06-S03); Charts in Word ebenso (E06-S01).
  Der Test `test_drawings_and_charts_are_not_supported_yet` deckt nun Zeichnungen in beiden
  Formaten und Charts in Word ab.
- **Warnung:** Charts auf Flow-Folien (außer genau zwei als einzige Teile eines
  `::: columns`) sind ein Fehler statt auf `Nur Titel` gezeichnet; ein Chart neben Tabelle oder
  Bild bekommt wie jedes Visual eine eigene Folie.
- **Abweichung:** Word nimmt die Folienarten an und zeigt nur Überschrift und Inhalt (eine Agenda
  ohne Liste bleibt dort leer) — Gestaltung mit E03-S03 (dort notiert). PDF folgt mit E05-S04.
- Der PPTX-Konverter erkennt die neuen Layouts nicht eigens (Rundreise
  `tests/generation/pptx/samples/layouts-pta.roundtrip.expected.md`: Agenda-Nummern als
  Absätze, Quelle des Zitats im Titel, Kontaktzeilen als Absätze) — Sache von E07.
- **Prüfpunkte:** `.tmp/review/layouts-pta.pptx` und `.tmp/review/chart-layouts.pptx` in
  PowerPoint öffnen: Agenda-Linien, Zitatquelle (Größe, Schrift), Kontaktfotos (Beschnitt),
  Listenebenen im Text von `Kontakt mit Text` (Platzhalter 37), Diagramm im Platzhalter
  („Daten bearbeiten"). Lange Agendapunkte werden nicht eingepasst (Platzhalter einzeilig).
- Tests: 351 → 408 (`tests/generation/pptx/test_kinds.py`, Beispiel
  `tests/generation/pptx/samples/layouts-pta.md`).
