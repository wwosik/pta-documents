# E17 Qualität und Arbeitsfluss: Rückweg aus Word, Typografie, Terminologie, Autorenkomfort

> Status: Entwurf

## Ziel

Was zwischen dem ersten Markdown und dem fertigen Dokument an Handarbeit bleibt, fällt weg:
Kundenkommentare aus Word kommen ins Markdown zurück, Text ist typografisch sauber, Begriffe
und Quellen sind einheitlich, und wer schreibt, sieht beim Speichern sofort das Ergebnis.

## Motivation

Ein Angebot oder Konzept geht als Word zum Kunden und kommt mit Kommentaren und Änderungen
zurück; heute müsste jemand sie von Hand ins Markdown übertragen, sonst ist die Quelle veraltet.
Dokumente einer Beratung werden an gerade Anführungszeichen, falschen Bindestrichen und
uneinheitlichen Schreibweisen („Email", „pta") gemessen — Kleinigkeiten, die eine KI ebenso
wenig zuverlässig trifft wie ein Mensch in Eile. Und wer ein Deck feilt, will nicht nach jeder
Zeile `./run.sh generate` tippen.

## Scope

| Story | Inhalt | Status |
| ----- | ------ | ------ |
| [E17-S01](E17-S01-rueckweg-aus-word.md) | Word-Kommentare aus Markdown; Kommentare und Änderungen eines zurückgeschickten DOCX zurück ins Markdown | Entwurf |
| [E17-S02](../60-prüfung/E17-S02-typografie-und-code.md) | Deutsche Typografie beim Erzeugen, Silbentrennung und Blocksatz im PDF, Code-Highlighting | in Prüfung |
| [E17-S03](E17-S03-terminologie-und-quellen.md) | Terminologieprüfung in `check`; `QUELLEN.md` maschinenlesbar, `[@kennung]`, Quellenverzeichnis | Entwurf |
| [E17-S04](E17-S04-watch-und-seitenumbrueche.md) | `./run.sh watch`; Seitenumbrüche und Querformat-Abschnitte in Word und PDF | Entwurf |

## Bereichsweite Entscheidungen

- **Markdown bleibt die Quelle.** Nichts, was aus Word zurückkommt, wird still übernommen: der
  Rückweg schreibt Kommentare als Blöcke und Änderungen als Vorschlag ins Markdown; der Mensch
  oder die KI entscheidet, was bleibt.
- Werkzeugverben und Schalter sind englisch (`watch`, `check --fix`, `review-import`), Front
  Matter deutsch (`typografie`, `blocksatz`, `quellenverzeichnis`), Syntaxnamen englisch
  (`::: comment`, `::: pagebreak`, `::: landscape`, `[@kennung]`) — wie überall im Repo.
- Die Bibliothek liest keine Dateien: `QUELLEN.md`, Terminologielisten und zurückgeschickte
  DOCX reicht das Werkzeug als Ressourcen oder Bytes herein.
- Alles, was Text verändert (Typografie, `--fix`), lässt Code-Spans, Codeblöcke, Links und Front
  Matter unangetastet und ist abschaltbar.
- Prüfungen melden sich über die Hinweise aus E08-S01 und die `style-…`-Codes aus E08-S02.

## Akzeptanz

Ein Angebot entsteht aus Markdown mit typografisch sauberen Anführungszeichen, geht als Word zum
Kunden, kommt mit zwei Kommentaren und einer Textänderung zurück; `review-import` setzt die
Kommentare an die richtigen Absätze und markiert die Änderung; `check` meldet „Email" und eine
unbenutzte Quelle; `watch` erzeugt das Dokument beim Speichern neu.

## Offene Fragen

1. Soll der Rückweg (E17-S01) auch für Präsentationen gelten — PowerPoint-Kommentare
   (`ppt/comments/`) zurück ins Markdown? Vorschlag: ja, nur Kommentare, keine Änderungen (es gibt
   in PowerPoint keine Änderungsverfolgung).

> (2026-11-07) Ja, nur Kommentare.

2. Typografie (E17-S02) standardmäßig **an**, mit dem Risiko, dass ein Konverter-Rundweg andere
   Zeichen liefert als geschrieben — oder standardmäßig aus? Vorschlag: an; wer gerade Zeichen
   will, schreibt `typografie: nein`.

> (2026-11-07) An; `typografie: nein` schaltet aus.

## Notizen

- Entstanden aus der Ideenrunde vom 2026-11-07 (Gruppe D, Ideen 13–16); vom Menschen zur
  Planung ausgewählt.
