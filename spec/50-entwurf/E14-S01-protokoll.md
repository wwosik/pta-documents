# E14-S01 Protokoll-Modus: Beschlüsse, Aufgaben, offene Punkte

> Status: Entwurf
> Epic: [E14 Dokumenttypen der Beratung](E14-dokumenttypen-der-beratung.md)
> Milestone: [M06 Inhalte, Dokumenttypen und Dokumentpflege](M06-inhalte-und-dokumentpflege.md)

## Zusammenfassung

In einem Protokoll markiert der Autor Beschlüsse, Aufgaben und offene Punkte dort, wo sie im
Gesprächsverlauf fallen (`::: decision`, `::: task @Müller bis 2026-12-01`, `::: open`); am Ende
des Dokuments entstehen daraus automatisch die Tabellen „Beschlüsse" und „Aufgaben" sowie eine
Liste der offenen Punkte. Die Präsentation bekommt eine Aufgaben-Folie.

## Kontext

- `markdown/parser.py` hat `tasklists_plugin` (Kästchen `- [ ]`); `generation/docx/writer.py`
  schreibt sie als Word-Aufgabenliste (Z. 501, `checkbox`). Container (`:::`) kommen mit E02-S02
  (`mdit_py_plugins.container`, Prüfung in `layout_syntax.check`).
- Front Matter ist flach (`markdown/front_matter.py`): eine Teilnehmerliste muss eine Zeile sein
  (`teilnehmer: A. Muster, B. Beispiel (Gast)`), wie `status.<kategorie>` ein Präfixschlüssel ist.
- Tabellen und Beschriftungen: `DocxWriter.table_block`, `caption` (E03-S02); Folientabellen im
  PTA-Stil: E04-S02.
- Datumswerte: `FrontMatter.date()` nimmt `2026-11-06` und `06.11.2026`; dieselbe Erkennung gilt
  für Termine in Aufgaben.

## Vorgeschlagener Ansatz

1. **Syntax** in `generation/common/layout_syntax.py` registrieren:
   - `::: decision` — ein Absatz, der Beschluss; optional `{nr=3}` zum Festhalten einer Nummer;
   - `::: task @Name bis 2026-12-01` — erster Absatz die Aufgabe; Verantwortlicher nach `@`
     (mehrere mit Komma), Termin nach `bis`, beides optional; `{status=erledigt}` für Aufgaben
     aus früheren Sitzungen (Werte `offen`, `in-arbeit`, `erledigt`, Farben aus den Status-Labels
     E02-S02);
   - `::: open` — offener Punkt, ein Absatz.
   Ein Container mit mehr als einem Absatz, einer Liste oder Tabelle ist ein Fehler mit Zeile
   („A task is one paragraph; move details into the text before it").
2. **Modell** `generation/common/minutes.py`: `collect(tokens, line_offset) -> Minutes(decisions,
   tasks, open_points)` mit laufenden Nummern (B1, B2 …; A1, A2 …; O1 …) in Dokumentreihenfolge.
   Die Nummern erscheinen auch an der Fundstelle als Kennung („**B1**" vor dem Beschluss).
3. **Darstellung im Text** (DOCX, PDF): Beschluss als Absatz in der Fazit-Box-Optik der Folien
   (Rahmen links in PTA-Blau, Stil „Zitat" mit Kennung); Aufgabe als Aufgabenlisten-Absatz mit
   Kästchen, Verantwortlichem fett und Termin; offener Punkt mit Kennung und „?"-Marke. PPTX:
   dieselben Blöcke als Callouts (E04-S03).
4. **Tabellen am Ende**, erzeugt vom Generator nach dem letzten Block, wenn der Protokoll-Modus
   an ist: `## Beschlüsse` (Nr | Beschluss), `## Aufgaben` (Nr | Aufgabe | Wer | Bis | Status) und
   `## Offene Punkte` (Nr | Punkt) als Tabellenformat „PTA" mit Beschriftung; Überschriften in der
   Sprache aus `sprache`. Überfällige Aufgaben (Termin vor `datum`) bekommen die Statusfarbe
   `danger`. PPTX: eine Folie „Aufgaben" mit der Tabelle vor der Abschlussfolie.
5. **Modus einschalten:** Front Matter `protokoll: ja`, oder das Werkzeug `generate` setzt ihn
   für Dateinamen `…-protokoll.md` (neue Endung neben `-bericht`, Ziel Word). Ohne Modus sind die
   Container trotzdem erlaubt (Kennung im Text, keine Tabellen) — etwa für Aufgaben in einem
   Statusbericht. Teilnehmer aus `teilnehmer:` kommen als Zeile unter das Deckblatt bzw. in die
   Kopfzeile ohne Deckblatt; `ort`, `datum` wie heute.
6. **Rundreise:** Der Konverter (E07-S02) liest die erzeugten Tabellen als normale Tabellen und
   die Container als Absätze mit Kennung; der Rundreise-Test vergleicht mit einer eigenen
   Erwartung (`protokoll.roundtrip.expected.md`), die die Abweichung festhält.
7. **Prüfung** (E08-S02): Aufgabe ohne Verantwortlichen oder Termin → Hinweis `task-incomplete`;
   Protokoll ohne `teilnehmer` → Hinweis.
8. **Beispiel** `samples/protokoll/` (Workshop-Protokoll mit drei Beschlüssen, fünf Aufgaben,
   einem offenen Punkt); `docs/anleitung.md` bekommt den Abschnitt „Protokoll schreiben".

## Akzeptanzkriterien

- [ ] `::: decision`, `::: task`, `::: open` werden in Word, PowerPoint und PDF gleich geprüft;
      falsche Form bricht mit Zeile ab.
- [ ] Mit `protokoll: ja` oder Dateiname `…-protokoll.md` stehen am Ende die Tabellen
      „Beschlüsse", „Aufgaben", „Offene Punkte" mit fortlaufenden Nummern, die zu den Kennungen im
      Text passen.
- [ ] Überfällige Aufgaben sind farblich markiert; `status=erledigt` zeigt ein angekreuztes Kästchen.
- [ ] Das Beispiel erzeugt ohne Fehler und ohne Hinweise.

## Offene Fragen

1. Syntax des Verantwortlichen und Termins: `::: task @Müller bis 2026-12-01` (Vorschlag, liest
   sich wie gesprochen) oder Attribute `::: task {wer="Müller" bis="2026-12-01"}` (eindeutiger,
   mehr Zeichen)?

> (2026-11-07) `::: task @Müller bis 2026-12-01`.
2. Sollen die Tabellen am **Ende** stehen (Vorschlag, wie in PTA-Protokollen üblich) oder direkt
   nach dem Deckblatt als Zusammenfassung?

> (2026-11-07) Am Ende.
3. Deutsche Containernamen (`::: beschluss`, `::: aufgabe`, `::: offen`), falls E02-S02 Frage 1
   so entschieden wird? Dann müssen sie hier und in `samples/protokoll/` nachgezogen werden.

> (2026-11-07) Englisch — Entscheidung zu E02-S02 Frage 1 vom 2026-11-07 gilt für alle neuen Syntaxnamen.

## Notizen

- Abhängigkeiten: E02-S02 (Container), E03-S02 (Tabellen), E04-S03 (Callouts in Folien),
  E08-S01/S02 (Hinweise). Der CSV-Export der Aufgaben ist in E14-S02 als `./run.sh export`
  mitgeplant.
