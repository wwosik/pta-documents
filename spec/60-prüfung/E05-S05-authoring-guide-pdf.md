# E05-S05 Authoring Guide PDF

> Status: in Prüfung
> Epic: [E05 PDF-Generator im PTA-Design](../50-entwurf/E05-pdf-generator.md)
> Milestone: [M05 PDF](../50-entwurf/M05-pdf.md)

## Zusammenfassung

Eine Anleitung für Schreiber von Markdown (oft KI-Agenten), wie aus ihrem Text ein PTA-PDF wird:
Gliederung, Front Matter, Tabellen, Bilder, Folien-Syntax, Diagramme, Zeichen, die die Schriften
nicht haben, und Fehler. Sie wird aus den Optionen erzeugt, damit sie nie vom Generator abweicht.

## Kontext

- DocLibs: `PdfGenerator.AuthoringGuide(options)` mit der Vorlage `AuthoringGuide/Pdf.md`
  (englisch, Platzhalter `{{diagrams}}`, `{{frontMatter}}`, `{{characters}}`), den gemeinsamen
  Bausteinen in `AuthoringGuides.cs` (`Fill`, `FrontMatter`, `Characters`, `Symbols`, `Words`)
  und den Tests `AuthoringGuideTests.cs` (7 Fälle) mit `authoring-guide-*.expected.md`.
- Die gemeinsamen Bausteine portiert E02-S05; die Diagramm- und Chart-Abschnitte liefern die
  Renderer (E06). Was DocLibs beschreibt, gilt für die PTA nur teilweise: Deckblatt aus dem
  Front Matter statt aus dem ersten `#`, `#` ist „Überschrift 1" ohne Seitenwechsel, kein
  `template`, `pageSize`, `orientation`, `showDate`, `showTagline`.
- Standards: Was ein Schreiber liest, ist deutsch.

## Vorgeschlagener Ansatz

1. Vorlage `src/pta_documents/generation/pdf/authoring_guide.md` (Paketdaten, über
   `importlib.resources`), deutsch, ab `##`, damit ein Aufrufer sie unter eine eigene Überschrift
   setzen kann. Abschnitte nach DocLibs `Pdf.md`, inhaltlich für die PTA:
   - **Gliederung**: Deckblatt aus `titel`, `untertitel`, `autor`, `ort`, `datum` (Varianten mit
     Deckblatt); `#`–`###` nummerierte Überschriften, tiefere Zwischenüberschriften; Absatz
     `**…**` als hervorgehobener Absatz bzw. Tabellentitel; `Tabelle: …` nach einer Tabelle;
     „Abbildung n" aus Titel oder Alt-Text; Listen, Zitate, Code, Links (absolut oder `#anker`),
     Fußnoten.
   - **Tabellen und Bilder**: volle Satzspiegelbreite, wiederholter Kopf, höchstens etwa sechs
     Spalten (Hoch) bzw. neun (Quer); Bilder nur aus den Ressourcen, `"scale=0.5"`, Bildreihen.
   - **Folien-Syntax**: Container, Alerts, `==mark==`, `[Wörter]{.success}`, Heading-Attribute —
     wie sie im PDF erscheinen (E05-S04).
   - `{{diagrams}}`: die Abschnitte der registrierten Code-Block-Renderer.
   - `{{frontMatter}}`: Tabelle der gültigen Schlüssel aus `VALID_KEYS` mit Werten und Standard —
     `vorlage` nennt alle `WordVariant`-Werte und als Standard `options.variant`.
   - `{{characters}}`: die `Symbols`, die Text- oder Codeschrift nicht haben, mit Ersatz; der Satz
     davor hängt davon ab, ob `replace_unsupported` gesetzt ist (Fehler oder Ersatz).
   - **Fehler** und ein **Beispiel** (Statusbericht mit Front Matter, Tabelle mit Beschriftung,
     Alert, nummerierter Liste).
2. `PdfGenerator.authoring_guide(options: PdfOptions | None = None) -> str` füllt die Vorlage mit
   `fill()` aus E02-S05; Ergebnis endet mit genau einem Zeilenumbruch.
3. Schriften für den Zeichenabschnitt kommen aus derselben Quelle wie beim Erzeugen (E01-S03).
   Tests erzwingen Selawik, damit die Erwartungsdatei nicht davon abhängt, ob Segoe UI auf dem
   Rechner liegt.
4. Tests `tests/generation/pdf/test_authoring_guide.py`, aus DocLibs übernommen: jedes
   `markdown`-Beispiel erzeugt ein PDF; unter 2 500 Wörtern; jeder Container, jeder Alert und
   jeder Front-Matter-Schlüssel kommt vor; der Standard von `vorlage` folgt den Optionen; der
   Zeichenabschnitt folgt Schrift und Hook; jeder Ersatz steht in jeder Schrift; Vergleich mit
   `authoring-guide.expected.md` (`PTA_DOCUMENTS_UPDATE_EXPECTED=1`).
5. `docs/verwendung.md` bekommt einen Abschnitt „Markdown → PDF" mit Aufruf und Verweis auf die
   Anleitung.

## Akzeptanzkriterien

- [x] `PdfGenerator.authoring_guide()` liefert deutsches Markdown ab `##`, das alle Schlüssel,
      Container und Alerts nennt, die der Generator annimmt.
- [x] Jedes Beispiel der Anleitung erzeugt fehlerfrei ein PDF.
- [x] Die Anleitung bleibt unter 2 500 Wörtern und gleicht `authoring-guide.expected.md`.
- [x] Der Zeichenabschnitt nennt genau die Symbole, die den eingesetzten Schriften fehlen, mit
      einem Ersatz, den alle Schriften haben.

## Offene Fragen

1. DOCX und PDF nehmen dasselbe Markdown und dasselbe Front Matter an. Soll es **eine** gemeinsame
   Anleitung „Dokumente" geben (mit einem kurzen Abschnitt zu den Unterschieden: Felder, die Word
   beim Öffnen aktualisiert, fehlende Zeichen im PDF), statt getrennter Anleitungen in E03-S05 und
   hier? Vorschlag: gemeinsam.

> (2026-11-07) Gemeinsam — eine Anleitung „Dokumente“ für Word und PDF; E03-S05 schreibt sie, E05-S05 ergänzt den PDF-Abschnitt.

2. Wird zusätzlich eine englische Fassung gebraucht (z. B. für `sprache: en` oder für Agenten),
   oder genügt die deutsche?

> (2026-11-07) Nein, nur Deutsch (wie E02-S05).

## Notizen

- Abhängig von E02-S05 (Bausteine), E05-S02 bis E05-S04 (was beschrieben wird); Renderer-
  Abschnitte aus E06, sobald es sie gibt.
- (2026-11-08, E02-S05) Die Vorlage liegt nach dem gemeinsamen Muster in
  `generation/pdf/authoring_guide/<name>.md` (`authoring_guides.template`), nicht in
  `generation/pdf/authoring_guide.md`. `characters_section(text, code, intro)` nimmt
  Code-Point-Funktionen (`lambda c: fonts.has_glyph(c, face)`); `SYMBOLS` ist portiert (`↑`/`↓`
  mit `hoch`/`runter` statt `up`/`down`).
- (2026-11-08, E03-S05) Der gemeinsame Guide „Dokumente“ ist der Word-Guide
  (`generation/docx/guide.py`, Vorlage `generation/docx/authoring_guide/docx.md`); er hat mit
  allen Renderern rund 2 460 Wörter. Ein PDF-Abschnitt (Felder, fehlende Zeichen) passt nur, wenn
  anderswo gekürzt wird — oder der PDF-Guide nimmt die Word-Vorlage mit eigenem Platzhalter und
  lässt Word-Eigenes (Inhaltsverzeichnis „Word füllt es beim Öffnen“) weg.

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08 im Haupt-Checkout (parallel setzt ein anderer Lauf desselben
Agents E04-S06 in einem Worktree um; gemeinsame Dateien hier nur `authoring_guides.py`
(`characters_section`, nur vom PDF benutzt), `docs/verwendung.md`, `docs/ki-anleitung.md` und
`ai/Gedächtnis.md`, dort nur ergänzt bzw. PDF-Zeilen geändert).

Neu: `src/pta_documents/generation/common/document_guide.py` (der Guide „Dokumente“:
`FormatTexts`, `DocumentOptions`, `VARIANT_TEXTS`, `variants_paragraph`, `front_matter_rows`,
`authoring_guide`), `src/pta_documents/generation/pdf/guide.py` (`TEXTS` des PDFs über
`texts(options)`, `EFFECT`, `NATIVE_IMAGES`, `characters`, `characters_intro`),
`PdfGenerator.authoring_guide(options)` in `generation/pdf/generator.py`,
`layout.fonts.shows` (die Regel „Zeichen vorhanden“, jetzt auch von `generate` benutzt). Die
Vorlage `generation/docx/authoring_guide/docx.md` ist nach
`generation/common/authoring_guide/documents.md` gezogen und hat Platzhalter für die
Format-Teile (`heading`, `target`, `footnote`, `links`, `characters`, `imageError`);
`generation/docx/guide.py` liefert nur noch Words `TEXTS` und ruft den gemeinsamen Aufbau — der
Word-Guide ist byte-gleich geblieben (`authoring-guide.expected.md` von E03-S05 unverändert).
Tests: `tests/generation/pdf/test_authoring_guide.py` (21 Fälle) mit der Erwartung
`tests/generation/pdf/samples/authoring-guide.expected.md`, ein Fall in
`tests/generation/pdf/layout/test_layout.py` (×16 Abstände), die Zeichen-Tests in
`tests/generation/common/test_authoring_guides.py` auf das neue Tabellenformat. Doku:
`docs/verwendung.md` (*Markdown → PDF*, *Authoring Guides*), `docs/ki-anleitung.md` (Verweis im
Abschnitt *Word-Bericht*), `ai/Gedächtnis.md` (PDF-Guide, Word-Guide, Authoring Guides — dort
auch die veraltete Zeile zu `guide_syntax` —, Layout-Engine).

### Entscheidungen

- **Ein Guide „Dokumente“ aus einer Vorlage** (Antwort auf Frage 1): Word und PDF füllen dieselbe
  Vorlage; jedes Format liefert nur, was bei ihm anders ist (`FormatTexts`). Der PDF-Guide ist
  damit der Word-Guide mit der Überschrift *Ein PTA-PDF aus Markdown*, der Spalte „Im PDF“,
  „Fußnote am Seitenende“, Links auch auf `#anker`, „Inhaltsverzeichnis mit Seitenzahlen“ (statt
  „Word füllt es beim Öffnen“), Bildformaten mit WebP, der eigenen Wirkung der Folien-Syntax
  (`::: scene` als Grafik, darum auch in der Container-Tabelle), der PDF-Meldung zum Bildformat,
  den Hinweis-Codes des PDFs und dem Abschnitt *Zeichen* nach *Typografie und Code*.
- **Zeichen aus denselben Schriften wie beim Erzeugen:** `design.fonts.resolve(system_fonts)`
  und `layout.fonts.shows` (Text: Regular und Bold, Code: Mono, Aliase zählen) — der Generator
  nimmt für `character-missing` jetzt dieselbe Funktion. Der Satz vor der Tabelle folgt
  `replace_unsupported`: `?` (Standard), „wird ersetzt“ (eigener Ersatz) oder Fehler (`None`).
  Erwartung und Tests mit `system_fonts=False` (Selawik, Inconsolata).
- **Symbole je Ersatz gruppiert** (`characters_section`): `| ✓ ✔ ☑ | [x] |` statt einer Zeile je
  Symbol mit „(in Code möglich)“; darunter ein Satz „In Code gehen: …“ (bzw. „Nur im Text
  gehen: …“). Symbole zählen nicht als Wörter, die Bemerkungen schon — so passt der Abschnitt ins
  Budget (77 → rund 45 Wörter).
- Was der PDF-Guide an Syntax nennt, muss der Word-Guide auch nennen (außer `{uebergang` aus der
  Szenenzeile); so bleibt die Kette Guide ↔ Beispiele aus `test_funktionen.py` auch für das PDF
  geschlossen, das keine eigenen Beispiele hat. `tests/samples/test_funktionen.py` bleibt
  unverändert (dort arbeitet E04-S06).
- Die Fehlerbeispiele sind echt: ein Test erzeugt jedes mit dem PDF-Generator und findet die
  Meldung im Guide; ein Test prüft, dass `[Lage](#lage)` wie im Guide ein interner Link wird.

### Abweichungen

- **Warnung (Abweichung von der Antwort auf Frage 1):** Die Antwort sah vor, dass E05-S05 dem
  Word-Guide einen PDF-Abschnitt anfügt. Der Word-Guide hat mit allen Renderern 2 464 von 2 500
  Wörtern; ein PDF-Abschnitt (Zeichen, Unterschiede) hätte Kürzungen an geprüftem Word-Text
  verlangt, und ein Word-Schreiber hätte PDF-Eigenes lesen müssen. Vorsichtigere Wahl: **eine
  Vorlage, zwei Ausgaben** — der Text ist gemeinsam (eine Stelle zum Pflegen), jeder Generator
  gibt die Fassung seines Formats aus, der Word-Guide bleibt Wort für Wort, wie er war. Soll es
  doch ein einziger Text für beide sein, ginge das über einen Abschnitt „Als PDF“ in der Vorlage
  und Kürzungen anderswo.
- **Warnung:** Die Vorlage liegt jetzt in `generation/common/authoring_guide/documents.md`, nicht
  mehr in `generation/docx/authoring_guide/docx.md` (E03-S05) und nicht in
  `generation/pdf/authoring_guide/pdf.md` (Notiz E02-S05): ein gemeinsamer Text gehört nach
  `common`.
- **Fehler der Layout-Engine behoben** (E05-S02, gleicher Agent): eine Überschrift direkt vor
  einem Bild mit Titel (Bild und Beschriftung als `KeepTogether`) brach das PDF mit
  `AttributeError: 'KeepTogether' object has no attribute 'canv'` ab — das Berichtsbeispiel des
  Guides (`# Nächste Schritte` + Bild) fiel darüber. `flowables.start_height` misst ein
  `KeepTogether` jetzt Teil für Teil (dessen eigenes `wrap` braucht den Canvas und antwortet mit
  „teilen“). Neuer Test `test_a_heading_stays_with_its_figure_and_caption`.
- Kein neuer Abschnitt „Markdown → PDF“ in `docs/verwendung.md`: den gibt es seit E05-S01; er
  bekommt einen Absatz mit Aufruf und Verweis.
- `docs/verwendung.md` beschreibt `layout.fonts.shows` nicht eigens (interne Hilfe).

### Warnungen

- **Wortbudget knapp:** mit allen Renderern 2 484 von 2 500 Wörtern (Standardoptionen hier
  dasselbe). Dafür ist `EFFECT` des PDFs kürzer als der Word-Satz und der Zeichenabschnitt
  gruppiert. Jede neue Zeile in der gemeinsamen Vorlage zählt in beiden Guides.
- Die **Renderer-Abschnitte** (Charts, Finanzdiagramme, Mermaid, E06) sprechen von „Folien“ und
  „Word“, nicht vom PDF (dort Vektorgrafik). Sie zu ergänzen hieße Renderer-Texte aller Guides
  ändern und Wörter finden; nicht hier.
- Der Zeichenabschnitt hängt von den Schriften des Rechners ab: `./run.sh authoring-guide pdf`
  nimmt Segoe UI/Consolas, wenn installiert, und nennt dann andere (meist weniger) Symbole als
  die Erwartungsdatei. Gewollt — er nennt, was beim Erzeugen auf diesem Rechner fehlt.
- Mermaid-Beispiel nur mit `.tmp/mm/env.sh` als PDF geprüft (dort grün); ohne mermaid-cli lässt
  der Test es aus.

### Prüfpunkte

- `./run.sh authoring-guide pdf` bzw. `tests/generation/pdf/samples/authoring-guide.expected.md`
  lesen, neben `tests/generation/docx/samples/authoring-guide.expected.md` (Diff zeigt genau die
  Format-Teile).
- Die Texte in `generation/pdf/guide.py` (`EFFECT`, Zeichen-Sätze) und die gruppierte
  Zeichentabelle.
- Ob „eine Vorlage, zwei Ausgaben“ der gemeinte gemeinsame Guide ist (siehe Warnung oben).

### Offene Punkte

- Renderer-Abschnitte mit PDF-Wirkung (siehe Warnungen), zusammen mit kürzeren Renderer-Texten
  (Offener Punkt aus E03-S05) in einer eigenen Story.
- M05 ist damit vollständig in `spec/60-prüfung/`; der Meilensteinkopf bleibt `Entwurf` wie bei
  M02/M03.
