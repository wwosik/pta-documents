# E08-S02 Prüfbefehl und Stilregeln

> Status: in Prüfung
> Epic: [E08 Rückmeldung an den Schreiber und KI-Anbindung](../50-entwurf/E08-rueckmeldung-und-ki-anbindung.md)
> Milestone: [M02 Rückmeldung und Folien-Syntax](../50-entwurf/M02-rueckmeldung-und-folien-syntax.md)

## Zusammenfassung

`./run.sh check documents/<thema>` prüft Markdown-Dateien, ohne Dokumente zu schreiben: Fehler
und Hinweise aus E08-S01, dazu Stilregeln aus den PTA-Musterfolien und eine Statistik (Folien,
Wörter je Folie, geschätzte Vortragsdauer, Seitenabschätzung). Für eine KI ist das der schnelle
Kontrollgang vor dem Erzeugen; für Menschen der Blick, ob ein Deck zu voll ist.

## Kontext

- Weder DocLibs noch vt-tools-libs haben einen Prüfbefehl; dort kommen Hinweise erst mit dem
  Dokument. Eigene Idee.
- Die PTA-Musterfolien nennen Regeln wörtlich (Designanalyse, Abschnitt *Regeln auf den
  Musterfolien*): nur die vorgegebenen Layouts, keine Fließtexte in Aufzählungen, einheitliche
  Satzzeichen am Zeilenende, Schreibweisen. Eine Regel zu Mindestschriftgrößen gibt es nicht; das
  Fitting (12 pt) ist unsere Untergrenze.
- `docs/ki-anleitung.md` Regel 5: fremde Bilder brauchen Urheber und Lizenz in Unterschrift oder
  auf der Folie und in `QUELLEN.md` (Muster `samples/gsb/`).
- Das Fitting in `generation/pptx/fitting.py` kennt die Höhe jedes Blocks; die Zahl der Folien
  steht nach dem `DeckWriter` fest. Für Word gibt es keine Seitenzahl ohne Layout-Engine (E05).

## Vorgeschlagener Ansatz

1. **Bibliothek** `generation/common/check.py`: `check(document, format, options) ->
   CheckResult(errors, notes, stats)`. Fehler kommen aus einem Probelauf des Generators in
   einen `io.BytesIO` (so bleibt nur ein Codepfad), Hinweise aus dessen `GenerationResult`
   (E08-S01); Stilregeln laufen auf den Parser-Tokens.
2. **Stilregeln** (`generation/common/style_rules.py`), je als Note mit Code `style-…`:
   - `style-bullets`: mehr als sieben Aufzählungspunkte auf einer Folie oder ein Punkt über 20
     Wörtern („Fließtext in Aufzählungen");
   - `style-words`: mehr als 80 Wörter auf einer Inhaltsfolie;
   - `style-punctuation`: gemischte Satzzeichen am Ende der Punkte einer Liste;
   - `style-title`: Folientitel über 60 Zeichen oder endend mit Punkt;
   - `style-image-source`: Bild ohne Urheber/Quelle in Titel oder Unterschrift (kein
     „Foto:", „Quelle:", „CC", „©"), wenn der Dokumentordner eine `QUELLEN.md` hat oder
     `--sources` gesetzt ist;
   - `style-alt-text`: Bild ohne Alt-Text (siehe E13-S03);
   - `style-heading-numbers`: Überschrift beginnt mit eigener Nummer („1. Einleitung"), obwohl
     Word nummeriert.
   Regeln sind abschaltbar: Front Matter `pruefung: aus` oder `--skip style-words`.
3. **Statistik** (`CheckStats`): Folien (Titel, Kapitel, Inhalt, Fortsetzungen), Wörter gesamt
   und je Folie (min/median/max), Notizen-Wörter (E09-S01), geschätzte Dauer (2 Minuten je
   Inhaltsfolie, plus Notizen bei 120 Wörtern/Minute — Faustregel, als solche ausgewiesen);
   Word: Wörter, Überschriften, Tabellen, Abbildungen, grobe Seitenzahl (Wörter / 350 zuzüglich
   Tabellen und Bilder) mit dem Hinweis, dass Word erst beim Öffnen zählt.
4. **Werkzeug** `tools/check/check.py`, `./run.sh check <datei-oder-ordner> [--strict]
   [--skip <code>,…] [--json]`: Formatwahl wie `generate`; Ausgabe je Datei: `OK`/`FEHLER`, dann
   Hinweise mit Zeile, dann die Statistik in zwei Zeilen; `--json` für Werkzeuge. Exit-Code 1 bei
   Fehlern, mit `--strict` auch bei Hinweisen.
5. **Dokumentation:** `anleitung.md` Abschnitt „Prüfen, bevor man erzeugt", `ki-anleitung.md`
   Regel 3 empfiehlt `check` vor `generate`; Codes in `verwendung.md`.
6. **Tests:** `tests/check/test_style_rules.py` je Regel positiv und negativ; `samples/` ohne
   Stilhinweise (Ausnahmen in den Beispielen ausdrücklich mit `pruefung: aus` je Datei, wenn sie
   absichtlich Grenzen zeigen, etwa die Fortsetzungsfolie in `funktionen-praesentation.md`).

## Akzeptanzkriterien

- [ ] `./run.sh check` schreibt keine Datei und meldet dieselben Fehler und Hinweise wie
      `generate`, dazu Stilhinweise und Statistik.
- [ ] Jede Stilregel hat einen Code, ist einzeln abschaltbar und in `verwendung.md` beschrieben.
- [ ] `--json` liefert eine maschinenlesbare Form; `--strict` setzt den Exit-Code bei Hinweisen.
- [ ] `samples/gsb` besteht die Prüfung ohne Hinweise.

## Offene Fragen

1. Welche Grenzwerte gelten (sieben Punkte, 80 Wörter, 60 Zeichen)? Die PTA-Musterfolien nennen
   keine Zahlen; die Werte oben sind Vorschläge zum Einstellen.

> (2026-11-07) Die vorgeschlagenen Werte (7 Punkte, 80 Wörter, 60 Zeichen, 20 Wörter je Punkt), einstellbar.
2. Soll die Quellenregel (`style-image-source`) immer gelten oder nur mit `QUELLEN.md`/`--sources`?

> (2026-11-07) Nur mit `QUELLEN.md` oder `--sources`.

## Notizen

- Die Dauer-Schätzung ist bewusst grob; sie soll Decks mit 60 Folien für 30 Minuten entlarven,
  nicht Minuten vorhersagen.

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08: `./run.sh check` (`tools/check/check.py`), Bibliothek
`generation/common/check.py` (`check`, `CheckOptions`, `CheckResult`, `DeckStats`,
`ReportStats`) und `generation/common/style_rules.py` (`style_notes`, `StyleCodes`,
`StyleLimits`, `skipped`). Doku in `docs/verwendung.md` (Abschnitt „Prüfen ohne Erzeugen"),
`docs/anleitung.md` (Abschnitt 2 „Prüfen, bevor man erzeugt"), `docs/ki-anleitung.md` (Regel 3,
Front-Matter-Tabelle, Checkliste).

### Entscheidungen

- Fehler und Hinweise kommen aus einem Probelauf von `DocxGenerator`/`PptxGenerator` in einen
  `BytesIO` — ein Codepfad, also genau die Meldungen von `generate`. Die Stilregeln laufen
  danach auf den Parser-Tokens (auch wenn die Erzeugung einen Fehler hat).
- Die Stilcodes stehen in `StyleCodes` (nicht in `NoteCodes`), die Hinweise sind aber gewöhnliche
  `GenerationNote`s und werden mit denen des Generators nach Zeile sortiert.
- Grenzen wie beschlossen (7 Punkte, 20 Wörter je Punkt, 80 Wörter, 60 Zeichen), einstellbar
  über `StyleLimits` (nur in der API; das Werkzeug hat keine Schalter dafür).
- `pruefung:` nimmt `aus`/`nein` (alle Stilregeln aus), `an`/`ja` (alle an) oder eine
  Komma-Liste von Codes, die übersprungen werden; ein unbekannter Code ist ein Fehler.
  `DocxGenerator` und `PptxGenerator` nehmen den Schlüssel an und ignorieren ihn
  (`Keys.CHECK`).
- Folien = `#`/`##` auf Token-Ebene 0 wie im PPTX-Parser. `style-bullets`, `style-words` und
  `style-image-source` gelten für `##`-Folien außer `{.contact}`; die Agenda darf 8 Punkte
  haben. `style-title` gilt für `#` und `##` außer der Titelfolie, `{.quote}` und `{.interim}`
  (dort sind Sätze gewollt); „…"/„..." ist kein Schlusspunkt.
- `style-punctuation`: `.`, `!`, `?` zählen gleich; eine Aufzählung `…;`/`…,` mit anderem
  Schluss beim letzten Punkt und ein Punkt mit `:` vor Unterpunkten sind erlaubt; Klammer oder
  Anführungszeichen am Ende verdecken kein Satzzeichen (`„Satz.“` endet mit Punkt, `(cont.)`
  ohne).
- `style-image-source`: Merkmale `Foto(s):`, `Bild(er):`, `Grafik:`, `Quelle(n):`,
  `Photo:`/`Image:`/`Source:`/`Credit:`, `CC`, `©`, `gemeinfrei`, `public domain`. PowerPoint:
  Bildtitel oder irgendein Text der Folie; Word: Bildtitel, der Absatz des Bildes oder der danach.
  Nur mit `QUELLEN.md` im Ordner der Datei oder `--sources` (Antwort 2).
- `style-alt-text` ist die einfache Regel (leerer Alt-Text); E13-S03 kann sie erweitern.
- `style-heading-numbers` nur Word, `#`–`###` (die nummerierten Ebenen), und nur Nummern mit
  Punkt (`1. …`, `2.3 …`) — `2026 in Zahlen` bleibt unbeanstandet.
- Statistik PowerPoint am Probe-Deck (Layoutname → Titel/Kapitel/Abschluss, sonst Inhalt;
  „(Forts.)"/„(cont.)" am Titel → Fortsetzung; Wörter ohne Titel-, Fußzeilen-, Nummer- und
  Datumsplatzhalter). Dauer = 2 min je Inhaltsfolie (Fortsetzungen eingeschlossen) + Notizen /
  120, aufgerundet. Word am Markdown: Wörter ohne Code und Notizen; Seiten = Wörter/350 + ½ je
  Tabelle und Abbildung, mindestens 1.
- `samples/funktionen/funktionen-praesentation.md` hat `pruefung: style-bullets, style-words`
  (die Folie „Viel Text wird verkleinert" ist absichtlich voll); alle anderen Beispiele bestehen
  ohne Ausnahme, `samples/gsb` mit Quellenregel.

### Abweichungen

- **Warnung:** Ausgabe englisch wie bei `generate` (`OK`/`ERROR`, Statistikzeilen) statt
  `OK`/`FEHLER` aus dem Plan; Hinweiszeilen tragen hinten `[code]`. `ERROR` geht bei `check`
  nach stdout (bei `generate` nach stderr), damit die Ausgabe ein zusammenhängender Bericht ist.
- **Warnung:** Tests liegen gemäß Spiegelbaum in `tests/generation/common/test_style_rules.py`
  und `test_check.py` statt in `tests/check/`.
- Das Werkzeug lädt `tools/generate/generate.py` per `importlib`, um Dateinamen, Formatwahl und
  Ressourcen genauso zu behandeln; `--sources` ist ein zusätzlicher Schalter.
- Zusätzlich zur Statistik des Plans: Zahl der Abschlussfolien.

### Prüfpunkte

- Grenzwerte und Wortlaut der Meldungen an echten Decks prüfen; die Wortzählung (Folge mit
  Buchstabe oder Ziffer) ist grob.
- `style-image-source` in Word erkennt die Quelle nur im Titel, im Absatz des Bildes oder im
  nächsten Absatz.

### Offene Punkte

- PDF: `check` nimmt nur DOCX/PPTX; der PDF-Generator braucht `Keys.CHECK` in `VALID_KEYS` und
  sollte in `check` ergänzt werden (in E05-S01 notiert).
