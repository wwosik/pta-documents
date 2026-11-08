## Funktionsübersicht PTA Documents

PTA Documents, Hamburg, 06.11.2026

PowerPoint: alles, was der Generator kann

::: notes

Begrüßen und sagen, dass jede Folie eine Funktion des Generators zeigt. Den Markdown-Quelltext jeder Folie zeigt ihre Notizenseite.

:::

## Text

01

## Textebenen der PTA-Vorlage

Ein Absatz ist die Ebene „Einleitungstext“.

Aufzählung, erste Ebene

zweite Ebene

dritte Ebene

Eine Subheadline mit

Text kann fett (in Segoe UI), kursiv, durchgestrichen, Code und ein Link sein.

:::: notes

Die Ebenen kommen aus dem Folienmaster der PTA-Vorlage. Sprechernotizen schreibt man in einen Block ::: notes unter die Überschrift der Folie:

- Absätze und Listen bleiben erhalten,

- ebenso fett, kursiv, Code und Links.

```
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

Listen dürfen bei einer anderen Zahl beginnen

und zählen weiter

auch verschachtelt

Zitate erscheinen kursiv.

::: notes

```
## Nummerierte Listen

3. Listen dürfen bei einer anderen Zahl beginnen
4. und zählen weiter
   1. auch verschachtelt

> Zitate erscheinen kursiv.
```

:::

## Viel Text wird verkleinert

Punkt 1: Inhalte, die nicht in voller Größe auf eine Folie passen, werden verkleinert.

Punkt 2: Die Untergrenze ist 12 pt.

Punkt 3: Passt es auch dann nicht, geht es auf einer weiteren Folie mit „(Forts.)“ weiter.

Punkt 4: Das meldet ./run.sh generate als Hinweis slide-split.

Punkt 5: Geteilt wird zwischen Punkten, nie mitten in einem Punkt.

Punkt 6: Verschachtelte Punkte bleiben bei ihrem Elternpunkt.

zum Beispiel dieser

Punkt 7: Besser sind kurze Folien.

Punkt 8: Diese Folie zeigt das Verkleinern absichtlich.

Punkt 9: Noch ein Punkt.

Punkt 10: Noch ein Punkt.

Punkt 11: Noch ein Punkt.

Punkt 12: Noch ein Punkt.

::: notes

```
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

:::

## Tabellen und Code

02

## Tabelle im PTA-Stil

Text vor der Tabelle steht oben.

| Umsatz nach Region |  |  |
| --- | --- | --- |
| Region | Umsatz | Veränderung |
| Nord | 1.200 | +4 % |
| Süd | 950 | -2 % |
| West | 1.480 | +7 % |

Text nach der Tabelle steht unten, zum Beispiel eine Quelle.

::: notes

```
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

:::

## Längere Tabelle

| Nr. | Eintrag | Wert |
| --- | --- | --- |
| 1 | Zeile | 10 |
| 2 | Zeile | 20 |
| 3 | Zeile | 30 |
| 4 | Zeile | 40 |
| 5 | Zeile | 50 |
| 6 | Zeile | 60 |
| 7 | Zeile | 70 |
| 8 | Zeile | 80 |
| 9 | Zeile | 90 |

Längere Tabellen werden mit wiederholter Kopfzeile geteilt (Hinweis slide-split).

::: notes

```
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

:::

## Code

from pta_documents.generation.pptx.generator import PptxGenerator

# Farbig im PTA-Schema, wenn die Sprache angegeben ist

with open("folien.pptx", "wb") as output:

PptxGenerator().generate(document, output)

::: notes

````
## Code

```python
from pta_documents.generation.pptx.generator import PptxGenerator

# Farbig im PTA-Schema, wenn die Sprache angegeben ist
with open("folien.pptx", "wb") as output:
    PptxGenerator().generate(document, output)
```
````

:::

## Bilder

03

## Bild mit Text

![Balkendiagramm](images/image10.png)

Ein Bild und Text ergeben das Layout „Titel, Text und Bild 01“; das Bild füllt seinen Rahmen und wird beschnitten. Dieses Bild hat schon die Proportionen des Rahmens.

::: notes

```
## Bild mit Text

Ein Bild und Text ergeben das Layout „Titel, Text und Bild 01"; das Bild füllt seinen Rahmen
und wird beschnitten. Dieses Bild hat schon die Proportionen des Rahmens.

![Balkendiagramm](images/diagramm-folie.png)
```

:::

## Bild allein

![Breites Bild](images/image11.png)

::: notes

```
## Bild allein

![Breites Bild](images/banner-folie.png)
```

:::

## SVG-Grafik

![Ablauf in drei Schritten](images/image12.png)

Eine SVG-Grafik füllt ihren Rahmen wie jedes Bild und bleibt in PowerPoint in jeder Größe scharf; ältere Versionen zeigen ein Bild in doppelter Auflösung.

::: notes

```
## SVG-Grafik

Eine SVG-Grafik füllt ihren Rahmen wie jedes Bild und bleibt in PowerPoint in jeder Größe
scharf; ältere Versionen zeigen ein Bild in doppelter Auflösung.

![Ablauf in drei Schritten](images/plan-folie.svg)
```

:::

## Bilder nebeneinander

![Kachel 1](images/image14.png)

![Kachel 2](images/image15.png)

![Kachel 3](images/image16.png)

Bis zu vier Bilder stehen nebeneinander; Text danach steht darunter.

::: notes

```
## Bilder nebeneinander

![Kachel 1](images/kachel-1.png) ![Kachel 2](images/kachel-2.png) ![Kachel 3](images/kachel-3.png)

Bis zu vier Bilder stehen nebeneinander; Text danach steht darunter.
```

:::

## Layouts

04

## Zwei Spalten

Linke Spalte

mit Aufzählung

Rechte Spalte

nach der Trennlinie ---

::: notes

```
## Zwei Spalten {layout="Titel und Text (zweispaltig)"}

Linke Spalte

- mit Aufzählung

---

Rechte Spalte

- nach der Trennlinie `---`
```

:::

## Jedes PTA-Layout über seinen Namen

![Kachel 2](images/image15.png)

Mit {layout="…"} wird jedes der 35 PTA-Layouts gewählt; Text und Bilder füllen dessen Platzhalter der Reihe nach.

::: notes

```
## Jedes PTA-Layout über seinen Namen {layout="Titel, Text und Bild 03"}

Mit `{layout="…"}` wird jedes der 35 PTA-Layouts gewählt; Text und Bilder füllen dessen
Platzhalter der Reihe nach.

![Kachel 2](images/kachel-2.png)
```

:::

## Flow-Folien

05

## Karten

Container

26 Tabellen

Die Konfiguration ist zu kompliziert

für 12 Arten von Regeln

3,2 GB

Große Fahrpläne sind zu langsam

Speicher je Fahrplan bei 5.000 Halten

:::: notes

```
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

## Zeilen

Container

Wirklich große Fahrpläne

Dokumente werden seitenweise geschrieben

Mehr Flexibilität

neue Preislogik ist eine Formel, keine Tabelle

Reproduzierbare Ergebnisse

jede Berechnung hält ihre Eingaben fest

:::: notes

```
## Zeilen {kicker="Container"}

::: rows
- **Wirklich große Fahrpläne** – Dokumente werden seitenweise geschrieben
- **Mehr Flexibilität** – neue Preislogik ist eine Formel, keine Tabelle
- **Reproduzierbare Ergebnisse** – jede Berechnung hält ihre Eingaben fest
:::
```

::::

## Flächen

Container

Unterwegs behoben

Sperren

der Join zählt wieder ohne Sperre

Duplikate

der Export-Wächter filtert jede Zeile

Jedes Ergebnis hat ein Manifest

Buchungsrevision, Regelversion und Parameterrevision.

::::: notes

```
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

## Aussage auf dunklem Grund

Aussage

Ein Broker garantiert die Zustellung mindestens einmal – nicht die Verarbeitung höchstens einmal.

Der Wettlauf im alten System geschah mit einem Broker.

:::: notes

```
## Aussage auf dunklem Grund {.dark kicker="Aussage"}

::: statement
Ein Broker garantiert die Zustellung mindestens einmal – nicht die Verarbeitung höchstens einmal.

Der Wettlauf im alten System geschah mit einem Broker.
:::
```

::::

## Vorher und nachher

Heute

26 Tabellen für 12 Arten von Regeln

Sperren im Join

Mit Hafen

Ein Dokument je Revision

Keine Datenbank, kein Message Broker

:::: notes

```
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

## Spalten, Kommentar und Fazit

PTA

Vier Wochen lang rechnen altes System und Hafen dieselben Buchungen.

| Woche | Gleiche Ergebnisse |
| --- | --- |
| 1 | 91 % |
| 2 | 97 % |
| 3 | 99 % |

Ziel: 100 %

Erst wenn der Schattenlauf vier Wochen lang gleiche Ergebnisse liefert, wird umgestellt.

::::: notes

```
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

## Hinweise

Alerts

Hinweis und Tipp stehen auf einer Fläche mit blauem Balken.

Ein Tipp sieht aus wie ein Hinweis.

::: notes

```
## Hinweise {kicker="Alerts"}

> [!NOTE]
> **Hinweis und Tipp** stehen auf einer Fläche mit blauem Balken.

> [!TIP]
> Ein Tipp sieht aus wie ein Hinweis.
```

:::

## Wichtige Hinweise

Alerts

Wichtig, Warnung und Vorsicht haben einen gelben Balken.

Eine Warnung.

Ein Grund zur Vorsicht.

::: notes

```
## Wichtige Hinweise {kicker="Alerts"}

> [!IMPORTANT]
> **Wichtig, Warnung und Vorsicht** haben einen gelben Balken.

> [!WARNING]
> Eine Warnung.

> [!CAUTION]
> Ein Grund zur Vorsicht.
```

:::

## Markierung und farbige Wörter

Text

| Status | Weiter durch |
| --- | --- |
| Angelegt | System |
| Wartet auf Freigabe | Mensch |

Zeilen in der Hervorhebungsfarbe brauchen einen Menschen. Stand: im Plan, unter Beobachtung, gestoppt, zur Kenntnis, ohne Bewertung.

::: notes

```
## Markierung und farbige Wörter {kicker="Text"}

| Status | Weiter durch |
| ------ | ------------ |
| Angelegt | System |
| ==Wartet auf Freigabe== | Mensch |

Zeilen in der ==Hervorhebungsfarbe== brauchen einen Menschen. Stand: [im Plan]{.success},
[unter Beobachtung]{.warning}, [gestoppt]{.danger}, [zur Kenntnis]{.info},
[ohne Bewertung]{.neutral}.
```

:::

## Status-Labels

Tabellen

| Teil | Status |
| --- | --- |
| Erfassung | ● Erledigt |
| Prüfung | ● In Prüfung |
| Engine | ● Als Nächstes |
| Schnittstelle | ● Blockiert |
| Archiv | ● Offen |

::: notes

```
## Status-Labels {kicker="Tabellen"}

| Teil | Status |
| ---- | ------ |
| Erfassung | `Erledigt` |
| Prüfung | `In Prüfung` |
| Engine | `Als Nächstes` |
| Schnittstelle | `Blockiert` |
| Archiv | `Offen` |
```

Die Texte stehen im Front Matter: status.success: Erledigt usw.

:::

## Diagramme

06

## Balkendiagramm

Aufträge je Quartal

Mio. EUR

Quelle: Vertrieb, Beispielzahlen

::: notes

````
## Balkendiagramm

```chart
type: bar
title: Aufträge je Quartal
unit: Mio. EUR
source: Quelle: Vertrieb, Beispielzahlen
---
Quartal, Plan, Ist
Q1, 12.5, 13.2
Q2, 11.8, 12.1
Q3, 12.5, 14
Q4, 13, 13.6
```
````

:::

## Linien mit Text davor

Antwortzeit

ms

Ein chart-Block wird ein echtes Diagramm; „Daten bearbeiten“ öffnet seine Tabelle.

::: notes

````
## Linien mit Text davor

Ein `chart`-Block wird ein echtes Diagramm; „Daten bearbeiten“ öffnet seine Tabelle.

```chart
type: line
title: Antwortzeit
unit: ms
---
Monat; Median; 95. Perzentil
Jan; 120,5; 310
Feb; 118; 295,5
Mär; 101; 260
Apr; 96,5;
Mai; 92; 230
```
````

:::

## Gestapelte Flächen mit Text danach

Fahrten je Tag

Tsd.

Mit stacked: true liegen Flächen oder Balken übereinander.

::: notes

````
## Gestapelte Flächen mit Text danach

```chart
type: area
stacked: true
title: Fahrten je Tag
unit: Tsd.
---
Tag, Bus, Bahn
Mo, 41, 55
Di, 43, 57
Mi, 42, 58
Do, 44, 60
Fr, 47, 63
```

Mit `stacked: true` liegen Flächen oder Balken übereinander.
````

:::

## Zwei Diagramme

Umsatz

Mio. EUR

Marge

%

:::: notes

````
## Zwei Diagramme

::: columns
```chart
title: Umsatz
unit: Mio. EUR
---
Jahr, Umsatz
2024, 41
2025, 45
```

---

```chart
type: line
title: Marge
unit: %
---
Jahr, Marge
2024, 8.5
2025, 9.1
```
:::
````

::::

## Finanzdiagramme

07

## Finanzdiagramm: Entwicklung

Monat für Monat oben, kumuliert unten; gestrichelt ist die Prognose.

::: notes

````
## Finanzdiagramm: Entwicklung

Monat für Monat oben, kumuliert unten; gestrichelt ist die Prognose.

```financial-chart
{
  "type": "development",
  "title": "Aufträge",
  "period": "April 2026",
  "lastActual": 3,
  "referenceRate": 0.05,
  "changeAtPeriod": 0.048,
  "changeAtYearEnd": 0.035,
  "estimates": [
    {"month": 5, "label": "Schätzung", "value": 103}
  ],
  "months": [
    {"label": "Jan", "previous": 14.2, "current": 15.0, "projection": 14.8, "previousCumulative": 14.2, "currentCumulative": 15.0, "projectionCumulative": 14.8, "reference": 14.9, "referenceCumulative": 14.9},
    {"label": "Feb", "previous": 15.1, "current": 15.9, "projection": 15.6, "previousCumulative": 29.3, "currentCumulative": 30.9, "projectionCumulative": 30.4, "reference": 15.9, "referenceCumulative": 30.8},
    {"label": "Mär", "previous": 17.8, "current": 18.1, "projection": 18.0, "previousCumulative": 47.1, "currentCumulative": 49.0, "projectionCumulative": 48.4, "reference": 18.7, "referenceCumulative": 49.5},
    {"label": "Apr", "previous": 16.4, "current": 17.9, "projection": 17.5, "previousCumulative": 63.5, "currentCumulative": 66.9, "projectionCumulative": 65.9, "reference": 17.2, "referenceCumulative": 66.7},
    {"label": "Mai", "previous": 17.0, "current": null, "projection": 18.6, "previousCumulative": 80.5, "currentCumulative": null, "projectionCumulative": 84.5, "reference": 17.9, "referenceCumulative": 84.5},
    {"label": "Jun", "previous": 18.3, "current": null, "projection": 19.1, "previousCumulative": 98.8, "currentCumulative": null, "projectionCumulative": 103.6, "reference": 19.2, "referenceCumulative": 103.7}
  ],
  "options": {"unit": "Mio. EUR"}
}
```
````

:::

## Finanzdiagramm: Wachstum je Zeile

::: notes

````
## Finanzdiagramm: Wachstum je Zeile

```financial-chart
{
  "type": "growth-by-row",
  "title": "Wachstum je Region",
  "period": "April 2026",
  "rows": [
    {"label": "Nord", "change": 0.081, "reference": 0.05},
    {"label": "Süd", "change": 0.032, "reference": 0.05, "emphasised": true},
    {"label": "Ost", "change": -0.021, "reference": 0.04},
    {"label": "West", "change": 0.124, "reference": 0.06}
  ],
  "overall": {"change": 0.052, "reference": 0.05},
  "options": {"width": 600}
}
```
````

:::

## Finanzdiagramm: Ist gegen Plan

::: notes

````
## Finanzdiagramm: Ist gegen Plan

```financial-chart
{
  "type": "actual-vs-reference",
  "title": "Ist gegen Plan",
  "period": "April 2026",
  "display": "growth",
  "rows": [
    {"label": "Alle Regionen", "aggregate": true, "measures": [{"series": "auftraege", "label": "Aufträge (Monat)", "yearToDate": false, "current": 18.4, "change": 0.031, "reference": 0.05, "referenceValue": 18.0}, {"series": "auftraege", "label": "Aufträge (lfd. J.)", "yearToDate": true, "current": 66.9, "change": 0.052, "reference": 0.05, "referenceValue": 66.0}, {"series": "umsatz", "label": "Umsatz (Monat)", "yearToDate": false, "current": 16.2, "change": 0.044, "reference": 0.06, "referenceValue": 16.0}, {"series": "umsatz", "label": "Umsatz (lfd. J.)", "yearToDate": true, "current": 60.3, "change": 0.061, "reference": 0.06, "referenceValue": 61.0}]},
    {"label": "Nord", "aggregate": false, "measures": [{"series": "auftraege", "label": "Aufträge (Monat)", "yearToDate": false, "current": 18.4, "change": 0.12, "reference": 0.05, "referenceValue": 18.0}, {"series": "auftraege", "label": "Aufträge (lfd. J.)", "yearToDate": true, "current": 66.9, "change": 0.081, "reference": 0.05, "referenceValue": 66.0}, {"series": "umsatz", "label": "Umsatz (Monat)", "yearToDate": false, "current": 16.2, "change": 0.09, "reference": 0.06, "referenceValue": 16.0}, {"series": "umsatz", "label": "Umsatz (lfd. J.)", "yearToDate": true, "current": 60.3, "change": 0.07, "reference": 0.06, "referenceValue": 61.0}]},
    {"label": "Süd", "aggregate": false, "measures": [{"series": "auftraege", "label": "Aufträge (Monat)", "yearToDate": false, "current": 18.4, "change": -0.04, "reference": 0.05, "referenceValue": 18.0}, {"series": "auftraege", "label": "Aufträge (lfd. J.)", "yearToDate": true, "current": 66.9, "change": 0.032, "reference": 0.05, "referenceValue": 66.0}, {"series": "umsatz", "label": "Umsatz (Monat)", "yearToDate": false, "current": 16.2, "change": 0.4, "reference": 0.06, "referenceValue": 16.0}, {"series": "umsatz", "label": "Umsatz (lfd. J.)", "yearToDate": true, "current": 60.3, "change": 0.05, "reference": 0.06, "referenceValue": 61.0}]}
  ]
}
```
````

:::

## Finanzdiagramm: Wachstumstrend

Mit "culture": "en" stehen Zahlen und Beschriftungen auf Englisch.

::: notes

````
## Finanzdiagramm: Wachstumstrend

```financial-chart
{
  "type": "growth-trend",
  "title": "Wachstum Aufträge",
  "period": "April 2026",
  "lastActual": 3,
  "reference": 0.05,
  "months": [
    {"label": "Jan", "change": 0.056},
    {"label": "Feb", "change": 0.054},
    {"label": "Mär", "change": 0.04},
    {"label": "Apr", "change": 0.048},
    {"label": "Mai", "change": 0.042},
    {"label": "Jun", "change": 0.035}
  ],
  "options": {"culture": "en", "labels": {"reference": "Target"}}
}
```

Mit `"culture": "en"` stehen Zahlen und Beschriftungen auf Englisch.
````

:::

## Finanzdiagramm: zwei Jahre

::: notes

````
## Finanzdiagramm: zwei Jahre

```financial-chart
{
  "type": "two-year",
  "title": "Umsatz je Produktlinie",
  "previousYear": "2025",
  "currentYear": "2026",
  "months": ["J", "F", "M", "A", "M", "J", "J", "F", "M", "A", "M", "J"],
  "series": [
    {"label": "Maschinen", "values": [42000, 45000, 47000, 44000, 40000, 41000, 44000, 48000, 50000, null, null, null]},
    {"label": "Ersatzteile", "values": [18000, 17000, 19000, 21000, 20000, 18000, 19000, 18000, 20000, null, null, null]},
    {"label": "Service", "values": [25000, 26000, 24000, 27000, 29000, 28000, 27000, 29000, 30000, null, null, null]}
  ],
  "options": {"scale": 1000, "unit": "Tsd. EUR"}
}
```
````

:::

## Finanzdiagramm: Übersichtstabelle

::: notes

````
## Finanzdiagramm: Übersichtstabelle

```financial-chart
{
  "type": "summary-table",
  "title": "Übersicht",
  "period": "April 2026",
  "columns": [
    {"label": "Gesamt", "total": true},
    {"label": "Maschinen"},
    {"label": "Service"},
    {"label": "Sonstige", "rest": true}
  ],
  "blocks": [
    {"metric": "Aufträge", "reference": 0.05, "cells": [{"current": 118.3, "previous": 112.5, "change": 0.052, "reference": 0.05}, {"current": 94.7, "previous": 91.3, "change": 0.037, "reference": 0.05}, {"current": 23.4, "previous": 21.0, "change": 0.114, "reference": 0.06}, {"current": 0.2, "previous": 0.2, "change": 0.0, "reference": 0.05}]},
    {"metric": "Marge", "reference": 0.01, "rateOf": "Umsatz", "cells": [{"current": 46.6, "previous": 44.9, "change": 0.038, "reference": 0, "rate": 0.427, "previousRate": 0.428, "referenceRate": 0.438}, {"current": 37.5, "previous": 36.7, "change": 0.022, "reference": 0, "rate": 0.432, "previousRate": 0.441, "referenceRate": 0.451}, {"current": 9.1, "previous": 8.2, "change": 0.11, "reference": 0, "rate": 0.414, "previousRate": 0.402, "referenceRate": 0.412}, {"current": 0.0, "previous": 0.0, "change": 0, "reference": 0}]}
  ],
  "options": {"unit": "Mio. EUR", "tolerance": 0.01, "restShare": 0.01}
}
```
````

:::

## PTA-Folienarten

08

## Agenda

01

Ausgangslage

02

Zielbild

03

Umsetzung

::: notes

```
## Agenda {.agenda}

1. Ausgangslage
2. Zielbild
3. Umsetzung
```

:::

## Die Migration ist ohne Ausfall möglich

::: notes

```
## Die Migration ist ohne Ausfall möglich {.interim}
```

:::

## Was man nicht messen kann, kann man nicht lenken — Peter Drucker, Ökonom

::: notes

```
## Was man nicht messen kann, kann man nicht lenken {.quote}

— Peter Drucker, Ökonom
```

:::

## Ihre Ansprechpartner

Erika Mustermann

Projektleiterin

erika.mustermann@example.org

+49 621 12345-0

Max Mustermann

Berater

max.mustermann@example.org

::: notes

```
## Ihre Ansprechpartner {.contact}

### Erika Mustermann

Projektleiterin
erika.mustermann@example.org
+49 621 12345-0

### Max Mustermann

Berater
max.mustermann@example.org
```

:::

## Vielen Dank!

::: notes

Nach Fragen fragen.

```
# Vielen Dank! {.closing}
```

:::
