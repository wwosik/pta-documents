---
titel: Diagramme
---

# Diagramme

Jede Mermaid-Art, die der Renderer zeichnet, in den PTA-Farben (Port von DocLibs `diagrams.md`).

## Ablauf

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

## Sequenz

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

## Klassen

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

## Zustände

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

## Datenmodell

```mermaid
erDiagram
  KUNDE ||--o{ AUFTRAG : erteilt
  AUFTRAG ||--|{ POSITION : enthält
  KUNDE {
    string name PK
    string email
  }
```

## Anteile

```mermaid
pie title Umsatz nach Region
  "Nord" : 1200
  "Süd" : 950
  "Ost" : 610
  "West" : 430
```

## Plan

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

## Mindmap

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

## Noch nicht gezeichnet

Eine Journey bleibt Code:

```mermaid
journey
  title Einen Bericht schreiben
  section Entwurf
    Schreiben: 4: Autor
```
