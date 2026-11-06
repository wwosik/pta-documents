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
    DocxGenerator().generate(document, output)
```

Bilder kommen nur aus `resources`, nie von der Platte. Fehler im Dokument sind immer
`DocumentConversionError` mit `reason` (für den Schreiber) und `format`.

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
    PptxGenerator().generate(document, output)
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
(`*-praesentation.md`) nach `.tmp/samples/<name>/`.
