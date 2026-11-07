# E09-S01 Sprechernotizen

> Status: Entwurf
> Epic: [E09 Präsentieren](E09-praesentieren.md)
> Milestone: [M02 Rückmeldung und Folien-Syntax](M02-rueckmeldung-und-folien-syntax.md)

## Zusammenfassung

Ein Block `::: notes` … `:::` unter einer Folie wird deren Notizenseite in PowerPoint, auf dem
Notizenmaster der PTA-Vorlage. Der PPTX-Konverter liest Notizenseiten als `::: notes` zurück, Word
lässt sie weg. Damit kann eine KI dem Vortragenden zu jeder Folie den Sprechtext mitgeben.

## Kontext

- vt-tools-libs: `~/mvv/vt-tools-libs/src/VtToolsLibs.DocumentGeneration.Pptx/NotesPages.cs`
  (110 Zeilen: Notizenmaster der Vorlage oder ein ergänzter mit Folienbild oben und Notizen
  unten; `Add`, `Write` je Notizenfolie) und `DeckWriter.cs` (`Notes(canvas, slide.Notes)`,
  Z. 209 und 461 ff.). Regeln laut `docs/VtToolsLibs.DocumentGeneration.Pptx.md` (*Presenting*):
  Notizen gehören zur **ersten** Folie ihrer Überschrift (auch Titel- und Trennfolien), mehrere
  Blöcke werden zusammengefügt; Absätze, Listen mit Aufzählungszeichen, fett, kursiv, Code und
  Links; Tabellen und Bilder in Notizen entfallen; Fortsetzungsfolien („Forts.") haben keine
  Notizen; ein Deck ohne Notizen bekommt keinen Notizenmaster.
- Hier: `markdown/parser.py` (32 Zeilen) kennt keine `:::`-Container — E02-S02 führt
  `mdit_py_plugins.container` ein und prüft Namen in `layout_syntax.check`; `generation/pptx/
  parser.py` (385 Zeilen) sammelt je Überschrift `Item`s, `_container` (Z. 222) durchläuft
  verschachtelte Token; `model.py` hat `Slide` ohne Notizenfeld; `writer.py` (529 Zeilen)
  schreibt mit python-pptx. `conversions/pptx.py` (174 Zeilen) liest nur `ppt/slides/`.
- Die eingebetteten Vorlagen `slides-basis.pptx`, `slides-basis-en.pptx` und
  `slides-schulung.pptx` enthalten bereits `ppt/notesMasters/notesMaster1.xml`: der Master der
  PTA-Vorlage wird genommen, ein eigener wird nie gebaut. python-pptx hat `slide.notes_slide`
  (legt die Notizenfolie auf dem Notizenmaster der Präsentation an) und `notes_text_frame`.

## Vorgeschlagener Ansatz

1. **Syntax** (gemeinsam mit E02-S02): `notes` in `layout_syntax.CONTAINERS` aufnehmen, ohne
   Argumente, in jedem Format gültig. Ein `::: notes` außerhalb eines Abschnitts (vor dem ersten
   `#`) ist ein Fehler mit Zeile: „A '::: notes' on line 12 belongs under a heading."
2. **Modell:** `Slide.notes: tuple[Paragraph, ...]` in `generation/pptx/model.py` (leer als
   Standard). `DeckParser._section` sammelt Container `notes` aus den Items der Überschrift und
   hängt ihre Absätze an die erste Folie des Abschnitts; Tabellen, Bilder und Codeblöcke darin
   werden weggelassen; Listenpunkte werden Absätze mit `level` ≥ 1. Für Titel-, Trenn- und
   Abschlussfolie gilt die Regel „kein Inhalt unter `#`" (E04-S01) **nicht** für `::: notes`.
3. **Schreiben** in `generation/pptx/notes.py`: `write_notes(slide: PptxSlide, paragraphs)` legt
   mit `slide.notes_slide` die Notizenfolie an, prüft, dass der Platzhalter `body` existiert, und
   schreibt die Absätze mit `writer.write_paragraphs` (Runs fett/kursiv/Code/Link; Aufzählung
   über `lvl`, Aufzählungszeichen aus dem Notizenmaster). Nur die erste Folie einer geteilten
   Folie (`fitting`, „Forts.") bekommt Notizen. Ohne Notizen entsteht keine Notizenfolie.
4. **Word:** `generation/docx/writer.py` überspringt Container `notes` (kein Fehler, kein Text).
   PDF: E05-S04 erweitert um `notizen: ja` (dort geplant: `showNotes`).
5. **Konverter** (`conversions/pptx.py`): hat eine Folie eine Notizenfolie (`notesSlide`-
   Relationship), wird der Text ihres `body`-Platzhalters nach der Folie als
   `::: notes` … `:::` ausgegeben (Absätze, Listen mit `-`); leere Notizen und Notizen, die nur
   den Platzhaltertext der Vorlage enthalten, entfallen. `ConversionOptions.notes: bool = True`
   für Aufrufer, die nur den Folieninhalt wollen.
6. **Rundreise-Test** (`tests/generation/pptx/`): `deck.md` um Notizen an einer Titel-, einer
   Trenn- und zwei Inhaltsfolien (eine davon so lang, dass sie geteilt wird) ergänzen; erwartetes
   Markdown enthält die Notizen genau einmal je Überschrift. Test gegen ein Deck ohne Notizen:
   keine `ppt/notesSlides/`. Prüfung der XML gegen die PTA-Vorlage: Notizenfolie referenziert den
   Notizenmaster der Vorlage.
7. **Doku:** `docs/anleitung.md` §5 und `docs/ki-anleitung.md` (Präsentation) um `::: notes`
   ergänzen, mit dem Rat, zu jeder Folie zwei bis fünf Sätze Sprechtext zu schreiben;
   `samples/funktionen/funktionen-praesentation.md` zeigt es; E04-S06 nimmt es in den Guide auf.

## Akzeptanzkriterien

- [ ] `::: notes` unter `#`, `##` und `# … {.closing}` wird zur Notizenseite der ersten Folie des
      Abschnitts; PowerPoint zeigt sie in der Notizenansicht ohne Reparaturmeldung.
- [ ] Absätze, Listen, fett, kursiv, Code und Links bleiben in den Notizen erhalten; Tabellen und
      Bilder darin erzeugen keinen Fehler und keinen Inhalt.
- [ ] Ein Deck ohne `::: notes` hat keine Notizenfolien; Fortsetzungsfolien haben keine Notizen.
- [ ] Der PPTX-Konverter gibt Notizenseiten als `::: notes` wieder; die Rundreise ist stabil.
- [ ] Word lässt `::: notes` kommentarlos weg.

## Offene Fragen

1. Sollen Notizen einer **geteilten** Folie auf der ersten Folie bleiben (wie vt-tools-libs) oder
   auf jeder Teilfolie wiederholt werden? Vorschlag: erste Folie.

> (2026-11-07) Auf jeder Teilfolie wiederholen.
2. Soll der Konverter Notizen standardmäßig ausgeben (Vorschlag: ja, für die Rundreise und weil
   eine KI beim Lesen fremder Decks den Sprechtext braucht)?

> (2026-11-07) Ja, standardmäßig.

## Notizen

- Abhängigkeit: `:::`-Container im Parser (E02-S02). Wird E09-S01 vorher umgesetzt, wird das
  Container-Plugin hier eingeführt und E02-S02 baut darauf auf.
- (2026-11-07, E08-S01) Der Hinweis-Code `NoteCodes.NOTES_DROPPED` (`notes-dropped`) ist in
  `generation/common/result.py` angelegt, wird aber noch nirgends erzeugt: der DOCX-Writer soll ihn
  hier melden, wenn er `::: notes` weglässt (`self.notes.add(...)` im `BodyWriter`).
