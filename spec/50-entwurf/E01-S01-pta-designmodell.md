# E01-S01 PTA-Designmodell

> Status: Entwurf
> Epic: [E01 PTA-Design als einziges Design](E01-pta-design.md)
> Milestone: [M01 PTA-Dokumente aus Markdown](M01-pta-dokumente-aus-markdown.md)

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

- [ ] Alle Farbwerte der Designanalyse sind als benannte Konstanten verfügbar; keine weitere Datei
      im Code enthält Hex-Farben.
- [ ] Der Vergleichstest Modell ↔ Vorlagen läuft grün.
- [ ] `vorlage: <unbekannt>` wirft `DocumentConversionError` mit den gültigen Varianten.

## Offene Fragen

1. Namen der Varianten im Front Matter: deutsch wie oben (`hoch`, `quer`, `schulung`) oder
   englisch (`portrait`, `landscape`, `training`)?

> (2026-11-06) Deutsch (`hoch`, `quer`, `schulung` …).

2. Ist die englische Titelfolie eine eigene Variante, oder folgt sie aus `lang: en` im Front
   Matter (und schaltet dann auch Texte wie „Seite"/„Stand" in Word um)?

> (2026-11-06) Über `sprache: en`, das auch die erzeugten Texte umschaltet.

## Notizen

