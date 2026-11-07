# E16-S01 Zielgruppenfassungen

> Status: Entwurf
> Epic: [E16 Schulung und Zielgruppen](E16-schulung-und-zielgruppen.md)

## Zusammenfassung

Blöcke, Folien und Abschnitte mit `{.internal}` oder in `::: internal` erscheinen nur in der
internen Fassung; `::: exercise` steht in jeder Fassung, `::: solution` nur beim Trainer.
`./run.sh generate --audience kunde|intern|trainer` wählt die Fassung, das Front Matter `fassung:`
setzt die Vorgabe des Dokuments. Interne Fassungen heißen `…-intern.docx` / `…-intern.pptx` und
tragen automatisch die Kennzeichnung `intern`.

## Kontext

- Keine Vorlage in DocLibs oder vt-tools-libs. Verwandt: `{.build}`/`{.frag}` als Attribut auf
  Blöcken (E09-S02) und die Container aus E02-S02 (`layout_syntax.CONTAINERS`,
  `heading_attributes.VALID`) — dieselben Stellen, an denen `internal`, `exercise`, `solution`
  registriert werden.
- Heute: `markdown/parser.py` liefert einen flachen Token-Strom (markdown-it-py) an
  `generation/docx/writer.py` und `generation/pptx/parser.py`; eine Zeile `{.klasse}` allein ist
  noch unbekannt. `tools/generate/generate.py` wählt Format aus dem Dateinamen und kennt die
  Schalter `--docx`, `--pptx`, `--out`.
- Kennzeichnung: `kennzeichnung: vertraulich | intern | entwurf | kein` (E12-S03, E04-S05) ist ein
  Front-Matter-Schlüssel, den `apply_front_matter` in die Optionen überträgt.

## Vorgeschlagener Ansatz

1. **Syntax** (E02-S02 erweitert): Container `internal`, `exercise`, `solution` ohne Argumente in
   allen Formaten; Heading-Attribut `.internal` auf `#` und `##` (ganzes Kapitel bzw. ganze Folie
   samt Notizen); Blockmarkierung `{.internal}` auf Listen, Tabellen, Absätzen, Bildern wie
   `{.build}`. `::: solution` muss direkt auf `::: exercise` folgen oder darin stehen, sonst
   Fehler: „A '::: solution' on line 40 needs a '::: exercise' right before it."
2. **Zielgruppe** `Audience` (`StrEnum`: `KUNDE`, `INTERN`, `TRAINER`) in
   `generation/common/audience.py`; `filter_tokens(tokens, audience, notes) -> list[Token]`
   entfernt bei `kunde` alles Interne und alle Lösungen, bei `intern` die Lösungen, bei `trainer`
   nichts; `exercise`-Zäune bleiben als Container für E04-S03/E03-S03 (Kasten „Übung"), `solution`
   als Kasten „Lösung" nur beim Trainer. Je weggelassenem Block ein Zähler; am Ende **ein**
   Hinweis `audience-omitted` (E08-S01): „12 internal blocks and 3 solutions were left out for
   the audience 'kunde'."
3. **Front Matter** `fassung: kunde | intern | trainer` (Standard: Epic-Frage 1) in `Keys`; die
   Generatoren bekommen `options.audience`, rufen `filter_tokens` vor dem Parsen auf und setzen,
   wenn die Fassung nicht `kunde` ist und `kennzeichnung` fehlt, `kennzeichnung = intern`.
4. **Werkzeug** `generate --audience kunde|intern|trainer|alle`: überschreibt `fassung:`;
   Dateiname `<name>.docx` für `kunde`, `<name>-intern.docx`, `<name>-trainer.pptx` sonst;
   `alle` erzeugt jede Fassung, in der sich der Token-Strom unterscheidet (sonst nur eine).
   `check` (E08-S02) zeigt Statistik je Fassung.
5. **Konverter:** nichts zu tun — weggelassene Blöcke sind nicht im Dokument. Rundreise-Tests
   laufen je Fassung gegen `deck-kunde.roundtrip.expected.md` und `deck-trainer….`.
6. **Doku:** `anleitung.md` §2 (Schalter, Dateinamen), §5 (Übung/Lösung), `ki-anleitung.md`
   (Regel: Preise, interne Bemerkungen und Lösungen immer in `internal`/`solution` schreiben, damit
   die Kundenfassung sauber bleibt); `samples/funktionen` zeigt alle drei Container; E04-S06,
   E03-S05 nehmen sie in die Guides auf.
7. **Tests** `tests/generation/common/test_audience.py`: jede Kombination Syntax × Fassung; Folie
   mit `.internal` fehlt ganz samt Notizen (E09-S01); Kapitelnummern der Trennfolien (E04-S01)
   zählen ohne die weggelassenen; Hinweis mit richtigen Zahlen; `solution` ohne `exercise` wirft.

## Akzeptanzkriterien

- [ ] `--audience kunde` enthält keinen Text aus `internal`- und `solution`-Blöcken, `intern`
      keine Lösungen, `trainer` alles; die Kundenfassung ist byteweise die Standardfassung.
- [ ] Interne und Trainerfassungen heißen `-intern`/`-trainer` und tragen die Kennzeichnung
      `intern`, sofern das Front Matter nichts anderes setzt.
- [ ] Ein Hinweis nennt die Zahl der weggelassenen Blöcke; Kapitel- und Foliennummern sind lückenlos.
- [ ] Rundreise je Fassung stabil; Guides und Anleitungen nennen die Syntax.

## Offene Fragen

1. Soll `::: internal` auch **innerhalb** einer Tabelle gehen (Spalte „intern" ausblenden), etwa
   über eine Kopfzelle `Kommentar {.internal}`? Vorschlag: nein, erst wenn der Bedarf da ist —
   Tabellen werden stattdessen doppelt geschrieben.

> (2026-11-07) Nein, vorerst nicht.

2. Sollen Lösungen in der Teilnehmerfassung (`kunde`) als leerer Kasten „Lösung" mit Linien
   bleiben (zum Ausfüllen) oder ganz fehlen? Vorschlag: ganz fehlen; das Handout (E16-S03) hat
   ohnehin Notizlinien.

> (2026-11-07) Ganz fehlen.

## Notizen

- `exercise`/`solution` als Kästen zeichnen E04-S03 (Folien, PTA-Stil der Fazit-Box) und
  E03-S03 (Word, Tabellenrahmen „PTA"); hier wird nur gefiltert und registriert.
