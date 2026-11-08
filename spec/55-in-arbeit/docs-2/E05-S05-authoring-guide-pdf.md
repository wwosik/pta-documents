# E05-S05 Authoring Guide PDF

> Status: in Bearbeitung (docs-2)
> Epic: [E05 PDF-Generator im PTA-Design](../../50-entwurf/E05-pdf-generator.md)
> Milestone: [M05 PDF](../../50-entwurf/M05-pdf.md)

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

- [ ] `PdfGenerator.authoring_guide()` liefert deutsches Markdown ab `##`, das alle Schlüssel,
      Container und Alerts nennt, die der Generator annimmt.
- [ ] Jedes Beispiel der Anleitung erzeugt fehlerfrei ein PDF.
- [ ] Die Anleitung bleibt unter 2 500 Wörtern und gleicht `authoring-guide.expected.md`.
- [ ] Der Zeichenabschnitt nennt genau die Symbole, die den eingesetzten Schriften fehlen, mit
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
