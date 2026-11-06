# E03-S02 DOCX-Inhalte

> Status: Entwurf
> Epic: [E03 DOCX-Generator auf den PTA-Word-Vorlagen](E03-docx-generator.md)
> Milestone: [M01 PTA-Dokumente aus Markdown](M01-pta-dokumente-aus-markdown.md)

## Zusammenfassung

Jeder Markdown-Block wird zu Absätzen in der passenden PTA-Formatvorlage; Zeichenformate,
Tabellen, Bilder und Links folgen den Regeln der Vorlage.

## Kontext

Formatvorlagen der PTA-Word-Vorlagen und ihre Werte stehen in der
[Designanalyse](../10-analysen/2026-11-06%20pta-designstandards.md#word). Stil-IDs sind die
deutschen IDs der Vorlage (`berschrift1` für „Überschrift 1", `Aufzhlungszeichen`, …) — sie werden
über den Stilnamen gesucht, nicht hart codiert.

## Vorgeschlagener Ansatz

1. Zuordnung Markdown → Formatvorlage:

   | Markdown | Formatvorlage (Name in Word) | Anmerkung |
   | -------- | ---------------------------- | --------- |
   | `#` | `Überschrift 1` | nummeriert `1` (Liste der Vorlage) |
   | `##` | `Überschrift 2` | `1.1` |
   | `###` | `Überschrift 3` | `1.1.1` |
   | `####`–`######` | `Zwischenüberschrift` | Versalien, nicht nummeriert |
   | Absatz | `Standard` | 10 pt, Zeilenabstand mind. 14 pt |
   | Absatz nur aus `**fett**` | `Standard fett` | |
   | `-`-Liste, Ebene 1–3 | `Aufzählungszeichen` mit `ilvl` 0–2 | ■ blau, dann ― |
   | `1.`-Liste, Ebene 1–3 | `Listenabsatz` mit `ilvl` 0–2 | `1.`, dann Aufzählung; Neustart je Liste über neue `w:num` |
   | Tabelle | Tabellenformatvorlage `PTA` | Kopfzeile blau mit weißer Schrift, graue Linien; Spaltenbreiten nach Inhalt |
   | Tabellentitel `**Titel**` direkt davor | `Standard fett` | wie in der Vorlage („Überschrift Tabelle") |
   | Tabellenbeschriftung | `Beschriftung` mit Feld `SEQ Tabelle` | „Tabelle 1: …" unter der Tabelle; Quelle: Absatz `Tabelle: …` direkt danach |
   | Bildunterschrift | `Beschriftung` mit Feld `SEQ Abbildung` | „Abbildung 1: …" unter dem Bild; Quelle: Bildtitel `![Alt](bild.png "Titel")`, sonst Alt-Text |
   | Bild | `Standard`, Inline-Bild in Satzspiegelbreite höchstens | Seitenverhältnis bleibt |
   | Codeblock | eigene Absatzvorlage `Code` (Consolas 9 pt, Hintergrund `E6E6E6`) | wird bei Bedarf in die Stile aufgenommen — die Vorlage hat keine (Entscheidung 2026-11-06) |
   | `> Zitat` | `Zitat`, falls vorhanden, sonst eingerückter `Standard` | |
   | `---` | Absatz mit unterer Linie in `AFAFAF` | |
   | Fußnote `[^1]` | Word-Fußnote, `Fußnotentext` | |
   | Link | Zeichenvorlage `Hyperlink` (`004676`, unterstrichen) | nur absolute URIs werden Hyperlinks |
   | `` `code` `` | Consolas | |
   | `**`, `*`, `~~` | fett, kursiv, durchgestrichen | |

2. Seitenumbruch: `#` beginnt keine neue Seite (wie in der Vorlage), Überschriften haben
   `keepNext` aus der Vorlage.
3. Tabellenbreite: Satzspiegel (Hoch 16,6 cm, Quer 25,3 cm); Spalten nach dem längsten Wort
   gewichtet, wie im PPTX-Generator von DocLibs.
4. Bilder aus den Ressourcen des `MarkdownDocument`; PNG/JPEG/GIF direkt, SVG über den
   Bildkonverter (E02-S04) — bis dahin Fehler.
5. Rundreise-Tests: Beispiel-Markdown → DOCX → DOCX-Konverter → Vergleich mit
   `*.roundtrip.expected.md`; die erzeugten Dateien gehen nach `.tmp/review/`.

## Akzeptanzkriterien

- [ ] Jeder Blocktyp der Tabelle erscheint im Ergebnis in genau der genannten Formatvorlage.
- [ ] Nummerierte Listen beginnen nach einer Unterbrechung neu bei 1.
- [ ] Das Ergebnis enthält keine Direktformatierung von Schriftart, -größe oder -farbe außer für
      Code.
- [ ] Bilder tragen „Abbildung n: …", Tabellen „Tabelle n: …"; mit `sprache: en` „Figure n"/„Table n".
- [ ] Rundreise-Test für Hoch- und Querformat grün.

## Offene Fragen

1. Sollen `##` die Kapitelebene 1 sein (wie vorgeschlagen, weil `#` der Dokumenttitel ist), oder
   soll `#` = „Überschrift 1" sein und der Titel nur aus dem Front Matter kommen?

> (2026-11-06) `#` ist „Überschrift 1"; der Titel kommt nur aus dem Front Matter.

2. Codeblöcke: Gibt es bei der PTA eine Vorgabe (Schrift, Hintergrund), oder ist der Vorschlag
   oben recht?

> (2026-11-06) Consolas auf `E6E6E6`, wie vorgeschlagen.

3. Sollen Abbildungen ebenfalls „Abbildung n: …"-Beschriftungen bekommen (Vorlage zeigt nur
   „Tabelle 1: …")?

> (2026-11-06) Ja, „Abbildung n: …".

## Notizen

