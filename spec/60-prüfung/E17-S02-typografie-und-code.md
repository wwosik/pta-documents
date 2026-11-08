# E17-S02 Deutsche Typografie, Silbentrennung, Code-Highlighting

> Status: in Prüfung
> Epic: [E17 Qualität und Arbeitsfluss](../50-entwurf/E17-qualitaet-und-arbeitsfluss.md)
> Milestone: [M02 Rückmeldung und Folien-Syntax](../50-entwurf/M02-rueckmeldung-und-folien-syntax.md)

## Zusammenfassung

Die Generatoren setzen deutschen Text typografisch richtig — „Anführungszeichen“,
Gedankenstrich, geschützte Leerzeichen in `z. B.` und `10 %` —, das PDF trennt Silben und kann
Blocksatz, und Codeblöcke werden in allen drei Formaten farbig hervorgehoben. Wer gerade Zeichen
will, schaltet die Typografie ab.

## Kontext

- `markdown/parser.py`: `MarkdownIt("commonmark", {"typographer": False})`. markdown-it-py
  bringt `typographer` (Ersetzungen `(c)`, `--`, `...`) und `smartquotes` mit; die Quotes sind
  über `options["quotes"]` einstellbar (`„“‚‘` für Deutsch). Geschützte Leerzeichen und
  Abkürzungen kennt es nicht.
- Konverter (E07-S02, E07-S03) geben Text zurück, wie er im Dokument steht; nach der Typografie
  enthält die Rundreise also `„…“` statt `"…"` — Epic-Frage 2.
- PDF (E05-S02): die portierte Layout-Engine bricht Zeilen an Leerzeichen; Silbentrennung und
  Blocksatz fehlen in DocLibs. **pyphen** (Wörterbücher von Hunspell/LibreOffice, Tri-Lizenz
  GPL 2 / LGPL 2.1 / MPL 1.1 — unter MPL nutzbar, pure Python) liefert deutsche Trennstellen;
  Alternative ohne Abhängigkeit gibt es nicht.
- Code: `generation/docx/writer.py` schreibt Codeblöcke in die Formatvorlage „Code" (Consolas,
  grau), PPTX in ein Textfeld, PDF in Mono — alles einfarbig. **Pygments** (BSD-2) liegt bereits
  in der `.venv` (`pygmentize`), ist aber keine Abhängigkeit; E02-S04 definiert die Code-Block-
  Renderer-Schnittstelle für Grafiken, nicht für Text.

## Vorgeschlagener Ansatz

1. **Typografie** (`markdown/typography.py`), als Core-Regel nach dem Parsen auf `text`-Token
   außerhalb von Code, Links-URLs, Front Matter und Mathe (falls je): Anführungszeichen `"…"` →
   `„…“`, `'…'` → `‚…‘` (Öffnen/Schließen nach Leerzeichen-Kontext, wie `smartquotes`, aber mit
   deutschen Zeichen und ohne Apostroph-Fehler in `geht's`); ` - ` und ` -- ` → ` – `; `...` →
   `…`; geschütztes Leerzeichen (U+00A0) in Abkürzungen mit Punkt (`z. B.`, `u. a.`, `d. h.`,
   `Nr. 3`, `S. 12`, `§ 5`, `Abs. 2`), zwischen Zahl und Einheit/Prozent (`10 %`, `5 km`,
   `3 Mio.`), in Datumsangaben `1. Januar`, geschütztes schmales Leerzeichen (U+202F) nur, wenn
   die Schrift es hat (Selawik: prüfen, sonst U+00A0); geschützter Bindestrich (U+2011) in
   `E‑Mail`? — nein (Frage 1). Sprache `en` nutzt `“…”`/`‘…’` und englische Regeln ohne
   Abkürzungsliste. Front Matter `typografie: ja | nein` (Standard ja, Epic-Frage 2);
   `DocxOptions.typography`, `PptxOptions.typography`, `PdfOptions.typography`.
2. **Konverter:** Option `ConversionOptions.plain_quotes` (Standard aus); an: `„“‚‘` → `"'`,
   `–` → `-`, U+00A0 → Leerzeichen, damit die Rundreise-Tests den Ausgangstext wiederfinden. Die
   Rundreise-Erwartungen (`*.roundtrip.expected.md`) werden einmal erneuert.
3. **Silbentrennung und Blocksatz** (E05-S02, `generation/pdf/hyphenation.py`): Extra `pdf`
   erhält `pyphen`; beim Zeilenumbruch darf ein Wort an einer Trennstelle geteilt werden, wenn
   sonst mehr als ein Fünftel der Zeile leer bliebe; mindestens zwei Zeichen vor und drei nach
   der Trennstelle, keine Trennung in Code, Links, letzten Wörtern eines Absatzes, nicht über
   Seitenwechsel; Wörter mit Bindestrich nur am Bindestrich. Front Matter `blocksatz: ja | nein`
   (Standard nein — die Word-Vorlage ist linksbündig, Frage 2); `silbentrennung: ja | nein`
   (Standard ja). Hurenkinder-/Schusterjungen-Regeln von E05-S02 bleiben.
4. **Code-Highlighting** (`generation/common/code_highlight.py`): Pygments (BSD) als Kern-
   abhängigkeit (klein, pure Python); Sprache aus dem Zaun (```` ```python ````), Lexer über
   `get_lexer_by_name`; Tokens auf ein PTA-Schema abgebildet: Schlüsselwörter PTA-Blau `006FB9`
   fett, Strings Dunkelblau `004676`, Kommentare Grau `787878` kursiv, Zahlen/Konstanten
   `404040`, Rest Text; kein Hintergrund je Token (die Fläche bleibt das Grau der Formatvorlage).
   Writer: DOCX Runs mit `w:color`/`w:b`/`w:i` in der Formatvorlage „Code"; PPTX Runs im
   Codetextfeld; PDF farbige Spans in Mono. Unbekannte Sprache oder kein Zaun → einfarbig, Hinweis
   `code-language-unknown` (E08-S01) nur bei angegebener, unbekannter Sprache. `highlight: nein`
   im Front Matter schaltet ab. Konverter geben Code weiterhin als Zaun mit Sprache zurück
   (Sprache aus dem ersten Run? — nein: aus einer Absatz-Eigenschaft, Frage 3).
5. **Dokumentation und Guides:** `anleitung.md`/`ki-anleitung.md`: „Gerade Anführungszeichen
   schreiben, die Typografie macht den Rest"; Liste der Ersetzungen; Hinweis, dass Code unberührt
   bleibt. Guides (E02-S05) bekommen den Abschnitt „Typografie".
6. **Tests** `tests/markdown/test_typography.py` (jede Regel, Code-Span unberührt, Apostroph,
   `en`), `tests/generation/pdf/test_hyphenation.py` (Trennung nur an Trennstellen, Mindestzeichen,
   kein Wort über Seitenwechsel, Blocksatz-Zeilenbreite), `tests/generation/*/test_code_highlight.py`
   (Farben je Token-Art, unbekannte Sprache einfarbig mit Hinweis); `samples/funktionen/` zeigt
   Typografie und ein farbiges Python-Beispiel.

## Akzeptanzkriterien

- [ ] `"Zitat" - z. B. 10 %` ergibt in Word, PowerPoint und PDF `„Zitat“ – z. B. 10 %` mit
      geschützten Leerzeichen; Code-Spans und Codeblöcke bleiben wörtlich.
- [ ] `typografie: nein` lässt alles wie geschrieben; `plain_quotes` macht die Rundreise grün.
- [ ] Das PDF trennt deutsche Wörter nur an pyphen-Trennstellen, nie in Code; `blocksatz: ja`
      ergibt bündige Zeilen.
- [ ] Ein ```` ```python ````-Block ist in allen drei Formaten farbig im PTA-Schema; ohne Sprache
      einfarbig.

## Offene Fragen

1. Geschützter Bindestrich (U+2011) in Wörtern wie `E-Mail`, `IT-Beratung`, damit sie nicht am
   Bindestrich umbrechen? Vorschlag: nein — Word und PowerPoint zeigen U+2011 in manchen Schriften
   als Kästchen; nur das PDF könnte ihn gefahrlos setzen, dann aber ohne Nutzen in Word.

> (2026-11-07) Nein.

2. Blocksatz im PDF als Standard (klassischer Berichtsstil) oder aus (wie die Word-Vorlage,
   linksbündig)? Vorschlag: aus.

> (2026-11-07) Aus; `blocksatz: ja` schaltet ein.

3. Wo merkt sich das DOCX die Codesprache für die Rundreise — als unsichtbare Absatz-
   Eigenschaft (`w:pPr` Erweiterung, Word ignoriert sie) oder als erste Kommentarzeile im Code?
   Vorschlag: Absatz-Eigenschaft; der Konverter liest sie, Word stört sich nicht.

> (2026-11-07) Absatz-Eigenschaft.

## Notizen

- Abhängigkeiten: E05-S02 (Layout-Engine) für Silbentrennung; E02-S05 für den Guide-Abschnitt;
  E07-S02/S03 für `plain_quotes`.
- pyphen ist Tri-Lizenz GPL/LGPL/MPL; die MPL-Wahl macht es für das Repo unbedenklich, steht aber
  ausdrücklich in `pyproject.toml` (Kommentar) und `docs/verwendung.md`.

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08: Typografie und Code-Highlighting für Word und PowerPoint,
`plain_quotes` in beiden Konvertern, Codezäune mit Sprache aus dem DOCX zurück. Der PDF-Teil
(Silbentrennung, Blocksatz, `blocksatz`/`silbentrennung`, farbiger Code in Mono,
`PdfOptions.typography`) folgt mit **E05-S02** (dort in den Notizen vermerkt) — es gibt noch
keinen PDF-Generator; pyphen ist deshalb noch nicht eingetragen.

### Entscheidungen

- `markdown/typography.py`: `typeset(tokens, language)` als Durchgang **nach** dem Parsen und
  nach `layout_syntax.check` (nicht als Core-Regel im gemeinsamen Parser), damit Prüfungen und
  Konverter-Tests den rohen Text sehen; die Generatoren rufen es auf, wenn
  `options.typography` (Front Matter `typografie`, Standard ja). Es ändert nur `text`-Kinder von
  `inline`-Token sowie Alt-Text/Titel von Bildern; Code-Spans, Codeblöcke, Link-Ziele,
  Autolinks, rohes HTML und das Front Matter bleiben. Anführungszeichen schauen über Kinder
  hinweg (`"**fett**"`).
- Der Attribut-Block am Ende einer Überschrift (`{kicker="Warum"}`) bleibt roh, sonst würden
  seine `"` zu „“ und die Attribute nicht mehr erkannt; der Kicker-Text selbst wird deshalb
  nicht gesetzt.
- Status-Labels aus dem Front Matter werden mit `typeset_text` genauso gesetzt, sonst fänden sie
  gesetzte Tabellenzellen (`Ziel: 100 %`) nicht mehr.
- Apostroph im Wort und nach einem Wort ohne offenes `'` wird `’` (U+2019).
- Geschützte Leerzeichen: Abkürzungen als allgemeine Regel „ein Buchstabe mit Punkt, dann ein
  bis zwei Buchstaben mit Punkt" (`z. B.`, `i. d. R.`, `z. Hd.`), feste Liste vor Zahlen (`Nr.`,
  `S.`, `Abs.`, `Art.`, `Kap.`, `Abb.`, `Tab.`, `Ziff.`, `§` …), feste Einheitenliste nach
  Zahlen (`%`, `€`, `km`, `GB`, `Mio.` …, in `de` und `en`), Tag + Monatsname.
- U+202F wird nie gesetzt (Plan: nur, wenn die Schrift es hat) — Word und PowerPoint nutzen
  Office-Schriften, deren Abdeckung hier nicht prüfbar ist; immer U+00A0. Kein U+2011
  (Frage 1).
- Code-Highlighting `generation/common/code_highlight.py`: Pygments als Kernabhängigkeit
  (BSD-2-Clause, Kommentar in `pyproject.toml`); `Keyword.Constant`/`Name.Constant` zählen als
  Konstanten (`404040`), `Operator.Word` (`and`, `in`) als Schlüsselwort; Leerzeichen hängen am
  Span davor. Hinweis `code-language-unknown` (neu in `NoteCodes`) nur bei angegebener,
  unbekannter Sprache und nicht für `mermaid`/`chart`/`financial-chart` (die haben
  `code-not-drawn`), und nicht bei abgeschalteter Hervorhebung.
- DOCX: Farben/fett/kursiv als direkte Run-Formatierung in der Formatvorlage „Code"; die
  Fence-Info (ganze Info-Zeile, nicht nur das erste Wort) steht als
  `<pta:codeLanguage pta:val="…"/>` im `w:pPr` (Frage 3). Damit Word das unbekannte Element
  ignoriert, deklariert `declare_own_namespace` den Namensraum am `w:document` und trägt `pta` in
  `mc:Ignorable` ein (nur, wenn ein Codeblock eine Sprache hat).
- Der DOCX-Konverter gab Codeblöcke bisher als gewöhnliche Absätze aus; er erkennt jetzt die
  Vorlage „Code" am Namen und gibt einen Zaun mit der gespeicherten Sprache aus (Umbrüche als
  Zeilen, ohne Markdown-Escape). Der PPTX-Konverter erkennt Codefelder weiterhin nicht.
- `ConversionOptions.plain_quotes` (Standard aus) wirkt auf das fertige Markdown außerhalb von
  Zäunen und Code-Spans: `„“”` → `"`, `‚‘’` → `'`, `–` → `-`, `…` → `...`, U+00A0/U+202F →
  Leerzeichen (`typography.plain`). `…` zusätzlich zum Plan, weil die Typografie `...` ersetzt.
- Die Rundreise-Erwartungen (`*.roundtrip.expected.md`, DOCX und PPTX) sind einmal erneuert:
  geschützte Leerzeichen vor `%`, `€`, `GB` und die neuen Codezäune im DOCX.
- Tests, die gesetzten Text oder einfarbigen Code prüften, sind angepasst, nicht abgeschwächt:
  `test_no_direct_font_size_or_colour_except_code` erlaubt Farben nur in „Code"-Absätzen,
  `test_code_box` prüft den Zeilentext über die Runs, `test_each_block_lands_in_its_style`
  erwartet `100 %` mit U+00A0.

### Warnungen

- **Warnung:** Der Front-Matter-Schlüssel heißt `syntaxhervorhebung` statt `highlight` aus dem
  Plan — Front-Matter-Schlüssel sind im Repo deutsch (Entscheidungen 2026-11-06/07). Bitte
  bestätigen oder umbenennen (`Keys.HIGHLIGHT`).
- **Warnung:** Das Öffnen in Word mit `pta:codeLanguage` + `mc:Ignorable` ist nicht geprüft
  (kein Word auf der Maschine). Nach MCE-Spezifikation korrekt; Word verwirft das Element beim
  Speichern, ein in Word gespeichertes DOCX verliert die Sprache also.
- **Warnung:** Typografie ist standardmäßig an (Epic-Frage 2): jeder bestehende Text mit
  `"…"`, ` - `, `...` oder `10 %` sieht in Word/PowerPoint jetzt anders aus, und Konverter geben
  die gesetzten Zeichen zurück, solange `plain_quotes` aus ist.
- **Warnung:** Die Abkürzungsregel ist allgemein und kann selten zu viel schützen (z. B.
  „Plan B. Da." → geschütztes Leerzeichen nach „B."); das verhindert nur einen Umbruch.

### Prüfpunkte

- `samples/funktionen/` zeigt Typografie (Bericht, Abschnitt „Code, Zitat und Trennlinie") und
  farbigen Python-Code in beiden Formaten: `./run.sh generate-samples funktionen`.
- Word und PowerPoint öffnen: Farben im Codeblock, geschützte Leerzeichen (Formatierungszeichen
  einblenden), „…“ in Überschriften und Tabellen.

### Offene Punkte

- PDF-Teil → E05-S02 (siehe dort). Guide-Abschnitt „Typografie" → E02-S05 (dort vermerkt).
- `sprache: en` hat keine englische Abkürzungsliste (Plan); `e.g.` bleibt wie geschrieben.
