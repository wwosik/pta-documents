---
vorlage: hoch-ohne-deckblatt
titel: Zielgruppenfassungen
datum: 2026-11-08
fassung: trainer
---
# Zielgruppenfassungen

Diese Datei ist die Trainerfassung (`fassung: trainer`): Sie zeigt alles und trägt deshalb die
Kennzeichnung „Für den internen Gebrauch". `./run.sh generate … --audience alle` schreibt daraus
auch die Kundenfassung und die interne Fassung.

## Interne Blöcke

Ein Absatz nach `{.internal}` und ein Block `::: internal` fehlen in der Kundenfassung:

```markdown
{.internal}
Diesen Absatz sehen nur die interne und die Trainerfassung.

::: internal
| Leistung | Tagessatz |
| -------- | --------: |
| Beratung | 1.200 € |
:::
```

{.internal}
Diesen Absatz sehen nur die interne und die Trainerfassung.

::: internal
| Leistung | Tagessatz |
| -------- | --------: |
| Beratung | 1.200 € |
:::

## Übung mit Lösung

Die Übung steht in jeder Fassung, die Lösung nur in der Trainerfassung:

```markdown
::: exercise
Welche Fassung zeigt Lösungen?
:::

::: solution
Nur die Trainerfassung.
:::
```

::: exercise
Welche Fassung zeigt Lösungen?
:::

::: solution
Nur die Trainerfassung.
:::

## Internes Kapitel {.internal}

Ein `#`- oder `##`-Abschnitt mit `{.internal}` fehlt in der Kundenfassung ganz, bis zur nächsten
Überschrift derselben Ebene:

```markdown
## Internes Kapitel {.internal}
```
