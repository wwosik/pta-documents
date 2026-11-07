# E07 Konvertierung nach Markdown

> Status: Entwurf

## Ziel

`.pdf`, `.docx` und `.pptx` → Markdown mit Bildern, Formaterkennung und die Markdown-Hilfen —
portiert aus `wwosik.DocLibs.DocumentConversions`, ohne den Windows-Teil und ohne JIRA-Wiki.

## Motivation

Die Konverter sind die Rückrichtung der Generatoren und deren Testwerkzeug (Rundreise-Tests).
Außerdem nützen sie allein: vorhandene PTA-Dokumente als Markdown lesbar machen, etwa für KI-Agenten.

## Scope

| Story | Inhalt | Status |
| ----- | ------ | ------ |
| [E07-S01](../55-in-arbeit/docs-2/E07-S01-formaterkennung-und-registry.md) | Formaterkennung, Registry, `ConversionOptions`, Ressourcensammlung | in Bearbeitung (docs-2) |
| [E07-S02](../60-prüfung/E07-S02-docx-nach-markdown.md) | DOCX → Markdown (deutsche und englische Stilnamen, Nummerierung, Tabellen, Bilder) — vorgezogen für die Rundreise-Tests in M01 | in Prüfung |
| [E07-S03](../60-prüfung/E07-S03-pptx-nach-markdown.md) | PPTX → Markdown | in Prüfung |
| [E07-S04](E07-S04-pdf-nach-markdown.md) | PDF → Markdown (pdfplumber; Absatz-, Silbentrennungs- und Listenheuristik) | Entwurf |
| E07-S05 | ~~Markdown ↔ JIRA-Wiki~~ | entfällt (2026-11-06) |
| [E07-S06](E07-S06-markdown-hilfen.md) | Markdown-Hilfen (`escape`, `code`, `table`, `normalize` …) | gestrichen (2026-11-07), Prüfpunkte in E07-S02 |

## Bereichsweite Entscheidungen

- `.doc`, `.rtf`, `.xls`, `.xlsx` über Office-Automatisierung entfallen (Entscheidung
  2026-11-06). OLE-Dateien werden erkannt und mit klarer Fehlermeldung abgelehnt.
- Die Erwartungsdateien (`*.expected.md`) von DocLibs dienen als Startpunkt der Tests; Abweichungen
  durch die Python-Bibliotheken werden im Plan dokumentiert, nicht still übernommen.

## Akzeptanz

Die Beispieldateien von DocLibs ergeben dasselbe Markdown wie dort oder eine begründete,
dokumentierte Abweichung.

## Offene Fragen

1. Wird Markdown ↔ JIRA-Wiki bei der PTA gebraucht?

> (2026-11-06) Nein, entfällt.

## Notizen

