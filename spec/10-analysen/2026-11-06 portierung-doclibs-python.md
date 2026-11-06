# Portierung DocLibs (.NET) → Python 3

> Stand: 2026-11-06. Quelle: `git.wosik.net/wwosik/doc-libs`, Release `2610.28.22`
> (Commit `2206e4a`).

Diese Analyse stellt fest, was DocLibs heute ist, was davon in die Python-Portierung für die PTA
übernommen wird, was entfällt und welche Python-Bibliotheken die .NET-Abhängigkeiten ersetzen.
Die Pläne dazu liegen in `spec/50-entwurf/`.

## Ausgangslage

DocLibs ist eine öffentliche, kundenneutrale .NET-10-Bibliothek (MIT), aufgeteilt in acht
NuGet-Pakete mit je einem Testprojekt — rund 17 000 Zeilen Code und 7 000 Zeilen Tests.

| Paket | Zeilen | Inhalt |
| ----- | -----: | ------ |
| `DocumentConversions` | 3 200 | `.pdf`/`.docx`/`.pptx` → Markdown mit Bildern, Formaterkennung, Markdown ↔ JIRA-Wiki, Markdown-Hilfen |
| `DocumentConversions.Svg` | 300 | SVG → PNG (SkiaSharp), SVG-Bilder in Folien und PDFs |
| `DocumentConversions.WindowsOnly` | 380 | `.doc`, `.rtf`, `.xls`, `.xlsx` über Office-COM |
| `DocumentGeneration` | 2 600 | Brands (`Brand`, `BrandPack`, `ResolvedBrand`), Zeichenmodell (`Drawing`) + SVG-Ausgabe, Front Matter, Folien-Syntax, Authoring Guides |
| `DocumentGeneration.Pptx` | 4 500 | Markdown → `.pptx`: eingebauter Master im Brand-Design oder fremde Vorlage, Flow-Layouts, Fitting, Schrifteinbettung (EOT), native Diagramme |
| `DocumentGeneration.Pdf` | 2 500 | Markdown → PDF/A-2b: eigene Layout-Engine, PdfPig als Writer, Liberation-Schriften |
| `DocumentGeneration.Diagrams` | 1 250 | Mermaid über Mermaider (C#) → SVG → `Drawing` |
| `DocumentGeneration.Charts` | 2 350 | `chart`-Blöcke (CSV) → native Folien-Diagramme / Vektoren; Finanzdiagramme |

Querschnitt, der mitportiert werden muss: die Fehlerklasse `DocumentConversionException` mit
`Reason`, „Stream rein, Stream raus" (keine Dateizugriffe außer auf Wunsch), synchron, die
Testmuster (Beispieldateien + `*.expected.md`, Roundtrip-Tests der Generatoren,
`DOCLIBS_UPDATE_EXPECTED=1`) und die Authoring Guides für Markdown-Schreiber.

## Was sich für die PTA-Kopie ändert

| Thema | DocLibs | PTA Documents |
| ----- | ------- | ------------- |
| Sprache | C# / .NET 10 | Python 3 |
| Zielgruppe | öffentlich, kundenneutral | intern für die PTA, eigenständig weitergeführt (keine Rückportierung) |
| Design | Brand-System: `Brand.Neutral`, eigener eingebauter PPTX-Master, Brand-Packs, Front-Matter-Auswahl `template:` | **Nur das PTA-Design**, abgeleitet aus `source-templates/` (siehe Designanalyse). Kein neutraler Brand, kein eingebauter Master, keine Brand-Packs |
| Vorlagen | PPTX: eingebauter Master oder Fremdvorlage | DOCX und PPTX werden **auf den PTA-Vorlagen selbst** erzeugt; PDF zeichnet das Design der Word-Vorlage nach |
| Formate | PPTX, PDF | **DOCX (neu)**, PPTX, PDF |
| WindowsOnly | `.doc`/`.rtf`/`.xls`/`.xlsx` per COM | entfällt (Entscheidung 2026-11-06) |
| Schriften | Liberation (gebündelt) bzw. Brand-Schriften | Segoe UI (PTA-Hausschrift, proprietär) — Strategie siehe E01 |
| Verteilung | nuget.org per Tag | offen (siehe Offene Punkte) |

„Standardvorlagen entfernen" heißt konkret: entfallen ersatzlos `Brand.Neutral`, der Testbrand
`sample`, `BrandPack`/`brand.json`, `BrandRegistry` und die Front-Matter-Auswahl `template:
<brand>`, der eingebaute PPTX-Master (`TemplateBuilder`), `CustomTemplateOptions` für beliebige
Fremdvorlagen und die Liberation-Schriften als Standard. An ihre Stelle tritt ein festes
PTA-Designmodell; die Front-Matter-Wahl betrifft nur noch die **Variante** der PTA-Vorlage
(Hochformat/Querformat, mit/ohne Deckblatt, BPS-PTA-DATIS; Basis-/Schulungsfolien).

## Abbildung der Abhängigkeiten

| .NET | Zweck | Python-Ersatz | Bewertung |
| ---- | ----- | ------------- | --------- |
| Markdig | Markdown-Parser mit Erweiterungen (Tabellen, Attribute, Container, Alerts, `==mark==`) | **markdown-it-py** + **mdit-py-plugins** (front_matter, attrs, container, footnote, deflist, tasklists) | gut; eigene Regeln für Alerts, `==mark==`, `[Wörter]{.success}` und die Heading-Attribute (die DocLibs ohnehin selbst parst) |
| DocumentFormat.OpenXml | DOCX/PPTX lesen und schreiben | **python-docx**, **python-pptx**, darunter **lxml** | gut; Tiefen (Nummerierung, Felder, Diagramm-XML, Schrifteinbettung, SVG-Erweiterung) per lxml direkt am XML |
| PdfPig (lesen) | Text, Positionen, Bilder aus PDF | **pdfplumber** (pdfminer.six) oder **pypdfium2** | gut; Zeilen-/Absatzheuristik wird 1:1 portiert |
| PdfPig (schreiben) + eigene Layout-Engine | PDF/A-2b mit Teilschriften, Lesezeichen, Links | **reportlab** (Canvas, Schrift-Subsetting) + **pikepdf** für XMP/OutputIntent/PDF/A-Kennung; Prüfung mit veraPDF | machbar; Layout-Engine wird portiert. Alternative siehe Offene Punkte |
| Mermaider (C#, MIT) | Mermaid → SVG | kein reifes reines Python-Paket. Optionen: **mermaid-cli** (Node + Chromium, `htmlLabels: false`) oder Mermaider selbst portieren | größtes Risiko — siehe Offene Punkte |
| SkiaSharp + Svg.Skia | SVG → PNG | **resvg-py** (Rust, ohne Systembibliotheken) oder **cairosvg** (braucht Cairo) | gut |
| System.Text.Json | `brand.json` | entfällt mit den Brand-Packs | — |
| eigene TrueType-/EOT-Logik | Schriftnamen, Einbettung in Folien | **fontTools** | gut |
| xUnit | Tests | **pytest** (+ Snapshot-Vergleich wie `*.expected.md`) | gut |

Kein Paket dieser Liste ist GPL/AGPL; borb (PDF/A, AGPL) und WeasyPrint (Pango-Systemabhängigkeit)
wurden bewusst nicht gewählt.

## Was wörtlich portiert wird, was neu entsteht

- **Portierung mit gleichem Verhalten:** Formaterkennung, die drei Konverter nach Markdown, JIRA
  hin und zurück, Markdown-Hilfen, Front Matter, Heading-Attribute und Container-Syntax,
  Zeichenmodell und SVG-Ausgabe, Charts samt Finanzdiagrammen, Fitting-Regeln der Folien,
  PDF-Seitenumbruchregeln (Überschriften bleiben beim Folgenden, keine Hurenkinder/Schusterjungen),
  Authoring Guides, Testmuster. Die `*.expected.md` der Konverter können als Startpunkt der
  Python-Tests übernommen werden, solange die Beispieldateien neutral bleiben.
- **Umbau:** PPTX schreibt nicht mehr auf einem selbstgebauten Master, sondern auf
  `PTA-Powerpoint-Basisvorlage.potx` und wählt dessen Layouts; Farben, Schriften und Größen kommen
  aus dem PTA-Designmodell statt aus `ResolvedBrand`.
- **Neu:** DOCX-Generator auf den PTA-`.dotx`. Er nutzt die Formatvorlagen der Vorlage
  (`Überschrift 1–3`, `Aufzählungszeichen`, `Listenabsatz`, Tabellenformat `PTA`, `Beschriftung`
  …), statt selbst zu formatieren — so bleibt das Ergebnis in Word bearbeitbar wie ein von Hand
  angelegtes PTA-Dokument.

## Größenordnung

Grob gleich groß wie das Original: ~16 700 Zeilen Code (ohne WindowsOnly) werden in Python erfahrungsgemäß etwas
kürzer, der DOCX-Generator kommt hinzu (geschätzt 1 500–2 500 Zeilen). Die Reihenfolge der Pläne
ist so gewählt, dass nach Meilenstein M01 ein nutzbares Werkzeug (Markdown → PTA-Word und
PTA-PowerPoint) steht, bevor PDF, Diagramme und Konverter folgen.

## Offene Punkte

Diese Punkte sind als *Offene Fragen* in den Plänen gestellt:

1. **Schrift für PDF:** Segoe UI ist proprietär (Microsoft) und darf nicht mitgeliefert werden.
   Vorschlag: im PDF **Selawik** (Microsofts metrikkompatibler Open-Source-Ersatz, OFL) bündeln;
   Segoe UI verwenden, wenn sie auf dem System gefunden wird und die Lizenz der PTA das Einbetten
   erlaubt. DOCX/PPTX nennen nur den Namen `Segoe UI` — Office hat ihn.
2. **PDF-Weg:** eigene Layout-Engine portieren (reportlab + pikepdf, keine Systemabhängigkeit,
   PDF/A-2b wie bisher) **oder** DOCX erzeugen und über LibreOffice nach PDF/A wandeln (identisch
   mit Word, aber LibreOffice auf jedem Rechner nötig).
3. **Mermaid:** mermaid-cli (Node/Chromium als Laufzeitabhängigkeit) oder Portierung von
   Mermaider nach Python (großer Aufwand) — oder Diagramme zunächst weglassen.
4. **Verteilung:** internes Paket-Repository der PTA, Installation direkt aus Git, oder nur als
   Quellcode im Repo?
5. **Git-Remote** dieses Repos (noch keiner eingerichtet).
6. **Logo:** Die Word-Vorlagen enthalten das PTA-Logo nur als EMF (1 KB, Vektor), die
   BPS-PTA-DATIS-Vorlage als PNG. Für PDF und SVG wird das Logo als SVG/PNG gebraucht — Zuschnitt
   aus der Vorlage oder offizielle Logodateien von der PTA?
