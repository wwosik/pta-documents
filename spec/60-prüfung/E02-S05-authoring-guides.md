# E02-S05 Authoring Guides

> Status: in Prüfung
> Epic: [E02 Markdown-Grundlagen der Generatoren](../50-entwurf/E02-markdown-grundlagen.md)
> Milestone: [M04 Präsentieren und Schulung](../50-entwurf/M04-praesentieren-und-schulung.md)

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

- [x] Die Bausteine sind getestet und hängen von keinem Extra ab.
- [x] Ein Generator kann seinen Guide aus Vorlage + Bausteinen erzeugen, ohne Schlüssel- oder
      Syntaxlisten zu wiederholen.
- [x] `./run.sh authoring-guide <format>` gibt den Guide aus, sobald der Generator ihn anbietet.

## Offene Fragen

1. Die Guides sind deutsch. Sollen sie zusätzlich auf Englisch erzeugt werden können (z. B.
   `authoring_guide(options, language=Language.EN)`), etwa für englischsprachige Agenten oder
   Kollegen — oder genügt Deutsch (Vorschlag)?

> (2026-11-07) Nur Deutsch.

## Notizen

- (2026-11-07, E08-S01) Der Abschnitt „Hinweise, die zurückkommen können" listet `NoteCodes.ALL`
  (`generation/common/result.py`); die Tabelle in `docs/verwendung.md` (Hinweise) ist die Vorlage.
- (E17-S02, docs-2) Die Guides bekommen einen Abschnitt „Typografie": gerade Anführungszeichen
  schreiben, die Generatoren setzen sie (Liste der Ersetzungen in `docs/verwendung.md`,
  *Typografie und Code*); Code, Links und Front Matter bleiben unberührt; `typografie: nein`;
  Codeblöcke mit Sprache werden farbig (`syntaxhervorhebung: nein`, Hinweis
  `code-language-unknown`).

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08: Bausteine `src/pta_documents/generation/common/authoring_guides.py`,
Werkzeug `tools/authoring-guide/authoring-guide.py` (`./run.sh authoring-guide docx|pptx|pdf`),
Testhilfen `tests/generation/guides.py`, Tests `tests/generation/common/test_authoring_guides.py`
mit der Testvorlage `tests/generation/common/authoring_guide/beispiel.md`, neuer Test in
`tests/samples/test_funktionen.py`. Doku: `docs/verwendung.md` (Abschnitt „Authoring Guides",
Punkt unter „Beispiele"), `ai/Gedächtnis.md`; Hinweise für die Folge-Stories in deren Notizen
(E03-S05, E04-S06, E05-S05).

### Entscheidungen

- **Bausteine wie geplant**, deutsch: `template`, `fill` (fehlender Wert = `KeyError`, drei und
  mehr Zeilenumbrüche werden zu einer Leerzeile, Ergebnis endet mit genau einem Umbruch),
  `front_matter_section(keys, valid, example)` mit `GuideKey(key, values, meaning)`,
  `characters_section` (Port von `Characters`/`Symbols`), `renderers_section`,
  `layout_syntax_section(format, effect)`, `words`. Über den Plan hinaus, weil die Notizen der
  Story (E08-S01, E17-S02) und die Folge-Stories sie verlangen und sie sonst je Guide doppelt
  entstünden: `notes_section(format)` (aus `NoteCodes.ALL`), `typography_section()`,
  `icons_section(format)` (aus `design.icons.ICONS`), `image_formats` (Port von `ImageFormats`),
  `names`/`choices`, `common_keys()` (Zeilen, die in allen Formaten gleich sind),
  `named_syntax`/`named_keys` mit `SYNTAX_PATTERN`/`KEY_PATTERN`.
- **Guide und Code laufen nicht auseinander:** `front_matter_section` wirft `ValueError`, wenn die
  Zeilen nicht genau `VALID_KEYS` beschreiben; die Texte zur Syntax stehen in Tabellen je Name
  (`CONTAINER_TEXTS`, `ALERT_TEXTS`, `STATUS_TEXTS`, `ATTRIBUTE_TEXTS`, `MARKER_TEXTS`,
  `NOTE_TEXTS`), ein Test vergleicht sie mit `layout_syntax`, `heading_attributes.VALID`,
  `block_markers.NAMES`, `StatusCategory` und `NoteCodes.ALL`. Ob ein Attribut an `#` oder `##`
  steht, kommt aus `VALID_ON_SECTION`/`VALID_ON_SLIDE`.
- **Guide und Beispiele laufen nicht auseinander** (Notiz E08-S03): `test_funktionen.py` hat
  `test_the_samples_show_the_syntax_the_guide_names` — Port des vt-tools-libs-Tests
  `TheTour_ShowsEverythingTheGuidesName`: jede Syntax, die der Guide nennt (Regex wie dort,
  `{.?` statt `{[.#]?`), steht wortgleich in den Beispielen des Formats. Bis die Generatoren
  Guides haben, liest der Test die gemeinsamen Abschnitte (`guide_syntax`: Folien-Syntax und der
  Chart-Abschnitt). Der bisherige Token-Test aus den Code-Listen bleibt; zusammen schließen sie
  das Dreieck Guide ↔ Code ↔ Beispiele.
- Damit das für Word und PDF aufgeht, nennt `layout_syntax_section` dort, was nur für Folien gilt
  (`notes`, im Word auch `scene`; Attribute außer `.internal`/`.appendix`; Blockmarker außer
  `{.internal}`), als bloße Namen ohne `:::`/`{`; im Deck steht `.appendix` so.
- Das Werkzeug ruft `authoring_guide()` des Generators mit Standardoptionen, sobald es die
  Methode gibt; vorher Code 1 mit Meldung, falsche Argumente Code 2. Die PDF-Klasse wird erst bei
  `pdf` importiert (Extra).
- Offene Frage 1 (Englisch): nein, nur Deutsch, wie beantwortet.

### Abweichungen

- **Warnung:** `docs/ki-anleitung.md` bleibt unverändert, auch die vollständige Icon-Liste
  (E15-S03). Solange kein Generator einen Guide anbietet, hätte ein Verschieben die Liste für
  Agenten in `documents/` verschwinden lassen. `icons_section` erzeugt sie für die Guides;
  E03-S05/E04-S06 können `ki-anleitung.md` dann auf `./run.sh authoring-guide` verweisen und den
  Test in `tests/design/icons/test_icons.py` mitziehen.
- **Warnung:** Die PTA-Folienarten (`.agenda`, `.interim`, `.quote`, `.contact`) stehen im
  Word-/PDF-Abschnitt nur als bloße Namen („gelten nur für Folien"), obwohl Word sie schlicht
  zeigt — der Word-Bericht der Funktionsübersicht zeigt sie nicht, und die Beispiele wollte ich
  in dieser Story nicht ändern (gemeinsame Dateien, Rundreise-Erwartungen). E03-S05 entscheidet.
- **Warnung:** Ersatz für `↑`/`↓` ist `hoch`/`runter` statt `up`/`down` (deutsche Guides).
- Die Vorlagen liegen in `<paket>/authoring_guide/<name>.md` wie geplant; E05-S05 nannte
  `generation/pdf/authoring_guide.md` — Notiz dort ergänzt.
- Das Werkzeug liegt als `tools/authoring-guide/authoring-guide.py` (Name mit Bindestrich wie im
  Plan); `run.sh`/`run.ps1` finden Werkzeuge von selbst, keine Änderung nötig.
- Epic- und Meilensteinkopf bleiben `Entwurf` wie bei den übrigen Stories dieses Ablaufs; nur
  die Zeilen der Scope-Tabellen stehen auf `in Prüfung`.

### Prüfpunkte

- Die deutschen Texte der Tabellen (`CONTAINER_TEXTS` …, `NOTE_TEXTS`) lesen — sie sind die
  Grundlage aller drei Guides.
- Wortbudget: Folien-Syntax für PowerPoint rund 700 Wörter, Icons rund 280; die Guides von
  E03-S05/E04-S06 müssen mit allem unter 2 500 bleiben.
- Testvorlage `tests/generation/common/authoring_guide/beispiel.md` zeigt, wie ein Guide aus
  Vorlage und Bausteinen entsteht; alle Beispiele darin erzeugen ein Word-Dokument ohne Hinweise.

### Offene Punkte

- E03-S05, E04-S06, E05-S05 schreiben die Guides; danach liest `guide_syntax` in
  `test_funktionen.py` den ganzen Guide (ohne die Fehlerbeispiele) und `./run.sh authoring-guide`
  gibt etwas aus.
- Stilhinweise (`StyleCodes`) haben noch keinen Abschnitt; bei Bedarf wie `notes_section`.
