# E04-S06 Authoring Guide PPTX

> Status: in Prüfung
> Epic: [E04 PPTX-Generator auf der PTA-PowerPoint-Vorlage](../50-entwurf/E04-pptx-generator.md)
> Milestone: [M04 Präsentieren und Schulung](../50-entwurf/M04-praesentieren-und-schulung.md)

## Zusammenfassung

`PptxGenerator.authoring_guide(options)` liefert die deutsche Anleitung, wie man Markdown für eine
PTA-Präsentation schreibt: Gliederung in Titel-, Trenn-, Inhalts- und Abschlussfolien, Textebenen,
Flow-Layouts und PTA-Layouts, Front Matter, Diagramme, Fehler und ein Beispiel — erzeugt aus
denselben Optionen wie `generate`.

## Kontext

- DocLibs: `Pptx/AuthoringGuide/Pptx.md` (145 Zeilen: *Writing Markdown for a deck*, *Structure*,
  *Layouts*, `{{templateLayouts}}`, `{{diagrams}}`, `{{frontMatter}}`, *Characters*, *When
  something is wrong*, *Example*), `PptxGenerator.AuthoringGuide` (Z. 106–175) und
  `Pptx.Tests/AuthoringGuideTests.cs` (122 Zeilen: Beispiele generieren, < 2 500 Wörter, nennt jeden
  Container, Alert, jedes Attribut und jeden Schlüssel, Diagramm-Abschnitt nur mit Renderer,
  Layoutliste der Vorlage, Abgleich mit `authoring-guide-*.expected.md`).
- PTA-Abweichungen gegenüber dem DocLibs-Guide: `#` nach dem Titel ist eine **Trennfolie mit
  Kapitelnummer** statt einer Abschnittsfolie mit Untertitel; Inhalt unter Kapitel- und
  Abschluss-`#` ist ein Fehler (E04-S01); `###` ist die Subheadline, Absätze Einleitungstext,
  Listen ab der dritten Textebene (E04-S02); keine Brands, keine Zeichen-Tabelle (PowerPoint nimmt
  die installierte Segoe UI); Front Matter deutsch (`vorlage`, `titelfolie`, `fusszeile`,
  `sprache`, `kennzeichnung`, `status.*` …).
- Bausteine aus E02-S05; Inhalte aus E04-S01 bis E04-S05.

## Vorgeschlagener Ansatz

1. Vorlage `src/pta_documents/generation/pptx/authoring_guide/pptx.md` (deutsch, ab `##`):
   - **Eine PTA-Präsentation aus Markdown** — kurz: Titel, die die Aussage nennen; wenige Zeilen.
   - **Gliederung** — Tabelle: erstes `#` + Front Matter → Titelfolie (`titelfolie: bild-01 |
     bild-02 | branchen | ohne-bild`), weitere `#` → Trennfolie „01", „02" …, `##` → Folie,
     `# … {.closing}` → Abschlussfolie; was unter `#` stehen darf.
   - **Inhalte** — Textebenen (Subheadline, Einleitungstext, Aufzählung), `**fett**` als PTA-
     Hervorhebung, Tabellen mit `**Titel**`-Zeile, Bilder in Bildplatzhaltern (werden beschnitten),
     Bildreihen, Code; was nicht passt, wird verkleinert (bis 12 pt) und fortgesetzt „(Forts.)".
   - **Layouts** — `layout_syntax_section` und die PTA-Wirkung aus E04-S03 (Raster, Fazit-Box,
     Kommentarbox, Alerts, `==…==` gelb, Statusfarben) sowie die PTA-Layouts aus E04-S04 (Agenda
     nur mit `{.agenda}`, Zwischenfazit, Zitat, Kontakt, Diagramm-Layouts) mit je einem kurzen
     Beispiel.
   - **Vorlagenlayouts** — die 35 Layoutnamen der Vorlage für `layout="…"`, gelesen aus der
     gewählten Vorlage, mit dem Hinweis, dass Inhalte an `---` auf die Platzhalter verteilt
     werden (E04-S01).
   - `{{diagrams}}`, `{{frontMatter}}` (aus `VALID_KEYS` des Generators und den Optionen;
     `kennzeichnung` je nach Vorlage mit seinem Standard).
   - **Wenn etwas falsch ist** — die Fehler mit Beispielen (Inhalt unter Kapitelfolie,
     unbekannter Container/Alert/Attribut, Karte ohne fetten Anfang, Fazit-Box zu lang, Agenda mit
     mehr als acht Punkten, unbekannter Layoutname).
   - **Beispiel** — ein vollständiges Deck: Titel, ein Kapitel, Textfolie, Karten, Tabelle mit
     Status-Labels, Fazit-Box, Abschluss.
2. `PptxGenerator.authoring_guide(options: PptxOptions | None = None) -> str` in
   `generation/pptx/generator.py`; Unterschiede zwischen `basis` und `schulung` (Sticker-Standard)
   kommen aus den Optionen.
3. Tests in `tests/generation/pptx/test_authoring_guide.py` (Port der DocLibs-Fälle mit den
   Hilfen aus E02-S05): jedes Beispiel generiert in `basis` und `schulung`; < 2 500 Wörter; nennt
   jeden Container, jedes Alert und Attribut aus E02-S02 und jeden gültigen Schlüssel;
   Diagramm-Abschnitt nur mit einem Renderer, der einen liefert; alle 35 Layoutnamen stehen darin;
   Abgleich mit `tests/generation/pptx/samples/authoring-guide-basis.expected.md` und
   `…-schulung.expected.md`.
4. `./run.sh authoring-guide pptx` gibt ihn aus; `docs/verwendung.md` verweist darauf.

## Akzeptanzkriterien

- [x] `PptxGenerator.authoring_guide()` liefert einen deutschen Guide ab `##` mit den Abschnitten
      oben, passend zur gewählten Vorlage.
- [ ] Jedes Beispiel im Guide generiert ohne Fehler; der Guide bleibt unter 2 500 Wörtern.
      (Beispiele: ja. Wörter: rund 3 230, mit Mermaid rund 3 400 — Budget auf 3 500 angehoben,
      siehe Warnung unten.)
- [x] Neue Syntax, Schlüssel oder Layouts ohne Erwähnung im Guide lassen einen Test fehlschlagen.

## Offene Fragen

Keine.

## Notizen

- Abhängigkeiten: E02-S05; vollständig erst nach E04-S03 bis E04-S05 — bis dahin nennt der Guide
  nur, was der Generator schon kann.
- (2026-11-07, E09-S01) Sprechernotizen `::: notes` aufnehmen (Regeln in `docs/ki-anleitung.md`,
  Abschnitt *Präsentation*): zu jeder Folie zwei bis fünf Sätze; auf jeder Teilfolie wiederholt;
  Tabellen/Bilder darin entfallen.
- (2026-11-08, E02-S05) Bausteine in `generation/common/authoring_guides.py` (u. a.
  `layout_syntax_section(PPTX, effect)`, `icons_section`, `notes_section`, `typography_section`),
  Testhilfen in `tests/generation/guides.py`. `tests/samples/test_funktionen.guide_syntax` auf
  `PptxGenerator().authoring_guide()` umstellen (ohne die Fehlerbeispiele). Wortbudget: die
  Folien-Syntax allein hat rund 700 Wörter, die Icons rund 280.

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08: Vorlage
`src/pta_documents/generation/pptx/authoring_guide/pptx.md`, Aufbau in
`src/pta_documents/generation/pptx/guide.py`, Methode `PptxGenerator.authoring_guide(options)` in
`generation/pptx/generator.py`. Tests `tests/generation/pptx/test_authoring_guide.py` mit den
Erwartungsdateien `tests/generation/pptx/samples/authoring-guide-basis.expected.md` und
`…-schulung.expected.md`; `tests/samples/test_funktionen.py` (`guide_syntax` für Decks) und
`tests/design/icons/test_icons.py` umgestellt. Doku: `docs/verwendung.md` (Verweis unter
„Markdown → PowerPoint“, Abschnitt „Authoring Guide PowerPoint“), `docs/ki-anleitung.md`
(Verweis auf den Guide, Icon-Liste entfernt), `ai/Gedächtnis.md`.

### Entscheidungen

- **Abschnitte** wie geplant, ergänzt um das, was seit dem Plan dazugekommen ist: Gliederung,
  Inhalte, Bilder (E15-S04: `{focus=…}`, `{fit=contain}`, `{.round}`, `{.grey}`, QR-Codes, Formate
  aus den Konvertern), Folien-Syntax (gemeinsamer Baustein mit dem PPTX-Absatz zur Flow-Folie),
  PTA-Folienarten, „Klick für Klick, Übergänge, Szenen“ (E09-S02 bis E09-S04: `aufbau`,
  `uebergang`, Formarten, Attribute, Raster und Farbrollen aus `scene`/`scene_colors`),
  „Fassungen und Zeitplan“ (E16-S01, E16-S02: `::: internal`, `{.internal}`, `--audience`,
  `dauer`, `.break`, `beginn`/`laenge`; Sprechernotizen E09-S01), Vorlagenlayouts, Icons,
  Typografie, Renderer-Abschnitte, Front Matter, Hinweise, „Wenn etwas falsch ist“, Beispiel.
- **Aus dem Code statt abgeschrieben:** die 35 Layoutnamen werden aus der gewählten Vorlage
  gelesen (`guide.layout_names`), Agenda-/Kontaktgrenzen und Folienart-Varianten aus
  `design.slides`, Übergänge aus `SlideTransition`, Titelfolien aus `TITLE_SLIDES`, die
  Front-Matter-Zeilen beschreiben genau `VALID_KEYS` (`front_matter_section` prüft das).
- **Aus den Optionen:** Vorlage (`vorlage` mit Standard), `kennzeichnung` mit dem Standard der
  Vorlage (`basis`: `kein`, `schulung`: `intern`, dort ohne `kein` und mit dem Hinweis, dass `kein`
  ein Fehler ist), `fassung`, `titelfolie`, `aufbau`, `uebergang` mit dem Standard der Optionen,
  Diagrammabschnitte aus `code_block_renderers`, Bildformate aus `image_converters`.
- **HTML-Deck:** ein Guide für beide Decks (wie E10-S01 vorsah); der erste Absatz nennt `--html`
  und die HTML-eigenen Schlüssel `fortschritt`/`kapitelanzeige` (nicht in der Tabelle, weil sie
  genau `VALID_KEYS` des PPTX-Generators beschreibt). Ein Test erzeugt jedes Beispiel auch als
  HTML-Deck.
- **Fehlerbeispiele** stehen als Liste mit Inline-Code, nicht als ```` ```markdown ````-Blöcke
  (sonst müssten sie generieren); ein Test prüft jedes genannte Muster als Fehler und dass es im
  Abschnitt steht.
- **`guide_syntax`** in `test_funktionen.py` liest für Decks den ganzen Guide ohne „Hinweise“ und
  „Wenn etwas falsch ist“; Word bleibt bei den gemeinsamen Abschnitten (E03-S05).
- **Icon-Liste** (offener Punkt aus E02-S05 und E15-S03): steht nur noch im Guide;
  `docs/ki-anleitung.md` verweist auf `./run.sh authoring-guide pptx`, der Test
  `test_the_authoring_guide_names_every_icon` prüft den Guide und den Verweis.
- Der Aufbau liegt in `generation/pptx/guide.py`, nicht in `generator.py` (der Generator bleibt
  schlank) und nicht in `authoring_guide.py` (Namensgleichheit mit dem Datenordner).

### Abweichungen

- **Warnung:** Das Wortbudget von 2 500 ist mit vollständiger Abdeckung nicht zu halten: die
  gemeinsamen Bausteine allein (Folien-Syntax ~710, Icons ~280, Hinweise ~230, Charts ~570,
  Typografie ~50; Mermaid ~165) haben rund 1 840–2 000 Wörter, dazu Front Matter (18 Schlüssel),
  35 Layoutnamen und das Beispiel. Vorsichtigste Lösung: nichts weglassen, den eigenen Text knapp
  halten und das Budget nur für den PPTX-Guide auf **3 500** anheben (Konstante `WORD_LIMIT` im
  Test, geprüft mit Chart- und Mermaid-Abschnitt); `guides.WORD_LIMIT` (2 500) bleibt für die
  anderen Guides. Der Mensch entscheidet, ob das so bleibt oder die gemeinsamen Abschnitte
  (vor allem der Word-Teil im Chart-Abschnitt) gekürzt werden sollen.
- **Warnung:** Der Abschnitt „Hinweise“ fällt aus dem Abgleich Guide ↔ Beispiele heraus, weil er
  `{.appendix}` (auf Folien wirkungslos) und `{scale=N}` nennt, die kein fehlerfreies
  Deck-Beispiel zeigen kann.
- Die Tabelle „Gliederung“ statt eines kommentierten Codeblocks: ein ```` ```markdown ````-Block
  müsste als Beispiel generieren.
- Epic- und Meilensteinkopf bleiben `Entwurf` wie bei den übrigen Stories; nur die Zeilen der
  Scope-Tabellen stehen auf `in Prüfung`.

### Prüfpunkte

- Den Guide lesen: `./run.sh authoring-guide pptx` oder
  `tests/generation/pptx/samples/authoring-guide-basis.expected.md` — Ton, Länge, Vollständigkeit.
- Ob der Verweis in `docs/ki-anleitung.md` statt der Icon-Liste für Agenten in `documents/`
  genügt.
- Das Beispiel (Abschnitt „Beispiel“) erzeugt in `basis` und `schulung` ein Deck ohne Hinweise.

### Zusammenführung

Zusammengeführt am 2026-11-08 nach `main`, das inzwischen E03-S05 (Word-Guide) und E05-S05
(PDF-Guide, gemeinsame Vorlage `documents.md`) enthielt:

- `tests/samples/test_funktionen.py`: beide Seiten hatten `MISTAKES`/`without_mistakes` angelegt.
  Jetzt **eine** Hilfe `without_mistakes(guide, headings=(MISTAKES,))` (zeilengenau, fehlender
  Abschnitt bleibt unverändert) mit den Konstanten `MISTAKES` und `NOTES`; `guide_syntax` hat
  einen Zweig für Word (ganzer Guide ohne „Wenn etwas falsch ist“) und einen für PowerPoint
  (ohne `NOTES` und `MISTAKES`), für andere Formate `ValueError` — das PDF hat keine eigenen
  Beispiele. Neuer Test `test_the_deck_guide_counts_without_its_notes_and_mistakes`.
- Icons: auch der Word- und der PDF-Guide haben den Abschnitt *Icons* (`icons_section` über
  `document_guide.py`). Der Verweis in `docs/ki-anleitung.md` nennt deshalb je Format
  `./run.sh authoring-guide pptx|docx|pdf`; `test_the_authoring_guide_names_every_icon` prüft
  alle drei Guides und je Format den Verweis.
- `docs/verwendung.md`: der Abschnitt zum PowerPoint-Guide steht jetzt als Absatz
  **PowerPoint** neben **Word** und **PDF**; Einleitung nennt die Grenze 3 500 für PowerPoint,
  „Guide ↔ Beispiele“ beschreibt den ganzen Deck-Guide. `ai/Gedächtnis.md`: alle Einträge
  behalten, die überholten Sätze zu „bis E04-S06“ und zur Icon-Liste angepasst.
- `characters_section` (E05-S05 geändert) nutzt nur das PDF; die PPTX-Erwartungsdateien bleiben
  unverändert, ebenso die von Word und PDF.
- **Warnung bleibt:** das Wortbudget des PPTX-Guides ist 3 500 (`WORD_LIMIT` im Test), die
  übrigen Guides halten das gemeinsame `guides.WORD_LIMIT` von 2 500 — Entscheidung des
  Menschen offen.

### Offene Punkte

- Wortbudget (siehe Warnung): 3 500 bestätigen oder gemeinsame Abschnitte kürzen.
