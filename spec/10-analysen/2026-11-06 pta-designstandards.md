# PTA-Designstandards aus den Vorlagen

> Stand: 2026-11-06. Quelle: die neun Dateien in `source-templates/`, ausgelesen aus dem XML der
> Office-Pakete. Werte sind exakt aus den Dateien; Umrechnung: 1 cm = 567 twips = 360 000 EMU,
> Word-Schriftgrößen in halben Punkt.

Diese Analyse hält fest, welche Designstandards die PTA-Vorlagen vorgeben. Sie ersetzt in der
Python-Portierung den neutralen Brand und alle Standardvorlagen von DocLibs: Was hier steht, ist
das einzige Design, das die Generatoren kennen.

## Die Vorlagen

| Datei | Art | Inhalt |
| ----- | --- | ------ |
| `PTA-Dokument_Hochformat_mit-Deckblatt.dotx` | Word | A4 hoch, Deckblatt, Inhaltsverzeichnis, Musterkapitel |
| `PTA-Dokument_Hochformat_ohne-Deckblatt.dotx` | Word | A4 hoch, ohne Deckblatt |
| `PTA-Dokument_Querformat_mit-Deckblatt.dotx` | Word | A4 quer, Deckblatt |
| `PTA-Dokument_Querformat_ohne-Deckblatt.dotx` | Word | A4 quer, ohne Deckblatt |
| `BPS-PTA-DATIS-Dokument.dotx` | Word | A4 hoch, ohne Deckblatt, Gruppenlogo „BPS \| PTA \| DATIS", Fußzeile „PTA Gruppe" |
| `PTA-Powerpoint-Basisvorlage.potx` | PowerPoint | Master mit 35 Layouts, 39 Musterfolien |
| `PTA-Powerpoint-Schulungsvorlage.potx` | PowerPoint | Schulungsvariante, 40 Musterfolien |
| `PTA-Powerpoint-Titelfolie EN.pptx` | PowerPoint | englische Titelfolie |
| `PTA-Powerpoint-Vorlagensammlung.pptx` | PowerPoint | Sammlung von 93 Musterfolien |

Alle Dateien kommen aus SharePoint (Dokument-IDs in `customXml/` und den benutzerdefinierten
Eigenschaften, Inhaltstyp `0x0101003A941D…`) und enthalten Altlasten (`[trash]/`-Teile). Beides
gehört nicht in erzeugte Dokumente.

## Farben

Die Word-Vorlagen teilen ein Theme (`PTA`, Farbschema „PTA Word", in allen fünf Dateien
bytegleich):

| Rolle | Wert | Verwendung in den Vorlagen |
| ----- | ---- | -------------------------- |
| Akzent 1 — **PTA-Blau** | `006FB9` | Titel, Untertitel, Überschrift 1, Aufzählungszeichen, Tabellenkopf, Beschriftungen, Firmenzeile und Seitenzahl in der Fußzeile, Logo |
| Akzent 2 — Dunkelblau | `004676` | Hyperlinks |
| Akzent 3 — Hellblau | `9FD8FF` | Verlaufslinie in Kopf- und Fußzeile |
| Akzent 4 — Dunkelgrau | `787878` | besuchte Hyperlinks |
| Akzent 5 — Mittelgrau | `AFAFAF` | Tabellenlinien |
| Akzent 6 — Hellgrau | `E6E6E6` | (auch Dunkel 2) Flächen |
| Hell 2 — Gelb | `FDDC35` | nur Formatvorlage „Überschrift 4" (ungenutzt) |
| Dunkel 1 / Hell 1 | `000000` / `FFFFFF` | Text / Hintergrund |

## Schriften

- **Segoe UI** ist Haupt- und Nebenschrift des Themes (Überschriften und Text). Sie ist
  proprietär (Microsoft) und auf Windows vorhanden; eingebettet ist sie in keiner Vorlage.
- Aufzählungszeichen stehen in Wingdings (■, `U+F06E`) und Calibri (―); „Calibri Light" und
  „Berlin Type" sind nur in ungenutzten Formatvorlagen bzw. Listen genannt.

## Word

### Seite

| Variante | Format | Ränder oben / unten / links / rechts | Kopfzeile / Fußzeile ab Rand | Satzspiegelbreite |
| -------- | ------ | ------------------------------------ | ---------------------------- | ----------------- |
| Hochformat (auch BPS-PTA-DATIS) | A4 210 × 297 mm | 3,50 / 2,00 / 2,20 / 2,20 cm | 0,95 / 0,60 cm | 16,6 cm |
| Querformat | A4 297 × 210 mm | 4,20 / 2,50 / 2,20 / 2,20 cm | 1,00 / 0,75 cm | 25,3 cm |

Standard-Tabstopp 1,25 cm; Sprache `de-DE`.

### Formatvorlagen

Text ist schwarz in Segoe UI, wenn nicht anders angegeben. Abstände in pt, Zeilenabstand
„mindestens".

| Formatvorlage | Größe | Stil | Farbe | Abstand vor / nach | Zeilenabstand | Weiteres |
| ------------- | ----: | ---- | ----- | -----------------: | ------------: | -------- |
| `Standard` | 10 | | Schwarz | 6 / 6 | 14 | Grundlage aller anderen |
| `Titel` | 34 | fett | PTA-Blau | 0 / 14 | 38 | Deckblatt |
| `Untertitel` | 22 | | PTA-Blau | 14 / 0 | 26 | Deckblatt |
| `Autor` | 14 | | Schwarz | 14 / 0 | 18 | Deckblatt: „Name Nachname, Ort, Datum" |
| `Überschrift 1` | 14 | fett | PTA-Blau | 14 / 9 | 18 | nummeriert `1`, Einzug 1,25 cm hängend, mit nächstem Absatz zusammen |
| `Überschrift 2` | 12 | fett | Schwarz | 14 / 9 | 16 | `1.1`, 1,25 cm hängend |
| `Überschrift 3` | 12 | | Schwarz | 14 / 9 | 16 | `1.1.1`, 1,70 cm hängend |
| `Zwischenüberschrift` | 10 | Versalien | Schwarz | 14 (BPS-PTA-DATIS und Hoch ohne Deckblatt: 0) / 6 | 14 | unnummeriert; auch „Inhalt" über dem Verzeichnis |
| `Standard fett` | 10 | fett | Schwarz | 14 / 6 | 14 | Absatz-Hervorhebung, „Überschrift Tabelle" |
| `Aufzählungszeichen` | 10 | | Schwarz | 6 / 6 | 14 | Ebene 1 ■ (Wingdings, PTA-Blau), Einzug 0,6 cm; Ebene 2 und 3 ― (Calibri, schwarz), 1,2 / 1,8 cm |
| `Listenabsatz` | 10 | | Schwarz | 6 / 6 | 14 | Ebene 1 `1.` (0,6 cm), Ebene 2 ■ blau (1,2 cm), Ebene 3 ― (1,8 cm) |
| `Beschriftung` | 8 | | PTA-Blau | 6 / 14 | 12 | „Tabelle 1: Beschriftung Tabelle", Feld `SEQ Tabelle` |
| `Verzeichnis 1` / `2` | 10 | | Schwarz | – / 5 | 14 | Einzug 0,75 / 1,75 cm hängend; Ebene 2 mit Punkt-Füllzeichen rechts |
| `Fußnotentext` | 8 | | Schwarz | | 9,6 | |
| `Kopfzeile` | 10 | | | 0 / 3 | 14 | |
| `Fußzeile` | 6,5 | | | 0 / 0 | 9,5 | |
| `Hyperlink` (Zeichen) | | unterstrichen | `004676` | | | |

Inhaltsverzeichnis: Feld `TOC \o "1-2" \h \z \u` — Ebenen 1 und 2, mit Hyperlinks.

Die Formatvorlagen sind in allen fünf Vorlagen gleich bis auf: den Abstand vor
`Zwischenüberschrift` (siehe Tabelle) und den Tabstopp mit Füllzeichen in `Verzeichnis 1`
(nur in Hoch ohne Deckblatt und BPS-PTA-DATIS).

### Tabellen

Tabellenformatvorlage **`PTA`**:

- Kopfzeile: Hintergrund PTA-Blau `006FB9`, weiße Schrift.
- Linien: nur waagerecht — unter jeder Zeile und unten, 0,5 pt in `AFAFAF`; keine senkrechten
  Linien, keine Rahmen links und rechts.
- Zellenränder links und rechts 0 (Text bündig mit dem Satzspiegel).
- Absätze in Zellen: 0 Abstand nach, einfacher Zeilenabstand.
- Über der Tabelle ein Titel in `Standard fett` („Überschrift Tabelle"), darunter die
  Beschriftung „Tabelle n: …" in `Beschriftung`.
- Mustertabellen: 4 Spalten (Hochformat) bzw. 6 Spalten (Querformat); erste Spalte
  „Tabellentitel".

### Kopf- und Fußzeile

- **Logo** oben rechts am Satzspiegelrand — Hochformat 2,22 × 1,28 cm, 1,09 cm von der
  Blattoberkante; Querformat 3,01 × 1,73 cm, 1,05 cm von oben (PTA:
  Vektorlogo als EMF; BPS-PTA-DATIS: PNG 2580 × 623 px, 4,57 × 1,10 cm, Schriftzüge
  „BPS | PTA | DATIS" in PTA-Blau mit grauen Trennern).
- **Verlaufslinie** unter der Kopfzeile und über der Fußzeile, so lang wie der Satzspiegel ab
  2,20 cm vom linken Blattrand (Hochformat 16,6 cm, 2,80 cm von oben; Querformat 25,3 cm, 3,40 cm
  von oben): Verlauf PTA-Blau → Hellblau (53 %) → Hellblau transparent.
- **Kopfzeile** (Folgeseiten): Titel fett in PTA-Blau, darunter Untertitel; in einer
  einzelligen Tabelle von 11,5 cm (quer 17,5 cm) Breite. In den Vorlagen mit Deckblatt per Feld `STYLEREF Titel`
  / `STYLEREF Untertitel` aus dem Deckblatt übernommen, in den anderen als fester Text.
- **Fußzeile**: Tabelle über den Satzspiegel (Hochformat drei gleiche Spalten; Querformat drei
  gleiche Spalten und eine leere schmale vierte) —
  links „PTA IT-Beratung" (BPS-PTA-DATIS: „PTA Gruppe") fett in PTA-Blau,
  Mitte „Stand: xx.xx.xxxx",
  rechts „Seite `PAGE` | `NUMPAGES`" mit fetter Seitenzahl in PTA-Blau; 6,5 pt.
- Erste Seite: Varianten mit Deckblatt haben eine eigene erste Kopfzeile (nur Logo und Linie,
  ohne Titeltext) und keine Fußzeile auf dem Deckblatt.

### Deckblatt

`Titel` („Titel des Dokuments"), `Untertitel` (im Querformat: „Gerne auch zweizeilig möglich"),
`Autor` („Name Nachname, Ort, Datum"), dann Seitenumbruch und das Inhaltsverzeichnis auf Seite 2.

### Dokumenteigenschaften

Titel und Betreff (Untertitel) in den Kerneigenschaften, Firma „PTA GmbH". Die Vorlagen nennen
noch ihre letzten Bearbeiter — das ist zu ersetzen, nicht zu übernehmen.

## PowerPoint

### Folie und Theme

- **Format 16:9**, 33,87 × 19,05 cm (12 192 000 × 6 858 000 EMU), in allen vier Dateien.
- Theme „PTA PowerPoint Vorlage", Farb- und Schriftschema „PTA 2020". Gleiche Akzente wie Word,
  aber **Text 404040** (Dunkelgrau, Word: Schwarz) und **Gelb `FDDC35` als Hervorhebungsfarbe**
  (Hintergrund 2).
- Zusätzliche Farben (`custClrLst`, Musterfolie „Weitere zu benutzende Farben"): **Grün `00B070`,
  Gelb-Orange `EAB500`, Rot `D91E18`** — Signalfarben (Ampel), nur für Status.
- Farbreihenfolge laut Farbmusterfolie, auch für Diagrammreihen: `006FB9`, `004676`, `9FD8FF`,
  `787878`, `AFAFAF`, `E6E6E6`.
- **Schriften:** Überschriften **Segoe UI**, Fließtext **Segoe UI Light**, Zitate **Georgia
  kursiv**. Regel auf Musterfolie 4 wörtlich: „Texthervorhebungen werden durch gefetteten Text in
  der Schriftart Segoe UI dargestellt." Keine Schrift eingebettet.

### Master

| Element | Wert |
| ------- | ---- |
| Titel | 32 pt fett, PTA-Blau, Segoe UI, Zeilenabstand 95 %, unten verankert; 1,33 / 2,36 cm, 31,20 × 1,30 cm, „maximal zweizeilig" |
| Inhaltsfläche | x 1,33–32,53 cm, y 4,62–17,72 cm (31,20 × 13,10 cm); zweispaltig 2 × 15,10 cm mit 1,00 cm Abstand; vierspaltig 4 × 7,00 cm |
| Textebene 1 „Subheadline" | 18 pt Segoe UI, PTA-Blau, ohne Aufzählungszeichen, 12 pt davor |
| Textebene 2 „Einleitungstext" | 18 pt Segoe UI Light, 404040, ohne Aufzählungszeichen, 6 pt davor |
| Textebene 3 „Erste Aufzählungsebene" | 18 pt Light, ■ (Wingdings `§`) in PTA-Blau, Einzug 0,60 cm hängend |
| Textebene 4 „Zweite Aufzählungsebene" | 16 pt Light, „−", Einzug 1,30 cm (0,70 hängend), 4 pt davor |
| Textebene 5 „Dritte Aufzählungsebene" | 14 pt Light, „−", Einzug 2,00 cm, 3 pt davor |
| Fußzeile | „PTA – Hier steht der übergeordnete Präsentationstitel", 9 pt, `787878`, ab 1,73 / 18,00 cm; **Foliennummer unten links** (0,56 cm), 9 pt; **kein Datum** |
| Erkennungszeichen | **Eckklammern** in PTA-Blau oben rechts und unten links, 1,33 × 1,33 cm aus 0,38 cm breiten Balken; auf den meisten Inhaltslayouts eine **Verlaufslinie** unter dem Titel (1,33 / 4,27 cm, 15,10 cm, 0,5 pt, PTA-Blau → Hellblau → transparent) |
| Logo | **nicht auf dem Master** — nur weiß auf den dunklen Titel- und Abschlusslayouts, 1,35 / 1,35 cm, 6,28 × 3,59 cm, mit Slogan „Kundenorientierte IT-Lösungen seit 1969" (Abschluss ohne Slogan) |

Wichtig für den Generator: die Textebenen 1 und 2 sind **keine** Aufzählungen. Eine
Markdown-Aufzählung beginnt auf Ebene 3; ein normaler Absatz ist Ebene 2, eine Zwischenüberschrift
Ebene 1.

### Layouts

35 Layouts mit deutschen Namen, alle ohne `type`-Attribut (benutzerdefiniert) — ein Generator muss
sie **über den Namen** finden. Dunkle Layouts (weiße Schrift) sind die mit Foto oder Verlauf.

| Gruppe | Layouts (Name wörtlich) | Verwendung |
| ------ | ----------------------- | ---------- |
| Titel | `Titelfolie mit Bild 01`, `Titelfolie mit Bild 02`, `Titelfolie Branchen`, `Titelfolie ohne Bild` | Titel 48 pt weiß, Untertitel 20 pt, Zeile „Name Nachname, Ort, Datum" 14 pt; keine Fußzeile |
| Agenda | `Agenda (kurz)` (≤ 4 Punkte, Nummern „0X" 32 pt), `Agenda (lang)` (≤ 8 Punkte, 14 pt) | dunkel, Foto mit Verlauf |
| Kapitel | `Trennfolie` | Kapitelnummer 88 pt fett, Kapitelname 32 pt Light, dunkel |
| Inhalt | `Nur Titel`, `Titel und Text`, `Titel und Text (zweispaltig)` | weiß; `Nur Titel` trägt 63 der 93 Musterfolien (alle Schaubilder als freie Formen) |
| Bild | `Titel, Bild und Text`, `Titel, Text und Bild 01`–`04`, `Titel, Text und zwei Bilder 01`–`03`, `Titel und Bild 01`, `Titel und Bild 02` | Bildplatzhalter füllen und beschneiden („Bilder … werden abgeschnitten, wenn das Seitenverhältnis ein anderes ist") |
| Zwischenfazit | `Zwischenfazit 01`, `Zwischenfazit 02` | dunkel, zentriert 32 pt |
| Diagramm | `Titel und Diagramm`, `Titel und zwei Diagramme`, `Titel, Diagramm und Text`, `Titel, Text und Diagramm` | Block: Diagrammtitel 18 pt PTA-Blau → Werteinheit 14 pt → Diagramm → Quellenangabe 9 pt |
| Zitat | `Zitat 01`, `Zitat 02` | Georgia kursiv 48 pt, weiß, dunkel |
| Kontakt | `Kontakt mit Text`, `Kontakt 01`–`05` | Foto, Name 16 pt PTA-Blau, Funktion, E-Mail, Telefon |
| Abschluss | `Abbschlussfolie` (sic, doppeltes „b") | „Finale Botschaft / Fazit", 24 pt fett weiß, Logo ohne Slogan |

Falle: Mehrere Layouts zeichnen Eckklammern, Linien oder das Logo über **unsichtbare
Platzhalter** (Text 1 pt, Aufforderung „x"). Die Musterfolien legen sie leer an; ein Generator muss
das ebenso tun, sonst fehlen die Grafiken.

### Tabellen

`tableStyles.xml` verweist nur auf die eingebaute „Mittlere Formatvorlage 2 – Akzent 1" und
definiert nichts Eigenes. Die Mustertabelle (Vorlagensammlung, Folie 38) überschreibt sie mit
Direktformatierung — **das ist der PTA-Standard für Folientabellen**:

| Zeile | Höhe | Text | Fläche / Linien |
| ----- | ---: | ---- | --------------- |
| Tabellentitel (verbunden) | 1,30 cm | 18 pt Segoe UI, PTA-Blau | keine Fläche |
| Kopfzeile | 1,30 cm | 16 pt Segoe UI, weiß | **Dunkelblau `004676`** |
| Datenzeilen | 1,10 cm | 14 pt Segoe UI Light, 404040 | waagerechte Linien 0,5 pt `E6E6E6`, keine senkrechten |
| letzte Datenzeile | 1,10 cm | wie oben | Linie unten 404040 |
| Summenzeile | 1,10 cm | 14 pt Segoe UI **fett** | Linien oben und unten 404040 |

Zahlen rechtsbündig, erste Spalte linksbündig ohne linken Innenabstand; Tabelle über die volle
Inhaltsbreite (31,20 cm). Achtung: **Word-Tabellen haben den Kopf in PTA-Blau `006FB9`, Folien in
Dunkelblau `004676`.**

### Weitere Muster

- **Diagramme:** Reihen in Akzent 1, 2, 3; Torten/Ringe Akzent 1–6; Wasserfall mit Rot `D91E18`
  für negative Werte; Achsenbeschriftung 14 pt Segoe UI Light; Achsenlinie 0,5 pt, keine
  Teilstriche.
- **Fazit-Box:** volle Breite am unteren Rand der Inhaltsfläche (1,33 / 15,78 cm, 31,20 × 1,94 cm),
  Fläche `004676`, 18 pt fett weiß, „maximal 2 Zeilen".
- **Kommentarbox:** Sprechblase mit weißer Fläche und Verlaufsrand Hellblau → PTA-Blau 1,5 pt, Text
  14 pt fett PTA-Blau.
- **Hervorhebung** in Schaubildern: Gelb `FDDC35`.
- **Sticker** „VERTRAULICH" bzw. „Für den internen Gebrauch" (Schulungsvorlage, auf dem Master):
  oben rechts links neben der Eckklammer, grauer Verlauf, 10 pt `787878`, rechtsbündig.
- Schriftgrößen in der Vorlagensammlung: 18 pt Standard, 14/12/10 pt in dichten Schaubildern,
  9 pt für Fußzeile und Quellen.

### Regeln auf den Musterfolien (wörtlich)

- „Bitte benutzen Sie nur die in der Vorlage vorgegebenen Layouts bei der Erstellung Ihrer
  Inhalte." / „Bitte vermeiden Sie aus technischen Gründen einen Layoutwechsel." (Basisvorlage, 1)
- „Einzufügende Objekte sollten nach Möglichkeit innerhalb der Inhaltsfläche an mindestens einer
  Linie ansetzen. Wenn Sie Layouts mit zwei Inhalten benutzen, richten Sie ihren Inhalt bitte an den
  vertikalen Linien (2 und 3) aus." (Basisvorlage, 2)
- „Erste Textebene: Subheadline / Zweite Textebene: Einleitungstext / Dritte Textebene: Erste
  Aufzählungsebene / Vierte Textebene: Zweite Aufzählungsebene / Fünfte Textebene: Dritte
  Aufzählungsebene" (Basisvorlage, 4)
- Fußzeile über „Einfügen → Kopf- und Fußzeile → Für alle übernehmen": Foliennummer an, Fußzeile
  an, Datum aus. (Basisvorlage, 5)
- Schulungsunterlagen (Schulungsvorlage, 1): Aufzeichnung nur mit „Kennzeichnung Vertraulichkeit
  der Folien, d.h. nur für internen Gebrauch", ohne Kundennamen, Projektdetails und
  personenbezogene Daten.

Eine Regel zu Mindestschriftgrößen oder zur Logoverwendung steht auf keiner Folie.

### Unterschiede der PowerPoint-Dateien

| Datei | Unterschied zur Basisvorlage |
| ----- | ---------------------------- |
| Vorlagensammlung | Master und alle 35 Layouts bytegleich; nur Musterfolien (mit think-cell erstellt) |
| Schulungsvorlage | Master mit Sticker „Für den internen Gebrauch"; fünf Layouts mit geänderter Sichtbarkeit der Mastergrafiken; Checkliste als Folie 1 |
| Titelfolie EN | deutsches Logo aus den Titellayouts entfernt; englisches Logo (PNG, „Customer-focused IT solutions since 1969", „50 years of IT") auf der Folie |

## Abweichungen zwischen Word und PowerPoint

| Thema | Word | PowerPoint |
| ----- | ---- | ---------- |
| Textfarbe | `000000` | `404040` |
| Fließtextschrift | Segoe UI | Segoe UI Light |
| Tabellenkopf | `006FB9` | `004676` |
| Tabellenlinien | `AFAFAF` | `E6E6E6`, Abschluss `404040` |
| Aufzählungszeichen Ebene 2+ | ― (Calibri) | − (Segoe UI Light) |
| Logo | auf jeder Seite oben rechts (blau) | nur Titel-/Abschlussfolien (weiß) |
| Fußzeile | „PTA IT-Beratung · Stand · Seite x \| y" | „PTA – <Präsentationstitel>", Nummer links |
| Firmenname | „PTA IT-Beratung" / „PTA Gruppe" (Fußzeile), „PTA GmbH" (Eigenschaften) | „PTA Unternehmensberatung" (Eigenschaften) |

Die Generatoren übernehmen jeweils die Regeln **ihres** Formats; das PDF folgt Word.

## Folgerungen für die Generatoren

1. DOCX und PPTX werden **auf** den Vorlagen erzeugt, nicht nachgebaut: Formatvorlagen, Layouts,
   Theme, Logos und Erkennungszeichen kommen unverändert aus der Datei.
2. Das PTA-Designmodell im Code enthält nur, was die Generatoren selbst zeichnen müssen
   (Folientabellen, Fazit-Box, Diagrammfarben, PDF-Seiten) — und liest die Werte, wo möglich, aus
   den Vorlagen, damit es nicht von ihnen abweicht.
3. Vor dem Einbetten werden SharePoint-Kennungen, `[trash]`-Teile, Bearbeiternamen und die
   Musterfolien bzw. der Mustertext entfernt.
