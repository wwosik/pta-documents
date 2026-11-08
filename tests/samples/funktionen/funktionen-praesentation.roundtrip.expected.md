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

## Bilder nebeneinander

![Kachel 1](images/image12.png)

![Kachel 2](images/image13.png)

![Kachel 3](images/image14.png)

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

![Kachel 2](images/image13.png)

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

## PTA-Folienarten

06

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
