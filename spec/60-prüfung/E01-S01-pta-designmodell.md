# E01-S01 PTA-Designmodell

> Status: in Prüfung
> Epic: [E01 PTA-Design als einziges Design](../50-entwurf/E01-pta-design.md)
> Milestone: [M01 PTA-Dokumente aus Markdown](../50-entwurf/M01-pta-dokumente-aus-markdown.md)

## Zusammenfassung

Ein unveränderliches Modell `pta_documents.design` mit den PTA-Farben, Schriften, Maßen und den
wählbaren Vorlagenvarianten — die einzige Stelle, an der Code Designwerte kennt.

## Kontext

Werte: [Designanalyse](../10-analysen/2026-11-06%20pta-designstandards.md). In DocLibs übernahm das
`ResolvedBrand` (425 Zeilen) samt Validierung und Standardwerten; davon bleibt nur ein Bruchteil,
weil nichts mehr validiert oder ergänzt werden muss.

## Vorgeschlagener Ansatz

1. `design/colors.py`: benannte Konstanten (`PTA_BLUE = "006FB9"`, `DARK_BLUE`, `LIGHT_BLUE`,
   `GREY_DARK`, `GREY_MID`, `GREY_LIGHT`, `YELLOW`, `SIGNAL_GREEN`, `SIGNAL_AMBER`, `SIGNAL_RED`,
   `TEXT_WORD = "000000"`, `TEXT_SLIDES = "404040"`), die Akzentreihenfolge als Palette und die
   Zuordnung der Status-Kategorien aus DocLibs (`success` → Grün, `warning` → Gelb-Orange,
   `danger` → Rot, `info` → PTA-Blau, `neutral` → Mittelgrau).
2. `design/variants.py`: Aufzählungen der Varianten —
   Word `hoch` (Standard), `hoch-ohne-deckblatt`, `quer`, `quer-ohne-deckblatt`;
   PowerPoint `basis` (Standard), `schulung` — mit Vorlagendatei und Eigenschaften (Deckblatt
   ja/nein, Seitenformat, Logo). `sprache: en` schaltet in PowerPoint auf die englische
   Titelfolie und in beiden Formaten die erzeugten Texte um („Seite"/„Page", „Stand"/„As of",
   „Tabelle"/„Table", „Abbildung"/„Figure").
3. `design/word.py`, `design/slides.py`: nur Werte, die kein Generator aus der Vorlage lesen kann —
   Folientabelle, Fazit-Box, Kommentarbox, Inhaltsfläche und Raster, Layoutnamen, PDF-Seitenaufbau
   (aus der Word-Vorlage abgeleitet).
4. Ein Test liest Theme und Formatvorlagen aus den Vorlagen und vergleicht sie mit dem Modell —
   ändert die PTA eine Vorlage, schlägt er fehl statt still abzuweichen.
5. Front Matter: `vorlage:` wählt die **Variante** (z. B. `vorlage: quer`); unbekannte Namen
   werfen mit Liste der gültigen.

## Akzeptanzkriterien

- [x] Alle Farbwerte der Designanalyse sind als benannte Konstanten verfügbar; keine weitere Datei
      im Code enthält Hex-Farben.
- [x] Der Vergleichstest Modell ↔ Vorlagen läuft grün.
- [x] `vorlage: <unbekannt>` wirft `DocumentConversionError` mit den gültigen Varianten.

## Offene Fragen

1. Namen der Varianten im Front Matter: deutsch wie oben (`hoch`, `quer`, `schulung`) oder
   englisch (`portrait`, `landscape`, `training`)?

> (2026-11-06) Deutsch (`hoch`, `quer`, `schulung` …).

2. Ist die englische Titelfolie eine eigene Variante, oder folgt sie aus `lang: en` im Front
   Matter (und schaltet dann auch Texte wie „Seite"/„Stand" in Word um)?

> (2026-11-06) Über `sprache: en`, das auch die erzeugten Texte umschaltet.

## Notizen


## Implementierungsnotizen

- Module: `design/colors.py` (einzige Datei mit Farbwerten; ein Test durchsucht `src/` nach
  Hex-Literalen), `design/variants.py` (`WordVariant`, `SlidesVariant`, `Language`,
  `GeneratedTexts`), `design/word.py`, `design/slides.py`.
- Varianten sind `StrEnum`s, deren Wert der deutsche Front-Matter-Name ist; `parse()` wirft
  `DocumentConversionError` mit Liste der gültigen Werte. Das Einlesen von `vorlage:`/`sprache:`
  aus dem Front Matter geschieht in den Generatoren (E03-S01, E04-S01).
- `sprache: en` wählt für `basis` die eingebettete englische Titelfolienvorlage
  (`slides-basis-en.pptx`); für `schulung` gibt es keine englische Fassung — dort schaltet
  `sprache: en` nur die erzeugten Texte um.
- **Abweichung von der Designanalyse:** Die beiden Querformat-Vorlagen enthalten die Formatvorlagen
  `Hyperlink`, `toc 1` und `toc 2` nicht (Word legt sie erst bei Gebrauch an).
  `word.BORROWED_STYLES` nennt sie; der DOCX-Generator übernimmt sie aus der Hochformat-Vorlage.
- Stilnamen sind die internen Namen aus `styles.xml` (`heading 1`, `List Bullet`, `caption` …),
  nicht die deutschen Anzeigenamen — python-docx sucht über `w:name`.
- `Code` und `Zitat` gibt es in keiner Vorlage; der Generator legt sie an (E03-S02).
- Der Vergleichstest liest direkt aus `source-templates/` (Theme-Farben, Schriften, Signalfarben,
  Formatvorlagen, Tabellenformat `PTA`, Layoutnamen, Platzhalter-Indizes, Inhaltsfläche,
  Schriftgrößen der fünf Textebenen).
- ruff: `RUF001`–`RUF003` sind abgeschaltet, weil deutsche Texte bewusst Gedankenstriche und
  typografische Anführungszeichen enthalten.
