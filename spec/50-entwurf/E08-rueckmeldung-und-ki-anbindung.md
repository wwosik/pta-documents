# E08 Rückmeldung an den Schreiber und KI-Anbindung

> Status: Entwurf

## Ziel

Wer Markdown schreibt — Mensch oder KI —, erfährt, was die Generatoren beim Erzeugen umgehen
mussten, kann ein Dokument prüfen, ohne es zu erzeugen, und findet jede Funktion der Bibliothek in
einem von Tests gesicherten Beispiel. Ein KI-Host kann die Generatoren als ein Werkzeug einbinden.

## Motivation

vt-tools-libs hat nach dem DocLibs-Stand unserer Portierung vier Dinge dazubekommen (Pläne
00024–00027, siehe [Abgleich](../10-analysen/2026-11-07%20abgleich-vt-tools-libs.md)):
`GenerationResult` mit Hinweisen an den Schreiber, das Werkzeug `make_document`, die
Feature-Tour mit Tests und die Authoring Guides für alle Formate. Unser `generate()` gibt
heute `None` zurück: eine geteilte Folie, ein weggelassenes Bild oder ein als Text gezeigtes
HTML fällt erst beim Öffnen in Office auf — das eine KI im Klon nicht kann. Der Prüfbefehl mit
Stilregeln ist eigene Idee: die PTA-Musterfolien nennen Regeln („kein Fließtext in
Aufzählungen", Satzzeichen, Schreibweisen), die sich zum Teil prüfen lassen.

## Scope

| Story | Inhalt | Status |
| ----- | ------ | ------ |
| [E08-S01](../60-prüfung/E08-S01-hinweise-aus-der-erzeugung.md) | `GenerationResult` mit `GenerationNote`s aus DOCX, PPTX (und PDF): geteilte Folien, HTML weggelassen, Diagramm nicht gezeichnet, Bild vergrößert, fehlende Zeichen; Ausgabe im Werkzeug `generate` | in Prüfung |
| [E08-S02](../60-prüfung/E08-S02-pruefbefehl-und-stilregeln.md) | `./run.sh check`: Hinweise ohne Erzeugen, Stilregeln der PTA-Musterfolien, Statistik (Folien, Wörter, Dauer), Bild ohne Quelle | in Prüfung |
| [E08-S03](E08-S03-funktionsuebersicht-durch-tests.md) | `samples/funktionen/` als gesicherte Feature-Tour: zeigt jede Syntax der Guides, erzeugt ohne Hinweise, Rundreise-Erwartungen committet | Entwurf |
| [E08-S04](E08-S04-werkzeug-make-document.md) | `make_document` für KI-Hosts: Beschreibung, JSON Schema, Guide aus den Optionen, `run`, `reply` | zurückgestellt (2026-11-07) |

## Bereichsweite Entscheidungen

- Hinweise sind **keine Fehler**: das Dokument ist brauchbar, der Schreiber soll es nur besser
  machen können. Fehler bleiben `DocumentConversionError`.
- Hinweistexte sind, wie Fehlermeldungen, **englisch** im Code und werden dem Schreiber so
  gezeigt (`reason` ist heute auch englisch; die Anleitungen zitieren die Meldungen). Ändert der
  Mensch das, gilt es für Fehler und Hinweise zugleich.
- Jeder Hinweis hat einen stabilen `code` (kebab-case), die Zeile im Markdown (Front Matter
  mitgezählt) und einen Satz, der sagt, was geschah und was stattdessen zu tun ist.
- Die Werkzeuge in `tools/` zeigen Hinweise nach jeder Datei; der Exit-Code bleibt 0, wenn nur
  Hinweise vorliegen (Frage 1).

## Akzeptanz

Ein Markdown mit zu voller Folie, rohem HTML und einem `mermaid`-Block ohne Renderer ergibt in
PPTX und DOCX ein Dokument und drei Hinweise mit Zeilennummern; `./run.sh generate` zeigt sie;
`./run.sh check` zeigt dieselben ohne Datei zu schreiben; `samples/funktionen/` erzeugt ohne
einen einzigen Hinweis.

## Offene Fragen

1. Soll `./run.sh generate` mit Exit-Code ≠ 0 enden, wenn es Hinweise gab (streng, gut für eine
   KI, die auf den Exit-Code schaut), oder nur bei Fehlern (wie heute)? Vorschlag: nur bei
   Fehlern; `--strict` macht Hinweise zu Fehlern.

> (2026-11-07) Nur bei Fehlern; `--strict` macht Hinweise zu Fehlern.
2. Wird ein KI-Host die Bibliothek direkt aufrufen (E08-S04), oder bleibt „Claude Code im Klon"
   der einzige Weg? Ohne Host kann E08-S04 warten.

> (2026-11-07) Nein. Die KI (Claude Code, Copilot in VS Code) arbeitet im Klon und ruft
> `run.sh` auf; E08-S04 ist zurückgestellt.

## Notizen
