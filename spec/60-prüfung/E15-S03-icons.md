# E15-S03 Icons

> Status: in Prüfung
> Epic: [E15 Visuelle Bausteine](../50-entwurf/E15-visuelle-bausteine.md)
> Milestone: [M03 Grafik, Diagramme und Charts](../50-entwurf/M03-grafik-diagramme-und-charts.md)

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

- [x] `:icon-check:` am Anfang eines Kartentitels ergibt eine Figur in PTA-Blau; in einer Liste
      ein Aufzählungssymbol; unbekannte Namen sind Fehler mit Vorschlägen.
- [x] Alle gebündelten Icons stehen im Guide; die Lizenz liegt im Paket.
- [x] Ohne Extra `svg` entstehen PNGs; mit Extra zusätzlich SVG in Word.
- [x] Die Rundreise liefert `:icon-name:` zurück.

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

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08 (begonnen in einer unterbrochenen Sitzung, deren Teilstand
geprüft, ergänzt und fertiggestellt wurde). Neu: `design/icons/` (162 Tabler-SVGs, unverändert
aus `icons/outline/` von `@tabler/icons` 3.50.0, `LICENSE-tabler-icons.txt`, `__init__.py` mit
`ICONS`, `svg`, `colored_svg`, `alt`/`from_alt`, `suggestions`, `unknown`; `loader.py`
mit `drawing`/`outlines`; `raster.py` mit `png`/`name_of`/`polylines`), `markdown/icon.py`
(Inline-Regel, Token `icon`), `generation/common/icons.py` (`check`, `leading`,
`without_leading`, `list_icons`, `color_on`). Angepasst: `markdown/parser.py`,
`markdown/typography.py`, `generation/common/layout_syntax.py` (Namensprüfung),
`generation/common/result.py` (Doku `code-not-drawn`), PPTX `model.py` (`Card.icon`,
`Paragraph.icon`), `parser.py`, `flow_parser.py`, `flow.py` (`FlowWriter.icon`), `writer.py`
(`icon_bullet`), `design/slides.py`, Word `writer.py` (`icon_picture`, `icon_bullet`),
`design/word.py`, PDF `layout/inline.py`, Konverter `conversions/docx.py` und
`conversions/pptx.py`. Tests: `tests/design/icons/` (`test_icons.py`, `test_loader.py`,
`test_raster.py`), `tests/markdown/test_icon.py`, `tests/generation/common/test_icons.py`,
`tests/generation/pptx/test_icons.py`, `tests/generation/docx/test_icons.py`,
`tests/generation/pdf/layout/test_inline.py`; `tests/samples/test_funktionen.py` verlangt Icons
als Aufzählung, als Kartenfigur (Deck) und im Text (Bericht). Beispiele: Abschnitt „Icons" in
`funktionen-bericht.md`, Folien „Icons in Karten" und „Icons als Aufzählung" in
`funktionen-praesentation.md`, README, Rundreisen. Doku: `docs/verwendung.md` (Abschnitt
„Icons (E15-S03)", Zeile der Syntaxtabelle), `docs/anleitung.md` (Abschnitt „Icons", Tabelle),
`docs/ki-anleitung.md` (Abschnitt mit allen Namen); `ai/Gedächtnis.md`.

### Entscheidungen

- **Icon-Set:** 162 Tabler-Icons (Plan: etwa 120) für Beratung und IT, alle aus `<path>`-Elementen
  auf 24 × 24, Strich 2 px. Der Lader liest nur diese Teilmenge und weist alles andere ab, damit
  ein neues Icon mit anderen Elementen in den Tests auffällt.
- **Prüfung an einer Stelle:** `layout_syntax.check` prüft die Namen für alle Formate; die
  Meldung nennt die bis zu drei ähnlichsten (`difflib`, Schwelle 0,5), sonst den Verweis auf die
  Anleitung.
- **Karte (PowerPoint):** Icon 1,2 cm (mit dem Verkleinern der Folie skaliert) als Formgruppe
  `icon:<name>` **über** dem Titel, linksbündig wie die Kennzahl; auch in der Listenform der
  Karten (`- :icon-x: **Titel** – Text`). Icon und Kennzahl zusammen sind ein Fehler.
- **Liste:** nur ungeordnete Listen, und nur wenn **jeder** Punkt der Ebene mit einem Icon
  beginnt; verschachtelte Listen bleiben unberührt. PowerPoint: `a:buBlip` mit PNG 96 px,
  `a:buSzPct` 110 % (Plan „0,5 cm" — relativ zur Schrift, damit es beim Verkleinern mitgeht).
  Word: Absatz in der Aufzählungsvorlage mit `numId 0`, Einzug der Ebene, hängend 0,6 cm, Icon
  11 pt und ein Tabulator.
- **Im Text (Word):** Bild 10 pt hoch auf der Grundlinie (etwa Versal- plus Oberlänge der
  Grundschrift); ein eigener Abstand von 0,1 em entfällt — der Abstand ist das Leerzeichen im
  Markdown.
- **Auf Folien sonst ein Fehler** (Antwort 2) — auch in Folientiteln, Tabellen und
  Sprechernotizen, weil alle durch dieselbe Lauf-Erzeugung gehen.
- **Farbe:** PTA-Blau; auf dunklen Flächen (`.dark`, `panel dark`) weiß — erkannt an der
  Textfarbe Weiß bzw. `Look.dark`.
- **Word-Bilder:** das PNG zeichnet immer die eigene Rasterung (Pillow, ohne Extra, byte-gleich);
  ist das Extra `svg` installiert (`svg_available()`), kommt die eingefärbte Original-SVG als
  `asvg:svgBlip` dazu. Das PNG nimmt nicht den Weg über `resvg`, damit beide Fälle dasselbe Bild
  zeigen.
- **Rundreise:** Word über die Bildbeschreibung `icon:<name>` (der Tabulator nach einem
  Icon-Aufzählungszeichen wird ein Leerzeichen), PowerPoint über den Gruppennamen der
  Kartenfigur und ein PNG-Textfeld `pta-documents-icon` im Bild des Aufzählungszeichens
  (`a:buBlip` hat keine Beschreibung).

### Abweichungen

- Die Alternativtext-Hilfen (`alt`, `from_alt`) liegen in `design/icons/`, nicht in
  `generation/common/`, weil die Konverter nichts aus `generation` importieren.
- Statt eines eigenen „Authoring Guide" (E04-S06, noch Entwurf) nennt `docs/ki-anleitung.md` alle
  Namen; der Test prüft diese Datei.
- Inline-Icons auf Folien als frei positionierte Formen gibt es nicht (Antwort 2), daher auch
  keine Positionsrechnung über TextMetrics.

### Warnungen

- **PDF:** Icons entfallen bis E05-S04 mit Hinweis `code-not-drawn` (reportlabs `<img>` in
  Absätzen nimmt nur Dateinamen oder — nur mit globaler `trustedHosts`-Einstellung —
  `data:`-URIs; beides verträgt sich nicht mit „Stream rein, Stream raus" und „kein globaler
  Zustand"). Icon-Aufzählungen zeigen im PDF das normale Aufzählungszeichen.
- **Word-Fußnoten:** ein Icon darin entfällt mit `code-not-drawn` (der Fußnotenteil hat keine
  Bildbeziehungen über python-docx) — vorsichtigste Wahl statt eines Fehlers.
- **Ohne Office geprüft:** dass PowerPoint `a:buBlip` mit `a:buSzPct` und Word die
  `numId 0`-Absätze mit hängendem Einzug wie gedacht zeigen, ist nicht in Office geprüft (keine
  Office-/LibreOffice-Installation). Die Icons selbst sind als Kontaktbogen gerastert geprüft.
- Icons in Word-Überschriften sind 10 pt hoch wie im Fließtext, nicht so hoch wie die
  Überschrift.
- Die Herkunft der SVGs (Version 3.50.0) stammt aus der unterbrochenen Sitzung; Lizenztext und
  Dateiaufbau entsprechen Tabler, die Version wurde nicht erneut gegen das npm-Paket geprüft.

### Prüfpunkte

- `.tmp/review/funktionen/funktionen-praesentation.pptx`, Folien „Icons in Karten" (Figur über
  dem Titel, PTA-Blau, einzeln verschiebbar) und „Icons als Aufzählung" (Bild-Aufzählungszeichen
  in Textgröße).
- `.tmp/review/funktionen/funktionen-bericht.docx`, Abschnitt „Icons": Aufzählung mit Icons
  statt ■, Icons im Text auf der Grundlinie.
- `./run.sh test tests/design/icons tests/markdown/test_icon.py
  tests/generation/common/test_icons.py tests/generation/pptx/test_icons.py
  tests/generation/docx/test_icons.py tests/generation/pdf/layout/test_inline.py`.

### Offene Punkte

- **PDF (E05-S04):** Icons im Text als kleine Vektorgrafik (z. B. eigenes Flowable bzw.
  `loader.drawing` auf dem Canvas) und als Aufzählungszeichen; danach den Hinweis in
  `layout/inline.py` entfernen. — *(2026-11-08) Erledigt in E05-S04 (als PNG wie in Word,
  nicht als Vektor: reportlabs Absätze setzen Bilder, keine Zeichnungen).*
- Icons in Word-Fußnoten.
- Wird der Authoring Guide (E04-S06) gebaut, übernimmt er die Namensliste (und den Test).
