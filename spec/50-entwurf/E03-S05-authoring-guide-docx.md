# E03-S05 Authoring Guide DOCX

> Status: Entwurf
> Epic: [E03 DOCX-Generator auf den PTA-Word-Vorlagen](E03-docx-generator.md)
> Milestone: [M04 Präsentieren und Schulung](M04-praesentieren-und-schulung.md)

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

- [ ] `DocxGenerator.authoring_guide()` liefert einen deutschen Guide ab `##` mit allen
      Abschnitten oben.
- [ ] Jedes Beispiel im Guide generiert ohne Fehler; der Guide bleibt unter 2 500 Wörtern.
- [ ] Ändert sich die Liste gültiger Schlüssel oder der Folien-Syntax, schlägt ein Test fehl, bis
      der Guide sie nennt.

## Offene Fragen

Keine.

## Notizen

- Abhängigkeiten: E02-S05; die Abschnitte zu Folien-Syntax und Diagrammen erst nach E03-S03 und
  E03-S04 vollständig — bis dahin beschreibt der Guide nur, was schon geht.
