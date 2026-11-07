# E12-S02 Dokumentvergleich mit Word-Änderungsverfolgung

> Status: Entwurf
> Epic: [E12 Dokumentpflege: Historie, Vergleich, Kennzeichnung](E12-dokumentpflege.md)
> Milestone: [M06 Inhalte, Dokumenttypen und Dokumentpflege](M06-inhalte-und-dokumentpflege.md)

## Zusammenfassung

Aus zwei Fassungen eines Markdown-Berichts entsteht **ein** Word-Dokument mit
Änderungsverfolgung: gelöschter Text durchgestrichen, neuer unterstrichen, mit Autor und Datum —
so, wie Word es selbst beim Vergleichen zeigt. Der Kunde sieht, was sich zwischen Angebot 1.0 und
1.1 geändert hat, und nimmt die Änderungen in Word an oder ab.

## Kontext

- Der DOCX-Writer (`generation/docx/writer.py`) schreibt Absätze als `w:p` mit Runs; Felder,
  Fußnoten und Tabellen baut er über lxml. Änderungsmarkierungen sind in OOXML `w:ins` und
  `w:del` um Runs (Text in `w:del` als `w:delText`), mit `w:author`, `w:date`, `w:id`; gelöschte
  Absatzmarken sind `w:del` in `w:rPr` der Absatzmarke.
- Der Vergleich läuft auf Markdown, nicht auf Word (Epic-Entscheidung): Markdown ist zeilen- und
  absatzorientiert und lässt sich mit `difflib` aus der Standardbibliothek vergleichen.
- `tools/generate/generate.py` ist das Muster für ein Werkzeug mit Dateizugriff; Git-Zugriff
  kommt wie in E12-S01 ins Werkzeug.

## Vorgeschlagener Ansatz

1. **Vergleich** in `src/pta_documents/generation/docx/compare.py`:
   - beide Fassungen parsen (`markdown/parser.py`), Blöcke in eine flache Folge bringen
     (Absatz, Überschrift, Listenpunkt, Tabelle, Bild, Code, Zitat — je mit Quelltext und Token);
   - **Absatzebene:** `difflib.SequenceMatcher` über die normalisierten Blocktexte ordnet
     gleiche, ersetzte, gelöschte und eingefügte Blöcke einander zu; ersetzte Blöcke gleicher Art
     mit einer Ähnlichkeit ≥ 0,5 (`ratio`) gelten als geändert, sonst als gelöscht + eingefügt;
   - **Wortebene** in geänderten Absätzen: `SequenceMatcher` über Wörter und Satzzeichen der
     Inline-Runs; Zeichenformat (fett, Link) hängt am Run, sodass eine Formatänderung ohne
     Textänderung als Löschen + Einfügen des Runs erscheint (Grenze, Schritt 5);
   - Ergebnis: ein Blockstrom mit Markierungen `Change.INSERTED | DELETED | EQUAL` an Runs und
     Blöcken.
2. **Schreiben:** der DOCX-Writer bekommt einen Modus, in dem Runs mit Markierung in `w:ins`/
   `w:del` gewickelt werden; gelöschte Blöcke werden ganz geschrieben und als gelöscht markiert
   (Absatzmarke eingeschlossen), eingefügte ganz als eingefügt. Tabellen, Bilder und Codeblöcke
   werden **als Ganzes** ersetzt (gelöscht + eingefügt), keine Zellvergleiche. Autor aus
   `--autor` oder dem Front Matter `autor` der neuen Fassung, Datum jetzt; `w:id` fortlaufend.
   Das Dokument selbst (Deckblatt, Front Matter, Historie) kommt aus der **neuen** Fassung;
   `w:settings` erhält `w:trackRevisions`, damit weitere Änderungen in Word ebenfalls
   nachverfolgt werden.
3. **Öffentliche Schnittstelle:** `DocxGenerator.compare(old: MarkdownDocument, new:
   MarkdownDocument, output, options, author) -> None`; Ressourcen kommen aus der neuen Fassung,
   gelöschte Bilder aus der alten.
4. **Werkzeug** `tools/compare/compare.py` und `./run.sh compare alt.md neu.md
   [--out ordner] [--author Name]`; `./run.sh compare neu.md --since HEAD~1` holt die alte
   Fassung mit `git show <rev>:<pfad>` (auch ein Tag oder Datum). Ausgabe
   `<name>-vergleich.docx`.
5. **Grenzen**, im Werkzeug-Hilfetext und in `docs/anleitung.md` genannt: Verschobene Absätze
   erscheinen als gelöscht + eingefügt (keine Verschiebungs-Markierung `w:moveFrom`); Tabellen
   und Bilder ganz; Formatänderungen als Textänderung; Front-Matter-Änderungen (Titel, Datum)
   erscheinen auf dem Deckblatt ohne Markierung; nur Word, keine Präsentation (Epic-Frage 2).
6. **Tests** `tests/generation/docx/test_compare.py`: eingefügter/gelöschter/geänderter Absatz,
   Wortänderung in einem Satz, ersetzte Tabelle, Liste mit neuem Punkt, unveränderte Datei →
   keine Markierung; „Annehmen" simulieren (alle `w:del` entfernen, `w:ins` auspacken) ergibt
   dasselbe XML wie die neue Fassung ohne Vergleich — der eigentliche Beweis, dass nichts verloren
   geht; Öffnen in Word ist Prüfpunkt des Menschen.

## Akzeptanzkriterien

- [ ] `./run.sh compare alt.md neu.md` ergibt ein Word-Dokument, das Word ohne Reparatur
      öffnet und dessen Änderungen im Überprüfen-Modus sichtbar sind.
- [ ] Alle Änderungen annehmen ergibt die neue Fassung, alle ablehnen die alte (Text und
      Struktur; Tabellen und Bilder als Ganzes).
- [ ] `--since <rev>` holt die alte Fassung aus Git; Autor und Datum stehen an jeder Änderung.
- [ ] Die Grenzen stehen in Hilfetext und Anleitung.

## Offene Fragen

1. Soll bei großen Umstellungen (mehr als die Hälfte der Blöcke geändert) das Werkzeug warnen,
   dass ein Vergleich wenig nützt, oder trotzdem schreiben? Vorschlag: schreiben und warnen.

> (2026-11-07) Schreiben und warnen.
2. Verschiebungen als `w:moveFrom`/`w:moveTo` erkennen (gleicher Block an anderer Stelle)?
   Vorschlag: in einer späteren Story, wenn der einfache Vergleich sich bewährt.

> (2026-11-07) Später, eigene Story.

## Notizen

- Abhängigkeiten: E03-S01/S02 (in Prüfung). Der Vergleich verträgt sich mit Variablen und
  Bausteinen (E11), weil er auf dem aufgelösten Markdown läuft.
