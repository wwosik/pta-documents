---
# Alle Schlüssel, die ein Word-Dokument kennt (Kommentarzeilen mit # sind erlaubt).
vorlage: hoch
titel: Funktionsübersicht PTA Documents
untertitel: "Word: alles, was der Generator kann"
autor: PTA Documents
ort: Hamburg
datum: 06.11.2026
firma: PTA IT-Beratung
sprache: de
inhaltsverzeichnis: ja
---
# Überschriften und Absätze

Jedes `#` ist ein Kapitel mit „Überschrift 1" und wird von Word nummeriert. Der Titel kommt
ausschließlich aus dem Front Matter und steht auf dem Deckblatt.

## Überschrift 2

Ein normaler Absatz in „Standard". Ein Zeilenumbruch
innerhalb des Absatzes wird zu einem Leerzeichen; ein harter Umbruch mit Backslash\
beginnt eine neue Zeile im selben Absatz.

### Überschrift 3

Die dritte Ebene ist ebenfalls nummeriert.

#### Zwischenüberschrift ab Ebene 4

Ab `####` gibt es keine Nummer mehr, sondern die PTA-Formatvorlage „Zwischenüberschrift".

##### Auch Ebene 5 und 6

landen in der Zwischenüberschrift.

**Ein Absatz, der nur aus Fettdruck besteht, wird „Standard fett".**

# Zeichenformate und Links

Text kann **fett**, *kursiv*, ***fett und kursiv***, ~~durchgestrichen~~ oder `Inline-Code`
sein. Absolute Links werden echte Hyperlinks: [PTA](https://www.pta.de) oder
[E-Mail](mailto:info@example.org). Relative Links wie [diese Datei](README.md) bleiben Text.

Fußnoten werden echte Word-Fußnoten.[^erste] Mehrere sind möglich.[^zweite]

Ein kleines Bild mitten im Text ![grünes Symbol](images/symbol.png) bleibt im Absatz.

# Listen

- Aufzählung, erste Ebene (blaues Quadrat)
  - zweite Ebene (Strich)
    - dritte Ebene
- noch ein Punkt der ersten Ebene

  mit einem zweiten Absatz im selben Punkt

1. Nummerierte Liste
2. zweiter Schritt
   - eine Aufzählung darin
3. dritter Schritt

Ein Absatz unterbricht die Liste — die nächste beginnt wieder bei 1:

1. neu bei eins
2. und weiter

Aufgabenlisten:

- [x] erledigt
- [ ] offen

Definitionslisten:

Formatvorlage
: Eine benannte Formatierung der PTA-Vorlage.

Front Matter
: Der Kopf des Dokuments zwischen zwei `---`-Zeilen.

# Tabellen

**Tabellentitel: ein fetter Absatz direkt vor der Tabelle**

| Spalte links | Mitte | Zahlen rechts |
| :----------- | :---: | ------------: |
| Text mit **fett** | zentriert | 1.234,50 € |
| Zeile zwei | – | 42 % |
| eine längere Zelle, deren Text umbricht, damit die Spaltenbreiten sichtbar werden | x | 7 |

Tabelle: Beschriftung unter der Tabelle („Tabelle: …" direkt danach)

Eine zweite Tabelle ohne Titel und ohne Beschriftung:

| A | B |
| --- | --- |
| 1 | 2 |

# Bilder

Ein Bild allein im Absatz bekommt eine Abbildungsbeschriftung aus seinem Titel:

![Balkendiagramm](images/diagramm.png "Ein selbst erzeugtes Balkendiagramm in den PTA-Farben")

Ohne Titel dient der Alt-Text als Beschriftung:

![Breites Bild, auf Satzspiegelbreite verkleinert](images/banner.png)

# Code, Zitat und Trennlinie

```python
from pta_documents.generation.docx.generator import DocxGenerator

DocxGenerator().generate(document, output)
```

> Ein Zitat wird in die Formatvorlage „Zitat" gesetzt
> und eingerückt.

Nach dieser Linie folgt das Ende.

---

Ende der Funktionsübersicht.

[^erste]: Fußnotentext in „Fußnotentext", mit **Formatierung** und [Link](https://example.org).
[^zweite]: Die zweite Fußnote.
