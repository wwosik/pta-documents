# E04-S02 PPTX-Inhalte und Fitting

> Status: Entwurf
> Epic: [E04 PPTX-Generator auf der PTA-PowerPoint-Vorlage](E04-pptx-generator.md)
> Milestone: [M01 PTA-Dokumente aus Markdown](M01-pta-dokumente-aus-markdown.md)

## Zusammenfassung

Die Inhalte einer Folie im PTA-Stil: Textebenen richtig belegt, Tabellen nach der Mustertabelle,
Bilder in Bildplatzhaltern, und was nicht passt, wird verkleinert oder auf Folgefolien fortgesetzt.

## Kontext

PTA-Textebenen: 1 Subheadline (18 pt Segoe UI blau), 2 Einleitungstext (18 pt Light), 3–5
Aufzählungen (■ 18 pt, − 16 pt, − 14 pt). DocLibs-Fitting: `DeckWriter.Fitting.cs`, `TextMetrics.cs`.
Werte in der [Designanalyse](../10-analysen/2026-11-06%20pta-designstandards.md#powerpoint).

## Vorgeschlagener Ansatz

1. Zuordnung im Inhaltsplatzhalter:

   | Markdown | Textebene |
   | -------- | --------- |
   | `###` | 1 (Subheadline) |
   | Absatz | 2 (Einleitungstext) |
   | `-`-Liste, Ebene 1 / 2 / 3 | 3 / 4 / 5 |
   | `1.`-Liste | Ebene 3–5 mit Nummerierung (`buAutoNum arabicPeriod`) statt ■ |
   | `**fett**` | fett in **Segoe UI** (nicht Light) — PTA-Regel für Hervorhebungen |
   | `*kursiv*`, `~~`, `` `code` ``, Links | wie DocLibs; Links in `004676` |

2. **Tabellen** als Tabellenobjekt über die Inhaltsbreite (31,20 cm), Direktformatierung nach der
   Mustertabelle: Kopf `004676` weiß 16 pt; Zeilen 14 pt Light mit Linien `E6E6E6`; letzte Linie
   `404040`; Zahlen rechtsbündig; ein vorangehender `**Titel**` wird Tabellentitelzeile (18 pt
   PTA-Blau). Spaltenbreiten nach DocLibs-Regel (längstes Wort).
3. **Bilder** in Bildplatzhaltern füllen und beschneiden (PTA-Verhalten); freie Bilder auf
   `Nur Titel` passen in die Inhaltsfläche, Seitenverhältnis bleibt.
4. **Code** in Consolas 14 pt auf `E6E6E6`-Fläche (keine PTA-Vorgabe; Entscheidung 2026-11-06).
5. **Fitting** aus DocLibs portieren: Text verkleinern bis zu einer Untergrenze, sonst Folgefolie
   „(Forts.)"; Tabellen zeilenweise auf Folgefolien mit wiederholtem Kopf. Untergrenze **12 pt**
   (Entscheidung 2026-11-06, wie in dichten Schaubildern der Vorlagensammlung).
6. Rundreise-Test `deck.md` → PPTX → PPTX-Konverter → `deck.roundtrip.expected.md`; Dateien nach
   `.tmp/review/`.

## Akzeptanzkriterien

- [ ] Absätze landen auf Ebene 2, Aufzählungen auf Ebene 3–5, `###` auf Ebene 1.
- [ ] Tabellen gleichen der Mustertabelle in Farben, Größen und Linien.
- [ ] Kein Text ragt aus dem Platzhalter; zu lange Inhalte werden fortgesetzt.
- [ ] Rundreise-Test grün.

## Offene Fragen

1. Codeblöcke auf Folien: kommen sie bei der PTA überhaupt vor, und gibt es eine Vorgabe?

> (2026-11-06) Consolas 14 pt auf `E6E6E6`, wie vorgeschlagen.

2. Untergrenze beim Verkleinern: 14 pt (Vorschlag) oder 12 pt, wie in dichten Schaubildern der
   Vorlagensammlung?

> (2026-11-06) 12 pt.

## Notizen

