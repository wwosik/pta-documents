# E16-S01 Zielgruppenfassungen

> Status: in Prüfung
> Epic: [E16 Schulung und Zielgruppen](../50-entwurf/E16-schulung-und-zielgruppen.md)
> Milestone: [M04 Präsentieren und Schulung](../50-entwurf/M04-praesentieren-und-schulung.md)

## Zusammenfassung

Blöcke, Folien und Abschnitte mit `{.internal}` oder in `::: internal` erscheinen nur in der
internen Fassung; `::: exercise` steht in jeder Fassung, `::: solution` nur beim Trainer.
`./run.sh generate --audience kunde|intern|trainer` wählt die Fassung, das Front Matter `fassung:`
setzt die Vorgabe des Dokuments. Interne Fassungen heißen `…-intern.docx` / `…-intern.pptx` und
tragen automatisch die Kennzeichnung `intern`.

## Kontext

- Keine Vorlage in DocLibs oder vt-tools-libs. Verwandt: `{.build}`/`{.frag}` als Attribut auf
  Blöcken (E09-S02) und die Container aus E02-S02 (`layout_syntax.CONTAINERS`,
  `heading_attributes.VALID`) — dieselben Stellen, an denen `internal`, `exercise`, `solution`
  registriert werden.
- Heute: `markdown/parser.py` liefert einen flachen Token-Strom (markdown-it-py) an
  `generation/docx/writer.py` und `generation/pptx/parser.py`; eine Zeile `{.klasse}` allein ist
  noch unbekannt. `tools/generate/generate.py` wählt Format aus dem Dateinamen und kennt die
  Schalter `--docx`, `--pptx`, `--out`.
- Kennzeichnung: `kennzeichnung: vertraulich | intern | entwurf | kein` (E12-S03, E04-S05) ist ein
  Front-Matter-Schlüssel, den `apply_front_matter` in die Optionen überträgt.

## Vorgeschlagener Ansatz

1. **Syntax** (E02-S02 erweitert): Container `internal`, `exercise`, `solution` ohne Argumente in
   allen Formaten; Heading-Attribut `.internal` auf `#` und `##` (ganzes Kapitel bzw. ganze Folie
   samt Notizen); Blockmarkierung `{.internal}` auf Listen, Tabellen, Absätzen, Bildern wie
   `{.build}`. `::: solution` muss direkt auf `::: exercise` folgen oder darin stehen, sonst
   Fehler: „A '::: solution' on line 40 needs a '::: exercise' right before it."
2. **Zielgruppe** `Audience` (`StrEnum`: `KUNDE`, `INTERN`, `TRAINER`) in
   `generation/common/audience.py`; `filter_tokens(tokens, audience, notes) -> list[Token]`
   entfernt bei `kunde` alles Interne und alle Lösungen, bei `intern` die Lösungen, bei `trainer`
   nichts; `exercise`-Zäune bleiben als Container für E04-S03/E03-S03 (Kasten „Übung"), `solution`
   als Kasten „Lösung" nur beim Trainer. Je weggelassenem Block ein Zähler; am Ende **ein**
   Hinweis `audience-omitted` (E08-S01): „12 internal blocks and 3 solutions were left out for
   the audience 'kunde'."
3. **Front Matter** `fassung: kunde | intern | trainer` (Standard: Epic-Frage 1) in `Keys`; die
   Generatoren bekommen `options.audience`, rufen `filter_tokens` vor dem Parsen auf und setzen,
   wenn die Fassung nicht `kunde` ist und `kennzeichnung` fehlt, `kennzeichnung = intern`.
4. **Werkzeug** `generate --audience kunde|intern|trainer|alle`: überschreibt `fassung:`;
   Dateiname `<name>.docx` für `kunde`, `<name>-intern.docx`, `<name>-trainer.pptx` sonst;
   `alle` erzeugt jede Fassung, in der sich der Token-Strom unterscheidet (sonst nur eine).
   `check` (E08-S02) zeigt Statistik je Fassung.
5. **Konverter:** nichts zu tun — weggelassene Blöcke sind nicht im Dokument. Rundreise-Tests
   laufen je Fassung gegen `deck-kunde.roundtrip.expected.md` und `deck-trainer….`.
6. **Doku:** `anleitung.md` §2 (Schalter, Dateinamen), §5 (Übung/Lösung), `ki-anleitung.md`
   (Regel: Preise, interne Bemerkungen und Lösungen immer in `internal`/`solution` schreiben, damit
   die Kundenfassung sauber bleibt); `samples/funktionen` zeigt alle drei Container; E04-S06,
   E03-S05 nehmen sie in die Guides auf.
7. **Tests** `tests/generation/common/test_audience.py`: jede Kombination Syntax × Fassung; Folie
   mit `.internal` fehlt ganz samt Notizen (E09-S01); Kapitelnummern der Trennfolien (E04-S01)
   zählen ohne die weggelassenen; Hinweis mit richtigen Zahlen; `solution` ohne `exercise` wirft.

## Akzeptanzkriterien

- [x] `--audience kunde` enthält keinen Text aus `internal`- und `solution`-Blöcken, `intern`
      keine Lösungen, `trainer` alles; die Kundenfassung ist byteweise die Standardfassung.
- [x] Interne und Trainerfassungen heißen `-intern`/`-trainer` und tragen die Kennzeichnung
      `intern`, sofern das Front Matter nichts anderes setzt.
- [x] Ein Hinweis nennt die Zahl der weggelassenen Blöcke; Kapitel- und Foliennummern sind lückenlos.
- [x] Rundreise je Fassung stabil; Guides und Anleitungen nennen die Syntax.

## Offene Fragen

1. Soll `::: internal` auch **innerhalb** einer Tabelle gehen (Spalte „intern" ausblenden), etwa
   über eine Kopfzelle `Kommentar {.internal}`? Vorschlag: nein, erst wenn der Bedarf da ist —
   Tabellen werden stattdessen doppelt geschrieben.

> (2026-11-07) Nein, vorerst nicht.

2. Sollen Lösungen in der Teilnehmerfassung (`kunde`) als leerer Kasten „Lösung" mit Linien
   bleiben (zum Ausfüllen) oder ganz fehlen? Vorschlag: ganz fehlen; das Handout (E16-S03) hat
   ohnehin Notizlinien.

> (2026-11-07) Ganz fehlen.

## Notizen

- `exercise`/`solution` als Kästen zeichnen E04-S03 (Folien, PTA-Stil der Fazit-Box) und
  E03-S03 (Word, Tabellenrahmen „PTA"); hier wird nur gefiltert und registriert.

## Implementierungsnotizen

Umgesetzt am 2026-11-08 (docs-2), ohne Zwischenprüfung.

### Entscheidungen

- **Ein Filter für alle Formate:** `generation/common/audience.py` (`Audience`, `filter_tokens`,
  `check`, `versions`, `resolve`, `needs_marking`). DOCX (`BodyWriter.write`), PPTX
  (`DeckParser.parse`) und PDF (`PdfGenerator.generate`) rufen `filter_tokens` direkt nach
  `layout_syntax.check` auf; das HTML-Deck erbt es über den PPTX-Lauf
  (`HtmlDeckOptions.audience` → `slides()`). `layout_syntax.check` prüft die Zielgruppen-Syntax
  über `audience.check` — alle Fassungen lehnen dieselben Fehler ab.
- **Container werden ausgepackt:** `internal`, `exercise`, `solution` verschwinden aus dem
  Token-Strom; was bleibt, steht eine `level` höher, als wäre es ohne Container geschrieben. So
  muss kein Generator die Container kennen (vorher hätte jeder Container eine Folie zur
  Flow-Folie gemacht und `FlowReader.container` wäre auf den Fehlerzweig gelaufen).
- **`{.internal}` ist ein Blockmarker** (`block_markers.NAMES`) und ein Überschriftenattribut
  (`HeadingAttributes.internal`, auf `#` und `##`). Ein `#` mit `.internal` reicht bis zum
  nächsten `#`, ein `##` bis zum nächsten `#`/`##` (oder bis zu den Fußnoten). `{.internal}` vor
  `::: notes` ist erlaubt (interne Sprechernotizen), vor einer `#`/`##`-Überschrift ein Fehler mit
  Verweis auf das Attribut.
- **Vorrang:** `options.audience` (Standard `None`) geht `fassung:` vor, damit `--audience` das
  Front Matter überschreibt (Story Punkt 4) — anders als bei allen übrigen Optionen. Eine
  falsche `fassung:` ist trotzdem ein Fehler.
- **Kennzeichnung:** nicht-`kunde` und kein `kennzeichnung:` im Front Matter → `intern`; eine
  über die API gesetzte Kennzeichnung (außer `kein`) bleibt. `fassung: trainer` mit
  `kennzeichnung: kein` ergibt eine Trainerfassung ohne Kennzeichnung (das Front Matter setzt
  etwas anderes, Akzeptanzkriterium 2).
- **Hinweis** `audience-omitted` (`NoteCodes.AUDIENCE_OMITTED`) ohne Zeile; ein weggelassenes
  Kapitel bzw. eine Folie zählt als **ein** Block, Blöcke darin nicht extra.
- **Werkzeuge:** `generate --audience kunde|intern|trainer|alle` (Dateiname `-intern`/`-trainer`
  auch, wenn nur `fassung:` die Fassung wählt), `check --audience …` mit Statistik je Fassung
  (`CheckOptions.audience`, `report_stats` filtert), `generate-samples` hängt das Suffix an.
- **Beispiele:** `samples/funktionen/fassungen-bericht.md` und `fassungen-praesentation.md` mit
  `fassung: trainer` (sonst kämen Hinweise, und die Beispiele müssen ohne Hinweise erzeugen).

### Abweichungen

- Fehlertext der Lösung ohne Übung im Format des Repos: `Line 40: A '::: solution' needs a
  '::: exercise' right before it (or around it).` statt „… on line 40 …".
- `filter_tokens(tokens, audience, notes, format, line_offset)` hat zwei Parameter mehr als im
  Plan (Fehlerformat und Zeilen für die Titelfolien-Prüfung).
- Rundreise-Erwartungen heißen `tests/generation/common/samples/fassungen-<fassung>.roundtrip.expected.md`
  (Deck) und `fassungen-<fassung>-bericht.roundtrip.expected.md` (Word).
- `generation/html/options.py` bekam ein Feld `audience` (der Plan nannte das HTML-Deck nicht;
  ohne das Feld wirkte `--audience --html` nicht).

### Warnungen

- **Warnung:** Übung und Lösung bekommen **keinen Kasten** („Übung"/„Lösung"). Die Notizen der
  Story verweisen dafür auf E04-S03/E03-S03, die aber schon umgesetzt sind und keinen Kasten
  vorsehen; vorsichtigste Wahl: Inhalt schlicht zeigen. Wer einen Kasten will, braucht eine
  eigene Story (Container dann nicht mehr auspacken, sondern in PPTX/Word/PDF zeichnen).
- **Warnung:** `{.internal}` vor der ersten `#` einer Präsentation (Titelfolie) ist ein Fehler
  (sonst würde das nächste Kapitel zur Titelfolie). In Word ist dasselbe ein gewöhnliches
  internes Kapitel. Keine Entscheidung im Plan; vorsichtige Wahl.
- **Warnung:** `#`/`##` innerhalb von `::: internal`/`exercise`/`solution` sind ein Fehler (nach
  dem Auspacken würden sie sonst Folien beginnen, was in anderen Containern nicht passiert).
- **Warnung:** Ein Block trägt weiterhin nur **einen** Marker; ein interner Build-Block wird als
  `::: internal` mit `{.build}` darin geschrieben. Ein anderer Marker vor einem der drei
  Container ist ein Fehler (er ginge beim Auspacken verloren).
- **Warnung:** Die Stilregeln von `check` und die Zeichenprüfung des PDF (`character-missing`)
  lesen das ungefilterte Markdown: ein fehlendes Zeichen in einem internen Block meldet auch die
  Kundenfassung. Die Statistik zählt die Fassung.
- **Warnung:** Fußnoten, auf die nur weggelassene Blöcke verweisen, bleiben als Definition im
  Token-Strom; der Generator setzt sie wie bisher (nicht gesondert geprüft).

### Prüfpunkte

- `./run.sh generate samples/funktionen/fassungen-praesentation.md --audience alle` schreibt drei
  PPTX; Kundenfassung ohne Folie „Preise", ohne Lösung, ohne Sticker; intern/trainer mit
  „Für den internen Gebrauch". In PowerPoint öffnen (hier kein Office vorhanden).
- Dasselbe für `fassungen-bericht.md` als DOCX und mit `--pdf` als PDF; `--html` für das Deck.
- `./run.sh check samples/funktionen --audience alle` zeigt je Fassung eine Statistik.
- Tests: `tests/generation/common/test_audience.py` (jede Syntax × Fassung × DOCX/PPTX/PDF/HTML,
  Folie samt Notizen, Kapitelnummern, Hinweis, Fehler, Kennzeichnung, Rundreisen, Werkzeug).

### Offene Punkte

- Kästen „Übung"/„Lösung" (siehe Warnung).
- Die Guides (E04-S06, E03-S05) nehmen die Syntax auf, wenn sie entstehen; `anleitung.md`,
  `ki-anleitung.md` und `verwendung.md` nennen sie schon.
