# E03-S05 Authoring Guide DOCX

> Status: in Prüfung
> Epic: [E03 DOCX-Generator auf den PTA-Word-Vorlagen](../50-entwurf/E03-docx-generator.md)
> Milestone: [M04 Präsentieren und Schulung](../50-entwurf/M04-praesentieren-und-schulung.md)

## Zusammenfassung

`DocxGenerator.authoring_guide(options)` liefert die deutsche Anleitung für Schreiber eines
PTA-Word-Dokuments in Markdown — welche Blöcke welche PTA-Formatvorlage ergeben, welches Front
Matter gilt, was Folien-Syntax in Word bewirkt — erzeugt aus denselben Optionen wie `generate`.

## Kontext

- DocLibs hat keinen DOCX-Generator; Vorbild sind `Pdf/AuthoringGuide/Pdf.md` (87 Zeilen) und
  `PdfGenerator.AuthoringGuide` samt `AuthoringGuideTests` (Beispiele generieren, < 2 500 Wörter,
  nennt alle Schlüssel, Abgleich mit `*.expected.md`).
- Bausteine aus E02-S05 (`authoring_guides.fill`, `front_matter_section`,
  `layout_syntax_section`, `renderers_section`); die Zuordnung Markdown → Formatvorlage steht in
  E03-S02, die Folien-Syntax in Word in E03-S03, Diagramme in E03-S04; die heutige Fassung für
  Menschen in `docs/verwendung.md`.
- Ein Abschnitt „Zeichen" entfällt: Word nimmt die installierte Segoe UI.

## Vorgeschlagener Ansatz

1. Vorlage `src/pta_documents/generation/docx/authoring_guide/docx.md` (deutsch, ab `##`), mit
   den Abschnitten:
   - **Ein PTA-Word-Dokument aus Markdown** — Inhalt schreiben, nicht formatieren; das Design
     kommt aus der Vorlage.
   - **Gliederung** — `#`–`###` sind „Überschrift 1–3" mit Nummern `1`, `1.1`, `1.1.1`; tiefere
     Ebenen „Zwischenüberschrift"; der Titel kommt aus `titel`, nie aus `#`.
   - **Inhalte** — Tabelle der Zuordnungen aus E03-S02 (Absatz, `**fett**`-Absatz, Listen,
     Tabellen mit `**Titel**` davor und `Tabelle: …` danach, Bilder mit Titel → „Abbildung n",
     Code, Zitat, Fußnoten, Links nur absolut).
   - **Folien-Syntax in Word** — `layout_syntax_section` plus die Word-Wirkung aus E03-S03
     (Container schlicht, Alerts als Hinweis, `==…==` gelb, farbige Wörter, Status-Labels,
     Bildreihen).
   - `{{diagrams}}` (Renderer-Abschnitte), `{{frontMatter}}`.
   - **Wenn etwas falsch ist** — Liste der Fehler mit Beispielen (`titel` fehlt bei Deckblatt,
     unbekannter Container, Bild nicht unter den Dateien, Bildformat ohne Konverter).
   - **Beispiel** — ein vollständiger kurzer Bericht mit Front Matter, zwei Kapiteln, Tabelle mit
     Titel und Beschriftung, Bild, Hinweis.
2. `DocxGenerator.authoring_guide(options: DocxOptions | None = None) -> str` in
   `generation/docx/generator.py`. Die Front-Matter-Tabelle entsteht aus `VALID_KEYS` des
   Generators mit Werten aus `WordVariant`, `Language` und den Standardwerten der Optionen
   (`vorlage` Standard `hoch` bzw. was die Optionen setzen).
3. Text zu Vorlagen: je Variante ein Satz (Hoch-/Querformat, mit/ohne Deckblatt; ohne Deckblatt
   stehen Titel und Untertitel in der Kopfzeile).
4. Tests in `tests/generation/docx/test_authoring_guide.py` mit den Hilfen aus E02-S05: jedes
   ```` ```markdown ````-Beispiel generiert in allen vier Varianten fehlerfrei; < 2 500 Wörter;
   nennt jeden gültigen Front-Matter-Schlüssel, jeden Container und jedes Alert; mit einem
   Test-Renderer erscheint dessen Abschnitt, ohne nicht; Abgleich mit
   `tests/generation/docx/samples/authoring-guide.expected.md`.
5. `./run.sh authoring-guide docx` (Werkzeug aus E02-S05) gibt ihn aus; `docs/verwendung.md`
   verweist darauf.

## Akzeptanzkriterien

- [x] `DocxGenerator.authoring_guide()` liefert einen deutschen Guide ab `##` mit allen
      Abschnitten oben.
- [x] Jedes Beispiel im Guide generiert ohne Fehler; der Guide bleibt unter 2 500 Wörtern.
- [x] Ändert sich die Liste gültiger Schlüssel oder der Folien-Syntax, schlägt ein Test fehl, bis
      der Guide sie nennt.

## Offene Fragen

Keine.

## Notizen

- Abhängigkeiten: E02-S05; die Abschnitte zu Folien-Syntax und Diagrammen erst nach E03-S03 und
  E03-S04 vollständig — bis dahin beschreibt der Guide nur, was schon geht.
- (2026-11-08, E02-S05) Bausteine stehen in `generation/common/authoring_guides.py`, Testhilfen
  in `tests/generation/guides.py`, Beispiel eines Guides aus Vorlage und Bausteinen in
  `tests/generation/common/test_authoring_guides.py` (`example_guide`). `common_keys()` liefert
  die Zeilen für `datum`, `sprache`, `typografie`, `syntaxhervorhebung`, `pruefung`, `fassung`.
  `tests/samples/test_funktionen.guide_syntax` auf `DocxGenerator().authoring_guide()`
  umstellen (ohne „Wenn etwas falsch ist"). PTA-Folienarten nennt `layout_syntax_section(DOCX)`
  nur als bloße Namen, weil der Word-Bericht sie nicht zeigt — Beispiele ergänzen und in
  `DOCUMENT_ATTRIBUTES` aufnehmen, wenn der Guide sie beschreiben soll. Die Icon-Liste aus
  `docs/ki-anleitung.md` kann dann auf den Guide verweisen (`icons_section`; Test in
  `tests/design/icons/test_icons.py` mitziehen).

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08: `DocxGenerator.authoring_guide(options)` in
`src/pta_documents/generation/docx/generator.py`, der Aufbau in
`src/pta_documents/generation/docx/guide.py`, Vorlage
`src/pta_documents/generation/docx/authoring_guide/docx.md`; Tests
`tests/generation/docx/test_authoring_guide.py` mit Erwartung
`tests/generation/docx/samples/authoring-guide.expected.md`; `guide_syntax` in
`tests/samples/test_funktionen.py` liest für Word jetzt den ganzen Guide. Doku:
`docs/verwendung.md` (Markdown → Word, Authoring Guides, Beispiele), `docs/ki-anleitung.md`
(Verweis im Abschnitt *Word-Bericht*), `ai/Gedächtnis.md`; Notiz in E05-S05.

### Entscheidungen

- **Abschnitte** wie geplant: *Ein PTA-Word-Dokument aus Markdown* (mit je einem Satz je Vorlage
  aus `guide.VARIANT_TEXTS`, Standard aus `options.variant`), *Gliederung*, *Inhalte* (Tabelle
  Markdown → Word: Absätze, fett, Zeichenformate, Listen samt Aufgaben und Definitionen, Tabellen
  mit Titel und Beschriftung, Harvey Balls, Abbildungen, Bildreihe, QR, Bildstile `{.round}`,
  `{.grey}`, `{scale=…}`, Code, Zitat, Trennlinie, Fußnoten, Links; die Bildformate aus
  `image_formats` mit den Konvertern der Optionen), *Folien-Syntax* (`layout_syntax_section` mit
  der Word-Wirkung aus E03-S03/E15-S01/E15-S02), *Icons*, *Typografie und Code*, die Abschnitte
  der Renderer (`{{diagrams}}`), *Front Matter*, *Wenn etwas falsch ist*, *Beispiel*. Zeitstrahl,
  Gantt, Schrittfolge, Risikomatrix, Fassungen und Anhang stehen über die gemeinsamen Tabellen
  (`CONTAINER_TEXTS`, `ATTRIBUTE_TEXTS`) im Guide; Kennzeichnung/Wasserzeichen und
  Inhaltsverzeichnis in der Front-Matter-Tabelle.
- **Standardwerte aus den Optionen:** `vorlage`, `inhaltsverzeichnis`, `kennzeichnung`,
  `sprache`, `typografie`, `syntaxhervorhebung` und `fassung` zeigen „(Standard)“ dort, wo die
  übergebenen `DocxOptions` stehen; die Zeilen der gemeinsamen Schlüssel kommen aus
  `common_keys()` und werden nur in ihren Werten ersetzt (`dataclasses.replace`), die
  gemeinsamen Bausteine bleiben unverändert.
- **Hinweise unter den Fehlern:** `notes_section(DOCX)` steht als `### Hinweise` unter *Wenn etwas
  falsch ist*. So schneidet `guide_syntax` nur diesen einen Abschnitt heraus, wie der Plan sagt —
  der Hinweistext zu `attribute-ignored` nennt `{.backup}`, das Word-Beispiele nicht zeigen.
- **Fehlerbeispiele sind echt:** ein Test erzeugt jedes der vier Fehlerbeispiele und prüft, dass
  die Meldung im Guide wortgleich Teil der echten Meldung ist.
- **Beispiele ohne Front Matter** (Chart, Finanzdiagramm, Mermaid) sind Teile eines Dokuments: der
  Test stellt ihnen `titel:` und ein `#` voran, damit sie auch in den Vorlagen mit Deckblatt
  erzeugen. Bilder im Beispiel bekommt der Test als PNG mit; Mermaid nur, wo mermaid-cli zeichnet.
- Erwartung und Wortgrenze mit festen Optionen (Chart- und Mermaid-Renderer, ein SVG-Konverter),
  damit sie nicht davon abhängen, ob mermaid-cli oder `svg` hier eingerichtet sind; die Grenze
  wird zusätzlich mit den Standardoptionen geprüft.
- Die Bildformate kommen aus `writer.SUPPORTED_IMAGES` (keine zweite Liste).

### Abweichungen

- **Warnung:** Die PTA-Folienarten (`.agenda`, `.interim`, `.quote`, `.contact`) bleiben im
  Word-Guide bloße Namen („gelten nur für Folien“), obwohl Word sie schlicht zeigt. Sie zu
  beschreiben hieße `DOCUMENT_ATTRIBUTES` (gemeinsam mit E04-S06 und dem PDF) ändern und die
  Word-Beispiele samt Rundreise-Erwartungen erweitern; das Wortbudget ist zudem erschöpft.
- **Warnung:** Die Icon-Liste in `docs/ki-anleitung.md` bleibt (Test in
  `tests/design/icons/test_icons.py` unverändert); dort steht nur ein Verweis auf
  `./run.sh authoring-guide docx`. Die Liste gilt auch für Präsentationen, deren Guide (E04-S06)
  parallel entsteht — erst wenn beide Guides da sind, sollte sie dort durch einen Verweis ersetzt
  werden.
- **Warnung:** Das Wortbudget ist knapp: mit allen Renderern 2 464 von 2 500 Wörtern (Folien-Syntax
  rund 570, Chart-/Finanz-Abschnitt 569, Icons 270, Front Matter 290, Hinweise 170). Darum ist der
  eigene Text knapp gehalten; „Bild im Text“, SVG-Grafik und die Ausrichtung von Tabellenspalten
  stehen nicht einzeln da. Jede neue Word-Syntax verlangt Kürzungen anderswo.
- `guide_syntax` behält für PowerPoint die gemeinsamen Abschnitte, bis E04-S06 umstellt; die
  Änderung in `test_funktionen.py` ist rein additiv (`MISTAKES`, `without_mistakes`, ein Zweig für
  Word, ein Test).

### Prüfpunkte

- `./run.sh authoring-guide docx` lesen (oder die Erwartungsdatei): Ton, Verständlichkeit für
  Agenten, ob etwas Wichtiges fehlt.
- Die Sätze je Vorlage (`VARIANT_TEXTS`) und die Word-Wirkung der Folien-Syntax (`guide.EFFECT`).

### Offene Punkte

- E05-S05 soll diesem Guide einen PDF-Abschnitt anfügen (Antwort dort) — das passt nur nach
  Kürzungen; Notiz in E05-S05.
- Kürzere Renderer-Texte (die Folien-Absätze stehen auch im Word-Guide) würden Platz schaffen;
  das betrifft E04-S06 mit und gehört in eine eigene Story.
