# E02-S02 Folien-Syntax: Heading-Attribute, Container, Alerts, Markierungen, Status-Labels

> Status: Entwurf
> Epic: [E02 Markdown-Grundlagen der Generatoren](E02-markdown-grundlagen.md)

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

- [ ] `layouts.md` aus DocLibs (ins Deutsche übertragen, `labels.` → `status.`) wird von DOCX und
      PPTX ohne Fehler angenommen.
- [ ] Jeder Fehlerfall der DocLibs-Tests wirft in DOCX und PPTX `DocumentConversionError` mit
      derselben Meldung und Zeilennummer.
- [ ] Geschweifte Klammern und eckige Klammern, die keine Attribute bzw. farbigen Wörter sind,
      bleiben Text.
- [ ] Die bestehenden Rundreise-Tests (DOCX, PPTX) bleiben grün.

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
