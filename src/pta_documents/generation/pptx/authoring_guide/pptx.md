## Eine PTA-Präsentation aus Markdown

Inhalt schreiben, nicht gestalten: das Design kommt aus der PTA-Vorlage `{{variant}}`. Titel
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

Bildformate: {{imageFormats}}, dazu QR-Codes `![QR-Code zur Umfrage](qr:https://…)` (eingepasst,
nie beschnitten; den Link zusätzlich als Text schreiben). Ein Bild mit Text kommt rechts in
„Titel, Text und Bild 01“, ein Bild allein in „Titel und Bild 01“, mehrere Bilder in einem
Absatz nebeneinander (höchstens vier). Bildplatzhalter beschneiden das Bild; hinter dem Bild
steuern das:

- `{focus=top}` — der Ausschnitt: {{focusValues}} oder ein Punkt `30%,20%` (von links, von oben);
  bei Fotos mit Personen immer setzen.
- `{fit=contain}` zeigt Grafiken und Screenshots ganz statt beschnitten.
- `{.round}` rund um den Fokus, `{.grey}` in Graustufen; mehrere in einer Klammer.

{{syntax}}

## PTA-Folienarten

Höchstens eine Art je `##`, nie mit `.dark`, `kicker`, Containern oder Alerts. Eine Agenda gibt
es nur mit `{.agenda}`: bis {{agendaShort}} Punkte „Agenda (kurz)“, bis {{agendaItems}} „Agenda
(lang)“. `{.contact}`: bis {{contactPersons}} Personen, Fotos hochkant (etwa 7 : 9), Zeilen
Funktion, E-Mail (mit `@`), Telefon (`+` oder Ziffer vorn). `layout="…"` wählt eine Variante
derselben Art, etwa {{kindLayouts}}.

## Klick für Klick, Übergänge, Szenen

- `aufbau: listen` lässt jede Liste Punkt für Punkt erscheinen. Blockmarker nie vor `#`/`##`,
  nie als letzte Zeile, nie auf Titel-, Trenn- und Abschlussfolien oder PTA-Folienarten.
- Ein Übergang für das ganze Deck (`uebergang:`) oder je Kapitel; an einer `##` nur für eine
  besondere Folie. `morph` wirkt erst ab PowerPoint 2019, sonst wird überblendet.
- Szenen: Arten {{sceneKinds}}; Attribute {{sceneAttributes}}; Raster {{sceneGrid}} über der
  Inhaltsfläche; Farben nur die Rollen {{sceneColors}} (oder `#RRGGBB`).

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
„Nur Titel“. Die Layouts: {{templateLayouts}}.

{{icons}}

{{typography}}

{{diagrams}}

{{frontMatter}}

{{notes}}

## Wenn etwas falsch ist

Der Generator bricht mit Zeile und Grund ab (`Line 12: …`) und nennt die gültigen Werte. Häufig:

- Text, Liste oder Bild unter `# Kapitel` oder `# Danke {.closing}`: Inhalt gehört unter ein `##`.
- Unbekannte Namen (`::: card`, `> [!INFO]`, `{.darkk}`, `:icon-rakete:`): die Meldung nennt die
  gültigen bzw. ähnlichen.
- Eine Karte als `- Titel – Text` ohne fetten Anfang, eine Fazit-Box mit Tabelle oder mehr als
  zwei Zeilen, eine Agenda mit mehr als {{agendaItems}} Punkten: kürzen oder teilen.
- `layout="Titel und Text zweispaltig"`: nur exakte Namen aus der Liste oben.
- Ein Icon im Fließtext oder Titel einer Folie.

## Beispiel

````markdown
---
titel: Kundenportal 2.0
autor: Erika Muster
vorlage: {{variant}}
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
