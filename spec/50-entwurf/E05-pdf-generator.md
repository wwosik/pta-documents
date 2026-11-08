# E05 PDF-Generator im PTA-Design

> Status: Entwurf

## Ziel

Markdown → PDF/A-2b im Design der PTA-Word-Vorlagen: dieselben Seitenränder, Schriftgrößen,
Farben, Kopf- und Fußzeilen, nummerierten Überschriften und Tabellen wie ein DOCX aus [E03](E03-docx-generator.md).

## Motivation

DocLibs zeichnet PDFs mit einer eigenen Layout-Engine (`LayoutEngine.cs`, 1 200 Zeilen) in einem
generischen Brand-Design. Für die PTA soll ein PDF aussehen wie ein aus Word exportiertes
PTA-Dokument, ohne dass Word nötig ist.

## Scope

| Story | Inhalt | Status |
| ----- | ------ | ------ |
| [E05-S01](../60-prüfung/E05-S01-grundgeruest-pdf.md) | Grundgerüst: reportlab + pikepdf, Selawik/Segoe UI (E01-S03), PDF/A-2b-Nachweis mit veraPDF | in Prüfung |
| [E05-S02](../60-prüfung/E05-S02-layout-engine.md) | Layout-Engine portieren: Absätze, Listen, Tabellen, Bilder, Code, Seitenumbruchregeln, Lesezeichen, Links | in Prüfung |
| [E05-S03](../60-prüfung/E05-S03-pta-seitenrahmen.md) | PTA-Seitenrahmen: Deckblatt, Kopfzeile mit Logo und Verlaufslinie, Fußzeile, Hoch/Quer | in Prüfung |
| [E05-S04](../60-prüfung/E05-S04-zeichen-folien-syntax-grafiken.md) | Fehlende Zeichen (`replace_unsupported`), Folien-Syntax, Diagramme/Charts als Vektoren | in Prüfung |
| [E05-S05](E05-S05-authoring-guide-pdf.md) | Authoring Guide PDF | Entwurf |

## Bereichsweite Entscheidungen

- **Eigene Layout-Engine** (Portierung aus DocLibs) auf reportlab + pikepdf, kein LibreOffice
  (Entscheidung 2026-11-06). Überschriften wie im DOCX: `#` = „Überschrift 1".
- Maße und Stile kommen aus dem PTA-Designmodell (E01-S01), das sie aus der Word-Vorlage liest —
  keine zweite Wertetabelle im PDF-Code.
- Seitenumbruchregeln von DocLibs bleiben: Überschriften bei ihrem Folgeinhalt, keine
  Hurenkinder und Schusterjungen, zu hohe Grafiken werden verkleinert.

## Akzeptanz

Ein Markdown ergibt als DOCX (nach PDF exportiert) und als PDF aus diesem Generator Seiten, die
nebeneinandergelegt dasselbe Design zeigen; veraPDF bestätigt PDF/A-2b.

## Offene Fragen

1. PDF-Weg: (a) Layout-Engine nach Python portieren (reportlab + pikepdf, keine
   Systemabhängigkeit) — Vorschlag; oder (b) DOCX aus E03 erzeugen und mit LibreOffice nach PDF/A
   wandeln (exakt wie Word, aber LibreOffice auf jedem Rechner nötig)?

> (2026-11-06) (a) Layout-Engine portieren.

2. Schrift im PDF: Segoe UI darf nicht mitgeliefert werden. Vorschlag: **Selawik** (OFL,
   metrikkompatibler Segoe-UI-Ersatz von Microsoft) bündeln und Segoe UI nehmen, wenn sie auf dem
   System liegt. Erlaubt die Schriftlizenz der PTA das Einbetten von Segoe UI in PDFs?

> (2026-11-06) Selawik bündeln, Segoe UI aus dem System nehmen, wenn vorhanden.

3. Gibt es das PTA-Logo als SVG oder hochaufgelöstes PNG? (Die Word-Vorlagen haben es nur als
   kleines EMF.)

> (2026-11-06) Logo aus dem EMF der Vorlage wandeln (E01-S04).

## Notizen

