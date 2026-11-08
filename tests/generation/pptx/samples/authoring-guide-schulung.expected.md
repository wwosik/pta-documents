## Eine PTA-Präsentation aus Markdown

Inhalt schreiben, nicht gestalten: das Design kommt aus der PTA-Vorlage `schulung`. Titel
nennen die Aussage, nicht das Thema; wenige Zeilen je Folie. Mit `--html` ergibt dasselbe
Markdown ein HTML-Deck mit denselben Folien; nur dort gelten `fortschritt: nein` und
`kapitelanzeige: nein`.

## Gliederung

| Markdown | Folie |
| -------- | ----- |
| erstes `#` | Titelfolie (Layout aus `titelfolie:`); ein Absatz darunter wird der Untertitel |
| jedes weitere `#` | Trennfolie mit Kapitelnummer „01“, „02“ … — nichts darunter außer `::: notes` |
| `##` | eine Folie; Titel höchstens zwei Zeilen |
| `# Botschaft {.closing}` | Abschlussfolie — nichts darunter außer `::: notes` |
| `# Backup {.backup}` | nach der Abschlussfolie: Reservefolien ohne Kapitelnummer, nicht in der Agenda |

Text vor dem ersten `#` und Fußnoten fallen weg.

## Inhalte

- Ein Absatz ist Einleitungstext, `-`-Listen sind Aufzählungen (bis drei Ebenen), `1.` nummeriert,
  `###` die Subheadline; `**fett**` ist die PTA-Hervorhebung.
- Höchstens sechs bis acht Punkte je Folie; was nicht passt, wird bis 12 pt verkleinert, dann auf
  „(Forts.)“-Folien fortgesetzt.
- Eine Tabelle, ein Codeblock, ein Diagramm oder eine Bildreihe je Folie; Text davor steht oben,
  Text danach unten (Quellen). Ein zweites davon unter demselben `##` ergibt eine weitere Folie
  mit demselben Titel. Ein `**fetter**` Absatz direkt vor einer Tabelle wird ihre Titelzeile;
  `[3/4]` in einer Zelle ist ein Harvey Ball (`[0/4]` bis `[4/4]`).
- Ein Absatz nur aus Code (`` `Python` `SQL` ``) wird eine Reihe Chips.

## Bilder

Bildformate: PNG, JPEG, SVG, dazu QR-Codes `![QR-Code zur Umfrage](qr:https://…)` (eingepasst,
nie beschnitten; den Link zusätzlich als Text schreiben). Ein Bild mit Text kommt rechts in
„Titel, Text und Bild 01“, ein Bild allein in „Titel und Bild 01“, mehrere Bilder in einem
Absatz nebeneinander (höchstens vier). Bildplatzhalter beschneiden das Bild; hinter dem Bild
steuern das:

- `{focus=top}` — der Ausschnitt: `center`, `top`, `bottom`, `left` oder `right` oder ein Punkt `30%,20%` (von links, von oben);
  bei Fotos mit Personen immer setzen.
- `{fit=contain}` zeigt Grafiken und Screenshots ganz statt beschnitten.
- `{.round}` rund um den Fokus, `{.grey}` in Graustufen; mehrere in einer Klammer.

## Folien-Syntax

Word, PowerPoint und PDF lesen dieselbe Syntax und prüfen sie, bevor sie schreiben: ein Fehler bricht mit der Zeile ab (`Line 12: …`) und nennt die gültigen Namen. Klammern, die nicht genau so aussehen, bleiben Text.

Auf Folien wird eine `##`-Folie mit Container, Alert, Chips, `.dark` oder `kicker` eine Flow-Folie auf „Nur Titel“: Karten im Raster (höchstens vier je Zeile), die Fazit-Box am Fuß der Folie, die Kommentarbox als Sprechblase am Block davor, Alerts als graue Fläche mit blauem oder gelbem Balken, `==…==` fett auf Gelb, Status-Labels mit Ampelpunkt. Was nicht passt, wird kleiner und dann geteilt; Karten, Flächen und Spalten werden nie geteilt.

### Container

Ein Container beginnt mit einer Zeile `::: <name>` (Argumente dahinter) und endet mit `:::`; ineinander stehen sie mit längeren Zäunen (`::::` außen).

| Container | Wofür |
| --------- | ----- |
| `::: cards` | Karten nebeneinander: je Karte `### Titel` und ein kurzer Text, oder eine Liste `- **Titel** – Text`; ein erster Absatz `**26 %**` ist die Kennzahl der Karte. |
| `::: rows` | Zeilen aus einer Liste `- **Begriff** – Beschreibung`. |
| `::: panel` | Eine Fläche um den Inhalt; `::: panel dark` dunkel. |
| `::: statement` | Eine Aussage: der erste Absatz groß und fett, der Rest normal. |
| `::: columns` | Spalten, getrennt durch `---` mit einer Leerzeile davor; `::: columns 1:2` oder `1:1:2` gibt die Breiten vor. |
| `::: conclusion` | Die PTA-Fazit-Box: nur Text, höchstens zwei Zeilen, einmal je Folie, nicht in einem anderen Container. |
| `::: comment` | Die PTA-Kommentarbox zum Block direkt davor; nur Text. |
| `::: notes` | Sprechernotizen der Folie: zwei bis fünf Sätze, die der Vortragende sagt; Tabellen und Bilder darin entfallen. |
| `::: timeline` | Ein Zeitstrahl aus einer Liste `- 2026-Q2: Text` (2 bis 8 Einträge, aufsteigend; Termine `2026`, `2026-03`, `2026-Q2`, `2026-03-15`, `15.03.2026` oder `heute`; `{.done}` am Ende eines Eintrags heißt erledigt). |
| `::: gantt` | Ein Projektplan aus einer Tabelle mit den Spalten Vorgang, Start, Ende und Wer (freiwillig), 1 bis 12 Zeilen, Start = Ende ist ein Meilenstein; `::: gantt raster=monat` (`woche`, `monat`, `quartal`) nur bei Bedarf. |
| `::: steps` | Eine Schrittfolge: 3 bis 6 Schritte, je `### Titel` und höchstens ein kurzer Absatz; `{.current}` an höchstens einem `###` hebt den aktuellen hervor. |
| `::: riskmatrix` | Eine Risikomatrix aus einer Tabelle mit den Spalten Nr, Risiko, Wahrscheinlichkeit, Auswirkung (Werte 1 bis 5) und Maßnahme (freiwillig); `::: riskmatrix green=4 yellow=12` verschiebt die Schwellen der Farben. |
| `::: scene` | Benannte Formen auf einem Raster, eine je Zeile `- name: box 10,10 40x20 "Text"`, allein unter einem `##`; zwei Szenenfolien mit denselben Namen und `{uebergang="morph"}` bewegen die Formen. |
| `::: internal` | Nur in den Fassungen `intern` und `trainer`: Preise, Bemerkungen. |
| `::: exercise` | Eine Aufgabe; steht in jeder Fassung. |
| `::: solution` | Die Lösung der Aufgabe davor (direkt nach oder in ihrem `::: exercise`), nur in der Fassung `trainer`. |

### Hinweise und Hervorhebungen

- Ein Zitat, dessen erste Zeile ein Alert ist, wird ein Hinweis: `> [!NOTE]` (Hinweis), `> [!TIP]` (Tipp), `> [!IMPORTANT]` (Wichtig), `> [!WARNING]` (Warnung), `> [!CAUTION]` (Vorsicht).
- `==Text==` markiert wie ein Textmarker; ist die erste Zelle einer Tabellenzeile ganz markiert, die ganze Zeile.
- `[Wörter]{.success}` setzt Wörter fett in einer Statusfarbe: `{.success}` (Erfolg, im Plan), `{.warning}` (Warnung, kritisch), `{.danger}` (Gefahr, verfehlt), `{.info}` (Information), `{.neutral}` (neutral, offen). Signalfarben nur für Status, zur Hervorhebung `==…==`.
- Status-Labels: `status.success: Erledigt; Fertig` im Front Matter und eine Tabellenzelle nur aus `` `Erledigt` `` ergeben ein Label in der Farbe.

### Attribute an Überschriften

Am Ende einer Überschrift, in geschweiften Klammern; mehrere in einer Klammer (`{.dark kicker="Kapitel 1"}`).

| Attribut | An | Wirkung |
| -------- | -- | ------- |
| `{.closing}` | `#` | Die Abschlussfolie; kein Inhalt darunter. |
| `{.dark}` | `##` | Die Folie auf dunklem Grund, für eine Kernaussage. |
| `{kicker="Kapitel 1"}` | `##` | Eine kleine Zeile über dem Titel. |
| `{layout="Titel und Text (zweispaltig)"}` | `#`, `##` | Ein Layout der PTA-Vorlage mit genau diesem Namen; `---` teilt den Inhalt auf. |
| `{uebergang="fade"}` | `#`, `##` | Der Übergang der Folie (an `#`: aller Folien des Kapitels). |
| `{.agenda}` | `##` | Die Agenda: eine Liste von höchstens acht Punkten, ohne Liste die Kapitel. |
| `{.interim}` | `##` | Ein Zwischenfazit: die Aussage im Titel, kein Inhalt. |
| `{.quote}` | `##` | Ein Zitat im Titel, höchstens ein Absatz (die Quelle) darunter. |
| `{.contact}` | `##` | Kontakte: je Person `### Name` und ein Absatz mit Foto, Funktion, E-Mail, Telefon. |
| `{.internal}` | `#`, `##` | Folie oder Kapitel nur in den Fassungen `intern`/`trainer`. |
| `{.backup}` | `#` | Einmal, nach der Abschlussfolie: die Folien danach sind Reservefolien ohne Nummer. |
| `{dauer=10}` | `#`, `##` | Geplante Minuten (`90`, `4h`, `1h30`, ohne Anführungszeichen) für den Zeitplan. |
| `{.break dauer=15}` | `##` | Eine Pause im Zeitplan, immer mit `dauer`, kein Inhalt. |

Die übrigen (`.appendix`) gelten nur für Word und PDF: PowerPoint nimmt sie an, die Überschrift bleibt eine gewöhnliche Überschrift.

### Blockmarker

Eine Zeile nur aus dem Marker, direkt vor dem Block (Absatz, Liste, Tabelle, Container):

- `{.build}`: Der Block erscheint beim Klick — Listen, Karten, Zeilen, Spalten und Bildreihen Punkt für Punkt.
- `{.frag}`: Der Block erscheint beim Klick als Ganzes.
- `{.exit}`: Der Block verschwindet beim Klick.
- `{.emphasize}`: Der Text wird beim Klick PTA-blau.
- `{.internal}`: Der Block steht nur in den Fassungen `intern` und `trainer`.
- Eingang: `{.build=appear}`, `=fly`, `=wipe` (Standard `=fade`, einblenden), ebenso an `{.frag}`. Nur unter `##`-Folien, sparsam.

## PTA-Folienarten

Höchstens eine Art je `##`, nie mit `.dark`, `kicker`, Containern oder Alerts. Eine Agenda gibt
es nur mit `{.agenda}`: bis 4 Punkte „Agenda (kurz)“, bis 8 „Agenda
(lang)“. `{.contact}`: bis 5 Personen, Fotos hochkant (etwa 7 : 9), Zeilen
Funktion, E-Mail (mit `@`), Telefon (`+` oder Ziffer vorn). `layout="…"` wählt eine Variante
derselben Art, etwa „Agenda (lang)“, „Zwischenfazit 02“, „Zitat 02“, „Kontakt 02“.

## Klick für Klick, Übergänge, Szenen

- `aufbau: listen` lässt jede Liste Punkt für Punkt erscheinen. Blockmarker nie vor `#`/`##`,
  nie als letzte Zeile, nie auf Titel-, Trenn- und Abschlussfolien oder PTA-Folienarten.
- Ein Übergang für das ganze Deck (`uebergang:`) oder je Kapitel; an einer `##` nur für eine
  besondere Folie. `morph` wirkt erst ab PowerPoint 2019, sonst wird überblendet.
- Szenen: Arten `box`, `round`, `pill`, `circle`, `text`, `line`, `arrow` und `image`; Attribute `fill`, `line`, `text`, `rotate`, `opacity`, `size`, `bold`, `solid`, `step` und `image`; Raster 160 × 67 über der
  Inhaltsfläche; Farben nur die Rollen `primary`, `text`, `muted`, `background`, `accent1–accent6`, `surface`, `border`, `line`, `success`, `warning`, `danger`, `info` und `neutral` (oder `#RRGGBB`).

## Fassungen und Zeitplan

- Preise, Tagessätze und alles, was der Kunde nicht sehen soll, immer in `::: internal` oder
  hinter `{.internal}`; Lösungen in `::: solution`. `./run.sh generate … --audience alle`
  schreibt alle Fassungen; interne tragen den Sticker „intern“.
- Für Schulungen jeder Folie oder jedem Kapitel eine Dauer geben und `beginn:`/`laenge:` setzen:
  Folien eines Kapitels mit `{dauer=45}` ohne eigene Angabe teilen sich den Rest, die Agenda
  zeigt Uhrzeiten und Pausen. Ab `{.closing}` keine `dauer` und kein `.break`.
- Sprechernotizen zu jeder Folie, auch zu Titel-, Trenn- und Abschlussfolie; nie vor dem ersten
  `#`.

## Vorlagenlayouts

`{layout="…"}` wählt ein Layout der Vorlage mit genau diesem Namen; die Inhalte werden an `---`
(mit Leerzeile davor) der Reihe nach auf seine Platzhalter verteilt. Mit Flow-Inhalt geht nur
„Nur Titel“. Die Layouts: „Titelfolie mit Bild 01“, „Titelfolie mit Bild 02“, „Titelfolie Branchen“, „Titelfolie ohne Bild“, „Agenda (kurz)“, „Agenda (lang)“, „Trennfolie“, „Nur Titel“, „Titel und Text“, „Titel und Text (zweispaltig)“, „Titel, Bild und Text“, „Titel, Text und Bild 01“, „Titel, Text und Bild 02“, „Titel, Text und Bild 03“, „Titel, Text und Bild 04“, „Titel, Text und zwei Bilder 01“, „Titel, Text und zwei Bilder 02“, „Titel, Text und zwei Bilder 03“, „Titel und Bild 01“, „Titel und Bild 02“, „Zwischenfazit 01“, „Zwischenfazit 02“, „Titel und Diagramm“, „Titel und zwei Diagramme“, „Titel, Diagramm und Text“, „Titel, Text und Diagramm“, „Zitat 01“, „Zitat 02“, „Kontakt mit Text“, „Kontakt 01“, „Kontakt 02“, „Kontakt 03“, „Kontakt 04“, „Kontakt 05“, „Abbschlussfolie“.

## Icons

`:icon-check:` setzt ein Strich-Icon in PTA-Blau — keine Bilddatei, keine Quelle nötig. Auf Folien nur vor dem Titel einer Karte (`### :icon-rocket: Start` in `::: cards`) und vor **jedem** Punkt einer Liste (dann das Aufzählungszeichen); anderswo ist ein Icon ein Fehler. Nur diese Namen; ein anderer ist ein Fehler, der ähnliche nennt:

`access-point` `adjustments` `alert-circle` `alert-triangle` `api` `arrow-down` `arrow-left` `arrow-right` `arrow-up` `arrows-exchange` `award` `ban` `bell` `bolt` `book` `brain` `briefcase` `bug` `building` `building-community` `bulb` `calculator` `calendar` `calendar-event` `cash` `certificate` `chart-bar` `chart-dots` `chart-line` `chart-pie` `check` `checklist` `circle-check` `circle-x` `clipboard-check` `clipboard-list` `clock` `cloud` `cloud-download` `cloud-upload` `code` `coin` `compass` `components` `copyright` `cpu` `currency-euro` `database` `device-desktop` `device-laptop` `device-mobile` `download` `edit` `eye` `file` `file-check` `file-text` `files` `filter` `flag` `flame` `flask` `folder` `folder-open` `gavel` `git-branch` `git-merge` `globe` `hand-stop` `headset` `heart` `heart-handshake` `help-circle` `hierarchy` `hierarchy-2` `home` `hourglass` `id-badge-2` `infinity` `info-circle` `key` `layers-intersect` `layout-dashboard` `leaf` `license` `lifebuoy` `link` `list-check` `loader` `lock` `lock-open` `mail` `map` `map-pin` `message` `message-circle` `messages` `microscope` `minus` `mood-sad` `mood-smile` `network` `notebook` `package` `pencil` `percentage` `phone` `player-pause` `player-play` `plug` `plus` `presentation` `printer` `progress` `puzzle` `receipt` `recycle` `refresh` `repeat` `report-analytics` `report-money` `robot` `rocket` `rotate` `route` `scale` `school` `search` `server` `server-2` `settings` `share` `shield` `shield-check` `shopping-cart` `sitemap` `sort-ascending` `sparkles` `square-check` `star` `target` `target-arrow` `terminal-2` `test-pipe` `thumb-down` `thumb-up` `tool` `tools` `trash` `trending-down` `trending-up` `truck` `upload` `user` `user-check` `users` `users-group` `wifi` `world` `writing` `x` `zoom-check`

## Typografie und Code

Gerade Anführungszeichen (`"…"`, `'…'`), ` - ` und `...` schreiben: der Generator setzt „…“, ‚…‘, – und … und schützt Leerzeichen in `z. B.`, `Nr. 3`, `10 %`. Code, Links und Front Matter bleiben unberührt; `typografie: nein` schaltet es ab. Codeblöcke mit Sprache (```` ```python ````) werden farbig (`syntaxhervorhebung: nein` schaltet ab); eine unbekannte Sprache ergibt den Hinweis `code-language-unknown`.

## Charts

Ein Codeblock mit der Sprache `chart` wird ein Balken-, Linien- oder Flächendiagramm in den
PTA-Farben — in Word und PowerPoint ein echtes Diagramm, dessen Daten sich mit „Daten
bearbeiten" ändern lassen. Oben stehen die Einstellungen, je Zeile `name: wert`, dann eine
Zeile `---`, dann die Daten als CSV: eine Kopfzeile (der Name der Kategorienspalte, dann ein
Name je Reihe) und eine Zeile je Kategorie.

````markdown
```chart
type: bar
title: Aufträge je Monat
unit: Tsd. EUR
source: Quelle: Vertrieb
---
Monat, Plan, Ist
Jan, 120, 132
Feb, 118, 121
Mär, 125, 140
```
````

- **Einstellungen** (englisch, alle freiwillig): `type` ist `bar` (Balken, Standard), `line`
  (Linien) oder `area` (Flächen); `stacked: true` stapelt Balken oder Flächen (Linien nie);
  `title`, `unit` (Einheit der Werte) und `source` (Quellenangabe). Ein Kommentar steht nach
  ` # `. Ohne Einstellungen besteht der Block nur aus der CSV.
- **Zahlen:** Mit `,` als Trennzeichen haben Zahlen einen Dezimalpunkt (`1250.5`), mit `;` ein
  Dezimalkomma (`1250,5`) — die Kopfzeile entscheidet. Keine Tausenderpunkte. Ein Feld in
  Anführungszeichen darf das Trennzeichen enthalten; ein leeres Feld lässt eine Lücke.
- **Folien:** Ein Chart allein kommt auf `Titel und Diagramm`, mit Text davor auf
  `Titel, Text und Diagramm`, mit Text danach auf `Titel, Diagramm und Text`; zwei Charts
  (auch in `::: columns`) auf `Titel und zwei Diagramme`. Titel, Einheit und Quelle stehen in
  den Platzhaltern des Layouts. Auf Folien mit Hinweisboxen, Karten o. Ä. ist ein Chart ein
  Fehler.
- **Word:** Das Diagramm steht über die Satzspiegelbreite (höchstens 5:8 so hoch), mit einem
  Titel darunter die Beschriftung „Abbildung n: Titel". Ein Absatz `Abbildung: …` direkt nach
  dem Block geht dem Titel vor.
- Ein Fehler in Einstellungen oder Daten bricht mit der Zeile ab, in der er steht.

### Finanzdiagramme

Ein Codeblock mit der Sprache `financial-chart` enthält eines der Diagramme einer
Ergebnisübersicht als JSON: `development` (Entwicklung über das Jahr), `growth-by-row`
(Wachstum je Zeile), `actual-vs-reference` (Ist gegen Plan), `growth-trend` (Wachstumstrend),
`two-year` (zwei Jahre Monat für Monat) oder `summary-table` (Übersichtstabelle). Die Schlüssel
sind englisch, weil solche Blöcke meist ein Programm schreibt. Wachstumsraten und Anteile sind
Brüche (`0.05` sind 5 %), `lastActual` zählt die Monate ab 0.

````markdown
```financial-chart
{
  "type": "growth-trend",
  "title": "Wachstum Aufträge",
  "period": "Mai 2026",
  "lastActual": 2,
  "reference": 0.05,
  "months": [
    { "label": "Jan", "change": 0.056 }, { "label": "Feb", "change": 0.054 },
    { "label": "Mär", "change": 0.04 }, { "label": "Apr", "change": 0.045 },
    { "label": "Mai", "change": 0.05 }
  ],
  "options": { "labels": { "reference": "Ziel" } }
}
```
````

- **Sprache:** Zahlen und Beschriftungen folgen `sprache:` (deutsch: `5,2 %`, *Vorjahr*, *Ist*,
  *Plan*, *Prognose*); `"culture": "en"` (oder `de`, `de-DE`, `en-US`, `en-GB`) stellt um.
- **Optionen** (`options`): `culture`, `scale` und `unit` (`1000000` und `Mio. EUR`), `labels`
  über denen der Sprache (`previous`, `current`, `reference`, `projection`, `estimate`,
  `change`, `overall`, `value`), `tolerance` (ab wann eine Zahl vorn oder hinten liegt, Standard
  `0.005`), `restShare` und `width` (Breite in Pixeln, Standard 560).
- **Regeln:** Eine Farbe bedeutet eine Reihe, Grün und Rot stehen nur an Zahlen, gestrichelt
  heißt Prognose, jede Werteachse enthält null.
- **Folien:** Das Diagramm steht als Gruppe bearbeitbarer Formen in der Inhaltsfläche von
  `Nur Titel` (mit Text davor auf `Titel und Text`), nie größer als gezeichnet.
- **Word:** Das Diagramm steht als Bild (scharf als SVG, mit PNG für ältere Word-Versionen) in
  seiner natürlichen Größe, höchstens über die Satzspiegelbreite; ein Absatz `Abbildung: …`
  direkt nach dem Block wird die Beschriftung „Abbildung n: …". Dafür braucht es das Extra `svg`.
- Ein unbekannter Schlüssel, ein falscher Typ oder ungültiges JSON bricht mit der Zeile ab;
  Kommentare (`//`) und ein Komma nach dem letzten Eintrag sind erlaubt.

## Front Matter

Einstellungen stehen in einem Block ganz oben, vor allem anderen, zwischen zwei Zeilen `---`: je Zeile `schlüssel: wert`, ohne Verschachtelung und ohne Listen. Schlüssel und Werte sind deutsch, Wahrheitswerte `ja` oder `nein`. Was der Standard schon tut, weglassen.

```markdown
---
titel: Kundenportal 2.0
vorlage: schulung
titelfolie: bild-01
kennzeichnung: vertraulich
status.success: Erledigt; Fertig
---
```

| Schlüssel | Werte | Bedeutung |
| --------- | ----- | --------- |
| `vorlage` | `basis`, `schulung` (Standard) | Die PTA-Vorlage; `schulung` ist die Schulungsvorlage mit dem Sticker „intern“. |
| `titel` | frei | Der Titel; ohne `titel` der Text des ersten `#`. |
| `untertitel` | frei | Der Untertitel der Titelfolie. |
| `autor` | frei | Autor auf der Titelfolie und in den Eigenschaften. |
| `ort` | frei | Ort auf der Titelfolie, nach dem Autor. |
| `datum` | `2026-11-08` oder `08.11.2026` | Das Datum des Dokuments statt des heutigen. |
| `sprache` | `de` (Standard), `en` | Die Sprache der erzeugten Texte („Seite“, „Tabelle“, Hinweisnamen). |
| `typografie` | `ja` (Standard), `nein` | Gerade Anführungszeichen, ` - ` und `...` werden „…“, – und …; `nein` lässt sie. |
| `syntaxhervorhebung` | `ja` (Standard), `nein` | Codeblöcke mit Sprache werden farbig; `nein`: einfarbig. |
| `pruefung` | `aus` oder `style-…`-Codes, durch Kommas getrennt | Nur `./run.sh check`: diese Stilregeln nicht prüfen. |
| `fusszeile` | frei | Die Fußzeile „PTA – …“; ohne Angabe der Titel der Präsentation. |
| `titelfolie` | `bild-01`, `bild-02` (Standard), `branchen`, `ohne-bild` | Das Layout der Titelfolie. |
| `kennzeichnung` | `vertraulich`, `intern` (Standard), `entwurf` | Der Sticker oben rechts auf allen Folien; die Schulungsvorlage braucht einen, `kein` ist dort ein Fehler. |
| `aufbau` | `listen`, `nein` (Standard) | `listen`: jede Liste erscheint Punkt für Punkt, als stünde `{.build}` davor. |
| `uebergang` | `none` (Standard), `fade`, `push`, `push-left`, `push-right`, `push-up`, `push-down`, `wipe`, `wipe-left`, `wipe-right`, `wipe-up`, `wipe-down`, `split`, `cover`, `uncover`, `zoom`, `cut`, `morph` | Der Übergang aller Folien, außer wo ein `#` oder `##` einen eigenen hat. |
| `fassung` | `kunde` (Standard), `intern`, `trainer` | Die Fassung: `kunde` ohne Internes und Lösungen, `intern` mit Internem, `trainer` mit allem. |
| `beginn` | Uhrzeit `09:00` | Beginn der Schulung: die Agenda zeigt Uhrzeiten. |
| `laenge` | Minuten `240`, `4h` oder `3h30` | Die geplante Länge, mit der Summe der `dauer` verglichen. |
| `status.<kategorie>` | Texte, durch `;` getrennt | Tabellenzellen nur aus einem dieser Texte als Code (`` `Erledigt` ``) werden Status-Labels in der Farbe der Kategorie: `success` (Erfolg, im Plan), `warning` (Warnung, kritisch), `danger` (Gefahr, verfehlt), `info` (Information), `neutral` (neutral, offen). Jeder Text gehört zu einer Kategorie. |

Ein unbekannter Schlüssel, ein doppelter oder ein ungültiger Wert ist ein Fehler, der die gültigen nennt.

## Hinweise

Was der Generator umgehen musste, meldet er als Hinweis mit Zeile (`line 12: …`); das Dokument ist trotzdem geschrieben. Das Markdown so ändern, dass keine Hinweise mehr kommen.

| Code | Was tun |
| ---- | ------- |
| `slide-split` | Zu viel für eine Folie; es geht auf „(Forts.)“-Folien weiter. Kürzen oder teilen. |
| `slide-overfull` | Passt auch bei 12 pt nicht und läuft über den Folienrand. Kürzen. |
| `image-cropped` | Der Bildrahmen schneidet mehr als ein Viertel des Bildes ab: `{focus=…}`, `{fit=contain}` oder ein Bild in passenden Proportionen. |
| `image-enlarged` | Ein Bild wird mehr als doppelt so groß gezeigt, wie es Pixel hat, und wirkt unscharf. |
| `raw-html` | Rohes HTML wird weggelassen; Markdown schreiben. |
| `code-not-drawn` | Ein Diagramm- oder Chart-Block wurde nicht gezeichnet und steht als Code da. |
| `code-language-unknown` | Die Sprache eines Codeblocks ist unbekannt; er steht einfarbig da. |
| `image-scale-in-title` | `scale=N` im Bildtitel gehört als `{scale=N}` hinter das Bild. |
| `audience-omitted` | Die Fassung hat interne Blöcke oder Lösungen weggelassen — erwartet, kein Fehler. |
| `schedule-missing` | Folien ohne `dauer` in einem Deck mit Zeitplan; sie zählen je 2 Minuten. |
| `schedule-length` | Die Summe der Dauern trifft `laenge:` nicht, oder ein Kapitel braucht mehr als seine `dauer`. |
| `schedule-estimate` | Nur `./run.sh check`: die geplante Zeit weicht stark von der Faustregel ab. |
| `attribute-ignored` | Ein Überschriftenattribut des anderen Dokumenttyps (`{.backup}` in Word und PDF, `{.appendix}` auf Folien) bleibt ohne Wirkung. |

## Wenn etwas falsch ist

Der Generator bricht mit Zeile und Grund ab (`Line 12: …`) und nennt die gültigen Werte. Häufig:

- Text, Liste oder Bild unter `# Kapitel` oder `# Danke {.closing}`: Inhalt gehört unter ein `##`.
- Unbekannte Namen (`::: card`, `> [!INFO]`, `{.darkk}`, `:icon-rakete:`): die Meldung nennt die
  gültigen bzw. ähnlichen.
- Eine Karte als `- Titel – Text` ohne fetten Anfang, eine Fazit-Box mit Tabelle oder mehr als
  zwei Zeilen, eine Agenda mit mehr als 8 Punkten: kürzen oder teilen.
- `layout="Titel und Text zweispaltig"`: nur exakte Namen aus der Liste oben.
- Ein Icon im Fließtext oder Titel einer Folie.

## Beispiel

````markdown
---
titel: Kundenportal 2.0
autor: Erika Muster
vorlage: schulung
status.success: Erledigt
status.warning: In Arbeit
---
# Kundenportal 2.0

Ergebnisse der Pilotphase

::: notes
Begrüßung und Ziel des Termins: Entscheidung über den Rollout.
:::

# Ergebnisse

## Der Pilot spart 30 % Bearbeitungszeit

Drei Abteilungen haben das Portal sechs Wochen genutzt.

- Anträge werden am selben Tag bearbeitet
- Rückfragen sinken um die Hälfte
- Die Kunden bewerten das Portal mit 4,6 von 5

::: notes
Die Zahlen stammen aus der Auswertung der Fachabteilungen.
:::

## Drei Bausteine tragen den Erfolg

::: cards
### Formulare
Alle Anträge digital, ohne Medienbruch.

### Status
Kunden sehen jederzeit den Stand.

### Postfach
Rückfragen ohne E-Mail-Verkehr.
:::

::: conclusion
Der Rollout lohnt sich ab dem ersten Quartal.
:::

## Zwei Pakete fehlen noch

| Paket | Stand |
| ----- | ----- |
| Formulare | `Erledigt` |
| Schnittstelle Archiv | `In Arbeit` |

> [!NOTE]
> Das Archiv folgt im März.

# Rollout freigeben {.closing}
````
