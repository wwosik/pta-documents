# E02-S05 Authoring Guides

> Status: Entwurf
> Epic: [E02 Markdown-Grundlagen der Generatoren](E02-markdown-grundlagen.md)

## Zusammenfassung

Das gemeinsame Gerüst für die Authoring Guides: eine Markdown-Beschreibung für Schreiber (Menschen
und KI-Agenten), die jeder Generator aus seinen Optionen erzeugt — Struktur, Layouts, Front Matter,
Diagramme der eingeschalteten Renderer, Fehler und ein vollständiges Beispiel, das fehlerfrei
generiert. Die Guides selbst schreiben E03-S05, E04-S06 und E05-S05.

## Kontext

- DocLibs: `DocumentGeneration/AuthoringGuides.cs` (132 Zeilen): `Template` (eingebettete
  `AuthoringGuide/*.md`), `Fill` (`{{name}}`-Platzhalter, leere Platzhalterzeilen hinterlassen
  keine Leerzeilen), `FrontMatter` (Abschnitt mit Tabelle der Schlüssel), `Characters` (Symbole,
  die den Schriften fehlen, mit Ersatz), `Renderers` (Abschnitte der Renderer), `Words`.
  Vorlagen: `Pptx/AuthoringGuide/Pptx.md` (145 Zeilen), `Pdf/AuthoringGuide/Pdf.md` (87),
  `Charts.md` (53), `Diagrams.md` (24).
- DocLibs-Tests je Guide: jedes Beispiel generiert, unter 2 500 Wörtern, nennt jeden Container,
  jedes Alert, Attribut und jeden Schlüssel, den der Parser kennt, Abgleich mit
  `authoring-guide-*.expected.md`.
- Hier: Was der Schreiber liest, ist deutsch (Standards), also auch die Guides; Brand-Auswahl
  (`template:`) entfällt, an ihre Stelle tritt `vorlage:`.

## Vorgeschlagener Ansatz

1. `src/pta_documents/generation/common/authoring_guides.py`:
   - `template(package, name) -> str` liest `<package>/authoring_guide/<name>.md` über
     `importlib.resources` (Zeilenenden normalisiert);
   - `fill(template, values) -> str` — Port von `Fill`, unbekannter Platzhalter ist ein
     Programmierfehler (`KeyError`), drei und mehr Leerzeilen werden zu einer;
   - `front_matter_section(keys: Sequence[GuideKey]) -> str` mit
     `GuideKey(key, values, meaning)`; die Tabelle entsteht aus der Liste gültiger Schlüssel des
     Generators, damit Guide und `check_keys` nicht auseinanderlaufen; Syntaxabsatz und Hinweis
     „unbekannter Schlüssel ist ein Fehler" auf Deutsch, Wahrheitswerte `ja`/`nein`;
   - `characters_section(has_text_glyph, has_code_glyph, intro) -> str` — Port von `Characters`
     samt der Symboltabelle (✓ → `[x]`, → → `->` …); nur das PDF braucht ihn (E05-S05), weil
     Word und PowerPoint die installierte Schrift nehmen;
   - `renderers_section(renderers)` aus `CodeBlockRenderer.authoring_guide` (E02-S04);
   - `layout_syntax_section(format)`: der gemeinsame Teil „Folien-Syntax" mit den Namen aus
     `layout_syntax.CONTAINERS`/`ALERTS` und `heading_attributes.VALID` (E02-S02), den jeder
     Guide mit einem formatspezifischen Satz („in Word schlicht dargestellt", „auf Folien als …")
     ergänzt;
   - `words(guide) -> int` (Folgen von Buchstaben/Ziffern).
2. Testhilfen in `tests/generation/guides.py`: `examples(guide)` holt alle ```` ```markdown ````-
   Blöcke; `assert_examples_generate(guide, generate)`; `assert_names_everything(guide, names)`;
   `assert_under(guide, 2500)`; Abgleich mit `*.expected.md` über `tests/expected.py`
   (`PTA_DOCUMENTS_UPDATE_EXPECTED=1`).
3. Werkzeug `tools/authoring-guide/authoring-guide.py` (`./run.sh authoring-guide docx|pptx|pdf`):
   schreibt den Guide mit Standardoptionen auf die Standardausgabe — zum Weitergeben an Schreiber
   ohne Python.
4. Tests für das Gerüst selbst: `fill` (Platzhalter allein in einer Zeile mit leerem Wert hinterlässt
   keine Leerzeile; fehlender Wert wirft), `front_matter_section` listet jeden übergebenen Schlüssel,
   `characters_section` mit erfundenen Glyphenfunktionen (fehlt im Text, fehlt nur im Code, alles
   vorhanden → nur Einleitung), `words`.

## Akzeptanzkriterien

- [ ] Die Bausteine sind getestet und hängen von keinem Extra ab.
- [ ] Ein Generator kann seinen Guide aus Vorlage + Bausteinen erzeugen, ohne Schlüssel- oder
      Syntaxlisten zu wiederholen.
- [ ] `./run.sh authoring-guide <format>` gibt den Guide aus, sobald der Generator ihn anbietet.

## Offene Fragen

1. Die Guides sind deutsch. Sollen sie zusätzlich auf Englisch erzeugt werden können (z. B.
   `authoring_guide(options, language=Language.EN)`), etwa für englischsprachige Agenten oder
   Kollegen — oder genügt Deutsch (Vorschlag)?

> (2026-11-07) Nur Deutsch.

## Notizen
