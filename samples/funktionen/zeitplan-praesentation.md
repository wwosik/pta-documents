---
vorlage: schulung
titel: Schulung planen
untertitel: "beginn: 09:00 · laenge: 25"
datum: 2026-11-08
fassung: trainer
beginn: 09:00
laenge: 25
---
# Schulung planen

::: notes
Diese Datei zeigt den Schulungs-Zeitplan: `dauer=…` an Folien und Kapiteln, eine Pause und
`beginn:`/`laenge:` im Front Matter. Die Trainerfassung (`fassung: trainer`) schreibt die
geplante Zeit als erste Zeile in die Notizen jeder Folie; `./run.sh schedule` macht daraus ein
Word-Dokument mit der Zeitplantabelle.
:::

## Agenda {.agenda dauer=2}

:::: notes
```markdown
## Agenda {.agenda dauer=2}
```
Mit `beginn:` steht vor jedem Kapitel seine Uhrzeit, die Pause ist ein eigener Punkt.
::::

# Grundlagen {dauer=8}

## Was wird geplant?

- Jede Folie: `{dauer=5}` oder `{dauer=1h30}`
- Ein Kapitel: `{dauer=45}` am `#`

:::: notes
```markdown
# Grundlagen {dauer=8}

## Was wird geplant?
```
Das Kapitel hat acht Minuten; seine drei Folien ohne eigene Angabe teilen sie sich.
::::

## Wie wird gerechnet?

- Folien ohne Angabe teilen den Rest des Kapitels
- Sonst zählen sie zwei Minuten, mit Hinweis

:::: notes
```markdown
## Wie wird gerechnet?
```
::::

## Was wird verglichen?

- Die Summe mit der geplanten Länge (`laenge`)
- Die Sprechzeit mit der Schätzung von `check`

:::: notes
```markdown
## Was wird verglichen?
```
::::

## Pause {.break dauer=5}

:::: notes
```markdown
## Pause {.break dauer=5}
```
Die Pausenfolie bleibt während der Pause stehen.
::::

# Praxis

## Übung {dauer=6}

- Eine eigene Schulung mit `dauer` planen
- Mit `./run.sh schedule` den Zeitplan schreiben

:::: notes
```markdown
## Übung {dauer=6}
```
::::

## Fragen {dauer=4}

- Was bleibt offen?

:::: notes
```markdown
## Fragen {dauer=4}
```
::::

# Danke {.closing}
