## Mermaid-Diagramme

PTA Documents, 08.11.2026

PowerPoint: jede Mermaid-Art als bearbeitbare Formen

## Ablauf (flowchart)

::: notes

````
## Ablauf (flowchart)

```mermaid
flowchart TD
  A[Markdown-Dokument] --> B{Front Matter?}
  B -->|ja| C[Vorlage wählen]
  B -.->|nein| D[(Standardvorlage)]
  C ==> E([Seiten setzen])
  D --> E
  subgraph Ausgabe
    E --> F>PDF/A-2b]
    E --> G{{PowerPoint}}
  end
  G --- H((Fertig))
```
````

:::

## Sequenz (sequenceDiagram)

::: notes

````
## Sequenz (sequenceDiagram)

```mermaid
sequenceDiagram
  participant App
  actor Nutzer
  App->>Nutzer: Fragt nach dem Bericht
  Nutzer-->>App: Schickt das Markdown
  Note over App,Nutzer: Die Vorlage steht im Front Matter
  loop Jedes Kapitel
    App-)Nutzer: Fortschritt
  end
  App-xNutzer: Fertig
```
````

:::

## Klassen (classDiagram)

::: notes

````
## Klassen (classDiagram)

```mermaid
classDiagram
  class Vorlage {
    +String Name
    +Farben Farben
    +Laden() Design
  }
  class Farben
  Vorlage *-- Farben
  Vorlage o-- Schriften : schriften
  Vorlage ..> Folienmaster
  CodeBlockRenderer <|.. MermaidRenderer
```
````

:::

## Zustände (stateDiagram-v2)

::: notes

````
## Zustände (stateDiagram-v2)

```mermaid
stateDiagram-v2
  [*] --> Entwurf
  Entwurf --> Prüfung : einreichen
  Prüfung --> Entwurf : ändern
  Prüfung --> Freigegeben : freigeben
  state Freigegeben {
    [*] --> Aktiv
    Aktiv --> Archiviert
  }
  Freigegeben --> [*]
```
````

:::

## Datenmodell (erDiagram)

::: notes

````
## Datenmodell (erDiagram)

```mermaid
erDiagram
  KUNDE ||--o{ AUFTRAG : erteilt
  AUFTRAG ||--|{ POSITION : enthält
  KUNDE {
    string name PK
    string email
  }
```
````

:::

## Anteile (pie)

::: notes

````
## Anteile (pie)

```mermaid
pie title Umsatz nach Region
  "Nord" : 1200
  "Süd" : 950
  "Ost" : 610
  "West" : 430
```
````

:::

## Plan (gantt)

::: notes

````
## Plan (gantt)

```mermaid
gantt
  title Releaseplan
  dateFormat YYYY-MM-DD
  section Bauen
  Entwurf :a1, 2026-01-05, 10d
  Umsetzung :after a1, 20d
  section Ausliefern
  Prüfung :2026-02-05, 7d
  Release :milestone, 2026-02-16, 0d
```
````

:::

## Mindmap (mindmap)

::: notes

````
## Mindmap (mindmap)

```mermaid
mindmap
  root((PTA-Docs))
    Konverter
      PDF
      DOCX
      PPTX
    Generatoren
      Word
      Folien
      [Vorlagen]
```
````

:::
