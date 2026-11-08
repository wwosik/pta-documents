# Beispiel: Funktionsübersicht

Zeigt alles, was die Generatoren heute können — jede Datei deckt einen Bereich ab. Der
Word-Bericht zeigt zu jeder Funktion den Markdown-Quelltext als Codeblock und darunter das
Ergebnis; in der Präsentation steht der Quelltext jeder Folie auf ihrer Notizenseite.

| Datei | Zeigt |
| ----- | ----- |
| `funktionen-bericht.md` | Word: alle Front-Matter-Schlüssel, Überschriften 1–6, Zeichenformate, Links, Fußnoten, Typografie, Listen (verschachtelt, Neustart, Aufgaben, Definitionen), Tabellen mit Titel, Ausrichtung und Beschriftung, Status-Labels, markierte Zeile, Abbildungen, Bild im Text, Bildreihe, SVG-Grafik, QR-Code (`qr:`), Diagramme aus `chart`-Blöcken (Balken, gestapelte Flächen, Linie mit Lücke, `;` mit Dezimalkomma, Beschriftung `Abbildung: …`), ein Finanzdiagramm als Abbildung, Code, Zitat, Trennlinie, Inhaltsverzeichnis; die Folien-Syntax in Word: alle Container außer `notes`, Alerts, `==Markierung==`, farbige Wörter; Zeitstrahl (`::: timeline`, als Bild) und Projektplan (`::: gantt raster=monat`, als Tabelle mit schattierten Monaten); Schrittfolge (`::: steps` mit `{.current}`, als Bild), Bewertungsmatrix mit Harvey Balls (`[3/4]`, als Zeichen), Risikomatrix (`::: riskmatrix green=4 yellow=12`, Bild mit Legende); Icons (`:icon-check:` als Aufzählungszeichen und im Text); Bildstile (`{.round}`, `{.grey}`, `{scale=0.3}` nach dem Bild) |
| `funktionen-praesentation.md` | PowerPoint: Titel-, Trenn- und Abschlussfolie, Textebenen, nummerierte Listen mit Startwert, Verkleinern, Tabelle im PTA-Stil mit Titelzeile, längere Tabelle, Code, Bild mit Text, Bild allein, SVG-Grafik, QR-Code (`qr:`, eingepasst statt beschnitten), Bildreihe, benannte Layouts mit `---`, Sprechernotizen (`::: notes`), Flow-Folien (alle Container, `.dark`, `kicker`, Alerts, Markierung, farbige Wörter, Status-Labels), Zeitstrahl und Projektplan (`::: timeline`, `::: gantt` als Formgruppen), Schrittfolge, Harvey Balls und Risikomatrix (`::: steps`, `[3/4]`, `::: riskmatrix` als Formgruppen mit Legende), Icons (`:icon-check:` als Kartenfigur und Bild-Aufzählungszeichen), Diagramme aus `chart`-Blöcken auf allen vier Diagrammlayouts, alle sechs Finanzdiagramme (`financial-chart`, mit Text davor und danach, alle `options`), PTA-Folienarten (`.agenda`, `.interim`, `.quote`, `.contact`, mit rundem Foto); Bildausschnitt (`{focus=top}`, `center`, `bottom`), eingepasstes Bild (`{fit=contain}`), rundes und graues Bild (`{.round}`, `{.grey}`) |
| `mermaid-praesentation.md` | PowerPoint: jede gezeichnete Mermaid-Art (`flowchart`, `sequenceDiagram`, `classDiagram`, `stateDiagram-v2`, `erDiagram`, `pie`, `gantt`, `mindmap`) als Gruppe bearbeitbarer Formen; braucht mermaid-cli (`./run.sh setup` mit Node.js, Prüfung mit `./run.sh mermaid`) — ohne bleiben die Blöcke Code mit Hinweis |
| `mermaid-bericht.md` | Word: Mermaid-Diagramme als Abbildungen (SVG mit PNG-Ersatz), mit und ohne `Abbildung: …`-Beschriftung; braucht mermaid-cli wie `mermaid-praesentation.md` |
| `varianten-dokument.md` | Word-Variante `quer-ohne-deckblatt` mit `sprache: en` und `firma` |
| `varianten-hochformat-dokument.md` | Word-Variante `hoch-ohne-deckblatt` mit `inhaltsverzeichnis: nein`, `typografie: nein`, `syntaxhervorhebung: nein` |
| `varianten-querformat-dokument.md` | Word-Variante `quer` (mit Deckblatt) |
| `varianten-folien.md` | Schulungsvorlage mit Sticker „For internal use only“, `titelfolie: ohne-bild`, `sprache: en` (englisches Logo) |
| `varianten-bild-01-folien.md` | `titelfolie: bild-01` |
| `varianten-branchen-folien.md` | `titelfolie: branchen` |
| `varianten-vertraulich-folien.md` | `kennzeichnung: vertraulich` (Sticker „VERTRAULICH“ oben rechts auf dem Master) |
| `images/` | selbst erzeugte Bilder in den PTA-Farben (keine fremden Rechte), `plan.svg` von Hand gezeichnet; `*-folie.png`/`*-folie.svg` sind dieselben Bilder in den Proportionen der Folien-Bildplatzhalter |

```sh
./run.sh generate samples/funktionen --out documents/funktionen
```

Alle Dateien erzeugen ohne Hinweise (`mermaid-praesentation.md` und `mermaid-bericht.md` nur, wenn mermaid-cli eingerichtet ist) (`./run.sh generate-samples funktionen` endet mit Code 0)
und bestehen `./run.sh check samples/funktionen --strict`; die Folie „Viel Text wird
verkleinert" ist absichtlich zu voll, darum schaltet `funktionen-praesentation.md` dafür
`pruefung: style-bullets, style-words` ab.
Geteilte „(Forts.)"-Folien zeigt die Funktionsübersicht deshalb nicht; was dabei gemeldet wird,
steht in [docs/anleitung.md](../../docs/anleitung.md), Abschnitt 8.

`./run.sh test` hält die Übersicht aktuell (`tests/samples/test_funktionen.py`): Fehlt einer
Syntax, einem Front-Matter-Schlüssel oder einer Vorlagenvariante ein Beispiel hier, schlägt
ein Test fehl und nennt das Fehlende. Jede Datei muss in der Tabelle oben stehen. Die erzeugten
Dokumente liegen danach in `.tmp/review/funktionen/`, ihre Rundreise durch die Konverter in
`tests/samples/funktionen/*.roundtrip.expected.md`.

Noch nicht enthalten, weil noch nicht umgesetzt: PDF.
