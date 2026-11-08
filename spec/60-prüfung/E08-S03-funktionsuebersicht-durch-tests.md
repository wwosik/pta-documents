# E08-S03 Funktionsübersicht durch Tests gesichert

> Status: in Prüfung
> Epic: [E08 Rückmeldung an den Schreiber und KI-Anbindung](../50-entwurf/E08-rueckmeldung-und-ki-anbindung.md)
> Milestone: [M02 Rückmeldung und Folien-Syntax](../50-entwurf/M02-rueckmeldung-und-folien-syntax.md)

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

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08: Test `tests/samples/test_funktionen.py` mit den
Rundreise-Erwartungen in `tests/samples/funktionen/`; `samples/funktionen/` überarbeitet und um
vier Variantendateien ergänzt; Codeblöcke in Sprechernotizen (Generator, Konverter, Statistik);
`generate-samples` kennt `-dokument`/`-folien`. Doku in `docs/verwendung.md` (Sprechernotizen,
Konverter, Statistik, Abschnitt „Beispiele" mit der Funktionsübersicht), `docs/anleitung.md`
(Abschnitt 1, Sprechernotizen), `docs/ki-anleitung.md`; `samples/funktionen/README.md`.

### Entscheidungen

- **Was gezeigt werden muss**, je Format aus dem Code gebildet (`required` im Test): jeder
  Schlüssel aus `VALID_KEYS` des Generators; `status.<kategorie>` jeder Kategorie im Front
  Matter *und* als Status-Label in einer Tabellenzelle; farbige Wörter jeder Kategorie; jede
  `vorlage:`-Variante (`WordVariant` bzw. `SlidesVariant`), jede `sprache:`; jeder Container aus
  `layout_syntax.CONTAINER_NAMES` plus die Argumentformen `::: panel dark` und `::: columns`
  mit Breiten; jeder Alert aus `ALERT_KINDS`; `==Markierung==`. Nur für PowerPoint: jedes
  Heading-Attribut aus `heading_attributes.VALID` (auch `.agenda`, `.interim`, `.quote`,
  `.contact`) und jede `titelfolie:` aus `TITLE_SLIDES`. Gesucht wird auf den Token des
  gemeinsamen Parsers, nicht per Regex im Text — Quelltext-Zäune zählen damit nicht als
  Beispiel. Ein Eintrag von `VALID`, den der Test nicht kennt, gilt als fehlend und wird genannt.
- Word muss `::: notes` nicht zeigen (es lässt Notizen mit `notes-dropped` weg, die Beispiele
  erzeugen aber ohne Hinweise) und keine Heading-Attribute (sie sind Folien-Syntax und entfallen
  in Word).
- **Quelle neben Ergebnis:** Der Bericht hat unter jeder `##`-Überschrift einen Satz, einen Zaun
  `markdown` und denselben Text als Ergebnis; der Test prüft, dass jede `##`-Funktion einen
  solchen Zaun hat und sein Inhalt außerhalb des Zauns wortgleich steht (beim Front Matter: am
  Dateianfang). Die Präsentation hat den Quelltext jeder `##`-Folie als Zaun in einem
  `:::: notes` am Ende der Folie (vier Doppelpunkte, damit `:::`-Zeilen im Quelltext den Block
  nicht schließen; bei `::::` im Quelltext fünf); gleiche Prüfung.
- **Codeblöcke in Sprechernotizen:** E09-S01 ließ sie weg; damit der Quelltext auf die
  Notizenseite kommt, schreibt `DeckParser._note_blocks` einen Zaun jetzt Zeile für Zeile als
  Absätze in Consolas (ohne Hervorhebung). Der PPTX-Konverter liest aufeinanderfolgende Absätze
  ganz in Consolas als Zaun ohne Sprache zurück und verlängert den Notizzaun über jede
  `:::`-Zeile darin; `check` zählt Absätze ganz aus Code nicht zu den gesprochenen Wörtern.
- **Varianten:** „eine Datei je Format und Variante" — neu `varianten-hochformat-dokument.md`
  (`hoch-ohne-deckblatt`, dazu `inhaltsverzeichnis`, `typografie`, `syntaxhervorhebung` auf
  `nein`), `varianten-querformat-dokument.md` (`quer`), `varianten-bild-01-folien.md`,
  `varianten-branchen-folien.md`. Die bestehenden Namen `varianten-dokument.md` und
  `varianten-folien.md` bleiben, weil andere Pläne (E09-S03, E12-S03) sie nennen.
- Neue Inhalte der Präsentation: Flow-Folien (alle Container, `.dark`, `kicker`, Alerts,
  Markierung, farbige Wörter, Status-Labels) und die PTA-Folienarten; der Bericht zeigt die
  Folien-Syntax in Word (Container außer `notes`, Alerts, Markierung, farbige Wörter,
  Status-Labels, markierte Zeile) und zusätzlich die Bildreihe.
- Formatwahl und Bilder wie `tools/generate` (Modul per `importlib`, `target_format`,
  `resources`); jede Datei muss einen Namen mit bekanntem Suffix haben und in der Tabelle der
  `README.md` stehen; verwaiste Erwartungsdateien lassen einen Test fehlschlagen.
- Neue Variantendateien tragen ein `datum`, damit nichts vom Tag der Erzeugung abhängt.
- Offene Frage 1 (erzeugte Dateien committen): nein, wie beantwortet.

### Abweichungen

- **Warnung:** Der Test lässt *keine* Hinweise zu, statt im `README.md` genannte Ausnahmen
  einzulesen — die `README.md` sagt „Alle Dateien erzeugen ohne Hinweise", eine Ausnahmeliste
  gibt es heute nicht. Braucht eine spätere Story eine absichtliche Fortsetzungsfolie, muss sie
  den Test um eine solche Liste erweitern.
- **Warnung:** Die Präsentation bekommt den Quelltext nicht „bis dahin als Codefolie davor",
  sondern gleich in die Notizen, weil E09-S01 schon umgesetzt ist; dafür wurden Codeblöcke in
  Notizen erst möglich gemacht (siehe Entscheidungen) — das ändert das Verhalten von E09-S01
  (bisher: Codeblöcke in Notizen entfallen).
- **Warnung:** Die Namen der 35 PTA-Layouts (`layout="…"`) werden nicht einzeln verlangt; der
  Plan nennt sie nicht, und ein Beispiel je Layout wäre eine eigene Präsentation. Verlangt wird
  `layout="…"` überhaupt.
- Der Test liegt wie im Plan in `tests/samples/` (kein Spiegel von `src/`, weil er die
  Beispiele prüft, nicht ein Modul).
- `generate-samples` erzeugte bisher nur `-bericht`/`-praesentation`; die Variantendateien fehlten
  dort stillschweigend. Jetzt dieselben Suffixe wie `generate`.

### Prüfpunkte

- `.tmp/review/funktionen/` bzw. `.tmp/samples/funktionen/` in Word und PowerPoint öffnen
  (auf der Entwicklungsmaschine gibt es kein Office): Wirkt der Bericht mit Quelltext und
  Ergebnis als Nachschlagewerk? Sind die Notizenseiten mit Consolas-Zeilen lesbar (lange
  Quelltexte wie bei „Viel Text wird verkleinert" können den Notizenplatzhalter überlaufen)?
- Kontaktfolie ohne Foto, Zwischenfazit- und Zitatfolie in der Funktionsübersicht ansehen.
- Rundreise-Erwartungen durchsehen: Der DOCX-Konverter verliert Inline-Code-Backticks (bestehendes
  Verhalten), Codeblöcke aus Notizen kommen ohne Sprache zurück.

### Offene Punkte

- Sobald die Authoring Guides da sind (E02-S05, E03-S05, E04-S06), soll der Test die verlangte
  Syntax aus den Guides lesen (Regex wie vt-tools-libs) statt aus den Code-Listen.
- Charts, Mermaid, SVG-Bilder und PDF ergänzen die Stories, die sie bringen (E06, E05); jede
  spätere Story mit neuer Syntax muss ihr Beispiel in `samples/funktionen/` ergänzen, sonst
  schlägt der Test fehl.
- Vorschau als Bilder (E10-S02) für die Funktionsübersicht.
