# Beispiel: Funktionsübersicht

Zeigt alles, was die Generatoren heute können — jede Datei deckt einen Bereich ab.

| Datei | Zeigt |
| ----- | ----- |
| `funktionen-bericht.md` | Word: alle Front-Matter-Schlüssel, Überschriften 1–6, Zeichenformate, Links, Fußnoten, Listen (verschachtelt, Neustart, Aufgaben, Definitionen), Tabellen mit Titel, Ausrichtung und Beschriftung, Abbildungen, Bild im Text, Code, Zitat, Trennlinie, Inhaltsverzeichnis |
| `funktionen-praesentation.md` | PowerPoint: Titel-, Trenn- und Abschlussfolie, Textebenen, nummerierte Listen mit Startwert, Verkleinern, Tabelle im PTA-Stil mit Titelzeile, längere Tabelle, Code, Bild mit Text, Bild allein, Bildreihe, benannte Layouts mit `---`, Sprechernotizen (`::: notes`) |
| `varianten-dokument.md` | Word-Variante `quer-ohne-deckblatt` mit `sprache: en` und `firma` |
| `varianten-folien.md` | Schulungsvorlage, `titelfolie: ohne-bild`, `sprache: en` |
| `images/` | selbst erzeugte Bilder in den PTA-Farben (keine fremden Rechte); `*-folie.png` sind dieselben Bilder in den Proportionen der Folien-Bildplatzhalter |

```sh
./run.sh generate samples/funktionen --out documents/funktionen
```

Alle Dateien erzeugen ohne Hinweise (`./run.sh generate-samples funktionen` endet mit Code 0)
und bestehen `./run.sh check samples/funktionen --strict`; die Folie „Viel Text wird
verkleinert" ist absichtlich zu voll, darum schaltet `funktionen-praesentation.md` dafür
`pruefung: style-bullets, style-words` ab.
Geteilte „(Forts.)"-Folien zeigt die Funktionsübersicht deshalb nicht; was dabei gemeldet wird,
steht in [docs/anleitung.md](../../docs/anleitung.md), Abschnitt 8.

Noch nicht enthalten, weil noch nicht umgesetzt: PDF, Mermaid, Charts, `:::`-Container,
Alerts, `==Markierung==`, Status-Labels, SVG-Bilder.
