# Mermaid-Diagramme

Word: Mermaid-Diagramme als scharfe Abbildungen

PTA Documents, Hamburg, 08.11.2026

# Mermaid-Diagramme in Word

## Ablauf

Ein mermaid-Block steht in Word als Bild (SVG, mit PNG für ältere Word-Versionen) in seiner natürlichen Größe, höchstens über die Satzspiegelbreite; ein Absatz Abbildung: … direkt danach wird die Beschriftung:

````markdown
```mermaid
flowchart LR
  A[Markdown] --> B{Front Matter?}
  B -->|ja| C[Vorlage wählen]
  B -->|nein| D[Standardvorlage]
  C --> E([Word-Dokument])
  D --> E
```

Abbildung: Vom Markdown zum Word-Dokument
````

![mermaid](images/image2.png)

Abbildung 1: Vom Markdown zum Word-Dokument

## Sequenz

Ohne Abbildung: … gibt es keine Beschriftung:

````markdown
```mermaid
sequenceDiagram
  participant App
  actor Nutzer
  Nutzer->>App: Schickt das Markdown
  App-->>Nutzer: Liefert den Bericht
```
````

![mermaid](images/image3.png)

## Anteile

````markdown
```mermaid
pie title Umsatz nach Region
  "Nord" : 1200
  "Süd" : 950
  "Ost" : 610
```

Abbildung: Umsatz nach Region
````

![mermaid](images/image4.png)

Abbildung 2: Umsatz nach Region
