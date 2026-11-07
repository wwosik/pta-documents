# Verwendung

Stand nach Meilenstein M01: Markdown → Word und PowerPoint auf den PTA-Vorlagen, Word und
PowerPoint → Markdown. PDF, Diagramme und Charts folgen (E05, E06).

## Einrichten

```sh
./run.sh setup      # .venv anlegen, Paket editierbar mit allen Extras installieren
./run.sh test       # Tests
```

In einem anderen Projekt wird das Paket aus dem Repo heraus installiert:
`pip install -e /pfad/zu/pta-documents` — veröffentlicht wird es nicht.

## Markdown → Word

```python
from pta_documents.generation.docx.generator import DocxGenerator
from pta_documents.markdown import DocumentResource, MarkdownDocument

document = MarkdownDocument(
    markdown_text,
    resources=[
        DocumentResource("images/bild.png", "image/png", png_bytes),
    ],
)
with open("bericht.docx", "wb") as output:
    result = DocxGenerator().generate(document, output)
print(result)  # Hinweise als Markdown-Liste, sonst "No notes."
```

Bilder kommen nur aus `resources`, nie von der Platte. Fehler im Dokument sind immer
`DocumentConversionError` mit `reason` (für den Schreiber) und `format`. Was der Generator
umgehen musste, ohne dass es ein Fehler ist, steht im Rückgabewert (siehe
[Hinweise](#hinweise-generationresult)).

| Front Matter | Werte | Wirkung |
| ------------ | ----- | ------- |
| `vorlage` | `hoch` (Standard), `hoch-ohne-deckblatt`, `quer`, `quer-ohne-deckblatt` | PTA-Word-Vorlage |
| `titel`, `untertitel` | Text | Deckblatt bzw. Kopfzeile; `titel` ist bei Vorlagen mit Deckblatt Pflicht |
| `autor`, `ort`, `datum` | Text; Datum `2026-11-06` oder `06.11.2026` | Zeile „Autor, Ort, Datum" auf dem Deckblatt; `datum` auch in der Fußzeile (sonst heute) |
| `firma` | Text | ersetzt „PTA IT-Beratung" in der Fußzeile |
| `sprache` | `de` (Standard), `en` | erzeugte Texte: Seite/Page, Stand/As of, Tabelle/Table, Abbildung/Figure, Inhalt/Contents |
| `inhaltsverzeichnis` | `ja`, `nein` | Inhaltsverzeichnis nach dem Deckblatt (Word füllt es beim Öffnen) |

Zuordnung: `#`–`###` → „Überschrift 1–3" (nummeriert), tiefere → „Zwischenüberschrift";
Absätze → „Standard"; Listen → „Aufzählungszeichen" bzw. „Listenabsatz"; Tabellen →
Tabellenformat „PTA", ein Absatz `Tabelle: …` direkt danach wird „Tabelle n: …"; ein Bild allein
im Absatz bekommt „Abbildung n: …" aus Titel oder Alt-Text; Codeblöcke → „Code", Zitate →
„Zitat"; Fußnoten werden Word-Fußnoten.

## Markdown → PowerPoint

```python
from pta_documents.generation.pptx.generator import PptxGenerator

with open("praesentation.pptx", "wb") as output:
    result = PptxGenerator().generate(document, output)
result.slides  # Zahl der erzeugten Folien
```

| Front Matter | Werte | Wirkung |
| ------------ | ----- | ------- |
| `vorlage` | `basis` (Standard), `schulung` | PTA-PowerPoint-Vorlage |
| `titelfolie` | `bild-02` (Standard), `bild-01`, `branchen`, `ohne-bild` | Layout der Titelfolie |
| `titel` | Text | Präsentationstitel (Eigenschaften, Fußzeile); sonst das erste `#` |
| `untertitel`, `autor`, `ort`, `datum` | Text | Titelfolie |
| `fusszeile` | Text | Fußzeile „PTA – …" (sonst der Titel) |
| `sprache` | `de`, `en` | `en`: englische Titelfolie mit englischem Logo, „(cont.)" statt „(Forts.)" |

Gliederung: erstes `#` = Titelfolie, weitere `#` = Trennfolie „01", „02" …,
`# Text {.closing}` = Abschlussfolie, `##` = Folie. `## Titel {layout="Name"}` wählt ein
PTA-Layout über seinen Namen; der Inhalt wird an `---` auf dessen Textplatzhalter verteilt.
Absätze sind Textebene 2, `###` Ebene 1, Listen Ebenen 3–5. Eine Tabelle, ein Codeblock oder
eine Bildreihe bekommt eine eigene Folie (Text davor oben, danach unten); ein Bild mit Text
kommt auf `Titel, Text und Bild 01`. Zu viel Inhalt wird bis 12 pt verkleinert und sonst auf
„(Forts.)"-Folien fortgesetzt.

## Folien-Syntax (gemeinsam für Word und PowerPoint)

Beide Generatoren lesen und prüfen dieselbe Folien-Syntax aus DocLibs, bevor sie schreiben
(`generation/common/layout_syntax.check`); ein Fehler ist eine `DocumentConversionError`, deren
`reason` mit der Zeile beginnt (`Line 12: Unknown container '::: card'. Valid containers: …`,
Front Matter mitgezählt).

| Syntax | Gültig | Heute in Word und PowerPoint |
| ------ | ------ | ---------------------------- |
| Heading-Attribute `{…}` am Ende von `#`/`##` | `#`: `.closing`, `layout="…"`; `##`: `.dark`, `kicker="…"`, `layout="…"` | `.closing`/`layout` wirken in PowerPoint (s. o.); `.dark`/`kicker` und in Word alle werden entfernt (gezeichnet ab E04-S03/E03-S03) |
| Container `::: name argumente` … `:::`, verschachtelt mit längeren Zäunen (`::::` außen) | `cards`, `rows`, `panel` (Argument `dark`), `statement`, `columns` (Argument `1:2` oder `1:1:2`) | Zäune entfallen, der Inhalt steht als normale Blöcke da |
| Alerts `> [!NOTE]` (erste Zeile des Zitats) | `NOTE`, `TIP`, `IMPORTANT`, `WARNING`, `CAUTION` | Markierungszeile entfällt, der Rest ist ein Zitat |
| `==Markierung==` | – | Gleichheitszeichen entfallen, Text normal |
| `[Wörter]{.success}` | `.success`, `.warning`, `.danger`, `.info`, `.neutral` | Klammern entfallen, Wörter fett (Farbe ab E03-S03/E04-S03) |
| Front Matter `status.<kategorie>: Text; Text` | dieselben fünf Kategorien, jeder Text nur einmal | geprüft; Status-Labels in Tabellen ab E03-S03/E04-S03 |

Andere geschweifte und eckige Klammern bleiben Text (`## Mengen {a, b}`, `[a] {.success}`,
`` `[a]{.success}` ``, `[a](https://…){.x}`); farbige Wörter gelten nie in Code und nie über
einen Zeilenumbruch. Die Bausteine für die späteren Zeichner: `markdown/parser.py`
(`CONTAINER_OPEN`, `container(token)`, `blockquote_open.meta[ALERT]`, Token `mark_open`),
`generation/common/heading_attributes.py` (`split`, `check_level`, `VALID`),
`layout_syntax.py` (`CONTAINERS`, `ALERTS`, `check_container`, `is_important`, `column_widths`,
`columns`, `coloured`), `coloured_words.py` (`apply` über beliebige Runs) und
`layout_tokens.py` (`tags`, `labelled_tags`, `label_cell`, `marked_row`, `only_images`).

## Code-Block-Renderer und Bildkonverter

Zwei Erweiterungspunkte, über die Diagramme, Charts und fremde Bildformate in die Generatoren
kommen (`DocxOptions` und `PptxOptions`, Felder `code_block_renderers` und `image_converters`):

```python
from pta_documents.generation.common.images import ConvertedImage
from pta_documents.generation.common.renderers import CodeBlockRequest, ImageGraphic
from pta_documents.generation.docx.options import DocxOptions


class Testbild:
    authoring_guide = None  # oder ein Abschnitt ab "##" für die Authoring Guides (E02-S05)

    def render(self, request: CodeBlockRequest) -> ImageGraphic | None:
        if request.info.split()[0] != "testbild":
            return None  # nicht meins: der Nächste wird gefragt, sonst bleibt es Code
        return ImageGraphic(DocumentResource("testbild.png", "image/png", png_bytes))


class SvgNachPng:
    format = "SVG"  # so nennen es die Authoring Guides; None: gar nicht

    def convert(self, image: DocumentResource, scale: float) -> ConvertedImage | None:
        if image.content_type != "image/svg+xml":
            return None
        return ConvertedImage(png_bytes, "image/png", breite_px, hoehe_px)  # natürliche Größe


options = DocxOptions(code_block_renderers=(Testbild(),), image_converters=(SvgNachPng(),))
```

- **Renderer** (`generation/common/renderers.py`, `CodeBlockRenderer`) bekommen jeden
  Codeblock mit Info-String (```` ```mermaid ````, ```` ```chart bar ````) als
  `CodeBlockRequest(info, code, line, format, language, dark)`: `line` ist die Zeile des
  öffnenden Zauns mit Front Matter, `language` die Dokumentsprache (`sprache:`), `dark` in
  PowerPoint, ob die Folie `{.dark}` ist. Der erste Renderer mit Ergebnis gewinnt; `None` heißt
  „nicht meins". Codeblöcke ohne Info-String und eingerückter Code gehen an keinen Renderer.
- Ergebnis `ImageGraphic(resource)`: das Bild steht an der Stelle des Codeblocks wie ein
  Markdown-Bild, mit dem Info-String als Alt-Text — in Word ohne „Abbildung n"-Beschriftung, in
  PowerPoint wie ein Bild allein auf einer Folie. `DrawingGraphic(drawing)` und
  `ChartGraphic(chart, drawing)` (Daten in `pta_documents.charts.ChartSpec`) sind vorgesehen,
  werden aber noch nicht gezeichnet: sie ergeben einen Fehler „… does not support yet"
  (Zeichnen folgt mit E03-S04, E04-S04 und E06).
- **Konverter** (`generation/common/images.py`, `ImageConverter`) bekommen jedes Bild, dessen
  Format der Generator nicht setzt (alles außer PNG, JPEG, GIF, BMP, TIFF, z. B. SVG), mit
  `scale = 2`; der erste mit Ergebnis gewinnt. Word setzt das Ergebnis in der natürlichen Größe
  aus `ConvertedImage` (Pixel bei 96 dpi), PowerPoint wie jedes andere Bild. Nimmt kein Konverter
  das Bild, bleibt es ein Fehler (`… is a image/svg+xml; …, and no image converter takes it`).
- **Fehler:** wirft ein Renderer oder Konverter eine `DocumentConversionError`, geht sie
  unverändert durch; jede andere Ausnahme wird zu `DocumentConversionError` im Format des
  Generators (Konverter: `The image '…' cannot be converted: …`), die ursprüngliche steht in
  `__cause__`.
- **Standard:** ohne Angabe nehmen die Optionen alle Renderer und Konverter der Bibliothek, die
  verfügbar sind (`default_renderers()`, `default_converters()`); `()` schaltet sie ab. Heute
  sind beide Listen leer — Charts, Mermaid (E06-S01/S03) und SVG → PNG (E06-S04, Extra `svg`)
  tragen sich dort ein.

## Hinweise (`GenerationResult`)

`generate()` beider Generatoren gibt ein `GenerationResult` zurück (`pta_documents.GenerationResult`,
Modul `pta_documents.generation.common.result`):

| Feld | Inhalt |
| ---- | ------ |
| `notes` | Tupel von `GenerationNote(code, line, message)`, nach Zeile sortiert, jeder Hinweis einmal; leer, wenn nichts umgangen werden musste |
| `slides` | Zahl der Folien (PowerPoint), sonst `None` |
| `pages` | Zahl der Seiten (PDF, später), sonst `None` — Word zählt Seiten erst beim Öffnen |

`line` ist die Zeile im Markdown, Front Matter mitgezählt (oder `None`); `message` ist ein
englischer Satz, was geschah und was stattdessen zu schreiben ist. `str(note)` ergibt
`line 12: …`, `str(result)` die Markdown-Liste `- line 12: …` bzw. `No notes.` — so kann sie
direkt an den Schreiber (oft eine KI) zurückgehen. Hinweise sind **keine Fehler**: das Dokument
ist geschrieben und brauchbar. Wer Hinweise wie Fehler behandeln will, prüft `result.notes`.

| `code` (`NoteCodes`) | Format | Wann |
| -------------------- | ------ | ---- |
| `slide-split` (`SLIDE_SPLIT`) | PPTX | Text, Tabelle, Code oder Bildreihe passt nicht auf eine Folie und geht auf „(Forts.)"-Folien weiter; Zeile des `##` |
| `slide-overfull` (`SLIDE_OVERFULL`) | PPTX | passt auch bei 12 pt nicht und läuft über den Folienrand (z. B. ein sehr langer Absatz) |
| `image-cropped` (`IMAGE_CROPPED`) | PPTX | ein Bildplatzhalter schneidet mehr als ein Viertel der Bildfläche ab |
| `image-enlarged` (`IMAGE_ENLARGED`) | PPTX, DOCX | ein Bild wird mehr als doppelt so groß gezeigt wie seine Pixel bei 96 dpi und wirkt unscharf |
| `raw-html` (`RAW_HTML`) | PPTX, DOCX | rohes HTML im Markdown; es wird **weggelassen**. HTML-Kommentare `<!-- … -->` fallen ohne Hinweis weg, `<br>` ist ein Zeilenumbruch |
| `code-not-drawn` (`CODE_NOT_DRAWN`) | PPTX, DOCX | ein Codeblock in `mermaid`, `chart` oder `financial-chart` wurde von keinem Renderer gezeichnet und steht als Code da (die Renderer der Bibliothek folgen mit E06) |
| `character-missing` (`CHARACTER_MISSING`) | PDF (E05-S04) | ein Zeichen fehlt in den Schriften |
| `notes-dropped` (`NOTES_DROPPED`) | DOCX (E09-S01) | Sprechernotizen fallen im Word-Dokument weg |

Die Codes sind stabil; neue kommen mit neuen Funktionen dazu. `./run.sh generate` zeigt die
Hinweise unter jeder Datei und endet mit `--strict` auch bei Hinweisen mit Code 1;
`./run.sh generate-samples` endet mit Code 1, sobald ein Beispiel Hinweise hat.

## Word/PowerPoint → Markdown

```python
from pta_documents.conversions.docx import DocxConverter
from pta_documents.conversions.pptx import PptxConverter

document = DocxConverter().convert(open("datei.docx", "rb"))
print(document.text)  # Markdown
for image in document.resources:
    ...  # images/image1.png usw.
```

`ConversionOptions(resource_path_prefix="images/", include_images=True)` steuert die Bilder.

## Beispiele

`samples/` enthält Beispielinhalte, z. B. `samples/gsb/` (Hauptbeskidenweg, mit CC-Fotos).
`./run.sh generate-samples [name]` erzeugt daraus DOCX (`*-bericht.md`) und PPTX
(`*-praesentation.md`) nach `.tmp/samples/<name>/`. Für beliebige Ordner und Dateien gibt es
`./run.sh generate <pfad> [--docx|--pptx] [--out <ordner>] [--strict]` (siehe [anleitung.md](anleitung.md)).
Die Beispiele erzeugen ohne Hinweise.
