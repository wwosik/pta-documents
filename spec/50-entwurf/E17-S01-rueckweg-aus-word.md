# E17-S01 Rückweg aus Word: Kommentare hin und zurück, Änderungen als Vorschlag

> Status: Entwurf
> Epic: [E17 Qualität und Arbeitsfluss](E17-qualitaet-und-arbeitsfluss.md)

## Zusammenfassung

Zwei Richtungen: Aus Markdown entstehen echte Word-Kommentare (`[Text]{.comment="Bitte
prüfen"}`, `::: comment Autor`), damit Fragen an den Kunden oder an Reviewer im Dokument stehen.
Und ein zurückgeschicktes DOCX mit Kommentaren und Änderungsverfolgung wird in das Markdown
zurückgeführt: Kommentare als `::: comment`-Blöcke an der passenden Stelle, Änderungen als
Markierung zur Durchsicht oder — auf Wunsch — direkt übernommen.

## Kontext

- `generation/docx/writer.py` (812 Zeilen) schreibt Absätze und Runs; Fußnoten baut er bereits
  als eigenen Part (`footnotes.xml`, `_collect_footnotes`, `_save_footnotes`) — Kommentare sind
  in OOXML genauso ein Part (`word/comments.xml`, Relationship `comments`), im Text
  `w:commentRangeStart`/`w:commentRangeEnd` um die Runs und `w:commentReference` in einem
  eigenen Run; jeder Kommentar hat `w:id`, `w:author`, `w:date`, `w:initials`.
- `conversions/docx.py` (357 Zeilen, E07-S02, umgesetzt): `_render_paragraph`, `_render_runs`,
  `_render_inline`; es überliest heute `w:ins`, `w:del`, `w:commentReference` nicht ausdrücklich —
  `w:del`-Text (`w:delText`) fällt weg, `w:ins`-Text wird wie normaler Text gelesen. Der
  Konverter kann Kommentare und Änderungen also nur mit einer Option ausgeben.
- E12-S02 ordnet zwei Markdown-Fassungen mit `difflib` einander zu (Blockebene, dann Wortebene);
  dieselbe Zuordnung dient hier zwischen dem zurückgelesenen Word-Text und dem Markdown.
- Die Flow-Syntax (E02-S02) kennt Container `::: name args` und `[Wörter]{.klasse}`; `.comment`
  kommt dort als Klasse mit Attribut hinzu.

## Vorgeschlagener Ansatz

1. **Syntax** (in `generation/common/layout_syntax.py`, E02-S02): Inline
   `[markierter Text]{.comment="Kommentartext" author="Name"}` (`author` optional, sonst Front
   Matter `autor`, sonst „PTA Documents"); Block `::: comment Name` … `:::` kommentiert den
   folgenden Block (oder bei Blockende den vorhergehenden — Frage 1); in PPTX wird ein Kommentar
   eine PowerPoint-Notiz-Anmerkung (`ppt/comments/`, Epic-Frage 1), im PDF weggelassen mit
   Hinweis `comment-dropped` (E08-S01).
2. **DOCX schreiben** (`generation/docx/comments.py`): Part `word/comments.xml` wie die Fußnoten
   anlegen, Kommentare nummerieren, Range um die Runs des markierten Textes, Referenzrun mit
   Formatvorlage `Kommentarzeichen`/`CommentReference` (in der PTA-Vorlage prüfen, sonst Standard);
   Datum jetzt, `w:initials` aus den Großbuchstaben des Namens.
3. **Konverter** (`conversions/docx.py`): `ConversionOptions.review: bool` (Standard aus). An:
   `w:ins`-Text wird `==Text==`, `w:del`-Text `~~Text~~` (jeweils mit `author`/`date` in
   `meta` für Schritt 4), Kommentare werden `::: comment Autor (JJJJ-MM-TT)`-Blöcke nach dem
   Absatz, den sie berühren, mit dem markierten Text als erstem Zitat (`> …`), damit die Stelle
   auch ohne Range erkennbar bleibt. Aus: wie heute, aber `w:del`-Text bleibt weg und `w:ins`
   wird gelesen (Dokument im Zustand „alles angenommen").
4. **Rückweg** (`generation/docx/review_import.py`, öffentlich `import_review(markdown,
   reviewed_docx: bytes, apply: bool) -> ReviewResult(markdown, comments, changes, unmatched)`):
   - DOCX mit `review=True` nach Markdown lesen;
   - die Blöcke beider Seiten wie in E12-S02 zuordnen (das Markdown ohne Front Matter, Word
     ohne Deckblatt/Historie/Verzeichnisse — die Blöcke der Vorlage werden anhand ihrer
     Formatvorlagen übersprungen);
   - Kommentare an den zugeordneten Markdown-Block hängen (`::: comment` direkt danach);
   - Änderungen: ohne `--apply` als `==neu==`/`~~alt~~` in den Markdown-Absatz übertragen, mit
     `--apply` den Absatztext durch die Word-Fassung ersetzen; Zeichenformat des Markdown-Absatzes
     bleibt, wo die Wortebene es zulässt (sonst Markierung auf den ganzen Absatz);
   - was sich nicht zuordnen lässt (neue Absätze ohne Nachbarn, geänderte Tabellen, Bilder),
     kommt in einen Block `::: comment Rückweg` am Ende mit dem Word-Text, damit nichts verloren
     geht, und in `unmatched`.
5. **Werkzeug** `tools/review-import/review-import.py`: `./run.sh review-import kunde.docx
   documents/x/angebot-bericht.md [--apply] [--out datei.md]` (Verbname Frage 2); ohne `--out`
   wird die Markdown-Datei überschrieben und die alte Fassung als `<name>.vor-review.md`
   daneben gelegt; Ausgabe: Zahl der Kommentare, Änderungen, nicht Zugeordnetes mit Zeilen.
6. **Grenzen** in Hilfetext, `anleitung.md` und `ki-anleitung.md`: verschobene Absätze gelten
   als gelöscht + neu; Änderungen in Tabellen, Bildern, Code nur als Ganzes im Sammelblock;
   Formatänderungen ohne Textänderung werden ignoriert; Kommentare an Deckblatt oder Fußzeile
   landen im Sammelblock. Für die KI: nach `review-import` das Markdown lesen, die
   `::: comment`-Blöcke abarbeiten, `==`/`~~` auflösen, dann `generate`.
7. **Tests** `tests/generation/docx/test_comments.py` (Kommentar schreiben → Konverter mit
   `review=True` liest ihn an derselben Stelle zurück) und `tests/generation/docx/test_review_import.py`
   mit selbst erzeugten DOCX, in deren XML Tests `w:ins`/`w:del`/Kommentare einsetzen: Kommentar
   an Absatz 3 landet nach Absatz 3; geändertes Wort wird `==`/`~~`; `--apply` ergibt den neuen
   Text; unverändertes DOCX ändert das Markdown nicht (Idempotenz); gelöschter Absatz → `~~…~~`.

## Akzeptanzkriterien

- [ ] `[Text]{.comment="…"}` und `::: comment` erzeugen Word-Kommentare am richtigen Text, die
      Word im Überprüfen-Bereich zeigt (Prüfpunkt des Menschen).
- [ ] `./run.sh review-import` setzt jeden Kommentar eines zurückgeschickten DOCX an den
      passenden Absatz und markiert Textänderungen; mit `--apply` entspricht der Absatztext dem
      Word-Text.
- [ ] Nichts aus dem DOCX geht verloren: nicht Zuordenbares steht im Sammelblock.
- [ ] Ein unverändertes DOCX lässt das Markdown unverändert.

## Offene Fragen

1. Kommentiert `::: comment` den **folgenden** Block (wie ein Hinweis davor) oder den
   **vorhergehenden** (wie eine Randnotiz)? Vorschlag: den folgenden; der Rückweg schreibt die
   Blöcke entsprechend **vor** den betroffenen Absatz.

> (2026-11-07) Den folgenden Block.

2. Verbname: `review-import` (Vorschlag), `import-review` oder `merge`?

> (2026-11-07) `review-import`.

3. Sollen die `::: comment`-Blöcke beim nächsten `generate` wieder Word-Kommentare werden
   (Dialog mit dem Kunden über mehrere Runden), oder nur Markierung für den Autor sein, die
   `generate` weglässt? Vorschlag: wieder Kommentare; wer sie loswerden will, löscht sie.

> (2026-11-07) Wieder Kommentare.

## Notizen

- Abhängigkeiten: E02-S02 (Container, Attribute), E12-S02 (Zuordnung), E07-S02 (Konverter).
- Ein Kunde ohne Word-Änderungsverfolgung schickt oft ein frei editiertes DOCX zurück; dann ist
  `review-import` ohne Änderungsmarken ein Vergleich Word-Text ↔ Markdown mit allen Unterschieden
  als Vorschlag — dasselbe Verfahren, nur alles „geändert".
