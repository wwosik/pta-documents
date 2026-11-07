# E17-S04 `watch`, Seitenumbrüche und Querformat-Abschnitte

> Status: Entwurf
> Epic: [E17 Qualität und Arbeitsfluss](E17-qualitaet-und-arbeitsfluss.md)

## Zusammenfassung

`./run.sh watch documents/<thema>` erzeugt die Dokumente eines Ordners bei jedem Speichern neu
und aktualisiert auf Wunsch die Vorschau. In Word und PDF lassen sich Seitenumbrüche setzen
(`::: pagebreak`, `# Kapitel {.newpage}`) und eine breite Tabelle in einen Querformat-Abschnitt
stellen (`::: landscape`), ohne das ganze Dokument quer zu drehen.

## Kontext

- `tools/generate/generate.py` erzeugt einmalig; Fehler und Hinweise (E08-S01) stehen im
  Terminal. `run.sh` führt jedes `tools/<name>/<name>.py` als Verb aus, ein neues Werkzeug
  braucht keinen Skripteintrag. Die Vorschau `./run.sh preview` kommt mit E10-S02.
- **watchfiles** (MIT, Rust-Kern mit Wheels für alle Plattformen) liefert Dateiänderungen ohne
  Polling; ohne Abhängigkeit geht Polling über `Path.stat().st_mtime` jede Sekunde (Frage 1).
- `---` allein im Absatz ist heute eine **Trennlinie** (E03-S02; `docx/writer.py` Z. 141
  `case "hr": self.horizontal_rule()`), in Präsentationen trennt `---` Inhalte auf benannte
  Layouts (E04-S01). Beides bleibt; der Seitenumbruch braucht eine eigene Syntax.
- Word: ein Seitenumbruch ist `<w:br w:type="page"/>` in einem Run oder `w:pageBreakBefore` in
  `w:pPr`; ein Abschnittswechsel ist ein `w:sectPr` in `w:pPr` des letzten Absatzes des
  Abschnitts mit `w:pgSz w:orient="landscape"` (Breite/Höhe vertauscht), eigenen `w:pgMar` und
  eigenen Kopf-/Fußzeilen-Relationen; die PTA-Querformat-Vorlagen (`PTA-Dokument_Querformat_*`)
  haben Kopf-/Fußzeile mit Logo an anderer Stelle (Designanalyse, Abschnitt *Kopf- und Fußzeile*;
  `design/word.py` kennt die Maße beider Varianten, E01-S01).
- PDF (E05-S02/S03): Seitenrahmen je Variante; ein Seitenwechsel innerhalb eines Dokuments
  zwischen Hoch- und Querformat ist dort eine Frage der Layout-Engine.
- Der DOCX-Konverter (E07-S02) überliest `w:sectPr` heute.

## Vorgeschlagener Ansatz

1. **`watch`** (`tools/watch/watch.py`, `./run.sh watch <ordner> [--preview] [--docx|--pptx]
   [--out <ordner>]`): beobachtet `*.md` und `images/**` des Ordners (nicht `documents/<thema>/
   vorschau/`, nicht die Ausgaben), entprellt 300 ms, erzeugt wie `generate` nur die geänderte
   Datei (bei Bildänderung alle), gibt Zeit, `wrote …`, Fehler und Hinweise aus, löscht nichts
   bei Fehlern (das alte Dokument bleibt); mit `--preview` danach `preview` für Präsentationen;
   Strg+C beendet sauber. Ein geöffnetes Word/PowerPoint sperrt die Datei: dann schreibt `watch`
   nach `<name>.neu.docx` und sagt es (Frage 2). Extra `watch = ["watchfiles>=1.0"]`; ohne Extra
   Polling (Frage 1).
2. **Seitenumbruch** (Syntax in E02-S02 registriert): Container `::: pagebreak` ohne Inhalt
   (ein Fehler, wenn er Inhalt hat) und Attribut `{.newpage}` auf `#`–`####` (Überschrift beginnt
   eine neue Seite). Word: leerer Absatz mit `w:br w:type="page"` bzw. `w:pageBreakBefore` an der
   Überschrift (bleibt bei Umbrüchen stabil, anders als ein eingefügter Umbruch); PDF: harter
   Seitenwechsel in der Layout-Engine; PowerPoint: `::: pagebreak` ist ein Fehler („Folien
   trennt `##`"), `{.newpage}` wird ignoriert; Konverter liest beide Formen zurück.
   Ein `::: pagebreak` direkt vor einer Überschrift wird zu `{.newpage}` zusammengefasst, damit
   kein Leerabsatz entsteht.
3. **Querformat-Abschnitt** `::: landscape` … `:::` (nur Word und PDF; in PowerPoint Fehler):
   - Word (`generation/docx/sections.py`): vor dem Container den laufenden Abschnitt mit einem
     `w:sectPr` (Hochformat, Kopien der Dokument-Kopf-/Fußzeilen-Relationen) abschließen, den
     Inhalt schreiben, danach ein `w:sectPr` Querformat mit `w:pgSz` vertauscht, `w:pgMar` und
     Kopf-/Fußzeilen aus der **Querformat-Vorlage** derselben Deckblatt-Variante (E01-S02 bettet
     sie ein; `design/word.py` liefert Maße und Teile); danach wieder Hochformat. Tabellen im
     Abschnitt nutzen die Querformat-Satzspiegelbreite (E03-S02 Tabellenbreite); Seitenzahlen
     laufen durch (`w:pgNumType` ohne Neustart).
   - PDF (E05-S02/S03): Seite im Querformat mit dem Querformat-Rahmen zeichnen, Seitenzahl
     weiter; Verweise und Lesezeichen bleiben.
   - Konverter: `w:sectPr` mit `orient="landscape"` zwischen Hochformat-Abschnitten wird
     `::: landscape`; andere Abschnittswechsel weiter überlesen.
   - In einem Querformat-Dokument (`vorlage: quer*`) ist `::: landscape` ein Fehler (Frage 3:
     oder `::: portrait` als Gegenstück?).
4. **Dokumentation:** `anleitung.md` Abschnitt 4 (Word) um „Seitenumbruch" und „Breite Tabelle
   im Querformat", Abschnitt „Beim Schreiben zuschauen: `watch`"; `ki-anleitung.md` empfiehlt
   `watch` nicht (die KI ruft `generate`/`check` gezielt auf), nennt aber `::: pagebreak` und
   `::: landscape`; Guides (E02-S05) listen die Container.
5. **Tests:** `tests/tools/test_watch.py` (Änderung erzeugt genau die Datei neu, Entprellung,
   Fehler lässt alte Datei stehen — mit Polling-Modus, damit der Test ohne Extra läuft);
   `tests/generation/docx/test_sections.py` (`::: landscape`: drei `w:sectPr`, Maße der
   Querformat-Vorlage, Kopf-/Fußzeile vorhanden, Rundreise liefert `::: landscape` zurück;
   `::: pagebreak` → `w:br type=page`; `{.newpage}` → `w:pageBreakBefore`); PDF-Tests nach
   E05-S02; `samples/funktionen/funktionen-bericht.md` zeigt beides.

## Akzeptanzkriterien

- [ ] `./run.sh watch documents/x` erzeugt nach dem Speichern einer Markdown-Datei nur diese
      neu und zeigt Fehler und Hinweise; `--preview` aktualisiert die PNGs.
- [ ] `::: pagebreak` und `{.newpage}` ergeben in Word und PDF einen Seitenwechsel an der
      Stelle; die Rundreise gibt sie zurück.
- [ ] `::: landscape` um eine Tabelle ergibt in Word einen Querformat-Abschnitt mit den Kopf-/
      Fußzeilen und Maßen der PTA-Querformat-Vorlage, davor und danach Hochformat; Word öffnet
      ohne Reparatur (Prüfpunkt des Menschen); im PDF dasselbe Bild.
- [ ] In Präsentationen sind beide Container Fehler mit verständlicher Meldung.

## Offene Fragen

1. `watchfiles` als Extra `watch` (ereignisgesteuert, sofort) oder nur Polling ohne Abhängigkeit
   (eine Sekunde Verzögerung, keine Installation)? Vorschlag: beides — Extra, wenn vorhanden,
   sonst Polling mit Hinweis.

>

2. Wenn Word die Zieldatei gesperrt hat: in `<name>.neu.docx` schreiben (Vorschlag), warten und
   erneut versuchen, oder Fehler?

>

3. Gegenstück `::: portrait` für Querformat-Dokumente, oder nur `::: landscape` in
   Hochformat-Dokumenten? Vorschlag: beides, dieselbe Technik, kaum Mehraufwand.

>

## Notizen

- Abhängigkeiten: E02-S02 (Container), E10-S02 (`preview`), E05-S02/S03 (PDF-Seiten),
  E07-S02 (Konverter), E01-S02 (eingebettete Querformat-Vorlagen).
- `::: landscape` ist für die PTA praktisch die einzige legitime Ausnahme von „ein Dokument, eine
  Vorlage": breite Kostentabellen und Projektpläne (E11-S03, Gantt-Idee) brauchen sie.
