---
vorlage: basis
titel: Zielgruppenfassungen
untertitel: "fassung: trainer"
datum: 2026-11-08
fassung: trainer
---
# Zielgruppenfassungen

::: notes
Diese Datei ist die Trainerfassung (`fassung: trainer`): Sie zeigt alles und trägt deshalb den
Sticker „Für den internen Gebrauch". `./run.sh generate … --audience alle` schreibt daraus auch
die Kundenfassung und die interne Fassung.
:::

# Übungen

## Interne Blöcke

Diesen Absatz sieht jede Fassung.

{.internal}
Diesen Absatz sehen nur die interne und die Trainerfassung.

::: internal
- Preise und interne Bemerkungen gehören in `::: internal`
- Die Kundenfassung lässt den Block weg
:::

:::: notes
```markdown
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

::: exercise
Wie viele Fassungen erzeugt `--audience alle` höchstens?
:::

::: solution
Drei: kunde, intern und trainer — aber nur die, die sich unterscheiden.
:::

:::: notes
```markdown
::: exercise
Wie viele Fassungen erzeugt `--audience alle` höchstens?
:::

::: solution
Drei: kunde, intern und trainer — aber nur die, die sich unterscheiden.
:::
```
::::

## Preise {.internal}

- Tagessatz nach Rahmenvertrag
- Diese Folie fehlt in der Kundenfassung samt Notizen

:::: notes
```markdown
## Preise {.internal}

- Tagessatz nach Rahmenvertrag
- Diese Folie fehlt in der Kundenfassung samt Notizen
```
::::

# Danke {.closing}
