# E04-S01 PPTX auf der PTA-Vorlage

> Status: Entwurf
> Epic: [E04 PPTX-Generator auf der PTA-PowerPoint-Vorlage](E04-pptx-generator.md)
> Milestone: [M01 PTA-Dokumente aus Markdown](M01-pta-dokumente-aus-markdown.md)

## Zusammenfassung

Der Rahmen des PPTX-Generators: die eingebettete PTA-Vorlage laden, aus der Markdown-Gliederung
Folien auf den passenden PTA-Layouts anlegen und Fußzeile, Foliennummer und Metadaten setzen.

## Kontext

DocLibs `PptxGenerator`, `DeckParser`, `DeckWriter` (zusammen ~2 400 Zeilen) — dort für einen
selbst erzeugten Master. Hier: 35 PTA-Layouts ohne `type`, Werte in der
[Designanalyse](../10-analysen/2026-11-06%20pta-designstandards.md#powerpoint).

## Vorgeschlagener Ansatz

1. Gliederung wie in DocLibs: `#` am Anfang = Titelfolie, weitere `#` = Kapitel, `##` = eine
   Folie, `# … {.closing}` = Abschlussfolie.
2. Zuordnung zu Layouts:

   | Markdown | Layout | Platzhalter |
   | -------- | ------ | ----------- |
   | erstes `#` + Absatz/Front Matter | `Titelfolie ohne Bild` (Standard, siehe Epic-Frage 1) | Titel (idx 0), Untertitel (idx 12), „Name, Ort, Datum" (idx 13) |
   | weiteres `#` | `Trennfolie` | Kapitelnummer (idx 14), Kapitelname (Titel) |
   | `##` mit Text | `Titel und Text` | Titel, Inhalt (idx 12) |
   | `##` nur mit Tabelle, Grafik oder Bildern | `Nur Titel` | Titel; Inhalt als freie Form in der Inhaltsfläche |
   | `##` mit genau einem Bild und Text | `Titel, Text und Bild 01` | Text (idx 12), Bild (idx 31) |
   | `##` mit genau einem Bild | `Titel und Bild 01` | Bild (idx 31) |
   | `# … {.closing}` | `Abbschlussfolie` | Titel |
   | `## … {layout="Name"}` | genanntes PTA-Layout | nach Platzhalterreihenfolge |

3. Unsichtbare Deko-Platzhalter (Aufforderung „x", z. B. Eckklammern, Linien, Logo auf
   `Titelfolie Branchen`) werden auf jeder Folie leer angelegt, wie es die Musterfolien tun.
4. Fußzeile: „PTA – <Titel>" (Front Matter `footer`, sonst der Präsentationstitel) und
   Foliennummer auf allen Folien außer Titel-, Trenn- und Abschlussfolie, wie es die Layouts
   vorsehen; kein Datum (PTA-Regel).
5. Metadaten: Titel, Autor; Firma „PTA Unternehmensberatung" aus der Vorlage bleibt, Bearbeiter
   der Vorlage werden ersetzt.
6. API: `PptxGenerator.generate(document, output, options: PptxOptions | None)`; Optionen
   `variant` (`basis`, `schulung`, `basis-en`), `footer`, `show_slide_numbers`.

## Akzeptanzkriterien

- [ ] Ein Markdown mit Titel, zwei Kapiteln, Textfolien, Bildfolie und Abschluss ergibt eine
      Präsentation, die PowerPoint und LibreOffice ohne Reparatur öffnen.
- [ ] Jede Folie verwendet ein Layout der PTA-Vorlage; keine Musterfolie bleibt übrig.
- [ ] Eckklammern, Titellinie und Logo erscheinen wie auf den Musterfolien.
- [ ] Fußzeile und Foliennummer wie in der Vorlage, kein Datum.

## Offene Fragen

1. Kapitelnummern auf Trennfolien zweistellig („01") wie im Layout-Platzhalter „0X"?

>

2. Wenn `{layout="Name"}` ein Layout mit mehreren Inhaltsplatzhaltern nennt (z. B. zweispaltig):
   Inhalte am `---` teilen wie bei `::: columns`?

>

## Notizen

