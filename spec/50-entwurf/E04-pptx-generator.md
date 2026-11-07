# E04 PPTX-Generator auf der PTA-PowerPoint-Vorlage

> Status: Entwurf

## Ziel

Markdown → `.pptx` auf der PTA-Basisvorlage (bzw. Schulungsvorlage, englische Titelfolie), mit
den PTA-Layouts statt des eingebauten Masters von DocLibs.

## Motivation

DocLibs baut Folien auf einem selbst erzeugten Master (`TemplateBuilder`) oder auf einer fremden
Vorlage, deren Layouts es nach `type` sucht. Die PTA-Layouts haben **keinen** `type`, zeichnen ihre
Erkennungszeichen teils über unsichtbare Platzhalter und belegen die Textebenen anders (Ebene 1
Subheadline, Ebene 2 Einleitungstext, Aufzählung erst ab Ebene 3) — siehe
[Designanalyse](../10-analysen/2026-11-06%20pta-designstandards.md#powerpoint). Der Generator wird
deshalb auf diese eine Vorlage zugeschnitten.

## Scope

| Story | Inhalt | Status |
| ----- | ------ | ------ |
| [E04-S01](../60-prüfung/E04-S01-pptx-auf-pta-vorlage.md) | Deck auf der PTA-Vorlage: Layoutwahl, Titel-, Kapitel-, Inhalts-, Abschlussfolien, Fußzeile | in Prüfung |
| [E04-S02](../60-prüfung/E04-S02-pptx-inhalte-und-fitting.md) | Inhalte: Textebenen, Listen, Tabellen im PTA-Stil, Bilder in Bildplatzhaltern, Code; Fitting | in Prüfung |
| [E04-S03](E04-S03-flow-layouts-im-pta-stil.md) | Flow-Layouts aus DocLibs im PTA-Stil: `cards`, `rows`, `panel`, `statement`, `columns`, Alerts, Fazit-Box, Kommentarbox, `==mark==` (Gelb), Status-Labels (Signalfarben) | Entwurf |
| [E04-S04](E04-S04-weitere-layouts.md) | Weitere Layouts aus Markdown: Agenda (nur ausdrücklich, keine automatische), Zwischenfazit, Zitat, Kontakt, Diagramm-Layouts | Entwurf |
| [E04-S05](E04-S05-schulungsvorlage-und-sticker.md) | Schulungsvorlage (`vorlage: schulung`) und englische Titelfolie (`sprache: en`); Sticker „VERTRAULICH" per Front Matter `kennzeichnung` (gemeinsam mit E12-S03) | Entwurf |
| [E04-S06](E04-S06-authoring-guide-pptx.md) | Authoring Guide PPTX | Entwurf |

## Bereichsweite Entscheidungen

- Layouts werden **über ihren Namen** in der PTA-Vorlage gewählt; die Zuordnung steht im
  Designmodell (E01-S01), einschließlich des Tippfehlers `Abbschlussfolie`.
- Die PTA-Regel „nur die in der Vorlage vorgegebenen Layouts" gilt auch für den Generator: freie
  Formen nur auf `Nur Titel` und innerhalb der Inhaltsfläche, ausgerichtet am Raster.
- Schrifteinbettung (EOT) aus DocLibs entfällt: Segoe UI ist auf den PTA-Rechnern installiert
  und darf nicht weitergegeben werden.
- Standard-Titelfolie ist `Titelfolie mit Bild 02`; jedes weitere `#` wird eine `Trennfolie` mit
  zweistelliger Kapitelnummer; eine Agenda entsteht nie automatisch (Entscheidungen 2026-11-06).
- Folientabellen werden mit Direktformatierung nach der Mustertabelle gezeichnet (Kopf
  `004676`), nicht über einen Tabellenstil.

## Akzeptanz

Das Beispiel-Deck (`deck.md` aus DocLibs, um PTA-Fälle ergänzt) ergibt eine Präsentation, die
PowerPoint ohne Reparatur öffnet, nur PTA-Layouts verwendet und beim Rücklesen mit dem
PPTX-Konverter (E07) den Markdown-Inhalt ergibt.

## Offene Fragen

1. Welche Titelfolie ist Standard: `Titelfolie ohne Bild` (Verlauf, kein Foto) oder
   `Titelfolie mit Bild 01`? Per Front Matter wählbar (`cover: bild-01 | bild-02 | ohne-bild |
   branche`)?

> (2026-11-06) `Titelfolie mit Bild 02` ist Standard.

2. Soll `# Kapitel` (oberste Überschrift nach dem Titel) automatisch eine `Trennfolie` mit
   Kapitelnummer „01", „02" … erzeugen?

> (2026-11-06) Ja, `Trennfolie` mit „01", „02" ….

3. Soll aus den Kapiteln automatisch eine Agenda-Folie entstehen (`Agenda (kurz)` bis 4,
   `Agenda (lang)` bis 8 Kapitel)?

> (2026-11-06) Nein, keine automatische Agenda.

## Notizen

