# E04-S05 Schulungsvorlage, englische Titelfolie, Sticker „VERTRAULICH"

> Status: in Prüfung
> Epic: [E04 PPTX-Generator auf der PTA-PowerPoint-Vorlage](../50-entwurf/E04-pptx-generator.md)
> Milestone: [M04 Präsentieren und Schulung](../50-entwurf/M04-praesentieren-und-schulung.md)

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

- [x] `kennzeichnung: vertraulich` zeigt „VERTRAULICH" oben rechts vor der Eckklammer auf jeder Folie
      mit Mastergrafiken, in Basis- und Schulungsvorlage.
- [x] Ohne Angabe sieht ein Schulungsdeck aus wie die Schulungsvorlage („Für den internen
      Gebrauch"), ein Basisdeck hat keinen Sticker.
- [x] Unbekannte Werte für `kennzeichnung` werfen `DocumentConversionError` mit den gültigen Werten.

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

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08. Neu: `generation/pptx/sticker.py` (`resolve`, `apply`,
`build`), `design.variants.Marking`, `design.slides.STICKER` (`StickerStyle`) und
`ENGLISH_LOGO_NAME`, eingebettete Vorlage `design/templates/slides-schulung-en.pptx`.
Angepasst: `markdown/front_matter.py` (`Keys.MARKING`), `design/variants.py`
(`GeneratedTexts.confidential/internal/draft`, `marking()`, `SlidesVariant.default_marking`,
`package_file` für `en` in beiden Varianten, `SLIDES_SOURCES`, `SLIDES_WITHOUT_TITLE_LOGO`),
PPTX `options.py` (`marking`), `generator.py` (Schlüssel, `resolve` vor dem Laden der Vorlage,
`apply` danach), `writer.py` (englisches Logo auch in `schulung`, mit Namen `PTA-Logo EN`),
Konverter `conversions/pptx.py` (überspringt das englische Logo), Werkzeug
`tools/prepare-templates/prepare-templates.py` (`remove_title_logos`). Tests:
`tests/generation/pptx/test_sticker.py`, `tests/generation/pptx/test_variants.py`, ergänzt
`tests/design/test_variants.py`, `test_embedded_templates.py`, `test_model_matches_templates.py`.
Beispiel `samples/funktionen/varianten-vertraulich-folien.md`, `varianten-folien.md` ergänzt,
README und Rundreisen. Doku: `docs/verwendung.md` (Abschnitt „Kennzeichnung (E04-S05)",
Tabelle), `docs/anleitung.md`, `docs/ki-anleitung.md`; `ai/Gedächtnis.md`.

### Entscheidungen

- **Ein Schlüssel `kennzeichnung`** mit `vertraulich`, `intern`, `entwurf`, `kein` (Entscheidung
  2026-11-07); `entwurf` gibt es in PowerPoint schon jetzt als Sticker „ENTWURF"/„DRAFT" im selben
  Muster. `PptxOptions.marking = None` heißt „wie die Vorlage" (`basis` ohne, `schulung`
  `intern`); das Front Matter schlägt die Optionen.
- **`schulung` + `kein`** wirft `DocumentConversionError` mit Hinweis auf die PTA-Regel und den
  dort gültigen Werten (Antwort 1). Der Fehler kommt vor dem Laden der Vorlage.
- **Sticker auf dem Master** aller Folienmaster des Decks: in `schulung` bleibt „Rectangle 7"
  unverändert bis auf Text und `lang` (ohne Angabe byte-gleich zum Vorlagen-Master, getestet);
  in `basis` wird dieselbe Form am Ende des Master-`spTree` angefügt (über der Eckklammer wie in
  der Schulungsvorlage), gleicher Name „Rectangle 7", nur Schemafarben. Lage und Größe sind für
  alle Texte die der Schulungsform (5,01 cm breit) — „VERTRAULICH" steht also nicht in der
  schmaleren 4,25-cm-Form der Vorlagensammlung, sondern rechtsbündig in der breiteren; die
  rechte Kante ist bei beiden dieselbe.
- **Maße auf das EMU** (`Area(10_252_364, 136_799, 1_802_836, 340_397)`) statt gerundeter
  Zentimeter, damit die Basisform deckungsgleich mit der Schulungsform ist; der Vergleichstest
  prüft Lage, Ränder, Verlauf, Größe und Farbe des Texts gegen den Schulungs-Master.
- **Englische Schulungsvariante** (Antwort 2): `prepare-templates` erzeugt
  `slides-schulung-en.pptx` aus der Schulungsvorlage und entfernt auf den vier Titellayouts jede
  Form mit EMF-Bild samt Beziehung („Picture 7"; auf `Titelfolie Branchen` der Bildplatzhalter
  idx 36) — genau das, was die englische Titelfolie gegenüber der Basisvorlage fehlt. Das
  Werkzeug bricht ab, wenn es auf einem Titellayout nicht genau ein Logo findet. Der Generator
  setzt das englische Logo wie bisher an `ENGLISH_LOGO_AREA`.
- **Layouts ohne Mastergrafiken** zeigen keinen Sticker (Antwort 3).

### Abweichungen

- **Konverter:** Das englische Logo heißt jetzt `PTA-Logo EN` und der PPTX-Konverter lässt es
  weg — vorher kam es aus englischen Basis-Decks als Bild ins Markdown zurück, und die Rundreise
  von `varianten-folien.md` (Schulung + Englisch) hätte es neu gezeigt. Nicht im Plan, aber das
  Logo ist Teil des Designs wie das deutsche des Layouts.
- **`SLIDES_SOURCES`** nennt die Schulungsvorlage nun zweimal (für `slides-schulung.pptx` und
  `-en.pptx`); `test_model_matches_templates.py` prüft jede Quelldatei nur einmal.
- Die Schulungs-Beispiele laufen über `PptxOptions(variant=TRAINING)` gegen **dieselben**
  Rundreise-Erwartungen wie die Basis (`tests/generation/pptx/test_variants.py`) — der Konverter
  liest keine Master, die Erwartungen sind identisch; eigene Erwartungsdateien gibt es nicht.

### Warnungen

- **Warnung:** `slides-schulung-en.pptx` macht das Paket um knapp 6 MB größer (die Bilder der
  Schulungsvorlage liegen darin ein zweites Mal). Die vorsichtigere Alternative — das Logo erst
  beim Erzeugen aus den Layouts zu entfernen — hätte eingebettete Vorlage und Laufzeit vermischt;
  gewählt ist der Weg des Plans (`prepare-templates`).
- **Warnung:** Auf den Titelfolien mit Bild (`bild-01`, `bild-02`, `branchen`) liegt das Foto des
  Layouts über dem Master — der Sticker ist dort wie in der Schulungsvorlage verdeckt. Auf
  `Titelfolie ohne Bild` der Basisvorlage (Mastergrafiken sichtbar) steht er. Wer „VERTRAULICH"
  auch auf dem Titelfoto braucht, bräuchte eine Form auf der Folie (nicht umgesetzt, Antwort 3
  sinngemäß).
- **Warnung:** Word und PDF lehnen `kennzeichnung` bis E12-S03 als unbekannten Schlüssel ab.

### Prüfpunkte

- `.tmp/review/deck-vertraulich.pptx`, `deck-schulung.pptx`, `deck-en.pptx`,
  `deck-schulung-en.pptx` in PowerPoint öffnen: Sticker oben rechts vor der Eckklammer, Verlauf
  und Schrift wie in der Schulungsvorlage; im Folienmaster an einer Stelle änderbar; englisches
  Logo auf der Titelfolie, kein deutsches darunter.
- Englische Schulungs-Titelfolien (`titelfolie: branchen` u. a.) mit der englischen Titelfolie der
  Basis vergleichen.
- PowerPoint-Prüfung steht aus (kein Office auf der Entwicklungsmaschine).

### Offene Punkte

- E12-S03: `kennzeichnung` in Word und PDF mit demselben `Marking`, Texte aus
  `GeneratedTexts.marking`.
- Branchenfoto auf `titelfolie: branchen` (Notiz oben) bleibt eine Lücke aus E04-S01.
