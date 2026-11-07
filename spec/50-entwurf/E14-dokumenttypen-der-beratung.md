# E14 Dokumenttypen der Beratung: Protokoll, Anforderungen, Abnahme, Skelette

> Status: Entwurf

## Ziel

Die wiederkehrenden Dokumente einer IT-Beratung bekommen Syntax, die ihre Besonderheiten kennt:
Protokolle mit Beschlüssen und Aufgaben, Konzepte mit nummerierten Anforderungen, Angebote und
Abnahmen mit Unterschriftenblock und rechnenden Tabellen — und ein Befehl, der den Startpunkt
für jede Dokumentart anlegt.

## Motivation

DocLibs und vt-tools-libs kennen nur allgemeines Markdown; was ein Protokoll von einem Konzept
unterscheidet, schreibt der Autor jedes Mal von Hand: die Aufgabenliste am Ende wird aus dem Text
zusammengesucht, Anforderungen werden händisch nummeriert und bei jeder Umstellung falsch, die
Angebotssumme wird im Kopf addiert. Eine Beratung schreibt diese Dokumente wöchentlich; was
sich daraus mechanisch ableiten lässt, soll die Bibliothek ableiten, damit Autor und KI nur noch
den Inhalt schreiben.

## Scope

| Story | Inhalt | Status |
| ----- | ------ | ------ |
| [E14-S01](E14-S01-protokoll.md) | Protokoll-Modus: `::: decision`, `::: task`, `::: open`; Tabellen „Beschlüsse" und „Aufgaben" am Ende; Aufgaben-Folie | Entwurf |
| [E14-S02](E14-S02-anforderungen.md) | `::: requirement` mit stabilen IDs (`REQ-001`), Priorität und Status, Anforderungsliste, Export | Entwurf |
| [E14-S03](E14-S03-abnahme-und-kalkulation.md) | Unterschriftenblock `::: signatures`; rechnende Tabellen `{.calc}` mit Summe, MwSt und deutschem Zahlenformat | Entwurf |
| [E14-S04](E14-S04-dokument-skelette.md) | `./run.sh new <art> documents/<thema>`: Skelette für Angebot, Konzept, Statusbericht, Protokoll, Schulung, Präsentation | Entwurf |

## Bereichsweite Entscheidungen

- **Abgeleitete Inhalte werden beim Erzeugen berechnet**, nicht in Word nachgerechnet: die
  Aufgabentabelle, die Anforderungsliste und die Summen stehen fertig im Dokument, damit PDF
  (E05) und Word dasselbe zeigen und das Rücklesen (E07) echte Tabellen findet.
- **Syntaxnamen englisch** wie die übrige Markdown-Syntax (`::: decision`, `::: task`,
  `::: requirement`, `::: signatures`, `{.calc}`); endgültig entscheidet E02-S02, Frage 1 —
  fällt sie deutsch aus, heißen sie `::: beschluss`, `::: aufgabe`, `::: anforderung`,
  `::: unterschriften`, `{.rechnen}`. Front-Matter-Schlüssel sind deutsch (`protokoll`,
  `teilnehmer`, `anforderungen.praefix`).
- Alle Container werden in `generation/common/layout_syntax.py` (E02-S02) registriert, damit
  DOCX, PPTX und PDF dieselben Fehler melden; Hinweise an den Schreiber laufen über E08-S01,
  die Prüfung ohne Erzeugen über `./run.sh check` (E08-S02).
- Die Tabellen dieser Stories nutzen das Tabellenformat „PTA" aus E03-S02 und die Beschriftung
  „Tabelle n: …"; keine eigenen Stile.
- Die Bibliothek liest keine Dateien; Skelette und Exporte liegen bei den Werkzeugen in `tools/`.

## Akzeptanz

In `samples/` liegen ein Protokoll, ein Konzept mit Anforderungen und ein Angebot mit
Kalkulation und Unterschriftenblock; `./run.sh new protokoll documents/test` erzeugt einen
Ordner, aus dem `./run.sh generate` ohne Fehler und Hinweise ein Word-Dokument macht.

## Offene Fragen

1. Gibt es bei der PTA verbindliche Gliederungen oder Vorlagen für Protokoll, Angebot, Konzept
   und Statusbericht (über die Word-Vorlagen hinaus)? Die Skelette in E14-S04 folgen sonst
   der üblichen Praxis.

> (2026-11-07) Nein; die Skelette folgen der üblichen Praxis.
2. Sollen Aufgaben und Anforderungen auch in ein Werkzeug außerhalb des Dokuments wandern
   (Excel, Jira, Azure DevOps)? E14-S01/S02 sehen nur einen CSV-Export vor.

> (2026-11-07) Nein, nur CSV-Export.

## Notizen
