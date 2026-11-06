# spec

Spezifikationen und der Aufgaben-Lebenszyklus. Der Ablauf steht in
[../ai/Arbeitsablauf.md](../ai/Arbeitsablauf.md); diese Datei ist die Karte der Ordner.

| Ordner | Inhalt |
| ------ | ------ |
| `00-ideensammlung/` | Rohe Ideen, vom Menschen geschrieben. Eine Datei je Idee oder Thema. |
| `10-analysen/` | Angeforderte Analysen, `JJJJ-MM-TT <slug>.md`. Das Ergebnis landet hier in Dateien, nie im Chat. |
| `50-entwurf/` | Offene Feature-Epics, Meilensteine und Stories, die auf Umsetzung warten. |
| `55-in-arbeit/<agent-id>/` | Von diesem Agent geclaimte Stories. Andere Agent-Ordner und den zugehörigen Code nicht anfassen. |
| `60-prüfung/` | Umgesetzte Stories, die auf Verifikation durch den Menschen warten. Jede trägt *Implementierungsnotizen*. |
| `70-fertig/<epic-id>-<slug>/` | Verifizierte Stories zusammen mit ihrem abgeschlossenen Feature-Epic. Technische Stories nutzen einen `T`-Containerordner. |

Die Zahlenpräfixe gibt es, damit der Ablauf unabhängig von der Projektsprache in der richtigen
Reihenfolge steht. Die Lücken sind Absicht — eine neue Stufe lässt sich einfügen, ohne alles
umzunummerieren.

| Art | ID und Dateiname | Datei |
| --- | ---------------- | ----- |
| Feature-Epic | `E01-kurztitel.md` | Ja; gruppiert Stories eines Produkt-/Fachbereichs |
| Feature-Story | `E01-S01-kurztitel.md` | Ja; Storynummer zählt innerhalb des Epics |
| Technische Story | `T01-S01-kurztitel.md` | Ja; `T01` ist ein Container ohne Datei |
| Meilenstein | `M01-kurztitel.md` | Ja; gruppiert Stories aus mehreren Epics |

Die nächste freie `E`-/`M`-ID und Storynummer innerhalb des `E`-/`T`-Containers verwenden.
Technische Container enthalten höchstens 99 Stories; nach `T01-S99` folgt `T02-S01`. Eine
bekannte externe Referenz steht nach der Story-ID und vor dem Slug. Storydateinamen bleiben beim
Verschieben zwischen Ordnern unverändert.

Jedes Feature-Epic führt seine Stories und deren Status in einer Scope-Tabelle. Eine Story gehört
zu genau einem Feature-Epic oder technischen Container; bereichsübergreifende Liefergruppen sind
Meilensteine.

- Eine Story vor der Umsetzung claimen; Claims werden auf `main` committet. Niemals eine von
  einem anderen Agent geclaimte Story anfassen. Siehe
  [../ai/Arbeitsablauf.md#eine-story-claimen](../ai/Arbeitsablauf.md#eine-story-claimen).
- Fertige Arbeit committen; nach einer erledigten Aufgabe rebasen und pushen.
- Analysen nie im Chat schreiben; die Datei schreiben.
