# E03 DOCX-Generator auf den PTA-Word-Vorlagen

> Status: Entwurf

## Ziel

Markdown → `.docx`, erzeugt **auf den PTA-Word-Vorlagen** aus `source-templates/`, sodass das
Ergebnis aussieht und sich in Word bearbeiten lässt wie ein von Hand angelegtes PTA-Dokument.

## Motivation

DocLibs kennt kein DOCX als Ziel. Die PTA arbeitet aber überwiegend mit den fünf Word-Vorlagen
(siehe [Designanalyse](../10-analysen/2026-11-06%20pta-designstandards.md)). Ein DOCX, das die
Formatvorlagen der Vorlage verwendet statt eigener Formatierung, bleibt verbindlich im PTA-Design,
auch wenn es danach weiterbearbeitet wird.

## Scope

| Story | Inhalt | Status |
| ----- | ------ | ------ |
| [E03-S01](../60-prüfung/E03-S01-docx-auf-pta-vorlage.md) | Dokument aus der Vorlage: Beispielinhalt entfernen, Varianten, Deckblatt, Kopf-/Fußzeile, Metadaten, Inhaltsverzeichnis | in Prüfung |
| [E03-S02](../60-prüfung/E03-S02-docx-inhalte.md) | Inhalte: Überschriften, Absätze, Listen, Tabellen mit Beschriftung, Bilder, Code, Links, Fußnoten, Zitate | in Prüfung |
| [E03-S03](../55-in-arbeit/docs-2/E03-S03-folien-syntax-in-word.md) | Folien-Syntax in Word: Container, Alerts, `==mark==`, Status-Labels, Bildreihen | in Bearbeitung (docs-2) |
| [E03-S04](E03-S04-diagramme-und-charts-im-docx.md) | Diagramme und Charts im DOCX (als Bild bzw. natives Word-Diagramm) | Entwurf |
| [E03-S05](E03-S05-authoring-guide-docx.md) | Authoring Guide DOCX | Entwurf |

## Bereichsweite Entscheidungen

- **Formatvorlagen statt Direktformatierung.** Jeder Markdown-Block wird einer Formatvorlage der
  PTA-Vorlage zugeordnet (Tabelle in E03-S02). Direktformatierung nur für Zeichenformat (fett,
  kursiv, Code, Links).
- Die Vorlage wird als Ganzes übernommen (Stile, Nummerierung, Theme, Kopf-/Fußzeilen, Logo);
  nur der Beispieltext im Körper wird ersetzt.
- **`#` ist „Überschrift 1"** (Entscheidung 2026-11-06), nicht der Dokumenttitel wie in den
  Folien; Titel, Untertitel, Autor, Ort und Datum kommen aus dem Front Matter. Das PDF (E05) folgt
  dem.
- python-docx für das Grobe, lxml für Felder (TOC, STYLEREF, SEQ, PAGE), Nummerierung und
  Abschnittseigenschaften.

## Akzeptanz

Ein Markdown-Bericht ergibt in jeder der vier Vorlagenvarianten ein DOCX, das Word ohne
Reparaturmeldung öffnet, dessen Stile ausschließlich PTA-Formatvorlagen sind und das beim
Rücklesen mit dem DOCX-Konverter (E07) wieder den Markdown-Inhalt ergibt.

## Offene Fragen

1. Welche Vorlage ist der Standard, wenn das Front Matter nichts sagt — Hochformat **mit**
   Deckblatt?

> (2026-11-06) Ja: `hoch` (Hochformat mit Deckblatt).

2. Wofür wird die BPS-PTA-DATIS-Vorlage verwendet (Gruppen-Dokumente)? Soll sie als eigene
   Variante wählbar sein?

> (2026-11-06) Nein, keine wählbare Variante.

## Notizen

