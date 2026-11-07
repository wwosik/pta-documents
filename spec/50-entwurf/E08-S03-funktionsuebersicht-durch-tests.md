# E08-S03 Funktionsübersicht durch Tests gesichert

> Status: Entwurf
> Epic: [E08 Rückmeldung an den Schreiber und KI-Anbindung](E08-rueckmeldung-und-ki-anbindung.md)
> Milestone: [M02 Rückmeldung und Folien-Syntax](M02-rueckmeldung-und-folien-syntax.md)

## Zusammenfassung

`samples/funktionen/` wird zur Feature-Tour, die Tests aktuell halten: jede Syntax, jeder
Front-Matter-Schlüssel und jedes Layout, das die Authoring Guides nennen, kommt in den Beispielen
vor; die Beispiele erzeugen ohne Hinweise; ihre Rundreise-Ergebnisse sind als
`*.expected.md` committet, und ein Blick in `.tmp/review/` zeigt die Dokumente.

## Kontext

- vt-tools-libs: `docs/tour.md` → `docs/tour.html` (committet), `Tools.Tests/TourTests.cs` (132
  Zeilen): die Tour wird in allen Formaten erzeugt, das HTML mit dem committeten verglichen
  (`VTTOOLS_UPDATE_EXPECTED=1`), sie braucht keine Hinweise, und ein Regex über den kombinierten
  Guide sammelt jede Syntax (`::: name`, `{.class}`, `key="…"`, `[!ALERT]`, Front-Matter-Schlüssel)
  und prüft, dass sie in `tour.md` vorkommt.
- Hier: `samples/funktionen/` (vier Markdowns, `README.md` mit Tabelle, was jede Datei zeigt;
  Commit 4f18fb9) wird von `./run.sh generate samples/funktionen --out documents/funktionen`
  erzeugt — von Hand, ohne Test. `documents/` ist git-ignoriert; ein HTML als sichtbares Ergebnis
  gibt es ohne E10 nicht. `tests/expected.py` kennt `PTA_DOCUMENTS_UPDATE_EXPECTED=1`.
- Die Authoring Guides (E02-S05, E03-S05, E04-S06) sind noch nicht umgesetzt; bis dahin dienen die
  Listen gültiger Schlüssel (`VALID_KEYS`), Heading-Attribute (`VALID`) und Container
  (`CONTAINERS`, E02-S02) als Quelle dessen, was gezeigt werden muss.

## Vorgeschlagener Ansatz

1. **Tests** `tests/samples/test_funktionen.py`:
   - jede Datei in `samples/funktionen/` wird für ihr Format erzeugt (Formatwahl wie
     `tools/generate`), ohne `DocumentConversionError` und ohne Hinweise (E08-S01) — außer den im
     `README.md` der Beispiele ausdrücklich genannten (die Fortsetzungsfolie ist Absicht);
   - Rundreise: zurückgelesen mit dem Konverter und verglichen mit
     `tests/samples/funktionen/<datei>.roundtrip.expected.md`;
   - die Dokumente werden nach `.tmp/review/funktionen/` geschrieben;
   - **Vollständigkeit:** aus `VALID_KEYS` beider Generatoren, `heading_attributes.VALID`,
     `layout_syntax.CONTAINERS`/`ALERTS` (E02-S02) und den Vorlagen-Variantennamen wird die Menge
     dessen gebildet, was vorkommen muss; der Test sucht jedes Element in den Beispieltexten
     (`vorlage:` mit jedem Wert, `::: cards`, `{.dark}`, `[!NOTE]`, `==…==` …) und nennt, was
     fehlt. Sobald ein Guide da ist (E02-S05), liest er stattdessen dessen Syntax mit demselben
     Regex wie vt-tools-libs, damit Guide, Beispiele und Code nicht auseinanderlaufen.
2. **Struktur der Beispiele** bleibt: eine Datei je Format und Variante; neue Funktionen kommen in
   die passende Datei, die `README.md`-Tabelle wächst mit (der Test prüft, dass jede Datei in der
   Tabelle steht).
3. **Quelle neben Ergebnis:** jede Funktion steht im Bericht als Überschrift, kurzer Satz, der
   Markdown-Quelltext als Codeblock und darunter das Ergebnis — so zeigt das Word-Dokument selbst
   die Tour, wie `tour.html` bei vt-tools-libs. In der Präsentation je Funktion eine Folie mit dem
   Quelltext im Notizenbereich (E09-S01), bis dahin als Codefolie davor.
4. **`generate-samples`** erzeugt weiterhin alle Beispiele für den Anwender; `anleitung.md`
   verweist auf `samples/funktionen/` als Nachschlagewerk und auf `.tmp/review/` nach `./run.sh
   test`.
5. **Vorschau** (E10-S02) rendert später die Funktionen-Präsentation zu PNGs — dann ist die Tour
   ohne Office sichtbar.

## Akzeptanzkriterien

- [ ] Eine neue gültige Syntax, ein neuer Schlüssel oder eine neue Variante ohne Beispiel in
      `samples/funktionen/` lässt einen Test fehlschlagen und nennt das Fehlende.
- [ ] Die Beispiele erzeugen ohne Hinweise außer den im `README.md` genannten.
- [ ] Rundreise-Erwartungen liegen unter `tests/samples/funktionen/` und werden mit
      `PTA_DOCUMENTS_UPDATE_EXPECTED=1` erneuert.
- [ ] Der Word-Bericht zeigt zu jeder Funktion Quelltext und Ergebnis.

## Offene Fragen

1. Sollen die erzeugten `.docx`/`.pptx` der Funktionsübersicht committet werden (Binärdateien,
   ändern sich bei jeder Änderung), damit Anwender sie ohne Erzeugen öffnen können? Vorschlag:
   nein — `./run.sh generate samples/funktionen` dauert Sekunden.

> (2026-11-07) Nein.

## Notizen

- Diese Story ergänzt die Guide-Tests aus E02-S05 (Guide ↔ Code) um die dritte Seite (Guide ↔
  Beispiele).
- (2026-11-07, E08-S01) `samples/funktionen/` erzeugt bereits ohne Hinweise; dafür wurden die
  Demo-Folien „(Forts.)" und „geteilte Tabelle" entfernt und Bilder `*-folie.png` in Platzhalter-
  Proportionen ergänzt. Tests: `test_the_samples_generate_without_notes` in
  `tests/generation/{docx,pptx}/test_notes.py`.
