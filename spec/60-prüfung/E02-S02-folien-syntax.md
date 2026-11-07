# E02-S02 Folien-Syntax: Heading-Attribute, Container, Alerts, Markierungen, Status-Labels

> Status: in Prüfung
> Epic: [E02 Markdown-Grundlagen der Generatoren](../50-entwurf/E02-markdown-grundlagen.md)
> Milestone: [M02 Rückmeldung und Folien-Syntax](../50-entwurf/M02-rueckmeldung-und-folien-syntax.md)

## Zusammenfassung

Die Markdown-Syntax der Folien-Layouts aus DocLibs wird einmal gemeinsam gelesen und geprüft, damit
DOCX, PPTX und PDF dieselbe Quelle annehmen und dieselben Fehler melden; das Zeichnen bleibt den
Generatoren (E03-S03, E04-S03, E05-S04).

## Kontext

- DocLibs: `HeadingAttributes.cs` (73 Zeilen), `LayoutSyntax.cs` (66), `ColouredWords.cs` (121),
  die Markdig-Erweiterungen `UseAlertBlocks`, `CustomContainerParser`, `EmphasisExtras.Marked` in
  `DeckParser.cs`/`MarkdownParser.cs` sowie Erkennung von Tags, beschrifteten Tags und
  Status-Label-Zellen in `DeckParser.cs` (`Tags`, `LabelledTags`, `Cell`).
- Hier vorhanden: `generation/common/heading_attributes.py` kennt nur `.closing` und
  `layout="…"` (vorgezogen in E04-S01); `markdown/parser.py` hat weder Container noch `==`;
  `FrontMatter.status_labels()` liest `status.<kategorie>` bereits (E02-S01).
- Die Syntax selbst bleibt wie in DocLibs (Entscheidung E02); die PTA-eigenen Ergänzungen aus
  E04-S03/E04-S04 (Fazit-Box, Kommentarbox, Agenda, Zwischenfazit, Zitat, Kontakt) werden in
  denselben Modulen registriert, damit auch Word und PDF sie kennen.

## Vorgeschlagener Ansatz

1. **Parser** (`markdown/parser.py`): `mdit_py_plugins.container` mit einer Regel, die jeden Namen
   annimmt (geprüft wird erst in Schritt 3; Name und Argumente stehen in `token.info`),
   verschachtelt über längere Zäune (`::::` um `:::`); `mdit_py_plugins.mark` für `==text==`;
   eine eigene Core-Regel für GitHub-Alerts: beginnt der erste Absatz eines Zitats mit `[!ART]`,
   wird die Markierung entfernt und `blockquote_open.meta["alert"] = "NOTE"` gesetzt.
2. **Heading-Attribute** (`generation/common/heading_attributes.py`): `dark: bool`,
   `kicker: str | None` ergänzen (Port von `HeadingAttributes.Split`, gleiche Regex, gleiche
   Meldungen, „name kicker twice"); neu `check_level(attributes, level, format)`: `.closing` nur
   auf `#`, `.dark`/`kicker` nur auf `##`, `layout` auf beiden. `VALID` wächst mit.
3. **Layout-Syntax** (`generation/common/layout_syntax.py`): Port von `LayoutSyntax` —
   `CONTAINERS`, `ALERTS`, `check_container(name, arguments, format)`, `is_important(kind,
   format)`, `column_widths("1:2")` — und `check(tokens, format, line_offset)`, das alle Container,
   Alerts und Heading-Attribute eines Dokuments prüft und die Zeile in die Meldung schreibt.
4. **Farbige Wörter** (`generation/common/coloured_words.py`): Port von `ColouredWords.Apply` als
   generische Funktion über Runs (`text`, `is_code`, `with_text`, `colour`), Code und
   Zeilenumbrüche maskiert; Kategorien aus `design.colors.StatusCategory`; Meldung
   „'[late]{.red}' names no colour. Valid: {.success}, …".
5. **Token-Hilfen** (`generation/common/layout_tokens.py`): `tags(inline)` (Absatz aus ≥ 2
   Code-Spans), `labelled_tags(list)` (Listenpunkte, die mit Code-Span beginnen), `label_cell(cell)`
   (Tabellenzelle = genau ein Code-Span), `marked_row(row)` (erste Zelle ganz `==…==`),
   `only_images(inline)` (Bildreihe, ≥ 2 Bilder) — bisher teils doppelt in den Writern.
6. **Einbindung:** `DocxGenerator` und `PptxGenerator` rufen `layout_syntax.check` vor dem
   Schreiben auf und kennen die neuen Token (bis E03-S03/E04-S03 schlicht: Containerzäune und
   `==` entfallen, der Inhalt bleibt). Gültige Front-Matter-Schlüssel bleiben `status.*`.
7. **Tests** aus DocLibs übernehmen: `SlideLayoutTests.Mistakes_Throw` und `LabelMistakes_Throw`
   (Meldungen „Unknown container '::: card'. Valid containers: …", „takes no arguments",
   „Unknown alert '[!HINT]'", „names no label category", „assigned to two categories"),
   `Braces_ThatAreNoAttributes_StayInTheTitle` (`## Sets {a, b}`),
   `ColouredWordsTests` (`[a] {.success}`, `[a]{.success extra}`, `` `[a]{.success}` ``,
   `[a](https://example.com){.x}` bleiben Text), `SlideLayoutSyntaxTests.Mistakes_Throw_LikeInDecks` —
   jeweils für DOCX und PPTX.

## Akzeptanzkriterien

- [x] `layouts.md` aus DocLibs (ins Deutsche übertragen, `labels.` → `status.`) wird von DOCX und
      PPTX ohne Fehler angenommen.
- [x] Jeder Fehlerfall der DocLibs-Tests wirft in DOCX und PPTX `DocumentConversionError` mit
      derselben Meldung und Zeilennummer.
- [x] Geschweifte Klammern und eckige Klammern, die keine Attribute bzw. farbigen Wörter sind,
      bleiben Text.
- [x] Die bestehenden Rundreise-Tests (DOCX, PPTX) bleiben grün.

## Offene Fragen

1. Wie heißen die **neuen, PTA-eigenen** Syntaxelemente, die DocLibs nicht kennt? Vorschlag
   englisch wie die übrige Syntax (`::: conclusion` für die Fazit-Box, `::: comment` für die
   Kommentarbox, `{.agenda}`, `{.interim}` für das Zwischenfazit, `{.quote}`, `{.contact}`) —
   oder deutsch nach den PTA-Begriffen (`::: fazit`, `::: kommentar`, `{.agenda}`,
   `{.zwischenfazit}`, `{.zitat}`, `{.kontakt}`)? Die Stories E04-S03/E04-S04 verwenden bis zur
   Antwort die englischen Namen.

> (2026-11-07) Englisch wie die übrige Syntax (`::: conclusion`, `::: comment`, `{.agenda}`, `{.interim}`, `{.quote}`, `{.contact}`); gilt auch für alle späteren Epics (E14–E17).

## Notizen

- `layout="…"` bleibt wie in E04-S01; nur Word und PDF lassen es fallen.

## Implementierungsnotizen

Umgesetzt am 2026-11-07 von `docs-2`.

**Was entstand**

- `markdown/parser.py`: Container-Plugin (`mdit_py_plugins.container`, Name `layout`) nimmt jeden
  Namen an — Token `CONTAINER_OPEN`/`CONTAINER_CLOSE`, `container(token)` liefert
  `(name, argumente)`; verschachtelt über längere Zäune. Core-Regel `alerts` vor `inline`: steht
  im ersten Absatz eines Zitats eine Zeile `[!ART]`, fällt sie weg und
  `blockquote_open.meta[ALERT]` ist die Art in Großbuchstaben (war die Zeile der ganze Absatz,
  fällt der Absatz weg; `[!TIP] Text` in derselben Zeile bleibt Text, wie bei GitHub).
- `markdown/mark.py`: `==mark==` als eigene Inline-Regel (`mark_open`/`mark_close`) nach der
  Durchstreichen-Regel von markdown-it-py — **mdit-py-plugins 0.6.1 hat kein `mark`-Plugin**,
  anders als der Plan annahm. Keine neue Abhängigkeit.
- `generation/common/heading_attributes.py`: `dark`, `kicker`, `block` (die Attribute wie
  geschrieben); Doppeltes allgemein („name kicker twice", „name .dark twice"); `check_level`;
  `VALID`, `VALID_ON_SECTION`, `VALID_ON_SLIDE`.
- `generation/common/layout_syntax.py`: `CONTAINERS`, `ALERTS`, `check_container`,
  `is_important`, `column_widths("1:2")`, `columns(parts, any_empty, arguments, format)` (Port von
  `ColumnWidths` mit Teilezahl, für E04-S03), `heading`, `without_attributes`, `coloured`,
  `token_text`/`token_is_code` und `check(tokens, format, line_offset)`.
- `generation/common/coloured_words.py`: generisches `apply` über Runs (Port von
  `ColouredWords.Apply`), `PATTERN`, `category`, `masked`.
- `generation/common/layout_tokens.py`: `tags`, `labelled_tags`, `label_cell`, `is_marked`,
  `marked_row`, `only_images` auf markdown-it-Token.
- Einbindung: `DeckParser.parse` und `BodyWriter.write` rufen `layout_syntax.check` direkt nach
  dem Tokenisieren auf; beide `generate()` rufen `front.status_labels()` (vorher wurde ein
  falsches `status.<x>` nirgends geprüft). Überschriften gehen in beiden über
  `without_attributes`, Inline-Token über `coloured`. DOCX lässt alle Heading-Attribute weg.
- Tests: `tests/generation/common/test_layout_syntax.py` (DOCX und PPTX parametrisiert: Beispiel
  `layouts.md`, alle Fehlerfälle mit Zeile, Klammern bleiben Text, farbige Wörter, Zäune und
  Markierungen), `tests/generation/common/test_layout_parts.py` (Einzelteile),
  `tests/markdown/test_parser.py` (Container, Markierung, Alerts). 178 → 266 Tests (+1 übersprungen
  wie bisher). Beispiel: `tests/generation/common/samples/layouts.md` (deutsch, `status.*`, um
  eine Zeile mit farbigen Wörtern ergänzt). Zum Ansehen: `.tmp/review/layouts.docx`, `layouts.pptx`.
- Doku: `docs/verwendung.md` (Abschnitt „Folien-Syntax"), `docs/anleitung.md` (5. „Folien-Syntax"),
  `docs/ki-anleitung.md` (Regeln Word und Präsentation, Abschnitt „Folien-Syntax"); `ai/Gedächtnis.md`.

**Entscheidungen und Abweichungen**

- Grundlage war `~/mvv/vt-tools-libs` (DocLibs selbst liegt nicht lokal vor). Übernommen ist nur,
  was der Plan nennt: Containerliste `cards, rows, panel, statement, columns` (ohne `notes`,
  `scene` — E09-S01/E09-S04), Heading-Attribute `.closing`, `.dark`, `kicker`, `layout` (ohne
  `#id`, `data-steps`, `transition`, `tint`, `.accent` und ohne unquotierte Werte `key=value`).
- Fehlermeldungen von `check` beginnen mit **`Line N: `** (Zeile im Markdown, Front Matter
  mitgezählt). Der PPTX-Parser hängt bei seinen älteren Meldungen weiter `(line N)` an; das ist
  nicht vereinheitlicht.
- Front-Matter-Fehler zu `status.*` haben keine Zeile (wie alle Front-Matter-Fehler seit
  E02-S01) und heißen „names no **status** category" statt „names no label category" — die
  Meldung aus E02-S01 bleibt, weil der Schlüssel `status.` heißt.
- Die gültigen Farben stehen in der Reihenfolge von `StatusCategory`
  (`{.success}, {.warning}, {.danger}, {.info}, {.neutral}`), nicht in der von DocLibs
  (`success, info, warning, danger, neutral`).
- `.closing` auf `##` meldet weiter „{.closing} goes on a '#' heading: the closing slide" (jetzt
  mit Liste der gültigen `##`-Attribute); `.dark`/`kicker` auf `#` sind neu ein Fehler.
- Farbige Wörter werden auf **Token-Ebene** zerlegt, nicht auf den Runs der Writer: PPTX schreibt
  einen Softbreak als Leerzeichen-Run, auf Run-Ebene ginge ein Wort sonst über den Umbruch.
  `coloured_words.apply` bleibt generisch, wie geplant. Bis zur Gestaltung sind farbige Wörter in
  DOCX und PPTX nur fett, ohne Klammern.
- `layout_tokens.only_images` verlangt wie DocLibs ≥ 2 Bilder; das DOCX-eigene `_only_images`
  (≥ 1 Bild = Abbildung) ist absichtlich nicht ersetzt. Die Writer nutzen `layout_tokens` noch
  nicht — das tun E03-S03/E04-S03.
- Die Fehlerfälle „each card starts with a ### heading", „starts with **bold** text" und
  „two or three columns" aus `SlideLayoutTests` prüfen die Struktur beim Zeichnen und gehören zu
  E04-S03/E03-S03; `layout_syntax.columns` ist vorbereitet, wird aber noch nicht aufgerufen.

**Warnungen**

- **Warnung:** Die PTA-eigenen Namen (`::: conclusion`, `::: comment`, `{.agenda}`,
  `{.interim}`, `{.quote}`, `{.contact}`) sind **noch nicht registriert** — sie sind heute ein
  Fehler „Unknown …". Vorsichtigste Wahl: angenommen wird nur, was auch eine Wirkung bekommt;
  E04-S03 bzw. E04-S04 tragen sie in `layout_syntax.CONTAINER_NAMES` bzw.
  `heading_attributes` (inkl. `VALID*`) ein, mit Meldungstexten, wenn sie auf der falschen Ebene
  stehen.
- **Warnung:** Der PDF-Teil (`Mistakes_Throw_LikeInDecks` für PDF) folgt mit E05-S04; dort ist
  in den Notizen vermerkt, was aufzurufen ist.

**Prüfpunkte**

- `.tmp/review/layouts.docx` und `layouts.pptx` ansehen: Inhalt der Container steht als normale
  Blöcke, Alerts sind Zitate ohne Markierung, `==…==` ist normaler Text.
- Ob `Line N: ` als Präfix gefällt oder alle Meldungen auf ein Format gebracht werden sollen.

**Offene Punkte**

- Gestaltung: Word E03-S03, PowerPoint E04-S03/E04-S04, PDF E05-S04.
