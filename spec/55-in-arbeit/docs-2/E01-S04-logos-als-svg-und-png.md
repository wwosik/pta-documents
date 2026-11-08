# E01-S04 Logos als SVG und PNG aus den EMF der Vorlagen

> Status: in Bearbeitung (docs-2)
> Epic: [E01 PTA-Design als einziges Design](../../50-entwurf/E01-pta-design.md)
> Milestone: [M03 Grafik, Diagramme und Charts](../../50-entwurf/M03-grafik-diagramme-und-charts.md)

## Zusammenfassung

Das PTA-Logo, das in den Vorlagen nur als EMF vorliegt, wird von `prepare-templates` einmal nach
SVG und PNG gewandelt und als Paketdaten mitgeliefert — für die Kopfzeile des PDF (E05-S03) und
für SVG- und PNG-Ausgaben, die ein Logo brauchen.

## Kontext

- Entscheidung 2026-11-06: Logo aus den EMF der Vorlagen wandeln (E05, Frage 3). DocLibs hat dafür
  keinen Code (Logos kamen als PNG aus dem Brand).
- Die Vektorlogos sind reine Pfad-EMFs ohne EMF+-Anteil (ausgelesen 2026-11-06):

  | Quelle | Teil | Inhalt | Füllfarbe im EMF |
  | ------ | ---- | ------ | ---------------- |
  | Word-Vorlagen (alle vier, gleich) | `word/media/image1.emf`, 1 060 Byte, Kopfzeile 2,22 × 1,28 cm | Wortmarke mit Eckklammer, ohne Slogan | `026FB9` |
  | `PTA-Powerpoint-Basisvorlage.potx` | `ppt/media/image2.emf`, 9 584 Byte, Titellayouts | weiß, mit Slogan „Kundenorientierte IT-Lösungen seit 1969" | `FFFFFF` |
  | dieselbe | `ppt/media/image9.emf`, 1 060 Byte, `Abbschlussfolie` | weiß, ohne Slogan | `FFFFFF` |

  Vorkommende Datensätze: Header, `SETMAPMODE`, `SETWINDOWEXTEX`/`ORGEX`,
  `SETVIEWPORTEXTEX`/`ORGEX`, `SETBKMODE`, `SETPOLYFILLMODE`, `CREATEBRUSHINDIRECT`,
  `EXTCREATEPEN`, `SELECTOBJECT`, `DELETEOBJECT`, `BEGINPATH`/`ENDPATH`/`FILLPATH`, `MOVETOEX`,
  `POLYBEZIERTO16`, `POLYPOLYGON16`, `CLOSEFIGURE`, `EOF` — ein kleiner eigener Interpreter
  genügt, kein Inkscape oder LibreOffice.
- `image4.emf` (Logo-Platzhalter von `Titelfolie Branchen`) ist EMF+ mit Bitmap und wird nicht
  gebraucht; das englische Logo gibt es nur als PNG (`slides-logo-en.png`, E01-S02).
- Der Farbwert `026FB9` im Word-Logo weicht vom PTA-Blau `006FB9` ab (siehe Frage 1).

## Vorgeschlagener Ansatz

1. `tools/prepare-templates/emf.py`: liest die oben genannten Datensätze, rechnet über
   Fenster/Viewport in Logo-Koordinaten um und schreibt pro `FILLPATH` bzw. `POLYPOLYGON16` einen
   `<path>` (M/L/C/Z) mit `fill` und `fill-rule` (ALTERNATE → `evenodd`, WINDING → `nonzero`),
   `viewBox` aus den Header-Bounds. Ein unbekannter Datensatz bricht mit Typnummer ab — nichts
   wird still ausgelassen.
2. `prepare-templates` findet die Logos **über die Beziehungen**, nicht über Dateinamen: das Bild
   in der Kopfzeile der Hochformat-Vorlage, das Bild auf `Titelfolie mit Bild 01` und auf
   `Abbschlussfolie`. Ergebnis in `src/pta_documents/design/logos/`: `logo-word.svg`,
   `logo-slides.svg`, `logo-slides-plain.svg` und je ein PNG (2 000 px breit, transparent,
   gerastert mit resvg aus dem Extra `svg`, das in der Entwicklungsumgebung installiert ist).
   `--check` vergleicht wie bisher; deterministisch (feste Zahlenformatierung, sortierte Ausgabe).
3. `pta_documents/design/logos.py`: `Logo` (`StrEnum`: `WORD`, `SLIDES`, `SLIDES_PLAIN`),
   `svg(logo) -> bytes`, `png(logo) -> bytes`, `aspect_ratio(logo) -> float` und
   `drawing(logo) -> Drawing` (E02-S03), das die eigene, bekannte SVG-Teilmenge zurückliest, damit
   das PDF das Logo als Vektor zeichnet. Die Farbe wird beim Schreiben auf die Konstante aus
   `design.colors` gesetzt (siehe Frage 1), sodass der Hex-Test für `src/` sauber bleibt.
4. Tests: jedes SVG parst, Seitenverhältnis = EMF-Frame = Ausdehnung in der Vorlage (±1 %);
   Füllfarben nur aus `design.colors`; PNG-Größe und Transparenz; `drawing()` ergibt dieselben
   Pfade wie das SVG; das Wheel enthält die Logos. Zum Ansehen `.tmp/review/logos.html` mit allen
   drei Logos auf weißem und dunkelblauem Grund.

## Akzeptanzkriterien

- [ ] `./run.sh prepare-templates` erzeugt die drei Logos als SVG und PNG reproduzierbar aus
      `source-templates/`; `--check` meldet keinen Unterschied.
- [ ] Das SVG des Word-Logos deckt sich in Form und Seitenverhältnis mit dem Logo in der
      Kopfzeile (Sichtvergleich in `.tmp/review/`, vom Menschen bestätigt).
- [ ] `design.logos.drawing(Logo.WORD)` liefert ein `Drawing` mit Vektorpfaden.

## Offene Fragen

1. Das Word-Logo ist im EMF mit `026FB9` gefüllt, das Theme-PTA-Blau ist `006FB9`. Soll das
   gewandelte Logo auf `006FB9` vereinheitlicht werden (Vorschlag), oder den EMF-Wert behalten?

> (2026-11-07) Ja, auf `006FB9` vereinheitlichen.

## Notizen

- Abhängigkeit: Schritt 3 (`drawing()`) braucht das Zeichenmodell aus E02-S03; SVG und PNG
  entstehen ohne es.
