# E17-S02 Deutsche Typografie, Silbentrennung, Code-Highlighting

> Status: Entwurf
> Epic: [E17 Qualität und Arbeitsfluss](E17-qualitaet-und-arbeitsfluss.md)

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
