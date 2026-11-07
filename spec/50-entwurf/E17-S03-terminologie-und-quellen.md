# E17-S03 Terminologieprüfung und Quellen aus `QUELLEN.md`

> Status: Entwurf
> Epic: [E17 Qualität und Arbeitsfluss](E17-qualitaet-und-arbeitsfluss.md)
> Milestone: [M06 Inhalte, Dokumenttypen und Dokumentpflege](M06-inhalte-und-dokumentpflege.md)

## Zusammenfassung

`check` kennt die bevorzugten Schreibweisen der PTA („E-Mail", nicht „Email"; „PTA", nicht
„pta") aus einer Terminologieliste und meldet oder korrigiert Abweichungen. `QUELLEN.md`, bisher
Prosa und Tabelle für Menschen, bekommt ein festes Format, aus dem `[@kennung]` im Text
Fußnoten, Quellenzeilen auf Folien und ein Quellenverzeichnis werden — und `check` sieht, welche
Quelle fehlt oder unbenutzt ist.

## Kontext

- E08-S02: `./run.sh check` mit `style-…`-Codes, abschaltbar; die Regel `style-image-source`
  sucht heute nur nach Wörtern wie „Foto:", „Quelle:", „CC", „©" in Titel oder Unterschrift —
  ohne zu wissen, welche Quellen es gibt.
- `samples/gsb/QUELLEN.md`: Abschnitte *Text* (Prosa mit Links) und *Fotos* (Tabelle Datei |
  Motiv | Urheber | Lizenz | Quelle). `docs/ki-anleitung.md` Regel 5 verlangt Urheber und Lizenz
  in der Bildunterschrift bzw. auf der Folie und in `QUELLEN.md`; `tools/generate/generate.py`
  überspringt `quellen.md` beim Erzeugen.
- Fußnoten gibt es in Word (E03-S02) und im PDF (E05-S02); auf Folien gibt es keine Fußnoten,
  aber die Diagramm-Layouts der Vorlage haben einen Platzhalter „Quelle" (E04-S04), und eine
  kleine Zeile am unteren Rand der Inhaltsfläche ist PTA-üblich.
- Die Bibliothek liest keine Dateien: Terminologie und Quellen kommen als `DocumentResource`
  (Content-Type `text/markdown`) in `MarkdownDocument.resources`, wie Bilder.

## Vorgeschlagener Ansatz

1. **Terminologieliste** als Markdown-Tabelle `| falsch | richtig | Hinweis |`, offiziell in
   `samples/terminologie.md` (versioniert, mit den ersten Einträgen: `Email → E-Mail`, `pta →
   PTA`, `Powerpoint → PowerPoint`, `Standart → Standard`, `Mandant → Kunde` (Hinweis statt
   Ersetzung)), eigene Ergänzungen in `documents/_terminologie.md` (git-ignoriert, überschreibt
   bei gleichem „falsch"). Ein Eintrag `/regex/` in der Spalte „falsch" ist ein regulärer
   Ausdruck (`/\bca\.\s/` → `etwa `); Groß-/Kleinschreibung zählt, wenn „falsch" einen
   Großbuchstaben enthält. `generation/common/terminology.py`: `Terminology.parse(markdown)`,
   `find(text) -> list[Finding(line, column, wrong, right, hint)]`, nur außerhalb von Code,
   Links-URLs und Front Matter (Wortgrenzen).
2. **`check`:** meldet jeden Fund als `style-terminology` mit Zeile („'Email' → 'E-Mail'");
   `--fix` ersetzt in der Markdown-Datei alle Funde mit eindeutigem „richtig" (keine Hinweise),
   schreibt die Zahl der Ersetzungen und lässt Code unberührt; `pruefung: aus` oder
   `--skip style-terminology` schaltet ab. Das Werkzeug lädt beide Listen und reicht sie als
   Ressource `terminologie.md` herein.
3. **`QUELLEN.md`-Format** (abwärtskompatibel: Prosa bleibt erlaubt und wird ignoriert): jede
   Quelle eine Listenzeile `- [kennung]: Autor/Urheber, *Titel*, Lizenz, URL, Stand` — oder die
   bestehende Tabelle mit einer zusätzlichen ersten Spalte `Kennung`. `markdown/sources.py`:
   `Sources.parse(markdown) -> dict[str, Source(key, author, title, licence, url, note)]`,
   Fehler mit Zeile bei doppelter Kennung oder fehlendem Autor.
4. **Im Text:** `[@kennung]` (auch `[@a; @b]`) wird in Word und PDF eine Fußnote „Autor, Titel,
   Lizenz, URL" (eine Fußnote je Kennung, Wiederholungen verweisen auf dieselbe), in PowerPoint
   eine Quellenzeile am unteren Rand der Inhaltsfläche (8 pt, Grau `787878`, mehrere Kennungen
   mit `·` getrennt; im Diagramm-Layout der Platzhalter „Quelle"); Bilder nennen ihre Quelle mit
   `quelle=kennung` im Bildtitel (`![Alt](images/a.jpg "Unterschrift" quelle=barania)`), was die
   Unterschrift um „Foto: Urheber, Lizenz" ergänzt — statt es von Hand zu schreiben wie heute in
   `samples/gsb/`. Unbekannte Kennung ist ein Fehler mit Zeile und den gültigen Kennungen.
5. **Quellenverzeichnis:** Front Matter `quellenverzeichnis: ja | nein` (Standard: ja, sobald
   `[@…]` oder `quelle=` vorkommt — Frage 1): in Word und PDF ein Abschnitt „Quellen" am Ende
   (Überschrift 1 ohne Nummer, Liste in Reihenfolge der ersten Verwendung oder alphabetisch —
   Frage 2), in PowerPoint eine Folie „Quellen" vor der Abschlussfolie, bei mehr als zwölf
   Quellen fortgesetzt.
6. **`check`:** `style-source-unknown` (Kennung ohne Eintrag — eigentlich Fehler, hier als
   Vorabprüfung), `style-source-unused` (Eintrag ohne Verwendung), und `style-image-source`
   (E08-S02) gilt als erfüllt, wenn das Bild `quelle=` trägt oder seine Datei in `QUELLEN.md`
   steht — dieselben Daten, eine Logik.
7. **Werkzeuge:** `generate` und `check` reichen `QUELLEN.md` (Groß-/Kleinschreibung egal) aus
   dem Dokumentordner als Ressource herein; `samples/gsb/QUELLEN.md` wird auf das Format
   umgestellt und die Markdowns nutzen `quelle=` — das Beispiel bleibt lizenzkonform, nur
   kürzer. `ki-anleitung.md` Regel 5 beschreibt das Format und `[@kennung]`.
8. **Tests:** `tests/check/test_terminology.py` (Fund, Regex, Groß-/Kleinschreibung, Code
   unberührt, `--fix` idempotent), `tests/markdown/test_sources.py` (Format, Fehler),
   Generatoren: Fußnote je Kennung einmal, Quellenzeile auf der Folie, Bildunterschrift ergänzt,
   Verzeichnis in Reihenfolge; `samples/gsb` ohne `style-source-*`-Hinweise.

## Akzeptanzkriterien

- [ ] `check` meldet „Email" mit Zeile und Vorschlag; `check --fix` ersetzt es, nicht aber in
      Code; eigene Einträge in `documents/_terminologie.md` wirken.
- [ ] `[@kennung]` ergibt in Word und PDF eine Fußnote, in PowerPoint eine Quellenzeile;
      `quelle=` ergänzt die Bildunterschrift um Urheber und Lizenz.
- [ ] Das Quellenverzeichnis nennt jede verwendete Quelle einmal; unbekannte Kennungen sind
      Fehler, unbenutzte Einträge Hinweise.
- [ ] `samples/gsb` nutzt das Format und erzeugt ohne Hinweise.

## Offene Fragen

1. Quellenverzeichnis automatisch, sobald Quellen verwendet werden (Vorschlag), oder nur mit
   `quellenverzeichnis: ja`?

> (2026-11-07) Automatisch; `quellenverzeichnis: nein` schaltet ab.

2. Reihenfolge im Verzeichnis: nach erster Verwendung (Vorschlag — wie Fußnoten) oder
   alphabetisch nach Autor?

> (2026-11-07) Nach erster Verwendung.

3. Soll `--fix` auch Einträge mit Hinweis (`Mandant → Kunde`) ersetzen, wenn `--fix=all`
   gesetzt ist? Vorschlag: nein, Hinweise bleiben Entscheidungen des Autors.

> (2026-11-07) Nein.

## Notizen

- Abhängigkeiten: E08-S02 (`check`), E03-S02/E05-S02 (Fußnoten), E04-S04 (Platzhalter
  „Quelle"), E13-S01 (Abkürzungen nutzen dieselbe Core-Regel-Technik für Wortfunde).
- Für Bildquellen deckt sich das mit E13-S03 (Alt-Texte): beide Prüfungen laufen über die
  Bild-Token und können in einem Durchgang gemeldet werden.
