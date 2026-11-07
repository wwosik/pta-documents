# E04-S06 Authoring Guide PPTX

> Status: Entwurf
> Epic: [E04 PPTX-Generator auf der PTA-PowerPoint-Vorlage](E04-pptx-generator.md)

## Zusammenfassung

`PptxGenerator.authoring_guide(options)` liefert die deutsche Anleitung, wie man Markdown für eine
PTA-Präsentation schreibt: Gliederung in Titel-, Trenn-, Inhalts- und Abschlussfolien, Textebenen,
Flow-Layouts und PTA-Layouts, Front Matter, Diagramme, Fehler und ein Beispiel — erzeugt aus
denselben Optionen wie `generate`.

## Kontext

- DocLibs: `Pptx/AuthoringGuide/Pptx.md` (145 Zeilen: *Writing Markdown for a deck*, *Structure*,
  *Layouts*, `{{templateLayouts}}`, `{{diagrams}}`, `{{frontMatter}}`, *Characters*, *When
  something is wrong*, *Example*), `PptxGenerator.AuthoringGuide` (Z. 106–175) und
  `Pptx.Tests/AuthoringGuideTests.cs` (122 Zeilen: Beispiele generieren, < 2 500 Wörter, nennt jeden
  Container, Alert, jedes Attribut und jeden Schlüssel, Diagramm-Abschnitt nur mit Renderer,
  Layoutliste der Vorlage, Abgleich mit `authoring-guide-*.expected.md`).
- PTA-Abweichungen gegenüber dem DocLibs-Guide: `#` nach dem Titel ist eine **Trennfolie mit
  Kapitelnummer** statt einer Abschnittsfolie mit Untertitel; Inhalt unter Kapitel- und
  Abschluss-`#` ist ein Fehler (E04-S01); `###` ist die Subheadline, Absätze Einleitungstext,
  Listen ab der dritten Textebene (E04-S02); keine Brands, keine Zeichen-Tabelle (PowerPoint nimmt
  die installierte Segoe UI); Front Matter deutsch (`vorlage`, `titelfolie`, `fusszeile`,
  `sprache`, `kennzeichnung`, `status.*` …).
- Bausteine aus E02-S05; Inhalte aus E04-S01 bis E04-S05.

## Vorgeschlagener Ansatz

1. Vorlage `src/pta_documents/generation/pptx/authoring_guide/pptx.md` (deutsch, ab `##`):
   - **Eine PTA-Präsentation aus Markdown** — kurz: Titel, die die Aussage nennen; wenige Zeilen.
   - **Gliederung** — Tabelle: erstes `#` + Front Matter → Titelfolie (`titelfolie: bild-01 |
     bild-02 | branchen | ohne-bild`), weitere `#` → Trennfolie „01", „02" …, `##` → Folie,
     `# … {.closing}` → Abschlussfolie; was unter `#` stehen darf.
   - **Inhalte** — Textebenen (Subheadline, Einleitungstext, Aufzählung), `**fett**` als PTA-
     Hervorhebung, Tabellen mit `**Titel**`-Zeile, Bilder in Bildplatzhaltern (werden beschnitten),
     Bildreihen, Code; was nicht passt, wird verkleinert (bis 12 pt) und fortgesetzt „(Forts.)".
   - **Layouts** — `layout_syntax_section` und die PTA-Wirkung aus E04-S03 (Raster, Fazit-Box,
     Kommentarbox, Alerts, `==…==` gelb, Statusfarben) sowie die PTA-Layouts aus E04-S04 (Agenda
     nur mit `{.agenda}`, Zwischenfazit, Zitat, Kontakt, Diagramm-Layouts) mit je einem kurzen
     Beispiel.
   - **Vorlagenlayouts** — die 35 Layoutnamen der Vorlage für `layout="…"`, gelesen aus der
     gewählten Vorlage, mit dem Hinweis, dass Inhalte an `---` auf die Platzhalter verteilt
     werden (E04-S01).
   - `{{diagrams}}`, `{{frontMatter}}` (aus `VALID_KEYS` des Generators und den Optionen;
     `kennzeichnung` je nach Vorlage mit seinem Standard).
   - **Wenn etwas falsch ist** — die Fehler mit Beispielen (Inhalt unter Kapitelfolie,
     unbekannter Container/Alert/Attribut, Karte ohne fetten Anfang, Fazit-Box zu lang, Agenda mit
     mehr als acht Punkten, unbekannter Layoutname).
   - **Beispiel** — ein vollständiges Deck: Titel, ein Kapitel, Textfolie, Karten, Tabelle mit
     Status-Labels, Fazit-Box, Abschluss.
2. `PptxGenerator.authoring_guide(options: PptxOptions | None = None) -> str` in
   `generation/pptx/generator.py`; Unterschiede zwischen `basis` und `schulung` (Sticker-Standard)
   kommen aus den Optionen.
3. Tests in `tests/generation/pptx/test_authoring_guide.py` (Port der DocLibs-Fälle mit den
   Hilfen aus E02-S05): jedes Beispiel generiert in `basis` und `schulung`; < 2 500 Wörter; nennt
   jeden Container, jedes Alert und Attribut aus E02-S02 und jeden gültigen Schlüssel;
   Diagramm-Abschnitt nur mit einem Renderer, der einen liefert; alle 35 Layoutnamen stehen darin;
   Abgleich mit `tests/generation/pptx/samples/authoring-guide-basis.expected.md` und
   `…-schulung.expected.md`.
4. `./run.sh authoring-guide pptx` gibt ihn aus; `docs/verwendung.md` verweist darauf.

## Akzeptanzkriterien

- [ ] `PptxGenerator.authoring_guide()` liefert einen deutschen Guide ab `##` mit den Abschnitten
      oben, passend zur gewählten Vorlage.
- [ ] Jedes Beispiel im Guide generiert ohne Fehler; der Guide bleibt unter 2 500 Wörtern.
- [ ] Neue Syntax, Schlüssel oder Layouts ohne Erwähnung im Guide lassen einen Test fehlschlagen.

## Offene Fragen

Keine.

## Notizen

- Abhängigkeiten: E02-S05; vollständig erst nach E04-S03 bis E04-S05 — bis dahin nennt der Guide
  nur, was der Generator schon kann.
