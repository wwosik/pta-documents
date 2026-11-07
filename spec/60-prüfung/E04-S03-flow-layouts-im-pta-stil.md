# E04-S03 Flow-Layouts im PTA-Stil

> Status: in Prüfung
> Epic: [E04 PPTX-Generator auf der PTA-PowerPoint-Vorlage](../50-entwurf/E04-pptx-generator.md)
> Milestone: [M02 Rückmeldung und Folien-Syntax](../50-entwurf/M02-rueckmeldung-und-folien-syntax.md)

## Zusammenfassung

Die Flow-Folien aus DocLibs — `cards`, `rows`, `panel`, `statement`, `columns`, Alerts, Tags,
Kicker, `.dark` — werden auf `Nur Titel` im PTA-Raster gezeichnet, dazu die PTA-Muster Fazit-Box
und Kommentarbox; `==Markierung==` erscheint in PTA-Gelb, farbige Wörter und Status-Labels in den
Signalfarben.

## Kontext

- DocLibs: `DeckParser.cs` (Container, Karten, Zeilen, Tags: Z. 318–540), `SlideModel.cs`
  (`FlowSlide`, 15 `FlowBlock`-Typen), `DeckWriter.cs` (Flow: Z. 272–695, Größen Text 16, Karten
  14, Kartentitel 16, Kennzahl 32, Statement 26, Kicker/Chips 12 pt), `DeckWriter.Fitting.cs`
  (Flow: alle Größen zweimal um ein Achtel, Abstände halbiert, dann Teilung zwischen Blöcken),
  `SlidePalette.cs`. Tests: `SlideLayoutTests.cs` (280 Zeilen), Beispiel `layouts.md`.
- PTA-Werte ([Designanalyse](../10-analysen/2026-11-06%20pta-designstandards.md#weitere-muster)):
  Inhaltsfläche 1,33/4,62 cm, 31,20 × 13,10 cm; zwei Spalten 15,10 cm + 1,00 cm; vier Spalten
  7,00 cm; Fazit-Box 1,33/15,78 cm, 31,20 × 1,94 cm, `004676`, 18 pt fett weiß, Einzug links
  1,90 cm, „maximal 2 Zeilen"; Kommentarbox `wedgeRectCallout`, weiß, Verlaufsrand `9FD8FF` →
  `006FB9` 1,5 pt, 14 pt fett PTA-Blau; Gelb `FDDC35` als Hervorhebung, Signalfarben nur für Status.
- Lesen und Prüfen: E02-S02; Folienmodell `generation/pptx/model.py`, Fitting `fitting.py`,
  Visuals `visuals.py` aus E04-S02. Namen der PTA-Ergänzungen siehe E02-S02, Frage 1.

## Vorgeschlagener Ansatz

1. **Modell:** `Run` um `mark`, `status: StatusCategory | None`, `label` erweitern; `FlowSlide(title,
   kicker, dark, blocks)` und die Blöcke `TextBlock`, `CodeLinesBlock`, `TableBlock`,
   `ImageRowBlock`, `ColumnsBlock`, `CardsBlock`/`Card`, `RowsBlock`/`Row`, `PanelBlock`,
   `CalloutBlock`, `StatementBlock`, `TagsBlock`, `LabelledTagsBlock`, neu `ConclusionBlock` und
   `CommentBlock` in `model.py`.
2. **Parser** (`parser.py`): Flow-Erkennung wie DocLibs (Attribute `.dark`/`kicker`, ein Container
   oder Alert irgendwo, eigener Tag-Absatz); Port von `Container`, `Cards`, `Rows`, `Item`, `Flow`,
   `Tags`, `LabelledTags`, `Columns` mit denselben Meldungen. `layout="…"` mit Flow-Inhalt ist nur
   mit `Nur Titel` erlaubt, sonst Fehler.
3. **Writer** `generation/pptx/flow.py`: Port von `Stack`/`Place` auf `Nur Titel`, alle Werte als
   `FlowStyle` in `design/slides.py`:
   - Text 18 pt Light `404040` (Einleitungstext), in Karten 14 pt; Karten- und Zeilentitel 18 pt
     Segoe UI PTA-Blau (wie die Subheadline); Kennzahl 32 pt fett PTA-Blau; Statement 24 pt fett
     PTA-Blau; Kicker 12 pt fett Versalien Dunkelblau über dem Titelplatzhalter bei 1,33/1,60 cm.
   - `cards`: Rechtecke (PTA-Muster sind eckig) ohne Fläche, Rand `E6E6E6` 0,75 pt, bis vier je
     Zeile im Raster (2 × 15,10, 3 × 9,73 oder 4 × 7,00 cm, Abstand 1,00 cm).
   - `rows`: Begriff im linken Drittel, Linien `E6E6E6` 0,5 pt über jeder Zeile, unter der letzten
     `404040` — wie die Folientabelle.
   - `panel`: Fläche `E6E6E6`; `panel dark`: `004676` mit weißer Schrift.
   - `columns`: Spalten an den Rasterlinien; **genau zwei gleiche Spalten nur mit Text** nehmen
     stattdessen das Layout `Titel und Text (zweispaltig)` (PTA-Regel: Vorlagenlayouts zuerst).
   - Alerts: Fläche `E6E6E6`, Balken links 0,15 cm in PTA-Blau (`NOTE`, `TIP`) bzw. Gelb
     `FDDC35` (`IMPORTANT`, `WARNING`, `CAUTION`), Text nicht kursiv.
   - Tags: Rahmen PTA-Blau 0,75 pt, Consolas 12 pt; beschriftete Tags: Chip fett, Text daneben.
   - Code auf Fläche `E6E6E6`, Consolas 14 pt, Zeilenabstand 130 % (wie E04-S02).
   - **Fazit-Box** (`::: conclusion`): immer am Fuß der Inhaltsfläche in den Maßen der Vorlage,
     höchstens einmal je Folie, die übrigen Blöcke stapeln darüber; passt der Text bei 18 pt
     nicht in zwei Zeilen, verkleinert bis 14 pt, sonst `DocumentConversionError`.
   - **Kommentarbox** (`::: comment`): Sprechblase rechtsbündig, Breite nach Text bis zur halben
     Inhaltsbreite, Spitze nach links unten auf den vorigen Block; Ränder 0,30/0,20 cm.
4. **Zeichenformate auf allen Folien** (`writer.run_element`): `==…==` fett in Segoe UI (PTA-Regel
   Hervorhebung) mit `a:highlight` `FDDC35`; Tabellenzeile mit markierter erster Zelle: Fläche
   `FDDC35`; `[Wörter]{.x}` fett in der Signalfarbe (`STATUS_COLORS`); Status-Label-Zelle auf
   Flow-Folien: fett in der Signalfarbe, nicht zugeordnete Labels Mittelgrau.
5. **`.dark`** nach Antwort auf Frage 1.
6. **Fitting:** Port von `FitFlow` mit Untergrenze 12 pt (E04-S02); Teilung zwischen Blöcken,
   Karten, Panels, Alerts, Spalten und Fazit-Box bleiben ganz; Folgefolien „(Forts.)" behalten
   Kicker, die Fazit-Box steht nur auf der letzten.
7. **Tests:** Port von `SlideLayoutTests` (Karten, Listenform, dunkles Panel, Alert-Balken, Tags,
   Code-Liste außerhalb Container bleibt Liste, markierte Zeilen und Labels, mehrere Tabellen,
   Statement, Kicker über dem Titel), Fazit-Box-Maße = Vorlage, Kommentarbox-Form, zweispaltig →
   Vorlagenlayout; `layouts.md` → PPTX → Rundreise `layouts.roundtrip.expected.md`; Ansicht
   `.tmp/review/layouts.pptx`.

## Akzeptanzkriterien

- [x] `layouts.md` ergibt Flow-Folien auf `Nur Titel`, deren Formen innerhalb der Inhaltsfläche an
      den Rasterlinien liegen.
- [x] Fazit-Box und Kommentarbox gleichen den Mustern der Vorlagensammlung (Folien 32, 43).
- [x] Alle Farben stammen aus `design.colors`; Signalfarben erscheinen nur bei Status.
- [ ] PowerPoint öffnet das Ergebnis ohne Reparatur (Prüfpunkt für den Menschen).

## Offene Fragen

1. Die PTA-Vorlage hat kein dunkles Inhaltslayout. Was soll `## Titel {.dark}` tun:
   (a) `Nur Titel` mit dem Verlaufshintergrund von `Titelfolie ohne Bild` und weißer Schrift
   (Vorschlag), (b) Fehler mit Hinweis auf Zwischenfazit/Zitat (E04-S04), oder (c) ignorieren?

> (2026-11-07) (a) `Nur Titel` mit dem Verlauf der Titelfolie und weißer Schrift.

2. Status-Labels in Tabellen: fetter Text in der Signalfarbe (Vorschlag), oder ein Ampelpunkt
   „●" in der Signalfarbe vor dem Text in `404040` wie im Ampel-Muster der Vorlagensammlung?

> (2026-11-07) Ampelpunkt „●“ in der Signalfarbe vor dem Text in `404040`, wie das Ampel-Muster der Vorlagensammlung.

## Notizen

- Gelb-Orange `EAB500` auf Weiß hat wenig Kontrast; beim Sichtprüfen besonders darauf achten.

## Implementierungsnotizen

Umgesetzt am 2026-11-07 von `docs-2`.

**Was entstand**

- `generation/pptx/model.py`: `Run` um `mark`, `status`, `label` erweitert; `Table.highlighted`
  (je Zeile, auch in `subset`); `FlowSlide(title, line, kicker, dark, blocks, conclusion)` und
  die Blöcke `TextBlock`, `CodeLinesBlock`, `TableBlock`, `ImageRowBlock` (ein oder mehrere
  Bilder), `ColumnsBlock`, `CardsBlock`/`Card`, `RowsBlock`/`Row`, `PanelBlock`, `CalloutBlock`,
  `StatementBlock`, `TagsBlock`, `LabelledTagsBlock`/`LabelledTag`, `ConclusionBlock`,
  `CommentBlock`; `trim` liegt jetzt hier.
- `generation/pptx/parser.py`: Abschnitte werden als Token-Bereiche gesammelt und erst am Ende
  entschieden: Flow-Folie (Port von `UsesLayouts`: `.dark`/`kicker`, Container oder Alert
  irgendwo, Tag-Absatz auf oberster Ebene) oder wie bisher. `table(…, labels=True)` macht auf
  Flow-Folien Status-Labels, `highlighted` gilt überall; `runs` kennt `mark_open`/`mark_close`
  und farbige Wörter (`status`). Front-Matter-Labels kommen über den neuen Parameter `labels`.
- `generation/pptx/flow_parser.py` (neu, `FlowReader`): Port von `Container`, `Cards`, `Rows`,
  `Item`, `Flow`, `Tags`, `LabelledTags`, `Columns` mit den Meldungen von DocLibs, dazu
  `::: conclusion` und `::: comment`.
- `generation/pptx/flow.py` (neu, `FlowWriter`, `write_flow_slide`): Port von `Stack`/`Place`
  und `FitFlow`; jede Methode misst, mit Folie zeichnet sie auch. Fazit-Box, Kommentarbox,
  Kicker, dunkler Hintergrund, Sonderfall zwei gleiche Textspalten.
- `design/slides.py`: `FlowStyle`/`FLOW`, `ConclusionStyle`/`CONCLUSION`,
  `CommentStyle`/`COMMENT`, `COLUMN_GUIDES` (die vier 7,00-cm-Spalten der Master-Hilfslinien),
  `grid(n)`, `DARK_BACKGROUND_LAYOUT`.
- `writer.py`: `run_element` setzt `==…==` (fett, `a:highlight` `FDDC35`), farbige Wörter (fett
  in `STATUS_COLORS`) und den Label-Punkt auf allen Folien, nimmt eine Textfarbe;
  `paragraph_element` kann explizite Größen je Ebene (`fitting.level_pt`), Farbe und „kein
  Abstand vor dem ersten Absatz"; Titel und Fußzeile können weiß. `visuals.draw_table`: gelbe
  Zeilen, weiße Zeilenschrift auf dunklen Folien; `draw_pictures` misst auch ohne Folie.
- `layout_syntax`: `conclusion` und `comment` in `CONTAINER_NAMES` registriert (gelten damit
  auch für Word, das den Inhalt bis E03-S03 schlicht zeigt); `at_line` öffentlich.
- Tests: `tests/generation/pptx/test_flow.py` (38 Tests: Port von `SlideLayoutTests` ohne die
  MVV-/Brand-Fälle, Fazit-Box-Maße gegen Folie 43 der Vorlagensammlung, Kommentarbox-Form,
  zweispaltig → Vorlagenlayout, Raster, Farben nur aus `design.colors`, Signalfarben nur an
  Status-Runs, Reihenfolge der `a:rPr`-Kinder, Aufbaufehler mit Zeile, Fitting mit Teilung).
  `layouts.md` um „Vorher und nachher" (zwei Textspalten) und „Der Schattenlauf" (Spalten 1:2
  mit Code, Tabelle, Kommentarbox, Fazit-Box) ergänzt; Rundreise
  `tests/generation/pptx/samples/layouts.roundtrip.expected.md`; Ansicht `.tmp/review/layouts.pptx`.
  313 → 351 Tests.
- Doku: `docs/verwendung.md` (Abschnitt „Flow-Folien", Tabelle der Folien-Syntax),
  `docs/anleitung.md` (5. „Folien-Syntax"), `docs/ki-anleitung.md` (Präsentation,
  Folien-Syntax); `ai/Gedächtnis.md`.

**Entscheidungen und Abweichungen**

- Grundlage war `~/mvv/vt-tools-libs`. Übernommen ist, was der Plan nennt; **nicht** übernommen
  (kein Plan, kein PTA-Muster): Karten-Badges `1 · Titel`, `### Titel {.accent}`, Callout-Label
  `**Label:**`, Takeaway-Absatz mit Verlaufsbalken, Lead unter dem Titel, Builds, Szenen,
  Notizen. `### Titel {.accent}` bleibt daher Text.
- Folien beginnen nur noch an `#`/`##` auf **Token-Ebene 0**: eine Überschrift in einem
  Container oder Zitat startet keine Folie mehr (vorher hätte `##` in einem Zitat eine Folie
  mitten im Zitat begonnen).
- Aufbaufehler (Karten, Zeilen, Spalten, Fazit-/Kommentarbox) beginnen mit `Line N: ` wie
  `layout_syntax.check`; der Fehler „Flow-Inhalt auf anderem Layout" und die zu lange Fazit-Box
  hängen wie die übrigen PPTX-Meldungen `(line N)` an.
- Frage 1 (`.dark`): `Nur Titel` mit dem kopierten `p:bg` von `Titelfolie ohne Bild`
  (Theme-Farben der Vorlage); Titel, Text, Kicker, Fußzeile, Tabellenzeilen, Zeilentitel und
  Chips weiß. Helle Flächen (Panel, Alert, Code, Karten haben keine Fläche) behalten dunkle
  Schrift; `panel dark` bleibt `004676`.
- Frage 2 (Status-Labels): eigener Run „● " in der Signalfarbe (nicht fett), Text normal in
  `404040`; nicht zugeordnete Labels Mittelgrau (`STATUS_COLORS[NEUTRAL]` = `AFAFAF`). Nur auf
  Flow-Folien, wie in DocLibs; auf anderen Folien bleibt ein Code-Span in einer Zelle Code.
- Karten: 2 und 4 Spalten liegen genau auf den Hilfslinien des Masters (4 × 7,00 cm bei 1,33 /
  9,43 / 17,43 / 25,53 cm — die Lücken sind 1,10/1,00/1,10 cm), 3 Spalten 9,73 cm mit 1,00 cm.
  Karten in einem Panel oder einer Spalte teilen deren Breite gleichmäßig.
- `columns` mit ungleichen Gewichten: Kanten, die höchstens 1,5 cm neben einer Hilfslinie
  liegen, rasten ein (z. B. `1:3`); `1:2` liegt nicht in der Nähe einer Linie und bleibt
  rechnerisch (10,07 + 20,13 cm). Nur die äußeren Kanten liegen dann an Linien.
- Zwei gleiche Textspalten gehen nur dann auf `Titel und Text (zweispaltig)`, wenn die Folie
  nicht dunkel ist, keine Fazit-Box hat, nichts außer den Spalten enthält und beide Texte in
  die Platzhalter passen; sonst Flow-Folie. Ein Kicker ist dort erlaubt.
- Schriftgrößen der Textebenen: explizite `sz` je Run (Ebenengröße × Faktor, nie unter 12 pt)
  statt `normAutofit`, weil Textfelder auf Flow-Folien unterschiedliche Grundgrößen haben
  (18/14 pt). Der erste Absatz eines Textfelds bekommt `spcBef 0`, damit Messung und Darstellung
  übereinstimmen.
- Karten- und Zeilentitel sind Subheadline-Absätze (Ebene 1 des Masters: Segoe UI 18 pt
  PTA-Blau, nicht fett); Kennzahl und Statement dieselbe Ebene fett in 32 bzw. 24 pt.
- Fazit-Box: Maße `cm(1.33)` usw. statt der EMU-Werte der Vorlage (Abweichung < 0,02 cm, Test
  mit 0,1 mm Toleranz); Ränder exakt wie die Vorlage (684000/180000/72000); `noAutofit` statt
  `spAutoFit` (feste Höhe 1,94 cm reicht für zwei Zeilen 18 pt). Mehrere Absätze sind erlaubt,
  zusammen höchstens zwei Zeilen; 18 → 16 → 14 pt, sonst Fehler mit Zeilenzahl.
- Bei Teilung einer Folie mit Fazit-Box rechnen alle Teile mit der um die Box verkürzten Fläche
  (vorsichtig), die Box steht nur auf dem letzten Teil.
- Rows: Linien als gerade Verbinder (`p:cxnSp`), Begriffsspalte genau ein Drittel, Abstand zur
  Beschreibung 1,00 cm.
- Tags ohne Fläche (nur Rahmen), damit sie auf grauen Panels und weißem Grund gleich wirken.

**Warnungen**

- **Warnung (Kommentarbox):** „Spitze nach links unten auf den vorigen Block" ist so umgesetzt:
  die Sprechblase liegt **rechtsbündig oben auf dem vorigen Block** (überlagert ihn), ihre Spitze
  zeigt nach links unten in den Block (`adj1` −60 000, `adj2` ≥ 60 000), sie nimmt keine eigene
  Höhe ein. Neben einem Bild oder Diagramm (der gedachte Fall) liegt sie im freien Raum; neben
  einem Text oder einer Tabelle über die ganze Breite **verdeckt sie deren rechte obere Ecke**.
  Vorsichtig wäre auch: eigene Zeile unter dem Block, Spitze nach links oben. Eine
  Kommentarbox ohne Block davor ist ein Fehler.
- **Warnung:** Ohne PowerPoint/LibreOffice auf der Maschine ist nichts gerendert geprüft; Maße
  und Überläufe stammen aus der Textschätzung (`text_metrics`). Der Master zeichnet auf
  `{.dark}`-Folien seine Linien und Eckklammern weiter in seinen Farben über den Verlauf.
- **Warnung:** Word nimmt `::: conclusion` und `::: comment` jetzt an und zeigt den Inhalt als
  normalen Text (Gestaltung E03-S03); `{.agenda}`, `{.interim}`, `{.quote}`, `{.contact}` sind
  weiterhin nicht registriert (E04-S04).

**Prüfpunkte**

- `.tmp/review/layouts.pptx` in PowerPoint öffnen (ohne Reparatur?) und ansehen: Raster der
  Karten, Kicker über dem Titel, dunkle Folie „Verarbeitung ohne Broker", gelbe Zeilen und
  Ampelpunkte im „Statusmodell"/„Stand", Fazit-Box und Kommentarbox auf „Der Schattenlauf"
  gegen Folien 43 und 32 der Vorlagensammlung, Kontrast von `EAB500` (Notiz der Story).
- Ob die Kommentarbox oben auf dem Block (jetzt) oder darunter stehen soll.
- Ob Tags eine weiße Fläche bekommen sollen.

**Offene Punkte**

- Word-Gestaltung derselben Syntax: E03-S03; PDF: E05-S04.
- Bilder auf Flow-Folien stehen wie auf Visual-Folien mit 0,50 cm Abstand nebeneinander, nicht an
  den Hilfslinien.
