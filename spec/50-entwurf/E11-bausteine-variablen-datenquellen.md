# E11 Bausteine, Variablen und Datenquellen

> Status: Entwurf

## Ziel

Markdown, das sich nicht jedes Mal neu schreiben muss: Platzhalter, die aus dem Front Matter oder
von der Kommandozeile gefüllt werden; wiederverwendbare Bausteine (Firmenprofil, Leistungsübersicht,
Kontaktfolien, Rechtliches) in einer gemeinsamen Ablage; Tabellen und Charts direkt aus CSV- und
Excel-Dateien im Dokumentordner; QR-Codes aus einem Link.

## Motivation

Weder DocLibs noch vt-tools-libs kennen das — dort ist jedes Markdown eine in sich geschlossene
Datei. In einer IT-Beratung wiederholen sich aber ganze Abschnitte: Jedes Angebot trägt das
Firmenprofil und die Kontaktfolie des Teams, jeder Statusbericht dieselbe Legende, jede Schulung
denselben rechtlichen Hinweis. Wer das kopiert, pflegt es an zwanzig Stellen. Zahlen für Tabellen
und Charts liegen ohnehin in Excel; sie abzutippen ist Arbeit und Fehlerquelle. Ein QR-Code auf
der letzten Folie führt die Teilnehmer einer Schulung ohne Abtippen zur Umfrage oder zum Repo.

## Scope

| Story | Inhalt | Status |
| ----- | ------ | ------ |
| [E11-S01](E11-S01-variablen.md) | Platzhalter `{{name}}` aus Front Matter `variablen.<name>`, Kommandozeile `--var` und eingebauten Werten | Entwurf |
| [E11-S02](E11-S02-bausteine.md) | Bausteine aus `documents/_bausteine/` einbinden, mit Bildern; Personen-Bausteine für Kontaktfolien | Entwurf |
| [E11-S03](E11-S03-tabellen-und-charts-aus-dateien.md) | Tabellen und `chart`-Blöcke aus CSV-/XLSX-Dateien des Dokumentordners | Entwurf |
| [E11-S04](E11-S04-qr-codes.md) | `![…](qr:https://…)` erzeugt einen QR-Code in PTA-Blau | Entwurf |

## Bereichsweite Entscheidungen

- **Die Bibliothek liest keine Dateien.** Bausteine, Datendateien und Variablen von der
  Kommandozeile löst das Werkzeug `tools/generate/generate.py` auf und übergibt sie als
  `DocumentResource` bzw. in `MarkdownDocument.metadata`; die Generatoren sehen nur Ressourcen,
  wie heute bei Bildern. Das hält die Rundreise-Tests und den Aufruf aus Python unverändert.
- **Fehler nennen die Quelle.** Eine Meldung aus einem Baustein nennt Baustein und Zeile darin
  (`firmenprofil.md, Zeile 12`), eine aus einer Datendatei Datei und Zeile bzw. Zelle.
- **Deutsch, was der Schreiber liest:** Front-Matter-Schlüssel (`variablen.`, Werte), der
  Absatz `Tabelle aus:`, Fehlermeldungen wie bisher englisch (Code-Konvention der
  `DocumentConversionError`, siehe E02).
- Alle vier Stories gelten für Word, PowerPoint und — sobald E05 steht — PDF; die Konverter (E07)
  bleiben unberührt, lesen also das fertige Ergebnis zurück (gefüllte Variablen, eingebundene
  Bausteine, QR-Code als Bild).
- Keine Vorlagensprache (Jinja o. Ä.): nur `{{name}}`, keine Bedingungen, keine Schleifen. Wer
  Logik braucht, erzeugt das Markdown mit einem Skript oder einer KI.

## Akzeptanz

`samples/angebot/` (neues Beispiel): ein Angebot bindet Firmenprofil und eine Kontaktfolie aus
`samples/bausteine/` ein, füllt `{{kunde}}` und `{{datum}}`, zeigt eine Kostentabelle aus
`daten/kosten.csv` und endet mit einem QR-Code — in Word und PowerPoint, ohne Hinweise aus der
Erzeugung (E08-S01).

## Offene Fragen

1. Wo liegen die gemeinsamen Bausteine der PTA: im Repo (`samples/bausteine/`, versioniert, für
   alle gleich) oder beim Anwender (`documents/_bausteine/`, git-ignoriert)? Vorschlag: beides —
   das Repo liefert die offiziellen Bausteine, `documents/_bausteine/` überschreibt bei gleichem
   Namen.

> (2026-11-07) Beides: Repo liefert die offiziellen Bausteine, `documents/_bausteine/` überschreibt bei gleichem Namen.
2. Sollen Variablen auch im Front Matter selbst gelten (`titel: Angebot für {{kunde}}`)?
   Vorschlag: ja, außer in `variablen.*` selbst.

> (2026-11-07) Ja, außer in `variablen.*`.

## Notizen

- (2026-11-07) Umsetzung gewünscht (Entscheidung des Menschen zu allen drei Epics E11–E13).
