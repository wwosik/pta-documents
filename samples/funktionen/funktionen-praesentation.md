---
vorlage: basis
titelfolie: bild-02
untertitel: "PowerPoint: alles, was der Generator kann"
autor: PTA Documents
ort: Hamburg
datum: 2026-11-06
fusszeile: Funktionsübersicht
sprache: de
---
Text vor der ersten Überschrift wird ignoriert.

# Funktionsübersicht PTA Documents

# Text

## Textebenen der PTA-Vorlage

Ein Absatz ist die Ebene „Einleitungstext".

- Aufzählung, erste Ebene
  - zweite Ebene
    - dritte Ebene

### Eine Subheadline mit ###

Text kann **fett** (in Segoe UI), *kursiv*, ~~durchgestrichen~~, `Code` und ein
[Link](https://www.pta.de) sein.

## Nummerierte Listen

3. Listen dürfen bei einer anderen Zahl beginnen
4. und zählen weiter
   1. auch verschachtelt

> Zitate erscheinen kursiv.

## Viel Text wird verkleinert und fortgesetzt

- Punkt 1: Inhalte, die nicht auf eine Folie passen, werden zuerst verkleinert.
- Punkt 2: Die Untergrenze ist 12 pt.
- Punkt 3: Danach geht es auf einer weiteren Folie weiter.
- Punkt 4: Deren Titel trägt den Zusatz „(Forts.)".
- Punkt 5: Geteilt wird zwischen Punkten, nie mitten in einem Punkt.
- Punkt 6: Verschachtelte Punkte bleiben bei ihrem Elternpunkt.
  - zum Beispiel dieser
- Punkt 7: Besser sind kurze Folien.
- Punkt 8: Diese Folie zeigt das Verhalten absichtlich.
- Punkt 9: Noch ein Punkt.
- Punkt 10: Noch ein Punkt.
- Punkt 11: Noch ein Punkt.
- Punkt 12: Noch ein Punkt.
- Punkt 13: Noch ein Punkt.
- Punkt 14: Noch ein Punkt.
- Punkt 15: Noch ein Punkt.
- Punkt 16: Noch ein Punkt.
- Punkt 17: Noch ein Punkt.
- Punkt 18: Noch ein Punkt.
- Punkt 19: Noch ein Punkt.
- Punkt 20: Noch ein Punkt.
- Punkt 21: Noch ein Punkt.
- Punkt 22: Noch ein Punkt.

# Tabellen und Code

## Tabelle im PTA-Stil

Text vor der Tabelle steht oben.

**Umsatz nach Region**

| Region | Umsatz | Veränderung |
| :----- | -----: | :---------: |
| Nord | 1.200 | +4 % |
| Süd | 950 | -2 % |
| West | 1.480 | +7 % |

Text nach der Tabelle steht unten, zum Beispiel eine Quelle.

## Lange Tabellen werden geteilt

| Nr. | Eintrag | Wert |
| --- | ------- | ---: |
| 1 | Zeile | 10 |
| 2 | Zeile | 20 |
| 3 | Zeile | 30 |
| 4 | Zeile | 40 |
| 5 | Zeile | 50 |
| 6 | Zeile | 60 |
| 7 | Zeile | 70 |
| 8 | Zeile | 80 |
| 9 | Zeile | 90 |
| 10 | Zeile | 100 |
| 11 | Zeile | 110 |
| 12 | Zeile | 120 |
| 13 | Zeile | 130 |
| 14 | Zeile | 140 |

## Code

```python
from pta_documents.generation.pptx.generator import PptxGenerator

PptxGenerator().generate(document, output)
```

# Bilder

## Bild mit Text

Ein Bild und Text ergeben das Layout „Titel, Text und Bild 01"; das Bild füllt seinen Rahmen
und wird beschnitten.

![Balkendiagramm](images/diagramm.png)

## Bild allein

![Breites Bild](images/banner.png)

## Bilder nebeneinander

![Kachel 1](images/kachel-1.png) ![Kachel 2](images/kachel-2.png) ![Kachel 3](images/kachel-3.png)

Bis zu vier Bilder stehen nebeneinander; Text danach steht darunter.

# Layouts

## Zwei Spalten {layout="Titel und Text (zweispaltig)"}

Linke Spalte

- mit Aufzählung

---

Rechte Spalte

- nach der Trennlinie `---`

## Jedes PTA-Layout über seinen Namen {layout="Titel, Text und Bild 03"}

Mit `{layout="…"}` wird jedes der 35 PTA-Layouts gewählt; Text und Bilder füllen dessen
Platzhalter der Reihe nach.

![Kachel 2](images/kachel-2.png)

# Vielen Dank! {.closing}
