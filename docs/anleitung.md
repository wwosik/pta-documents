# Anleitung für Anwender

Mit PTA Documents schreibst du einen Bericht oder eine Präsentation als Markdown-Text und
bekommst daraus ein Word-Dokument oder eine PowerPoint-Präsentation **auf den offiziellen
PTA-Vorlagen** — mit Deckblatt, Logo, Kopf- und Fußzeile, PTA-Formatvorlagen und PTA-Layouts.
Umgekehrt macht es aus vorhandenen Word- und PowerPoint-Dateien Markdown.

Noch nicht möglich (geplant): PDF, Diagramme (Mermaid), Charts, farbige Hinweisboxen und
Kartenlayouts auf Folien, SVG-Bilder.

## 1. Einmal einrichten

Du arbeitest direkt in einem Klon dieses Repos. Voraussetzung ist Python 3.12 oder neuer.

```sh
git clone <repo-url> pta-documents
cd pta-documents
./run.sh setup          # unter Windows: .\run.ps1 setup
```

Ob alles läuft, zeigt das Beispiel zum Hauptbeskidenweg:

```sh
./run.sh generate samples/gsb --out documents/gsb
```

Danach liegen `gsb-bericht.docx` und `gsb-praesentation.pptx` in `documents/gsb/`. Die
Markdown-Dateien in `samples/gsb/` sind die beste Vorlage für eigene Dokumente; alles, was
die Generatoren können, zeigt `samples/funktionen/`
(`./run.sh generate samples/funktionen --out documents/funktionen`).

Später holst du Neuerungen mit `git pull` und danach einmal `./run.sh setup`.

## 2. Eigene Dokumente erzeugen

Eigene Dokumente gehören in den Ordner **`documents/`** — git ignoriert ihn, nichts davon landet
im Repo, und `git pull` stört ihn nicht. Ein Thema, ein Ordner:

```
documents/statusbericht-q3/
  statusbericht-bericht.md        → Word
  statusbericht-praesentation.md  → PowerPoint
  images/                         → Bilder (PNG, JPEG, GIF)
```

```sh
./run.sh generate documents/statusbericht-q3
```

Word und PowerPoint entstehen neben den Markdown-Dateien. Die Endung des Dateinamens wählt das
Format: `…-bericht.md` oder `…-dokument.md` → Word, `…-praesentation.md` oder `…-folien.md` →
PowerPoint. Andere Namen gehen mit `--docx` bzw. `--pptx`; `--out <ordner>` schreibt woanders hin;
statt eines Ordners kann man auch einzelne Dateien angeben. Bilder werden relativ zur
Markdown-Datei angegeben: `![Beschreibung](images/foto.jpg "Bildunterschrift")`.

Ein Fehler in einer Datei wird gemeldet, die anderen Dateien werden trotzdem erzeugt.

## 3. Der Kopf des Dokuments (Front Matter)

Ganz oben, zwischen zwei Zeilen `---`, stehen Angaben zum Dokument — je Zeile `schlüssel: wert`.
Werte mit Doppelpunkt in Anführungszeichen setzen. Ja/Nein heißt `ja`/`nein`, ein Datum
`2026-11-06` oder `06.11.2026`.

```markdown
---
titel: Statusbericht Projekt Nordlicht
untertitel: Quartal 3
autor: Erika Muster
ort: Hamburg
datum: 2026-11-06
---
```

| Schlüssel | Word | PowerPoint | Bedeutung |
| --------- | :--: | :--------: | --------- |
| `vorlage` | ✓ | ✓ | Word: `hoch` (Standard), `hoch-ohne-deckblatt`, `quer`, `quer-ohne-deckblatt`. PowerPoint: `basis` (Standard), `schulung` |
| `titel` | ✓ | ✓ | Titel; in Word mit Deckblatt Pflicht |
| `untertitel` | ✓ | ✓ | Untertitel |
| `autor`, `ort`, `datum` | ✓ | ✓ | Zeile „Autor, Ort, Datum" auf Deckblatt bzw. Titelfolie |
| `firma` | ✓ | | ersetzt „PTA IT-Beratung" in der Word-Fußzeile |
| `inhaltsverzeichnis` | ✓ | | `ja`: Inhaltsverzeichnis nach dem Deckblatt |
| `sprache` | ✓ | ✓ | `de` (Standard) oder `en` — z. B. „Page"/„Table"/„Figure", englische Titelfolie |
| `fusszeile` | | ✓ | Text der Fußzeile „PTA – …" (sonst der Titel) |
| `titelfolie` | | ✓ | `bild-02` (Standard), `bild-01`, `branchen`, `ohne-bild` |

Ein falscher Schlüssel oder Wert bricht mit einer Meldung ab, die die gültigen Werte nennt.

## 4. Word-Bericht schreiben

| Du schreibst | Im Word-Dokument |
| ------------ | ---------------- |
| `# Kapitel` | Überschrift 1 (nummeriert 1, 2, 3 …) |
| `## Abschnitt`, `### Unterabschnitt` | Überschrift 2 und 3 (1.1, 1.1.1) |
| `#### Zwischentitel` | Zwischenüberschrift (Versalien, ohne Nummer) |
| normaler Absatz | Standard |
| `**Absatz nur fett**` | Standard fett — direkt vor einer Tabelle ist das ihr Titel |
| `- Punkt` (eingerückt bis 3 Ebenen) | PTA-Aufzählung (■, dann ―) |
| `1. Schritt` | nummerierte Liste, jede Liste beginnt wieder bei 1 |
| Tabelle mit `\|` | Tabellenformat „PTA" (blauer Kopf) |
| `Tabelle: Text` direkt unter der Tabelle | Beschriftung „Tabelle 1: Text" |
| Bild allein im Absatz | Bild in Satzspiegelbreite, darunter „Abbildung 1: …" aus dem Bildtitel (in `"…"`) oder dem Alt-Text |
| ```` ``` ```` Codeblock | Formatvorlage Code (Consolas, grau hinterlegt) |
| `> Zitat` | eingerücktes Zitat |
| `[Text](https://…)` | Hyperlink |
| `Text[^1]` und `[^1]: Erklärung` | Word-Fußnote |
| `**fett**`, `*kursiv*`, `~~durch~~`, `` `code` `` | entsprechend formatiert |

Der Titel kommt **nur** aus dem Front Matter — `#` ist immer ein Kapitel.

## 5. Präsentation schreiben

```markdown
# Titel der Präsentation        ← Titelfolie (das erste #)

# Erstes Kapitel                ← Trennfolie „01"

## Folientitel                  ← eine Folie

Einleitender Satz.              ← Textebene „Einleitungstext"

- Aufzählung                    ← Aufzählungsebenen (bis 3 tief)

### Zwischenzeile               ← Textebene „Subheadline"

# Danke! {.closing}             ← Abschlussfolie
```

- Unter einem Kapitel-`#` und unter der Abschlussfolie darf **kein Inhalt** stehen — die
  PTA-Layouts haben dort keinen Platz. Inhalt gehört unter `##`.
- Eine **Tabelle**, ein **Codeblock** oder **mehrere Bilder** bekommen eine eigene Folie; Text
  davor steht oben, Text danach unten. Ein fetter Absatz direkt vor der Tabelle wird ihre
  Titelzeile.
- **Ein Bild mit Text** kommt auf das Layout „Titel, Text und Bild 01", ein Bild allein auf
  „Titel und Bild 01" — das Bild wird auf den Rahmen zugeschnitten.
- **Bestimmtes Layout:** `## Folie {layout="Titel und Text (zweispaltig)"}`. Der Inhalt wird an
  Zeilen `---` auf die Textfelder verteilt (links, rechts). Der Name muss genau stimmen; bei einem
  Tippfehler listet die Meldung alle 35 Layouts.
- **Zu viel Inhalt** wird bis 12 pt verkleinert; reicht das nicht, geht es auf einer Folie
  „… (Forts.)" weiter. Besser: kurze Folien schreiben.
- Text vor dem ersten `#` wird ignoriert. Fotos brauchen ihren Urheber auf der Folie, wenn die
  Lizenz das verlangt (siehe `samples/gsb/`).

### Folien-Syntax

Mit einer eigenen Syntax werden aus einer `##`-Folie **Flow-Folien** im PTA-Stil. PowerPoint
zeichnet sie auf dem Layout `Nur Titel`; Word nimmt dieselbe Syntax an und zeigt sie schlicht:
Container-Inhalte nacheinander (Karten- und Spaltenüberschriften fett statt als Überschrift),
Hinweiskästen, Fazit- und Kommentarbox als graue Absätze mit farbiger Linie links und fetter Art
am Anfang („Hinweis:", „Fazit:"), `==Markierung==` gelb hinterlegt, farbige Wörter und
Status-Labels in der Statusfarbe, mehrere Bilder in einem Absatz nebeneinander, jedes mit seiner
Beschriftung.

```markdown
## Warum neu bauen? {kicker="Warum"}

::: cards
### Zu kompliziert
**26 Tabellen**

für 12 Arten von Regeln.

### Zu langsam
**3,2 GB**

Speicher je Fahrplan.
:::

::: conclusion
Ein Neubau ist günstiger als jede weitere Erweiterung.
:::
```

- Container `::: name` … `:::` (verschachtelt mit längeren Zäunen, `::::` außen):
  `cards` (Karten nebeneinander, je eine `###`-Überschrift, darunter optional eine fette
  Kennzahl, oder eine Liste `- **Titel** – Text`), `rows` (eine Liste `- **Begriff** –
  Beschreibung`), `panel` bzw. `panel dark` (graue bzw. dunkelblaue Fläche), `statement` (der
  erste Absatz groß), `columns` bzw. `columns 1:2` (Spalten, getrennt durch eine Zeile `---` mit
  Leerzeile davor), `conclusion` (die PTA-Fazit-Box am Fuß der Folie, höchstens zwei Zeilen,
  einmal je Folie) und `comment` (die PTA-Kommentarbox, eine Sprechblase rechts oben auf dem
  Block davor, z. B. einem Diagramm).
- Hinweiskästen `> [!NOTE]`, `[!TIP]` (Balken PTA-Blau), `[!IMPORTANT]`, `[!WARNING]`,
  `[!CAUTION]` (Balken Gelb); ein Absatz aus Code-Spans `` `a` `b` `` wird zu Chips.
- `==Markierung==` ist fett auf PTA-Gelb (auf allen Folien); eine Tabellenzeile, deren erste
  Zelle ganz markiert ist, steht auf Gelb.
- Farbige Wörter `[im Plan]{.success}` (`.warning`, `.danger`, `.info`, `.neutral`) sind fett
  in der Signalfarbe; im Front Matter `status.success: Erledigt` usw. — eine Tabellenzelle, die
  nur `` `Erledigt` `` enthält, bekommt auf Flow-Folien einen Ampelpunkt „●" in dieser Farbe.
- An `##`-Überschriften: `{kicker="Warum"}` (kleine Zeile über dem Titel) und `{.dark}` (Folie
  auf dem Verlauf der Titelfolie, Schrift weiß).
- Genau zwei gleich breite Spalten nur mit Text kommen auf das Vorlagenlayout
  `Titel und Text (zweispaltig)`.
- Passt eine Flow-Folie nicht, wird alles bis zu zweimal um ein Achtel kleiner (nie unter
  12 pt), dann geht es auf einer Folie „(Forts.)" weiter; Karten, Flächen und Spalten werden
  nicht geteilt, die Fazit-Box steht auf der letzten.

Ein Tippfehler oder ein falscher Aufbau (z. B. eine Karte ohne `###`) ergibt eine
Fehlermeldung mit Zeilennummer, die sagt, was zu ändern ist.

### Agenda, Zwischenfazit, Zitat, Kontakt

Für diese PTA-Folien genügt ein Attribut an der `##`-Überschrift; das passende Layout sucht
PowerPoint selbst aus.

```markdown
## Agenda {.agenda}

## Die Migration ist ohne Ausfall möglich {.interim}

## Was man nicht messen kann, kann man nicht lenken {.quote}

— Peter Drucker, Ökonom

## Ihre Ansprechpartner {.contact}

### Erika Mustermann

![Erika Mustermann](images/erika.jpg)
Projektleiterin
erika.mustermann@pta.de
+49 621 12345-0
```

- `{.agenda}` ohne Liste nimmt die Kapitel (`#`) der Präsentation; mit einer Liste deren Punkte
  (höchstens acht, ab fünf das lange Layout). Eine Agenda entsteht nur mit `{.agenda}`.
- `{.interim}` ist nur die Überschrift (Zwischenfazit), `{.quote}` die Überschrift als Zitat und
  ein Absatz darunter als Quelle.
- `{.contact}`: je Person eine `###`-Überschrift mit dem Namen, darunter Foto und Zeilen für
  Funktion, E-Mail und Telefon (Reihenfolge egal); ein bis fünf Personen. Bei genau einer
  Person darf danach noch Text oder eine Liste folgen. Ohne Foto bleibt keine graue Fläche.
- `layout="Zwischenfazit 02"` bzw. `layout="Zitat 02"` wählt die zweite Variante.
- Diagramme aus `chart`-Blöcken kommen auf die PTA-Diagrammlayouts, sobald der Chart-Renderer
  da ist (E06-S01).

## 6. Aus Python aufrufen (optional)

```python
from pathlib import Path

from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.generation.pptx.generator import PptxGenerator
from pta_documents.markdown import DocumentResource, MarkdownDocument, content_type_of

folder = Path("mein-ordner")
images = [
    DocumentResource(f"images/{p.name}", content_type_of(p.name), p.read_bytes())
    for p in (folder / "images").glob("*")
]
document = MarkdownDocument((folder / "bericht.md").read_text(encoding="utf-8"), images)
with open("bericht.docx", "wb") as output:
    DocxGenerator().generate(document, output)
```

Für PowerPoint `PptxGenerator` statt `DocxGenerator`. Python aufrufen geht mit
`.venv/bin/python mein-skript.py` (Windows: `.venv\Scripts\python mein-skript.py`). Word und PowerPoint nach Markdown:
siehe [verwendung.md](verwendung.md).

## 7. Mit einer KI arbeiten

Eine KI (z. B. Claude Code im geklonten Repo) kann die Markdown-Dateien für dich schreiben und
die Dokumente erzeugen. Sag ihr, sie soll zuerst [ki-anleitung.md](ki-anleitung.md) lesen —
`AGENTS.md` verweist sie ohnehin dorthin.

## 8. Wenn etwas schiefgeht

Fehler im Dokument melden sich als `DocumentConversionError` mit einem Satz, der sagt, was zu
ändern ist, meist mit Zeilennummer und den gültigen Werten, z. B.:

- `The template 'hoch' has a cover page and needs a title: add 'titel: …'` → `titel` ergänzen
  oder `vorlage: hoch-ohne-deckblatt`.
- `The image 'images/foto.png' … is not among the document's resources` → Datei fehlt in
  `images/` oder der Pfad ist falsch geschrieben.
- `… is a image/svg+xml` → SVG geht noch nicht; als PNG exportieren.
- `The PTA layout of a chapter slide has no place for content` → Inhalt unter ein `##`.

Neben Fehlern gibt es **Hinweise**: das Dokument wurde geschrieben, aber der Generator musste
etwas umgehen. `./run.sh generate` zeigt sie eingerückt unter der Datei, mit Zeilennummer im
Markdown (das Front Matter mitgezählt):

```
wrote documents/kunde/kunde-praesentation.pptx
  - line 14: The slide "Kosten" has too much for one slide and continues on 1 more. Split it in the Markdown or shorten it.
  - line 30: Raw HTML is left out of the deck. Write it in Markdown, or leave it out.
```

Hinweise sind keine Fehler, aber fast immer ein Grund, das Markdown zu ändern: eine
„(Forts.)"-Folie heißt meist zu viel Inhalt — besser selbst auf zwei Folien mit eigenen Titeln
aufteilen. Rohes HTML wird weggelassen, `mermaid`- und `chart`-Blöcke erscheinen (noch) als
Code, beschnittene oder stark vergrößerte Bilder besser in passender Größe und passenden
Proportionen ablegen. `--strict` lässt den Befehl bei Hinweisen wie bei Fehlern mit Code 1
enden. Alle Codes: [verwendung.md](verwendung.md#hinweise-generationresult).

Word fragt beim Öffnen eines Dokuments mit Inhaltsverzeichnis, ob Felder aktualisiert werden
sollen — mit „Ja" bestätigen, dann füllt Word das Verzeichnis.
