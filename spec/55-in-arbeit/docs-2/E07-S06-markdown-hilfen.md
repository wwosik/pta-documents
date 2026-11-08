# E07-S06 Markdown-Hilfen

> Status: in Bearbeitung (docs-2) — reaktiviert 2026-11-08 auf Wunsch des Menschen
> Epic: [E07 Konvertierung nach Markdown](../../50-entwurf/E07-konvertierung-nach-markdown.md)

## Zusammenfassung

Die Markdown-Hilfen von DocLibs (`MarkdownText`) sind bereits vollständig portiert. Diese Story
macht sie zu einer dokumentierten, öffentlichen Schnittstelle für Aufrufer, die selbst Markdown
schreiben, und schließt die Lücken in Tests und Beschreibung.

## Kontext

- DocLibs `MarkdownText.cs` (220 Zeilen) hat genau acht öffentliche Funktionen: `Escape`,
  `EscapeLineStart`, `Code`, `Destination`, `Cell`, `Table`, `Compact`, `Normalize`; Tests
  `MarkdownTextTests.cs` (7 Fälle). Weitere Hilfen gibt es im Paket nur für JIRA-Wiki
  (`Jira/`, entfällt) und `MarkdownDocument` (portiert in E02-S01).
- Alle acht stehen schon in `src/pta_documents/markdown/text.py` (136 Zeilen, vorgezogen in
  E07-S02, siehe dessen Implementierungsnotizen); die sieben DocLibs-Tests stehen in
  `tests/markdown/test_text.py`. DOCX- und PPTX-Konverter nutzen sie als `md`.
- Was fehlt: `text.py` hat kein `__all__`, `cell()` und die Tabellenhilfen sind knapp
  beschrieben, `docs/` erwähnt die Hilfen nicht, und `pta_documents.markdown` nennt das Modul
  nicht als öffentlich. DocLibs dokumentiert sie in `docs/wwosik.DocLibs.DocumentConversions.md`
  (Abschnitt *Markdown helpers*): öffentlich „for consumers that write Markdown themselves".

## Vorgeschlagener Ansatz

1. Kein Umzug: das Modul bleibt `pta_documents.markdown.text` und wird als öffentliche
   Schnittstelle festgeschrieben (`__all__` mit den acht Namen; der Aufruf bleibt
   `from pta_documents.markdown import text as md`, weil `escape`, `code`, `table` als nackte
   Namen zu allgemein sind). `pta_documents.markdown.__init__` nennt `text` im Docstring.
2. Docstrings nach DocLibs vervollständigen — jede Funktion sagt, was sie schützt und was nicht:
   `escape` nur, was formatieren würde (`customfield_10682` bleibt), `escape_line_start` für
   Blockanfänge, `code` mit Backtick-Zaun, `destination` mit `<…>`, `cell` nur `|`, `table` mit
   `<br>` für Zeilenumbrüche in Zellen, `compact` ohne leere Zeilen und Spalten, `normalize`
   (Zeilenenden, Leerzeilen, harte Umbrüche nur als `\`).
3. Tests ergänzen, wo DocLibs-Verhalten bisher nur indirekt geprüft ist: `\` am Ende und vor
   Satzzeichen, `<` vor `/`, `!`, `?`; `+` als Listenmarke ohne Unterstreichungsregel; neun
   Ziffern als Grenze der nummerierten Liste; `table()` mit ungleich langen Zeilen, Tabs und
   `\r\n` in Zellen; `normalize("")` und nur Leerzeilen → `""`. Dazu eine Rundreise-Eigenschaft:
   `escape(x)` als Absatz durch den Parser (`markdown/parser.py`) gerendert ergibt wieder `x`
   für eine feste Liste heikler Eingaben.
4. `docs/verwendung.md`: Abschnitt „Markdown selbst schreiben" mit Beispiel (Tabelle aus Daten,
   Text sicher einsetzen, `normalize` am Ende) und dem Hinweis, dass die Konverter dieselben
   Hilfen nutzen.
5. Epic E07: Zeile E07-S06 auf den Stand bringen (Funktionen vorhanden seit E07-S02, diese Story
   nur Schnittstelle, Tests, Doku).

## Akzeptanzkriterien

- [ ] `pta_documents.markdown.text.__all__` nennt genau die acht Funktionen aus DocLibs;
      pyright strict und ruff sind grün.
- [ ] Jede Funktion hat einen Docstring, der ihr Verhalten an einem Beispiel zeigt.
- [ ] Die zusätzlichen Grenzfälle und die Rundreise-Eigenschaft sind getestet und grün.
- [ ] `docs/verwendung.md` beschreibt die Hilfen mit einem lauffähigen Beispiel.

## Offene Fragen

1. Da die Funktionen schon portiert sind: soll diese kleine Story bestehen bleiben (Schnittstelle,
   Tests, Doku wie oben), oder wird sie gestrichen und der Rest bei der Prüfung von E07-S02
   miterledigt?

> (2026-11-07) Gestrichen; Schnittstelle, Tests und Doku werden bei der Prüfung von E07-S02 miterledigt.

## Notizen

- Die Anker für Überschriften (GitHub-artige Kennungen für `[x](#anker)`) entstehen in E05-S02
  als `markdown/anchors.py`; sie sind keine DocLibs-`MarkdownText`-Funktion und gehören nicht
  hierher.
