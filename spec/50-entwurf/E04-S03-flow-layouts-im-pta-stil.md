# E04-S03 Flow-Layouts im PTA-Stil

> Status: Entwurf
> Epic: [E04 PPTX-Generator auf der PTA-PowerPoint-Vorlage](E04-pptx-generator.md)
> Milestone: [M02 Rückmeldung und Folien-Syntax](M02-rueckmeldung-und-folien-syntax.md)

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

- [ ] `layouts.md` ergibt Flow-Folien auf `Nur Titel`, deren Formen innerhalb der Inhaltsfläche an
      den Rasterlinien liegen.
- [ ] Fazit-Box und Kommentarbox gleichen den Mustern der Vorlagensammlung (Folien 32, 43).
- [ ] Alle Farben stammen aus `design.colors`; Signalfarben erscheinen nur bei Status.
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
