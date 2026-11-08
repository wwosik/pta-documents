# E16 Schulung und Zielgruppen: Fassungen, Zeitplan, Handout, Backup

> Status: Entwurf

## Ziel

Eine Markdown-Quelle, mehrere Fassungen und Begleitstücke: eine interne und eine Kundenfassung
desselben Dokuments, Aufgaben mit Lösungen nur für den Trainer, ein Zeitplan aus den
Foliendauern, ein Teilnehmerhandout aus Folienbildern und Sprechernotizen, und Backup-Folien
bzw. Anhänge, die hinter dem eigentlichen Ende stehen.

## Motivation

PTA-Schulungen und Kundenpräsentationen werden heute mehrfach gepflegt: eine Fassung mit internen
Bemerkungen und Preisen, eine für den Kunden; Übungen einmal mit, einmal ohne Lösung; der Zeitplan
in einer eigenen Tabelle, das Handout als separater Export. Jede Änderung muss an allen Stellen
nachgezogen werden. Mit einer Quelle, aus der Werkzeuge die Fassungen erzeugen, bleibt alles
konsistent — und eine KI, die das Markdown schreibt, muss die Varianten nicht selbst auseinander
halten. Weder DocLibs noch vt-tools-libs kennen das; eigene Idee (Entscheidung 2026-11-07).

## Scope

| Story | Inhalt | Status |
| ----- | ------ | ------ |
| [E16-S01](../60-prüfung/E16-S01-zielgruppenfassungen.md) | `{.internal}` / `::: internal`, `::: exercise` / `::: solution`; `generate --audience kunde\|intern\|trainer`; Suffix `-intern`, automatische `kennzeichnung: intern` | in Prüfung |
| [E16-S02](E16-S02-schulungs-zeitplan.md) | `{dauer=5}` auf Folien und Kapiteln, Pausen; Agenda mit Uhrzeiten, Trainer-Zeitplan, Abgleich mit `laenge:` | Entwurf |
| [E16-S03](E16-S03-teilnehmerhandout.md) | `./run.sh handout`: Word-Handout mit Folienbildern (E10-S02) und Notizen oder Notizlinien, 2/3/6 Folien je Seite | Entwurf |
| [E16-S04](../60-prüfung/E16-S04-backup-folien-und-anhang.md) | `# Backup {.backup}` hinter der Abschlussfolie; `# Anhang {.appendix}` mit Nummerierung A, B, C in Word und PDF | in Prüfung |

## Bereichsweite Entscheidungen

- **Zielgruppen heißen `kunde`, `intern`, `trainer`.** `trainer` schließt `intern` ein (alles,
  was intern sichtbar ist, plus Lösungen). Die Namen sind Front-Matter-Werte und
  Schalterwerte, darum deutsch; die Syntaxnamen (`{.internal}`, `::: exercise`, `::: solution`,
  `{.backup}`, `{.appendix}`, `{.break}`) englisch wie alle übrige Syntax (E02).
- **Weglassen geschieht vor dem Generator.** Eine Fassung ist ein gefilterter Token-Strom
  (`generation/common/audience.py`); die Generatoren DOCX, PPTX, PDF und HTML wissen nichts von
  Zielgruppen. So gilt es für alle Formate zugleich, und die Konverter lesen nur, was da ist.
- **Nichts geht versehentlich raus.** Ohne Angabe ist die Fassung `kunde`; die interne und die
  Trainerfassung tragen das Suffix `-intern` bzw. `-trainer` im Dateinamen und die Kennzeichnung
  `intern` (E12-S03, E04-S05), sofern das Front Matter nichts Strengeres setzt.
- **Hinweise statt Stille.** Jede Fassung meldet über E08-S01, wie viele Blöcke sie weggelassen
  hat, und E08-S02 rechnet Dauern und Wörter je Fassung.
- **Handout und Zeitplan sind Word-Dokumente auf den PTA-Vorlagen** (E03), keine neuen Formate.

## Akzeptanz

Ein Schulungs-Markdown mit internen Blöcken, drei Übungen mit Lösungen, Dauern auf jeder Folie,
einer Pause und einem Backup-Kapitel ergibt mit einem Befehl je Zielgruppe eine PPTX, die
PowerPoint ohne Reparatur öffnet; die Kundenfassung enthält keinen internen Text und keine
Lösung, die Trainerfassung beides; `handout` liefert ein Word-Dokument mit Folienbildern,
Notizen und dem Zeitplan; der Zeitplan summiert auf die Front-Matter-Länge oder meldet die
Abweichung.

## Offene Fragen

1. Standardfassung ohne Angabe: `kunde` (nichts Internes geht versehentlich raus — Vorschlag)
   oder `intern` (wer intern arbeitet, sieht alles und muss für den Kunden bewusst exportieren)?

> (2026-11-07) `kunde`.

2. Soll `./run.sh generate` ohne `--audience` **alle** Fassungen erzeugen, in denen sich das
   Dokument unterscheidet (eine Datei je Fassung), oder nur die Standardfassung? Vorschlag: nur
   die Standardfassung; `--audience alle` erzeugt jede.

> (2026-11-07) Nur die Standardfassung; `--audience alle` erzeugt jede.

## Notizen

- Reihenfolge: E16-S01 zuerst (E16-S02 und E16-S03 nutzen die Fassungen), E16-S04 unabhängig.
  E16-S03 braucht E10-S02 für die Folienbilder, läuft ohne das Extra aber als Text-Handout.
