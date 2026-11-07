# E09-S02 Builds: Inhalte erscheinen Klick für Klick

> Status: Entwurf
> Epic: [E09 Präsentieren](E09-praesentieren.md)

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

- [ ] `{.build}` vor einer Liste lässt die Punkte in PowerPoint einzeln per Klick erscheinen, mit
      Fade; die Liste bleibt ein bearbeitbarer Platzhaltertext mit den Aufzählungszeichen der
      Vorlage.
- [ ] `{.build}` vor einer Tabelle und `{.frag}` vor einem Block zeigen den Block als Ganzes auf
      einen Klick; `aufbau: listen` baut alle äußeren Listen.
- [ ] Ein unbekannter Marker oder ein Marker ohne folgenden Block wirft mit Zeilennummer.
- [ ] Word und PDF erzeugen aus demselben Markdown ohne Fehler dasselbe wie ohne Marker.
- [ ] PowerPoint öffnet Decks mit Builds ohne Reparaturmeldung (Prüfpunkt des Menschen).

## Offene Fragen

1. Name des Front-Matter-Schlüssels: `aufbau: listen` (Vorschlag), `animation: listen` oder
   `klickweise: ja`?

>

2. Soll der PPTX-Konverter Builds als `{.build}` zurückgeben, damit ein Deck → Markdown → Deck
   seine Animationen behält? Vorschlag: nein, Animationen sind kein Inhalt; die Rundreise prüft
   Inhalt.

>

## Notizen

- Abhängig von E04-S03 nur für Karten, Reihen und Spalten; Listen, Tabellen, Bilder und Code
  lassen sich vorher umsetzen.
