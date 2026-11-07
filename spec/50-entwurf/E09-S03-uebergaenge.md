# E09-S03 Folienübergänge

> Status: Entwurf
> Epic: [E09 Präsentieren](E09-praesentieren.md)
> Milestone: [M04 Präsentieren und Schulung](M04-praesentieren-und-schulung.md)

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

- [ ] `uebergang: fade` im Front Matter überblendet jede Folie; `{uebergang="push"}` auf `##`
      gilt nur für diese Folie, auf `#` für das Kapitel.
- [ ] `morph` läuft in PowerPoint 2019/365 als Morph und in älteren Programmen und LibreOffice als
      Überblendung; keine Reparaturmeldung.
- [ ] Ohne Angabe hat keine Folie einen Übergang (Deck wie heute).
- [ ] Ein unbekannter Wert wirft mit Zeile und den gültigen Werten; Word nimmt das Attribut ohne
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
