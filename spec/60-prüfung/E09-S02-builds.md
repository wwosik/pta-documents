# E09-S02 Builds: Inhalte erscheinen Klick für Klick

> Status: in Prüfung
> Epic: [E09 Präsentieren](../50-entwurf/E09-praesentieren.md)
> Milestone: [M04 Präsentieren und Schulung](../50-entwurf/M04-praesentieren-und-schulung.md)

## Zusammenfassung

Eine Zeile `{.build}` vor einer Liste lässt deren Punkte einzeln erscheinen, vor Karten, Reihen,
Bildreihen und Spalten je Element, vor einer Tabelle die ganze Tabelle; `{.frag}` lässt einen
beliebigen Block mit dem nächsten Klick erscheinen. Jeder Build ist ein Fade, wie PowerPoint ihn
schreibt. Ein Front-Matter-Schlüssel baut alle Listen auf.

## Kontext

- vt-tools-libs: `~/mvv/vt-tools-libs/src/VtToolsLibs.DocumentGeneration.Pptx/Animations.cs`
  (111 Zeilen): `Build(Step, ShapeId, Paragraph, Target)`, `Timing(builds)` schreibt `p:timing`
  mit Hauptsequenz (`mainSeq`), je Klick ein `p:par` mit `clickEffect` für das erste und
  `withEffect` für weitere Ziele, Effekt `presetID=10` (Fade) mit `p:set style.visibility` und
  `p:animEffect filter="fade"` über 500 ms; `p:bldLst` mit `p:bldP build="p"` für absatzweise
  gebaute Textformen, `p:bldP animBg="1"` für ganze Textformen, `p:bldGraphic`/`p:bldAsOne` für
  Tabellen; Bilder und Gruppen ohne Eintrag. Regeln (`docs/VtToolsLibs.DocumentGeneration.Pptx.md`,
  *Presenting*): `{.build}` als Zeile allein vor Liste/Karten/Reihen/Tabelle, `{.frag}` vor jedem
  anderen Block oder als erste Zeile eines Absatzes, Front Matter `build: lists` baut jede
  äußere Liste, Schritte in Markdown-Reihenfolge, ein Block auf einer Fortsetzungsfolie baut
  dort. `{.build}` direkt über einer Tabelle (ohne Leerzeile) markiert die Tabelle.
- Hier: `markdown/parser.py` kennt keine Zeilen aus nur `{.build}`; `heading_attributes.py`
  (50 Zeilen) parst nur Heading-Attribute. `writer.py` schreibt Text in den Körperplatzhalter
  (`write_paragraphs`, Z. 430), Tabellen und Bilder als Formen; Flow-Layouts kommen mit E04-S03.
  python-pptx hat keine Animations-API; `p:timing` wird mit lxml an `slide._element` angehängt
  (`generation/common/openxml.py` hat die Namensraum-Hilfen).
- Formen-IDs (`cNvPr id`) vergibt python-pptx fortlaufend; die Builds brauchen sie erst nach dem
  Anlegen der Formen, also wird am Ende jeder Folie geschrieben.

## Vorgeschlagener Ansatz

1. **Syntax** (`generation/common/block_markers.py`, Port von `BlockMarkers.cs` aus vt-tools-libs,
   55 Zeilen): eine Zeile aus nur `{.build}` oder `{.frag}` wird als Marker für den folgenden
   Block gelesen, auch als erste Zeile eines Absatzes; jeder andere Klassenname in einer solchen
   Zeile ist ein Fehler: „Unknown block marker '{.wide}' on line 7. Valid markers: {.build},
   {.frag}." Die Erkennung läuft über die Zeilen der Token (`token.map`) vor dem Parser der
   Generatoren, damit Word und PDF die Marker ebenso kennen (und still entfernen).
2. **Modell:** `Item.step: int` (0 = mit der Folie) in `generation/pptx/model.py`; `Paragraph`
   trägt den Schritt je Absatz, `Table`, `Image(s)`, `Code` und die Container aus E04-S03 je
   Block. `DeckParser` zählt Schritte je Folie in Markdown-Reihenfolge: `{.build}` vor einer
   Liste vergibt jedem Absatz jeder Ebene einen eigenen Schritt, vor Karten/Reihen/Spalten/
   Bildreihe je Element, vor einer Tabelle einen für die ganze Tabelle; `{.frag}` einen für den
   Block. `PptxOptions.build_lists: bool` (Front Matter `aufbau: listen | nein`, Schlüssel in
   `front_matter.Keys`) markiert jede Liste, die nicht in einer anderen steckt.
3. **Schreiben** (`generation/pptx/animations.py`): `Build(step, shape_id, paragraph, target)` und
   `timing(builds) -> etree._Element` als Port von `Animations.Timing`, XML eins zu eins wie
   PowerPoint. `DeckWriter` sammelt beim Schreiben jeder Form ihre Builds (Textplatzhalter:
   Absatzindex nach dem Teilen durch `fitting`; Tabelle: `Graphic`; Bild: `Other`) und hängt
   `p:timing` am Ende der Folie an. Nach dem Teilen einer Folie beginnen die Schritte auf jeder
   Teilfolie wieder bei 1.
4. **Word und PDF:** Marker werden entfernt, der Block bleibt (E03-S03, E05-S04 verweisen hierher).
   **Konverter** (E07-S03): `p:timing` wird nicht gelesen.
5. **Tests** (`tests/generation/pptx/test_animations.py`, Port von `AnimationTests.cs` aus
   vt-tools-libs): Liste mit drei Punkten → drei Klicks mit `pRg` 0..2; Tabelle → `bldGraphic`;
   Bild → kein `bldLst`-Eintrag, aber Effekt; `aufbau: listen` baut äußere Listen, nicht
   verschachtelte; Marker ohne Block und unbekannte Marker werfen mit Zeile; eine geteilte Folie
   hat auf beiden Teilen `p:timing`; die Rundreise bleibt gleich (Marker erscheinen nicht im
   Markdown des Konverters — bewusst, siehe Frage 2).
6. **Doku:** `docs/anleitung.md`, `docs/ki-anleitung.md`, `samples/funktionen/`, Guide E04-S06.

## Akzeptanzkriterien

- [x] `{.build}` vor einer Liste lässt die Punkte in PowerPoint einzeln per Klick erscheinen, mit
      Fade; die Liste bleibt ein bearbeitbarer Platzhaltertext mit den Aufzählungszeichen der
      Vorlage.
- [x] `{.build}` vor einer Tabelle und `{.frag}` vor einem Block zeigen den Block als Ganzes auf
      einen Klick; `aufbau: listen` baut alle äußeren Listen.
- [x] Ein unbekannter Marker oder ein Marker ohne folgenden Block wirft mit Zeilennummer.
- [x] Word und PDF erzeugen aus demselben Markdown ohne Fehler dasselbe wie ohne Marker.
- [ ] PowerPoint öffnet Decks mit Builds ohne Reparaturmeldung (Prüfpunkt des Menschen).

## Offene Fragen

1. Name des Front-Matter-Schlüssels: `aufbau: listen` (Vorschlag), `animation: listen` oder
   `klickweise: ja`?

> (2026-11-07) `aufbau: listen`.
2. Soll der PPTX-Konverter Builds als `{.build}` zurückgeben, damit ein Deck → Markdown → Deck
   seine Animationen behält? Vorschlag: nein, Animationen sind kein Inhalt; die Rundreise prüft
   Inhalt.

> (2026-11-07) Nein.

## Notizen

- (2026-11-07) Erweiterung nach Entscheidung im Epic (Frage 1): neben Fade auch `{.build=appear}`, `{.build=fly}`, `{.build=wipe}` als Eingang; `{.exit}` (Element verschwindet beim Klick) und `{.emphasize}` (Hervorhebung in PTA-Blau beim Klick). Die Attribute werden in `heading_attributes`/`layout_syntax` (E02-S02) registriert; der Guide nennt sie. Der Konverter ignoriert sie weiterhin.

- Abhängig von E04-S03 nur für Karten, Reihen und Spalten; Listen, Tabellen, Bilder und Code
  lassen sich vorher umsetzen.

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08. Neu: `markdown/block_markers.py` (`Marker`, `read`,
Kernregel `block_markers_rule`, `MARKER`/`ERROR`, `NAMES`, `ENTRANCES`),
`generation/pptx/animations.py` (`Builds`, `Build`, `Target`, `timing`). Angepasst:
`markdown/parser.py` (Regel nach `alerts`), `markdown/front_matter.py` (`Keys.BUILD` =
`aufbau`, `Keys.BUILD_LISTS`), `generation/common/layout_syntax.py` (wirft `meta[ERROR]`),
PPTX `model.py` (`Effect`, `Click`, Feld `click` an `Paragraph`, `Table`, `Image`, `Code`,
`Diagram`, `Chart` und allen Flow-Blöcken außer `TextBlock`/`ImageRowBlock`, `ColumnsBlock.clicks`;
`Table.subset`/`Code.part` behalten den Klick), `parser.py` (`marked`, `at`, `paragraph_click`,
`take_each`, `read_block`, `_check_markers`), `flow_parser.py` (`read`, Klicks je Karte, Zeile,
Spalte), `writer.py` (`at`, `each`, `write_builds`, `draw_visual`/`draw_shapes`), `flow.py`,
`kinds.py` (Chart-Folie), `options.py` (`build_lists`), `generator.py` (Schlüssel `aufbau`).
Tests: `tests/markdown/test_block_markers.py` (26), `tests/generation/pptx/test_animations.py`
(25), `tests/samples/test_funktionen.py` verlangt jeden Marker und jeden Eingang im Deck.
Beispiele: Kapitel „Präsentieren" (vier Folien) in `samples/funktionen/funktionen-praesentation.md`,
`aufbau: listen` in `varianten-folien.md`, README und Rundreisen erneuert. Doku:
`docs/verwendung.md` (Abschnitt „Builds (E09-S02)", Front-Matter- und Syntax-Tabelle),
`docs/anleitung.md` („Klick für Klick", Schlüssel `aufbau`), `docs/ki-anleitung.md`;
`ai/Gedächtnis.md`.

### Entscheidungen

- **Syntax und Effekte** wie Plan und Notiz 2026-11-07: `{.build}`, `{.frag}`, `{.exit}`,
  `{.emphasize}`; `{.build}`/`{.frag}` mit `=fade` (Standard), `=appear`, `=fly`, `=wipe`.
  `{.build}` baut Listen (jeder Absatz jeder Ebene), `::: cards`, `::: rows`, `::: columns` und
  Absätze nur aus Bildern Element für Element, jeden anderen Block als Ganzes; `{.frag}` immer
  als Ganzes. Absätze in einem gebauten Block oder Element erben dessen Klick (Port von
  vt-tools-libs `current`).
- **Eine Marker-Zeile** steht als eigener Absatz vor dem Block, als erste Zeile des markierten
  Absatzes oder als letzte Zeile eines Absatzes direkt vor dem Block (so in einem Listenpunkt
  vor einer verschachtelten Liste — dort ist die Zeile in CommonMark Fortsetzung des Punkts).
  Tabellen, Listen (ab 1), Zäune, Zitate und Container unterbrechen einen Absatz, darum geht
  `{.build}` ohne Leerzeile direkt über einer Tabelle.
- **Fehler mit Zeile** (Format von `layout_syntax.check`, `Line N: …`, Zeile des Markers):
  unbekannter Marker, mehrere Klassen, Wert an `{.exit}`/`{.emphasize}`, unbekannter Eingang,
  Marker ohne Block (Ende, vor `---`, am Ende eines Containers), vor `#`/`##`, vor
  `::: notes`, zwei Marker vor einem Block, Marker mitten im Absatz, `{.emphasize}` vor
  Nicht-Text, nummerierte Liste ab ≠ 1 direkt unter dem Marker. PowerPoint zusätzlich: Marker
  unter `#` (Titel, Trenner, Abschluss) und auf PTA-Folienarten, Marker auf Teilen, die nur als
  Ganzes gelesen werden (Kartenüberschrift in `::: cards`, Kinder von `steps`/`timeline` …).
- **Klicks** über das Deck gezählt; eine Folie spielt ihre Klicks in Zahlreihenfolge. Nach dem
  Teilen (`Forts.`) baut jeder Teil, was auf ihm steht (geprüft: beide Teile haben `p:timing`,
  Absatz 0 zuerst).
- **Schreiben:** nicht mit Formen-IDs im Modell, sondern beim Zeichnen: `DeckWriter.at(slide,
  click)` merkt jede in der Zeit angelegte Form des `spTree` (auch ersetzte Platzhalter: Bild,
  Chart), Absätze kommen über `Builds.paragraphs` mit ihrem Index nach `fitting`. Eine Form, deren
  Absätze gebaut werden, oder die ein innerer Klick schon hat, wird nicht noch einmal als Ganzes
  gebaut. `p:timing` entsteht beim nächsten `new_slide` (nach `finish`) und nur für Formen und
  Absätze, die noch da sind.
- **XML** nach `Animations.cs`: `mainSeq`, je Klick `clickEffect` + `withEffect`, 500 ms;
  Fade = Preset 10, Erscheinen = 1, Hereinfliegen = 2 (Subtyp 4, von unten, `ppt_y` von
  `1+#ppt_h/2`), Wischen = 22 (Subtyp 4, `wipe(up)`), Ausgang = Exit-Preset 10 (`fade` out,
  danach `hidden`), Hervorheben = Emphasis-Preset 3 (`animClr` auf `style.color`, PTA-Blau aus
  `design.colors`). `bldP build="p"` / `animBg="1"` / `bldGraphic` mit `bldAsOne`; je Form und
  Effektklasse eine eigene `grpId` (Ausgang und Hervorhebung auf derselben Form: 0 und 1).
- **Antworten:** Schlüssel `aufbau: listen` (Frage 1), der Konverter liest keine Builds
  (Frage 2, Test `test_the_converter_reads_no_builds`).

### Abweichungen

- **Erkennung als Kernregel** des gemeinsamen Parsers (`markdown/block_markers.py`) statt als
  Zeilenvorlauf in `generation/common/block_markers.py`: so sehen Word, PDF, `check` und die
  Stilregeln ohne eigene Änderung dasselbe Markdown (keine Zeile in `generation/docx` oder
  `generation/pdf` angefasst); geprüft wird in `layout_syntax.check`, das alle Generatoren
  rufen. Meldungen im Format `Line N: Unknown block marker '{.wide}'. Valid markers: …` statt
  „… on line 7".
- **Modell:** `click: Click | None` (Nummer und Effekt) statt `step: int`, auch an Bildern und
  Flow-Blöcken; `Images` und `ImageRowBlock` tragen keinen eigenen Klick (ihre Bilder tun es).
- Die Notiz „in `heading_attributes`/`layout_syntax` registrieren": die Namen stehen in
  `block_markers.NAMES`/`ENTRANCES` (eine Stelle für alle Formate); `heading_attributes` bleibt
  unverändert, weil Marker keine Heading-Attribute sind.
- E04-S03 war umgesetzt, Karten, Zeilen und Spalten sind daher dabei.

### Warnungen

- **Warnung:** `aufbau` kennt nur PowerPoint; Word und PDF lehnen den Schlüssel wie `fusszeile`
  als unbekannt ab. Vorsichtige Wahl, weil eine Präsentation nicht als Word erzeugt wird und die
  Schlüssellisten von Word/PDF parallel in E12-S03 geändert werden. Die Marker selbst nehmen
  Word und PDF an (Test: `document.xml` und PDF byte-gleich mit und ohne Marker).
- **Warnung:** `{.exit}` und `{.emphasize}` wirken auf den ganzen Block mit einem Klick, auch vor
  einer Liste (nicht Punkt für Punkt). `{.emphasize}` färbt nur Text (Bilder, Tabellen, Rahmen
  bleiben); auf PTA-blauem Text (Überschriften auf Flow-Folien) oder dunklen Folien ist die
  Hervorhebung kaum zu sehen. Das Effekt-XML ist nur `animClr` auf `style.color` — PowerPoint
  schreibt für „Schriftfarbe" womöglich weitere Knoten; ungeprüft.
- **Warnung:** Hereinfliegen und Wischen kommen fest von unten; eine Richtung ist nicht wählbar
  (Epic: „bewusst klein halten").
- **Warnung:** Auf Titel-, Trenn-, Abschlussfolie und PTA-Folienarten (Agenda, Zwischenfazit,
  Zitat, Kontakt) sind Marker ein Fehler, nicht still ignoriert — so merkt der Schreiber, dass
  dort nichts gebaut wird. Agenda-Builds wären möglich, sind aber nicht im Plan.
- **Warnung:** `aufbau: listen` baut auch Listen in Containern (Karten, Flächen) und in einem
  mit `{.frag}` markierten Block (Fläche erscheint, dann die Punkte einzeln) — wie vt-tools-libs;
  Listen in Sprechernotizen nie.
- **Warnung:** Innerhalb eines Klicks steht die zuerst angelegte Textform vor ihrem Rahmen
  (`withEffect`, gleichzeitig) — sichtbar ist kein Unterschied, im Animationsbereich von
  PowerPoint aber die Reihenfolge.

### Prüfpunkte

- In PowerPoint öffnen (keine Reparaturmeldung) und als Bildschirmpräsentation durchklicken:
  `.tmp/review/deck-builds-list.pptx` (drei Punkte nacheinander, Fade),
  `.tmp/review/deck-builds-cards.pptx` (Karte für Karte mit Rahmen, Titel und Text),
  `.tmp/review/funktionen/funktionen-praesentation.pptx` Folien 57–60 (Liste mit zweiter Ebene
  und `{.frag}`-Absatz, Tabelle „Erscheinen", Karten „Hereinfliegen" und Hinweis „Wischen",
  Ausgang und PTA-blaue Hervorhebung), `.tmp/review/funktionen/varianten-folien.pptx`
  (`aufbau: listen`).
- Im Animationsbereich prüfen, dass die Effekte als „Verblassen", „Erscheinen", „Hereinfliegen
  (von unten)", „Wischen (von unten)", „Verblassen (Ausgang)" und „Schriftfarbe" erscheinen und
  sich bearbeiten lassen; die Liste bleibt Platzhaltertext mit den Aufzählungszeichen der
  Vorlage.
- PowerPoint-Prüfung steht aus (kein Office auf der Entwicklungsmaschine).

### Offene Punkte

- E09-S03 (Übergänge) schreibt `p:transition` vor `p:timing` (im Gedächtnis vermerkt) und nutzt
  `animations.py` mit.
- E09-S04 (Szenen): `step` als Build über `Builds`/`Target.OTHER`.
- E14-S03 (`{.calc}`) und E16-S01 (Zielgruppen) tragen ihre Marker in `block_markers.NAMES` ein
  und müssen sie in `DeckParser.marked` behandeln, sonst wirft `_check_markers`.
- E04-S06 (Guide PowerPoint) nennt die Marker, Eingänge und `aufbau`.
