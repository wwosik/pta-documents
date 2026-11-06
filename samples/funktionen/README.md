# Beispiel: Funktionsübersicht

Zeigt alles, was die Generatoren heute können — jede Datei deckt einen Bereich ab.

| Datei | Zeigt |
| ----- | ----- |
| `funktionen-bericht.md` | Word: alle Front-Matter-Schlüssel, Überschriften 1–6, Zeichenformate, Links, Fußnoten, Listen (verschachtelt, Neustart, Aufgaben, Definitionen), Tabellen mit Titel, Ausrichtung und Beschriftung, Abbildungen, Bild im Text, Code, Zitat, Trennlinie, Inhaltsverzeichnis |
| `funktionen-praesentation.md` | PowerPoint: Titel-, Trenn- und Abschlussfolie, Textebenen, nummerierte Listen mit Startwert, Verkleinern und „(Forts.)", Tabelle im PTA-Stil mit Titelzeile, geteilte Tabelle, Code, Bild mit Text, Bild allein, Bildreihe, benannte Layouts mit `---` |
| `varianten-dokument.md` | Word-Variante `quer-ohne-deckblatt` mit `sprache: en` und `firma` |
| `varianten-folien.md` | Schulungsvorlage, `titelfolie: ohne-bild`, `sprache: en` |
| `images/` | selbst erzeugte Bilder in den PTA-Farben (keine fremden Rechte) |

```sh
./run.sh generate samples/funktionen --out documents/funktionen
```

Noch nicht enthalten, weil noch nicht umgesetzt: PDF, Mermaid, Charts, `:::`-Container,
Alerts, `==Markierung==`, Status-Labels, SVG-Bilder.
