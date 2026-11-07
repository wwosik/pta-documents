# E11-S01 Variablen: Platzhalter aus Front Matter und Kommandozeile

> Status: Entwurf
> Epic: [E11 Bausteine, Variablen und Datenquellen](E11-bausteine-variablen-datenquellen.md)

## Zusammenfassung

`{{kunde}}` im Markdown-Text wird vor dem Erzeugen durch einen Wert ersetzt, der aus dem Front
Matter (`variablen.kunde: Muster AG`), von der Kommandozeile (`--var kunde="Muster AG"`) oder aus
eingebauten Werten (`{{heute}}`, `{{titel}}`) kommt. Ein Angebotstext lässt sich so für den
nächsten Kunden erzeugen, ohne ihn anzufassen.

## Kontext

- `markdown/front_matter.py` liest eine flache YAML-Teilmenge ohne Listen; `status.<kategorie>`
  ist bereits ein Schlüssel mit Präfix (`Keys.STATUS_PREFIX`, `check_keys(allow_status=True)`,
  `status_labels()`). `variablen.<name>` folgt demselben Muster.
- `MarkdownDocument.metadata` (`markdown/document.py`) trägt heute Titel und Autor aus den
  Konvertern; die Generatoren lesen daraus. Variablen von der Kommandozeile passen dort hinein.
- `tools/generate/generate.py` kennt nur `--docx`, `--pptx`, `--out`.
- Code-Spans und Codeblöcke dürfen `{{…}}` enthalten (Vorlagensprachen, Helm, Ansible) — sie
  bleiben unberührt. Der Parser (`markdown/parser.py`) liefert `code_inline`- und `fence`-Token
  mit `map`, sodass die Ersetzung zeilengenau an ihnen vorbei kann.

## Vorgeschlagener Ansatz

1. **Modul** `src/pta_documents/markdown/variables.py`:
   - `PATTERN = re.compile(r"\{\{\s*([a-z][a-z0-9_-]*)\s*\}\}")` — Namen klein, wie Front-Matter-
     Schlüssel;
   - `substitute(text: str, values: Mapping[str, str], format, line_offset) -> str` ersetzt
     außerhalb von Codeblöcken (Zäune ``` und ~~~, gleiche Erkennung wie `GenerationNotes.
     Characters` in vt-tools-libs) und Code-Spans; ein unbekannter Name wirft
     `DocumentConversionError`: „Line 14: the variable '{{kunde}}' has no value. Define
     'variablen.kunde: …' in the front matter or pass --var kunde=…. Known: heute, titel, …";
   - `\{{` schreibt ein wörtliches `{{` (Escape wie bei Markdown-Sonderzeichen).
2. **Werte** in `FrontMatter.variables() -> dict[str, str]` aus `variablen.<name>`-Schlüsseln
   (Präfix `Keys.VARIABLES_PREFIX = "variablen."`; `check_keys` bekommt `allow_variables`);
   Reihenfolge: eingebaute Werte < Front Matter < `metadata` (Kommandozeile gewinnt, damit ein
   Skript den Front-Matter-Standard überschreiben kann).
3. **Eingebaute Werte:** `heute` (Datum im Format der Sprache, `06.11.2026` / `2026-11-06`),
   `titel`, `untertitel`, `autor` aus dem Front Matter; Liste in `variables.BUILT_IN`, damit
   Authoring Guide (E02-S05) und Fehlermeldung dieselbe Quelle haben.
4. **Einbindung:** `DocxGenerator.generate` und `PptxGenerator.generate` rufen `substitute` auf
   `front.body` auf, bevor der Parser läuft — Zeilennummern bleiben gleich, weil `{{…}}` nie
   einen Zeilenumbruch enthält. Front-Matter-Werte selbst werden ebenfalls ersetzt, außer
   `variablen.*` (Frage 2 im Epic).
5. **Werkzeug:** `generate.py` nimmt `--var name=wert` (mehrfach) und legt die Werte als
   `MarkdownDocument.metadata["variablen.<name>"]` ab; `docs/anleitung.md` und
   `docs/ki-anleitung.md` beschreiben `--var`.
6. **Tests** `tests/markdown/test_variables.py`: Ersetzung, Code bleibt, Escape, unbekannter Name
   mit Zeile, Vorrang, eingebaute Werte; Rundreise-Tests für DOCX und PPTX mit einem Beispiel, das
   `{{kunde}}` im Titel, im Text und in einer Tabellenzelle hat.

## Akzeptanzkriterien

- [ ] `{{kunde}}` in Text, Überschrift, Tabelle und Front Matter wird in Word und PowerPoint
      ersetzt; in Code-Spans und Codeblöcken nicht.
- [ ] Ein unbekannter Name bricht mit Zeile, Name und den bekannten Namen ab.
- [ ] `--var` überschreibt `variablen.*`; `{{heute}}` folgt `sprache`.
- [ ] Das Rücklesen (E07) eines erzeugten Dokuments zeigt die Werte, keine Platzhalter.

## Offene Fragen

1. Soll ein Platzhalter **ohne** Wert statt eines Fehlers leer bleiben, wenn er mit `?` endet
   (`{{ansprechpartner?}}`)? Vorschlag: nein — Fehler sind sicherer, eine KI korrigiert sie
   sofort.

> (2026-11-07) Nein, immer Fehler.
2. Dürfen Werte Markdown enthalten (`variablen.hinweis: **wichtig**`)? Vorschlag: ja, weil die
   Ersetzung vor dem Parsen läuft; ein Wert mit Zeilenumbruch ist aber ein Fehler.

> (2026-11-07) Ja; ein Wert mit Zeilenumbruch ist ein Fehler.

## Notizen

- Abhängigkeiten: keine; E11-S02 nutzt dieselben Werte in Bausteinen.
