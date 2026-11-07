# E16-S02 Schulungs-Zeitplan aus Foliendauern

> Status: Entwurf
> Epic: [E16 Schulung und Zielgruppen](E16-schulung-und-zielgruppen.md)

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

- [ ] `{dauer=…}` und `{.break}` werden gelesen; falsche Werte werfen mit Zeile und Beispiel.
- [ ] Agenda mit `beginn:` zeigt Uhrzeiten je Kapitel und Pause; ohne `beginn:` wie bisher.
- [ ] `schedule` schreibt ein Word-Dokument mit der Zeitplantabelle; die Summe stimmt.
- [ ] Trainerfassung zeigt die geplante Zeit in den Notizen, Kundenfassung nicht.
- [ ] Hinweise bei fehlenden Dauern und Abweichung von `laenge:`.

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
