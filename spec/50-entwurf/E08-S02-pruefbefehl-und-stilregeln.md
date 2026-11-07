# E08-S02 Prüfbefehl und Stilregeln

> Status: Entwurf
> Epic: [E08 Rückmeldung an den Schreiber und KI-Anbindung](E08-rueckmeldung-und-ki-anbindung.md)

## Zusammenfassung

`./run.sh pruefen documents/<thema>` prüft Markdown-Dateien, ohne Dokumente zu schreiben: Fehler
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
     `--quellen` gesetzt ist;
   - `style-alt-text`: Bild ohne Alt-Text (siehe E13-S03);
   - `style-heading-numbers`: Überschrift beginnt mit eigener Nummer („1. Einleitung"), obwohl
     Word nummeriert.
   Regeln sind abschaltbar: Front Matter `pruefung: aus` oder `--ohne style-words`.
3. **Statistik** (`CheckStats`): Folien (Titel, Kapitel, Inhalt, Fortsetzungen), Wörter gesamt
   und je Folie (min/median/max), Notizen-Wörter (E09-S01), geschätzte Dauer (2 Minuten je
   Inhaltsfolie, plus Notizen bei 120 Wörtern/Minute — Faustregel, als solche ausgewiesen);
   Word: Wörter, Überschriften, Tabellen, Abbildungen, grobe Seitenzahl (Wörter / 350 zuzüglich
   Tabellen und Bilder) mit dem Hinweis, dass Word erst beim Öffnen zählt.
4. **Werkzeug** `tools/check/check.py`, `./run.sh pruefen <datei-oder-ordner> [--streng]
   [--ohne <code>,…] [--json]`: Formatwahl wie `generate`; Ausgabe je Datei: `OK`/`FEHLER`, dann
   Hinweise mit Zeile, dann die Statistik in zwei Zeilen; `--json` für Werkzeuge. Exit-Code 1 bei
   Fehlern, mit `--streng` auch bei Hinweisen.
5. **Dokumentation:** `anleitung.md` Abschnitt „Prüfen, bevor man erzeugt", `ki-anleitung.md`
   Regel 3 empfiehlt `pruefen` vor `generate`; Codes in `verwendung.md`.
6. **Tests:** `tests/check/test_style_rules.py` je Regel positiv und negativ; `samples/` ohne
   Stilhinweise (Ausnahmen in den Beispielen ausdrücklich mit `pruefung: aus` je Datei, wenn sie
   absichtlich Grenzen zeigen, etwa die Fortsetzungsfolie in `funktionen-praesentation.md`).

## Akzeptanzkriterien

- [ ] `./run.sh pruefen` schreibt keine Datei und meldet dieselben Fehler und Hinweise wie
      `generate`, dazu Stilhinweise und Statistik.
- [ ] Jede Stilregel hat einen Code, ist einzeln abschaltbar und in `verwendung.md` beschrieben.
- [ ] `--json` liefert eine maschinenlesbare Form; `--streng` setzt den Exit-Code bei Hinweisen.
- [ ] `samples/gsb` besteht die Prüfung ohne Hinweise.

## Offene Fragen

1. Welche Grenzwerte gelten (sieben Punkte, 80 Wörter, 60 Zeichen)? Die PTA-Musterfolien nennen
   keine Zahlen; die Werte oben sind Vorschläge zum Einstellen.

>

2. Soll die Quellenregel (`style-image-source`) immer gelten oder nur mit `QUELLEN.md`/`--quellen`?

>

## Notizen

- Die Dauer-Schätzung ist bewusst grob; sie soll Decks mit 60 Folien für 30 Minuten entlarven,
  nicht Minuten vorhersagen.
