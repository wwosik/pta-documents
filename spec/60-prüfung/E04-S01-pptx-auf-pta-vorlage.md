# E04-S01 PPTX auf der PTA-Vorlage

> Status: in Prüfung
> Epic: [E04 PPTX-Generator auf der PTA-PowerPoint-Vorlage](../50-entwurf/E04-pptx-generator.md)
> Milestone: [M01 PTA-Dokumente aus Markdown](../50-entwurf/M01-pta-dokumente-aus-markdown.md)

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
   | erstes `#` + Front Matter | `Titelfolie mit Bild 02` (Standard; andere per Front Matter `titelfolie`) | Titel (idx 0), Untertitel (idx 12), „Autor, Ort, Datum" (idx 13) aus `untertitel`, `autor`, `ort`, `datum` |
   | weiteres `#` | `Trennfolie` | Kapitelnummer „01", „02" … (idx 14), Kapitelname (Titel) |
   | `##` mit Text | `Titel und Text` | Titel, Inhalt (idx 12) |
   | `##` nur mit Tabelle, Grafik oder Bildern | `Nur Titel` | Titel; Inhalt als freie Form in der Inhaltsfläche |
   | `##` mit genau einem Bild und Text | `Titel, Text und Bild 01` | Text (idx 12), Bild (idx 31) |
   | `##` mit genau einem Bild | `Titel und Bild 01` | Bild (idx 31) |
   | `# … {.closing}` | `Abbschlussfolie` | Titel |
   | `## … {layout="Name"}` | genanntes PTA-Layout | nach Platzhalterreihenfolge; bei mehreren Inhaltsplatzhaltern wird der Inhalt an `---`-Zeilen geteilt, wie bei `::: columns` |

3. Unsichtbare Deko-Platzhalter (Aufforderung „x", z. B. Eckklammern, Linien, Logo auf
   `Titelfolie Branchen`) werden auf jeder Folie leer angelegt, wie es die Musterfolien tun.
4. Fußzeile: „PTA – <Titel>" (Front Matter `fusszeile`, sonst der Präsentationstitel) und
   Foliennummer auf allen Folien außer Titel-, Trenn- und Abschlussfolie, wie es die Layouts
   vorsehen; kein Datum (PTA-Regel).
5. Metadaten: Titel, Autor; Firma „PTA Unternehmensberatung" aus der Vorlage bleibt, Bearbeiter
   der Vorlage werden ersetzt.
6. API: `PptxGenerator.generate(document, output, options: PptxOptions | None)`; Optionen
   `variant` (`basis`, `schulung`), `language`, `footer`, `show_slide_numbers`; im Front Matter
   `vorlage`, `sprache`, `fusszeile`, `titelfolie`.

## Akzeptanzkriterien

- [ ] Ein Markdown mit Titel, zwei Kapiteln, Textfolien, Bildfolie und Abschluss ergibt eine
      Präsentation, die PowerPoint und LibreOffice ohne Reparatur öffnen.
- [x] Jede Folie verwendet ein Layout der PTA-Vorlage; keine Musterfolie bleibt übrig.
- [x] Eckklammern, Titellinie und Logo erscheinen wie auf den Musterfolien.
- [x] Fußzeile und Foliennummer wie in der Vorlage, kein Datum.

## Offene Fragen

1. Kapitelnummern auf Trennfolien zweistellig („01") wie im Layout-Platzhalter „0X"?

> (2026-11-06) Ja, zweistellig.

2. Wenn `{layout="Name"}` ein Layout mit mehreren Inhaltsplatzhaltern nennt (z. B. zweispaltig):
   Inhalte am `---` teilen wie bei `::: columns`?

> (2026-11-06) An `---`-Zeilen teilen, wie bei `::: columns`.

## Notizen


## Implementierungsnotizen

- `generation/pptx/`: `model.py` (Folienmodell), `parser.py` (`DeckParser`, Markdown → Folien,
  nach DocLibs), `writer.py` (`DeckWriter`, Folien auf PTA-Layouts), `generator.py`
  (`PptxGenerator.generate(document, output, options)`), `options.py` (`PptxOptions`).
  Heading-Attribute in `generation/common/heading_attributes.py` (Port aus DocLibs, nur
  `.closing` und `layout="…"`; `.dark`/`kicker` kommen mit E04-S03 — vorgezogener Teil von
  E02-S02).
- Gliederung: erstes `#` → Titelfolie (`titelfolie:` wählt das Layout, Standard
  `Titelfolie mit Bild 02`); weitere `#` → `Trennfolie` mit „01", „02" …; `# … {.closing}` →
  `Abbschlussfolie`; `##` → Folie. Ein `layout="…"` auf `#` ersetzt das Standardlayout.
- **Festlegungen:**
  - Unter einem Kapitel- oder Abschluss-`#` darf kein Inhalt stehen (die PTA-Layouts haben dafür
    keinen Platz) → `DocumentConversionError` mit Zeilennummer. Unter dem ersten `#` ist nur Text
    erlaubt; er wird Untertitel, wenn `untertitel` im Front Matter fehlt.
  - Fehlt ein `#`, steht aber `titel` im Front Matter, wird trotzdem eine Titelfolie angelegt.
  - Zeile „Autor, Ort, Datum" aus `autor`, `ort`, `datum` (Datum nur, wenn angegeben).
  - Leer gebliebene Platzhalter werden entfernt (keine „Klicken Sie …"-Hinweise); die
    unsichtbaren Deko-Platzhalter (Aufforderung „x") bleiben leer auf der Folie, wie es
    python-pptx beim Anlegen aus dem Layout ohnehin tut.
  - Fußzeile und Foliennummer werden aus den Platzhaltern des Layouts kopiert (python-pptx
    legt sie nicht an) — also genau auf den Layouts, die sie vorsehen; nie Datum. Text
    „PTA – " + (`fusszeile` oder Präsentationstitel).
  - `{layout="…"}` auf `##`: Text wird an `---` geteilt und der Reihe nach auf die
    Textplatzhalter verteilt (Deko-Platzhalter ausgenommen), Bilder auf die Bildplatzhalter;
    was nicht passt, ergibt einen Fehler mit Erklärung. Unbekannte Layoutnamen listen alle 35.
  - `sprache: en` + `basis`: englische Titelfolienvorlage und das englische Logo an der
    Position der Musterfolie (vorgezogener Teil von E04-S05).
  - Metadaten: Titel, Autor, zuletzt geändert von, Revision 1; Firma „PTA Unternehmensberatung"
    bleibt aus der Vorlage.
- Bilder: genau ein Bild + Text → `Titel, Text und Bild 01`, ein Bild allein → `Titel und Bild 01`,
  jeweils in den Bildplatzhalter (python-pptx schneidet auf das Seitenverhältnis zu,
  PTA-Verhalten). Tabellen, Code und Bildreihen folgen in E04-S02.
- **Prüfpunkt (offen):** Weder PowerPoint noch LibreOffice auf dieser Maschine — geprüft ist
  das Wiederöffnen mit python-pptx und eindeutige Shape-IDs. Bitte `.tmp/review/frame.pptx` in
  PowerPoint öffnen; erstes Akzeptanzkriterium daher noch nicht abgehakt.
