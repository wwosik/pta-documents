# Projektgedächtnis

Gesammelte Fakten zu dieser Codebasis: getroffene Entscheidungen, verwendete Muster, Fallen, die
man sich merken sollte. Gemeinsam hier statt im geräte-lokalen Gedächtnis irgendeines Werkzeugs,
damit jeder Agent auf jedem Rechner dasselbe liest.

Sachlich und aktuell halten. Was hier steht und nicht mehr stimmt, wird in derselben Änderung
korrigiert, die es unwahr gemacht hat — ein veralteter Eintrag ist schlimmer als ein fehlender,
weil ihm vertraut wird.

## Überblick

- Angelegt am 2026-11-06 aus dem Katalog `projekt-init` (`core`, `spec-workflow`). Der Katalog
  hat keine Python-Komponente; die Python-Konventionen kommen mit
  `spec/50-entwurf/T01-S01-python-projektgeruest.md`.
- Eigenständig weitergeführte Python-3-Portierung von DocLibs (.NET, `wwosik/doc-libs`, Stand
  Release `2610.28.22`). Es gibt keine Rückportierung und keinen Abgleich mit dem Original.
- Analysen in `spec/10-analysen/`, Pläne in `spec/50-entwurf/`, Reihenfolge in
  `M01-pta-dokumente-aus-markdown.md`.
- **Stack:** Python ≥ 3.12, venv + pip (kein uv), hatchling, pytest, ruff, pyright strict.
  Kern: python-docx, python-pptx, lxml, markdown-it-py + mdit-py-plugins, Pillow. Extras:
  `pdf` (reportlab, pikepdf, pdfplumber), `svg` (resvg-py), `diagrams` (mermaid-cli, extern).
- **Paketstruktur** (`src/pta_documents/`): `errors.py` (`DocumentConversionError`,
  `DocumentFormat`), `markdown/` (Dokumentmodell, Front Matter, Parser), `design/`
  (Designmodell, eingebettete Vorlagen), `conversions/` (→ Markdown), `generation/`
  (`common/`, `docx/`, `pptx/`).
- **Stand 2026-11-06:** M01 umgesetzt (alle Stories in `spec/60-prüfung/`): DOCX- und
  PPTX-Generator auf den PTA-Vorlagen, DOCX-/PPTX-Konverter, Front Matter, Designmodell,
  eingebettete Vorlagen. PDF, Diagramme/Charts, PDF-Konverter, Folien-Syntax und Flow-Layouts
  sind nur geplant. Bedienung: `docs/verwendung.md`.
- **Zweite Referenz:** `~/mvv/vt-tools-libs` (Schwesterbibliothek von DocLibs für die MVV,
  .NET) ist seit DocLibs `2610.28.22` weitergegangen — Hinweise an den Schreiber
  (`GenerationResult`), Sprechernotizen, Builds, Übergänge, Szenen, HTML-Decks,
  `make_document`, Feature-Tour. Abgleich: `spec/10-analysen/2026-11-07 abgleich-vt-tools-libs.md`;
  daraus die Epics E08–E10. E11–E17 sind eigene Ideen (Bausteine, Dokumentpflege, lange
  Berichte, Dokumenttypen der Beratung, visuelle Bausteine, Schulung, Arbeitsfluss), alle Stand
  2026-11-07 im Entwurf und vom Menschen zur Umsetzung gewünscht; E08-S04 ist zurückgestellt.
- **Werkzeugverben und Schalter sind englisch** (`generate`, `check`, `preview`, `compare`,
  `--strict`), Front Matter und Anleitungen deutsch, Markdown-Syntaxnamen englisch
  (Entscheidung 2026-11-07).
- Erzeugte Beispieldateien zum Ansehen schreiben die Tests nach `.tmp/review/`. Auf der
  Entwicklungsmaschine gibt es weder Word/PowerPoint noch LibreOffice; das Öffnen in Office ist
  ein offener Prüfpunkt der Stories.

## Entscheidungen

- **Entscheidungen des Menschen vom 2026-11-06:** Projektsprache Deutsch; portiert wird alles
  außer `DocumentConversions.WindowsOnly` (Office-COM); zusätzlich ein DOCX-Generator auf den
  PTA-Word-Vorlagen; erst Analysen und Pläne, umgesetzt wird nach Annahme der Pläne.
- **Nur das PTA-Design.** Die Standardvorlagen von DocLibs (neutraler Brand, Brand-Packs,
  eingebauter Folienmaster, fremde Vorlagen) entfallen; die Standards stammen aus
  `source-templates/` (siehe `spec/10-analysen/2026-11-06 pta-designstandards.md`).
- **Weitere Entscheidungen vom 2026-11-06** (Einzelheiten in den Plänen und unter
  *Entscheidungen* in `spec/10-analysen/2026-11-06 portierung-doclibs-python.md`): keine
  Veröffentlichung, ein Paket mit Extras, Python ≥ 3.12, vorerst kein Remote/CI; PDF über eine
  portierte Layout-Engine mit Selawik/Segoe UI; Mermaid über mermaid-cli; JIRA-Wiki entfällt;
  BPS-PTA-DATIS ist keine Variante; Front Matter deutsch; in Word und PDF ist `#` „Überschrift 1",
  in Folien die Titel- bzw. Trennfolie.

## Fallen

- Die PTA-Folienlayouts haben kein `type`-Attribut — nur über den Namen auffindbar. Das
  Abschlusslayout heißt `Abbschlussfolie` (sic).
- Mehrere Folienlayouts zeichnen Eckklammern, Linien und Logo über unsichtbare Platzhalter
  (Aufforderung „x"); sie müssen auf jeder Folie leer angelegt werden.
- Word und PowerPoint der PTA unterscheiden sich: Text `000000` vs. `404040`, Tabellenkopf
  `006FB9` vs. `004676`.
- Die Querformat-Word-Vorlagen haben die Formatvorlagen `Hyperlink`, `toc 1`, `toc 2` nicht; sie
  werden aus der Hochformat-Vorlage übernommen (`design/word.py`, `BORROWED_STYLES`).
- Stilnamen in `styles.xml` sind die internen englischen (`heading 1`, `List Bullet`,
  `caption`); nur eigene Formatvorlagen der PTA heißen deutsch (`Autor`, `Standard fett`,
  `Zwischenüberschrift`, `PTA`).
- python-pptx: `itertext()` auf seinen Elementen liefert Text mehrfach — Text immer über die
  `a:t`-Elemente lesen.
- python-pptx legt Fußzeilen- und Foliennummer-Platzhalter beim Anlegen einer Folie nicht an;
  der Generator kopiert sie aus dem Layout.
- python-docx zeigt Stilnamen als UI-Namen („Heading 1"); verglichen wird mit dem `w:name` aus
  `styles.xml` („heading 1").
