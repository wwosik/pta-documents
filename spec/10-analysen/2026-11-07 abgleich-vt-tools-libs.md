# Abgleich mit vt-tools-libs

> Stand: 2026-11-07. Quelle: `~/mvv/vt-tools-libs`, Commit `49456ab` („Plan 00029 done"), 49 Commits
> vom 2026-10-20 bis 2026-10-29.

vt-tools-libs ist die Schwesterbibliothek von DocLibs für die MVV: dieselbe Herkunft, .NET 10,
zehn NuGet-Pakete, rund 23 000 Zeilen Code (33 000 mit Tests). Unsere Portierung geht vom DocLibs-Release
`2610.28.22` aus ([Portierungsanalyse](2026-11-06%20portierung-doclibs-python.md)). vt-tools-libs
ist seitdem mit den Plänen 00013–00029 weitergegangen; diese Analyse stellt fest, was es hat, was
wir nicht haben, und was davon für die PTA-Kopie infrage kommt. Die daraus entstandenen Pläne
liegen in `spec/50-entwurf/` (E08–E13).

## Pakete im Vergleich

| vt-tools-libs | Zeilen | Bei uns |
| ------------- | -----: | ------- |
| `DocumentConversions` (+ JIRA) | 3 200 | E07 (ohne JIRA); DOCX/PPTX → Markdown umgesetzt |
| `DocumentConversions.Svg` | 300 | E06-S04 |
| `DocumentConversions.WindowsOnly` | 380 | entfällt |
| `DocumentGeneration` (Brands, Zeichnen, Szenen, Guides, `GenerationResult`) | 4 100 | E01/E02 teilweise; Brands entfallen; **Szenen und `GenerationResult` fehlen** |
| `DocumentGeneration.Fonts` (Liberation) | 50 | entfällt (Selawik/Segoe UI, E01-S03) |
| `DocumentGeneration.Html` | 2 600 | **fehlt** |
| `DocumentGeneration.Charts` | 2 400 | E06-S01, E06-S02 |
| `DocumentGeneration.Tools` (`make_document`) | 500 | **fehlt** |
| `DocumentGeneration.Diagrams` | 1 500 | E06-S03 |
| `DocumentGeneration.Pptx` | 5 500 | E04; Basis umgesetzt (E04-S01, E04-S02) |
| `DocumentGeneration.Pdf` | 2 700 | E05 |
| — | — | **E03 DOCX-Generator** gibt es nur bei uns |

## Was vt-tools-libs hat und wir nicht einmal geplant hatten

Diese Funktionen sind nach dem DocLibs-Stand entstanden, den unsere Analyse zugrunde legt, und
fehlen deshalb in den Plänen E01–E07.

| Funktion | vt-tools-libs | Nutzen für die PTA | Plan |
| -------- | ------------- | ------------------ | ---- |
| **Hinweise an den Schreiber** | `GenerationResult` mit `Notes` (`GenerationNote(Code, Line, Message)`): geteilte oder übervolle Folien, fehlende Zeichen, weggelassenes HTML, nicht gezeichnete Diagramme, vergrößerte Bilder. `generate` gibt bei uns nichts zurück. | Eine KI, die Markdown schreibt, erfährt sonst nie, dass ihre Folie geteilt wurde | E08-S01 |
| **Sprechernotizen** | `::: notes` → Notizenseite in PPTX (Notizenmaster), im PDF optional | Schulungen und Kundenpräsentationen | E09-S01 |
| **Builds** | `{.build}` / `{.frag}`: Listen, Karten, Tabellen erscheinen per Klick (Fade); `build: lists` | Vorträge | E09-S02 |
| **Übergänge** | Front Matter `transition`, `{transition=…}`: none, fade, push, wipe, morph | Vorträge; Morph mit Szenen | E09-S03 |
| **Szenen** | `::: scene`: benannte Formen auf einem 160 × 90-Raster, Schritte, Morph zwischen Folien | Architekturbilder, die sich über Folien entwickeln — Bedarf offen | E09-S04 |
| **HTML-Präsentation** | eine selbständige HTML-Datei: dieselben Folien, Notizen mit Timer, Druck je Folie | Vorschau ohne PowerPoint — auch für eine KI per Screenshot | E10 |
| **`make_document`-Werkzeug** | Beschreibung, JSON Schema, Guide aus den Optionen; `Run`, `Reply` in festem JSON | Anbindung an einen KI-Host (Chat-Assistent der PTA) | E08-S04 |
| **Feature-Tour** | `docs/tour.md` → `tour.html`, von Tests aktuell gehalten; prüft, dass die Tour jede Syntax der Guides zeigt | Unsere `samples/funktionen/` ist dasselbe ohne Absicherung | E08-S03 |
| **Bildreihen** | bis vier Bilder nebeneinander, `"caption"` als Unterschrift, `scale=N` als Obergrenze | Fotos auf Folien | war schon da (E04-S02: Bildreihe); Unterschrift und `scale` als Prüfpunkt in E04-S03 |
| **Vorlagen-Layout je Folie** `{layout="…"}`, Abschlussfolie `{.closing}`, `date`, `footer` | Plan 00020 | — | umgesetzt (E04-S01) |
| **Zeichen-Hinweise** | Zeichen, die die Schriften nicht haben, als Note | PDF mit Selawik | E05-S04 + E08-S01 |

## Was vt-tools-libs hat und wir bereits planen

Flow-Layouts (`cards`, `rows`, `panel`, `statement`, `columns`, Alerts, Tags, `==mark==`,
farbige Wörter, Kicker, Status-Labels) — E02-S02, E03-S03, E04-S03; PDF — E05; Mermaid, Charts,
Finanzdiagramme, SVG — E06; PDF → Markdown — E07-S04; Authoring Guides mit Tests gegen
`authoring-guide-*.expected.md` — E02-S05, E03-S05, E04-S06, E05-S05.

Unterschiede im Detail, die die Pläne noch nicht nennen und die bei der Umsetzung geprüft werden
sollten:

- **Fortsetzungsfolien** (Plan 00021): vt-tools-libs schätzt Texthöhen nach Zeichenklassen und
  gibt Textfolien, die verkleinert wurden, PowerPoints `normAutofit`. Unser `fitting.py` misst
  mit Pillow; `normAutofit` fehlt (Prüfpunkt E04-S02).
- **Bilder** (Plan 00018): Bilder auf Folien werden bis zum Vierfachen vergrößert, um ihren Raum
  zu füllen; ab dem Doppelten gibt es eine Note. Bei uns beschneidet der Bildplatzhalter der
  PTA-Vorlage; eine Note „Bild stark vergrößert" wäre trotzdem nützlich (E08-S01).
- **Rohes HTML** (Plan 00015) wird weggelassen, nicht als Text geschrieben; bei uns erscheint es als
  Text (`ki-anleitung.md`). Mit E08-S01 sollte es weggelassen und gemeldet werden.
- **Callouts** (Plan 00028): ein führendes `**Label:**` wird ein eigenes Kästchen; `### 1 · Titel`
  in Karten zeigt die Zahl als Badge; `### Titel {.accent}` füllt eine Karte; ein kurzer erster
  Absatz wird ein Lead, ein fetter letzter ein Fazit. Für E04-S03 zu prüfen, ob das zum PTA-Stil
  passt (die Fazit-Box der Vorlage ist das PTA-Gegenstück zum Fazit-Absatz).
- **Diagramme** (Plan 00029): Knoten mit 1,5 pt Linie, fette erste Zeile, Gruppen als rahmenlose
  Flächen mit Kapitälchen-Titel, Datenbanken als runde Kästen. Für E06-S03 als Startpunkt des
  PTA-Looks geeignet.

## Was wir bewusst nicht übernehmen

- **Brand-System** (`Brand`, `BrandPack`, `BrandRegistry`, `neutral`, `mvv-dark`, Canvas,
  Glows, `SectionBackground`, `ClosingArtwork`), eingebauter PPTX-Master, MVV-Look (Pläne
  00014, 00028, 00029): die PTA hat ein festes Design aus ihren Vorlagen (Entscheidung 2026-11-06).
- **Schriften:** `DocumentGeneration.Fonts` (Liberation), Einbettung der Brand-Schriften als EOT in
  Decks. Segoe UI darf nicht weitergegeben werden; PDF nimmt Selawik (E01-S03).
- **Konvertierungen:** WindowsOnly (Office-COM) und Markdown ↔ JIRA-Wiki (Entscheidungen
  2026-11-06).
- **.NET-Spezifisches:** Source Link und PDBs (Plan 00013), NuGet-Feed, `yyMM.d.H.r`-Versionen,
  Azure Pipelines. Wir veröffentlichen nicht.
- **`DocumentGeneration.Html` als Präsentationsformat für Zuhörer:** die PTA präsentiert mit
  PowerPoint. Ein HTML-Deck wird in E10 nur als Vorschau- und Prüfwerkzeug vorgeschlagen.

## Neue Ideen, die keine der beiden Bibliotheken hat

Aus dem Alltag einer IT-Beratung (Angebote, Konzepte, Statusberichte, Schulungen) abgeleitet und
als Pläne ausgearbeitet; ob sie gebraucht werden, entscheidet der Mensch je Epic.

| Idee | Kurz | Plan |
| ---- | ---- | ---- |
| Prüfbefehl mit Stilregeln | `./run.sh pruefen`: Hinweise ohne Erzeugen, Regeln der PTA-Musterfolien (Punkte je Folie, Wörter je Folie), geschätzte Vortragsdauer, Bild ohne Quelle, fehlender Alt-Text | E08-S02 |
| Variablen | `{{kunde}}` aus Front Matter oder Kommandozeile — ein Angebot für mehrere Kunden | E11-S01 |
| Bausteine | Firmenprofil, Leistungen, Kontaktfolien einmal schreiben, überall einbinden | E11-S02 |
| Tabellen und Charts aus Dateien | CSV/XLSX aus dem Dokumentordner als Tabelle oder Chart | E11-S03 |
| QR-Codes | `![](qr:https://…)` in PTA-Blau — Link zur Umfrage oder zum Repo auf der Folie | E11-S04 |
| Änderungshistorie | Tabelle „Dokumentenhistorie" aus dem Markdown oder aus `git log` | E12-S01 |
| Dokumentvergleich | zwei Fassungen → Word mit Änderungsverfolgung, für Angebotsrunden | E12-S02 |
| Kennzeichnung | „Vertraulich"/„Entwurf" in Word und PDF, passend zum Sticker in PowerPoint (E04-S05) | E12-S03 |
| Abkürzungen und Glossar | `*[PTA]: …` → Abkürzungsverzeichnis | E13-S01 |
| Querverweise | „siehe Tabelle 3", „Kapitel 2.1" als Word-Felder | E13-S02 |
| Barrierefreiheit | Alt-Texte, Tabellenköpfe, Dokumentsprache, PDF/UA — für öffentliche Auftraggeber | E13-S03 |

## Empfohlene Reihenfolge

Nach M01 zuerst, was ohne neue Formate geht und sofort hilft, besonders einer KI als Schreiber:
E08-S01 (Hinweise), E09-S01 (Sprechernotizen), E08-S03 (Funktionsübersicht durch Tests gesichert).
Dann die ohnehin geplante Folien-Syntax (E02-S02, E04-S03) und E09-S02/S03. E08-S04, E10 und
E09-S04 erst, wenn der Bedarf feststeht. Die Ideen in E11–E13 sind unabhängig voneinander; E12-S02
(Dokumentvergleich) und E13 brauchen vor allem Word und können parallel zum PDF (E05) entstehen.

## Offene Punkte

Vom Menschen am 2026-11-07 entschieden:

1. Wird ein KI-Host (Chat-Assistent) die Bibliothek aufrufen, sodass E08-S04 nötig ist, oder
   bleibt der Weg „Claude Code im Klon" (`docs/ki-anleitung.md`)?

> Nein, nur der Klon mit `run.sh`; E08-S04 zurückgestellt.
2. Brauchen PTA-Vorträge Szenen (E09-S04) und ein HTML-Deck (E10), oder genügen Notizen, Builds
   und Übergänge in PowerPoint?

> Alles gewünscht: Notizen, Builds, Übergänge, Szenen, HTML-Deck und PNG-Vorschau.
3. Welche der Ideen E11–E13 sind gewünscht?

> Alle drei. Der Schlüssel `kennzeichnung` gilt gemeinsam für alle Formate (E04-S05, E12-S03).
