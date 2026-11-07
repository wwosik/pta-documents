---
titel: Projekt Hafen
autor: PTA
status.success: Erledigt
status.info: In Prüfung
status.warning: Als Nächstes
---

# Projekt Hafen

Fahrpläne neu gebaut: Dokumente statt Tabellen

## Warum den Planer neu bauen? {kicker="Warum"}

::: cards
### Die Konfiguration ist zu kompliziert
**26 Tabellen**

für 12 Arten von Regeln; die Formel versteckt sich in der Struktur.

### Große Fahrpläne sind zu langsam
**3,2 GB**

Speicher je Fahrplan bei 5.000 Halten, vor allem Objekt-Overhead.
:::

:::: panel
**Unterwegs behoben**

::: cards
- **Sperren** – der Join zählt wieder ohne Sperre
- **Duplikate** – der Export-Wächter filtert jede Zeile
- **Herkunft** – Ergebnisse halten ihre Eingaben nicht fest
:::
::::

## Unsere Daten sind Dokumente {kicker="Beobachtung"}

Einmal angelegt, ändern sich die Daten kaum: Sie werden gelesen, ergänzt und neu berechnet.

| Was | Heute | Hafen |
| --- | ----- | ----- |
| Buchung | Buchungstabellen, Zeile für Zeile | Ein Dokument je Revision |
| Berechnung | Ergebnistabellen | Ein Dokument je Version, einmal geschrieben |
| Regeln | 26 Tabellen | Ein Dokument mit Formeln |

> [!NOTE]
> **Der Fairness halber:** Buchungen werden nach der Erfassung noch bearbeitet – daher Revisionen statt strenger Unveränderlichkeit.

## Was es bringt {kicker="Nutzen"}

::: rows
- **Wirklich große Fahrpläne** – Dokumente werden seitenweise geschrieben und gestreamt
- **Mehr Flexibilität für weniger Aufwand** – neue Preislogik ist eine Formel, keine Tabelle mit Migration
- **Reproduzierbare Ergebnisse** – jede Berechnung hält ihre Eingaben fest
- **Einfachere Infrastruktur** – nur Speicher, keine Datenbank, kein Message Broker
:::

## Speicher ohne Datenbank {kicker="Architektur"}

Blob-Speicher ist die einzige externe Abhängigkeit.

::: cards
### Dokumente im Blob-Speicher
- `write-once` Ergebnisse, Regelversionen
- `revisions` Buchungen, Referenzdaten
- `latest-wins` nur der Regelkopf

### Tabellen für Status und Listen
`Bookings` `Schedules` `WorkQueue` `RuleVersions` `Hosts` `Audit`
:::

::: panel dark
### Jedes Ergebnis hat ein Manifest
Buchungsrevision, Regelversion, Parameterrevision und eine Revision je Referenzquelle.
:::

## Statusmodell {kicker="Architektur"}

| Status | Weiter durch |
| ------ | ------------ |
| Angelegt | `System` |
| ==WartetAufFreigabe== | `Mensch` |
| Berechnet | `System` |
| ==Fehlgeschlagen== | `Mensch` |

Zeilen in der ==Hervorhebungsfarbe== brauchen einen Menschen.

## Verarbeitung ohne Broker {.dark kicker="Architektur"}

::: statement
Ein Broker garantiert die Zustellung mindestens einmal – nicht die Verarbeitung höchstens einmal.

Der Wettlauf im alten System geschah mit einem Broker.
:::

::: cards
- **Die Warteschlange ist eine Tabelle** – übernommen per Compare-and-Swap, mit Leases
- **Ein Broker heißt doppelte Maschinerie** – Compare-and-Swap brauchen wir ohnehin
:::

## Stand und nächste Schritte

| Teil | Status |
| ---- | ------ |
| Host, Speicher, Kennungen | `Erledigt` |
| Erfassung und Prüfung | `Erledigt` |
| Warteschlange und Detailseiten | `In Prüfung` |
| Engine und Ergebnisse | `Als Nächstes` |

Stand heute: [im Plan]{.success}, die Engine [unter Beobachtung]{.warning}.

> [!IMPORTANT]
> **Dann ein Schattenlauf:** Hafen berechnet dieselben Buchungen, und die Ergebnisse werden verglichen.
