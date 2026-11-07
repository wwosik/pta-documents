# E12-S01 Dokumentenhistorie

> Status: Entwurf
> Epic: [E12 Dokumentpflege: Historie, Vergleich, Kennzeichnung](E12-dokumentpflege.md)

## Zusammenfassung

Ein Word-Bericht oder PDF bekommt nach dem Deckblatt eine Tabelle „Dokumentenhistorie" (Version |
Datum | Autor | Änderung) — geschrieben im Markdown als `::: historie` oder, auf Wunsch, aus dem
`git log` der Markdown-Datei abgeleitet.

## Kontext

- Die PTA-Word-Vorlagen (`source-templates/*.dotx`) enthalten keine Historientabelle; die
  Designanalyse nennt keine Vorgabe. Üblich ist sie trotzdem in Konzepten und Angeboten
  (Epic-Frage 1).
- E03-S01 baut Deckblatt und Inhaltsverzeichnis aus der Vorlage; das Inhaltsverzeichnis kommt mit
  `inhaltsverzeichnis: ja`. Die Historie steht sinnvoll dazwischen oder danach (Frage 1).
- Tabellen schreibt der DOCX-Writer im Tabellenformat „PTA" (E03-S02) mit Titelzeile aus einem
  fetten Absatz; die Historie nutzt dieselbe Routine.
- Der Container-Parser kommt mit E02-S02; `::: historie` ist dort ein weiterer Containername.
- `tools/generate/generate.py` kennt den Pfad der Markdown-Datei und kann `git log` aufrufen; die
  Bibliothek darf es nicht (Entscheidung Epic).

## Vorgeschlagener Ansatz

1. **Markdown:** ein Container

   ```markdown
   ::: historie
   | Version | Datum | Autor | Änderung |
   | ------- | ----- | ----- | -------- |
   | 0.9 | 2026-10-20 | E. Muster | Entwurf für den Workshop |
   | 1.0 | 2026-11-06 | E. Muster | Anmerkungen des Kunden eingearbeitet |
   :::
   ```

   mit genau einer Tabelle von drei oder vier Spalten (ohne Autor erlaubt). Er darf überall im
   Text stehen, wird aber an die feste Stelle nach dem Deckblatt gesetzt (Frage 1); zwei
   Container sind ein Fehler. In PowerPoint ist der Container ein Fehler („a deck has no
   document history; remove the block or move it to the report").
2. **Aus Git:** Front Matter `historie: git` (Werte `git`, `nein`; Standard `nein`). Das
   Werkzeug `generate.py` liest `git log --follow --format=%ad%x09%an%x09%s --date=short` der
   Markdown-Datei, nimmt nur Commits, deren Betreff mit einer Version beginnt (`1.0: …`,
   `v0.9 …`; Frage 2), und übergibt die Zeilen als `MarkdownDocument.metadata["historie"]`
   (eine Zeile je Eintrag, Felder durch Tab). Die Bibliothek baut daraus dieselbe Tabelle wie
   aus dem Container. Beides zusammen ist ein Fehler.
3. **Schreiben** in `generation/docx/writer.py` (neue Methode `_history(rows)`): Überschrift
   „Dokumentenhistorie"/„Document history" als „Zwischenüberschrift" (unnummeriert, E03-S02),
   die Tabelle im Tabellenformat „PTA" mit Kopfzeile, Datum nach `sprache` formatiert, danach ein
   Seitenumbruch, wenn ein Inhaltsverzeichnis folgt. Im PDF (E05-S03) dasselbe an derselben
   Stelle.
4. **Version aufs Deckblatt:** die letzte Zeile der Historie liefert die Version; sie erscheint
   auf dem Deckblatt hinter dem Untertitel („Version 1.0") und in den Dokumenteigenschaften
   (`cp:version`), sofern das Deckblatt der Vorlage den Platz hat (E03-S01 prüft die
   Platzhalter).
5. **Tests** `tests/generation/docx/test_history.py`: Container, Git-Zeilen über `metadata`,
   beide → Fehler, in PPTX → Fehler, Rundreise (E07-S02 liest die Tabelle als normale Tabelle
   zurück; Abweichung in der Erwartungsdatei). Für `generate.py` ein Test mit einem temporären
   Git-Repo in `.tmp/`. `docs/anleitung.md` erhält ein Kapitel „Dokumentenhistorie".

## Akzeptanzkriterien

- [ ] `::: historie` ergibt nach dem Deckblatt eine Tabelle im PTA-Stil mit Überschrift; die
      letzte Version steht auf dem Deckblatt.
- [ ] `historie: git` baut die Tabelle aus den versionierten Commits der Datei; ohne Git-Repo
      oder ohne passende Commits ist das eine klare Meldung des Werkzeugs, kein leeres Kapitel.
- [ ] Container in einer Präsentation, zwei Container oder Container plus `historie: git` sind
      Fehler mit Zeile.

## Offene Fragen

1. Position: direkt nach dem Deckblatt und **vor** dem Inhaltsverzeichnis (Vorschlag), oder am
   Ende des Dokuments?

> (2026-11-07) Nach dem Deckblatt, vor dem Inhaltsverzeichnis.
2. Woran erkennt das Werkzeug einen Historien-Commit — Betreff beginnt mit einer Versionsnummer
   (Vorschlag), ein Trailer `Version: 1.0`, oder jeder Commit zählt?

> (2026-11-07) Betreff beginnt mit einer Versionsnummer; andere Commits zählen nicht.

## Notizen

- Abhängigkeiten: E02-S02 (Container). PDF-Teil erst mit E05-S03.
