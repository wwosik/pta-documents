# E15-S03 Icons

> Status: in Bearbeitung (docs-2)
> Epic: [E15 Visuelle Bausteine](../../50-entwurf/E15-visuelle-bausteine.md)
> Milestone: [M03 Grafik, Diagramme und Charts](../../50-entwurf/M03-grafik-diagramme-und-charts.md)

## Zusammenfassung

`:icon-check:` setzt ein Icon aus einem gebündelten, frei lizenzierten Strich-Icon-Set in
PTA-Blau — als Figur vor dem Titel einer Karte, als Aufzählungssymbol einer Liste oder im Text.
Karten-Folien bekommen so das, was sie in PowerPoint sonst aus der Icon-Bibliothek von Hand
bekommen, und eine KI kann Icons nennen statt Bilder zu suchen.

## Kontext

- Karten (`::: cards`, E04-S03) kennen nach vt-tools-libs Plan 00028 eine „Figur vor dem Titel"
  (Zahl als Badge); ein Icon ist die zweite Figur. Listen auf Folien haben die PTA-Aufzählung
  (■, ―; E04-S02), in Word „Aufzählungszeichen" (E03-S02).
- Erzeugte Bilder: E11-S04 führt das Schema `qr:` mit `GeneratedImage.resolve(reference)` ein;
  Icons können denselben Weg nehmen (`![](icon:check)`) oder eine Inline-Syntax (Frage 1).
- SVG → PNG und SVG in Office: E06-S04 (`asvg:svgBlip`), ohne Extra `svg` nur PNG über eine
  eigene Rasterung — Strich-Icons mit 24 × 24-Raster lassen sich auch ohne resvg als Pfade ins
  Zeichenmodell (E02-S03) übernehmen und als Formen schreiben.
- Icon-Set: **Tabler Icons** (MIT, ~5 000 SVG-Strichzeichnungen, 24 × 24, Strich 2 px) —
  Lizenz erlaubt Bündelung mit Hinweis; alternativ Lucide (ISC). Material Symbols (Apache 2.0)
  wäre auch zulässig, ist aber flächig und passt weniger zum schlichten PTA-Stil.

## Vorgeschlagener Ansatz

1. **Teilmenge bündeln**: `src/pta_documents/design/icons/*.svg`, etwa 120 Icons für Beratung
   und IT (check, x, alert-triangle, info-circle, clock, calendar, users, user, building, server,
   cloud, database, lock, shield, key, settings, tool, code, bug, rocket, target, flag, chart-bar,
   chart-line, trending-up, currency-euro, file-text, folder, mail, phone, map-pin, search,
   lightbulb, puzzle, arrow-right, refresh, plus, minus, star, thumb-up, …) mit `LICENSE` des
   Sets; eine Liste `ICONS` in `design/icons/__init__.py`; der Authoring Guide nennt alle Namen
   (Test: jeder gebündelte Name steht im Guide).
2. **Lesen**: Tabler-SVGs sind `path`, `circle`, `line`, `polyline`, `rect` mit `stroke`;
   `design/icons/loader.py` wandelt sie in ein `Drawing` (E02-S03: Pfade mit `stroke`, ohne
   Füllung, runde Enden) — die Mini-Teilmenge des SVG-Lesers aus E06-S03, ohne Text und
   Transformationen (die Tabler nicht braucht). Farbe beim Lesen gesetzt: PTA-Blau, auf dunklen
   Flächen (`.dark`, `panel dark`, Fazit-Box) Weiß, in Text die Textfarbe.
3. **Syntax** (Frage 1): Inline `:icon-check:` in `markdown/parser.py` als eigene Inline-Regel
   (`^:icon-([a-z0-9-]+):`), Token `icon` mit `meta["name"]`; unbekannter Name → Fehler mit
   Zeile und den drei ähnlichsten Namen (`difflib.get_close_matches`). In Code-Spans unberührt.
4. **Wirkung**:
   - **Karte** (`::: cards`): steht das Icon am Anfang des `###`-Titels, wird es die Figur
     (1,2 cm, über oder vor dem Titel wie das Badge von E04-S03); ein Icon und eine Zahl
     zusammen sind ein Fehler.
   - **Liste**: beginnt jeder Punkt einer Liste mit einem Icon, wird es das Aufzählungssymbol
     (PowerPoint: `a:buBlip` mit PNG 0,5 cm; Word: Bild im Absatz mit hängendem Einzug statt
     Aufzählungszeichen); sonst steht es inline.
   - **Inline**: Höhe der Schrift (x-Höhe + Oberlänge), auf der Grundlinie, Abstand 0,1 em;
     PowerPoint als Bild im Textlauf gibt es nicht — Inline-Icons auf Folien werden Formen an der
     berechneten Position (TextMetrics, E04-S02) oder, in Platzhaltertext, ein Fehler mit Hinweis
     auf Karten/Listen (Frage 2).
   - **Word**: PNG (2× Auflösung) plus SVG über E06-S04, wenn das Extra da ist, sonst PNG aus
     eigener Rasterung mit Pillow (Pfade zeichnen — Pillow kann Linien/Bögen, keine Béziers:
     Béziers werden in 16 Segmente aufgeteilt).
5. **Konverter (E07)**: ein Icon kommt als Bild zurück (`![](images/icon-check.png)`); der
   Konverter erkennt die Bildbeschreibung `icon:check` (im `descr` des Bildes abgelegt) und
   schreibt wieder `:icon-check:`. Rundreise bleibt damit verlustfrei.
6. **Tests**: Loader für jedes gebündelte Icon (Pfade, Maße 24 × 24), Lizenzdatei vorhanden,
   Fehler mit Vorschlägen, Karte mit Icon-Figur, Liste mit Icon-Aufzählung, Word-Bild mit
   `descr`, Rundreise; Beispiel in `samples/funktionen/`.

## Akzeptanzkriterien

- [ ] `:icon-check:` am Anfang eines Kartentitels ergibt eine Figur in PTA-Blau; in einer Liste
      ein Aufzählungssymbol; unbekannte Namen sind Fehler mit Vorschlägen.
- [ ] Alle gebündelten Icons stehen im Guide; die Lizenz liegt im Paket.
- [ ] Ohne Extra `svg` entstehen PNGs; mit Extra zusätzlich SVG in Word.
- [ ] Die Rundreise liefert `:icon-name:` zurück.

## Offene Fragen

1. Syntax `:icon-check:` (Vorschlag — kurz, im Text verwendbar, aus Markdown-Emoji-Konventionen
   bekannt) oder `![](icon:check)` wie `qr:` (ein Mechanismus für alle erzeugten Bilder, aber
   sperrig im Kartentitel)?

> (2026-11-07) `:icon-check:`.

2. Inline-Icons in Folientexten: als frei positionierte Formen (fragil beim Fitting) oder
   Fehler mit Hinweis auf Karten und Listen? Vorschlag: Fehler — Folientext ist Platzhaltertext.

> (2026-11-07) Fehler mit Hinweis auf Karten und Listen.

3. Tabler (MIT) oder Lucide (ISC)? Beide passen; Tabler hat mehr Icons, Lucide ist die Fortsetzung
   von Feather mit sehr einheitlichem Strich. Vorschlag: Tabler.

> (2026-11-07) Tabler Icons (MIT).

## Notizen

- Paketgröße: 120 Tabler-SVGs ≈ 60 KB; nichts spricht gegen eine größere Teilmenge, aber der
  Guide soll lesbar bleiben.
