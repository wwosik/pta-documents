# E01-S03 Schriften für PDF und SVG

> Status: in Prüfung
> Epic: [E01 PTA-Design als einziges Design](../50-entwurf/E01-pta-design.md)
> Milestone: [M03 Grafik, Diagramme und Charts](../50-entwurf/M03-grafik-diagramme-und-charts.md)

## Zusammenfassung

Ein Schriftmodul `pta_documents.design.fonts`, das PDF-Generator (E05) und SVG→PNG (E06-S04)
die Schriftdateien liefert: Segoe UI aus dem System, wenn sie vollständig vorhanden ist, sonst
das gebündelte Selawik (OFL); dazu Ersatzschriften für Code und Zitate, Breiten und Glyphenprüfung.

## Kontext

- Segoe UI ist die PTA-Hausschrift, proprietär und darf nicht mitgeliefert werden
  ([Designanalyse](../10-analysen/2026-11-06%20pta-designstandards.md#schriften)); Entscheidung
  2026-11-06: Selawik bündeln, Segoe UI aus dem System nehmen, wenn vorhanden.
- DocLibs: `DocumentGeneration.Pdf/Fonts.cs` (147 Zeilen: `FontFace`, `IFontMetrics`, `FontSet`
  mit Liberation als Standard, Breiten je Zeichen) und `DocumentGeneration/TrueTypeInfo.cs`
  (175 Zeilen: Umrisse `glyf`/CFF, Familienname, `OS/2 fsType`, `cmap`). Liberation entfällt.
- Selawik (Microsoft, OFL 1.1) ist metrisch an Segoe UI angelehnt, hat aber **keine kursiven
  Schnitte** (nur Regular, Light, Semilight, Semibold, Bold).
- DOCX und PPTX brauchen dieses Modul nicht: Word und PowerPoint nehmen die installierte Schrift,
  eingebettet wird nichts (E04, bereichsweite Entscheidung).

## Vorgeschlagener Ansatz

1. **Dateien** in `src/pta_documents/design/fonts/` (Unterpaket mit `__init__.py`, Paketdaten über
   `importlib.resources`): `Selawik-Regular.ttf`, `Selawik-Bold.ttf`, `Selawik-Light.ttf`, der
   Code-Ersatz (Vorschlag Inconsolata Regular/Bold, OFL — liegt in den DocLibs-Testdaten
   `brand-sample/fonts/mono/`), der Zitat-Ersatz Gelasio Italic (OFL, metrisch kompatibel zu
   Georgia) und die Lizenztexte `OFL-*.txt`. Herkunft, Version und SHA-256 stehen im Docstring
   des Moduls; die Dateien legt der Mensch einmal ab, kein Download zur Laufzeit.
2. **`FontFace`** (`StrEnum`): `REGULAR`, `BOLD`, `ITALIC`, `BOLD_ITALIC`, `LIGHT`, `MONO`,
   `MONO_BOLD`, `QUOTE`. **`FontFile(family, content: bytes, synthetic_italic: bool)`**,
   **`FontSet(name, files)`** mit `width(text, face, size_pt)` und `has_glyph(code_point, face)` —
   Port von `FontSet.Width`/`HasGlyph`, nur BMP wie in DocLibs.
3. **Lesen mit fontTools** (neu in den Extras `pdf` und `svg`, nicht im Kern): Port der nötigen
   Teile von `TrueTypeInfo` — nur TrueType-Umrisse (`glyf`), Familienname (Name-ID 1, sonst 16),
   `fsType`, `cmap` und `hmtx`. Fehlt fontTools, sagt der `ImportError`, welches Extra fehlt.
4. **`bundled() -> FontSet`**: Selawik für Regular/Bold/Light; Italic und Bold Italic sind
   Regular bzw. Bold mit `synthetic_italic=True` (die PDF-Engine schrägt per Textmatrix, siehe
   Frage 1); Mono und Quote aus den Ersatzschriften.
5. **`resolve(system_fonts: bool = True, search_dirs: Sequence[Path] | None = None) -> FontSet`**:
   sucht `segoeui.ttf`, `segoeuib.ttf`, `segoeuii.ttf`, `segoeuiz.ttf`, `segoeuil.ttf`,
   `consola.ttf`, `consolab.ttf`, `georgiai.ttf` ohne Rücksicht auf Groß/Klein in
   `%WINDIR%\Fonts`, `%LOCALAPPDATA%\Microsoft\Windows\Fonts`, `/usr/share/fonts`,
   `/usr/local/share/fonts`, `~/.local/share/fonts`, `~/.fonts`, `/Library/Fonts`,
   `~/Library/Fonts` (rekursiv). Eine Familie wird nur **ganz** übernommen (Segoe UI nur mit
   allen vier Textschnitten), sonst bleibt der gebündelte Ersatz — keine Mischung im Dokument.
   Schriften mit `fsType`-Bit „eingeschränkt" (2) oder CFF-Umrissen werden übergangen. Kein
   Cache; das ist der einzige Dateizugriff der Bibliothek außerhalb von Werkzeugen und gilt nur,
   wenn `system_fonts` an ist.
6. **CSS-Familien** für SVG (E02-S03): `CSS_FAMILY = "Segoe UI, Selawik, sans-serif"`,
   `CSS_MONO_FAMILY = "Consolas, Inconsolata, monospace"`.
7. **Tests:** jede gebündelte Datei lädt, hat `glyf`-Umrisse und erlaubt Einbettung; SHA-256 fest;
   `resolve(system_fonts=False)` ergibt `bundled()`; mit einem Testordner aus umbenannten
   Selawik-Kopien (`segoeui*.ttf`) wird „Segoe UI" gewählt, mit nur drei Schnitten nicht;
   `width()` liegt für einen Mustersatz nahe an `generation/common/text_metrics.py`; das Wheel
   enthält Schriften und Lizenzen (`tests/test_package.py`).

## Akzeptanzkriterien

- [ ] `design.fonts.bundled()` liefert alle acht Schnitte aus Paketdaten, ohne Netz und ohne
      Systemschriften.
- [ ] Ist Segoe UI vollständig installiert, nimmt `resolve()` sie; sonst überall Selawik.
- [ ] Keine Segoe-UI-, Consolas- oder Georgia-Datei liegt im Repo oder im Paket; die OFL-Texte
      liegen neben den gebündelten Schriften.
- [ ] Der Kern (DOCX, PPTX, Konverter) importiert weder fontTools noch dieses Modul.

## Offene Fragen

1. Selawik hat keine Kursive. Soll Kursivtext im PDF (ohne Segoe UI) **schräggestellt** werden
   (Vorschlag, 12° per Textmatrix), oder aufrecht bleiben? (Dieselbe Frage steht in E05-S01;
   die Antwort hier gilt für beide.)

> (2026-11-07) Schrägstellen (12° per Textmatrix); gilt auch für E05-S01.

2. Ersatz für Consolas im Code: **Inconsolata** (Vorschlag, ähnlicher Duktus, liegt schon in den
   DocLibs-Testdaten), **Cascadia Mono** (OFL, Microsoft; so vorgeschlagen in E05-S01) oder
   Liberation Mono (wie DocLibs, Courier-Breiten)? Die Antwort gilt auch für E05-S01.

> (2026-11-07) Inconsolata (OFL); gilt auch für E05-S01.

3. In PowerPoint stehen Zitate in Georgia kursiv; die Word-Formatvorlage `Zitat` (E03-S02) ist
   ein eingerückter Standard-Absatz. Sollen `Zitat` in Word und damit Zitate im PDF ebenfalls
   Georgia kursiv werden (dann wird Gelasio Italic im PDF gebraucht), oder bleibt Gelasio nur für
   SVG/PNG von Folieninhalten?

> (2026-11-07) Nein — Word und PDF bleiben bei der Word-Vorlage; Gelasio nur für SVG/PNG von Folieninhalten.

## Notizen

- E05-S01 baut sein `pdf/fonts.py` auf diesen Dateien auf; Breiten dürfen dort über reportlab
  kommen, Auswahl und Dateien aber nur aus `design.fonts`.
- Mit echten Breiten aus Selawik könnte später auch das Fitting der Folien
  (`text_metrics.py`, bisher geschätzt) genauer werden — nicht Teil dieser Story.

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08: Unterpaket `src/pta_documents/design/fonts/`
(`__init__.py` mit `FontFace`, `FontFile`, `FontSet`, `bundled()`, `resolve()`,
`default_font_dirs()`, `CSS_*FAMILY`; `truetype.py` als Port der nötigen Teile von
`TrueTypeInfo`), die sechs Schriftdateien und drei OFL-Texte als Paketdaten, fontTools (MIT) in
den Extras `pdf` und `svg`. Tests in `tests/design/test_fonts.py` und `tests/test_package.py`
(Wheel), Doku in `docs/verwendung.md` (Abschnitt „Schriften für PDF und SVG"), Eintrag in
`ai/Gedächtnis.md`. `samples/` und die Anleitungen für Schreiber bleiben unverändert — es gibt
keine neue Syntax und keinen neuen Front-Matter-Schlüssel.

### Entscheidungen

- **fontTools wird lazy geladen** (nur in `truetype.read_info`). Damit liefert `bundled()` die
  Bytes auch ohne Extra; erst Messen, Glyphenprüfung und `resolve()` brauchen fontTools, und der
  `ImportError` nennt dann die Extras `pdf` und `svg`. Die Familiennamen der gebündelten Dateien
  stehen deshalb in einer Tabelle im Modul; ein Test prüft sie gegen die Name-Tabelle.
- `FontFile.info` (Metriken, `fsType`, Umrisse) ist eine `cached_property` je Dateiobjekt. Sie
  ändert kein Ergebnis und gilt nur für das Objekt; `resolve()` selbst hat keinen Cache.
- `width()` liefert **Punkt** (Summe der Vorschubbreiten aus `hmtx`, ohne Kerning); Zeichen ohne
  Glyphe zählen mit der Breite von `.notdef`. `has_glyph()` kennt nur die BMP, wie DocLibs.
- Familienname: Name-ID 1, sonst 16 (wie geplant). Für Selawik Light ist das „Selawik Light",
  für Segoe UI Light entsprechend „Segoe UI Light"; `FontSet.name` ist die Familie der
  Textschnitte („Selawik" bzw. „Segoe UI").
- Systemschriften werden am **Dateinamen** erkannt, nicht am Familiennamen — so verlangt es der
  Test mit umbenannten Selawik-Kopien. Gesucht wird in der Reihenfolge der Ordner, darin
  sortiert; die erste Datei je Name gewinnt.
- Unlesbare Systemdateien (fontTools wirft) gelten wie fehlende; die ganze Familie fällt dann
  auf den gebündelten Ersatz zurück.
- „Eingeschränkt" heißt: Bit `0x0002` in `OS/2 fsType` ist gesetzt.
- Zusätzlich `CSS_QUOTE_FAMILY = "Georgia, Gelasio, serif"` für Zitate in SVG (Frage 3: Gelasio
  nur für SVG/PNG von Folieninhalten) und `SYNTHETIC_ITALIC_ANGLE = 12.0` (Frage 1) als
  Konstante für E05.
- Test „Kern importiert nichts davon": ein Unterprozess importiert Paket, Konverter und beide
  Generatoren und prüft `sys.modules`; zusätzlich darf nur `fonts/truetype.py` fontTools nennen.
- Der Wheel-Test baut mit der hatchling-API (`WheelBuilder`) in ein `tmp_path`.

### Abweichungen

- **Warnung:** GitHub (Releases und API) antwortete in dieser Umgebung durchgehend mit 503; die
  Release-Zip von Selawik war nicht zu bekommen. Herkunft der Dateien daher:
  - `Selawik-Regular.ttf`, `Selawik-Bold.ttf`: Release-Binärdateien 1.01 (Version 1.01, mit
    `DSIG`, `fsType` 0), wie sie das npm-Paket `@docx-editor.dev/fonts` 2.35.0 (Apache-2.0/OFL)
    unverändert weitergibt — nicht gegen die Release-Zip geprüft.
  - `Selawik-Light.ttf`: **selbst gebaut** mit fontmake 3.12.2 aus
    `Source files/UFO/Selawik-Light.ufo` des Tags `1.01` (über jsDelivr). Ohne Hinting, `fsType`
    8 (bearbeitbar einbettbar), Version „1.001". Zur Probe aus derselben Quelle gebautes Regular
    hat dieselben 348 Zeichen und dieselben Breiten wie das Release, außer bei 16 Glyphen
    (kombinierende Akzente mit Breite 0 im Release, `ď`). Bauen aus der unveränderten
    Originalquelle ist keine „Modified Version" im Sinne der OFL, der Name Selawik bleibt
    zulässig — aber es ist nicht die Datei des Releases.
  - Inconsolata 3.000 (`fonts/ttf`, Tag `3.000`, googlefonts/Inconsolata) und Gelasio 1.008
    (`fonts/ttf`, Branch `master`, SorkinType/Gelasio) über jsDelivr — nicht aus den
    DocLibs-Testdaten, die hier nicht vorliegen.
  Der Plan sah vor, dass der Mensch die Dateien ablegt; das habe ich übernommen, um die Story
  nicht zu blockieren. Austausch: Datei ersetzen, SHA-256 im Test und im Modul-Docstring
  nachziehen.
- **Warnung:** Segoe UI wird nur mit **fünf** Dateien übernommen (`segoeui`, `segoeuib`,
  `segoeuii`, `segoeuiz` **und** `segoeuil`), nicht nur mit den vier Textschnitten — sonst stünde
  Fließtext in Selawik Light neben Überschriften in Segoe UI („keine Mischung im Dokument").
  Auf Windows ist `segoeuil.ttf` immer dabei.
- **Warnung:** Selawik hat **kein U+00A0** (geschütztes Leerzeichen), das die Typografie
  (E17-S02) setzt, und kein U+202F. Für PDF (E05) muss der Generator ausweichen (z. B. als
  Leerzeichen setzen oder `glyph-missing` melden); ein Test hält die Lücke fest.
- DocLibs-Quellen (`Fonts.cs`, `TrueTypeInfo.cs`) lagen nicht vor; der Port folgt der
  Beschreibung im Plan.

### Prüfpunkte

- Herkunft der Schriftdateien akzeptieren oder durch die Dateien der Release-Zip
  (`selawk.ttf`, `selawkb.ttf`, `selawkl.ttf`) ersetzen — vor allem Selawik Light.
- Auf einem Windows-Rechner `fonts.resolve().name == "Segoe UI"` und `fsType` der echten Segoe-UI-,
  Consolas- und Georgia-Dateien prüfen (erwartet: einbettbar).
- `width()` gegen `text_metrics.width()`: Selawik ist für einen deutschen Mustersatz rund 5–8 %
  schmaler als die Schätzung (Test erlaubt 15 %).

### Offene Punkte

- E05-S01 nutzt `design.fonts` für Auswahl und Dateien und muss fehlende Glyphen (U+00A0)
  behandeln; E06-S04 braucht für resvg Dateipfade (`importlib.resources.as_file` auf
  `fonts.read`-Namen oder die Bytes direkt).
- Genaueres Fitting der Folien mit echten Breiten (`text_metrics.py`) bleibt außerhalb dieser
  Story.
