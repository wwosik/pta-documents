## Zielgruppenfassungen

08.11.2026

fassung: trainer

::: notes

Diese Datei ist die Trainerfassung (fassung: trainer): Sie zeigt alles und trägt deshalb den Sticker „Für den internen Gebrauch“. ./run.sh generate … --audience alle schreibt daraus auch die Kundenfassung und die interne Fassung.

:::

## Übungen

01

## Interne Blöcke

Diesen Absatz sieht jede Fassung.

Diesen Absatz sehen nur die interne und die Trainerfassung.

Preise und interne Bemerkungen gehören in ::: internal

Die Kundenfassung lässt den Block weg

:::: notes

```
Diesen Absatz sieht jede Fassung.

{.internal}
Diesen Absatz sehen nur die interne und die Trainerfassung.

::: internal
- Preise und interne Bemerkungen gehören in `::: internal`
- Die Kundenfassung lässt den Block weg
:::
```

::::

## Übung mit Lösung

Wie viele Fassungen erzeugt --audience alle höchstens?

Drei: kunde, intern und trainer — aber nur die, die sich unterscheiden.

:::: notes

```
::: exercise
Wie viele Fassungen erzeugt `--audience alle` höchstens?
:::

::: solution
Drei: kunde, intern und trainer — aber nur die, die sich unterscheiden.
:::
```

::::

## Preise

Tagessatz nach Rahmenvertrag

Diese Folie fehlt in der Kundenfassung samt Notizen

::: notes

```
## Preise {.internal}

- Tagessatz nach Rahmenvertrag
- Diese Folie fehlt in der Kundenfassung samt Notizen
```

:::

## Danke
