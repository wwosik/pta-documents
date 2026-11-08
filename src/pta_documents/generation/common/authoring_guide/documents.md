## {{heading}}

Inhalt schreiben, nicht formatieren: Schrift, Farben, Nummern, Kopf- und Fußzeile kommen aus der
PTA-Vorlage. Kein HTML.

{{variants}}

## Gliederung

- `#`, `##`, `###` werden „Überschrift 1–3“ mit den Nummern `1`, `1.1`, `1.1.1`; `####` und
  tiefer „Zwischenüberschrift“ ohne Nummer. Keine Nummern selbst schreiben.
- Der Titel kommt aus `titel:`, nie aus `#`: das erste `#` ist Kapitel 1.
- `# Glossar {.appendix}` am ersten Anhangskapitel: ab dort heißen die Kapitel A, B, C.

## Inhalte

| Markdown | {{target}} |
| -------- | ------- |
| Absatz; `\` am Zeilenende bricht um | „Standard“ |
| Absatz nur aus `**fett**` | „Standard fett“ |
| `**fett**`, `*kursiv*`, `~~weg~~`, `` `Code` `` | Zeichenformat |
| `-`, `1.` (bis drei Ebenen), `- [x]`, `Begriff` mit `: Erklärung` darunter | Liste, Aufgaben, Definition |
| Tabelle, direkt davor ein Absatz `**Titel**`, direkt danach `Tabelle: …` | Tabelle „PTA“ mit Titel und „Tabelle n: …“ |
| Tabellenzelle genau `[3/4]` (`0` bis `4`) | Harvey Ball |
| Bild allein im Absatz `![Alt](images/a.png "Titel")` | „Abbildung n: Titel“ (sonst Alt-Text) |
| mehrere Bilder in einem Absatz | nebeneinander, höchstens vier je Zeile |
| `![QR-Code](qr:https://pta.de "https://pta.de")` | QR-Code in PTA-Blau, ohne Bilddatei |
| `{.round}`, `{.grey}` oder `{scale=0.5}` direkt nach dem Bild | rund, grau, halb so groß |
| Codeblock, `> Zitat`, `---` | „Code“, „Zitat“, Trennlinie |
| `Satz.[^1]` und `[^1]: Text` | {{footnote}} |
{{links}}

Bildformate: {{imageFormats}}. Die Dateien gibt der Aufrufer mit; `images/a.png` muss darunter
sein.

{{syntax}}

{{icons}}

{{typography}}

{{characters}}

{{diagrams}}

{{frontMatter}}

## Wenn etwas falsch ist

Ein Fehler bricht ab und sagt (englisch), was zu ändern ist:

- `vorlage: hoch` ohne `titel:` — `… has a cover page and needs a title`.
- `::: karte` — `Line 12: Unknown container '::: karte'. Valid containers: …`.
- Bilddatei fehlt — `The image 'images/a.png' (line 8) is not among the document's resources.`
- Bildformat ohne Konverter — `… {{imageError}} …`.

{{notes}}

## Beispiel

````markdown
---
titel: Statusbericht Netzausbau
untertitel: Stand Mai 2026
autor: Erika Mustermann
kennzeichnung: vertraulich
status.success: Erledigt
status.warning: Verzug
---
# Lage

Der Ausbau ist [im Plan]{.success}; ==ein Paket== braucht Hilfe.

**Arbeitspakete**

| Paket | Stand |
| ----- | ----- |
| Migration | `Erledigt` |
| Schnittstellen | `Verzug` |

Tabelle: Stand der Arbeitspakete

# Nächste Schritte

![Zeitplan](images/plan.png "Zeitplan bis 2027")

> [!NOTE]
> Die Abnahme ist am 15.06.2026.
````
