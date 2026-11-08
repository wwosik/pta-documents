# E10-S01 HTML-Deck-Generator

> Status: in Prüfung
> Epic: [E10 HTML-Präsentation und Vorschau](../50-entwurf/E10-html-praesentation-und-vorschau.md)
> Milestone: [M04 Präsentieren und Schulung](../50-entwurf/M04-praesentieren-und-schulung.md)

## Zusammenfassung

`HtmlDeckGenerator.generate(document, output, options)` schreibt eine selbständige HTML-Datei:
dieselben Folien wie der PPTX-Generator — Titelfolie, Trennfolie mit Kapitelnummer,
Inhaltsfolien, benannte Layouts, Abschlussfolie — im PTA-Look aus dem Designmodell, mit Tastatur-
und Touch-Bedienung, Notizenpanel, Fortschrittsbalken und Druck je Folie auf eine Seite.

## Kontext

- vt-tools-libs: `~/mvv/vt-tools-libs/src/VtToolsLibs.DocumentGeneration.Html/`:
  `HtmlDeckGenerator.cs` (220 Zeilen), `HtmlDeckWriter.cs` (1 057: Bühne 1600 × 900 px,
  Cover, Trennfolien, Layoutfolien, Fußzeile), `DeckSplitter.cs` (552: teilt Text- und
  Tabellenfolien an denselben Stellen wie PPTX), `SlideFitting.cs` (236: Rest schrumpft im
  Browser bis 55 %), `Images.cs` (102: Bilder als `data:`-URI), `ColouredSpans.cs`,
  `CodeBlockGraphics.cs` (Inline-SVG), `HtmlDeckOptions.cs` (76), `HtmlDeckStrings.cs` (32:
  Sprache, Tastenhinweis, „Notizen · Folie {0}", Ansage für Screenreader), `Runtime/deck.css`
  (278) und `deck.js` (276: Tasten ←/→/Leertaste/N/F, Hash-Navigation `#12`, Notizenpanel mit
  Timer, `prefers-reduced-motion`, Druck). Tests `HtmlDeckGeneratorTests.cs` (620 Zeilen).
- Hier: `generation/pptx/parser.py` (385) liefert `Slide`-Modelle (`TitleSlide`, `ChapterSlide`,
  `ContentSlide`, `VisualSlide`, `LayoutSlide`, `ClosingSlide`), `fitting.py` (239) die Teilung,
  `design/slides.py` die Maße (`CONTENT_AREA`, `LEVEL_SIZES_PT`, Fußzeilen-Platzhalter,
  `TITLE_SLIDES`), `design/colors.py` die Palette, `design/variants.py` `TEXTS` für `de`/`en`.
  Kein HTML-Writer, kein eingebettetes Selawik (E01-S03), kein Logo als SVG (E01-S04).
- Die PTA-Titelfolien liegen auf Fotos (`bild-01`, `bild-02`, `branchen`): die Bilder stecken
  in den Layouts der eingebetteten Vorlage und werden daraus gelesen (`design/templates.py`),
  nicht ein zweites Mal gebündelt.

## Vorgeschlagener Ansatz

1. **Paket** `src/pta_documents/generation/html/`: `generator.py` (`HtmlDeckGenerator`,
   `VALID_KEYS` = die des PPTX-Generators plus `fortschritt`, `kapitelanzeige`),
   `options.py` (`HtmlDeckOptions`: `variant`, `language`, `footer`, `title_slide`, `date`,
   `show_progress=True`, `show_chapters=True`, `build_lists`, `transition`,
   `continuation_suffix`), `writer.py`, `runtime/deck.css`, `runtime/deck.js`,
   `runtime/selawik-*.woff2` (aus E01-S03 konvertiert, OFL-Text daneben).
2. **Folien aus dem PPTX-Parser:** `DeckParser` und `fitting` unverändert nutzen; der HTML-
   Writer bekommt die fertig geteilten `Slide`s. Was `fitting` nicht teilt (Layoutfolien,
   Karten), schrumpft im Browser per `deck.js` bis 55 % wie in vt-tools-libs.
3. **Bühne und Look** (`writer.py` + `deck.css`): Bühne 1600 × 900 px (16:9 wie die Vorlage,
   33,87 × 19,05 cm → 1 cm ≙ 47,24 px), skaliert und mit Rändern ins Fenster gesetzt. Jede Maßzahl
   kommt aus `design/slides.py` und wird im Writer in px umgerechnet — keine zweite Wertetabelle
   im CSS, CSS-Variablen werden vom Writer gesetzt. Titelfolie: Foto des gewählten Layouts aus
   der Vorlage, weißes Logo (E01-S04), Titel, Untertitel, Zeile „Autor, Ort, Datum";
   Trennfolie: dunkel, Kapitelnummer „01"; Inhaltsfolie: Titel, Textebenen (Subheadline,
   Einleitungstext, Aufzählung ■/―), Eckklammern, Fußzeile „PTA – …" mit Foliennummer;
   Tabellen im PTA-Stil (Kopf `004676`), Code, Bilder mit `object-fit: cover` im Bildrahmen;
   Abschlussfolie mit Logo ohne Slogan. Benannte Layouts (`layout="…"`): die Platzhalter der
   PTA-Vorlage als absolut positionierte Boxen aus dem Layout-XML (Lage und Größe lesen,
   `---` verteilt wie in PPTX). Flow-Layouts (E04-S03) und PTA-Layouts (E04-S04) folgen dort.
4. **Bilder** als `data:`-URIs (PNG/JPEG/GIF direkt, SVG inline nach E06-S04); eine fehlende
   Ressource ist derselbe Fehler wie in PPTX.
5. **Laufzeit** (`deck.js`, Port von vt-tools-libs ohne skriptgesteuerte Szenen): Tasten,
   Touch-Wischen, Hash `#n`, Fortschrittsbalken, Kapitelanzeige, Notizenpanel (`N`) mit Timer,
   Vollbild (`F`), Übergänge in CSS (`fade`, `push`, `wipe`; `morph` bewegt Szenenformen nach
   E09-S04, sonst wie `fade`), Builds als Schritte, Screenreader-Ansage „Folie 3 von 12",
   `prefers-reduced-motion`. `@media print`: eine Seite je Folie, 16:9, ohne Panel.
6. **Texte** in `design/variants.py` `TEXTS` ergänzen (Tastenhinweis, „Notizen", „Folie {0} von
   {1}"), `lang` aus `sprache`.
7. **Sicherheit:** Rohes HTML aus dem Markdown wird als Text geschrieben (escaped); Links auf
   `http(s)` öffnen in neuem Tab; es gibt keine Option, Skript durchzulassen.
8. **Werkzeug:** `tools/generate/generate.py` bekommt `--html` (Suffix `.html`); `run.sh`/
   `run.ps1` bleiben unverändert, weil sie jedes `tools/<name>/<name>.py` als Verb ausführen.
9. **Tests** (`tests/generation/html/`): `deck.md` ergibt gleich viele Folien mit gleichen Titeln
   wie PPTX (Vergleich der Modelle); Snapshot `deck.expected.html` nach `tests/expected.py`;
   kein `<script>` außer dem eingebetteten; Rohes HTML ist escaped; jede Titelfolienvariante und
   `vorlage: schulung` rendern; Bilder sind `data:`-URIs; mit Playwright (Extra `[preview]`,
   sonst `skip`): Seite lädt ohne Konsolenfehler, Pfeiltaste wechselt die Folie, Druck-CSS ergibt
   so viele Seiten wie Folien.
10. **Doku:** `docs/verwendung.md` (Abschnitt *Markdown → HTML*), `docs/anleitung.md` (§2
    `--html`, Bedienung im Browser), `docs/ki-anleitung.md`; Guide über E04-S06 (ein Guide für
    beide Decks, wie in vt-tools-libs, mit Absatz zu den Unterschieden).

## Akzeptanzkriterien

- [x] Jedes Markdown, das `PptxGenerator` annimmt, ergibt ein HTML-Deck mit derselben Folienzahl,
      denselben Titeln und derselben Teilung; dieselben Fehler mit denselben Meldungen.
- [x] Die Datei ist selbständig (keine externen Ressourcen, `file://` genügt), unter 5 MB bei
      Textdecks, UTF-8 ohne BOM.
- [ ] Im Browser auf einem Rechner mit Segoe UI sind Titelfolie, Trennfolie, Inhaltsfolie und
      Abschlussfolie neben der PPTX-Folie nicht zu unterscheiden (Prüfpunkt des Menschen);
      ohne Segoe UI mit Selawik gleiche Zeilenumbrüche.
- [x] Rohes HTML und Skript aus dem Markdown werden nie ausgeführt.
- [x] Druck ergibt eine Seite je Folie.

## Offene Fragen

1. Reicht für `layout="…"` das Lesen der Platzhalterlagen aus dem Layout-XML, oder sollen nur
   die in E04-S04 benannten PTA-Layouts unterstützt werden und andere auf eine Inhaltsfolie
   zurückfallen? Vorschlag: Lagen lesen — die 35 Layouts sind sonst nicht zu pflegen.

> (2026-11-07) Lagen aus dem Layout-XML lesen.
2. Sollen Titelfotos der Vorlage (`bild-01`, `bild-02`, `branchen`) ins HTML eingebettet werden
   (je ~0,5–1 MB) oder durch den PTA-Verlauf (`ohne-bild`) ersetzt werden? Vorschlag: einbetten,
   sonst zeigt die Vorschau nicht, was PowerPoint zeigt.

> (2026-11-07) Einbetten.

## Notizen

- Größenordnung in vt-tools-libs ~2 600 Zeilen C# + 554 Zeilen CSS/JS; hier kleiner, weil Brands,
  Dark-Mode, Canvas und skriptgesteuerte Szenen entfallen.
- Flow-Layouts (E04-S03), PTA-Layouts (E04-S04), Diagramme (E06) und Szenen (E09-S04) ergänzen
  diesen Writer jeweils in ihrer Story — wie sie den PPTX-Writer ergänzen.

## Implementierungsnotizen

### Entscheidungen

- **Gezeichnet wird die geschriebene PPTX, nicht das Folienmodell.** `HtmlDeckGenerator` lässt
  `PptxGenerator` das Deck in einen Puffer schreiben und zeichnet dessen Folien
  (`generation/html/`: `ooxml.py` Theme/Farben, `geometry.py` Umrisse, `text.py` Text,
  `shapes.py` Formbäume, `charts.py` Diagramme, `timing.py` Builds/Übergänge, `writer.py` Seite,
  `runtime/deck.css`, `runtime/deck.js`). Grund: Die Teilung macht nicht der Parser, sondern der
  `DeckWriter` beim Zeichnen (`fitting` wird aus `writer.py`, `flow.py`, `kinds.py`, `visuals.py`
  gerufen; `FlowWriter` misst und zeichnet in einem). Ein zweiter Writer auf den Modellen hätte
  rund 2 500 Zeilen Flow-, Arten- und Fitting-Logik doppeln müssen; so sind Folienzahl, Titel,
  Teilung, Fehler und Hinweise **per Bauart** die der PPTX (AK 1), und Szenen (E09-S04) und
  künftige Folienarten erscheinen im HTML ohne eigenen Code, solange sie Standard-DrawingML sind.
  Layout, Master, Theme, Platzhaltervererbung und Textstile kommen aus der Vorlage im Deck —
  keine zweite Wertetabelle (Bereichsentscheidung „nachgezeichnet, nicht erfunden").
- Benannte Layouts (Frage 1): erledigt sich mit — jede Form steht dort, wo sie in der PPTX steht.
- Titelfotos (Frage 2): eingebettet, aus den Layouts der Vorlage im Deck. Die EMF-Logos der
  Layouts zeigt kein Browser; an ihre Stelle tritt das SVG-Logo aus E01-S04 (Abschlussfolie ohne
  Slogan, sonst mit).
- Native Diagramme werden aus ihrem Diagrammteil in eine `ChartSpec` zurückgelesen und mit
  `charts.drawing` gezeichnet (wie die Rückfälle in Word/PDF).
- Sicherheit: eine Content-Security-Policy (`default-src 'none'`, Skript nur mit dem SHA-256 der
  eingebetteten Laufzeit, Bilder und Schriften nur `data:`), aller Text escaped, Links nur
  `http(s):`/`mailto:` (http(s) in neuem Tab, `noopener noreferrer`).
- Front Matter: `fortschritt` und `kapitelanzeige` (`ja`/`nein`, Standard `ja`) nur im HTML-Deck;
  vor dem PPTX-Lauf werden sie zu Kommentarzeilen, damit Zeilennummern in Meldungen gleich
  bleiben. Fehler kommen als `DocumentConversionError` mit neuem Format `DocumentFormat.HTML` und
  dem `reason` der PPTX.
- Texte der Laufzeit (Tastenhinweis, „Notizen · Folie {0}", „Folie {0} von {1}") in
  `design.variants.GeneratedTexts` (`key_hint`, `notes_title`, `slide_announcement`).
- Werkzeug: `./run.sh generate … --html` schreibt `<name>.html`; `run.sh`/`run.ps1` unverändert.
- Playwright als Extra `preview` (Apache-2.0) in `pyproject.toml`.

### Abweichungen vom Plan

- Kein eigener Writer auf `Slide`-Modellen (siehe oben); `DeckParser` und `fitting` laufen
  unverändert, aber innerhalb von `PptxGenerator`. Das Schrumpfen im Browser bis 55 % aus
  vt-tools-libs entfällt: Die PPTX hat ihre Schriftgrößen und `normAutofit` schon, das HTML
  übernimmt sie.
- Schriften als TTF (`font/ttf`) statt WOFF2: so ohne Umwandlung und ohne neue Abhängigkeit
  (brotli) direkt aus `design.fonts`; die OFL-Texte liegen dort schon daneben. Größe der Schriften
  im HTML rund 0,5 MB.
- `HtmlDeckOptions.continuation_suffix` entfällt — das „(Forts.)" kommt aus der PPTX, ein anderer
  Text würde die gleichen Titel brechen.
- Rohes HTML wird nicht „als Text geschrieben", sondern wie in PowerPoint weggelassen (Hinweis
  `raw-html`) — sonst stünde im HTML anderer Text als auf der Folie.
- Die Laufzeit ist kein wörtlicher Port: ohne Szenen-API, Zählwerke und Morph-Bewegung; Übergänge
  als CSS-Animationen für alle Werte von `SlideTransition` (`morph` blendet über).
- Snapshot heißt `tests/generation/html/samples/deck.expected.html` und ist normalisiert (Daten-
  URIs als SHA-256-Kürzel, Schriften und Laufzeit herausgenommen), sonst wäre er 2 MB groß.

### Warnungen

- **Warnung:** Treue der Darstellung ist ohne PowerPoint nur gegen die eigene Erwartung geprüft
  (Screenshots mit Playwright/Chromium unter Linux, Selawik). Vereinfachungen: Abstand vor dem
  ersten Absatz eines Textkörpers wird weggelassen (wie PowerPoint, angenommen), einfacher
  Zeilenabstand 1,33 em (Segoe UI) bzw. 1,17 em (Consolas), `wedgeRectCallout` mit angenäherter
  Spitze, unbekannte Voreinstellungsformen als Rechteck, Gruppen ohne Drehung, `fillRef`/`lnRef`
  des Themes als Vollfarbe, Bildeffekte außer Graustufen und Deckkraft fehlen.
- **Warnung:** SVG-Bilder stehen als `<img>` im HTML (sicherer als inline); ihre Texte nutzen
  dann die Schriften des Browsers, nicht das eingebettete Selawik.
- **Warnung:** Die Titelfolie `branchen` zeigt in PPTX und HTML eine weiße Fläche mit weißem Titel
  und weißem Logo: Der Bildplatzhalter des Layouts für das Branchenfoto bleibt leer und wird vom
  PPTX-Generator entfernt. Das ist ein Verhalten des PPTX-Generators (E04), nicht des HTML-Decks;
  hier nicht geändert.
- **Warnung:** Decks mit Titel-, Trenn- und Abschlussfolie sind knapp 4 MB groß (die Fotos der
  Vorlage als Base64 rund 3,3 MB); mit eigenen Fotos auch darüber (`gsb`: 8 MB).
  Textdecks bleiben unter 5 MB. Die Fotos werden nicht neu kodiert.
- **Warnung:** Playwright steht nicht in `./run.sh setup` (Plan: Launcher unverändert); wer die
  Browsertests laufen lassen will, installiert `.[preview]` und `python -m playwright install
  chromium`. Ohne sie werden die drei Tests übersprungen.
- **Warnung:** `fortschritt`/`kapitelanzeige` kommen in `samples/funktionen/` nicht vor — dort
  würden sie die PPTX-Erzeugung brechen; `test_funktionen.py` prüft nur DOCX- und PPTX-Schlüssel.

### Prüfpunkte für den Menschen

- `./run.sh generate samples/funktionen/funktionen-praesentation.md --html` und die PPTX auf
  einem PTA-Rechner mit Segoe UI nebeneinander: Titel-, Trenn-, Inhalts-, Abschlussfolie, Flow-
  Folien, Tabellen, Diagramme (AK 3). Besonders Zeilenumbrüche, Abstand über dem ersten Absatz,
  Aufzählungszeichen und Icon-Aufzählungen.
- Bedienung in Chrome, Edge und Firefox: Tasten, Notizenpanel (`N`), Vollbild, Wischen, Druck
  als PDF (eine Seite je Folie).
- Lauf ohne Netzwerk über `file://`.

### Offene Punkte

- E10-S02 (Vorschau als Bilder) kann `HtmlDeckGenerator` und Playwright direkt nutzen.
- Morph im Browser bewegt keine Formen (E09-S04 ergänzt Szenen in der PPTX; die Bewegung im HTML
  wäre ein Nachtrag in `deck.js` über gleichnamige Formen).
