# Projektgedächtnis

Gesammelte Fakten zu dieser Codebasis: getroffene Entscheidungen, verwendete Muster, Fallen, die
man sich merken sollte. Gemeinsam hier statt im geräte-lokalen Gedächtnis irgendeines Werkzeugs,
damit jeder Agent auf jedem Rechner dasselbe liest.

Sachlich und aktuell halten. Was hier steht und nicht mehr stimmt, wird in derselben Änderung
korrigiert, die es unwahr gemacht hat — ein veralteter Eintrag ist schlimmer als ein fehlender,
weil ihm vertraut wird.

## Überblick

- Angelegt am 2026-11-06 aus dem Katalog `projekt-init` (`core`, `spec-workflow`). Der Katalog
  hat keine Python-Komponente; die Python-Konventionen kommen mit
  `spec/50-entwurf/T01-S01-python-projektgeruest.md`.
- Eigenständig weitergeführte Python-3-Portierung von DocLibs (.NET, `wwosik/doc-libs`, Stand
  Release `2610.28.22`). Es gibt keine Rückportierung und keinen Abgleich mit dem Original.
- Analysen in `spec/10-analysen/`, Pläne in `spec/50-entwurf/`, Reihenfolge in
  `M01-pta-dokumente-aus-markdown.md`.
- **Stack:** Python ≥ 3.12, venv + pip (kein uv), hatchling, pytest, ruff, pyright strict.
  Kern: python-docx, python-pptx, lxml, markdown-it-py + mdit-py-plugins, Pillow. Extras:
  `pdf` (reportlab, pikepdf, pdfplumber), `svg` (resvg-py), `diagrams` (mermaid-cli, extern).
- **Paketstruktur** (`src/pta_documents/`): `errors.py` (`DocumentConversionError`,
  `DocumentFormat`), `markdown/` (Dokumentmodell, Front Matter, Parser), `design/`
  (Designmodell, eingebettete Vorlagen), `conversions/` (→ Markdown), `generation/`
  (`common/`, `docx/`, `pptx/`).
- **Stand 2026-11-06:** M01 umgesetzt (alle Stories in `spec/60-prüfung/`): DOCX- und
  PPTX-Generator auf den PTA-Vorlagen, DOCX-/PPTX-Konverter, Front Matter, Designmodell,
  eingebettete Vorlagen. PDF, Diagramme/Charts und PDF-Konverter sind nur geplant; die
  Folien-Syntax wird seit E02-S02 gelesen und geprüft, PowerPoint zeichnet sie seit E04-S03 als
  Flow-Folien, seit E04-S04 auch Agenda, Zwischenfazit, Zitat, Kontakt und Charts in den
  Diagrammlayouts (ohne `chart`-Renderer bis E06-S01); Word noch nicht (E03-S03). Bedienung:
  `docs/verwendung.md`.
- **Zweite Referenz:** `~/mvv/vt-tools-libs` (Schwesterbibliothek von DocLibs für die MVV,
  .NET) ist seit DocLibs `2610.28.22` weitergegangen — Hinweise an den Schreiber
  (`GenerationResult`), Sprechernotizen, Builds, Übergänge, Szenen, HTML-Decks,
  `make_document`, Feature-Tour. Abgleich: `spec/10-analysen/2026-11-07 abgleich-vt-tools-libs.md`;
  daraus die Epics E08–E10. E11–E17 sind eigene Ideen (Bausteine, Dokumentpflege, lange
  Berichte, Dokumenttypen der Beratung, visuelle Bausteine, Schulung, Arbeitsfluss), alle Stand
  2026-11-07 im Entwurf und vom Menschen zur Umsetzung gewünscht; E08-S04 ist zurückgestellt.
- **Umsetzungsreihenfolge** nach M01: Meilensteine M02 (Rückmeldung, Folien-Syntax) → M03
  (Grafik, Charts) → M04 (Präsentieren, Schulung, Guides) → M05 (PDF) → M06 (Inhalte,
  Dokumentpflege); jede der 59 offenen Stories nennt ihren Meilenstein im Kopf.
- **Vorgaben für die Umsetzung von M02–M06 (2026-11-07):** Agent `docs-2`, ohne Zwischenprüfung;
  nur lokal committen (Push macht der Mensch); neue Abhängigkeiten nur mit freizügiger Lizenz
  (MIT, BSD, Apache, OFL) und als Extra, wo der Plan es vorsieht; fehlt eine Entscheidung,
  die vorsichtigste vernünftige wählen und als Warnung in den Implementierungsnotizen festhalten.
- **Werkzeugverben und Schalter sind englisch** (`generate`, `check`, `preview`, `compare`,
  `--strict`), Front Matter und Anleitungen deutsch, Markdown-Syntaxnamen englisch
  (Entscheidung 2026-11-07).
- Erzeugte Beispieldateien zum Ansehen schreiben die Tests nach `.tmp/review/`. Auf der
  Entwicklungsmaschine gibt es weder Word/PowerPoint noch LibreOffice; das Öffnen in Office ist
  ein offener Prüfpunkt der Stories.

- **Hinweise an den Schreiber** (E08-S01): `generate()` beider Generatoren gibt
  `GenerationResult(notes, slides, pages)` zurück (`generation/common/result.py`, auch aus
  `pta_documents` importierbar). Neue Umgehungen melden mit `Notes.add(NoteCodes.X, line, msg)`
  — der Sammler wird in `generate()` angelegt und an Parser und Writer übergeben; neue Codes in
  `NoteCodes` (und `ALL`) eintragen und in `docs/verwendung.md` aufführen. `samples/` muss ohne
  Hinweise erzeugen (Tests `test_the_samples_generate_without_notes`).

- **Renderer und Bildkonverter** (E02-S04): `generation/common/renderers.py`
  (`CodeBlockRenderer`, `render`, `default_renderers`) und `images.py` (`ImageConverter`,
  `convert_image`, `default_converters`, Maßstab `GENERATOR_SCALE = 2`). Optionen
  `code_block_renderers`/`image_converters` nutzen die `default_*`-Funktionen als
  `default_factory` (Entscheidung: standardmäßig an, wenn verfügbar; `()` schaltet ab) — neue
  Renderer/Konverter der Bibliothek dort eintragen. Fences laufen in beiden Generatoren über
  `code_blocks.draw` (notiert `code-not-drawn` nur, wenn nichts gezeichnet hat); PPTX konvertiert
  Bilder im Parser (`DeckParser._placeable`), DOCX in `BodyWriter.place_picture`.

## Entscheidungen

- **Entscheidungen des Menschen vom 2026-11-06:** Projektsprache Deutsch; portiert wird alles
  außer `DocumentConversions.WindowsOnly` (Office-COM); zusätzlich ein DOCX-Generator auf den
  PTA-Word-Vorlagen; erst Analysen und Pläne, umgesetzt wird nach Annahme der Pläne.
- **Nur das PTA-Design.** Die Standardvorlagen von DocLibs (neutraler Brand, Brand-Packs,
  eingebauter Folienmaster, fremde Vorlagen) entfallen; die Standards stammen aus
  `source-templates/` (siehe `spec/10-analysen/2026-11-06 pta-designstandards.md`).
- **Weitere Entscheidungen vom 2026-11-06** (Einzelheiten in den Plänen und unter
  *Entscheidungen* in `spec/10-analysen/2026-11-06 portierung-doclibs-python.md`): keine
  Veröffentlichung, ein Paket mit Extras, Python ≥ 3.12, vorerst kein Remote/CI; PDF über eine
  portierte Layout-Engine mit Selawik/Segoe UI; Mermaid über mermaid-cli; JIRA-Wiki entfällt;
  BPS-PTA-DATIS ist keine Variante; Front Matter deutsch; in Word und PDF ist `#` „Überschrift 1",
  in Folien die Titel- bzw. Trennfolie.

## Fallen

- Die PTA-Folienlayouts haben kein `type`-Attribut — nur über den Namen auffindbar. Das
  Abschlusslayout heißt `Abbschlussfolie` (sic).
- Mehrere Folienlayouts zeichnen Eckklammern, Linien und Logo über unsichtbare Platzhalter
  (Aufforderung „x"); sie müssen auf jeder Folie leer angelegt werden.
- Word und PowerPoint der PTA unterscheiden sich: Text `000000` vs. `404040`, Tabellenkopf
  `006FB9` vs. `004676`.
- Die Querformat-Word-Vorlagen haben die Formatvorlagen `Hyperlink`, `toc 1`, `toc 2` nicht; sie
  werden aus der Hochformat-Vorlage übernommen (`design/word.py`, `BORROWED_STYLES`).
- Stilnamen in `styles.xml` sind die internen englischen (`heading 1`, `List Bullet`,
  `caption`); nur eigene Formatvorlagen der PTA heißen deutsch (`Autor`, `Standard fett`,
  `Zwischenüberschrift`, `PTA`).
- python-pptx: `itertext()` auf seinen Elementen liefert Text mehrfach — Text immer über die
  `a:t`-Elemente lesen.
- python-pptx legt Fußzeilen- und Foliennummer-Platzhalter beim Anlegen einer Folie nicht an;
  der Generator kopiert sie aus dem Layout.
- Der gemeinsame Markdown-Parser (`markdown/parser.py`) hat seit E08-S01 `html: True`: rohes HTML
  kommt als `html_block`/`html_inline` an und wird von den Generatoren weggelassen (Hinweis
  `raw-html`). Ausnahmen in `generation/common/html.py`: Kommentare still weg, `<br>` = Umbruch
  (die Konverter schreiben `<br>` in Tabellenzellen), die Checkbox des Tasklist-Plugins.
- Inline-Token haben kein eigenes `map`-Feld pro Kind; die Zeile eines Kindes liefert
  `markdown.parser.child_lines(inline, offset)` (zählt Soft-/Hardbreaks).
- **Folien-Syntax** (E02-S02): Der Parser nimmt Container **jedes** Namens an (Token
  `container_layout_open`, Name/Argumente über `markdown.parser.container(token)`); gültige Namen
  prüft erst `layout_syntax.check`, das beide Generatoren vor dem Schreiben aufrufen. Neue
  Container, Alerts oder Heading-Attribute dort bzw. in `heading_attributes.py` eintragen (eine
  Stelle für alle Formate). `==mark==` ist eine eigene Inline-Regel (`markdown/mark.py`) —
  mdit-py-plugins hat keine. Fehler dieser Prüfung beginnen mit `Line N: `; ältere Meldungen des
  PPTX-Parsers hängen `(line N)` an.
- **Flow-Folien** (E04-S03): `generation/pptx/flow_parser.py` (`FlowReader`, arbeitet auf
  Token-Bereichen: `block_end`/`children`) liest, `flow.py` (`FlowWriter`) zeichnet; jede
  Methode misst, mit Folie (`FlowWriter(deck, slide)`) zeichnet sie auch — Messen und Zeichnen
  nie getrennt implementieren. Alle Maße in `design/slides.py` (`FLOW`, `CONCLUSION`, `COMMENT`,
  `grid`, `COLUMN_GUIDES`). Folien beginnen nur an `#`/`##` auf Token-Ebene 0 — eine
  Überschrift in einem Container oder Zitat startet keine Folie. Aufbaufehler beginnen wie
  `layout_syntax.check` mit `Line N: ` (`layout_syntax.at_line`).
- Der Test `test_no_colour_values_outside_the_colour_module` verbietet jede Zeichenkette aus
  sechs Hex-Ziffern außerhalb von `design/colors.py` — auch Zahlen wie `"100000"` in XML-Attributen
  (als `int` schreiben und mit `str()` setzen).
- Farbige Wörter werden auf **Token-Ebene** zerlegt (`layout_syntax.coloured`: Textkinder mit
  `meta[STATUS]`), bevor ein Writer Runs baut — so maskieren Softbreaks und Code, auch wenn ein
  Writer einen Softbreak später als Leerzeichen schreibt.
- **PTA-Folienarten** (E04-S04): `{.agenda}`, `{.interim}`, `{.quote}`, `{.contact}` sind
  `HeadingAttributes.kind` (`heading_attributes.SLIDE_KINDS`); PPTX liest sie in
  `generation/pptx/kind_parser.py`, schreibt sie in `kinds.py` (auch `ChartSlide`). Layouts je
  Art in `design/slides.KIND_LAYOUTS`. `Agenda`- und `Zitat`-Layouts haben keine
  Fußzeilen-Platzhalter. Die Agenda-Trennlinien sind dekorative Platzhalter („x"): `finish`
  lässt sie stehen, `write_agenda` entfernt die unter dem letzten Punkt selbst.
- **Charts auf Folien** (E04-S04): PPTX nimmt Fences über `code_blocks.render_graphic` (alle
  Grafikarten) statt `draw`; `ChartGraphic` wird `model.Chart` und landet über
  `generation/pptx/chart.insert_chart` nativ im Diagrammplatzhalter. Zeichnungen werfen weiter
  (`code_blocks.unsupported`). Word nutzt noch `draw` (wirft für Charts bis E06-S01).
- python-docx zeigt Stilnamen als UI-Namen („Heading 1"); verglichen wird mit dem `w:name` aus
  `styles.xml` („heading 1").
