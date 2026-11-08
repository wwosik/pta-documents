"""Markdown of the visual building blocks of E15-S02, shared by the generator tests."""

from __future__ import annotations

from typing import Final

STEPS: Final = """::: steps
### Analyse
Interviews und Ist-Aufnahme
### Konzept
Soll-Bild
### Umsetzung {.current}
In Sprints
### Abnahme
### Betrieb
:::
"""
RATING: Final = """| Kriterium | A     | B     |
| --------- | ----- | ----- |
| Kosten    | [3/4] | [1/4] |
| Zeit      | [0/4] | [4/4] |
"""
RISKS: Final = """::: riskmatrix
| Nr | Risiko        | Wahrscheinlichkeit | Auswirkung | Maßnahme   |
| -- | ------------- | ------------------ | ---------- | ---------- |
| 1  | Ausfall       | 2                  | 4          | Vertretung |
| 2  | Daten         | 4                  | 4          | Prüfen     |
| 3  | Schnittstelle | 4                  | 4          | Mock       |
:::
"""
