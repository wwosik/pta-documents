# E11-S02 Bausteine: wiederverwendbare Markdown-Abschnitte

> Status: Entwurf
> Epic: [E11 Bausteine, Variablen und Datenquellen](E11-bausteine-variablen-datenquellen.md)

## Zusammenfassung

Ein Markdown bindet mit einer Zeile einen Baustein aus einer gemeinsamen Ablage ein — das
Firmenprofil, die Leistungsübersicht, die Kontaktfolie einer Kollegin, den rechtlichen Hinweis
einer Schulung — samt dessen Bildern. Geändert wird der Baustein an einer Stelle; jedes Dokument,
das ihn einbindet, bekommt beim nächsten Erzeugen den neuen Stand.

## Kontext

- `MarkdownDocument` (`markdown/document.py`) kennt Text und `resources`; Bilder kommen nie von
  der Platte (Entscheidung E02). Das Werkzeug `tools/generate/generate.py` sammelt die Bilder des
  Dokumentordners (`resources(folder)`).
- `docs/anleitung.md` legt fest: ein Thema, ein Ordner in `documents/`, Bilder in `images/`.
  Eine Ablage für Gemeinsames gibt es noch nicht.
- E04-S04 plant `## … {.contact}` mit Bild, Name, Funktion, E-Mail, Telefon je Person — genau die
  Daten, die sich in einem Personen-Baustein ablegen lassen.
- Fehler nennen heute die Zeile im Dokument (`line_of` in `markdown/parser.py`, `line_offset`
  für das Front Matter). Ein eingebundener Baustein verschiebt Zeilen; die Meldung muss trotzdem
  auf die richtige Datei und Zeile zeigen.

## Vorgeschlagener Ansatz

1. **Syntax:** eine Zeile `::: include firmenprofil` (Container-Zaun ohne Inhalt und ohne
   schließendes `:::`, Name ohne Endung, Unterordner mit `/`: `personen/mustermann`) — Frage 1.
   Der Container-Parser aus E02-S02 erkennt sie; vor E02-S02 reicht eine Zeilenregel.
2. **Ablage:** Bausteine liegen als `<name>.md` mit eigenem `images/` in `samples/bausteine/`
   (im Repo, offizielle PTA-Bausteine) und `documents/_bausteine/` (beim Anwender, gewinnt bei
   gleichem Namen; Epic-Frage 1). Ein Baustein hat kein Front Matter und beginnt frühestens bei
   `##` — Frage 2.
3. **Auflösung im Werkzeug**, nicht in der Bibliothek: `generate.py` legt jeden Baustein als
   `DocumentResource("_bausteine/<name>.md", "text/markdown", bytes)` und seine Bilder als
   `_bausteine/<name>/images/…` ab. Die Bibliothek findet Bausteine nur in `resources`; fehlt
   einer, lautet die Meldung „Line 30: the building block 'firmenprofil' is not among the
   document's resources. Put it in documents/_bausteine/firmenprofil.md."
4. **Einfügen** in `src/pta_documents/markdown/includes.py`: `expand(text, document, format,
   line_offset) -> tuple[str, LineMap]` ersetzt jede Include-Zeile durch den Bausteintext,
   schreibt Bildpfade des Bausteins auf `_bausteine/<name>/images/…` um und führt eine
   `LineMap` (Dokumentzeile → Quelle und Zeile). Rekursion: Bausteine dürfen Bausteine einbinden,
   höchstens fünf Ebenen tief, ein Zyklus ist ein Fehler. Variablen (E11-S01) werden nach dem
   Einfügen ersetzt, gelten also auch im Baustein.
5. **Fehlerzeilen:** `DocumentConversionError` bekommt ein optionales `source: str | None`;
   `LineMap.describe(line)` liefert „firmenprofil.md, line 12" statt der Dokumentzeile. Die
   Generatoren reichen die `LineMap` an ihre Fehlerstellen weiter (eine Hilfsfunktion in
   `generation/common/`, damit nicht jeder Writer sie kennt).
6. **Personen-Bausteine:** `personen/<kuerzel>.md` enthält genau eine Kontaktfolie
   `## {.contact}` nach E04-S04 (Bild, Name, Funktion, E-Mail, Telefon). `::: include
   personen/mustermann` unter einer Folie `## Ihre Ansprechpartner {.contact}` fügt die Person
   ein; bis zu fünf Includes ergeben `Kontakt 01`–`05`.
7. **Tests** `tests/markdown/test_includes.py`: Einfügen, Bildpfade, Rekursion, Zyklus, fehlender
   Baustein, Fehlerzeile aus dem Baustein; Rundreise mit `samples/angebot/` (Epic-Akzeptanz).
   `docs/anleitung.md` bekommt ein Kapitel „Bausteine", `docs/ki-anleitung.md` die Regel, erst in
   `_bausteine/` nachzusehen, bevor man Firmenprofil oder Kontaktfolie schreibt.

## Akzeptanzkriterien

- [ ] `::: include firmenprofil` fügt den Baustein mit seinen Bildern in Word und PowerPoint ein;
      ein Baustein aus `documents/_bausteine/` gewinnt gegen den gleichnamigen im Repo.
- [ ] Ein Fehler im Baustein nennt Bausteindatei und Zeile darin.
- [ ] Zyklus, zu tiefe Verschachtelung und fehlender Baustein sind Fehler mit Zeile im Dokument.
- [ ] Der Aufruf aus Python ohne das Werkzeug funktioniert weiter; ein Include ohne passende
      Ressource ist dort derselbe Fehler wie ein fehlendes Bild.

## Offene Fragen

1. Syntax: `::: include firmenprofil` (passt zu den Containern aus E02-S02) oder
   `!include firmenprofil.md` (Pandoc-Nähe)? Vorschlag: `::: include`, weil der Parser es ohnehin
   kennt und ein unbekannter Container schon heute ein Fehler wäre.

>

2. Darf ein Baustein Überschriften jeder Ebene enthalten, oder passt der Generator die Ebenen an
   die Einfügestelle an (`::: include firmenprofil` unter `##` hebt `#` → `##`)? Vorschlag:
   keine Anpassung — der Baustein wird so geschrieben, wie er eingefügt werden soll.

>

## Notizen

- Abhängigkeiten: E11-S01 (Variablen im Baustein), E04-S04 (Kontaktfolie) für Schritt 6.
