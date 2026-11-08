---
vorlage: basis
titelfolie: bild-02
untertitel: "PowerPoint: alles, was der Generator kann"
autor: PTA Documents
ort: Hamburg
datum: 2026-11-06
fusszeile: Funktionsübersicht
sprache: de
typografie: ja
syntaxhervorhebung: ja
pruefung: style-bullets, style-words
status.success: Erledigt
status.info: In Prüfung
status.warning: Als Nächstes
status.danger: Blockiert
status.neutral: Offen
---
Text vor der ersten Überschrift wird ignoriert.

# Funktionsübersicht PTA Documents

::: notes
Begrüßen und sagen, dass jede Folie eine Funktion des Generators zeigt. Den Markdown-Quelltext
jeder Folie zeigt ihre Notizenseite.
:::

# Text

## Textebenen der PTA-Vorlage

Ein Absatz ist die Ebene „Einleitungstext".

- Aufzählung, erste Ebene
  - zweite Ebene
    - dritte Ebene

### Eine Subheadline mit ###

Text kann **fett** (in Segoe UI), *kursiv*, ~~durchgestrichen~~, `Code` und ein
[Link](https://www.pta.de) sein.

::: notes
Die Ebenen kommen aus dem Folienmaster der PTA-Vorlage. Sprechernotizen schreibt man in einen
Block `::: notes` unter die Überschrift der Folie:

- Absätze und Listen bleiben erhalten,
- ebenso **fett**, *kursiv*, `Code` und [Links](https://www.pta.de).
:::

:::: notes
```markdown
## Textebenen der PTA-Vorlage

Ein Absatz ist die Ebene „Einleitungstext".

- Aufzählung, erste Ebene
  - zweite Ebene
    - dritte Ebene

### Eine Subheadline mit ###

Text kann **fett** (in Segoe UI), *kursiv*, ~~durchgestrichen~~, `Code` und ein
[Link](https://www.pta.de) sein.

::: notes
Die Ebenen kommen aus dem Folienmaster der PTA-Vorlage. Sprechernotizen schreibt man in einen
Block `::: notes` unter die Überschrift der Folie:

- Absätze und Listen bleiben erhalten,
- ebenso **fett**, *kursiv*, `Code` und [Links](https://www.pta.de).
:::
```
::::

## Nummerierte Listen

3. Listen dürfen bei einer anderen Zahl beginnen
4. und zählen weiter
   1. auch verschachtelt

> Zitate erscheinen kursiv.

:::: notes
```markdown
## Nummerierte Listen

3. Listen dürfen bei einer anderen Zahl beginnen
4. und zählen weiter
   1. auch verschachtelt

> Zitate erscheinen kursiv.
```
::::

## Viel Text wird verkleinert

- Punkt 1: Inhalte, die nicht in voller Größe auf eine Folie passen, werden verkleinert.
- Punkt 2: Die Untergrenze ist 12 pt.
- Punkt 3: Passt es auch dann nicht, geht es auf einer weiteren Folie mit „(Forts.)" weiter.
- Punkt 4: Das meldet `./run.sh generate` als Hinweis `slide-split`.
- Punkt 5: Geteilt wird zwischen Punkten, nie mitten in einem Punkt.
- Punkt 6: Verschachtelte Punkte bleiben bei ihrem Elternpunkt.
  - zum Beispiel dieser
- Punkt 7: Besser sind kurze Folien.
- Punkt 8: Diese Folie zeigt das Verkleinern absichtlich.
- Punkt 9: Noch ein Punkt.
- Punkt 10: Noch ein Punkt.
- Punkt 11: Noch ein Punkt.
- Punkt 12: Noch ein Punkt.

:::: notes
```markdown
## Viel Text wird verkleinert

- Punkt 1: Inhalte, die nicht in voller Größe auf eine Folie passen, werden verkleinert.
- Punkt 2: Die Untergrenze ist 12 pt.
- Punkt 3: Passt es auch dann nicht, geht es auf einer weiteren Folie mit „(Forts.)" weiter.
- Punkt 4: Das meldet `./run.sh generate` als Hinweis `slide-split`.
- Punkt 5: Geteilt wird zwischen Punkten, nie mitten in einem Punkt.
- Punkt 6: Verschachtelte Punkte bleiben bei ihrem Elternpunkt.
  - zum Beispiel dieser
- Punkt 7: Besser sind kurze Folien.
- Punkt 8: Diese Folie zeigt das Verkleinern absichtlich.
- Punkt 9: Noch ein Punkt.
- Punkt 10: Noch ein Punkt.
- Punkt 11: Noch ein Punkt.
- Punkt 12: Noch ein Punkt.
```
::::

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

:::: notes
```markdown
## Tabelle im PTA-Stil

Text vor der Tabelle steht oben.

**Umsatz nach Region**

| Region | Umsatz | Veränderung |
| :----- | -----: | :---------: |
| Nord | 1.200 | +4 % |
| Süd | 950 | -2 % |
| West | 1.480 | +7 % |

Text nach der Tabelle steht unten, zum Beispiel eine Quelle.
```
::::

## Längere Tabelle

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

Längere Tabellen werden mit wiederholter Kopfzeile geteilt (Hinweis `slide-split`).

:::: notes
```markdown
## Längere Tabelle

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

Längere Tabellen werden mit wiederholter Kopfzeile geteilt (Hinweis `slide-split`).
```
::::

## Code

```python
from pta_documents.generation.pptx.generator import PptxGenerator

# Farbig im PTA-Schema, wenn die Sprache angegeben ist
with open("folien.pptx", "wb") as output:
    PptxGenerator().generate(document, output)
```

:::: notes
````markdown
## Code

```python
from pta_documents.generation.pptx.generator import PptxGenerator

# Farbig im PTA-Schema, wenn die Sprache angegeben ist
with open("folien.pptx", "wb") as output:
    PptxGenerator().generate(document, output)
```
````
::::

# Bilder

## Bild mit Text

Ein Bild und Text ergeben das Layout „Titel, Text und Bild 01"; das Bild füllt seinen Rahmen
und wird beschnitten. Dieses Bild hat schon die Proportionen des Rahmens.

![Balkendiagramm](images/diagramm-folie.png)

:::: notes
```markdown
## Bild mit Text

Ein Bild und Text ergeben das Layout „Titel, Text und Bild 01"; das Bild füllt seinen Rahmen
und wird beschnitten. Dieses Bild hat schon die Proportionen des Rahmens.

![Balkendiagramm](images/diagramm-folie.png)
```
::::

## Bild allein

![Breites Bild](images/banner-folie.png)

:::: notes
```markdown
## Bild allein

![Breites Bild](images/banner-folie.png)
```
::::

## SVG-Grafik

Eine SVG-Grafik füllt ihren Rahmen wie jedes Bild und bleibt in PowerPoint in jeder Größe
scharf; ältere Versionen zeigen ein Bild in doppelter Auflösung.

![Ablauf in drei Schritten](images/plan-folie.svg)

:::: notes
```markdown
## SVG-Grafik

Eine SVG-Grafik füllt ihren Rahmen wie jedes Bild und bleibt in PowerPoint in jeder Größe
scharf; ältere Versionen zeigen ein Bild in doppelter Auflösung.

![Ablauf in drei Schritten](images/plan-folie.svg)
```
::::

## Bilder nebeneinander

![Kachel 1](images/kachel-1.png) ![Kachel 2](images/kachel-2.png) ![Kachel 3](images/kachel-3.png)

Bis zu vier Bilder stehen nebeneinander; Text danach steht darunter.

:::: notes
```markdown
## Bilder nebeneinander

![Kachel 1](images/kachel-1.png) ![Kachel 2](images/kachel-2.png) ![Kachel 3](images/kachel-3.png)

Bis zu vier Bilder stehen nebeneinander; Text danach steht darunter.
```
::::

# Layouts

## Zwei Spalten {layout="Titel und Text (zweispaltig)"}

Linke Spalte

- mit Aufzählung

---

Rechte Spalte

- nach der Trennlinie `---`

:::: notes
```markdown
## Zwei Spalten {layout="Titel und Text (zweispaltig)"}

Linke Spalte

- mit Aufzählung

---

Rechte Spalte

- nach der Trennlinie `---`
```
::::

## Jedes PTA-Layout über seinen Namen {layout="Titel, Text und Bild 03"}

Mit `{layout="…"}` wird jedes der 35 PTA-Layouts gewählt; Text und Bilder füllen dessen
Platzhalter der Reihe nach.

![Kachel 2](images/kachel-2.png)

:::: notes
```markdown
## Jedes PTA-Layout über seinen Namen {layout="Titel, Text und Bild 03"}

Mit `{layout="…"}` wird jedes der 35 PTA-Layouts gewählt; Text und Bilder füllen dessen
Platzhalter der Reihe nach.

![Kachel 2](images/kachel-2.png)
```
::::

# Flow-Folien

## Karten {kicker="Container"}

::: cards
### Die Konfiguration ist zu kompliziert
**26 Tabellen**

für 12 Arten von Regeln

### Große Fahrpläne sind zu langsam
**3,2 GB**

Speicher je Fahrplan bei 5.000 Halten
:::

:::: notes
```markdown
## Karten {kicker="Container"}

::: cards
### Die Konfiguration ist zu kompliziert
**26 Tabellen**

für 12 Arten von Regeln

### Große Fahrpläne sind zu langsam
**3,2 GB**

Speicher je Fahrplan bei 5.000 Halten
:::
```
::::

## Zeilen {kicker="Container"}

::: rows
- **Wirklich große Fahrpläne** – Dokumente werden seitenweise geschrieben
- **Mehr Flexibilität** – neue Preislogik ist eine Formel, keine Tabelle
- **Reproduzierbare Ergebnisse** – jede Berechnung hält ihre Eingaben fest
:::

:::: notes
```markdown
## Zeilen {kicker="Container"}

::: rows
- **Wirklich große Fahrpläne** – Dokumente werden seitenweise geschrieben
- **Mehr Flexibilität** – neue Preislogik ist eine Formel, keine Tabelle
- **Reproduzierbare Ergebnisse** – jede Berechnung hält ihre Eingaben fest
:::
```
::::

## Flächen {kicker="Container"}

:::: panel
**Unterwegs behoben**

::: cards
- **Sperren** – der Join zählt wieder ohne Sperre
- **Duplikate** – der Export-Wächter filtert jede Zeile
:::
::::

::: panel dark
### Jedes Ergebnis hat ein Manifest
Buchungsrevision, Regelversion und Parameterrevision.
:::

::::: notes
```markdown
## Flächen {kicker="Container"}

:::: panel
**Unterwegs behoben**

::: cards
- **Sperren** – der Join zählt wieder ohne Sperre
- **Duplikate** – der Export-Wächter filtert jede Zeile
:::
::::

::: panel dark
### Jedes Ergebnis hat ein Manifest
Buchungsrevision, Regelversion und Parameterrevision.
:::
```
:::::

## Aussage auf dunklem Grund {.dark kicker="Aussage"}

::: statement
Ein Broker garantiert die Zustellung mindestens einmal – nicht die Verarbeitung höchstens einmal.

Der Wettlauf im alten System geschah mit einem Broker.
:::

:::: notes
```markdown
## Aussage auf dunklem Grund {.dark kicker="Aussage"}

::: statement
Ein Broker garantiert die Zustellung mindestens einmal – nicht die Verarbeitung höchstens einmal.

Der Wettlauf im alten System geschah mit einem Broker.
:::
```
::::

## Vorher und nachher

::: columns
**Heute**

- 26 Tabellen für 12 Arten von Regeln
- Sperren im Join

---

**Mit Hafen**

- Ein Dokument je Revision
- Keine Datenbank, kein Message Broker
:::

:::: notes
```markdown
## Vorher und nachher

::: columns
**Heute**

- 26 Tabellen für 12 Arten von Regeln
- Sperren im Join

---

**Mit Hafen**

- Ein Dokument je Revision
- Keine Datenbank, kein Message Broker
:::
```
::::

## Spalten, Kommentar und Fazit {kicker="PTA"}

:::: columns 1:2
**Vier Wochen** lang rechnen altes System und Hafen dieselben Buchungen.

---

| Woche | Gleiche Ergebnisse |
| ----- | ------------------ |
| 1 | 91 % |
| 2 | 97 % |
| 3 | 99 % |

::: comment
Ziel: 100 %
:::
::::

::: conclusion
Erst wenn der Schattenlauf vier Wochen lang gleiche Ergebnisse liefert, wird umgestellt.
:::

::::: notes
```markdown
## Spalten, Kommentar und Fazit {kicker="PTA"}

:::: columns 1:2
**Vier Wochen** lang rechnen altes System und Hafen dieselben Buchungen.

---

| Woche | Gleiche Ergebnisse |
| ----- | ------------------ |
| 1 | 91 % |
| 2 | 97 % |
| 3 | 99 % |

::: comment
Ziel: 100 %
:::
::::

::: conclusion
Erst wenn der Schattenlauf vier Wochen lang gleiche Ergebnisse liefert, wird umgestellt.
:::
```
:::::

## Hinweise {kicker="Alerts"}

> [!NOTE]
> **Hinweis und Tipp** stehen auf einer Fläche mit blauem Balken.

> [!TIP]
> Ein Tipp sieht aus wie ein Hinweis.

:::: notes
```markdown
## Hinweise {kicker="Alerts"}

> [!NOTE]
> **Hinweis und Tipp** stehen auf einer Fläche mit blauem Balken.

> [!TIP]
> Ein Tipp sieht aus wie ein Hinweis.
```
::::

## Wichtige Hinweise {kicker="Alerts"}

> [!IMPORTANT]
> **Wichtig, Warnung und Vorsicht** haben einen gelben Balken.

> [!WARNING]
> Eine Warnung.

> [!CAUTION]
> Ein Grund zur Vorsicht.

:::: notes
```markdown
## Wichtige Hinweise {kicker="Alerts"}

> [!IMPORTANT]
> **Wichtig, Warnung und Vorsicht** haben einen gelben Balken.

> [!WARNING]
> Eine Warnung.

> [!CAUTION]
> Ein Grund zur Vorsicht.
```
::::

## Markierung und farbige Wörter {kicker="Text"}

| Status | Weiter durch |
| ------ | ------------ |
| Angelegt | System |
| ==Wartet auf Freigabe== | Mensch |

Zeilen in der ==Hervorhebungsfarbe== brauchen einen Menschen. Stand: [im Plan]{.success},
[unter Beobachtung]{.warning}, [gestoppt]{.danger}, [zur Kenntnis]{.info},
[ohne Bewertung]{.neutral}.

:::: notes
```markdown
## Markierung und farbige Wörter {kicker="Text"}

| Status | Weiter durch |
| ------ | ------------ |
| Angelegt | System |
| ==Wartet auf Freigabe== | Mensch |

Zeilen in der ==Hervorhebungsfarbe== brauchen einen Menschen. Stand: [im Plan]{.success},
[unter Beobachtung]{.warning}, [gestoppt]{.danger}, [zur Kenntnis]{.info},
[ohne Bewertung]{.neutral}.
```
::::

## Status-Labels {kicker="Tabellen"}

| Teil | Status |
| ---- | ------ |
| Erfassung | `Erledigt` |
| Prüfung | `In Prüfung` |
| Engine | `Als Nächstes` |
| Schnittstelle | `Blockiert` |
| Archiv | `Offen` |

:::: notes
```markdown
## Status-Labels {kicker="Tabellen"}

| Teil | Status |
| ---- | ------ |
| Erfassung | `Erledigt` |
| Prüfung | `In Prüfung` |
| Engine | `Als Nächstes` |
| Schnittstelle | `Blockiert` |
| Archiv | `Offen` |
```

Die Texte stehen im Front Matter: `status.success: Erledigt` usw.
::::

# PTA-Folienarten

## Agenda {.agenda}

1. Ausgangslage
2. Zielbild
3. Umsetzung

:::: notes
```markdown
## Agenda {.agenda}

1. Ausgangslage
2. Zielbild
3. Umsetzung
```
::::

## Die Migration ist ohne Ausfall möglich {.interim}

:::: notes
```markdown
## Die Migration ist ohne Ausfall möglich {.interim}
```
::::

## Was man nicht messen kann, kann man nicht lenken {.quote}

— Peter Drucker, Ökonom

:::: notes
```markdown
## Was man nicht messen kann, kann man nicht lenken {.quote}

— Peter Drucker, Ökonom
```
::::

## Ihre Ansprechpartner {.contact}

### Erika Mustermann

Projektleiterin
erika.mustermann@example.org
+49 621 12345-0

### Max Mustermann

Berater
max.mustermann@example.org

:::: notes
```markdown
## Ihre Ansprechpartner {.contact}

### Erika Mustermann

Projektleiterin
erika.mustermann@example.org
+49 621 12345-0

### Max Mustermann

Berater
max.mustermann@example.org
```
::::

# Vielen Dank! {.closing}

::: notes
Nach Fragen fragen.
:::

:::: notes
```markdown
# Vielen Dank! {.closing}
```
::::
