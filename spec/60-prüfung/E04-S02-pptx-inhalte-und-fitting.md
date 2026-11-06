# E04-S02 PPTX-Inhalte und Fitting

> Status: in Prüfung
> Epic: [E04 PPTX-Generator auf der PTA-PowerPoint-Vorlage](../50-entwurf/E04-pptx-generator.md)
> Milestone: [M01 PTA-Dokumente aus Markdown](../50-entwurf/M01-pta-dokumente-aus-markdown.md)

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

- [x] Absätze landen auf Ebene 2, Aufzählungen auf Ebene 3–5, `###` auf Ebene 1.
- [x] Tabellen gleichen der Mustertabelle in Farben, Größen und Linien.
- [x] Kein Text ragt aus dem Platzhalter; zu lange Inhalte werden fortgesetzt.
- [x] Rundreise-Test grün.

## Offene Fragen

1. Codeblöcke auf Folien: kommen sie bei der PTA überhaupt vor, und gibt es eine Vorgabe?

> (2026-11-06) Consolas 14 pt auf `E6E6E6`, wie vorgeschlagen.

2. Untergrenze beim Verkleinern: 14 pt (Vorschlag) oder 12 pt, wie in dichten Schaubildern der
   Vorlagensammlung?

> (2026-11-06) 12 pt.

## Notizen


## Implementierungsnotizen

- `generation/pptx/fitting.py` (Messung und Aufteilung), `generation/pptx/visuals.py`
  (Tabellen, Codebox, Bildreihen, freie Textbox), eingebunden in `DeckWriter`.
- **Textebenen** wie geplant; die Größen, Einzüge und Abstände der fünf Ebenen liest
  `BodyStyle.read()` aus dem Master der Vorlage (nicht aus Konstanten). Nummerierte Listen
  setzen `buAutoNum arabicPeriod` (mit `startAt`, wenn die Liste nicht bei 1 beginnt), sonst
  gelten die Aufzählungszeichen des Masters. Fett setzt zusätzlich `+mj-lt` (Segoe UI).
- **Fitting:** Text schrumpft über `normAutofit fontScale` (wie PowerPoints „Text bei Überlauf
  verkleinern", bleibt beim Bearbeiten angepasst) in 2-pt-Schritten von 18 pt bis 12 pt; passt
  er dann nicht, wird an Gruppen (Absatz mit seinen verschachtelten Listenpunkten) auf Folgefolien
  „Titel (Forts.)" geteilt. Tabellen gehen von 16/14 pt (Kopf/Zeilen) bis 12/12 pt und werden
  sonst zeilenweise geteilt (Kopf auf jeder Folie, Titelzeile nur auf der ersten, Text oberhalb
  auf der ersten, unterhalb auf der letzten). Code geht von 14 auf 12 pt und wird sonst
  zeilenweise geteilt. Mehr als vier Bilder nebeneinander → weitere Folien.
- Die Höhen sind **Schätzungen** (DocLibs-`TextMetrics`, ohne Schriftdatei). Text kann in
  PowerPoint daher etwas mehr oder weniger Platz brauchen; `normAutofit` gleicht kleine
  Abweichungen beim ersten Bearbeiten aus.
- **Folien mit Visual:** ohne Text oberhalb `Nur Titel`, mit Text oberhalb `Titel und Text`, dessen
  Textplatzhalter auf die Höhe des Textes verkleinert wird; darunter Tabelle/Code/Bilder, Text
  unterhalb in einer Textbox, die die fünf Ebenen des Masters als `lstStyle` übernimmt (sieht aus
  wie im Platzhalter). Genau ein Bild mit Text bleibt bei `Titel, Text und Bild 01` (E04-S01).
- **Tabellen** als Tabellenobjekt über die Inhaltsbreite, Direktformatierung nach der
  Mustertabelle: Kopf `004676` mit weißer Schrift in Segoe UI, Zeilen in Segoe UI Light `404040`,
  waagerechte Linien `E6E6E6` 0,5 pt, letzte Linie `404040`, keine senkrechten Linien, erste Spalte
  ohne linken Innenabstand. Ein `**fetter**` Absatz direkt vor der Tabelle wird die verbundene
  Titelzeile (18 pt PTA-Blau). Ausrichtung aus Markdown; ohne Angabe werden Spalten, die nur
  Zahlen enthalten, rechtsbündig (außer der ersten). Summenzeilen gibt es noch nicht.
- **Code** als Rechteck mit Fläche `E6E6E6`, Consolas 14 pt `404040`, ohne Umbruch.
- Text vor der ersten Überschrift wird wie in DocLibs ignoriert.
- Rundreise: `tests/generation/pptx/samples/deck.md` (DocLibs-`deck.md`, um PTA-Fälle ergänzt:
  Kapitel, Tabellentitel, Bild mit Text, Bildreihe, benanntes Layout, Abschluss; ohne Mermaid)
  → `deck.roundtrip.expected.md`. Der Konverter verliert Ebenen und Formatierung (E07-S03).
- **Prüfpunkt:** `.tmp/review/deck.pptx` in PowerPoint ansehen — besonders Tabelle, Codebox und
  ob geschätzte Textmengen in die Platzhalter passen.
