## Schulung planen

08.11.2026

beginn: 09:00 · laenge: 25

::: notes

Diese Datei zeigt den Schulungs-Zeitplan: dauer=… an Folien und Kapiteln, eine Pause und beginn:/laenge: im Front Matter. Die Trainerfassung (fassung: trainer) schreibt die geplante Zeit als erste Zeile in die Notizen jeder Folie; ./run.sh schedule macht daraus ein Word-Dokument mit der Zeitplantabelle.

:::

## Agenda

01

09:02 Grundlagen

02

09:10 Pause

03

09:15 Praxis

::: notes

Geplant: 09:00–09:02 (2 min)

```
## Agenda {.agenda dauer=2}
```

Mit beginn: steht vor jedem Kapitel seine Uhrzeit, die Pause ist ein eigener Punkt.

:::

## Grundlagen

01

::: notes

Geplant: 09:02–09:10 (8 min)

:::

## Was wird geplant?

Jede Folie: {dauer=5} oder {dauer=1h30}

Ein Kapitel: {dauer=45} am #

::: notes

Geplant: 09:02–09:05 (3 min)

```
# Grundlagen {dauer=8}

## Was wird geplant?
```

Das Kapitel hat acht Minuten; seine drei Folien ohne eigene Angabe teilen sie sich.

:::

## Wie wird gerechnet?

Folien ohne Angabe teilen den Rest des Kapitels

Sonst zählen sie zwei Minuten, mit Hinweis

::: notes

Geplant: 09:05–09:08 (3 min)

```
## Wie wird gerechnet?
```

:::

## Was wird verglichen?

Die Summe mit der geplanten Länge (laenge)

Die Sprechzeit mit der Schätzung von check

::: notes

Geplant: 09:08–09:10 (2 min)

```
## Was wird verglichen?
```

:::

## Pause · 5 min

::: notes

Geplant: 09:10–09:15 (5 min)

```
## Pause {.break dauer=5}
```

Die Pausenfolie bleibt während der Pause stehen.

:::

## Praxis

02

::: notes

Geplant: 09:15–09:25 (10 min)

:::

## Übung

Eine eigene Schulung mit dauer planen

Mit ./run.sh schedule den Zeitplan schreiben

::: notes

Geplant: 09:15–09:21 (6 min)

```
## Übung {dauer=6}
```

:::

## Fragen

Was bleibt offen?

::: notes

Geplant: 09:21–09:25 (4 min)

```
## Fragen {dauer=4}
```

:::

## Danke
