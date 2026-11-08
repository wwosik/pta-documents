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
  Kern: python-docx, python-pptx, lxml, markdown-it-py + mdit-py-plugins, Pillow, Pygments, segno. Extras:
  `pdf` (reportlab, pikepdf, pdfplumber, fontTools), `svg` (resvg-py, fontTools), `diagrams`
  (cssselect; mermaid-cli über Node.js in `tools/mermaid/`).
- **Paketstruktur** (`src/pta_documents/`): `errors.py` (`DocumentConversionError`,
  `DocumentFormat`), `markdown/` (Dokumentmodell, Front Matter, Parser), `design/`
  (Designmodell, eingebettete Vorlagen), `drawing/` (Zeichenmodell, SVG aus und nach
  `Drawing`), `diagrams/` (Mermaid), `conversions/`
  (→ Markdown), `generation/` (`common/`, `docx/`, `pptx/`).
- **Stand 2026-11-06:** M01 umgesetzt (alle Stories in `spec/60-prüfung/`): DOCX- und
  PPTX-Generator auf den PTA-Vorlagen, DOCX-/PPTX-Konverter, Front Matter, Designmodell,
  eingebettete Vorlagen. PDF, Diagramme/Charts und PDF-Konverter sind nur geplant; die
  Folien-Syntax wird seit E02-S02 gelesen und geprüft, PowerPoint zeichnet sie seit E04-S03 als
  Flow-Folien, seit E04-S04 auch Agenda, Zwischenfazit, Zitat, Kontakt und Charts in den
  Diagrammlayouts (`chart`-Blöcke seit E06-S01, auch nativ in Word; Finanzdiagramme seit
  E06-S02 als Formengruppe, Mermaid seit E06-S03 über mermaid-cli, beide in Word seit E03-S04
  als Bild); Word zeigt sie seit
  E03-S03 schlicht in eigenen Formatvorlagen. Bedienung:
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
  `code_blocks.render_graphic` (notiert `code-not-drawn` nur, wenn nichts gezeichnet hat;
  `code_blocks.draw`/`unsupported` nutzt nur ein Generator, der noch nicht alle Grafikarten
  setzt — derzeit keiner); PPTX konvertiert
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
  `generation/pptx/chart.insert_chart` nativ im Diagrammplatzhalter; Zeichnungen seit E06-S02
  als Formengruppe. Word nimmt seit E06-S01 ebenfalls `render_graphic`
  (`BodyWriter.draw`) und setzt Charts über `generation/docx/chart.add_chart`.
- **Folien-Syntax in Word** (E03-S03): `BodyWriter` legt eigene Vorlagen bei Bedarf an
  (`design/word.STYLES`: `Hinweis`, `Hinweis wichtig`, `Markierung`, `Status …`, Tabellenvorlage
  `Bildreihe`); Runs bekommen höchstens eine `rStyle` (Hyperlink vor Status vor Markierung).
  Überschriften in `:::`-Containern und Personen von `{.contact}` sind „Standard fett", nie
  „Überschrift 3". Der DOCX-Konverter erkennt die Vorlagen am Namen (`_Context.style_names`),
  nicht an der Style-ID. Fett aus einer Zeichenvorlage sieht `run.bold` nicht (`run.style.font`).
- python-docx zeigt Stilnamen als UI-Namen („Heading 1"); verglichen wird mit dem `w:name` aus
  `styles.xml` („heading 1").
- **Sprechernotizen** (E09-S01): `DeckParser._take_notes` entfernt jedes `::: notes` vor dem
  Lesen aus den Token und hängt die Absätze als `Slide.notes` (kw-only) an **alle** Folien der
  Überschrift; `DeckWriter.new_slide` schreibt sie (`generation/pptx/notes.py`). Wer neue
  Folienarten baut, muss dafür nichts tun, solange er `new_slide` nutzt. Word meldet
  `notes-dropped`.
- **Formaterkennung und Registry** (E07-S01): `pta_documents.conversions` exportiert `detect`,
  `ConverterRegistry`, `DocumentConverter` (Protocol), `ConversionOptions`, `convert`. Neue
  Konverter der Bibliothek in `ConverterRegistry.default()` (`conversions/registry.py`)
  eintragen; der PDF-Konverter wird über `PDF_CONVERTER_MODULE` lazy geladen und fehlt still,
  solange Modul oder Extra fehlen. Ablehnungsmeldungen stehen in `ConverterRegistry._rejection`.
  Die Testbeispiele `sample.doc/.xls/.xlsx/.rtf/.pdf` stammen aus `~/mvv/vt-tools-libs`; der
  Autor „VT-Tools" ist byte-gleich lang durch „PTA-Docs" ersetzt (OLE/PDF-Offsets bleiben).
- **Typografie und Code** (E17-S02): `markdown/typography.typeset(tokens, language)` setzt die
  Textkinder in place (Anführungszeichen, `–`, `…`, U+00A0) — beide Generatoren rufen es nach
  `layout_syntax.check` auf (`options.typography`, Front Matter `typografie`). Wer Text mit
  Front-Matter-Werten vergleicht (Status-Labels), muss sie mit `typeset_text` genauso setzen.
  Der Attribut-Block am Ende einer Überschrift bleibt roh — sonst bricht `kicker="…"`.
  Tests, die erzeugten Text mit `"`, ` - `, `%` o. ä. vergleichen, sehen die gesetzten Zeichen.
  Code-Highlighting: `generation/common/code_highlight` (Pygments, Kernabhängigkeit);
  `highlight_fence` notiert `code-language-unknown`. DOCX speichert die Fence-Info als
  `<pta:codeLanguage pta:val="…"/>` im `w:pPr` (Namensraum `urn:pta-documents:wordprocessingml`,
  `declare_own_namespace` deklariert ihn am Wurzelelement und trägt ihn in `mc:Ignorable` ein —
  Word öffnet sonst nicht); der DOCX-Konverter macht aus „Code"-Absätzen wieder Zäune.
- **Prüfbefehl und Stilregeln** (E08-S02): `generation/common/check.check(document, format,
  CheckOptions)` erzeugt probeweise in einen `BytesIO` (Fehler/Hinweise = die von `generate`) und
  hängt die Stilhinweise aus `style_rules.style_notes` an (Codes `StyleCodes`, `style-…`, nicht in
  `NoteCodes`). Neue Stilregeln dort eintragen, in `StyleCodes.ALL` und in `docs/verwendung.md`
  (Test prüft das). Front-Matter-Schlüssel `pruefung` (`Keys.CHECK`) steht in `VALID_KEYS` beider
  Generatoren, die ihn ignorieren — ein neuer Generator (PDF) muss ihn auch annehmen. `samples/`
  muss `check --strict` bestehen (`test_the_samples_pass_the_check_without_notes`).
- **Funktionsübersicht** (E08-S03): `tests/samples/test_funktionen.py` verlangt, dass
  `samples/funktionen/` jede Syntax, jeden Front-Matter-Schlüssel (`VALID_KEYS` je Generator,
  `status.<kategorie>`) und jede Vorlagenvariante (`vorlage`, `sprache`, `titelfolie`) zeigt —
  die Liste kommt aus dem Code (`layout_syntax`, `heading_attributes.VALID`, Enums). Wer etwas
  davon hinzufügt, ergänzt das Beispiel (Bericht: `##` + Satz + ```` ```markdown ````-Zaun +
  dasselbe als Ergebnis; Präsentation: Quelltext als Zaun in `:::: notes` am Ende der Folie),
  die `README.md`-Tabelle bei neuen Dateien, und erneuert die Rundreisen
  (`tests/samples/funktionen/*.roundtrip.expected.md`). Eine neue Variante = eine neue kleine
  `varianten-…-dokument.md`/`-folien.md`. Codeblöcke in `::: notes` schreibt der PPTX-Generator
  seit E08-S03 als Consolas-Zeilen, der Konverter liest sie als Zaun zurück, `check` zählt sie
  nicht als gesprochene Wörter. `generate-samples` kennt auch `-dokument`/`-folien`.
- **Schriften für PDF und SVG** (E01-S03): `pta_documents.design.fonts` (Unterpaket mit den
  `.ttf` und `OFL-*.txt` als Paketdaten) — `bundled()`, `resolve()`, `FontSet.width/has_glyph`,
  `CSS_*FAMILY`. fontTools nur in `fonts/truetype.py` und dort lazy; Kern und
  `design/__init__.py` dürfen das Modul nie importieren (Test). Selawik Regular/Bold sind die
  Release-Binärdateien 1.01 (über npm `@docx-editor.dev/fonts`), **Selawik Light ist aus der
  UFO-Quelle mit fontmake gebaut** (GitHub-Releases waren nicht erreichbar) — wird sie durch
  `selawkl.ttf` des Releases ersetzt, die SHA-256 in `tests/design/test_fonts.py` und im
  Modul-Docstring nachziehen. Selawik hat **kein U+00A0** (Typografie setzt es!): der
  PDF-Generator (E05) muss für fehlende Glyphen ausweichen. Segoe UI wird nur mit allen fünf
  Dateien (inkl. `segoeuil.ttf`) übernommen.
- **Logos** (E01-S04): `pta_documents.design.logos` (Unterpaket; SVG/PNG als Paketdaten daneben)
  — `Logo` (`WORD`, `SLIDES`, `SLIDES_PLAIN`), `svg()`, `png()`, `size()`, `aspect_ratio()`,
  `shapes()` (liest die eigene SVG-Teilmenge: nur `<path>` mit absolutem `M`/`L`/`C`/`Z`) und
  seit E02-S03 `drawing(logo, width=None)` (viewBox-Einheiten oder auf `width` CSS-Pixel
  skaliert). Erzeugt werden die Dateien von
  `prepare-templates` mit dem EMF-Leser `tools/prepare-templates/emf.py` (unbekannte Datensätze
  brechen ab); EMF-Farben werden über `LOGO_COLORS` im Werkzeug auf `design.colors` abgebildet
  (`026FB9` → PTA-Blau). Das Werkzeug braucht resvg (Extra `svg`) — auch für `--check`, das
  `test_embedded_templates_are_up_to_date` aufruft; PNGs werden nach Pixeln verglichen.
  `pyproject.toml`: pyright `extraPaths = ["src", "tools/prepare-templates"]` (ohne `src` verliert
  pyright die automatische Suche dort) und pytest `pythonpath`, damit `import emf` geht.
- **Zeichenmodell** (E02-S03): `pta_documents.drawing` (`model.py`, `svg_output.py` — der Name
  `svg.py` ist dem SVG-Leser von E06-S03 vorbehalten). Frozen-slots-Dataclasses mit Tupeln
  (`__post_init__` wandelt Listen), optionale Felder keyword-only; Segmente und Elemente sind
  Unions (`PathSegment`, `DrawingItem`) — Ausgaben verzweigen per `match`, eine neue Art
  (E15-S02: `ShapeKind.CHEVRON`/`PIE`) muss in jedem `match` ergänzt werden (pyright meldet
  fehlende Fälle über den Rückgabetyp). `to_svg` validiert Farben (`RRGGBB`) und Zahlen
  (endlich) mit `ValueError`. `SvgOptions` holt die CSS-Familien **lazy** aus `design.fonts`,
  damit Kern-Importe `design.fonts` nicht laden (`test_the_core_imports_neither_fonttools_nor…`
  importiert auch `drawing` und `design.logos`). `DrawingGraphic.drawing`/`ChartGraphic.drawing`
  sind jetzt `Drawing`. Im Paket `drawing/` darf keine Hex-Farbe stehen, auch nicht in
  Kommentaren (eigener, strengerer Test). Zum Ansehen: `.tmp/review/drawing.html` (Tooltips).
- **SVG-Bilder** (E06-S04): Paket `pta_documents.svg` (`sanitizer.clean`, `converter.to_png`/
  `natural_size`, `SvgImageConverter`, `is_svg`); resvg und `design.fonts` werden erst in
  `to_png` importiert. `images.default_converters()` trägt `SvgImageConverter` ein, wenn
  `find_spec("resvg_py")` etwas findet; `refusal_hint` nennt sonst das Extra. `ConvertedImage`/
  `Conversion` haben `svg` (das bereinigte SVG) — DOCX (`place_picture`) und PPTX
  (`visuals.attach_svg`, aus `draw_pictures` und `fill_picture`) hängen es über
  `generation/common/svg_blip.attach` als `asvg:svgBlip` an das PNG; das PPTX-`Image` trägt dazu
  `natural` und `svg` (kw-only), `picture_size` liefert die natürliche Größe. Neue Bildwege in
  PowerPoint müssen `attach_svg` aufrufen. resvg setzt **fehlende Schriftfamilien in `serif`** —
  darum zeigen `serif`, `sans-serif` und der Standard auf Selawik (Test vergleicht PNG-Bytes).
  Keine `image-enlarged`-Hinweise für SVG in PowerPoint. Samples: `images/plan.svg`,
  `images/plan-folie.svg`.
- **Charts** (E06-S01): `pta_documents.charts` (`parser.parse` → `ChartSpec`, Fehler
  `ChartBlockError(ValueError)` mit `Line N: ` der fehlerhaften Zeile; `drawing.draw`/`scale`/
  `format_number`). Der `ChartRenderer` liegt in `charts/renderer.py` und wird **nicht** aus
  `charts/__init__` importiert (Zirkel mit `generation.common.renderers`, das `charts.spec`
  importiert); `default_renderers()` importiert ihn in der Funktion. Er ist ein frozen
  Dataclass, damit `DocxOptions() == …` vergleicht. Einstellungen englisch (`type`, `title`,
  `unit`, `source`, `stacked`, Liste `parser.SETTINGS`); `;` in der Kopfzeile = Dezimalkomma.
  Typ, Daten und PTA-Stil der nativen Diagramme für **beide** Formate in
  `generation/common/native_chart.py` (`apply_style` auf einem python-pptx-`Chart`); Word baut
  das Chart-XML mit python-pptx (`pptx.oxml.parse_xml` + `Chart(chart_space, None)`) und hängt
  Teil und Arbeitsmappe selbst an (`generation/docx/chart.py`). Abgeleitete Farben nur über
  `colors.tint` (überlappende Flächen). Kein Rückweg zum `chart`-Block: der PPTX-Konverter
  lässt Diagramme weg, der DOCX-Konverter liest sie seit E03-S04 als Tabelle. `test_funktionen.py` verlangt jede Art, jede Einstellung und beide
  Trennzeichen in `samples/funktionen/`. Wer einen Test mit ```` ```chart ```` ohne gültige
  Daten schreibt, muss die Renderer abschalten (`code_block_renderers=()`).
- **Finanzdiagramme** (E06-S02): `pta_documents.charts.financial` (Port von DocLibs
  `Financial*.cs` aus `~/mvv/vt-tools-libs`, DocLibs selbst liegt nicht lokal): `model`
  (Dataclasses, `CHART_TYPES`), `options` (Kultur `de`/`de-DE`/`en`/`en-US`/`en-GB`, eigenes
  Zahlenformat `format_decimal`, deutsch mit Leerzeichen vor `%`: `5,2 %`), `canvas` (Achse,
  Urteilsfarben, Endbeschriftungen), je Diagramm ein Modul, `json_block` (**eigener JSON-Leser**
  mit Zeilen, Kommentaren und Komma am Ende; Schlüssel = Feldname in camelCase, Pflichtfeld =
  Feld ohne Standardwert; `to_json` schreibt, was `parse` gleich zurückliest). Farbrollen in
  `design/chart_colors.py` (nur `colors`-Werte und `colors.tint`). Der `ChartRenderer` nimmt
  auch `financial-chart` → `DrawingGraphic`; Kultur-Standard = `sprache:`. PowerPoint setzt
  `DrawingGraphic` über `generation/pptx/drawing.py` als Gruppe `Drawing <id>` (Modell-Visual
  `Diagram`, Inhaltsfläche wie Tabellen, nie vergrößert) — E06-S03 (Mermaid) nutzt denselben
  Schreiber; der PPTX-Konverter überspringt `Drawing`-Gruppen. Word setzt Zeichnungen seit
  E03-S04 als SVG-Bild. Schnappschüsse
  `tests/charts/financial/samples/*.expected.svg` (Testdaten `figures.py`, deutsch);
  `test_funktionen.py` verlangt im Deck jeden Typ und jede Option.
- **Mermaid** (E06-S03): `pta_documents.diagrams.mermaid` (`MermaidRenderer`, frozen
  Dataclass; `find_command`: Argument → `PTA_DOCUMENTS_MMDC` → `mmdc` im `PATH` → repo-lokal
  `tools/mermaid/node_modules/.bin/mmdc`, das `./run.sh setup` per `npm ci` installiert —
  `package.json`/`package-lock.json` dort, mermaid-cli 12.2.0, puppeteer 25.16.0).
  `default_renderers()` nimmt ihn nur, wenn `find_command()` etwas findet. Neu in
  `renderers.py`: `RendererUnavailableError` — der Block bleibt Code, `code_blocks.render_graphic`
  macht daraus `code-not-drawn` mit der Meldung (fehlendes mmdc/Chromium, Word). SVG → Drawing:
  `drawing/svg.py` (`to_drawing`, `SvgDrawingError(ValueError)`), `svg_geometry.py`,
  `svg_style.py` (`Cascade` mit `cssselect`, lazy importiert; Extra `diagrams`). Die SVG-Tags
  werden vor dem Lesen vom Namensraum befreit (sonst greifen Typselektoren nicht). Farben in
  `design/diagram_colors.py` (`theme_variables`, `theme_css`); **Attributselektoren im
  `themeCSS` brechen Mermaids `%%{init}%%`** (dann fällt alles auf `htmlLabels: true` und
  `foreignObject` zurück). `look: classic` ist Pflicht (Mermaid 12 nutzt sonst „neo" mit
  animierten Strichmustern). **Auf dieser Maschine** startet Chromium nur mit
  `PUPPETEER_EXECUTABLE_PATH` (z. B. Playwrights `chrome-headless-shell` unter
  `~/.cache/ms-playwright/`, puppeteer konnte ohne `unzip` keins laden) und
  `PTA_DOCUMENTS_PUPPETEER_CONFIG` auf eine Datei `{"args": ["--no-sandbox"]}`; ohne beide werden
  die Tests mit echtem mmdc übersprungen (`tests/diagrams/support.mermaid_works`), ebenso
  `samples/funktionen/mermaid-praesentation.md` in den Beispieltests (`drawable`). Aufgezeichnete
  SVGs je Typ in `tests/diagrams/samples/` (laufen immer); neu aufzeichnen mit
  `PTA_DOCUMENTS_UPDATE_EXPECTED=1` bei funktionierendem mmdc (Mermaids Ausgabe ändert sich
  von Lauf zu Lauf leicht). Wer einen Test mit ```` ```mermaid ```` und Standardoptionen schreibt,
  hängt vom Rechner ab — Renderer explizit setzen.
- **Grafiken in Word** (E03-S04): `BodyWriter.block` (Fall `fence`) → `draw` (alle Grafikarten)
  → `graphic_figure`: `ChartGraphic` nativ (`docx_chart.add_chart(…, width, height, …)`, Größe
  `chart_size`: Satzspiegelbreite, höchstens `design/word.CHART_HEIGHT_RATIO` = 5:8 hoch,
  gedeckelt bei `FIGURE_HEIGHT_SHARE` = 80 % der Satzspiegelhöhe), `DrawingGraphic` über
  `generation/docx/drawings.convert` (`to_svg` → die Bildkonverter → `insert_picture` mit
  `natural` und `svg`; ohne SVG-Konverter `DocumentConversionError` mit Hinweis auf das Extra
  `svg`), `ImageGraphic` wie bisher. Ein Absatz `Abbildung:`/`Figure:` direkt nach dem Zaun
  (gleiche `level`) wird die Beschriftung und geht dem Chart-Titel vor (`_figure_caption`).
  `place_picture` konvertiert nur noch und ruft `insert_picture`. Der Mermaid-Renderer hat
  keinen Word-Zweig mehr: mit eingerichtetem mermaid-cli zeichnet er auch für Word. Der
  DOCX-Konverter liest `c:chart` als Markdown-Tabelle aus dem Wertecache des Chart-Teils
  (`_render_chart`, Kopf der Kategorienspalte leer). `samples/funktionen/mermaid-bericht.md`
  braucht wie die Mermaid-Präsentation mmdc (Tests überspringen sie sonst über `drawable`, auch
  `tests/generation/docx/test_notes.py`). `test_funktionen.py` verlangt im Bericht einen
  `financial-chart` und eine `Abbildung: …`-Beschriftung nach einer Grafik.
- **QR-Codes** (E11-S04): `generation/common/generated_images.py` — Bildreferenzen mit Schema
  `qr:` (`SCHEMES`, `is_generated`) erzeugt `add_generated(document, tokens, format,
  line_offset)` als PNG-Ressource unter der Referenz selbst (segno, Kernabhängigkeit, BSD-3;
  `micro=False`, sonst macht segno aus kurzem Text Micro-QR, den Handys kaum lesen). Beide
  Generatoren rufen es direkt nach `layout_syntax.check` auf und arbeiten danach mit dem
  zurückgegebenen Dokument (`BodyWriter.source`, `DeckParser.document`). `scale=N` im Titel
  nimmt es aus dem Titel und legt es in `Token.meta[SCALE]` (`scale_of`); Word multipliziert die
  Größe (PNG-dpi = 3 cm), PowerPoint über `Image.scale`. `Image.fit` lässt `fill_picture` das
  Bild in den Platzhalter einpassen statt beschneiden (`visuals.fit_picture`). Ein neues Schema
  in `SCHEMES` eintragen; `test_funktionen.py` verlangt jedes im Beispiel.
  `style-image-source` überspringt erzeugte Bilder (`style_rules.needs_source`).
