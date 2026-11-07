# E10-S01 HTML-Deck-Generator

> Status: Entwurf
> Epic: [E10 HTML-Präsentation und Vorschau](E10-html-praesentation-und-vorschau.md)

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

- [ ] Jedes Markdown, das `PptxGenerator` annimmt, ergibt ein HTML-Deck mit derselben Folienzahl,
      denselben Titeln und derselben Teilung; dieselben Fehler mit denselben Meldungen.
- [ ] Die Datei ist selbständig (keine externen Ressourcen, `file://` genügt), unter 5 MB bei
      Textdecks, UTF-8 ohne BOM.
- [ ] Im Browser auf einem Rechner mit Segoe UI sind Titelfolie, Trennfolie, Inhaltsfolie und
      Abschlussfolie neben der PPTX-Folie nicht zu unterscheiden (Prüfpunkt des Menschen);
      ohne Segoe UI mit Selawik gleiche Zeilenumbrüche.
- [ ] Rohes HTML und Skript aus dem Markdown werden nie ausgeführt.
- [ ] Druck ergibt eine Seite je Folie.

## Offene Fragen

1. Reicht für `layout="…"` das Lesen der Platzhalterlagen aus dem Layout-XML, oder sollen nur
   die in E04-S04 benannten PTA-Layouts unterstützt werden und andere auf eine Inhaltsfolie
   zurückfallen? Vorschlag: Lagen lesen — die 35 Layouts sind sonst nicht zu pflegen.

>

2. Sollen Titelfotos der Vorlage (`bild-01`, `bild-02`, `branchen`) ins HTML eingebettet werden
   (je ~0,5–1 MB) oder durch den PTA-Verlauf (`ohne-bild`) ersetzt werden? Vorschlag: einbetten,
   sonst zeigt die Vorschau nicht, was PowerPoint zeigt.

>

## Notizen

- Größenordnung in vt-tools-libs ~2 600 Zeilen C# + 554 Zeilen CSS/JS; hier kleiner, weil Brands,
  Dark-Mode, Canvas und skriptgesteuerte Szenen entfallen.
- Flow-Layouts (E04-S03), PTA-Layouts (E04-S04), Diagramme (E06) und Szenen (E09-S04) ergänzen
  diesen Writer jeweils in ihrer Story — wie sie den PPTX-Writer ergänzen.
