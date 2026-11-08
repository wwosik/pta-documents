# E16-S02 Schulungs-Zeitplan aus Foliendauern

> Status: in Prüfung
> Epic: [E16 Schulung und Zielgruppen](../50-entwurf/E16-schulung-und-zielgruppen.md)
> Milestone: [M04 Präsentieren und Schulung](../50-entwurf/M04-praesentieren-und-schulung.md)

## Zusammenfassung

`{dauer=5}` auf einer Folie oder einem Kapitel gibt Minuten an, `## Pause {.break dauer=15}` eine
Pause. Daraus entstehen eine Agenda mit Uhrzeiten, ein Trainer-Zeitplan als Tabelle und die
geplante Uhrzeit in den Sprechernotizen jeder Folie; die Summe wird mit der geplanten Länge
verglichen und mit der Schätzung aus E08-S02 abgeglichen.

## Kontext

- Keine Vorlage in DocLibs oder vt-tools-libs. E08-S02 schätzt die Vortragsdauer grob (zwei
  Minuten je Inhaltsfolie); hier gibt der Autor sie an.
- Heading-Attribute: `heading_attributes.split` liest heute `.closing` und `layout="…"`; E02-S02
  fügt `.dark`, `kicker` hinzu, E04-S04 `.agenda`, `.interim` … Attribute mit Wert (`key=value`)
  gibt es bereits (`layout`).
- Agenda nur ausdrücklich: `## Agenda {.agenda}` mit genau einer Liste → `Agenda (kurz)`/
  `Agenda (lang)` (E04-S04, Entscheidung 2026-11-06). Sprechernotizen: E09-S01 (`::: notes`,
  auf jeder Teilfolie wiederholt). Fassungen: E16-S01.

## Vorgeschlagener Ansatz

1. **Syntax:** Attribut `dauer=<minuten>` (ganze Zahl oder `1h30`) auf `#` (Kapitel: Summe der
   Folien darunter, wenn gesetzt überschreibt es sie — Frage 1) und `##`; `.break` auf `##` für
   eine Pausenfolie (Layout `Zwischenfazit 01` mit Text „Pause · 15 min" — Frage 2) oder, ohne
   Inhalt, nur ein Eintrag im Zeitplan ohne Folie. Front Matter `beginn: 09:00` (Startzeit) und
   `laenge: 4h` bzw. `laenge: 240` (geplante Gesamtlänge), beide nur PPTX.
2. **Modell:** `Slide.duration: int | None`, `Slide.is_break`; `generation/pptx/schedule.py`
   baut aus den Folien einen `Schedule`: Einträge (Kapitel oder Pause, Beginn, Ende, Dauer),
   Summe gesetzter Dauern, Zahl der Folien ohne Dauer; Fortsetzungsfolien erben die Dauer ihrer
   ersten Folie (zählen einmal).
3. **Agenda mit Uhrzeiten:** steht `{.agenda}` und `beginn:`, bekommt jeder Agendapunkt, der ein
   Kapitel benennt, die Uhrzeit vorangestellt („09:00 Einführung"); Pausen erscheinen als eigene
   Punkte. Mehr als acht Punkte bleiben ein Fehler (E04-S04).
4. **Sprechernotizen:** jede Folie mit Zeitplan bekommt als erste Notizenzeile „Geplant:
   09:20–09:25 (5 min)"; ohne `::: notes` entsteht dafür eine Notizenseite nur beim Trainer
   (Fassung `trainer`, E16-S01), damit Teilnehmerexporte sauber bleiben.
5. **Zeitplan-Dokument:** `./run.sh schedule <praesentation.md>` schreibt `<name>-zeitplan.docx`
   (PTA-Vorlage `hoch-ohne-deckblatt`, E03): Tabelle Von | Bis | Dauer | Kapitel/Folie | Notizen
   (leer, für den Trainer), Pausen hervorgehoben (`==…==`), Summe; dieselbe Tabelle setzt E16-S03
   vorn ins Handout. Der Generator liefert sie auch als Markdown (`Schedule.to_markdown()`), damit
   eine KI sie prüfen kann.
6. **Hinweise** (E08-S01): `schedule-missing` („7 slides have no 'dauer'; the schedule assumes 2
   min each."), `schedule-length` („Planned 240 min, slides sum to 265 min."), und ein Vergleich
   mit der Schätzung aus E08-S02, wenn die Angabe um mehr als die Hälfte abweicht
   (`schedule-estimate`).
7. **Doku und Tests:** `anleitung.md` §5 (Schulung planen), `ki-anleitung.md`; Guide E04-S06.
   Tests: Summen, Uhrzeiten über Pausen hinweg, `1h30`, fehlende `beginn:` (Agenda ohne
   Uhrzeiten, Zeitplan mit relativen Zeiten „+0:15"), Fassung `kunde` ohne Zeitnotizen.

## Akzeptanzkriterien

- [x] `{dauer=…}` und `{.break}` werden gelesen; falsche Werte werfen mit Zeile und Beispiel.
- [x] Agenda mit `beginn:` zeigt Uhrzeiten je Kapitel und Pause; ohne `beginn:` wie bisher.
- [x] `schedule` schreibt ein Word-Dokument mit der Zeitplantabelle; die Summe stimmt.
- [x] Trainerfassung zeigt die geplante Zeit in den Notizen, Kundenfassung nicht.
- [x] Hinweise bei fehlenden Dauern und Abweichung von `laenge:`.

## Offene Fragen

1. `dauer` auf einem Kapitel: Summe der Folien darunter (Folien ohne Angabe teilen den Rest)
   oder nur Anzeige im Zeitplan? Vorschlag: Rest gleichmäßig verteilen, dann braucht nicht jede
   Folie eine Zahl.

> (2026-11-07) Rest gleichmäßig verteilen.

2. Pausenfolie zeigen (`Zwischenfazit 01` mit „Pause · 15 min", bleibt während der Pause auf der
   Leinwand) oder Pause nur im Zeitplan? Vorschlag: Folie zeigen, mit `{.break}` ohne Inhalt.

> (2026-11-07) Folie zeigen, `{.break}` ohne Inhalt.

3. Verbname `schedule` oder Zeitplan immer nur als Teil des Handouts (E16-S03)? Vorschlag:
   eigenes Verb, weil der Trainer den Zeitplan oft vor dem Handout braucht.

> (2026-11-07) Eigenes Verb `schedule`.

## Notizen

- Für Kundenpräsentationen ohne Schulungscharakter genügt `dauer` auf wenigen Folien plus
  `laenge:`, um die Überlänge eines Decks früh zu sehen (ergänzt E08-S02).

## Implementierungsnotizen

Umgesetzt am 2026-11-08 (docs-2), ohne Zwischenprüfung.

### Entscheidungen

- **Syntax:** `dauer=…` ist ein Überschriftenattribut an `#` und `##` und der **einzige** Wert,
  der ohne Anführungszeichen geht (`{dauer=5}`, `{dauer=1h30}`; `dauer="5"` geht auch). Andere
  Klammern ohne Anführungszeichen bleiben wie bisher Text (`## Mengen {a=b}`). Werte: Minuten
  (`5`, `90`, `45min`), Stunden (`4h`) oder Stunden und Minuten (`1h30`), mehr als 0
  (`generation/common/durations.py`); falsche Werte werfen über `layout_syntax.check` mit
  `Line N:` und Beispielen.
- **`.break` ist eine PTA-Folienart** (`heading_attributes.SLIDE_KINDS`, `KIND_LAYOUTS["break"]`
  = `Zwischenfazit 01`/`02`): dadurch gelten die Regeln der Folienarten von selbst (nur `##`,
  nicht mit `.dark`/`kicker`/einer anderen Art, `layout="Zwischenfazit 02"` wählbar). Die Folie
  ist ein `InterimSlide` mit dem Titel „<Überschrift> · 15 min". Ohne `dauer` oder mit Inhalt ist
  sie ein Fehler (Frage 2: Folie zeigen, ohne Inhalt).
- **Kapiteldauer** (Frage 1): Folien ohne Angabe teilen den Rest in ganzen Minuten (die ersten
  bekommen die übrigen Minuten). Bleibt Zeit, endet das Kapitel erst nach seiner Dauer; brauchen
  die Folien mehr, gilt deren Summe mit Hinweis `schedule-length` an der Kapitelzeile.
- **Modell** in `generation/common/training_schedule.py` (`Schedule`, `ScheduleEntry`,
  `EntryKind`, `build`, `deck_schedule`, `schedule_document`), aus den Level-0-Überschriften
  der gefilterten Fassung gebaut — so zählen geteilte Folien einmal, und `check` und das
  Werkzeug brauchen keinen PPTX-Lauf dafür. Einen Zeitplan hat ein Deck nur, wenn es `dauer`,
  eine Pause, `beginn:` oder `laenge:` nennt.
- **Agenda** (`KindReader.timed`): nur mit `beginn:`. Punkte, die ein Kapitel nennen (Vergleich
  ohne Groß-/Kleinschreibung und Leerraum), bekommen „09:05 " vorangestellt; jede Pause wird ein
  Punkt „09:25 Pause" vor dem ersten Kapitel, das nach ihr beginnt. Eine Agenda-Liste, die kein
  Kapitel nennt, bleibt ganz unverändert (auch ohne Pausen). Mehr als acht Punkte bleiben ein
  Fehler; die Meldung nennt die Zahl der Pausen.
- **Sprechernotizen** (`DeckParser._planned`): nur in der Trainerfassung, erste Zeile
  „Geplant: 09:20–09:25 (5 min)" (englisch „Planned"), ohne `beginn:` „+0:20–+0:25"; auf jeder
  Teilfolie einer geteilten Folie; Trennfolien zeigen die Zeit ihres Kapitels; Titel- und
  Abschlussfolie bekommen keine.
- **Hinweise:** `schedule-missing` (einmal, an der ersten Folie ohne Angabe), `schedule-length`
  (Summe ≠ `laenge:`, ohne Zeile; Kapitelüberlauf, mit Zeile) aus dem PPTX-Generator;
  `schedule-estimate` nur aus `check`, weil die Schätzung von E08-S02 das Probedeck braucht —
  verglichen wird die Sprechzeit **ohne Pausen**, und nur, wenn mindestens eine Folie eine
  Dauer hat.
- **Werkzeug** `./run.sh schedule` (`tools/schedule/schedule.py`, Frage 3): erzeugt erst das
  Deck in den Speicher (Fehler und Hinweise wie beim Erzeugen), dann `<name>-zeitplan.docx` auf
  `hoch-ohne-deckblatt` mit Überschrift „Zeitplan: <Titel>", einer Zeile „Beginn 09:00 · geplante
  Länge 240 min · Summe 265 min" und der Tabelle; `--markdown` druckt das Markdown,
  `--audience` wählt die Fassung (Standard `trainer`), `--strict` wie bei `generate`.
- **Beispiel** `samples/funktionen/zeitplan-praesentation.md` (`vorlage: schulung`,
  `fassung: trainer`, `beginn`, `laenge`, Kapitel- und Foliendauern, Pause, Agenda mit
  Uhrzeiten); es erzeugt ohne Hinweise und besteht `check --strict`.

### Abweichungen

- Das Modell liegt in `generation/common/training_schedule.py` statt `generation/pptx/schedule.py`:
  `generation/common/schedule.py` gibt es schon (Zeitstrahl/Gantt, E15-S01), und `check` sowie
  das Werkzeug brauchen den Zeitplan ohne PPTX-Lauf.
- Keine Felder `Slide.duration`/`Slide.is_break`: die Dauer hängt an der Überschrift
  (`ScheduleEntry.heading`), die Pause ist die Folienart `break`.
- Die Tabelle zeigt Kapitel- und Folienzeilen (Kapitel fett), angenommene Dauern als „≈ 2 min"
  und darunter einen Satz dazu; die Zeile „Summe" steht in der Tabelle.
- `tools/generate`: `--audience alle` schreibt für ein Deck mit Zeitplan immer auch die
  Trainerfassung (sonst wäre sie mangels anderen Token-Stroms weggefallen, und die Zeitnotizen
  gäbe es nur mit `--audience trainer`).
- Die Texte des Zeitplans (Spaltenköpfe, „Geplant") stehen in `training_schedule.TEXTS`, nicht in
  `design.variants.GeneratedTexts` (um die gemeinsam genutzte Datei nicht zu berühren).

### Warnungen

- **Warnung:** Die Zeitnotiz bekommt **nur** die Trainerfassung, nicht die interne (Plan:
  „nur beim Trainer"; Akzeptanz nennt nur Trainer und Kunde). Vorsichtigste Wahl.
- **Warnung:** Pausen zählen **nicht** zur `dauer` ihres Kapitels, und Pausen am Ende eines
  Kapitels stehen im Zeitplan hinter dem Kapitel. Der Plan sagt dazu nichts; sonst hätte eine
  Pause im Kapitel die Zeit seiner Folien aufgefressen.
- **Warnung:** Alles nach der Abschlussfolie (`{.closing}`) ist nicht geplant (passt zu
  Backup-Folien aus E16-S04); `dauer` an der Abschlussfolie ist ein Fehler.
- **Warnung:** `dauer` an der Titelfolie (erstes `#`) wirkt wie an einem Kapitel für die
  Folien davor (ohne eigene Kapitelzeile); ohne Folien darunter ist es die Zeit der Titelfolie.
- **Warnung:** `schedule-length` meldet jede Abweichung von `laenge:`, auch eine Minute.
- **Warnung:** Word und PDF nehmen `dauer` und `.break` an und lassen die Dauer weg; die Pause
  steht in Word fett (wie `.interim`), im PDF als Überschrift (wie die übrigen Folienarten).
  Die PPTX-Rundreise liest eine Pausenfolie als `{.interim}` „Pause · 15 min" zurück.
- **Warnung:** Folien vor dem ersten `#` (eigentlich ungewöhnlich) bilden eine Gruppe ohne
  Kapitel; ein danach folgendes `#` gilt im Zeitplan als Kapitel, obwohl PowerPoint es zur
  Titelfolie macht.

### Prüfpunkte

- `./run.sh generate samples/funktionen/zeitplan-praesentation.md --audience alle` schreibt
  Kunden- und Trainerfassung; in der Trainerfassung beginnt jede Notizenseite mit „Geplant: …",
  die Agenda zeigt „09:02 Grundlagen", „09:10 Pause", „09:15 Praxis", die Pausenfolie „Pause ·
  5 min". In PowerPoint öffnen (hier kein Office vorhanden).
- `./run.sh schedule samples/funktionen/zeitplan-praesentation.md --markdown` schreibt
  `zeitplan-praesentation-zeitplan.docx`; in Word öffnen (Tabelle, gelb markierte Pause,
  Kennzeichnung „intern"). Ein Exemplar liegt nach den Tests in `.tmp/review/zeitplan/`.
- `./run.sh check samples/funktionen --strict` bleibt grün; ein Deck mit `{dauer=60}` auf einer
  Folie meldet `schedule-estimate`.
- Tests: `tests/generation/common/test_durations.py`, `test_training_schedule.py` (Lesen,
  Fehler, Summen, Kapitelrest, Pausen, Uhrzeiten über Pausen und Mittag, relative Zeiten,
  `1h30`, Fassungen, Hinweise, Tabelle, Werkzeug) und `tests/generation/pptx/test_training_schedule.py`
  (Pausenfolie, Agenda mit/ohne `beginn:`, Notizen je Fassung, geteilte Folien, Word, HTML,
  `generate --audience alle`).

### Offene Punkte

- E16-S03 setzt dieselbe Tabelle (`Schedule.to_markdown()`) vorn ins Handout.
- Der Guide (E04-S06) nimmt die Syntax auf, wenn er entsteht.
- Ob die interne Fassung die Zeitnotizen auch zeigen soll (siehe Warnung).
