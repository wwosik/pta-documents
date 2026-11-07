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
„Zitat"; Fußnoten werden Word-Fußnoten. Folien-Syntax: siehe *Folien-Syntax in Word* unten.

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

### Flow-Folien (E04-S03)

Eine `##`-Folie mit `:::`-Container, Alert, einem Absatz nur aus Code-Spans (Tags), `{.dark}`
oder `kicker="…"` wird eine Flow-Folie (`generation/pptx/flow_parser.py` liest, `flow.py`
zeichnet, Werte in `design/slides.py`: `FLOW`, `CONCLUSION`, `COMMENT`, `grid`). Sie steht auf
`Nur Titel`; die Blöcke stapeln sich in der Inhaltsfläche (1,33/4,62 cm, 31,20 × 13,10 cm), mit
0,40 cm Abstand:

| Block | Gestaltung |
| ----- | ---------- |
| Text | 18 pt Segoe UI Light `404040`, Ebenen wie im Textplatzhalter; in Karten 14 pt |
| `cards` | Rechtecke ohne Fläche, Rand `E6E6E6` 0,75 pt; bis vier je Zeile im Raster (2 × 15,10, 3 × 9,73, 4 × 7,00 cm an den Hilfslinien des Masters); Kennzahl 32 pt fett, Titel 18 pt Segoe UI, beide PTA-Blau |
| `rows` | Begriff (18 pt Segoe UI PTA-Blau) im linken Drittel, Linien `E6E6E6` 0,5 pt über jeder Zeile, `404040` unter der letzten |
| `panel` / `panel dark` | Fläche `E6E6E6` / `004676` mit weißer Schrift |
| `statement` | erster Absatz 24 pt fett PTA-Blau |
| `columns` | Spalten 1,00 cm auseinander; über die ganze Breite an den Hilfslinien (gleich breite genau, andere bis 1,5 cm daneben eingerastet); **genau zwei gleiche Spalten nur mit Text** → Layout `Titel und Text (zweispaltig)`, wenn der Text dort passt |
| Alerts | Fläche `E6E6E6`, Balken links 0,15 cm PTA-Blau (`NOTE`, `TIP`) bzw. Gelb `FDDC35`, Text nicht kursiv |
| Tags | Rahmen PTA-Blau 0,75 pt, Consolas 12 pt; beschriftete Tags (Liste `` - `x` Text `` in einem Container): Chip fett, Text daneben |
| Code | Fläche `E6E6E6`, Consolas 14 pt, Zeilenabstand 130 % |
| Tabellen, Bilder | wie auf Visual-Folien; Bilder teilen sich die übrige Höhe (mindestens 4,76 cm) |
| `conclusion` | PTA-Fazit-Box (Vorlagensammlung Folie 43): 1,33/15,78 cm, 31,20 × 1,94 cm, `004676`, 18 pt fett weiß, Einzug links 1,90 cm; höchstens zwei Zeilen (verkleinert bis 14 pt, sonst Fehler), einmal je Folie, nur direkt auf der Folie; die Blöcke stapeln darüber |
| `comment` | PTA-Kommentarbox (Folie 32): `wedgeRectCallout`, weiß, Verlaufsrand `9FD8FF` → `006FB9` 1,5 pt, 14 pt fett PTA-Blau, Ränder 0,30/0,20 cm; rechtsbündig oben auf dem Block davor, höchstens halb so breit wie ihr Platz, Spitze nach links unten auf den Block; nimmt keine Höhe ein |

- `kicker="…"`: 12 pt fett Versalien `004676` bei 1,33/1,60 cm über dem Titel.
- `{.dark}`: `Nur Titel` mit dem Hintergrund von `Titelfolie ohne Bild`; Titel, Text, Kicker,
  Fußzeile weiß; helle Flächen (Panel, Alert, Code) behalten ihre dunkle Schrift.
- Auf **allen** Folien: `==…==` fett mit Hervorhebung `FDDC35`; eine Tabellenzeile, deren erste
  Zelle ganz markiert ist, hat die Fläche `FDDC35`; `[Wörter]{.x}` fett in `STATUS_COLORS`. Auf
  Flow-Folien ist eine Tabellenzelle aus genau einem Code-Span ein Status-Label: „●" in der
  Farbe seiner Kategorie (`status.<kategorie>` im Front Matter, sonst `AFAFAF`), Text `404040`.
- Fitting (Port von `FitFlow`): alle Größen bis zu zweimal um ein Achtel kleiner (Abstände dann
  halb), nie unter 12 pt; sonst Teilung zwischen Blöcken, Absatzgruppen, Tabellenzeilen (Kopf
  wiederholt), Zeilen von `rows` und beschrifteten Tags. Karten, Panels, Alerts, Spalten werden
  nie geteilt, eine Kommentarbox bleibt bei ihrem Block; Folgefolien „(Forts.)" behalten den
  Kicker, die Fazit-Box steht nur auf der letzten. Hinweise `slide-split`/`slide-overfull`.
- Mit Flow-Inhalt ist nur `layout="Nur Titel"` erlaubt. Aufbaufehler melden die Zeile
  (`Line 4: In '::: cards', each card starts with a ### heading, …`; Karten ohne Titel,
  `rows` ohne Liste, `- ` ohne fetten Titel, `statement` ohne Absatz, Spalten ≠ zwei/drei,
  zwei Fazit-Boxen, Fazit-Box in einem Container, Kommentarbox ohne Block davor).

### PTA-Folienarten und Diagramm-Layouts (E04-S04)

Ein Heading-Attribut am `##` wählt eine PTA-Folienart (`generation/pptx/kind_parser.py` liest,
`kinds.py` schreibt; Layoutnamen und Platzhalter in `design/slides.py`: `LAYOUTS`,
`PLACEHOLDERS`, `KIND_LAYOUTS`). Höchstens eine je Folie, nicht mit `.dark`, `kicker` oder
Flow-Inhalt; `layout="…"` darf nur ein Layout derselben Art wählen.

| Schreiben | Layout | Belegung |
| --------- | ------ | -------- |
| `## Agenda {.agenda}` mit genau einer Liste (je Punkt eine Zeile) | ≤ 4 Punkte `Agenda (kurz)`, 5–8 `Agenda (lang)`, mehr = Fehler | Nummern „01" … (idx 14, 16 …), Texte (15, 17 …); ungenutzte Paare und die Linien unter dem letzten Punkt entfallen |
| `## Agenda {.agenda}` ohne Inhalt | wie oben | die Kapitel des Decks: alle `#` nach dem ersten, ohne `{.closing}` |
| `## Aussage {.interim}` (kein Inhalt) | `Zwischenfazit 01` (`02` über `layout`) | Überschrift im Titel |
| `## Zitat {.quote}`, optional ein Absatz darunter | `Zitat 01` (`02`) | Überschrift im Titel; der Absatz ist die Quelle: zweiter Absatz im Titel, 24 pt Segoe UI Light, nicht kursiv |
| `## Kontakt {.contact}`, je Person `###` Name, darunter ein Absatz: Foto (optional), Zeilen Funktion, E-Mail (mit `@`, wird `mailto:`-Link), Telefon (beginnt mit `+` oder Ziffer) in beliebiger Reihenfolge | n Personen (1–5) `Kontakt 0n`; eine Person mit weiterem Text (Absätze, Listen nach dem Kontaktabsatz) `Kontakt mit Text` | je Person Bild/Name/Funktion/E-Mail/Telefon (34/14/35/36/38, 39/40–43 …), Text 37; was fehlt (auch das Foto), entfällt |

Ohne `{.agenda}` entsteht nie eine Agendafolie. Fehler melden die Zeile (`Line 3: An agenda
holds 8 items at most, this one 9. Split it into two agenda slides.`; Inhalt unter
`{.interim}`, mehr als ein Absatz unter `{.quote}`, sechs Personen, zwei E-Mail-Zeilen, Text
bei mehreren Personen, ein fremdes Layout).

**Charts:** Liefert ein Code-Block-Renderer für einen Fence einen `ChartGraphic`, setzt
PowerPoint ein natives Diagramm (`generation/pptx/chart.py`, python-pptx `insert_chart`, Reihen
in `ChartSpec.colors`) in den Diagrammplatzhalter: ein Chart allein → `Titel und Diagramm`, mit
Text davor → `Titel, Text und Diagramm`, Text danach → `Titel, Diagramm und Text`, zwei Charts
ohne anderes (auch als einzige Teile eines `::: columns`) → `Titel und zwei Diagramme`.
`ChartSpec.title`/`unit`/`source` stehen in den Platzhaltern Diagrammtitel/Werteinheit/
Quellenangabe (leere entfallen), der Titel nicht zusätzlich im Diagramm. Ein Chart neben einer
Tabelle oder einem Bild bekommt eine eigene Folie; auf einer Flow-Folie ist er ein Fehler. Mit
`layout="…"` geht ein Chart in den nächsten Diagrammplatzhalter des Layouts. Den
`chart`-Renderer und den PTA-Diagrammstil liefert E06-S01; Word wirft für Charts bis dahin
„does not support yet", Zeichnungen (`DrawingGraphic`) in beiden Formaten bis E02-S03/E06.

### Sprechernotizen (E09-S01)

Ein Container `::: notes` … `:::` (ohne Argumente, auch in anderen Containern) gehört zur
Überschrift (`#` oder `##`), unter der er steht. `DeckParser` nimmt alle `::: notes` vor dem
Lesen aus den Token (`_take_notes`), so dass sie keine Folie zur Flow-Folie machen und unter
Titel-, Trenn- und Abschlussfolie erlaubt sind; mehrere Blöcke einer Überschrift werden
zusammengefügt (`Slide.notes`). Jede Folie, die für die Überschrift entsteht, bekommt sie —
auch jede „(Forts.)"-Folie und die Folgefolien eines zweiten Visuals (Entscheidung
2026-11-07). `generation/pptx/notes.py` (`write_notes`, aus `DeckWriter.new_slide`) legt mit
python-pptx die Notizenfolie auf dem Notizenmaster der PTA-Vorlage an und schreibt die Absätze
in dessen Platzhalter `body`: Text auf Ebene 0, Listenpunkte auf Ebene 1–3 (die Aufzählungszeichen
des Masters), nummerierte mit `buAutoNum`; fett, kursiv, Code (Consolas) und Links bleiben.
Tabellen, Bilder, Codeblöcke und Linien in Notizen entfallen ohne Fehler. Ein Deck ohne
`::: notes` hat keine `ppt/notesSlides/`. Ein `::: notes` vor dem ersten `#`/`##` ist ein Fehler
von `layout_syntax.check` (`Line 3: A '::: notes' belongs under a heading: …`). Word lässt
Notizen weg und meldet `notes-dropped`.

## Folien-Syntax (gemeinsam für Word und PowerPoint)

Beide Generatoren lesen und prüfen dieselbe Folien-Syntax aus DocLibs, bevor sie schreiben
(`generation/common/layout_syntax.check`); ein Fehler ist eine `DocumentConversionError`, deren
`reason` mit der Zeile beginnt (`Line 12: Unknown container '::: card'. Valid containers: …`,
Front Matter mitgezählt).

| Syntax | Gültig | Heute in Word und PowerPoint |
| ------ | ------ | ---------------------------- |
| Heading-Attribute `{…}` am Ende von `#`/`##` | `#`: `.closing`, `layout="…"`; `##`: `.dark`, `kicker="…"`, `layout="…"`, PTA: `.agenda`, `.interim`, `.quote`, `.contact` (eine davon, nicht mit `.dark`/`kicker`) | PowerPoint: alle wirken (s. o., Flow-Folien, PTA-Folienarten); Word: entfernt, die Folienarten schlicht (s. u.) |
| Container `::: name argumente` … `:::`, verschachtelt mit längeren Zäunen (`::::` außen) | `cards`, `rows`, `panel` (Argument `dark`), `statement`, `columns` (Argument `1:2` oder `1:1:2`), PTA: `conclusion`, `comment`; `notes` (Sprechernotizen) | PowerPoint: Flow-Folien, `notes` auf die Notizenseite; Word: Inhalt nacheinander, Fazit/Kommentar als „Hinweis", `notes` entfällt |
| Alerts `> [!NOTE]` (erste Zeile des Zitats) | `NOTE`, `TIP`, `IMPORTANT`, `WARNING`, `CAUTION` | PowerPoint: Fläche mit Balken; Word: „Hinweis" bzw. „Hinweis wichtig" mit fetter Art am Anfang |
| `==Markierung==` | – | PowerPoint: fett auf `FDDC35`; Word: Zeichenvorlage „Markierung" |
| `[Wörter]{.success}` | `.success`, `.warning`, `.danger`, `.info`, `.neutral` | Klammern entfallen; PowerPoint fett in der Signalfarbe, Word Zeichenvorlage „Status …" |
| Front Matter `status.<kategorie>: Text; Text` | dieselben fünf Kategorien, jeder Text nur einmal | geprüft; PowerPoint: Status-Labels in Tabellen auf Flow-Folien; Word: Label-Zellen in der Zeichenvorlage „Status …" |

Andere geschweifte und eckige Klammern bleiben Text (`## Mengen {a, b}`, `[a] {.success}`,
`` `[a]{.success}` ``, `[a](https://…){.x}`); farbige Wörter gelten nie in Code und nie über
einen Zeilenumbruch. Die Bausteine für die späteren Zeichner: `markdown/parser.py`
(`CONTAINER_OPEN`, `container(token)`, `blockquote_open.meta[ALERT]`, Token `mark_open`),
`generation/common/heading_attributes.py` (`split`, `check_level`, `VALID`),
`layout_syntax.py` (`CONTAINERS`, `ALERTS`, `check_container`, `is_important`, `column_widths`,
`columns`, `coloured`), `coloured_words.py` (`apply` über beliebige Runs) und
`layout_tokens.py` (`tags`, `labelled_tags`, `label_cell`, `marked_row`, `only_images`).

### Folien-Syntax in Word

Word zeigt die Folien-Syntax schlicht, über eigene Formatvorlagen statt Direktformatierung
(E03-S03; die Vorlagen legt der Generator bei Bedarf an):

| Syntax | In Word |
| ------ | ------- |
| Heading-Attribute (`kicker`, `.dark`, `layout`, `.closing`) | entfallen, `#` bleibt „Überschrift 1" |
| `::: cards`, `rows`, `panel`, `statement`, `columns` | Inhalt als normale Blöcke nacheinander; eine Überschrift in einem Container (`### Karte`) und eine Kennzahl `**26 Tabellen**` werden „Standard fett" (keine Nummer, kein Verzeichniseintrag); der erste Absatz von `statement` wird „Standard fett"; die `---` zwischen Spalten entfallen |
| `::: conclusion`, `::: comment` | „Hinweis", erster Absatz beginnt mit **Fazit:** bzw. **Kommentar:** |
| `> [!NOTE]`, `[!TIP]` | „Hinweis" (Linie 3 pt PTA-Blau links, graue Fläche), beginnt mit **Hinweis:** bzw. **Tipp:** |
| `> [!IMPORTANT]`, `[!WARNING]`, `[!CAUTION]` | „Hinweis wichtig" (Linie Gelb `FDDC35`), beginnt mit **Wichtig:**, **Warnung:**, **Vorsicht:** (`sprache: en`: Note, Tip, Important, Warning, Caution, Conclusion, Comment) |
| `==Markierung==` | Zeichenvorlage „Markierung" (Schattierung `FDDC35`); erste Tabellenzelle ganz markiert = alle Zellen der Zeile schattiert |
| `[Wörter]{.success}` … | Zeichenvorlagen „Status Erfolg", „Status Warnung", „Status Gefahr", „Status Info", „Status Neutral" (fett in der Statusfarbe) |
| Tabellenzelle nur `` `Erledigt` `` mit `status.success: Erledigt` | Zeichenvorlage der Kategorie (ohne Consolas); nicht zugeordnete Code-Zellen und Tags bleiben Code |
| Absatz aus ≥ 2 Bildern | rahmenlose Tabelle „Bildreihe" über die Satzspiegelbreite, gleich breite Zellen, höchstens vier je Zeile, unter jedem Bild „Abbildung n: …"; Zeilen werden nicht getrennt |
| `{.agenda}` | „Überschrift 2" mit der Liste; ohne Liste die folgenden `#`-Kapitel (ohne `{.closing}`) als nummerierte Liste |
| `{.interim}` | die Aussage als „Standard fett" |
| `{.quote}` | Zitat und Quelle als „Zitat" |
| `{.contact}` | „Überschrift 2", je Person `###` als „Standard fett", Foto höchstens 3 cm breit ohne Beschriftung, jede Zeile für sich |

Die Aufbauregeln der Folien (z. B. höchstens acht Agendapunkte, Fazit-Box höchstens zwei Zeilen)
prüft nur PowerPoint; Word meldet die Fehler von `layout_syntax.check` wie PowerPoint. Der
DOCX-Konverter liest die neuen Vorlagen wie „Standard"; „Hinweis …" wird wieder ein Zitat (ein
Alert mit seiner Art, `> [!NOTE]`), eine Bildreihe wieder ein Absatz aus Bildern mit den
Beschriftungen danach.

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
Der PPTX-Konverter gibt die Notizenseite einer Folie (Platzhalter `body` der `notesSlide`)
nach deren Inhalt als `::: notes` … `:::` aus, Listenebenen als `-`-Listen; leere Notizen und
Notizen nur aus dem Aufforderungstext des Notizenmasters entfallen. `ConversionOptions(notes=False)`
lässt sie weg.

## Beispiele

`samples/` enthält Beispielinhalte, z. B. `samples/gsb/` (Hauptbeskidenweg, mit CC-Fotos).
`./run.sh generate-samples [name]` erzeugt daraus DOCX (`*-bericht.md`) und PPTX
(`*-praesentation.md`) nach `.tmp/samples/<name>/`. Für beliebige Ordner und Dateien gibt es
`./run.sh generate <pfad> [--docx|--pptx] [--out <ordner>] [--strict]` (siehe [anleitung.md](anleitung.md)).
Die Beispiele erzeugen ohne Hinweise.
