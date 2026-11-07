# E04-S05 Schulungsvorlage, englische Titelfolie, Sticker „VERTRAULICH"

> Status: Entwurf
> Epic: [E04 PPTX-Generator auf der PTA-PowerPoint-Vorlage](E04-pptx-generator.md)
> Milestone: [M04 Präsentieren und Schulung](M04-praesentieren-und-schulung.md)

## Zusammenfassung

Was an den Varianten der PowerPoint-Vorlage noch fehlt: ein Vertraulichkeits-Sticker per Front
Matter („VERTRAULICH" bzw. „Für den internen Gebrauch") nach dem Muster der Vorlagen, die
Absicherung der Schulungsvorlage durch Tests über alle Folienarten und die englischen Texte dazu.

## Kontext

- Schon erledigt (E04-S01, E01-S02): `vorlage: schulung` wählt `slides-schulung.pptx`;
  `sprache: en` mit `basis` nimmt `slides-basis-en.pptx` und setzt das englische Logo
  (`ENGLISH_LOGO_AREA`) auf die Titelfolie. Für `schulung` gibt es keine englische Fassung;
  `sprache: en` schaltet dort nur erzeugte Texte um.
- Sticker in den Vorlagen (Inventar): Schulungs-Master „Rectangle 7" bei 28,48/0,38 cm,
  5,01 × 0,95 cm, Verlauf Akzent 6 transparent (1,77 %) → Akzent 6 (31 %) → Text 2 (100 %),
  Ränder l/o/u 0,20 cm, r 0,30 cm, mittig, Text „Für den internen Gebrauch" 10 pt Akzent 4 Segoe
  UI rechtsbündig. Muster „VERTRAULICH" (Vorlagensammlung, Folie 44) gleich gebaut bei
  29,23/0,38 cm, 4,25 × 0,95 cm.
- Der Schulungs-Master zeigt den Sticker auf allen Layouts mit Mastergrafiken; die Schulungsvorlage
  blendet ihn auf `Titelfolie ohne Bild` und `Zitat 01` aus und auf `Titel, Bild und Text`,
  `Titel, Text und Bild 02`, `Titel, Text und zwei Bilder 01` ein (`showMasterSp`).
- PTA-Regel (Schulungsvorlage, Folie 1): Aufzeichnungen nur mit „Kennzeichnung Vertraulichkeit
  der Folien, d.h. nur für internen Gebrauch".

## Vorgeschlagener Ansatz

1. **Front Matter** `kennzeichnung:` (neuer Schlüssel in `front_matter.Keys`; in Word und PDF
   wirkt er nach E12-S03 — Entscheidung 2026-11-07: ein gemeinsamer Schlüssel statt `sticker`) mit
   den Werten `vertraulich`, `intern`, `entwurf`, `kein`. Standard: `basis` → `kein`, `schulung` →
   `intern` (wie die Vorlage). `PptxOptions.marking: Marking | None`; `Marking` als `StrEnum` in
   `design/variants.py`, gemeinsam mit E12-S03.
2. **Text:** `GeneratedTexts` um „VERTRAULICH"/„CONFIDENTIAL", „Für den internen
   Gebrauch"/„For internal use only" und „ENTWURF"/„DRAFT" erweitern.
3. **Zeichnen** in `generation/pptx/sticker.py`, **auf dem Master** des erzeugten Decks wie in der
   Schulungsvorlage (damit er auf jeder Folie mit Mastergrafiken steht und in PowerPoint an einer
   Stelle geändert wird):
   - `schulung`: die vorhandene Form „Rectangle 7" behalten und nur ihren Text setzen (`intern`
     bleibt, `vertraulich` ersetzt ihn; `kein` siehe Frage 1).
   - `basis`: eine Form nach demselben Muster in den Master-`spTree` einfügen, Lage und Größe
     wie die Schulungsform (rechtsbündig vor der Eckklammer), Farben als Schemafarben
     (`accent6`, `tx2`, `accent4`), keine Hex-Werte.
   - Maße und Ränder in `design/slides.py` (`STICKER_AREA`), geprüft gegen den Schulungs-Master
     im Vergleichstest (E01-S01).
4. **Schulungsvorlage absichern:** die Rundreise-Beispiele `deck.md` (E04-S02), `layouts.md`
   (E04-S03) und `layouts-pta.md` (E04-S04) laufen zusätzlich mit `vorlage: schulung`; ein Test
   prüft, dass die fünf geänderten Layouts ihre `showMasterSp`-Einstellung aus der Vorlage behalten
   und der Sticker auf den Inhaltsfolien sichtbar ist.
5. **Englisch:** Test, dass `sprache: en` + `basis` auf allen vier Titellayouts das englische Logo
   und kein deutsches zeigt (auch `Titelfolie Branchen`, dessen Logo-Platzhalter idx 36 in der
   englischen Vorlage fehlt); mit `schulung` nach Antwort auf Frage 2.
6. Ansicht: `.tmp/review/deck-schulung.pptx`, `deck-vertraulich.pptx`, `deck-en.pptx`.

## Akzeptanzkriterien

- [ ] `kennzeichnung: vertraulich` zeigt „VERTRAULICH" oben rechts vor der Eckklammer auf jeder Folie
      mit Mastergrafiken, in Basis- und Schulungsvorlage.
- [ ] Ohne Angabe sieht ein Schulungsdeck aus wie die Schulungsvorlage („Für den internen
      Gebrauch"), ein Basisdeck hat keinen Sticker.
- [ ] Unbekannte Werte für `kennzeichnung` werfen `DocumentConversionError` mit den gültigen Werten.

## Offene Fragen

1. Darf `kennzeichnung: kein` die Kennzeichnung der **Schulungsvorlage** entfernen? Vorschlag: nein
   (Fehler mit Hinweis auf die PTA-Regel), weil die Kennzeichnung dort verpflichtend ist.

> (2026-11-07) Nein — Fehler mit Hinweis auf die PTA-Regel.

2. Soll es eine englische Schulungsvariante geben (`vorlage: schulung` + `sprache: en`):
   `prepare-templates` entfernt wie in der englischen Titelfolie das deutsche Logo aus den
   Titellayouts der Schulungsvorlage, der Generator setzt das englische? Oder bleibt das deutsche
   Logo mit deutschem Slogan (heutiger Stand)?

> (2026-11-07) Ja, englische Schulungsvariante mit englischem Logo wie bei der Titelfolie EN.

3. Auf Layouts ohne Mastergrafiken (in der Basisvorlage u. a. `Titel und Bild 02`,
   `Zwischenfazit 01/02`, `Zitat 02`) erscheint ein Master-Sticker nicht — wie in der
   Schulungsvorlage. Genügt das, oder soll „VERTRAULICH" dort zusätzlich als Form auf der Folie
   stehen?

> (2026-11-07) Genügt, wie die Schulungsvorlage.

## Notizen

- `titelfolie: branchen` erwartet ein Branchenfoto im Bildplatzhalter idx 34; heute bleibt er leer
  und wird entfernt. Das ist eine Lücke aus E04-S01, nicht Teil dieser Story.
