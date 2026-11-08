# E01-S04 Logos als SVG und PNG aus den EMF der Vorlagen

> Status: in Prüfung
> Epic: [E01 PTA-Design als einziges Design](../50-entwurf/E01-pta-design.md)
> Milestone: [M03 Grafik, Diagramme und Charts](../50-entwurf/M03-grafik-diagramme-und-charts.md)

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

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08: EMF-Leser `tools/prepare-templates/emf.py`,
Logo-Teil in `tools/prepare-templates/prepare-templates.py` (`build_logos`, `sync`), Unterpaket
`src/pta_documents/design/logos/` mit dem Modul und den sechs Dateien `logo-word`,
`logo-slides`, `logo-slides-plain` je als `.svg` und `.png`. Tests in
`tests/design/test_logos.py` und `tests/test_package.py` (Wheel), Doku in `docs/verwendung.md`
(Abschnitt „Logos als SVG und PNG"), Eintrag in `ai/Gedächtnis.md`. `samples/` und die
Anleitungen für Schreiber bleiben unverändert — keine neue Syntax, kein neuer Schlüssel.

### Entscheidungen

- **Unterpaket statt `logos.py`:** Code und Dateien liegen zusammen in `design/logos/`
  (`__init__.py` + Paketdaten), wie bei `design/fonts/`. Ein Modul `logos.py` neben einem Ordner
  `logos/` wäre möglich, aber verwirrend. Der Importpfad `pta_documents.design.logos` bleibt wie
  geplant.
- **Koordinaten:** Punkte werden über Fenster/Viewport (`MM_ANISOTROPIC`) in Geräteeinheiten
  umgerechnet und um die linke obere Ecke der Header-Bounds verschoben; `viewBox="0 0 B H"` mit
  B/H = Ausdehnung der Header-Bounds (Word 496 × 284, Folien 3409 × 1950). Die Bounds decken sich
  exakt mit dem EMF-Frame. Zahlen mit höchstens drei Nachkommastellen, ohne Nullen am Ende, ohne
  `-0`; `width`/`height` des SVG = viewBox.
- **Farben:** Das Werkzeug bildet jede EMF-Füllfarbe über `LOGO_COLORS` auf eine Konstante aus
  `design.colors` ab (`006FB9`, `FFFFFF`, und `026FB9` → `PTA_BLUE` nach Frage 1); eine andere
  Farbe bricht ab. Die SVG-Dateien enthalten die Werte; der Hex-Test gilt weiter nur für `.py`.
- **Logos finden:** Word über die `header`-Beziehungen von `word/document.xml` der
  Hochformatvorlage mit Deckblatt; alle Kopfzeilen müssen genau dasselbe EMF zeigen. Folien über
  den Layoutnamen (`p:cSld/@name`) und das eine EMF, das ein `a:blip` des Layouts referenziert.
  Ein Test prüft, dass alle vier Word-Vorlagen in allen Kopfzeilen mit Bild dasselbe EMF tragen.
- **EMF-Leser streng:** außer unbekannten Datensätzen brechen auch nicht unterstützte Werte ab
  (anderer Map-Mode als `MM_ANISOTROPIC`, Pinsel nicht `BS_SOLID`, Stift nicht `PS_NULL`,
  Lagerobjekte, `MOVETOEX` außerhalb eines Pfads, `POLYPOLYGON16` innerhalb). `SETBKMODE` wird
  übergangen (wirkt nur auf Text und Schraffuren). Alle drei Logos füllen mit `WINDING` →
  `fill-rule="nonzero"`.
- **PNG:** resvg mit `width=2000`, `skip_system_fonts=True`, ohne Hintergrund (transparent);
  Höhe gerundet (1146 bzw. 1145 px). `--check` vergleicht PNGs nach Pixeln (RGBA über Pillow),
  damit ein anderer PNG-Encoder allein keinen Unterschied meldet; SVGs byte-genau.
- **Aufräumen:** Im Logo-Ordner entfernt das Werkzeug nur fremde `.svg`/`.png`, nie das Modul.
- pyright bekommt `extraPaths = ["src", "tools/prepare-templates"]`, pytest
  `pythonpath = ["tools/prepare-templates"]`, damit Werkzeug und Test `import emf` schreiben
  können (ohne explizites `src` verliert pyright die automatische Suche dort und meldet einen
  Fehler in `tests/conversions/test_registry.py`).
- Zum Ansehen schreibt `test_review_page` `.tmp/review/logos.html`: alle drei Logos als SVG und
  PNG auf weißem und dunkelblauem Grund.

### Abweichungen

- **Warnung:** `drawing(logo) -> Drawing` (Schritt 3) ist **nicht** umgesetzt — das Zeichenmodell
  aus E02-S03 gibt es noch nicht (Notiz der Story: Abhängigkeit). Stattdessen liefert
  `shapes(logo)` die Pfade als `LogoShape(segments, fill, even_odd)` mit Segmenten
  `("M"|"L"|"C"|"Z", Koordinaten)`; E02-S03 ergänzt `drawing()` als dünne Abbildung darauf.
  Das dritte Akzeptanzkriterium bleibt damit bis E02-S03 offen.
- Zusätzlich `size(logo)` (Breite/Höhe der viewBox) und `PNG_WIDTH`.
- Seitenverhältnis Word-Logo: viewBox/EMF-Frame 1,7465, Kopfzeilenrahmen der Vorlage
  799 200 × 460 800 EMU = 1,7344 — 0,7 % Abweichung, innerhalb der geplanten ±1 %. Word staucht
  das Logo also minimal; das SVG folgt dem EMF.
- Einzelne Punkte liegen bis zu 1/3 Einheit außerhalb der Header-Bounds (z. B. x = 496,333);
  das SVG beschneidet sie wie das EMF — sichtbar ist das nicht.

### Warnungen

- **Warnung:** `prepare-templates` (auch `--check` und damit
  `test_embedded_templates_are_up_to_date`) braucht jetzt resvg aus dem Extra `svg`; ohne es
  bricht das Werkzeug mit einem Hinweis auf `pip install -e '.[svg]'` ab. `run.sh setup`
  installiert das Extra.
- **Warnung:** Die PNGs hängen von der Rasterung durch resvg ab (hier `resvg-py` 0.5.0). Eine
  andere resvg-Version kann einzelne Kantenpixel anders glätten; dann meldet `--check` einen
  Unterschied, und `./run.sh prepare-templates` schreibt die PNGs neu (Diff ansehen, committen).

### Prüfpunkte

- `.tmp/review/logos.html` öffnen (entsteht mit `./run.sh test tests/design/test_logos.py`):
  Form und Seitenverhältnis des Word-Logos gegen die Kopfzeile einer Word-Vorlage halten
  (Akzeptanzkriterium 2, Sichtvergleich durch den Menschen).
- Farbe des Word-Logos: jetzt `006FB9` statt `026FB9` aus dem EMF.

### Offene Punkte

- E02-S03: `logos.drawing()` aus `shapes()` bauen (`even_odd` → `DrawingShape.even_odd`,
  Maßstab viewBox → CSS-Pixel nach Bedarf) und das dritte Akzeptanzkriterium hier abhaken.
- E05-S03 nimmt das Logo für die PDF-Kopfzeile aus diesem Modul.
