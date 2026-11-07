# E13-S01 Abkürzungen und Glossar

> Status: Entwurf
> Epic: [E13 Lange Berichte: Abkürzungen, Querverweise, Barrierefreiheit](E13-lange-berichte.md)

## Zusammenfassung

`*[SLA]: Service Level Agreement` irgendwo im Markdown erklärt eine Abkürzung; mit
`abkuerzungsverzeichnis: ja` entsteht daraus ein Verzeichnis als Tabelle, und die erste
Verwendung im Text kann ausgeschrieben werden („Service Level Agreement (SLA)"). Ein Glossar
schreibt man als Definitionsliste in `::: glossar`.

## Kontext

- `markdown/parser.py` nutzt markdown-it-py mit `footnote`, `tasklists`, `deflist`.
  mdit-py-plugins enthält kein `abbr`-Plugin (markdown-it-abbr gibt es nur für JavaScript);
  die Abkürzungssyntax braucht eine eigene Block-Regel (Definition) und eine Core-Regel, die
  Vorkommen im Text in `abbr_open`/`abbr_close`-Token wickelt — rund 80 Zeilen, nach dem Muster
  des JavaScript-Plugins.
- Definitionslisten (`Begriff` / `: Erklärung`) liest der Parser schon; der DOCX-Writer schreibt
  sie (E03-S02, `samples/funktionen/` zeigt sie). Ein Glossar ist eine Definitionsliste an einer
  festen Stelle mit Überschrift.
- Word kennt keine Abkürzungen als Objekt; ein Verzeichnis ist eine normale Tabelle. Screenreader
  lesen in Word nichts aus Tooltips, daher kein `w:fldSimple`-Trick — das Verzeichnis und die
  ausgeschriebene erste Verwendung sind die barrierefreie Form (E13-S03).
- Ordnung der Verzeichnisse: Epic-Frage 1.

## Vorgeschlagener Ansatz

1. **Parser:** `markdown/abbreviations.py` mit einer Block-Regel für `*[ABK]: Erklärung`
   (Zeile am Blockanfang, ohne Leerzeichen vor `*`; Erklärung bis Zeilenende; Definitionen
   erzeugen kein Ausgabe-Token, sondern `env["abbreviations"]`) und einer Core-Regel, die
   Vorkommen als ganze Wörter in `text`-Token außerhalb von Code, Links und Überschriften findet
   (Frage 1) und in `abbr_open`(`meta={"title": …}`)/`abbr_close` wickelt. Doppelte Definition
   mit anderem Text ist ein Fehler mit Zeile; Definition ohne Vorkommen ein Hinweis (E08-S01,
   Code `abbreviation-unused`).
2. **Erste Verwendung:** Front Matter `abkuerzungen: verzeichnis | ausschreiben | beides | nein`
   (Standard `verzeichnis`, Frage 2). Bei `ausschreiben`/`beides` schreibt der Writer das erste
   Vorkommen im Fließtext als „Service Level Agreement (SLA)"; Überschriften und Tabellen zählen
   nicht als erste Verwendung. In PowerPoint gilt dieselbe Regel je Folie — Frage 3.
3. **Verzeichnis:** bei `verzeichnis`/`beides` eine Tabelle „Abkürzungsverzeichnis"/„List of
   abbreviations" (Zwischenüberschrift unnummeriert, Tabellenformat „PTA", zwei Spalten,
   alphabetisch, nur verwendete Abkürzungen) am Ende des Dokuments vor dem Glossar (Epic-Frage 1).
   Im PDF (E05) dasselbe über die Layout-Engine. In PowerPoint entsteht kein Verzeichnis.
4. **Glossar:** Container `::: glossar` (E02-S02) mit genau einer Definitionsliste; wird an die
   feste Stelle am Ende gesetzt, Überschrift „Glossar"/„Glossary", Begriffe fett (Formatvorlage
   wie E03-S02 für Definitionslisten), alphabetisch sortiert, wenn der Container `sortiert`
   als Argument trägt. In PowerPoint ist `::: glossar` eine normale Folie mit Definitionsliste
   („Glossar" als Folientitel), weil ein Deck kein Ende im Sinne eines Anhangs hat.
5. **Konverter (E07-S02):** liest Verzeichnis und Glossar als Tabelle bzw. Liste zurück; die
   Rundreise weicht ab (Erwartungsdatei), Abkürzungsdefinitionen gehen verloren — dokumentiert.
6. **Tests** `tests/markdown/test_abbreviations.py` (Regel, Wortgrenzen, Code/Links/Überschriften
   ausgenommen, Fehler bei Widerspruch) und `tests/generation/docx/test_glossary.py`
   (Verzeichnis, erste Verwendung, Glossar, Reihenfolge, Englisch); `samples/funktionen/
   funktionen-bericht.md` und die Anleitungen zeigen beides.

## Akzeptanzkriterien

- [ ] `*[SLA]: …` und `abkuerzungen: beides` ergeben in Word die ausgeschriebene erste
      Verwendung und ein alphabetisches Verzeichnis nur der verwendeten Abkürzungen.
- [ ] `::: glossar` ergibt ein Kapitel „Glossar" am Ende, in PowerPoint eine Folie.
- [ ] Widersprüchliche Definitionen sind Fehler mit Zeile; ungenutzte ein Hinweis.
- [ ] Abkürzungen in Code, Links und Überschriften bleiben unverändert.

## Offene Fragen

1. Abkürzungen auch in Überschriften ausschreiben? Vorschlag: nein — Überschriften bleiben kurz,
   das Inhaltsverzeichnis auch.

>

2. Standard `verzeichnis` (Vorschlag) oder `beides`?

>

3. In PowerPoint die erste Verwendung je Folie ausschreiben, nur auf der ersten Folie, oder gar
   nicht? Vorschlag: gar nicht — Folien sind knapp; wer will, schreibt es hin.

>

## Notizen

- Abhängigkeiten: E02-S02 (Container), E08-S01 (Hinweise) für den Hinweis auf ungenutzte
  Definitionen; PDF-Teil mit E05-S02.
