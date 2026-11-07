# E14-S04 Dokument-Skelette: `./run.sh new`

> Status: Entwurf
> Epic: [E14 Dokumenttypen der Beratung](E14-dokumenttypen-der-beratung.md)
> Milestone: [M06 Inhalte, Dokumenttypen und Dokumentpflege](M06-inhalte-und-dokumentpflege.md)

## Zusammenfassung

`./run.sh new angebot documents/muster-ag` legt einen Dokumentordner mit fertigem Startpunkt an:
Markdown mit vorbelegtem Front Matter und der üblichen Gliederung der Dokumentart, `images/`,
`QUELLEN.md`. Die Arten sind `angebot`, `konzept`, `statusbericht`, `protokoll`, `schulung` und
`praesentation`; Platzhalter wie `{{kunde}}` werden von der Kommandozeile oder im Dialog gefüllt.

## Kontext

- Heute beginnt jedes Dokument mit Kopieren aus `samples/gsb/` oder `samples/funktionen/`
  (`docs/anleitung.md`, Abschnitt 2); die Beispiele sind Demonstrationen, keine Vorlagen für
  Angebote oder Protokolle. Eine KI (`docs/ki-anleitung.md`) muss Front Matter und Gliederung
  jedes Mal aus der Anleitung zusammensetzen.
- `tools/generate/generate.py` zeigt das Muster eines Werkzeugs (Argumente, Formatwahl über
  Dateinamen-Endungen `-bericht`, `-praesentation`); `run.sh`/`run.ps1` führen jedes
  `tools/<name>/<name>.py` als Verb aus — `new` braucht keinen Skripteintrag.
- Variablen `{{name}}` und `--var`: E11-S01; Bausteine (`::: include firmenprofil`): E11-S02;
  Protokoll-Syntax: E14-S01; Anforderungen: E14-S02; Kalkulation und Unterschriften: E14-S03.

## Vorgeschlagener Ansatz

1. **Skelette** in `samples/skelette/<art>/` mit `README.md` (Tabelle: Art | Zieldatei |
   Gliederung), je Art eine oder zwei Markdown-Dateien:
   - `angebot`: `{{thema}}-angebot-bericht.md` — Ausgangslage, Zielsetzung, Leistungsumfang,
     Vorgehen und Zeitplan, Aufwand und Preise (`{.calc mwst=19}`), Annahmen und Abgrenzung,
     Ansprechpartner (`::: include personen/…`), Unterschriften (`::: signatures`);
   - `konzept`: Management Summary, Ausgangslage, Ziele, Anforderungen (`::: requirement`),
     Lösungskonzept, Architektur (Mermaid-Platz), Risiken, nächste Schritte, Anhang;
   - `statusbericht`: Gesamtstatus (Status-Label), Fortschritt seit letztem Bericht, nächste
     Schritte, Risiken und Probleme, Entscheidungsbedarf, Termine, Aufgaben (`::: task`);
   - `protokoll`: Front Matter mit `protokoll: ja`, `teilnehmer`, Tagesordnung, je Punkt ein
     Abschnitt mit `::: decision` / `::: task` / `::: open` als Kommentar-Beispiel;
   - `schulung`: `…-praesentation.md` mit `vorlage: schulung`, `kennzeichnung: intern`,
     Lernziele, Agenda-Kapitel, Übungsfolien, Zusammenfassung, Abschluss; dazu
     `…-handout-bericht.md` als Teilnehmerunterlage;
   - `praesentation`: Titel, drei Kapitel mit je einer Textfolie, Fazit-Box, Kontakt, Abschluss.
   Jedes Skelett trägt Kommentare `<!-- … -->` mit Schreibhinweisen, die beim Erzeugen
   verschwinden, und erzeugt ohne Fehler und ohne Hinweise (Test).
2. **Werkzeug** `tools/new/new.py`: `./run.sh new <art> <ordner> [--var name=wert …] [--force]`:
   - legt `<ordner>/`, `<ordner>/images/`, `<ordner>/QUELLEN.md` (aus `samples/gsb/QUELLEN.md`
     entleert) an; bricht ab, wenn der Ordner Markdown enthält, außer mit `--force`;
   - kopiert die Dateien des Skeletts und ersetzt die Platzhalter der Kopie (`{{kunde}}`,
     `{{thema}}`, `{{titel}}`, `{{autor}}`, `{{datum}}` → heute) mit `--var`-Werten; fehlende
     Werte fragt es im Terminal ab (bei nicht interaktivem Aufruf, etwa durch eine KI: Fehler mit
     der Liste der fehlenden Namen). Platzhalter, die ins Dokument gehören sollen
     (`{{kunde}}` im Text für E11-S01), bleiben als `\{{kunde}}` im Skelett geschützt;
   - benennt die Dateien nach `--var thema=…` (`nordlicht-angebot-bericht.md`);
   - gibt die nächsten Schritte aus: Datei öffnen, `./run.sh check`, `./run.sh generate`.
3. **Front Matter** je Skelett vollständig vorbelegt (`titel`, `untertitel`, `autor`, `ort`,
   `datum`, `vorlage`, `kennzeichnung`, bei Word `inhaltsverzeichnis: ja`), mit allen Schlüsseln,
   die für die Art gelten — auskommentiert, wo optional (`# firma: …`).
4. **Dokumentation:** `docs/anleitung.md` Abschnitt 2 beginnt mit `new`; `docs/ki-anleitung.md`
   empfiehlt `new` als ersten Schritt und nennt die Arten; `samples/skelette/README.md` beschreibt
   die Gliederungen.
5. **Tests** `tests/tools/test_new.py`: jede Art anlegen, Platzhalter ersetzt, Ordnerinhalt wie
   erwartet, Abbruch bei vorhandenem Markdown, `--force`; jedes Skelett (mit Beispielwerten) läuft
   durch `generate` ohne Fehler und ohne Hinweise (E08-S01), sobald die verwendete Syntax
   umgesetzt ist — bis dahin markiert `README.md`, welche Skelette noch Platzhaltertext statt
   Syntax enthalten.

## Akzeptanzkriterien

- [ ] `./run.sh new <art> <ordner>` legt für jede der sechs Arten einen Ordner an, aus dem
      `./run.sh generate` ohne Fehler ein Dokument erzeugt.
- [ ] Platzhalter werden aus `--var` oder im Dialog gefüllt; nicht interaktiv fehlende Werte
      sind ein Fehler mit Namensliste.
- [ ] Ein vorhandener Ordner mit Markdown wird ohne `--force` nicht überschrieben.
- [ ] Anleitung und KI-Anleitung nennen `new` als Startpunkt.

## Offene Fragen

1. Gibt es im Haus verbindliche Gliederungen für Angebot, Konzept, Statusbericht, Protokoll
   (etwa aus dem Qualitätsmanagement)? Dann ersetzen sie die oben vorgeschlagenen.

> (2026-11-07) Keine verbindlichen Gliederungen bekannt; die vorgeschlagenen gelten.
2. Sollen die Skelette in `samples/skelette/` liegen (Vorschlag, neben den Beispielen) oder in
   einem eigenen Ordner `templates/` im Repo-Root, und dürfen Anwender eigene in
   `documents/_skelette/` ergänzen (Muster wie Bausteine, E11 Frage 1)?

> (2026-11-07) `samples/skelette/`, eigene in `documents/_skelette/` (Muster wie Bausteine).
3. Soll `new` ohne Angabe der Art ein Menü zeigen? Vorschlag: ja, interaktiv; nicht interaktiv
   Fehler mit Artenliste.

> (2026-11-07) Ja: interaktiv Menü, nicht interaktiv Fehler mit Artenliste.

## Notizen

- Abhängigkeiten: E11-S01 (Variablen im Text), E14-S01 bis E14-S03 für die Syntax der
  Skelette; `new` selbst ist unabhängig und kann vorher mit einfacheren Skeletten kommen.
