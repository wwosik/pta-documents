# E09-S03 Folienübergänge

> Status: in Prüfung
> Epic: [E09 Präsentieren](../50-entwurf/E09-praesentieren.md)
> Milestone: [M04 Präsentieren und Schulung](../50-entwurf/M04-praesentieren-und-schulung.md)

## Zusammenfassung

Ein Front-Matter-Schlüssel setzt den Übergang aller Folien, ein Heading-Attribut den einer
Folie bzw. eines Kapitels: kein Übergang (Standard), Überblenden, Schieben, Wischen oder Morph.
Morph wird so geschrieben, dass ältere Programme überblenden.

## Kontext

- vt-tools-libs: `~/mvv/vt-tools-libs/src/VtToolsLibs.DocumentGeneration/SlideTransition.cs`
  (44 Zeilen: `None`, `Fade`, `Push`, `Wipe`, `Morph`; Namen kleingeschrieben, `Valid` für
  Fehlermeldungen) und `…Pptx/Animations.cs` `Transition(...)`: `<p:transition spd="med">` mit
  `p:fade`, `p:push`, `p:wipe`; Morph als `mc:AlternateContent` mit `mc:Choice Requires="p159"`
  (`p159:morph option="byObject"`, `spd="slow"`) und `mc:Fallback` mit `p:fade`. Geschrieben in
  `DeckWriter.cs` Z. 211 je Folie: `slide.Transition ?? options.Transition`. Front Matter
  `transition`, Attribut `{transition=…}` auf `#` (gilt für alle Folien des Kapitels) und `##`;
  Fortsetzungsfolien behalten den Übergang.
- Hier: `heading_attributes.py` kennt `.closing` und `layout="…"`, wirft für alles andere
  („Unknown heading attribute … Valid attributes: …"); E02-S02 erweitert um `.dark` und `kicker`
  und führt `check_level` ein. `PptxOptions` (24 Zeilen) hat keinen Übergang; `writer.py`
  schreibt nichts in `p:transition`. python-pptx hat keine Übergangs-API; das Element steht in
  `p:sld` direkt nach `p:clrMapOvr` und vor `p:timing` (Reihenfolge laut Schema — die
  Reihenfolge ist entscheidend, sonst meldet PowerPoint eine Reparatur).
- Die PTA-Vorlagen definieren selbst keine Übergänge; die PTA-Regeln auf den Musterfolien sagen
  dazu nichts (Designanalyse, *Regeln auf den Musterfolien*).

## Vorgeschlagener Ansatz

1. **Modell:** `SlideTransition` als `StrEnum` in `generation/common/slide_transition.py` mit den
   Werten `none`, `fade`, `push`, `wipe`, `morph`, `parse(name, format)` mit Fehlermeldung, die
   die gültigen Werte nennt; `VALID` für Guides und Meldungen. Deutsch oder englisch: Frage 1.
2. **Front Matter:** Schlüssel `uebergang` in `front_matter.Keys`, nur PPTX (Word wirft wie bei
   `fusszeile`); `PptxOptions.transition: SlideTransition = SlideTransition.NONE`;
   `apply_front_matter` setzt ihn.
3. **Heading-Attribut** `uebergang="…"` in `heading_attributes.py` (`HeadingAttributes.transition`),
   erlaubt auf `#` und `##`; doppelt genannt wirft wie `layout`. Der `DeckParser` trägt den Wert
   in `Slide.transition: SlideTransition | None` ein; bei `#` gilt er für die Trennfolie und alle
   Folien des Kapitels, bis ein `##` ihn überschreibt. Fortsetzungsfolien erben ihn.
4. **Schreiben** (`generation/pptx/animations.py`, mit E09-S02): `transition(kind) ->
   etree._Element | None`, Port von `Animations.Transition`, eingefügt an der Schemaposition in
   `p:sld` (nach `p:clrMapOvr`, vor `p:timing`); `none` schreibt nichts.
5. **Word, PDF, Konverter:** das Attribut wird angenommen und ignoriert; der Konverter liest
   `p:transition` nicht.
6. **Tests** (`tests/generation/pptx/test_transitions.py`): Front Matter setzt alle Folien;
   `##`-Attribut überschreibt eine Folie; `#`-Attribut gilt für das Kapitel; Morph erzeugt
   `mc:AlternateContent` mit `p159`-Namensraum und Fade-Rückfall; ungültiger Wert wirft mit Liste;
   Elementreihenfolge in `p:sld` ist schemakonform (Test mit lxml: Index von `p:transition` <
   Index von `p:timing`).
7. **Doku:** Tabelle der Front-Matter-Schlüssel in `docs/anleitung.md`, `docs/ki-anleitung.md`,
   `docs/verwendung.md`; Guide E04-S06; `samples/funktionen/varianten-folien.md` zeigt `uebergang`.

## Akzeptanzkriterien

- [x] `uebergang: fade` im Front Matter überblendet jede Folie; `{uebergang="push"}` auf `##`
      gilt nur für diese Folie, auf `#` für das Kapitel.
- [ ] `morph` läuft in PowerPoint 2019/365 als Morph und in älteren Programmen und LibreOffice als
      Überblendung; keine Reparaturmeldung.
- [x] Ohne Angabe hat keine Folie einen Übergang (Deck wie heute).
- [x] Ein unbekannter Wert wirft mit Zeile und den gültigen Werten; Word nimmt das Attribut ohne
      Wirkung an.

## Offene Fragen

1. Werte deutsch (`kein`, `ueberblenden`, `schieben`, `wischen`, `morph`) oder englisch wie die
   übrige Syntax (`none`, `fade`, `push`, `wipe`, `morph`)? Vorschlag: englisch — es sind
   Syntaxwerte wie `.closing`, und „Morph" heißt auch im deutschen PowerPoint so. Der
   Schlüssel bleibt deutsch (`uebergang`).

> (2026-11-07) Englisch.
2. Soll `morph` ohne eine Szene (E09-S04) überhaupt erlaubt sein? Es wirkt dann wie eine
   Überblendung mit bewegtem Titel. Vorschlag: erlauben, der Guide erklärt die Wirkung.

> (2026-11-07) Erlauben.

## Notizen

- (2026-11-07) Erweiterung nach Entscheidung im Epic (Frage 1): Richtungen `push-left|right|up|down`, `wipe-left|right|up|down` (ohne Richtung wie bisher von links), zusätzlich `split`, `cover`, `uncover`, `zoom`, `cut` nach PowerPoints dezenten Übergängen (`p:split`, `p:cover`, `p:pull`, `p:zoom`, `p:cut`). `SlideTransition` wächst entsprechend; der HTML-Deck (E10-S01) nähert sie in CSS an oder blendet.

- Kleinste Story des Epics; kann vor E09-S02 umgesetzt werden, teilt sich mit ihr nur das Modul
  `animations.py`.

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08. Neu: `generation/common/slide_transition.py`
(`SlideTransition`, `parse`, `VALID`), `tests/generation/pptx/test_transitions.py` (37 Tests).
Angepasst: `generation/common/heading_attributes.py` (`uebergang="…"`,
`HeadingAttributes.transition`, `VALID…`), `markdown/front_matter.py` (`Keys.TRANSITION`),
PPTX `options.py` (`transition`), `generator.py` (Schlüssel `uebergang`), `model.py`
(`Slide.transition`, kw-only), `parser.py` (`chapter_transition`, `_transition`),
`animations.py` (`transition`, `set_transition`), `writer.py` (`new_slide`);
`tests/samples/test_funktionen.py` (Attribut `uebergang` → Feld `transition`). Beispiele:
`# Präsentieren {uebergang="fade"}` und Folie „Folienübergang" (`push-up`) in
`samples/funktionen/funktionen-praesentation.md`, `uebergang: fade` in `varianten-folien.md`,
README und Rundreisen erneuert. Doku: `docs/verwendung.md` (Abschnitt „Folienübergänge
(E09-S03)", Front-Matter- und Syntax-Tabelle), `docs/anleitung.md` („Folienübergänge",
Schlüssel), `docs/ki-anleitung.md`; `ai/Gedächtnis.md`.

### Entscheidungen

- **Werte englisch** (Frage 1), Schlüssel und Attribut deutsch (`uebergang`); `morph` ohne Szene
  erlaubt (Frage 2), der Guide sagt, dass er dann überblendet bzw. den Titel bewegt.
- **Werte** nach der Notiz vom 2026-11-07: `none`, `fade`, `push`, `push-left|right|up|down`,
  `wipe`, `wipe-left|right|up|down`, `split`, `cover`, `uncover`, `zoom`, `cut`, `morph`.
  Groß-/Kleinschreibung egal (wie vt-tools-libs).
- **Geltung:** Folie > Kapitel > Deck. Ein `#` setzt den Übergang für seine Folie (Titel-,
  Trenn- oder Abschlussfolie) und alle `##` bis zum nächsten `#`; ein `#` ohne Attribut setzt
  ihn zurück auf den des Decks. `{uebergang="none"}` schaltet ihn für eine Folie bzw. ein
  Kapitel ab. „Forts."-Folien und alle Folien einer Überschrift (Chart-, Bild-, Flow-Folien)
  erben ihn (wie die Notizen, über `replace` in `DeckParser._section`).
- **Prüfung im gemeinsamen Teil:** der Wert wird in `heading_attributes.split` geprüft, also in
  allen Formaten mit Zeile (`Line 3: Unknown slide transition 'slide'. Valid transitions: …`);
  Word und PDF nehmen ein gültiges Attribut ohne Wirkung an (Test: `document.xml` und PDF
  byte-gleich).
- **XML** wie `Animations.Transition`: `p:transition spd="med"` mit dem Effektelement, Morph als
  `mc:AlternateContent` (`mc:Choice Requires="p159"`, `p159:morph option="byObject"`, Fallback
  `p:fade`, beide `spd="slow"`), Namensräume lokal am Element. Eingefügt sofort nach
  `p:clrMapOvr` beim Anlegen der Folie; `p:timing` kommt später ans Ende (vor `p:extLst`), die
  Reihenfolge `cSld`, `clrMapOvr`, Übergang, `timing` ist getestet.
- **Richtungen** sind die Bewegungsrichtung der Folie, wie das Attribut `dir` (`push-up` →
  `dir="u"`: die neue Folie kommt von unten und schiebt die alte nach oben). `split` schreibt
  `orient="vert" dir="out"`, `uncover` ist `p:pull`, `cover`/`uncover`/`zoom` ohne Richtung.

### Abweichungen

- Der Vorschlag nannte `parse(name, format)` als Funktion; es ist `SlideTransition.parse`
  (Klassenmethode wie `Marking.parse`). Das Front Matter nutzt `FrontMatter.one_of` wie die
  übrigen Schlüssel (Meldung „expected 'none' or 'fade' or …").
- Guide E04-S06 gibt es noch nicht; die Werte stehen in `docs/ki-anleitung.md`.

### Warnungen

- **Warnung:** `push` und `wipe` ohne Richtung schreiben `<p:push/>`/`<p:wipe/>` wie
  vt-tools-libs, also `dir="l"` (Bewegung nach links, in PowerPoint „Von rechts"). Die Notiz
  sagt „ohne Richtung wie bisher von links"; vt-tools-libs beschreibt `wipe` als „von links
  aufgedeckt", das Schema-Standard `l` bedeutet aber die Richtung der Bewegung. Gewählt wurde
  das byte-gleiche Port-Verhalten; ob PowerPoint das als „Von rechts" anzeigt, ist ungeprüft.
- **Warnung:** `uebergang` im Front Matter kennt nur PowerPoint; Word und PDF lehnen den
  Schlüssel wie `aufbau` als unbekannt ab (vorsichtige Wahl wie in E09-S02). Das
  Heading-Attribut nehmen alle Formate an.
- **Warnung:** Die Geschwindigkeit ist fest (`med`, Morph `slow`), eine Dauer ist nicht wählbar.
  Ein Front-Matter-Wert gilt auch für die Titelfolie (sie „kommt" in der Bildschirmpräsentation
  ebenfalls mit Übergang herein) — wie vt-tools-libs.
- **Warnung:** `cut` schreibt `p:cut` mit `spd="med"`; PowerPoint selbst schreibt dort womöglich
  kein `spd` (ungeprüft, das Attribut ist laut Schema erlaubt).

### Prüfpunkte

- In PowerPoint öffnen (keine Reparaturmeldung), als Bildschirmpräsentation durchklicken und
  im Register „Übergänge" prüfen: `.tmp/review/deck-transition-fade.pptx` (jede Folie
  „Verblassen"), `.tmp/review/deck-transition-chapter.pptx` (Kapitel 01 „Schieben" von unten,
  Folie „Two" „Morph", der Rest ohne), `.tmp/review/funktionen/funktionen-praesentation.pptx`
  (Kapitel „Präsentieren" überblendet, Folie „Folienübergang" schiebt nach oben, die Builds
  laufen danach wie bisher), `.tmp/review/funktionen/varianten-folien.pptx` (`uebergang: fade`
  mit `aufbau: listen`).
- Morph in PowerPoint 2019/365 als „Morphen" und in LibreOffice Impress als Überblenden;
  die Richtungen `push-*`/`wipe-*` in PowerPoint mit den Effektoptionen abgleichen.
- PowerPoint-Prüfung steht aus (kein Office auf der Entwicklungsmaschine).

### Offene Punkte

- E09-S04 (Szenen) nutzt `morph` zwischen Szenenfolien; der Übergang muss dort nur gesetzt
  werden (`Slide.transition`).
- E10-S01 (HTML-Deck) nähert die Übergänge in CSS an oder blendet (Notiz 2026-11-07).
- E04-S06 (Guide PowerPoint) nennt `uebergang` und die Werte (`slide_transition.VALID`).
