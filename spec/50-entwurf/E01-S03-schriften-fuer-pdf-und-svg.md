# E01-S03 Schriften für PDF und SVG

> Status: Entwurf
> Epic: [E01 PTA-Design als einziges Design](E01-pta-design.md)
> Milestone: [M03 Grafik, Diagramme und Charts](M03-grafik-diagramme-und-charts.md)

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
