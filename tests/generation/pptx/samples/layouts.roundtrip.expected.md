## Projekt Hafen

PTA

Fahrpläne neu gebaut: Dokumente statt Tabellen

## Warum den Planer neu bauen?

Warum

26 Tabellen

Die Konfiguration ist zu kompliziert

für 12 Arten von Regeln; die Formel versteckt sich in der Struktur.

3,2 GB

Große Fahrpläne sind zu langsam

Speicher je Fahrplan bei 5.000 Halten, vor allem Objekt-Overhead.

Unterwegs behoben

Sperren

der Join zählt wieder ohne Sperre

Duplikate

der Export-Wächter filtert jede Zeile

Herkunft

Ergebnisse halten ihre Eingaben nicht fest

## Unsere Daten sind Dokumente

Beobachtung

Einmal angelegt, ändern sich die Daten kaum: Sie werden gelesen, ergänzt und neu berechnet.

| Was | Heute | Hafen |
| --- | --- | --- |
| Buchung | Buchungstabellen, Zeile für Zeile | Ein Dokument je Revision |
| Berechnung | Ergebnistabellen | Ein Dokument je Version, einmal geschrieben |
| Regeln | 26 Tabellen | Ein Dokument mit Formeln |

Der Fairness halber: Buchungen werden nach der Erfassung noch bearbeitet – daher Revisionen statt strenger Unveränderlichkeit.

## Was es bringt

Nutzen

Wirklich große Fahrpläne

Dokumente werden seitenweise geschrieben und gestreamt

Mehr Flexibilität für weniger Aufwand

neue Preislogik ist eine Formel, keine Tabelle mit Migration

Reproduzierbare Ergebnisse

jede Berechnung hält ihre Eingaben fest

Einfachere Infrastruktur

nur Speicher, keine Datenbank, kein Message Broker

## Speicher ohne Datenbank

Architektur

Blob-Speicher ist die einzige externe Abhängigkeit.

Dokumente im Blob-Speicher

write-once

Ergebnisse, Regelversionen

revisions

Buchungen, Referenzdaten

latest-wins

nur der Regelkopf

Tabellen für Status und Listen

Bookings

Schedules

WorkQueue

RuleVersions

Hosts

Audit

Jedes Ergebnis hat ein Manifest

Buchungsrevision, Regelversion, Parameterrevision und eine Revision je Referenzquelle.

## Statusmodell

Architektur

| Status | Weiter durch |
| --- | --- |
| Angelegt | ● System |
| WartetAufFreigabe | ● Mensch |
| Berechnet | ● System |
| Fehlgeschlagen | ● Mensch |

Zeilen in der Hervorhebungsfarbe brauchen einen Menschen.

## Verarbeitung ohne Broker

Architektur

Ein Broker garantiert die Zustellung mindestens einmal – nicht die Verarbeitung höchstens einmal.

Der Wettlauf im alten System geschah mit einem Broker.

Die Warteschlange ist eine Tabelle

übernommen per Compare-and-Swap, mit Leases

Ein Broker heißt doppelte Maschinerie

Compare-and-Swap brauchen wir ohnehin

## Vorher und nachher

Heute

26 Tabellen für 12 Arten von Regeln

Sperren im Join

Mit Hafen

Ein Dokument je Revision

Keine Datenbank, kein Message Broker

## Der Schattenlauf

Plan

Vier Wochen lang rechnen altes System und Hafen dieselben Buchungen.

vergleiche --alt planer --neu hafen

| Woche | Gleiche Ergebnisse |
| --- | --- |
| 1 | 91 % |
| 2 | 97 % |
| 3 | 99 % |

Ziel: 100 %

Erst wenn der Schattenlauf vier Wochen lang gleiche Ergebnisse liefert, wird umgestellt.

## Stand und nächste Schritte

| Teil | Status |
| --- | --- |
| Host, Speicher, Kennungen | ● Erledigt |
| Erfassung und Prüfung | ● Erledigt |
| Warteschlange und Detailseiten | ● In Prüfung |
| Engine und Ergebnisse | ● Als Nächstes |

Stand heute: im Plan, die Engine unter Beobachtung.

Dann ein Schattenlauf: Hafen berechnet dieselben Buchungen, und die Ergebnisse werden verglichen.
