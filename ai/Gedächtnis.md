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
  (→ Markdown), `generation/` (`common/`, `docx/`, `pptx/`, `pdf/` seit E05-S01, `html/` seit
  E10-S01).
- **Stand 2026-11-06:** M01 umgesetzt (alle Stories in `spec/60-prüfung/`): DOCX- und
  PPTX-Generator auf den PTA-Vorlagen, DOCX-/PPTX-Konverter, Front Matter, Designmodell,
  eingebettete Vorlagen. Seit E05-S01/E05-S02 ein PDF-Generator (Rumpf im Word-Design, PDF/A-2b;
  seit E05-S03 mit Seitenrahmen, seit E05-S04 mit allen Grafiken), seit E07-S04 ein
  PDF-Konverter; die
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
- **Builds** (E09-S02): Marker-Zeilen (`{.build}`, `{.frag}`, `{.exit}`, `{.emphasize}`) nimmt
  eine Kernregel des gemeinsamen Parsers heraus (`markdown/block_markers.py`, `meta[MARKER]` am
  ersten Token des Blocks; falsche bleiben als Absatz mit `meta[ERROR]`, `layout_syntax.check`
  wirft) — Word/PDF brauchen dafür keinen Code. Neue Blockmarker (geplant `{.calc}` E14-S03; seit
  E16-S01 `{.internal}`) in `NAMES` eintragen; PPTX wirft für jeden Marker, den `DeckParser.marked`
  nicht angewendet hat (`_check_markers`), also dort mit behandeln. Klicks: `model.Click` als
  kw-only `click` an Absätzen, Visuals und Flow-Blöcken; wer einen Block neu baut, gibt
  `deck.current` (Blöcke) bzw. `paragraph_click()` (Absätze) mit und zeichnet neue Formen in
  `DeckWriter.at(slide, click)` (bzw. `each` für eine Form je Klick); Absätze werden über
  `Builds.paragraphs` erfasst (in `write_paragraphs` und `FlowWriter.text` schon drin). `p:timing`
  schreibt `DeckWriter.write_builds` beim nächsten `new_slide` (vor `p:extLst`, also nach
  `p:transition`). Front Matter `aufbau: listen` nur PowerPoint.
- **Übergänge** (E09-S03): `generation/common/slide_transition.SlideTransition` (Werte englisch,
  Richtung = Bewegungsrichtung wie `dir` in PresentationML), Front Matter `uebergang` nur
  PowerPoint (`PptxOptions.transition`), Heading-Attribut `uebergang="…"` auf `#` (Kapitel) und
  `##` — geprüft in `heading_attributes.split`, also in allen Formaten. `DeckParser._transition`
  setzt `Slide.transition` (kw-only, wie `notes`); `new_slide` schreibt es sofort nach
  `p:clrMapOvr` (`animations.set_transition`). Morph ist `mc:AlternateContent` (p159, Fallback
  Fade) — wer `p:transition` sucht, muss auch dort schauen.
- **Szenen** (E09-S04): `::: scene` wird **roh** gelesen — eine Kernregel des gemeinsamen Parsers
  hängt jedem Container seine Quellzeilen an (`markdown.parser.SOURCE_LINES` in `meta`).
  Modell/Leser `generation/common/scene.py` (Raster 160 × 67 über `CONTENT_AREA`, `UNIT_EMU`
  70 200), Farben `scene_colors.py` (nur `design.colors`), `layout_syntax.check` prüft Platz und
  Grammatik in allen Formaten. PPTX: `SceneSlide` → `scene_writer` (Formen `!!name`, Morph über
  E09-S03, `step` = `Click(n)`); PDF: `drawing/scene.draw` → `SceneFlowable` (Bilder zwischen den
  Items); Word: weg mit `scene-dropped`. Ein `p:sp` ohne `txBody` ist für Builds `Target.OTHER`.
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
  PDF-Generator weicht aus (seit E05-S02 leiht U+00A0 beim Registrieren die Glyphe des
  Leerzeichens, `truetype.with_aliases`; andere fehlende Zeichen gehen seit E05-S04 an
  `replace_unsupported`, Standard `?`).
  Segoe UI wird nur mit allen fünf
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
  (seit E15-S02 `ShapeKind.CHEVRON`/`HOME_PLATE`/`PIE`) muss in jedem `match` ergänzt werden
  (pyright meldet fehlende Fälle über den Rückgabetyp). `to_svg` validiert Farben (`RRGGBB`) und Zahlen
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
  zurückgegebenen Dokument (`BodyWriter.source`, `DeckParser.document`). `scale=N` gilt seit
  E15-S04 für alle Bilder (`scale_of` liest `image_attributes.of`); Word multipliziert die
  Größe (PNG-dpi = 3 cm), PowerPoint über `Image.scale`. `Image.fit` lässt `fill_picture` das
  Bild in den Platzhalter einpassen statt beschneiden (`visuals.fit_picture`). Ein neues Schema
  in `SCHEMES` eintragen; `test_funktionen.py` verlangt jedes im Beispiel.
  `style-image-source` überspringt erzeugte Bilder (`style_rules.needs_source`).
- **Zeitstrahl und Gantt** (E15-S01): Container `timeline`/`gantt` in `layout_syntax`
  (`CONTAINER_NAMES`; `gantt` nimmt `raster=…`, geprüft über `schedule.grid_argument`). Modell
  und Leser in `generation/common/schedule.py` (`read_timeline`, `read_gantt`, `parse_date`,
  `grid_for`, `units`); **`layout_syntax.check` liest beide schon** (Fehler `Line N: …` aus dem
  Leser, nicht doppelt präfixen) und nimmt dafür `today` — „heute" ist `options.date`
  (Front Matter `datum`), sonst `date.today()` (`schedule.reference_day`). Zeichnung
  formatunabhängig in `drawing/schedule.py` (`draw(schedule, width_px, dark=)`). PowerPoint:
  Flow-Block `ScheduleBlock` → `FlowWriter.schedule` → `generation/pptx/drawing.place` (eine
  Gruppe `Drawing <n>`, Breite des Platzes, nie geschrumpft). Word: `BodyWriter.timeline` (Bild
  über `docx_drawings.convert`, Extra `svg`) und `BodyWriter.gantt` (Tabelle „PTA",
  Schattierung, `tcBorders` **nach** `w:shd` anlegen, sonst falsche Schema-Reihenfolge). Der
  DOCX-Konverter liest leere Zellen mit Füllung PTA-Blau/Hellblau als `■`. Das PDF (E05-S04)
  zeichnet den Zeitstrahl als Vektoren und setzt den Gantt als Tabelle wie Word
  (`StoryBuilder.layout_container` → `drawing`/`gantt`; „heute" = `LayoutSettings.today`).
- **Schritte, Harvey Balls, Risikomatrix** (E15-S02): Container `steps`/`riskmatrix` in
  `layout_syntax` (`riskmatrix` nimmt `green=… yellow=…`, `risks.thresholds_argument`); Leser
  `generation/common/steps.py` und `risks.py` (Hilfen `child_blocks`, `table_rows`, `error_at`
  aus `schedule.py`, früher privat), `layout_syntax.check` liest beide. Zeichnungen
  `drawing/steps.py` (`draw`, `texts_fit`), `drawing/riskmatrix.py` (natürliche Größe, Achsen =
  Spaltenköpfe 3/4), `drawing/harvey.py`, Formen in `drawing/shapes.py`; PPTX-`pie` braucht das
  Quadrat des ganzen Kreises — `_pie_bounds` liest es aus dem Pfad (Start = Mitte). Harvey
  Balls: `layout_tokens.harvey_cell`; PPTX `Run.harvey` → `visuals.harvey_ball` (Gruppe
  `harvey-n` über der Zelle, der Konverter schreibt `[n/4]` per Position zurück), Word Zeichen in
  Segoe UI Symbol, PDF `flowables.HarveyBall`. PPTX-Blöcke `StepsBlock`/`RiskMatrixBlock`
  (Legende rechts, unter 7 cm Platz darunter); Word `BodyWriter.steps`/`risk_matrix`
  (`drawing_picture`). Das PDF zeichnet beide wie Word, als Vektoren (`StoryBuilder.steps`/
  `risk_matrix`, E05-S04). `test_funktionen.py` verlangt `[n/4]` und
  `::: riskmatrix <thresholds>`.
- **PDF-Generator** (E05-S01 + E05-S02, zusammengeführt 2026-11-08): `generation/pdf/` ist nur
  mit Extra `pdf` importierbar (`__init__` wirft sonst `ImportError(EXTRA_MISSING)`); `check` und
  die Werkzeuge importieren es erst bei `--pdf`/`DocumentFormat.PDF`, der Kern nie. Ablauf in
  `PdfGenerator.generate`: Front Matter (`VALID_KEYS` = die von DOCX) → `create_parser().parse` +
  `layout_syntax.check(…, today)` → `generated_images.add_generated(…, notes)` → `typeset` (und
  die
  Status-Labels) → `design.fonts.resolve` → `Notes.characters` (`character-missing`) →
  **`frame.lay_out(tokens, document, LayoutSettings, FrameInfo, notes, PdfInfo)`** (seit
  E05-S03; ohne Rahmen `layout.layout`) → `pdfa.to_pdfa`
  (pikepdf) auf `result.content`; `GenerationResult.pages` = `result.pages`. Es gibt **ein**
  `PdfInfo` (`metadata.py`) für reportlab und PDF/A und **eine** Schriftregistrierung
  (`layout/fonts.register`). Das Seitenmodell, der eigene Renderer und das Zwischenlayout von
  E05-S01 sind entfallen (Stand in Commit 175e572); E05-S03 zeichnet den Seitenrahmen über
  `render(…, decorate, page_count, first_top_pt)`, E05-S04 Zeichnungen als eigene Flowables auf
  dem reportlab-Canvas.
  Fehlende Zeichen gehen durch `PdfFonts.shown` (Text: Regular+Bold, Code: Mono; `ALIASES`
  zählen als vorhanden) — PDF/A verbietet `.notdef`; siehe den Eintrag E05-S04. **Jeder** Text,
  der auf den Canvas kommt (auch Seitenrahmen, Deckblatt, Zeichnungen), muss durch `shown`.
  QR-Codes sind 3 cm
  (× `scale_of`) wie in Word (`StoryBuilder.picture`). Pillows sRGB-Profil trägt die aktuelle
  Uhrzeit — `pdfa.srgb_profile` setzt sie fest, sonst sind Dateien nicht byte-gleich. Selawik hat
  **weder Griechisch noch Kyrillisch**; ohne Segoe UI werden solche Zeichen `?`. Tests mit
  `PdfOptions(created=…, system_fonts=False)`, damit sie nicht vom Rechner abhängen; veraPDF ist
  hier nicht installiert (Test wird übersprungen). Präsentationen gibt es nicht als PDF
  (`fusszeile` u. a. sind keine gültigen Schlüssel). Jedes Word-Beispiel in `samples/` muss als
  PDF ohne Hinweise entstehen (`tests/generation/pdf/test_generator.py`; Mermaid-Beispiele nur,
  wo mermaid-cli läuft).
- **PDF-Seitenrahmen** (E05-S03): `design/word_frame.read(variant)` liest Kopf-/Fußzeilen der
  Vorlage (`PageFrame` → `PageKind` → `Band` mit `FrameTable`/`FrameParagraph`, Logo-`Box`,
  `FrameRule`), `generation/pdf/frame.py` zeichnet sie (`PageDecorator`) und setzt Deckblatt und
  Verzeichnis vor die Story (`lay_out`, rendert bis Seitenzahl und `RenderedPdf.heading_pages`
  stabil sind). Felder erkennt `word_frame` am Platzhaltertext (`word.TITLE_PLACEHOLDER`,
  `COMPANY_PLACEHOLDER` …) — ändern die Vorlagen ihn, brechen `tests/design/test_word_frame.py`.
  `WordDesign.paragraph_ids` bildet `w:styleId` auf `w:name` ab (Kopf-/Fußzeilen nennen Ids:
  `Fuzeile`). Das Deckblatt beginnt bei `word_frame.body_top(…, 1, …)`: die erste Kopfzeile von
  `hoch`/`quer` ist ein leerer Absatz mit 200/150 pt Abstand danach, Word schiebt den Text darunter
  (8,50/6,79 cm) — dafür hat `render` eine eigene erste `PageTemplate`. `hoch-ohne-deckblatt` hat
  keinen `w:titlePg`: seine „first"-Kopfzeile gilt nicht. Inhaltsverzeichnis aus
  `Story.outline` (`Outline` trägt seit E05-S03 `heading`, `number`, `text`, `anchor`), Seiten aus
  `_Template.afterFlowable`. Tests lesen den Rumpf mit `tests/generation/pdf/support.type_area`
  (Seite auf den Satzspiegel beschnitten), sonst stehen Kopf- und Fußzeilentexte im Text.
  reportlabs Stubs kennen `FILL_EVEN_ODD` nicht (eigene Konstanten in `frame.py`).
- **PDF-Layout-Engine** (E05-S02): `pta_documents.generation.pdf.layout` (Unterpaket) auf
  reportlabs **Platypus** statt eines eigenen Seitenmodells — `layout(tokens, document,
  LayoutSettings, notes, PdfInfo, decorate)` bzw. `build_story` + `render`. Werte der
  Formatvorlagen und den Satzspiegel liest `design/word_styles.read(variant)` aus der Vorlage
  (kein Wert im PDF-Code doppeln). Fallen:
  reportlab unterscheidet eingebettete Schriften am **PostScript-Namen** — die schräggestellte
  Kursive (`truetype.slanted`) heißt deshalb `…-Slanted`, sonst landet sie nicht im PDF;
  `Frame(overlapAttachedSpace=0)`, sonst verschluckt reportlab den kleineren von Abstand nach/vor
  (Word addiert); Absätze mit `allowWidows=0`/`allowOrphans=0`; Seitenumbruch vor Überschriften
  über `KeepWithStart` (eigener `CondPageBreak`, nie oben auf einer Seite), Fußnoten über
  `FootnoteAnchor`, das `frame._y1p` hebt — `handle_frameBegin` setzt den Rahmen mit
  `frame._geom()` zurück. Zeilenhöhe „einfach" = `FontInfo.line_height` (Windows-Ascent +
  -Descent), nicht reportlabs `face.ascent`. Neue Blockarten im PDF in `layout/story.py`
  (`StoryBuilder.block`) eintragen, gemeinsame Erkennungen mit dem DOCX in
  `generation/common/block_shapes.py`.
- **Icons** (E15-S03): `:icon-name:` ist eine Inline-Regel (`markdown/icon.py`, Token `icon`,
  `meta["name"]`, vor `emphasis`; Code-Spans laufen vorher). 162 Tabler-SVGs (MIT, unverändert)
  in `design/icons/` mit `ICONS`, `svg`, `colored_svg`, `alt`/`from_alt` (`icon:<name>`),
  `loader.drawing` (nur `<path>`, Quadrat `stroke="none"` entfällt) und `raster.png` (Pillow,
  Name im PNG-Textfeld `pta-documents-icon`). Gemeinsames in `generation/common/icons.py`
  (`check` — von `layout_syntax.check` gerufen —, `leading`, `without_leading`, `list_icons`:
  nur Bullet-Listen, **jeder** Punkt mit Icon). PPTX: `Card.icon` → `FlowWriter.icon` (Gruppe
  `icon:<name>`), `Paragraph.icon` → `DeckWriter.icon_bullet` (`a:buBlip`); jedes andere Icon
  in Folientext wirft in `DeckParser.runs`. Word: `BodyWriter.icon_picture`/`icon_bullet`
  (`numId 0`, hängender Einzug, `w:tab` im Bild-Run); PDF (E05-S04): `InlineWriter` schreibt
  `<img src="pta-icon:name"/>`, das `PtaParagraph` über einen eigenen `ParaParser` liest
  (`flowables._Parser`, reportlabs `<img>` kennt nur Dateien/URLs, `data:` sperrt rl_config),
  Aufzählungszeichen `MarkerKind.ICON`. Konverter: DOCX über `docPr/@descr`, PPTX über
  Gruppenname
  und PNG-Textfeld. `docs/ki-anleitung.md` muss jeden Namen nennen (Test
  `tests/design/icons/test_icons.py`).
- **Bildattribute** (E15-S04): `{…}` direkt nach einem Bild ist eine eigene Inline-Regel
  (`markdown/image_attributes.py`, Rohtext in `Token.meta[ATTRIBUTES]`) — **nicht**
  `mdit_py_plugins.attrs` (dort beginnt `%` einen Kommentar, `{focus=30%,20%}` bliebe Text).
  Gelesen und geprüft (Fehler `Line N: …`) wird in `generation/common/image_attributes.take`,
  aufgerufen aus `generated_images.add_generated` für **alle** Bilder (auch PDF, mit `notes`);
  Ergebnis in `Token.meta[KEY]`, Abruf mit `of(token)`. `scale=` im Titel: noch bis 2027-11, mit
  Hinweis `image-scale-in-title`. `.grey`/`.round` macht `image_styles.apply` als neue
  PNG-Ressource (`<name>-grey.png`, `-round.png`) und **schreibt `src` des Tokens um** —
  PowerPoint behält `.round` (Ellipse über `picture.auto_shape_type`, Quadrat-Ausschnitt per
  `srcRect`, `visuals.round_picture`/`draw_pictures`). Ausschnitt um den Fokus:
  `image_attributes.visible_window` (`visuals.crop_picture` in `fill_picture`). Word/PDF
  schneiden nie; `focus`/`fit` sind dort wirkungslos. Der PPTX-Konverter liest `prst="ellipse"`
  als `{.round}` zurück. Beispielbild `samples/funktionen/images/portraet.png` (selbst gezeichnet,
  880 × 1000, verliert im Rahmen „Titel, Text und Bild 01" knapp unter 25 %).
- **Kennzeichnung und Schulungsvorlage** (E04-S05): `kennzeichnung:` (`Keys.MARKING`,
  `design.variants.Marking`, Texte `GeneratedTexts.marking`) — in PPTX ein Sticker **auf dem
  Master** (`generation/pptx/sticker.py`: `resolve` vor dem Laden der Vorlage, `apply` danach);
  Schulung behält „Rectangle 7" und setzt nur den Text, Basis bekommt eine Form aus
  `design.slides.STICKER` (Maße auf das EMU wie der Schulungs-Master, Vergleichstest). Standard
  `basis` → `kein`, `schulung` → `intern`; `schulung` + `kein` ist ein Fehler. Word/PDF: siehe
  den Eintrag E12-S03 (dort Standard `kein`). Englisch: `package_file` liefert
  für `en` immer `slides-<variante>-en.pptx`; `slides-schulung-en.pptx` macht
  `prepare-templates` aus der Schulungsvorlage ohne die EMF-Logos der vier Titellayouts
  (`SLIDES_WITHOUT_TITLE_LOGO`, `remove_title_logos`). Das englische Logo heißt
  `PTA-Logo EN` (`design.slides.ENGLISH_LOGO_NAME`) und wird vom PPTX-Konverter übersprungen.
- **Kennzeichnung in Word und PDF** (E12-S03): derselbe Schlüssel `kennzeichnung`
  (`DocxOptions.marking`/`PdfOptions.marking`, Standard `Marking.NONE`). Ort:
  `word_frame.marking_area(frame)` — 3 pt unter der Kopfzeilenlinie der *anderen* Seiten (auch auf
  dem Deckblatt, dessen `quer`-Linie tiefer liegt), Maße in `design.word.MARKING`. Word
  (`generation/docx/marking.py`): Textfeld (`wps`, `wrapNone`, Name `PTA-Kennzeichnung`) und bei
  `entwurf` das VML-Wasserzeichen (`WATERMARK_SHAPE`, Id `PowerPlusWaterMarkObject<n>`) werden an
  den **letzten Absatz** jedes Kopfzeilenteils gehängt — nie ein neuer Absatz, sonst wird die
  Kopfzeile höher und schiebt den Text. `docPr`-Ids: höchste über **alle** Teile + 1 (die Fußzeile
  hat eigene Ids; die Vorlagen selbst haben doppelte). Der Deckblatt-Absatz (Stil „Autor") kommt
  in der DOCX-Rundreise als Text zurück. PDF: Text in `PageDecorator._marking`, Wasserzeichen
  `frame.Watermark` über `render(…, underlay=…)` (`onPage`, vor dem Inhalt), Farbe gegen Weiß
  gemischt statt Alpha (PDF/A ohne Soft-Mask). pdfplumber hält 45°-Text für `upright` — Tests
  erkennen das Wasserzeichen an `matrix[1]`.
- **Grafiken und fehlende Zeichen im PDF** (E05-S04): Zeichnungen (`DrawingGraphic`,
  `ChartGraphic.drawing`, Zeitstrahl, Schritte, Risikomatrix, Gantt-Raute) sind
  `generation/pdf/layout/drawings.DrawingFlowable` (Pfade/Text direkt auf dem Canvas, y nur dort
  gespiegelt; Texte werden im Konstruktor gemessen, damit fehlende Zeichen beim Bauen der Story
  werfen). Größe/Schrumpfen in `StoryBuilder.drawing_flowable`, Beschriftung aus
  `Abbildung: …` nach dem Zaun in `graphic_figure` (Charts sonst ohne, der Titel steht in der
  Zeichnung). SVG-Bilder wandelt das PDF mit `story.IMAGE_SCALE = 3`. Fehlende Zeichen:
  `generation/common/graphemes.clusters` (ohne `regex`), `PdfFonts.replace`
  (= `PdfOptions.replace_unsupported`/`LayoutSettings.replace_unsupported`, Standard
  `fonts.question_mark`, `None` = Fehler) mit Antwort-Cache je Dokument (`PdfFonts.replaced`;
  `prepare` legt `PdfFonts` je Dokument an). Lesezeichen/Inhaltsverzeichnis zeigen den Ersatz
  (`Outline.text` ist schon ersetzt), Anker bleiben aus dem Original. `layouts.md` und die
  Fehlerfälle der Folien-Syntax laufen in `tests/generation/common/test_layout_syntax.py` auch
  für PDF (`GENERATORS`; die farbigen Wörter nur `OFFICE`).
- **PDF-Konverter** (E07-S04): `conversions/pdf.py` (`PdfConverter`, Port von DocLibs auf
  pdfplumber, Bilder über pikepdf; importiert pdfplumber auf Modulebene — die Registry lädt ihn
  weiter lazy über `PDF_CONVERTER_MODULE`). pdfplumber misst von oben, PdfPig von unten: die
  Vergleiche sind gedreht, die Schwellen gleich. Über DocLibs hinaus (für die Rundreise der
  PTA-PDFs): Tabellen (`find_tables`-Gitter und `ruled_tables` für den Stil `PTA`: gefüllte
  Kopfzeile + Linie an deren Unterkante + Zeilenlinien, Abbruch, wenn der Text weiter unter der
  Linie beginnt als im Kopf), gezeichnete Aufzählungszeichen/Aufgabenkästchen (`_markers`,
  `mark_items`), Codezäune aus Festbreitenschrift (`MONOSPACED`; die Füllfläche dahinter hält
  den Block zusammen, `code_areas`), Bilder an ihrer Stelle statt am Seitenende, gedrehte Zeichen
  (Wasserzeichen) gefiltert (`_not_rotated`), Kopf-/Fußzeilen nur, wenn der Schlüssel auf keiner
  Seite doppelt vorkommt. `sample.pdf.expected.md` ist die Datei aus DocLibs, unverändert — wer
  die Heuristik ändert, muss sie byte-gleich halten. Rundreisen von `report.md`/`long.md` mit
  Seitenrahmen in `tests/generation/pdf/layout/samples/*.roundtrip.expected.md` (Front Matter mit
  festem `datum`, `code_block_renderers=()`, sonst hängt das Ergebnis von Tag und mmdc ab).
  Ändert der PDF-Generator Layout oder Seitenrahmen, ändern sich diese Rundreisen mit.
- **HTML-Deck** (E10-S01): `generation/html/` zeichnet nicht aus den Modellen, sondern **die
  PPTX, die `PptxGenerator` in einen Puffer schreibt** (Teilung passiert im `DeckWriter`, nicht
  im Parser — ein zweiter Writer hätte Flow, Arten, Fitting doppeln müssen). Folgen: alles, was
  der PPTX-Writer neu zeichnet (Szenen E09-S04, neue Formen), erscheint im HTML von selbst,
  solange es Standard-DrawingML ist; neue `prstGeom` in `generation/html/geometry.preset`
  nachtragen (sonst Rechteck), neue Animationen/Übergänge in `timing.py`. Fehler werden mit
  Format `html` und gleichem `reason` neu geworfen; die eigenen Schlüssel `fortschritt`/
  `kapitelanzeige` werden vor dem PPTX-Lauf zu Kommentarzeilen (`# …`), damit Zeilen gleich
  bleiben — PowerPoint selbst lehnt sie ab. EMF-Logos der Layouts ersetzt `shapes.image_data`
  durch die SVG-Logos (E01-S04). Eine CSP mit dem SHA-256 von `"\n" + deck.js` erlaubt nur die
  Laufzeit — wer `deck.js` oder das `<script>`-Gerüst im Writer ändert, ändert den Hash mit
  (Test). Schnappschuss `tests/generation/html/samples/deck.expected.html` ändert sich bei jeder
  Änderung an PPTX-Layout oder Writer mit. Playwright ist Extra `preview` (seit E10-S02 auch in
  `./run.sh setup`); `test_browser.py` überspringt ohne. Zum Ansehen: `.tmp/review/*.html`.
- **Vorschau als Bilder** (E10-S02): `pta_documents.preview` (`render_deck(html) →
  [SlidePicture]`, `contact_sheet`, `PreviewUnavailableError`, `chromium_available`), Werkzeug
  `./run.sh preview` → `<ordner>/vorschau/<name>/folie-NN.png` + `uebersicht.png`. Das Deck
  kommt per `context.route` aus dem Speicher (`https://deck.preview/`), ein Vorschau-Stil vor
  `</head>` setzt „Segoe UI"/„Consolas" per `@font-face` auf Selawik/Inconsolata und schaltet
  Seite um die Bühne, Animationen und Übergänge ab; Builds im Endzustand. Seit E10-S02 installiert
  `./run.sh setup` das Extra `preview` und — nur wenn `preview --check-browser` scheitert —
  `playwright install chromium` (Fehler nur als Meldung). Playwright startet Chromium von sich
  aus ohne Sandbox. **Referenzbilder** nur vom kleinen Test-Deck
  `tests/preview/samples/vorschau-referenz.md` in `tests/preview/expected/vorschau-referenz/`
  (halbe Größe, ~0,6 MB); sie ändern sich bei sichtbaren Änderungen an PPTX-Layout oder
  HTML-Writer: mit `PTA_DOCUMENTS_UPDATE_EXPECTED=1` neu schreiben und `.tmp/review/preview/`
  ansehen. Die Funktionsübersicht bekommt **keine** eingecheckten Bilder (sie wächst mit jeder
  Story, das Repo würde jedes Mal um MB wachsen), nur einen Rauchtest (Folienzahl = PPTX, Maße,
  Wiederholbarkeit). Das Test-Deck nur ändern, wenn es nötig ist. `samples/*/vorschau/` ist
  git-ignoriert.
- **Zielgruppenfassungen** (E16-S01): `generation/common/audience.py` (`Audience` `kunde`/`intern`/
  `trainer`, `filter_tokens`, `check`, `versions`). Jeder Generator ruft **nach**
  `layout_syntax.check` (prüft die Syntax für alle Fassungen) `filter_tokens` auf — ein neuer
  Generator oder ein neuer Parse-Weg muss das auch, sonst geht Internes hinaus. Die Container
  `internal`/`exercise`/`solution` werden ausgepackt (Inhalt eine `level` höher, kein Kasten),
  `{.internal}` (Blockmarker und Überschriftenattribut) aus `meta` entfernt. `options.audience`
  (Standard `None`) geht **vor** `fassung:` — umgekehrt wie sonst; nicht-`kunde` setzt
  `kennzeichnung` auf `intern`, wenn das Front Matter keine nennt. Die Stilregeln von `check` und
  `Notes.characters` (PDF) lesen das ungefilterte Markdown, nur die Statistik die Fassung.
  Beispiele mit Internem brauchen `fassung: trainer`, sonst kommt `audience-omitted`.
- **Schulungs-Zeitplan** (E16-S02): `generation/common/training_schedule.py` (`Schedule`,
  `ScheduleEntry`, `build` aus den Level-0-Überschriften, `deck_schedule(document, audience)`,
  `schedule_document`; nicht zu verwechseln mit `schedule.py` = Zeitstrahl/Gantt E15-S01),
  Zahlen/Uhrzeiten in `durations.py`. `dauer=5` ist der **einzige** Attributwert ohne
  Anführungszeichen (`heading_attributes._BARE`); `.break` ist eine PTA-Folienart
  (`SLIDE_KINDS`, `KIND_LAYOUTS["break"]` = Zwischenfazit-Layouts, `KindReader` macht ein
  `InterimSlide` „Pause · 15 min"). `DeckParser.parse` baut den Zeitplan auf `self.tokens` (nach
  `_take_notes`: `ScheduleEntry.heading` ist der Index dort, wie bei `speaker_notes`); die
  Agenda (`KindReader.timed`) und die Zeitnotiz der Trainerfassung (`DeckParser._planned`) lesen
  ihn. Front Matter `beginn`/`laenge` nur PPTX (`PptxOptions.begin`/`length`). Hinweise
  `schedule-missing`/`schedule-length` aus dem Generator, `schedule-estimate` nur aus `check`
  (`_with_estimate`, braucht die Statistik des Probedecks). `generate --audience alle` hängt für
  Decks mit Zeitplan die Trainerfassung an (`tools/generate.audiences_of`), weil sich deren
  Token-Strom nicht unterscheidet. Werkzeug `./run.sh schedule` → `<name>-zeitplan.docx`.
- **Backup und Anhang** (E16-S04): `HeadingAttributes.backup`/`.appendix` (nur `#`), Regeln für
  das ganze Dokument in `generation/common/backup.check` (aus `layout_syntax.check`, alle
  Formate). PPTX: `Slide.backup` (kw-only, wie `notes`) ab `{.backup}`, `ChapterSlide.number`
  `None` = ohne Nummer; die Trennfolie heißt `Backup` (`p:cSld/@name`) — HTML-Deck, `check`
  (`DeckStats.backup`) und PPTX-Konverter finden den Anfang über `design.slides.backup_start`
  (Name, sonst erste Folie hinter der Abschlussfolie). Wer Agenda/Zeitplan aus `#`-Kapiteln baut,
  hört vor `{.backup}` (Deck) bzw. `{.appendix}` (Word) auf. Word: eigene Kopie der
  Überschriften-`abstractNum` mit `upperLetter` (`BodyWriter._appendix_num`), die Absätze tragen
  `w:numPr`; ändert sich die Überschriften-Nummerierung der Vorlage, prüft
  `test_the_appendix_is_lettered_in_word`. PDF: `StoryBuilder.appendix`, `backup.letters`.
  Das jeweils andere Attribut meldet `attribute-ignored`. Zusammen mit E16-S02:
  `training_schedule.build` endet an `{.closing}` **oder** `{.backup}`; `backup.check` weist `{.break}` und `dauer=…` ab
  der Abschlussfolie bzw. ab dem Backup ab (Entscheidung 2026-11-08, vorsichtig: Fehler statt
  stillschweigend ungeplant).
- **Teilnehmerhandout** (E16-S03): `pta_documents/handout/handout.py` (`build_handout`,
  `write_handout`, `slide_pictures`, `HandoutLayout` 2/3/6, Standard 3). Kein eigener
  Word-Writer: das Handout ist Markdown, die Folien liest es aus der **im Speicher erzeugten
  PPTX** (python-pptx: Layoutname, Titel, Text, Notizen — so stimmen Foliennummern, geteilte
  Folien und die „Geplant"-Notiz der Trainerfassung mit Deck und Vorschau überein). Zwei
  DOCX-Optionen nur über die API dafür: `DocxOptions.figure_numbers=False` (Beschriftung ohne
  `SEQ`) und `side_by_side_columns=True` (`::: columns` als Tabelle im Stil „Bildreihe",
  `BodyWriter.cell`/`blocks()` lenken Absätze und Tabellen in die Zelle; nur `---` trennt
  Spalten, `***` bleibt Linie). Linien zum Schreiben sind `***`. Bildmaße in `geometry` aus
  `design.word_styles` (Seite, Absatzhöhen); `print_picture` setzt die dpi so, dass die
  natürliche Größe die gewünschte Breite ist (der DOCX-Generator nimmt sie). Backup-Folien nur
  in der Trainerfassung. Ohne Playwright: Text-Handout und Hinweis `handout-without-pictures`.
  Werkzeug `./run.sh handout`; `./run.sh preview` kennt seitdem `--audience`
  (`vorschau/<name>-trainer/`).
- **Authoring Guides** (E02-S05): Bausteine in `generation/common/authoring_guides.py`, Vorlagen
  je Generator in `<paket>/authoring_guide/<name>.md` (Paketdaten, `template(package, name)`;
  E05-S05 nannte noch `generation/pdf/authoring_guide.md` — dem gemeinsamen Ort folgen). Ein
  Guide entsteht aus `fill(template(…), {…})` mit den Abschnitten (`front_matter_section`,
  `layout_syntax_section`, `icons_section`, `notes_section`, `typography_section`,
  `renderers_section`, für das PDF `characters_section`); `front_matter_section` wirft
  `ValueError`, wenn die `GuideKey`-Zeilen nicht genau `VALID_KEYS` beschreiben. Werkzeug
  `./run.sh authoring-guide docx|pptx|pdf` ruft `<Generator>().authoring_guide()`, sobald es die
  Methode gibt (sonst Code 1). Testhilfen `tests/generation/guides.py`. **Regel für spätere
  Stories:** neue Container, Alerts, Überschriftenattribute, Blockmarker, Hinweis-Codes brauchen
  einen Text in `CONTAINER_TEXTS`/`ALERT_TEXTS`/`ATTRIBUTE_TEXTS`/`MARKER_TEXTS`/`NOTE_TEXTS`
  (Tests vergleichen mit den Code-Listen; was nur für Folien bzw. nur für Word/PDF gilt, über
  `DOCUMENT_ATTRIBUTES`, `DOCUMENT_ONLY_ATTRIBUTES`, `DOCUMENT_MARKERS`, `LEFT_OUT_CONTAINERS`);
  ein neuer Front-Matter-Schlüssel braucht eine `GuideKey`-Zeile im Guide des Generators, ein
  neuer Renderer sein `authoring_guide`. Was ein Guide an Syntax nennt (`named_syntax`, Regex
  `SYNTAX_PATTERN` wie vt-tools-libs), muss wortgleich in `samples/funktionen/` des Formats stehen
  (`test_the_samples_show_the_syntax_the_guide_names`, heute aus den gemeinsamen Abschnitten;
  E03-S05/E04-S06 stellen `guide_syntax` auf den ganzen Guide um, ohne die Fehlerbeispiele). Im
  Word-Guide stehen `.agenda`/`.interim`/`.quote`/`.contact` nur als bloße Namen, weil der
  Word-Bericht sie nicht zeigt. Die Icon-Liste steht weiter in `docs/ki-anleitung.md` (Test
  E15-S03), bis die Guides sie übernehmen.
- **Word-Guide** (E03-S05): `DocxGenerator().authoring_guide(options)` → `generation/docx/guide.py`
  (Vorlage `generation/docx/authoring_guide/docx.md`, Satz je Vorlage in `VARIANT_TEXTS`,
  Front-Matter-Zeilen mit den Standardwerten der Optionen). `guide_syntax` in
  `tests/samples/test_funktionen.py` liest für Word den ganzen Guide ohne „Wenn etwas falsch ist“
  (darunter steht auch `### Hinweise`, weil `notes_section` `{.backup}` nennt). **Wortbudget:**
  mit allen Renderern rund 2 460 von 2 500 Wörtern — wer Word-Syntax, Schlüssel oder einen
  Renderer-Abschnitt ergänzt, muss anderswo kürzen (`test_the_guide_stays_under_the_word_limit`);
  Erwartung `tests/generation/docx/samples/authoring-guide.expected.md` mit
  `PTA_DOCUMENTS_UPDATE_EXPECTED=1` erneuern.
