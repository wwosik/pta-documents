# Verwendung

Stand nach Meilenstein M01: Markdown → Word und PowerPoint auf den PTA-Vorlagen, Word und
PowerPoint → Markdown; seit E06-S01 native Diagramme aus `chart`-Blöcken in beiden Formaten,
seit E06-S02 Finanzdiagramme (`financial-chart`) als Formengruppe in PowerPoint und als SVG,
seit E06-S03 Mermaid-Diagramme (`mermaid`, über mermaid-cli) als Formengruppe in PowerPoint,
seit E03-S04 beide auch in Word als Abbildung (SVG mit PNG-Ersatz). Seit E05-S01/E05-S02 der
PDF-Generator (PDF/A-2b im Design der Word-Vorlage, siehe
[Markdown → PDF](#markdown--pdf-e05-s01-e05-s02)), seit E05-S03 mit Deckblatt,
Inhaltsverzeichnis, Kopf- und Fußzeile ([PTA-Seitenrahmen](#pta-seitenrahmen-im-pdf-e05-s03)),
seit E05-S04 mit allen Grafiken als Vektoren und Ersatz fehlender Zeichen
([Grafiken und fehlende Zeichen](#grafiken-und-fehlende-zeichen-im-pdf-e05-s04)).

## Einrichten

```sh
./run.sh setup      # .venv anlegen, Paket editierbar mit allen Extras installieren,
                    # mit Node.js auch mermaid-cli (tools/mermaid, npm ci),
                    # Playwright (Extra preview) und, falls keins startet, sein Chromium
./run.sh test       # Tests
./run.sh mermaid    # prüfen, ob Mermaid-Blöcke hier gezeichnet werden
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
| `kennzeichnung` | `vertraulich`, `intern`, `entwurf`, `kein` (Standard) | Text unter dem Logo jeder Seite und auf dem Deckblatt, bei `entwurf` zusätzlich Wasserzeichen, siehe [Kennzeichnung in Word und PDF](#kennzeichnung-in-word-und-pdf-e12-s03) |
| `fassung` | `kunde` (Standard), `intern`, `trainer` | welche Fassung entsteht; `DocxOptions.audience` geht vor, siehe [Zielgruppenfassungen](#zielgruppenfassungen-e16-s01) |
| `typografie` | `ja` (Standard), `nein` | deutsche (bzw. englische) Typografie, siehe [Typografie und Code](#typografie-und-code-e17-s02) |
| `syntaxhervorhebung` | `ja` (Standard), `nein` | Codeblöcke mit Sprache farbig |
| `pruefung` | `aus`, `an` (Standard) oder Liste von Codes | nur für `./run.sh check`: Stilregeln abschalten, siehe [Prüfen ohne Erzeugen](#prüfen-ohne-erzeugen-check) |

Zuordnung: `#`–`###` → „Überschrift 1–3" (nummeriert), tiefere → „Zwischenüberschrift";
Absätze → „Standard"; Listen → „Aufzählungszeichen" bzw. „Listenabsatz"; Tabellen →
Tabellenformat „PTA", ein Absatz `Tabelle: …` direkt danach wird „Tabelle n: …"; ein Bild allein
im Absatz bekommt „Abbildung n: …" aus Titel oder Alt-Text (`![…](qr:…)` ist ein QR-Code, siehe
[QR-Codes](#qr-codes-e11-s04)); Codeblöcke → „Code", Zitate →
„Zitat"; Fußnoten werden Word-Fußnoten; Diagramme und Charts aus Codeblöcken siehe
[Grafiken in Word](#grafiken-in-word-e03-s04). Folien-Syntax: siehe *Folien-Syntax in Word* unten.

### Kennzeichnung in Word und PDF (E12-S03)

`kennzeichnung:` (`DocxOptions.marking`, `PdfOptions.marking`, derselbe
`design.variants.Marking` wie der Folien-Sticker) kennzeichnet ein Dokument; Standard ist `kein`.

| Wert | Text (`sprache: de` / `en`) | Wasserzeichen |
| ---- | --------------------------- | ------------- |
| `vertraulich` | VERTRAULICH / CONFIDENTIAL | – |
| `intern` | FÜR DEN INTERNEN GEBRAUCH / FOR INTERNAL USE ONLY | – |
| `entwurf` | ENTWURF / DRAFT | ENTWURF / DRAFT |
| `kein` | – | – |

- **Kopfzeile:** der Text in 9 pt Versalien, PTA-Blau über die Theme-Farbe `accent1`,
  rechtsbündig auf dem Satzspiegel, 3 pt unter der Verlaufslinie der Kopfzeile, also unter dem
  Logo (`word_frame.marking_area`: Hoch 2,91 cm, Quer 3,51 cm von oben, eine Zeile
  „Kopfzeile", endet über dem Satzspiegel) — auf jeder Seite, das Deckblatt eingeschlossen (auf
  dem Deckblatt von `quer` liegt die Linie tiefer, die Kennzeichnung bleibt unter dem Logo).
  Word: ein Textfeld ohne Ränder und ohne Textumbruch (`wp:anchor`, `wrapNone`, Name
  `PTA-Kennzeichnung`) im Absatz der Vorlage, der Logo und Linie trägt — die Kopfzeile behält
  ihre Höhe, der Text rückt nicht. Maße in `design.word.MARKING`.
- **Deckblatt:** derselbe Text in „Autor" (14 pt), PTA-Blau, unter „Autor, Ort, Datum". Der
  DOCX-Konverter liest ihn als Absatz zurück (er steht im Rumpf); die Kopfzeilen liest er nicht.
- **Wasserzeichen** (`entwurf`): in Word ein WordArt-Shape, wie Word es unter *Entwurf →
  Wasserzeichen* schreibt (VML `v:shape` mit `v:textpath`, Id `PowerPlusWaterMarkObject…`,
  `design.word.WATERMARK_SHAPE`), in jeder Kopfzeile, Segoe UI, Akzent 5 (`AFAFAF`) mit 50 %
  Deckkraft, um 45° gedreht über der Mitte des Satzspiegels, so groß, wie dessen kürzere Seite
  es zulässt (`design.word.watermark_size`). Word zeigt es hinter dem Text jeder Seite und
  entfernt es über *Wasserzeichen entfernen*. Im PDF dieselbe Lage und Größe (mit den echten
  Schriftmaßen) als gedrehter Text, **vor** dem Inhalt gezeichnet (`render(…, underlay=…)`) und
  ohne Transparenz: die Farbe ist Akzent 5 zu 50 % mit dem weißen Papier gemischt, was hinter
  dem Inhalt gleich aussieht und PDF/A ohne Soft-Mask lässt.
- **`kein`** ändert nichts: die Kopfzeilenteile sind byte-gleich zu einem Dokument ohne den
  Schlüssel.

## Markdown → PDF (E05-S01, E05-S02)

Braucht das Extra `pdf` (reportlab, pikepdf; `./run.sh setup` installiert es). Ohne Extra
schlägt schon der Import fehl, mit einem `ImportError`, der `pip install -e '.[pdf]'` nennt.

```python
import datetime as dt

from pta_documents.generation.pdf import PdfGenerator, PdfOptions

with open("bericht.pdf", "wb") as output:
    result = PdfGenerator().generate(document, output, PdfOptions(created=dt.datetime(2026, 11, 8)))
print(result.pages, result)
```

```sh
./run.sh generate bericht.md --pdf     # schreibt bericht.pdf daneben
./run.sh check bericht.md --pdf        # Probelauf, zählt die Seiten
```

- **Stand:** Das Ergebnis ist ein PDF/A-2b mit eingebetteten Schriften und Metadaten. Den Rumpf
  setzt die [Layout-Engine](#pdf-layout-engine-e05-s02) in den Formatvorlagen und auf dem
  Satzspiegel der gewählten Word-Vorlage (Nummerierung, Listen, Tabellen, Bilder, QR-Codes, Code
  mit Hervorhebung, Hinweis-Boxen, Fußnoten, Lesezeichen, Links, Seitenumbruchregeln), im
  [PTA-Seitenrahmen](#pta-seitenrahmen-im-pdf-e05-s03) mit Deckblatt, Inhaltsverzeichnis, Kopf-
  und Fußzeile (seit E05-S03). Seit E05-S04 zeichnet es jede Grafik:
  [Zeichnungen und Charts als Vektoren](#grafiken-und-fehlende-zeichen-im-pdf-e05-s04)
  (`chart`, `financial-chart`, Mermaid, `::: timeline`, `::: steps`, `::: riskmatrix` mit der
  Legende als Tabelle), `::: gantt` als Tabelle wie Word, Icons als kleine Bilder, SVG-Bilder
  über die Bildkonverter; Harvey Balls (`[3/4]` in Tabellen) als kleine Grafik in der Zelle.
- **Front Matter:** dieselben Schlüssel wie Word: `vorlage` (Hoch- oder Querformat; Vorlagen mit
  Deckblatt brauchen wie in Word einen `titel`), `titel`, `untertitel`, `autor`, `ort`, `datum`
  (auch „heute" in Zeitstrahl und Gantt), `firma`, `sprache`, `typografie`,
  `syntaxhervorhebung`, `inhaltsverzeichnis`, `pruefung`, `status.<kategorie>`. Titel und Autor
  fallen auf `document.metadata` zurück. `firma` ersetzt „PTA IT-Beratung" in der Fußzeile,
  `inhaltsverzeichnis: ja` setzt ein Verzeichnis mit Seitenzahlen nach dem Deckblatt.
  Präsentationen (`fusszeile` u. a.) gibt es nicht als PDF.
- **`PdfOptions`:** `variant`, `language`, `typography`, `highlight`, `date`, `company`, `toc`
  wie `DocxOptions`; `created` (Zeitstempel der Metadaten, sonst jetzt in UTC — gleiche Eingabe
  und gleiches `created` ergeben byte-gleiche Dateien); `system_fonts` (Standard `True`: Segoe UI
  und Consolas aus dem System, wenn vollständig installiert, sonst Selawik und Inconsolata, siehe
  [Schriften](#schriften-für-pdf-und-svg-e01-s03)); `code_block_renderers`, `image_converters`
  wie in Word (Bilder, die nicht PNG, JPEG, GIF, BMP, TIFF oder WebP sind, z. B. SVG, gehen über
  die Bildkonverter, im PDF in dreifacher Größe); `replace_unsupported` (Ersatz fehlender
  Zeichen, siehe unten).
- **Fehlende Zeichen:** Selawik hat weder Griechisch noch Kyrillisch, keine der Schriften hat
  Emoji. Ein Zeichen, das der Schrift fehlt (Text: Regular und Bold, Code: die Codeschrift),
  geht als **Graphem-Cluster** (`👍🏽`, `❤️`, `👨‍👩‍👧` je eines; `generation/common/graphemes.py`)
  an `PdfOptions.replace_unsupported` — einmal je Cluster und Dokument; was die Funktion
  zurückgibt, steht an seiner Stelle und muss selbst in der Schrift stehen, sonst
  `DocumentConversionError`. Standard ist `question_mark` (`?`, mit dem Hinweis
  `character-missing` an der ersten Zeile); `replace_unsupported=None` macht jedes solche Zeichen
  zum Fehler mit Zeichen, Codepunkt und Schrift: `The character 'Δ' (U+0394) is not in the font
  (Selawik). …` (außerhalb der BMP ein Codepunkt: `U+1F600`). Das gilt für Text, Überschriften
  (Lesezeichen und Inhaltsverzeichnis zeigen den Ersatz, der Anker bleibt), Tabellen, Code,
  Deckblatt, Kopf- und Fußzeile, Kennzeichnung und die Beschriftungen von Zeichnungen;
  Leerraum wird ein Leerzeichen, unsichtbare Format- und Steuerzeichen (U+200B …) entfallen,
  Variationsselektoren und ZWJ an sonst vorhandenen Zeichen auch. PDF/A erlaubt kein
  `.notdef`. U+00A0, U+202F und U+2011 leihen sich die Glyphe von Leerzeichen bzw. Bindestrich
  und zählen nicht als fehlend. Die Metadaten (Titel, Autor) bleiben unverändert Unicode.

  ```python
  PdfOptions(replace_unsupported=lambda cluster: {"✓": "ja", "👍": "(+)"}.get(cluster, "?"))
  ```
- **PDF/A-2b:** XMP mit `pdfaid:part` 2 / `conformance` B, Titel, Autor, Sprache, Producer
  „PTA Documents" und Zeitstempel gleich im Info-Dictionary; OutputIntent `GTS_PDFA1` mit
  sRGB-Profil (aus Pillow); `/F 4` auf jeder Annotation; `/Lang` (`de-DE`/`en`); PDF 1.7;
  `/ID` aus dem Inhalt; unverschlüsselt. Geprüft wird der Aufbau mit pikepdf; veraPDF
  (`verapdf --flavour 2b`) prüft ein Test nur, wenn `verapdf` im `PATH` liegt.
- **Aufbau** (`generation/pdf/`): `generator.py` (Front Matter, Parser, `layout_syntax.check`,
  QR-Codes, Typografie, Schriften, dann `frame.lay_out` und `pdfa.to_pdfa`), `frame.py`
  (Seitenrahmen, E05-S03), `options.py`
  (`PdfOptions`), `layout/` (die Layout-Engine, siehe unten), `pdfa.py` (`to_pdfa(data, info)`,
  pikepdf), `metadata.py` (`PdfInfo`: Titel, Autor, Betreff, Sprache, Zeitstempel — dieselbe
  Klasse für reportlab und den PDF/A-Schritt).
- **Lizenzen:** reportlab BSD, pikepdf MPL-2.0 (nur als Bibliothek genutzt, nicht verändert),
  pdfplumber MIT (nur Tests und PDF-Konverter).

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
| `sprache` | `de`, `en` | `en`: englisches Logo auf der Titelfolie (in `basis` und `schulung`), „(cont.)" statt „(Forts.)" |
| `kennzeichnung` | `vertraulich`, `intern`, `entwurf`, `kein` | Sticker oben rechts auf dem Master, siehe [Kennzeichnung](#kennzeichnung-e04-s05); in Word und PDF siehe [dort](#kennzeichnung-in-word-und-pdf-e12-s03) |
| `fassung` | `kunde` (Standard), `intern`, `trainer` | welche Fassung entsteht; `PptxOptions.audience` geht vor, siehe [Zielgruppenfassungen](#zielgruppenfassungen-e16-s01) |
| `typografie`, `syntaxhervorhebung` | `ja` (Standard), `nein` | wie in Word, siehe [Typografie und Code](#typografie-und-code-e17-s02) |
| `pruefung` | `aus`, `an` (Standard) oder Liste von Codes | wie in Word |
| `aufbau` | `listen`, `nein` (Standard) | `listen`: jede äußere Liste Punkt für Punkt, siehe [Builds](#builds-e09-s02) |
| `uebergang` | `none` (Standard), `fade`, `push`, `wipe` (mit `-left`/`-right`/`-up`/`-down`), `split`, `cover`, `uncover`, `zoom`, `cut`, `morph` | Übergang jeder Folie, siehe [Folienübergänge](#folienübergänge-e09-s03) |
| `beginn` | Uhrzeit `09:00` | Beginn der Schulung: Agenda und Zeitplan mit Uhrzeiten, siehe [Schulungs-Zeitplan](#schulungs-zeitplan-e16-s02) |
| `laenge` | Minuten `240` oder `4h`, `3h30` | geplante Gesamtlänge; der Zeitplan wird damit verglichen (Hinweis `schedule-length`) |

Gliederung: erstes `#` = Titelfolie, weitere `#` = Trennfolie „01", „02" …,
`# Text {.closing}` = Abschlussfolie, `##` = Folie; `# Backup {.backup}` beginnt die
Backup-Folien hinter der Abschlussfolie (siehe [Backup-Folien und Anhang](#backup-folien-und-anhang-e16-s04)). `## Titel {layout="Name"}` wählt ein
PTA-Layout über seinen Namen; der Inhalt wird an `---` auf dessen Textplatzhalter verteilt.
Absätze sind Textebene 2, `###` Ebene 1, Listen Ebenen 3–5. Eine Tabelle, ein Codeblock oder
eine Bildreihe bekommt eine eigene Folie (Text davor oben, danach unten); ein Bild mit Text
kommt auf `Titel, Text und Bild 01`. Zu viel Inhalt wird bis 12 pt verkleinert und sonst auf
„(Forts.)"-Folien fortgesetzt.

### Kennzeichnung (E04-S05)

`kennzeichnung:` (`PptxOptions.marking`, `design.variants.Marking`) setzt einen Sticker nach dem
Muster der Schulungsvorlage oben rechts vor die Eckklammer — **auf den Master** des erzeugten
Decks (`generation/pptx/sticker.py`), also auf jede Folie, deren Layout die Mastergrafiken zeigt;
auf Layouts ohne Mastergrafiken (`Titelfolie ohne Bild` der Schulungsvorlage, `Titel und Bild 02`,
`Zwischenfazit 01/02`, `Zitat 01/02` u. a.) fehlt er wie in der Vorlage. Auf den Titelfolien mit
Bild liegt das Foto des Layouts über ihm.

| Wert | Text (`sprache: de` / `en`) |
| ---- | --------------------------- |
| `vertraulich` | VERTRAULICH / CONFIDENTIAL |
| `intern` | Für den internen Gebrauch / For internal use only |
| `entwurf` | ENTWURF / DRAFT |
| `kein` | kein Sticker |

Ohne Angabe: `basis` → `kein`, `schulung` → `intern` (wie die Vorlage). Die Schulungsvorlage
behält ihre Form „Rectangle 7", nur der Text wird ersetzt; `schulung` + `kein` ist ein Fehler
(PTA-Regel: Schulungsfolien sind als „nur für den internen Gebrauch" gekennzeichnet). Im
Basis-Master entsteht dieselbe Form neu (`design.slides.STICKER`: 28,48/0,38 cm,
5,01 × 0,95 cm, Ränder 0,20/0,20/0,30/0,20 cm, Verlauf Akzent 6 transparent → Akzent 6 → Text 2,
Text 10 pt Akzent 4 in der Überschriftenschrift, rechtsbündig — nur Schemafarben).
Der PPTX-Konverter liest den Master nicht; der Sticker kommt nicht ins Markdown zurück.

**Englisch:** `sprache: en` nimmt für `basis` die englische Titelfolie (`slides-basis-en.pptx`),
für `schulung` die Schulungsvorlage, deren vier Titellayouts `prepare-templates` das deutsche
Logo nimmt (`slides-schulung-en.pptx`, `SLIDES_WITHOUT_TITLE_LOGO`); der Generator setzt auf
jede Titelfolie das englische Logo (`ENGLISH_LOGO_AREA`, Name `PTA-Logo EN`, den der Konverter
überspringt).

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
| `## Agenda {.agenda}` ohne Inhalt | wie oben | die Kapitel des Decks: alle `#` nach dem ersten, ohne `{.closing}`, bis vor `{.backup}` |
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
`layout="…"` geht ein Chart in den nächsten Diagrammplatzhalter des Layouts, dann mit Titel und
Einheit im Diagramm selbst. Renderer und PTA-Diagrammstil: [Charts](#charts-e06-s01).

**Zeichnungen** (`DrawingGraphic`, z. B. [Finanzdiagramme](#finanzdiagramme-e06-s02)) setzt
PowerPoint als Gruppe bearbeitbarer Formen (`generation/pptx/drawing.py`, Port von DocLibs
`DrawingWriter.cs`): Rechteck, abgerundetes Rechteck und Ellipse als Vorlagenformen, alles
andere als `custGeom`, je Textzeile ein Textfeld ohne Ränder in Segoe UI (Code: Consolas),
Hotspots entfallen. Die Gruppe heißt `Drawing <id>` mit dem Info-String als Alternativtext und
steht wie eine Tabelle in der Inhaltsfläche von `Nur Titel` (Text davor → `Titel und Text`,
Text danach als Textfeld darunter), oben mittig, auf den Platz verkleinert, nie vergrößert
(1 px = 9525 EMU). Auf Flow-Folien und benannten Layouts ist eine Zeichnung ein Fehler; Word
setzt Zeichnungen als Bild (siehe [Grafiken in Word](#grafiken-in-word-e03-s04)). Der
PPTX-Konverter lässt `Drawing`-Gruppen weg.

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
Ein Codeblock wird ein Absatz je Zeile, ganz in Consolas, ohne Hervorhebung (E08-S03: so steht
der Markdown-Quelltext einer Folie in `samples/funktionen/` auf ihrer Notizenseite); enthält er
`:::`-Zeilen, braucht der Notizblock einen längeren Zaun (`:::: notes`). Tabellen, Bilder und
Linien in Notizen entfallen ohne Fehler. Ein Deck ohne
`::: notes` hat keine `ppt/notesSlides/`. Ein `::: notes` vor dem ersten `#`/`##` ist ein Fehler
von `layout_syntax.check` (`Line 3: A '::: notes' belongs under a heading: …`). Word lässt
Notizen weg und meldet `notes-dropped`.

### Builds (E09-S02)

Eine Zeile aus nur `{.build}`, `{.frag}`, `{.exit}` oder `{.emphasize}` markiert den Block
danach (`markdown/block_markers.py`, Port von vt-tools-libs `BlockMarkers`): als eigener Absatz,
als erste Zeile des Absatzes, den sie markiert, oder als letzte Zeile eines Absatzes direkt vor
dem Block (so in einem Listenpunkt vor einer verschachtelten Liste). Eine Kernregel des
gemeinsamen Parsers (`block_markers_rule`, nach `alerts`) nimmt die Zeile aus den Token und legt
den `Marker` in `meta[MARKER]` des ersten Tokens des Blocks — **alle** Formate lesen so dasselbe
Markdown; Word und PDF erzeugen ohne die Zeile genau dasselbe wie ohne Marker. Eine falsche
Marker-Zeile bleibt als Absatz mit `meta[ERROR]` stehen und `layout_syntax.check` wirft sie mit
Zeile: unbekannter Marker (`Line 7: Unknown block marker '{.wide}'. Valid markers: {.build},
{.frag}, {.exit}, {.emphasize}; …`), mehrere Klassen, ein Marker ohne Block (am Ende, vor `---`,
vor dem Ende eines Containers), vor einer Folienüberschrift (`#`/`##`), vor `::: notes`, zwei
Marker vor einem Block, ein Marker mitten im Absatz, `{.emphasize}` vor etwas anderem als Text
(Absatz, Liste, Überschrift). `{.build}` und `{.frag}` nehmen einen Eingang: `=fade` (Standard),
`=appear`, `=fly`, `=wipe`. Front Matter `aufbau: listen` (`Keys.BUILD`, nur PowerPoint,
`PptxOptions.build_lists`) wirkt wie `{.build}` vor jeder Liste, die nicht in einer anderen steckt
(auch in Containern); `nein` ist der Standard.

| Marker | vor | in PowerPoint |
| ------ | --- | ------------- |
| `{.build}` | Liste | jeder Absatz jeder Ebene ein Klick |
| `{.build}` | `::: cards`, `::: rows`, `::: columns`, Absatz nur aus Bildern | jedes Element (Karte, Zeile, Spalte, Bild) ein Klick, mit allem darin |
| `{.build}`, `{.frag}` | jedem anderen Block (Tabelle, Code, Grafik, Chart, Container, Alert, Absatz) | der Block auf einem Klick |
| `{.exit}` | Block | der Block ist da und blendet beim Klick aus |
| `{.emphasize}` | Absatz, Liste, Überschrift | der Text wird beim Klick PTA-blau |

PowerPoint: `DeckParser` zählt Klicks (`model.Click(number, effect)`, Effekt `model.Effect`)
über das Deck in Markdown-Reihenfolge (`marked`, `at`, `paragraph_click`, `take_each`); Absätze,
Tabellen, Bilder, Code, Zeichnungen, Charts und Flow-Blöcke tragen `click` (kw-only), Karten,
Zeilen und Spalten (`ColumnsBlock.clicks`) je Element; Absätze in einem Block erben dessen
Klick. Marker auf Titel-, Trenn- und Abschlussfolien, auf PTA-Folienarten und auf Teilen eines
Blocks, die nur als Ganzes gebaut werden (Kartenüberschrift, Punkt in `::: rows`), sind Fehler.
`DeckWriter` sammelt beim Zeichnen in `animations.Builds`: `write_paragraphs` und
`FlowWriter.text` jeden Absatz mit Klick (Ziel `pRg`), `DeckWriter.at(slide, click)` jede in der
Zeit angelegte Form als Ganzes, `DeckWriter.each` je Bild einer Bildreihe; beim Anlegen der
nächsten Folie (und am Ende) schreibt `Builds.write` `p:timing` (vor `p:extLst`) — nur für Formen,
die `finish` stehen ließ. Eine geteilte Folie baut auf jedem Teil, mit den Klicks ihrer Teile.
Effekte wie PowerPoint (500 ms): Fade (Preset 10), Erscheinen (1), Hereinfliegen von unten (2),
Wischen von unten (22), Ausblenden (Exit 10), Schriftfarbe PTA-Blau (Emphasis 3). Build-Liste:
`bldP build="p"` für absatzweise, `bldP animBg="1"` für ganze Formen, `bldGraphic`/`bldAsOne`
für Tabellen und Charts; Bilder und Gruppen ohne Eintrag; eigene `grpId` je Form und
Effektklasse. Der PPTX-Konverter liest keine Builds.

### Folienübergänge (E09-S03)

`generation/common/slide_transition.SlideTransition` (`StrEnum`, Port von vt-tools-libs
`SlideTransition`, erweitert nach der Entscheidung vom 2026-11-07) nennt die Werte, `VALID` die
Liste für Meldungen. Front Matter `uebergang` (`Keys.TRANSITION`, nur PowerPoint) setzt
`PptxOptions.transition` (Standard `none`); das Heading-Attribut `uebergang="…"`
(`HeadingAttributes.transition`, auf `#` und `##`) prüft `heading_attributes.split` in **allen**
Formaten (`Line 3: Unknown slide transition 'slide'. Valid transitions: none, fade, …`); Word und
PDF ignorieren es. `DeckParser._transition` gibt jeder Folie einer Überschrift
`Slide.transition`: die eigene, sonst die des letzten `#` (Trennfolie und Kapitel; ein `#` ohne
Attribut setzt sie zurück); geteilte Folien erben sie. `DeckWriter.new_slide` schreibt
`animations.set_transition(slide.transition ?? options.transition)` direkt nach `p:clrMapOvr`,
also vor `p:timing` (Schemareihenfolge, sonst Reparatur).

| Wert | XML (`spd="med"`) |
| ---- | --- |
| `fade` | `p:fade` |
| `push`, `push-left`/`-right`/`-up`/`-down` | `p:push`, `dir="l"`/`"r"`/`"u"`/`"d"` (Richtung der Bewegung, Standard `l`) |
| `wipe`, `wipe-left`/`-right`/`-up`/`-down` | `p:wipe`, ebenso |
| `split` | `p:split orient="vert" dir="out"` |
| `cover`, `uncover` | `p:cover`, `p:pull` |
| `zoom`, `cut` | `p:zoom`, `p:cut` |
| `morph` | `mc:AlternateContent`: `mc:Choice Requires="p159"` mit `p159:morph option="byObject"`, `mc:Fallback` mit `p:fade` (beide `spd="slow"`) |

`none` schreibt nichts. Der PPTX-Konverter liest keine Übergänge.

### Szenen (E09-S04)

Ein `::: scene` unter einem `##` legt benannte Formen an feste Stellen der Folie; trägt die
nächste Szenenfolie `{uebergang="morph"}`, bewegt PowerPoint die gleichnamigen Formen von der
einen Lage in die andere (verschieben, vergrößern, drehen, umfärben, ein- und ausblenden):

```markdown
## Drei Orte {uebergang="morph"}

::: scene
- sp: box   10,20  36x14  "SharePoint"
- od: round 62,30  36x14  "OneDrive"              rotate=-3
- q:  pill  45,52  70x9   "Welche Version gilt?"  fill=warning step=1
:::

## Ein Ort {uebergang="morph"}

::: scene
- sp: box   50,20  60x18  "Ein Ablageort"  fill=primary text=background bold
- od: round 50,20  60x18                   opacity=0
- a:  arrow 80,40  0x14                    step=1
:::
```

- **Eine Form je Zeile:** `name: art x,y bxh "Text" schlüssel=wert …`, wahlweise als
  Listenpunkt (`- `), damit das Markdown anderswo als Liste lesbar bleibt. Leerzeilen und
  `<!-- Kommentare -->` zählen nicht. Die Zeilen werden roh gelesen
  (`markdown.parser.SOURCE_LINES` am Container-Token), nicht als Markdown.
- **Raster:** 160 × 67 quadratische Einheiten über die Inhaltsfläche von `Nur Titel`
  (`design.slides.CONTENT_AREA`, eine Einheit 0,195 cm = `scene.UNIT_EMU` 70 200 EMU), von ihrer
  oberen linken Ecke. Zahlen dürfen Nachkommastellen haben; eine Form, deren Kasten über das
  Raster hinausreicht, ist ein Fehler (`… reaches outside the grid of 160 × 67 units …`).
  Der Titel steht darüber, wo das Layout ihn hinsetzt.
- **Arten:** `box`, `round` (runde Ecken), `pill`, `circle`, `text` (ohne Kasten, linksbündig),
  `line` und `arrow` (von `x,y` nach `x+b,y+h`; `b` und `h` dürfen negativ oder 0 sein), `image`
  (`image=<pfad>` aus den Ressourcen des Dokuments, in den Kasten **eingepasst**, nie
  beschnitten; der Text ist der Alternativtext). Text steht in Kästen waagerecht und
  senkrecht mittig, in Segoe UI Light (fett: Segoe UI), Standardgröße 16 pt.
- **Attribute:** `fill`, `line`, `text` (Farben), `rotate` (Grad, im Uhrzeigersinn), `opacity`
  (0–1), `size` (Schriftgröße in pt), `bold`, `solid` (Kästen: Farbfüllung voll statt weich),
  `step` (der Klick, auf dem die Form erscheint; 0 = mit der Folie — ein Fade wie die Builds).
- **Farben** (`generation/common/scene_colors.py`) nur aus der PTA-Palette: `primary` (PTA-Blau),
  `text` (Folientext), `muted` und `line` (dunkles Grau), `border` (mittleres Grau), `surface`
  (helles Grau der PTA-Flächen), `background` (Weiß), `accent1`–`accent6` (Theme-Akzente),
  `success`, `info`, `warning`, `danger`, `neutral` (Signalfarben) — dazu `#RRGGBB` aus dem
  Markdown oder `none`. Kästen sind standardmäßig `surface` mit `border`-Linie, Linien und
  Pfeile `line`, Text `text` (auf `.dark`-Folien freier Text Weiß). Eine Füllung in einer Farbe
  außer PTA-Blau ist **weich**: die Farbe zu 12 % auf Weiß, mit der Farbe als Linie und Text in
  `text`; `solid` hält sie voll.
- **Eine Szenenfolie** ist ein `##` mit genau einem `::: scene` und sonst nur `::: notes` (und
  HTML-Kommentaren); das `##` nimmt `.dark`, `kicker="…"`, `uebergang="…"` und höchstens
  `layout="Nur Titel"`. Eine Szene unter `#`, vor der ersten Überschrift, in einem anderen
  Container, eine zweite Szene, weiterer Inhalt, eine PTA-Folienart, ein anderes Layout oder ein
  Blockmarker vor der Szene sind Fehler. `layout_syntax.check` prüft das und liest jede Szene
  (`scene.check_place`, `scene.read_scene`), in **allen** Formaten mit Zeile:
  `Line 14: Scene shape '- b: blob 0,0 1x1': unknown kind 'blob'. Valid kinds: box, round, …`.
- **PowerPoint** (`generation/pptx/scene_writer.py`): Folie auf `Nur Titel` (Titel, Kicker,
  dunkler Hintergrund wie Flow-Folien), je Form ein `p:sp` (`rect`, `roundRect` mit `adj`,
  `ellipse`, `line` mit `tailEnd` für Pfeile) bzw. ein `p:pic`, benannt `!!name` — so paart Morph
  die Formen. Deckkraft ist `a:alpha` (Bilder `a:alphaModFix`), Drehung `rot`.
- **PDF** (`drawing/scene.py`, `StoryBuilder.scene`): die Szene als Standbild in Textbreite,
  alle Schritte sichtbar, auf Weiß bzw. PTA-Dunkelblau mit dünnem Rahmen; Deckkraft wird auf
  den Grund gemischt (PDF/A), unsichtbare Formen (`opacity=0`) fehlen, Text steht ungedreht in
  einer Zeile. **Word** lässt die Szene weg und meldet `scene-dropped`.
- Der PPTX-Konverter liest die Texte der Formen als Absätze zurück.

## Markdown → HTML-Deck (E10-S01)

```python
from pta_documents.generation.html.generator import HtmlDeckGenerator
from pta_documents.generation.html.options import HtmlDeckOptions

with open("folien.html", "wb") as output:
    result = HtmlDeckGenerator().generate(document, output, HtmlDeckOptions())
```

`./run.sh generate <datei-oder-ordner> --html` schreibt `<name>.html` neben das Markdown (nur
mit dem Schalter, nie nebenbei). Das HTML-Deck ist eine **Vorschau** der PowerPoint-Präsentation
im Browser (Entscheidung E10, Frage 2), kein eigenes Zielformat.

**Aufbau.** `HtmlDeckGenerator.generate` liest das Front Matter (`VALID_KEYS` = die des
PPTX-Generators plus `fortschritt` und `kapitelanzeige`, `Keys.PROGRESS`/`Keys.CHAPTERS`, beide
`ja`/`nein`, Standard `ja`), lässt dann **`PptxGenerator` das Deck in einen Puffer schreiben**
(die beiden eigenen Schlüssel als Kommentarzeilen, damit Zeilennummern gleich bleiben) und
zeichnet dessen Folien mit `HtmlDeckWriter` (`generation/html/writer.py`). Darum hat das
HTML-Deck dieselben Folien, Titel, Teilungen („(Forts.)"), Fehler und Hinweise wie die PPTX;
Fehler kommen als `DocumentConversionError` mit Format `html` und dem `reason` der PPTX.
`GenerationResult` ist das der PPTX. `HtmlDeckOptions` hat die Felder von `PptxOptions` (über
`slides()` weitergereicht) und `show_progress`, `show_chapters`.

**Zeichnen** (`generation/html/`): `shapes.py` setzt jede Form des Folien-, Layout- und
Masterbaums absolut auf eine Bühne von 1600 px Breite (1 EMU = 1600 / Folienbreite px, 1 pt =
1,667 px; Höhe 900 px bei 16:9): Umriss und Füllung als Inline-SVG (`geometry.py`: die
Voreinstellungen `rect`, `roundRect`, `ellipse`, `line`, `pie`, `chevron`, `homePlate`,
`triangle`, `wedgeRectCallout` und `a:custGeom`; andere als Rechteck), Text als HTML
(`text.py`: Vererbung Präsentation → Master-Textstil → Listenstile von Master- und
Layout-Platzhalter → Form → Absatz → Lauf, `normAutofit` wie PowerPoint, Aufzählungszeichen aus
Wingdings als Unicode, einfacher Zeilenabstand 1,33 em für Segoe UI/Selawik, 1,17 em für
Consolas, kein Abstand vor dem ersten Absatz), Bilder als Kasten mit dem Bild als Hintergrund
(`srcRect` als Ausschnitt, Ellipse rund; `asvg:svgBlip` statt des PNG), Tabellen als
HTML-Tabelle, native Diagramme als Zeichnung ihrer Daten (`charts.py`: Diagrammteil →
`ChartSpec` → `charts.drawing.draw` → `to_svg`). Farben aus dem Theme der Vorlage
(`ooxml.Palette`, mit `clrMap` und `lumMod`/`shade`/`tint`/`alpha`). Die EMF-Logos der Layouts
zeigt kein Browser: an ihre Stelle tritt das SVG-Logo aus E01-S04 (`Logo.SLIDES`, auf der
Abschlussfolie `SLIDES_PLAIN`). Jedes Bild steht einmal als CSS-Klasse `imN` mit `data:`-URI im
Kopf (`ImageStore`).

**Builds und Übergänge** liest `timing.py` aus dem, was der PPTX-Generator schrieb: jede
Klickgruppe der Hauptsequenz ist ein Schritt (`data-build="n"`, `data-effect` =
`fade`/`appear`/`fly`/`wipe`/`exit`/`emphasize`, an der Form oder am Absatz), der Übergang aus
`p:transition` (`data-transition`, `morph` blendet im Browser über). Sprechernotizen stehen
verborgen in `<aside class="notes">` jeder Folie.

**Seite.** Eine Datei, UTF-8 ohne BOM: Selawik (300/400/700) und Inconsolata (OFL, aus
`design.fonts`) als `@font-face` mit `data:`-URI — `font-family: "Segoe UI", Selawik,
sans-serif`, Segoe UI wird nie eingebettet. `runtime/deck.css` und `runtime/deck.js` (Port der
vt-tools-libs-Laufzeit ohne Szenen) stehen inline; eine Content-Security-Policy
(`default-src 'none'`, Skript nur mit dem SHA-256 der Laufzeit) lässt kein anderes Skript und
keinen Abruf zu. Rohes HTML lässt schon der PPTX-Generator weg (Hinweis `raw-html`), Text ist
escaped, Links nur `http(s):`/`mailto:`, `http(s)` öffnen in neuem Tab. Texte der Laufzeit in
`design.variants.TEXTS` (`key_hint`, `notes_title`, `slide_announcement`), `lang` aus `sprache`.

**Bedienung:** →/Leertaste/Bild ab/Klick weiter (erst die Schritte, dann die Folie), ←/Bild auf
zurück, Pos1/Ende, `#12` in der Adresse springt zu Folie 12, Wischen auf Touch-Geräten, `N`
Notizenpanel mit Uhr, `F` Vollbild, `B` schwarz. Fortschrittsbalken unten, Kapitel (`#`) oben.
`prefers-reduced-motion` schaltet Übergänge und Aufbauten ab. Drucken (oder „Als PDF
speichern") ergibt eine Seite je Folie in 16:9, mit allen Aufbauten.

Tests: `tests/generation/html/` (Schnappschuss `samples/deck.expected.html`, Daten-URIs als
Hash, Schriften und Laufzeit herausgenommen); `test_browser.py` braucht Playwright (Extra
`preview`, `pip install -e '.[preview]'` und `python -m playwright install chromium`) und wird
sonst übersprungen.

## Vorschau als Bilder (E10-S02)

```python
from pta_documents.preview import contact_sheet, render_deck

pictures = render_deck(html_bytes, scale=1, slides=None)  # [SlidePicture(number, png)]
sheet = contact_sheet(pictures, columns=4)  # PNG-Bytes
```

`./run.sh preview <datei-oder-ordner> [--scale n] [--slides 3,7-9] [--html] [--audience …]`
(`tools/preview/preview.py`) erzeugt für jede Präsentation (`…-praesentation.md`,
`…-folien.md`; Word-Berichte: „there is no preview for Word documents") das HTML-Deck im
Speicher, leert `<ordner>/vorschau/<name>/` und schreibt dort `folie-NN.png` und
`uebersicht.png`, danach die Hinweise des Generators. `--audience kunde|intern|trainer` wählt die
Fassung (E16-S01, sonst `fassung:`); andere als `kunde` landen in `vorschau/<name>-intern/` bzw.
`…-trainer/`. Bilder unter `vorschau/` gehen nicht als
Ressourcen ins Deck. `--check-browser` endet mit 0, wenn Playwright und Chromium starten (für
`setup`). Exit-Code 1 bei Fehlern im Dokument oder fehlender Vorschau, 2 bei falschen Schaltern.

**Ablauf** (`preview/deck.py`): Playwright (Extra `preview`, Apache-2.0, per `importlib`
geladen) startet Chromium headless mit `--font-render-hinting=none`; der Kontext hat Viewport
1600 × Bühnenhöhe, `device_scale_factor=scale`, `reduced_motion="reduce"`, Locale `de-DE`,
Zeitzone Europe/Berlin. Das Deck wird über `context.route` aus dem Speicher unter
`https://deck.preview/` ausgeliefert, jede andere Anfrage abgewiesen — keine Datei, kein Netz.
Vor `</head>` kommt ein Vorschau-Stil: `@font-face` „Segoe UI" = Selawik und „Consolas" =
Inconsolata (die eingebetteten Schriften aus `writer.FONT_FACES`; eine eigene `@font-face`
verdeckt die installierte Schrift), die Bühne ohne Skalierung oben links, Kapitelleiste,
Fortschritt, Tastenhinweis und Notizen ausgeblendet, Animationen und Übergänge aus. Je Folie:
`location.hash = '#n'`, warten bis `#sN` aktiv ist, alle `[data-build]` der Folie auf `on`
(Endzustand), `document.fonts.ready` und zwei Frames, Screenshot der Bühne. Zwei Läufe ergeben
byte-gleiche PNGs. Fehlt Playwright oder startet Chromium nicht: `PreviewUnavailableError` mit
`INSTALL_HINT`. `chromium_available()` prüft beides.

`contact_sheet`: Kacheln 400 px breit in Zeilen zu `columns`, 16 px Abstand, darunter die
Foliennummer (Selawik 18 px), Hintergrund `GREY_LIGHT`, Rahmen `GREY_DARK`; PNG optimiert.

Tests: `tests/preview/` — ohne Browser Kontaktbogen, Vorschau-Stil, Meldung ohne Playwright,
Schalter des Werkzeugs; mit Browser (sonst übersprungen) Anzahl und Maße, Auswahl mit
`--scale 2`, Wiederholbarkeit, Aufbauten im Endzustand und Werkzeug am Ordner. Der Vergleich
mit Referenzbildern läuft am kleinen, festen Test-Deck `tests/preview/samples/vorschau-referenz.md`
(sieben Folien: Titel, Text mit Liste, Karten, Spalten mit Fazit, Diagramm, dunkle Folie,
Schlussfolie; Diagramme nur mit `ChartRenderer`, ohne Mermaid) gegen
`tests/preview/expected/vorschau-referenz/folie-NN.png`: Referenzen in halber Größe (800 × 450,
zusammen ~0,6 MB), ein Pixel weicht ab, wenn ein Kanal um mehr als 16 abweicht; weniger als
0,5 % abweichende Pixel je Folie. Neu schreiben mit `PTA_DOCUMENTS_UPDATE_EXPECTED=1` und das
Ergebnis in `.tmp/review/preview/` ansehen. Die Funktionsübersicht
`samples/funktionen/funktionen-praesentation.md` wächst mit jeder Story und hat deshalb keine
eingecheckten Bilder, nur einen Rauchtest: ein Bild je Folie der PPTX, jedes 1600 × 900, erste
und letzte Folie bei einem zweiten Lauf byte-gleich (Bilder in
`.tmp/review/preview/funktionen-praesentation/`).

## Folien-Syntax (gemeinsam für Word und PowerPoint)

Beide Generatoren lesen und prüfen dieselbe Folien-Syntax aus DocLibs, bevor sie schreiben
(`generation/common/layout_syntax.check`); ein Fehler ist eine `DocumentConversionError`, deren
`reason` mit der Zeile beginnt (`Line 12: Unknown container '::: card'. Valid containers: …`,
Front Matter mitgezählt).

| Syntax | Gültig | Heute in Word und PowerPoint |
| ------ | ------ | ---------------------------- |
| Heading-Attribute `{…}` am Ende von `#`/`##` | `#`: `.closing`, `layout="…"`, `uebergang="…"`; `##`: `.dark`, `kicker="…"`, `layout="…"`, `uebergang="…"` (siehe [Folienübergänge](#folienübergänge-e09-s03)), PTA: `.agenda`, `.interim`, `.quote`, `.contact` (eine davon, nicht mit `.dark`/`kicker`); beide: `.internal` (siehe [Zielgruppenfassungen](#zielgruppenfassungen-e16-s01)); nur `#`: `.backup`, `.appendix` (siehe [Backup-Folien und Anhang](#backup-folien-und-anhang-e16-s04)); beide: `dauer=5` (ohne Anführungszeichen, auch `dauer=1h30`), `##`: `.break` (Pause, eine PTA-Folienart, braucht `dauer`; siehe [Schulungs-Zeitplan](#schulungs-zeitplan-e16-s02)) | PowerPoint: alle wirken (s. o., Flow-Folien, PTA-Folienarten); Word: entfernt, die Folienarten schlicht (s. u.) |
| Container `::: name argumente` … `:::`, verschachtelt mit längeren Zäunen (`::::` außen) | `cards`, `rows`, `panel` (Argument `dark`), `statement`, `columns` (Argument `1:2` oder `1:1:2`), PTA: `conclusion`, `comment`; `notes` (Sprechernotizen); `timeline`, `gantt` (Argument `raster=woche\|monat\|quartal`, siehe [Zeitstrahl und Gantt](#zeitstrahl-und-gantt-e15-s01)); `steps`, `riskmatrix` (Argumente `green=4 yellow=12`, siehe [Schrittfolge, Harvey Balls und Risikomatrix](#schrittfolge-harvey-balls-und-risikomatrix-e15-s02)); `scene` (siehe [Szenen](#szenen-e09-s04)); `internal`, `exercise`, `solution` (siehe [Zielgruppenfassungen](#zielgruppenfassungen-e16-s01)) | alle Formate: `internal`/`exercise`/`solution` werden je Fassung weggelassen oder ohne Rahmen gezeigt; PowerPoint: Flow-Folien, `notes` auf die Notizenseite, `timeline`/`gantt`/`steps`/`riskmatrix` als Formgruppe (die Legende der Risikomatrix als Tabelle daneben); `scene` als benannte Formen auf `Nur Titel`; Word: Inhalt nacheinander, Fazit/Kommentar als „Hinweis", `notes` entfällt, `timeline`/`steps`/`riskmatrix` als Bild (Legende als Tabelle darunter), `gantt` als Tabelle, `scene` entfällt; PDF wie Word, die Grafiken als Vektoren, `scene` als Standbild |
| Alerts `> [!NOTE]` (erste Zeile des Zitats) | `NOTE`, `TIP`, `IMPORTANT`, `WARNING`, `CAUTION` | PowerPoint: Fläche mit Balken; Word: „Hinweis" bzw. „Hinweis wichtig" mit fetter Art am Anfang |
| `==Markierung==` | – | PowerPoint: fett auf `FDDC35`; Word: Zeichenvorlage „Markierung" |
| Zeile aus nur `{.build}`, `{.frag}`, `{.exit}`, `{.emphasize}` vor einem Block | `{.build}`/`{.frag}` mit `=fade`, `=appear`, `=fly`, `=wipe` (siehe [Builds](#builds-e09-s02)) | PowerPoint: der Block erscheint (verschwindet, wird blau) Klick für Klick; Word/PDF: die Zeile entfällt |
| Zeile aus nur `{.internal}` vor einem Block | auch vor `::: notes` (siehe [Zielgruppenfassungen](#zielgruppenfassungen-e16-s01)) | alle Formate: der Block fehlt in der Kundenfassung |
| Bildattribute `{…}` direkt nach einem Bild | `focus=…`, `fit=cover\|contain`, `scale=N`, `.round`, `.grey` (siehe [Bildattribute](#bildattribute-e15-s04)) | PowerPoint: Ausschnitt im Bildplatzhalter, rund als Ellipse; Word/PDF: kein Beschnitt, rund/grau als PNG |
| Icon `:icon-name:` | die gebündelten Namen (siehe [Icons](#icons-e15-s03)) | PowerPoint: am Anfang eines Kartentitels die Figur der Karte, vor jedem Punkt einer Liste das Aufzählungssymbol, sonst Fehler; Word und PDF: Bild im Text, vor jedem Punkt einer Liste statt des Aufzählungszeichens |
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
| `{.agenda}` | „Überschrift 2" mit der Liste; ohne Liste die folgenden `#`-Kapitel (ohne `{.closing}`, bis vor `{.appendix}`) als nummerierte Liste |
| `{.interim}` | die Aussage als „Standard fett" |
| `{.quote}` | Zitat und Quelle als „Zitat" |
| `{.contact}` | „Überschrift 2", je Person `###` als „Standard fett", Foto höchstens 3 cm breit ohne Beschriftung, jede Zeile für sich |

Die Aufbauregeln der Folien (z. B. höchstens acht Agendapunkte, Fazit-Box höchstens zwei Zeilen)
prüft nur PowerPoint; Word meldet die Fehler von `layout_syntax.check` wie PowerPoint. Der
DOCX-Konverter liest die neuen Vorlagen wie „Standard"; „Hinweis …" wird wieder ein Zitat (ein
Alert mit seiner Art, `> [!NOTE]`), eine Bildreihe wieder ein Absatz aus Bildern mit den
Beschriftungen danach.

## Typografie und Code (E17-S02)

Beide Generatoren setzen den Text typografisch (`markdown.typography.typeset` auf den Token,
nach der Prüfung der Folien-Syntax), sofern nicht `typografie: nein` bzw.
`DocxOptions(typography=False)`/`PptxOptions(typography=False)`:

| Geschrieben | Gesetzt (`sprache: de`) | `sprache: en` |
| ----------- | ----------------------- | ------------- |
| `"Zitat"`, `'halb'` | „Zitat“, ‚halb‘ | “Zitat”, ‘halb’ |
| `geht's`, `Hans'` | geht’s, Hans’ | ebenso |
| ` - `, ` -- ` (mit Leerzeichen) | ` – ` (Halbgeviertstrich) | ebenso |
| `...` | … | ebenso |
| `z. B.`, `u. a.`, `d. h.`, `i. d. R.` | geschütztes Leerzeichen (U+00A0) | unverändert |
| `Nr. 3`, `S. 12`, `Abs. 2`, `§ 5` | geschütztes Leerzeichen vor der Zahl | unverändert |
| `10 %`, `5 km`, `3 Mio.`, `2 GB`, `20 °C` | geschütztes Leerzeichen vor der Einheit | ebenso |
| `1. Januar`, `24. Dez.` | geschütztes Leerzeichen | unverändert |

Unverändert bleiben Code-Spans, Codeblöcke, Link-Ziele, Autolinks, rohes HTML, das
Attribut-Block einer Überschrift (`{kicker="…"}`) und das Front Matter (auch `titel:`).
Bindestriche in Wörtern (`E-Mail`) bleiben (Entscheidung 2026-11-07), ein schmales
geschütztes Leerzeichen (U+202F) wird nie gesetzt. Status-Labels (`status.<kategorie>`)
werden genauso gesetzt, damit sie die gesetzten Tabellenzellen wiederfinden.

Codeblöcke mit Sprache im Zaun (```` ```python ````) werden mit **Pygments** (BSD-2-Clause,
Kernabhängigkeit) farbig hervorgehoben (`generation.common.code_highlight`): Schlüsselwörter
PTA-Blau fett, Zeichenketten Dunkelblau, Kommentare Grau kursiv, Zahlen und Konstanten
`404040`, der Rest in der Textfarbe; die graue Fläche bleibt. Word schreibt Runs mit
`w:color`/`w:b`/`w:i` in der Formatvorlage „Code" und merkt sich die Sprache als eigene,
für Word ignorierbare Absatz-Eigenschaft `<pta:codeLanguage pta:val="python"/>` (Namensraum
`urn:pta-documents:wordprocessingml`, in `mc:Ignorable`); der DOCX-Konverter gibt Absätze in
„Code" daraus wieder als Zaun mit Sprache aus. PowerPoint färbt die Runs im Codefeld (auch auf
Flow-Folien und über „(Forts.)"-Folien hinweg). Ohne Sprache bleibt der Block einfarbig; eine
unbekannte Sprache ergibt den Hinweis `code-language-unknown`. `syntaxhervorhebung: nein`
bzw. `highlight=False` schaltet die Farben ab. Das PDF färbt Code genauso (seit E05-S02) und
setzt die Typografie wie Word.

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
  Markdown-Bild, mit dem Info-String als Alt-Text — in Word mit „Abbildung n"-Beschriftung nur,
  wenn ein Absatz `Abbildung: …` folgt, in PowerPoint wie ein Bild allein auf einer Folie.
  `DrawingGraphic(drawing)` und `ChartGraphic(chart, drawing)` (Daten in
  `pta_documents.charts.ChartSpec`, `drawing` ist ein `Drawing` aus
  [`pta_documents.drawing`](#zeichenmodell-und-svg-e02-s03)): Charts setzen beide Generatoren
  nativ ([Charts](#charts-e06-s01)); Zeichnungen setzt PowerPoint als Formengruppe, Word als
  Bild ([Grafiken in Word](#grafiken-in-word-e03-s04)).
- **Nicht verfügbar:** Kann ein Renderer den Block hier nicht zeichnen (sein Werkzeug fehlt,
  oder das Format hat noch keinen Platz für seine Grafik), wirft er
  `RendererUnavailableError(grund)`: der Block bleibt Code, der Hinweis `code-not-drawn` nennt
  den Grund (so macht es der Mermaid-Renderer ohne mmdc oder Chromium).
- **Konverter** (`generation/common/images.py`, `ImageConverter`) bekommen jedes Bild, dessen
  Format der Generator nicht setzt (alles außer PNG, JPEG, GIF, BMP, TIFF, z. B. SVG), mit
  `scale = 2`; der erste mit Ergebnis gewinnt. Word setzt das Ergebnis in der natürlichen Größe
  aus `ConvertedImage` (Pixel bei 96 dpi), PowerPoint wie jedes andere Bild (Seitenverhältnis
  aus der natürlichen Größe). Gibt der Konverter in `ConvertedImage.svg` ein SVG mit, legen
  beide es neben das PNG (`asvg:svgBlip`, siehe [SVG-Bilder](#svg-bilder-e06-s04)). Nimmt kein
  Konverter das Bild, bleibt es ein Fehler (`… is a image/webp; …, and no image converter takes
  it`; für ein SVG ohne Extra `svg`: `…; SVG images need the extra 'svg' …`).
- **Fehler:** wirft ein Renderer oder Konverter eine `DocumentConversionError`, geht sie
  unverändert durch (ebenso `RendererUnavailableError`, siehe oben); jede andere Ausnahme wird zu `DocumentConversionError` im Format des
  Generators (Konverter: `The image '…' cannot be converted: …`), die ursprüngliche steht in
  `__cause__`.
- **Standard:** ohne Angabe nehmen die Optionen alle Renderer und Konverter der Bibliothek, die
  verfügbar sind (`default_renderers()`, `default_converters()`); `()` schaltet sie ab.
  `default_converters()` enthält mit dem Extra `svg` den `SvgImageConverter` (E06-S04), sonst
  nichts; `default_renderers()` enthält den `ChartRenderer` (E06-S01, Kern) und, wenn
  `find_command()` ein mermaid-cli findet, den `MermaidRenderer` (E06-S03).

## Charts (E06-S01)

Ein ```` ```chart ````-Block (Sprache ohne Groß/Klein, nichts dahinter) wird über den
`ChartRenderer` (`pta_documents.charts.renderer`, in `default_renderers()`) ein
`ChartGraphic(chart, drawing)`. Syntax für Schreiber: [anleitung.md](anleitung.md#diagramme-aus-daten);
`ChartRenderer().authoring_guide` liefert denselben Abschnitt als `## Charts`.

```python
from pta_documents.charts import parse, draw, scale, format_number
from pta_documents.charts.renderer import ChartRenderer

spec = parse("type: line\n---\nx; a\n1; 2,5\n", line=10)  # ChartSpec; ChartBlockError bei Fehlern
drawing = draw(spec)  # Drawing 640 × 380 px, Zahlen deutsch („1.250,5")
```

- **Parser** (`charts/parser.py`, Port von `ChartParser.cs`): Einstellungen `type`, `title`,
  `unit`, `source`, `stacked` bis zur Zeile `---` (Schlüssel ohne Groß/Klein, doppelt =
  Fehler, Kommentar nach `` # `` oder als ganze Zeile `#…`), dann CSV. Die Kopfzeile entscheidet
  das Trennzeichen: enthält sie außerhalb von Anführungszeichen ein `;`, gilt `;` mit
  Dezimalkomma, sonst `,` mit Dezimalpunkt. Zahlen nur als `[+-]Ziffern[.,Ziffern][e±n]`, kein
  Tausendertrennzeichen, kein `nan`/`inf`; leere Zellen sind `None` (Lücke), fehlende Zellen am
  Zeilenende auch. Linien stapeln nie. Jeder Fehler ist `ChartBlockError` (`ValueError`) und
  beginnt mit `Line N: The chart block cannot be drawn: …` — N ist die Zeile im Dokument, in der
  der Fehler steht (Einstellung, Kopf- oder Datenzeile), sonst die des Zauns; die Generatoren
  machen daraus `DocumentConversionError` (Ursache in `__cause__`).
- **Zeichnung** (`charts/drawing.py`, Port von `ChartDrawing.cs`, für PDF/SVG): Titel, Einheit,
  Werteachse mit runden Schritten (`scale()`: 0 bzw. Minimum bis Maximum bzw. größte Summe in
  etwa sechs Schritten aus 1, 2, 2,5, 5, 10 × 10ⁿ), Kategorien, Legende, Quelle. Farben nur aus
  `design.colors`: Reihen `ChartSpec.colors` (Akzente der Reihe nach), Text `TEXT_WORD`,
  `TEXT_SLIDES` (PPTX) oder `WHITE` (`{.dark}`), Gitter `GREY_LIGHT`, Nulllinie `GREY_MID`;
  überlappende Flächen `colors.tint(farbe, 0.55)`. Zahlen in der Dokumentsprache
  (`format_number`).
- **Nativ** (`generation/common/native_chart.py`): Typ (`COLUMN_CLUSTERED`/`COLUMN_STACKED`,
  `LINE_MARKERS`, `AREA`/`AREA_STACKED`), Daten (`CategoryChartData`) und Stil für beide
  Generatoren: Lücke 60 %, keine Teilstriche, Kategorienachse 0,5 pt `GREY_MID`, Gitter 0,5 pt
  `GREY_LIGHT`, keine Werteachsenlinie, Werteachse ab 0 (Balken, Flächen), Legende unten ab zwei
  Reihen, kein Rahmen, Linien 2,25 pt mit Kreismarken. PowerPoint
  (`generation/pptx/chart.py`): 14 pt Segoe UI Light `TEXT_SLIDES`, Platzierung siehe
  [Diagramm-Layouts](#pta-folienarten-und-diagramm-layouts-e04-s04). Word
  (`generation/docx/chart.py`): Chart-XML von python-pptx als Teil `word/charts/chartN.xml`,
  Arbeitsmappe `word/embeddings/Microsoft_Excel_WorksheetN.xlsx` (`c:externalData`), inline
  über die Satzspiegelbreite, höchstens 5:8 so hoch (siehe
  [Grafiken in Word](#grafiken-in-word-e03-s04)), 10 pt Segoe UI `TEXT_WORD`, Einheit als
  Titel der Werteachse; mit `title` danach „Abbildung n: Titel", `source` als Absatz in
  „Beschriftung" ohne Nummer. Der DOCX-Konverter liest ein Diagramm als Tabelle seiner Daten,
  der PPTX-Konverter lässt es weg.

## Grafiken in Word (E03-S04)

`BodyWriter.block` (`generation/docx/writer.py`) fragt für jeden Zaun die Renderer
(`code_blocks.render_graphic`) und setzt jede Grafikart in einen eigenen Absatz
(`graphic_figure`):

- **Zeichnungen** (`DrawingGraphic`: Mermaid, Finanzdiagramme) über
  `generation/docx/drawings.py`: `drawing.to_svg` (Text in `Segoe UI, Selawik, sans-serif`) →
  `DocumentResource("<sprache>-<n>.svg")` → die Bildkonverter wie ein SVG-Bild aus Markdown
  ([SVG-Bilder](#svg-bilder-e06-s04)): PNG im doppelten Maßstab im `a:blip`, das SVG als
  `asvg:svgBlip`. Größe: die natürliche Größe des Drawings (1 px = 0,75 pt), verkleinert auf
  Satzspiegelbreite und 80 % der Satzspiegelhöhe, nie vergrößert. Alt-Text = Info-String.
  Nimmt kein Konverter SVG, ist das ein `DocumentConversionError`
  `Line N: The `<sprache>` block is a drawing, which Word places as an SVG image …` mit dem
  Hinweis auf das Extra `svg` (bzw. auf `DocxOptions.image_converters`, wenn sie abgeschaltet
  sind).
- **Charts** (`ChartGraphic`): nativ ([Charts](#charts-e06-s01)), so breit wie der Satzspiegel,
  höchstens 5:8 so hoch, gedeckelt bei 80 % der Satzspiegelhöhe (`design/word.py`:
  `CHART_HEIGHT_RATIO`, `FIGURE_HEIGHT_SHARE`) — im Querformat greift der Deckel.
- **Bilder** (`ImageGraphic`): wie ein Markdown-Bild.
- **Beschriftung, für alle gleich:** Ein Absatz, der mit `Abbildung:` (oder `Figure:`) beginnt
  und direkt nach dem Zaun auf derselben Ebene steht, wird „Abbildung n: …" in „Beschriftung"
  (`SEQ Abbildung`, fortlaufend mit den Bildern; mit `sprache: en` „Figure n: …"). Sonst gilt
  der Titel eines Charts (`title`); ohne beides keine Beschriftung. Der Absatz geht dem Titel
  vor. Grafik, Beschriftung und Quelle halten zusammen (`keepNext`).
- **Rücklesen:** Der DOCX-Konverter macht aus einem nativen Diagramm (`c:chart`) eine
  Markdown-Tabelle aus den zwischengespeicherten Werten des Chart-Teils: erste Spalte die
  Kategorien (Kopf leer), dann je Reihe eine Spalte, Zahlen ohne `.0`, leere Werte leer. Eine
  Zeichnung kommt als Bild (PNG) zurück.

## Finanzdiagramme (E06-S02)

Die sechs Diagramme einer Ergebnisübersicht (Port von DocLibs `DocumentGeneration.Charts`):
`DevelopmentChart` (Jahr Monat für Monat: Balken oben, kumuliert oder Wachstumsrate unten),
`GrowthByRowChart` (Wachstum je Zeile), `ActualVsReferenceChart` (Ist gegen Plan, Wachstum oder
Werte), `GrowthTrendChart` (Wachstumstrend), `TwoYearChart` (zwei Jahre, höchstens sechs
Kategorien) und `SummaryTable` (Übersichtstabelle) — aus Python-Daten oder einem
```` ```financial-chart ````-Block (JSON), gezeichnet als `Drawing`.

```python
from pta_documents.charts import financial
from pta_documents.charts.financial import FinancialChartOptions, GrowthTrendChart, TrendMonth

chart = GrowthTrendChart(title="Wachstum", last_actual=1, reference=0.05,
                         months=(TrendMonth("Jan", 0.06), TrendMonth("Feb", 0.04)))
options = FinancialChartOptions(culture="de-DE", scale=1_000_000, unit="Mio. EUR")
drawing = financial.draw(chart, options)   # Drawing, 560 px breit (options.width)
svg = financial.to_svg(chart, options)     # eigenständiges SVG mit Tooltips, ohne Skript
block = financial.to_json(chart, options)  # Inhalt eines financial-chart-Blocks
chart, options = financial.parse(block, line=12)  # FinancialChartError (ValueError) mit Zeile
```

- **Daten** (`charts/financial/model.py`): Frozen Dataclasses mit Tupeln; Wachstumsraten und
  Anteile sind Brüche (`0.052` = 5,2 %), `last_actual` ist ein Index ab 0. Fehlende oder
  unpassende Daten (keine Monate, Zeilen verschiedener Länge, mehr als sechs Kategorien) sind
  `ValueError`.
- **Block** (`charts/financial/json_block.py`): ein JSON-Objekt mit `type` (`development`,
  `growth-by-row`, `actual-vs-reference`, `growth-trend`, `two-year`, `summary-table`), den
  Feldern in camelCase (`lastActual`, `projectionComparedFrom`, `yearToDate`, `rateOf` …) und
  optional `options` (`culture`, `scale`, `unit`, `labels`, `tolerance`, `restShare`, `width`).
  Eigener kleiner JSON-Leser: Kommentare `//` und `/* */` und ein Komma nach dem letzten Eintrag
  sind erlaubt; unbekannte Schlüssel, doppelte Schlüssel, falsche Typen (eine Ganzzahl muss
  ganz sein, `true`/`false` ist keine Zahl), fehlende Pflichtfelder (die Felder ohne
  Standardwert, z. B. `label` und `change` eines Monats) und ungültiges JSON sind Fehler
  `Line N: The financial-chart block cannot be drawn: …` mit der Zeile im Dokument (Zeile des
  Zauns + Zeile im Block); Fehler in den Daten selbst tragen die Zeile des Zauns.
- **Optionen** (`charts/financial/options.py`): `culture` ist `de`, `de-DE`, `en`, `en-US` oder
  `en-GB` (Standard: im Renderer die Dokumentsprache, sonst `de-DE`); deutsch `5,2 %`,
  `1.250,5`, `-1,2 Pp.`, englisch `5.2%`, `1,250.5`, `-1.2pp`, gerundet kaufmännisch.
  Beschriftungen `FinancialChartLabels` (deutsch *Vorjahr, Ist, Plan, Prognose, Schätzung,
  Veränderung, Gesamt, Wert*, englisch *Previous, Current, Reference, Projection, Estimate,
  Change, Overall, Value*), `labels` im Block legt sich über die der Sprache.
- **Farben** (`design/chart_colors.py`, `FinancialChartColors`): Reihen `PTA_BLUE`, `DARK_BLUE`,
  `LIGHT_BLUE` je in vier Abstufungen über `colors.tint` (Füllung 18 %, blass 8 %, kräftig 65 %,
  Linie 100 %); Kategorien der Zwei-Jahres-Linien die Akzente der Reihe nach, verteilt nach
  Höhe der Linie (`financial.category_colors`); Referenz `GREY_DARK`, Referenzfläche und Gitter
  `GREY_LIGHT`, Achse `GREY_MID`, Band `tint(GREY_LIGHT, 0.5)`; vorn `SIGNAL_GREEN`, gleichauf
  `GREY_DARK`, hinten `SIGNAL_RED` (nur an Zahlen); Hervorhebung die kräftige erste Reihe;
  Tabellenkopf `PTA_BLUE`, Gesamtspalte `DARK_BLUE` mit `tint(PTA_BLUE, 0.1)`; Fläche und
  Schreibgrund weiß; Text `TEXT_WORD` (im Renderer für PowerPoint `TEXT_SLIDES`); Tooltip
  `TEXT_SLIDES` mit weißer Schrift. Keine dunkle Variante: auf `{.dark}` steht ein Diagramm
  ohnehin nicht (Flow-Folie).
- **SVG:** `to_svg` über `drawing.to_svg` in `Segoe UI, Selawik, sans-serif`; jeder Balken,
  Punkt und jede Linie hat einen Tooltip (Klassen `chart-hoverable`/`chart-tooltip`, siehe
  [Zeichenmodell](#zeichenmodell-und-svg-e02-s03)).
- **Renderer:** Der `ChartRenderer` nimmt neben `chart` auch `financial-chart` (ohne Groß/Klein,
  nichts dahinter) und liefert `DrawingGraphic`; seine `authoring_guide` hat dazu den Abschnitt
  `### Finanzdiagramme`. PowerPoint setzt es als Formengruppe (siehe
  [PTA-Folienarten](#pta-folienarten-und-diagramm-layouts-e04-s04)), Word als Bild (siehe
  [Grafiken in Word](#grafiken-in-word-e03-s04)).

## Mermaid (E06-S03)

```` ```mermaid ````-Blöcke zeichnet mermaid-cli (`mmdc`, Node.js mit einem kopflosen Chromium)
**lokal** zu SVG; `pta_documents.drawing.svg.to_drawing` macht daraus ein `Drawing`, das
PowerPoint als Gruppe bearbeitbarer Formen setzt (Schreiber aus E06-S02, Text in Segoe UI,
Rechteck, abgerundetes Rechteck und Ellipse als Vorlagenformen, alles andere als freie Form).
Kein Aufruf verlässt den Rechner: der Code geht über stdin an `mmdc`, das SVG kommt über stdout
zurück, mit `securityLevel: strict`.

**Einrichten.** Node.js ab 22, dann `./run.sh setup`: es installiert mermaid-cli in der
festgelegten Version aus `tools/mermaid/package.json` (`@mermaid-js/mermaid-cli` 12.2.0,
puppeteer 25.16.0, beide MIT, mit `package-lock.json`) per `npm ci` nach
`tools/mermaid/node_modules/`. puppeteer lädt dabei ein Chrome nach `~/.cache/puppeteer` (dafür
braucht es `unzip`). `./run.sh mermaid` prüft die Einrichtung und zeichnet ein Testdiagramm;
`./run.sh mermaid datei.mmd` schreibt die Zeichnung nach `.tmp/mermaid/` (SVG und PNG).

| Variable | Wirkung |
| -------- | ------- |
| `PTA_DOCUMENTS_MMDC` | ein anderes `mmdc` (sonst `mmdc` im `PATH`, sonst das repo-lokale) |
| `PUPPETEER_EXECUTABLE_PATH` | ein vorhandenes Chrome/Chromium statt des von puppeteer geladenen |
| `PTA_DOCUMENTS_PUPPETEER_CONFIG` | Pfad zu einer puppeteer-Konfiguration für `mmdc -p`, z. B. `{"args": ["--no-sandbox"]}`, wo Chromium keine Sandbox starten darf (Ubuntu ab 23.10 ohne AppArmor-Profil, Container) |

Ohne mermaid-cli bleibt jeder ```` ```mermaid ````-Block Code mit dem Hinweis `code-not-drawn`
und der Einrichtungsanleitung; ebenso, wenn `mmdc` Chromium nicht starten kann (der Hinweis
nennt die Variablen oben).

```python
from pta_documents.diagrams import MermaidErrorMode, MermaidRenderer
from pta_documents.charts.renderer import ChartRenderer
from pta_documents.generation.pptx.options import PptxOptions

renderer = MermaidRenderer(
    command=None,            # mmdc; None: PTA_DOCUMENTS_MMDC, PATH, tools/mermaid
    chromium=None,           # None: PUPPETEER_EXECUTABLE_PATH oder puppeteers eigenes
    puppeteer_config=None,   # None: PTA_DOCUMENTS_PUPPETEER_CONFIG
    timeout_s=60,
    on_error=MermaidErrorMode.KEEP_CODE,  # Standard THROW
)
options = PptxOptions(code_block_renderers=(ChartRenderer(), renderer))
```

- **Typen** (`diagrams.SUPPORTED`, erkannt am ersten Wort nach YAML-Kopf und `%%`-Zeilen):
  `flowchart`/`graph`, `sequenceDiagram`, `classDiagram`, `stateDiagram-v2`, `erDiagram`,
  `pie`, `gantt`, `mindmap`. Alle anderen (`journey`, `timeline`, …) bleiben Code — ohne
  Hinweis, sie sind kein Fehler.
- **Aussehen:** vor den Code kommt eine Zeile `%%{init: …}%%` (`mermaid.init_directive`):
  Thema `base`, Aussehen `classic`, `htmlLabels: false` (Text als SVG-Text, auch im
  Flussdiagramm), Umbruchbreite 300 px, Schrift `Segoe UI, Selawik, sans-serif` und die
  Theme-Variablen aus `design/diagram_colors.py`: Flächen `GREY_LIGHT`, Rahmen `PTA_BLUE`,
  Linien `GREY_DARK`, Text `TEXT_SLIDES` (Word: `TEXT_WORD`), Hintergrund weiß, Torten- und
  Mindmap-Farben die Akzente der Reihe nach (weiße Schrift auf `PTA_BLUE`, `DARK_BLUE`,
  `GREY_DARK`), dazu `themeCSS` für Gantt-Gitter und Sequenz-Pfeilspitzen.
- **Fehler:** Ein Syntaxfehler (mmdc endet mit Code ≠ 0) ist mit `THROW` ein Fehler
  `Line N: The mermaid block cannot be drawn: <Meldung von Mermaid>` (N = Zeile des Zauns; die
  Zeilennummer in Mermaids Meldung zählt Mermaid selbst), mit `KEEP_CODE` bleibt der Block Code
  (ohne Hinweis). Ebenso ein SVG, das `to_drawing` nicht kennt. Eine Zeitüberschreitung ist
  immer ein Fehler. Fehlt `mmdc` oder startet Chromium nicht: `RendererUnavailableError`, der
  Block bleibt Code mit Hinweis.
- **Word:** setzt das Diagramm als Bild (SVG mit PNG-Ersatz, siehe
  [Grafiken in Word](#grafiken-in-word-e03-s04)); mmdc zeichnet dafür mit Word-Textfarbe.
- `MermaidRenderer.authoring_guide` ist der Abschnitt `## Diagramme` für die Authoring Guides.
- Jeder Block startet ein Chromium (hier etwa 0,7 s).

### SVG → `Drawing`

`pta_documents.drawing.svg.to_drawing(svg)` (Port von DocLibs `SvgDrawing`, `SvgGeometry`,
`SvgStyle`; Module `drawing/svg.py`, `svg_geometry.py`, `svg_style.py`) liest Grundformen,
Pfade (alle Befehle, Bögen und Quadratische werden kubisch), Marker (auch mit `viewBox`),
Text mit `tspan`-Zeilen und fetten Teilen (`em`, `dominant-baseline`), Gruppen mit
Transformationen (auch die CSS-Eigenschaft `transform` mit `transform-origin`), Verläufe (die
erste Farbe), Deckkraft (mit Weiß gemischt) und `fill-rule`. CSS: die Regeln aus `<style>`
nach Wichtigkeit, Spezifität und Reihenfolge (Selektoren über `cssselect`, Extra `diagrams`),
dann `style`-Attribut, dann Präsentationsattribute; Werte mit `var()`, `color-mix()`, Hex,
`rgb()`/`rgba()`, `hsl()`/`hsla()`, Farbnamen, `currentColor`, `px`/`pt`/`em`/`rem`.
Schatten (`filter`), `symbol` und `@keyframes` fallen weg. **Alles andere wirft
`SvgDrawingError`** (ein `ValueError`) statt es wegzulassen: `foreignObject`, `<image>`,
`<use>`, `clip-path`, `mask`, gedrehter Text, unbekannte Farben, Einheiten oder At-Regeln.

## Schriften für PDF und SVG (E01-S03)

Word und PowerPoint nehmen die installierten Schriften und betten nichts ein. Wer Schriftdateien
braucht (PDF-Generator, SVG → PNG), holt sie aus `pta_documents.design.fonts` (Extra `pdf` oder
`svg`, wegen fontTools; der Kern importiert das Modul nie):

```python
from pta_documents.design import fonts
from pta_documents.design.fonts import FontFace

schriften = fonts.resolve()  # Segoe UI aus dem System, sonst Selawik
schriften = fonts.bundled()  # nur die mitgelieferten Schriften
schriften.name  # "Segoe UI" oder "Selawik"
datei = schriften.file(FontFace.BOLD)  # FontFile(family, content, synthetic_italic)
schriften.width("Text", FontFace.REGULAR, 10)  # Breite in Punkt, ohne Kerning
schriften.has_glyph(0x20AC, FontFace.LIGHT)  # nur BMP; U+00A0 fehlt in Selawik
```

- **Schnitte** (`FontFace`): `REGULAR`, `BOLD`, `ITALIC`, `BOLD_ITALIC`, `LIGHT`, `MONO`,
  `MONO_BOLD`, `QUOTE`.
- **Mitgeliefert** (OFL 1.1, Lizenztexte `OFL-*.txt` neben den Dateien): Selawik Regular, Bold,
  Light; Inconsolata Regular und Bold für Code; Gelasio Italic für Zitate (nur für SVG/PNG von
  Folieninhalten — Word und PDF setzen Zitate nach der Word-Vorlage). Selawik hat keine Kursive:
  `ITALIC`/`BOLD_ITALIC` sind Regular/Bold mit `synthetic_italic=True`; die PDF-Engine schrägt sie
  um `SYNTHETIC_ITALIC_ANGLE` (12°).
- **Aus dem System** (`resolve(system_fonts=True, search_dirs=None)`): gesucht wird rekursiv und
  ohne Rücksicht auf Groß/Klein in `%WINDIR%\Fonts`, `%LOCALAPPDATA%\Microsoft\Windows\Fonts`,
  `/usr/share/fonts`, `/usr/local/share/fonts`, `~/.local/share/fonts`, `~/.fonts`,
  `/Library/Fonts`, `~/Library/Fonts` (oder nur in `search_dirs`). Eine Familie ersetzt die
  mitgelieferte nur ganz: Segoe UI mit `segoeui.ttf`, `segoeuib.ttf`, `segoeuii.ttf`,
  `segoeuiz.ttf` **und** `segoeuil.ttf`; Consolas mit `consola.ttf` und `consolab.ttf`; Georgia
  kursiv mit `georgiai.ttf`. Dateien, die nicht eingebettet werden dürfen (`fsType`
  „eingeschränkt"), CFF-Umrisse haben oder nicht lesbar sind, zählen als fehlend. Es gibt keinen
  Cache; `system_fonts=False` ergibt `bundled()`.
- **CSS** für SVG: `CSS_FAMILY` (`Segoe UI, Selawik, sans-serif`), `CSS_MONO_FAMILY`
  (`Consolas, Inconsolata, monospace`), `CSS_QUOTE_FAMILY` (`Georgia, Gelasio, serif`).
- Fehlt fontTools, nennt der `ImportError` die Extras; `bundled()` und `fonts.read(name)`
  (Bytes einer mitgelieferten Datei) gehen auch ohne.

## PDF-Layout-Engine (E05-S02)

Die Layout-Engine setzt den Markdown-Rumpf auf Seiten im Design der PTA-Word-Vorlage; der
PDF-Generator (`PdfGenerator`, oben) ruft sie auf und macht aus dem Ergebnis PDF/A. Sie liegt in
`pta_documents.generation.pdf.layout` (Extra `pdf`) und arbeitet auf reportlabs Platypus:

```python
from pta_documents.generation.common import generated_images, layout_syntax
from pta_documents.generation.pdf.layout import LayoutSettings, PdfInfo, layout
from pta_documents.markdown.parser import create_parser

tokens = create_parser().parse(front.body)
layout_syntax.check(tokens, DocumentFormat.PDF, front.body_line, heute)
dokument = generated_images.add_generated(dokument, tokens, DocumentFormat.PDF, front.body_line)
typeset(tokens, sprache)           # wenn die Typografie an ist
einstellungen = LayoutSettings(
    variant=WordVariant.PORTRAIT,  # Vorlage: Formatvorlagen und Satzspiegel
    language=Language.DE,          # „Tabelle"/„Abbildung", Hinweis-Wörter
    fonts=None,                    # None: Selawik/Inconsolata; fonts.resolve() für Segoe UI
    justify=False,                 # Blocksatz (Beschriftungen, Zellen, Code bleiben links)
    highlight=True,                # Code farbig (E17-S02)
    image_converters=(), code_block_renderers=(),
    line_offset=front.body_line,
    status_labels={},              # FrontMatter.status_labels(), für Statusbeschriftungen
)
pdf = layout(tokens, dokument, einstellungen, notes, PdfInfo(title=..., author=...))
pdf.content, pdf.pages  # PDF-Bytes (noch kein PDF/A, das macht pdfa.to_pdfa), Seitenzahl
```

`layout(…, decorate=f)` setzt die Seiten zweimal: zuerst, um sie zu zählen, dann mit
`f(canvas, seite, seitenzahl)` am Ende jeder Seite (für Kopf- und Fußzeile, E05-S03). Wer
eigene Flowables davor- oder dahintersetzen will, nimmt die beiden Hälften:
`build_story(tokens, dokument, prepare(einstellungen), notes)` und `render(story, info, decorate,
page_count)`. `render(…, underlay=g)` ruft `g(canvas, seite, seitenzahl)` am **Anfang** jeder
Seite, also hinter dem Inhalt (Wasserzeichen, E12-S03).

- **Werte aus der Vorlage:** `pta_documents.design.word_styles.read(variante)` liest Größe,
  fett, kursiv, Versalien, Farbe, Abstand vor/nach, Zeilenabstand, Einzug/hängend und „mit
  nächstem Absatz zusammen" jeder Formatvorlage aus `styles.xml` (über `basedOn`,
  `docDefaults` und das Theme), die Einzüge nummerierter Vorlagen aus `numbering.xml`, die
  Tabellenvorlage `PTA` und den Satzspiegel aus `w:sectPr`. Was die Vorlagen nicht haben, kommt
  wie im DOCX aus `design/word.py` (Code, Zitat, Hinweis-Boxen).
- **Zuordnung wie im DOCX:** `#`–`###` → Überschrift 1–3 mit Nummer (`1`, `1.1`, `1.1.1`) im
  hängenden Einzug, tiefere → „Zwischenüberschrift" in Versalien; Überschriften in Containern →
  „Standard fett"; ein ganz fetter Absatz → „Standard fett"; `Tabelle: …` nach einer Tabelle →
  „Tabelle n: …", ein Bild allein mit Titel oder Alt-Text → „Abbildung n: …" (beide in
  „Beschriftung"); Listen beginnen bei 1, die äußere Liste bestimmt die Vorlage
  („Aufzählungszeichen" oder „Listenabsatz"), tiefere Ebenen nehmen deren Ebenen 2 und 3.
  `#` beginnt keine neue Seite.
- **Seitenumbruch:** Überschriften (auch mehrere hintereinander) und der Titel „Standard fett"
  über einer Tabelle stehen nie allein am Seitenende — es muss der Anfang des Folgenden
  mitpassen (zwei Zeilen eines Absatzes, Kopf und erste Zeile einer Tabelle, ein ganzes Bild).
  Kein Absatz lässt eine einzelne Zeile oben oder unten auf einer Seite. Listenzeichen gehen mit
  der ersten Zeile. Tabellen wiederholen ihren Kopf und teilen zu hohe Zeilen. Abstand nach und
  Abstand vor addieren sich wie in Word.
- **Bilder:** 96 dpi (ein Pixel = 0,75 pt), `{scale=0.5}` nach dem Bild (oder noch im Titel) skaliert, sonst werden sie
  nur verkleinert (ein QR-Code ist wie in Word 3 cm breit, mal `scale`): auf die Satzspiegelbreite, auf 80 % der Satzspiegelhöhe und so weit, dass sie
  mit der Überschrift davor auf eine Seite passen. PNG und JPEG direkt, GIF/BMP/TIFF/WebP über
  Pillow, alles andere über die Bildkonverter. Mehrere Bilder in einem Absatz stehen
  nebeneinander (bis vier je Reihe).
- **Listenzeichen** sind gezeichnet: Ebene 1 ■ in PTA-Blau, Ebene 2/3 ― schwarz, Aufgaben ☐/☒
  als Kästchen.
- **Lesezeichen** für Überschrift 1–3 mit ihrer Nummer, beim Öffnen sichtbar. **Links:**
  `[x](#anker)` springt auf die Überschrift mit dem GitHub-Anker (`markdown/anchors.py`:
  Kleinbuchstaben, Satzzeichen weg, Leerzeichen → `-`, Wiederholungen `-1`, `-2`); externe Links
  brauchen eine absolute URL (`https:`, `mailto:` …), sonst bleibt nur der Text.
- **Fußnoten** stehen am Fuß der Seite mit dem Verweis („Fußnotentext", Trennlinie 2 Zoll);
  passen sie mit dem Anfang des Absatzes nicht mehr hin, wandern beide auf die nächste Seite.
- **Schriften:** jede Schrift wird bei reportlab unter `PTA-<sha8>` ihres Inhalts registriert
  (`layout/fonts.register`, die einzige Registrierung).
  Fehlende Leerzeichen-Glyphen (U+00A0, U+202F, U+2011 in Selawik) leihen sich die Glyphe von
  Leerzeichen bzw. Bindestrich (`truetype.with_aliases`); Kursiv ist eine schräggestellte Kopie
  (`truetype.slanted`, 12°). Zeilenhöhe „einfach" = Windows-Ascent + -Descent der Schrift wie
  in Word.
- **Seitenrahmen:** Deckblatt, Kopf-/Fußzeile und Inhaltsverzeichnis setzt `frame.lay_out`
  (E05-S03, unten) um die Engine herum; `render(…, first_top_pt=…)` lässt die erste Seite tiefer
  beginnen, `RenderedPdf.heading_pages` nennt die Seite jeder Überschrift 1–3 (nach Anker).
- **Grafiken und fehlende Zeichen** seit E05-S04, siehe
  [unten](#grafiken-und-fehlende-zeichen-im-pdf-e05-s04).
- **Noch nicht:** Silbentrennung; die Folien-Syntax (`cards`, `columns` …) zeigt wie in Word
  ihren Inhalt nacheinander, nicht als Boxen und Spalten.

## Grafiken und fehlende Zeichen im PDF (E05-S04)

- **Zeichnungen** (`DrawingGraphic` und `ChartGraphic` der Code-Block-Renderer, `::: timeline`,
  `::: steps`, `::: riskmatrix`) setzt `layout/drawings.DrawingFlowable` als Vektoren auf den
  reportlab-Canvas: Formen als Pfade (Kurven, Strichmuster, runde Ecken und Enden, Füllregel
  `evenodd`), Texte als echter, durchsuchbarer Text in der Schrift des Dokuments (Segoe UI bzw.
  Selawik, fette Spans fett, `mono` in der Codeschrift). Eine Zeile mit `max_width` wird mit der
  echten Schrift gemessen, bis auf 70 % verkleinert und dann nach ihrem `anchor` gesetzt.
  Tooltips und Hotspots gibt es nur im SVG. Größe: 0,75 pt je Pixel, nur verkleinert — auf die
  Satzspiegelbreite, auf 80 % der Satzspiegelhöhe und so, dass die Zeichnung mit den
  Überschriften davor (und ihrer Beschriftung) auf eine Seite passt; links wie ein Bild in Word,
  nie geteilt.
- **Charts** (`chart`) zeichnet das PDF aus `ChartGraphic.drawing` (`charts/drawing.py`) mit
  Titel, Einheit, Achsen, Legende und Quelle in der Zeichnung; **Finanzdiagramme** und
  **Mermaid** sind `DrawingGraphic`. Ein Absatz `Abbildung: …` direkt nach dem Codeblock (gleiche
  Ebene) wird die Beschriftung „Abbildung n: …" und bleibt bei der Grafik; ohne ihn hat ein
  Chart keine Beschriftung (der Titel steht schon in der Zeichnung — Word nimmt den Titel).
  Ein `ImageGraphic` wird wie ein Bild gesetzt.
- **Zeitstrahl** über `drawing.schedule.timeline(…, Satzspiegelbreite)`, „heute" ist
  `LayoutSettings.today` (Front Matter `datum`, sonst heute). **Gantt** als Tabelle im
  PTA-Tabellenstil wie in Word: Spaltenanteile `word.GANTT_NAME_SHARE`/`GANTT_OWNER_SHARE`,
  Laufzeit PTA-Blau (anderer Verantwortlicher Hellblau), Meilenstein als dunkelblaue Raute
  (gezeichnet — ◆ fehlt den Schriften), die Spalte von heute mit 1,5 pt Linie rechts.
- **Schrittfolge** wie Word: Texte unter den Pfeilen in 12 pt, sonst 10 pt, passen sie auch so
  nicht, zeigt die Zeichnung nur die Titel und die Texte folgen als Liste („**Titel**: Text").
  **Risikomatrix** in natürlicher Größe, die Legende darunter als PTA-Tabelle.
- **Icons:** im Text ein PNG (`word.ICON_PIXELS`, PTA-Blau) 10 pt hoch auf der Grundlinie;
  beginnt jeder Punkt einer Liste mit einem Icon, ist es das Aufzählungszeichen (11 pt,
  `MarkerKind.ICON`). Die Absätze lesen `<img src="pta-icon:name"/>` über einen eigenen
  reportlab-Parser (`flowables._Parser`), weil reportlabs `<img>` nur Dateien und URLs nimmt.
- **Bilder anderer Formate** (SVG) wandelt das PDF in **dreifacher** natürlicher Größe
  (`story.IMAGE_SCALE`, ≈ 288 dpi) und setzt sie in natürlicher Größe; ohne passenden Konverter
  ein Fehler mit Pfad und Hinweis auf das Extra.
- **Folien-Syntax:** `layouts.md` (`tests/generation/common/samples/`) erzeugt auch als PDF ohne
  Hinweise; falsche Container, Alerts und Attribute werfen dieselben Fehler wie in Word und
  PowerPoint (`tests/generation/common/test_layout_syntax.py`, parametrisiert für alle drei).
- **Fehlende Zeichen:** siehe [Markdown → PDF](#markdown--pdf-e05-s01-e05-s02).
- Ein PDF meldet damit keinen `code-not-drawn` mehr außer für einen `mermaid`-Block ohne
  eingerichtetes mermaid-cli (wie Word); `samples/` erzeugt als PDF ohne Hinweise
  (`tests/generation/pdf/test_generator.py`).

## PTA-Seitenrahmen im PDF (E05-S03)

Was in Word um den Text jeder Seite steht, zeichnet der PDF-Generator nach der gewählten Vorlage
(`vorlage`): `hoch`, `hoch-ohne-deckblatt`, `quer`, `quer-ohne-deckblatt`.

- **Werte aus der Vorlage:** `pta_documents.design.word_frame.read(variante)` liest aus
  `word/header*.xml`, `word/footer*.xml` und dem `w:sectPr` des Rumpfs, was Word zeigt:
  `PageFrame(page, other, first)` mit je einem `PageKind(header, footer)` für die erste Seite
  (nur mit `w:titlePg`, also `hoch` und `quer`) und alle anderen. Ein `Band` enthält die Blöcke
  (`FrameTable` mit Zeilen und Zellen, `FrameParagraph` mit Formatvorlage, direkter Formatierung
  und Feld `FrameField`: Titel, Untertitel, Firma, Stand, Seite), das Logo (`Box` aus dem
  `wp:anchor` der Grafik) und die Linien (`FrameRule` mit Verlauf aus `a:gradFill`, Strich aus
  `a:lnRef` des Themes). Positionen in Punkt ab der linken oberen Ecke. Welches Feld ein Absatz
  ist, sagt der Platzhaltertext der Vorlage („Titel des Dokuments", „PTA IT-Beratung", „Stand:",
  `PAGE`). `body_top(frame, seite, zeilenfaktor)` ist, wo der Text einer Seite beginnt: am
  oberen Rand, oder tiefer, wenn die Kopfzeile darüber hinausreicht — so setzt Word das
  Deckblatt (`hoch` 8,50 cm, `quer` 6,79 cm).
- **Kopfzeile** (jede Seite außer dem Deckblatt): Titel fett in PTA-Blau und darunter der
  Untertitel in „Kopfzeile" 10 pt, senkrecht mittig in der Kopfzeilentabelle (11,5 bzw.
  17,5 cm); was nicht hineinpasst, endet mit „…". Ohne `untertitel` steht der Titel allein (der
  DOCX-Generator löscht den Absatz ebenso). Logo oben rechts (Hoch 2,22 × 1,28 cm, Quer 3,01 ×
  1,73 cm) als Vektorgrafik (`design.logos`, Logo `WORD`), einmal als Form-XObject eingebettet
  und auf jeder Seite verwendet; Verlaufslinie PTA-Blau → Hellblau (53 %) → transparent, das
  transparente Ende gegen Weiß gemischt.
- **Fußzeile:** Verlaufslinie, darunter die Zellen der Fußzeilentabelle in 6,5 pt — „PTA
  IT-Beratung" (`firma`) fett in PTA-Blau, „Stand: TT.MM.JJJJ" (`datum`, sonst der Tag von
  `PdfOptions.created`, sonst heute), „Seite n | m" fett in PTA-Blau; `n` und `m` zählen jede
  Seite, das Deckblatt eingeschlossen (wie `PAGE`/`NUMPAGES` in Word). Mit `sprache: en`
  „As of:" und „Page". Die Fußzeile endet im Fußzeilenabstand über dem unteren Seitenrand.
- **Deckblatt** (`hoch`, `quer`): auf Seite 1 nur Logo und Linie (Quer: bei 6,00 cm), keine
  Fußzeile; „Titel" 34 pt fett PTA-Blau, „Untertitel" 22 pt, „Autor" 14 pt mit „Autor, Ort,
  Datum" (jedes nur, wenn angegeben), dann Seitenwechsel — wie `write_cover` im DOCX.
- **Inhaltsverzeichnis** (`inhaltsverzeichnis: ja`): nach dem Deckblatt (ohne Deckblatt am
  Anfang) „Inhalt" in „Zwischenüberschrift", dann Überschrift 1 und 2 (wie `TOC \o "1-2"`) in
  „Verzeichnis 1/2": Nummer im hängenden Einzug, Text, Seitenzahl rechtsbündig, Ebene 2 mit
  Punkten davor; jeder Eintrag verlinkt die Überschrift. Danach Seitenwechsel.
- **Ablauf:** `frame.lay_out(tokens, dokument, LayoutSettings, FrameInfo, notes, PdfInfo)` setzt
  Deckblatt und Verzeichnis vor die Story der Engine und rendert, bis Seitenzahl und Seiten der
  Überschriften stabil sind (meist zwei Durchgänge, höchstens `MAX_PASSES`); `PageDecorator`
  zeichnet Kopf und Fuß jeder Seite (`decorate`). `FrameInfo` trägt Titel, Untertitel, Autor,
  Ort, Datum, Stand, Firma, `toc` und `marking` ([Kennzeichnung](#kennzeichnung-in-word-und-pdf-e12-s03),
  E12-S03: Text in `PageDecorator`, Wasserzeichen `Watermark` als `underlay`).

## Zeichenmodell und SVG (E02-S03)

Diagramme, Charts, Logos und später die visuellen Bausteine liegen als **`Drawing`** vor, bevor
ein Generator sie als Formen, Vektoren oder Bild ausgibt (`pta_documents.drawing`, reines
Python, kein Extra). Koordinaten sind CSS-Pixel (1 px = 0,75 pt) ab der linken oberen Ecke,
Farben `RRGGBB` ohne `#` aus `design.colors`:

```python
from pta_documents.design import colors
from pta_documents.drawing import (
    Drawing,
    DrawingHotspot,
    DrawingHover,
    DrawingPath,
    DrawingShape,
    DrawingText,
    ShapeKind,
    SvgOptions,
    TextAnchor,
    to_svg,
)

balken = DrawingShape(
    DrawingPath.rectangle(10, 20, 40, 60),
    colors.PTA_BLUE,
    None,
    0,
    kind=ShapeKind.RECTANGLE,
    hover=DrawingHover("Q1: 60", 30, 20),
)
beschriftung = DrawingText.line(30, 95, "Q1", 12, colors.TEXT_SLIDES, anchor=TextAnchor.MIDDLE)
punkt = DrawingHotspot(30, 20, 8, dot=colors.SIGNAL_RED, hover=DrawingHover("Ziel", 30, 20))
svg = to_svg(Drawing(120, 100, (balken, beschriftung, punkt)), SvgOptions(background=colors.WHITE))
```

- **Elemente:** `DrawingShape(path, fill, stroke, stroke_width, *, dash, kind, corner_radius,
  round_joins, even_odd, hover)` — `path` enthält immer den Umriss, `kind` (`PATH`,
  `RECTANGLE`, `ROUNDED_RECTANGLE`, `ELLIPSE`) erlaubt eigene Formen; `even_odd` setzt die
  Füllregel `evenodd` (PTA-Ergänzung für Logos und Mermaid). `DrawingPath(segments)` aus
  `MoveTo`, `LineTo`, `CubicTo`, `ClosePath`, mit `bounds` (Kontrollpunkte eingeschlossen) und
  `DrawingPath.rectangle(...)`. `DrawingText(x, baseline, spans, size, color, *, anchor,
  max_width, mono, hover)` ist eine Zeile aus `DrawingSpan(text, bold, color)`;
  `DrawingText.line(...)` für eine Zeile in einem Schnitt. `DrawingHotspot(x, y, radius, *,
  dot, dot_radius, hover)` ist eine unsichtbare Trefferfläche nur für einen Tooltip.
- Alle Typen sind unveränderliche Dataclasses mit Tupeln: Zeichnungen sind nach Inhalt gleich
  und hashbar.
- **`to_svg(drawing, options)`** schreibt ein eigenständiges SVG (`width`/`height` in Pixeln,
  passende `viewBox`). Jedes Element mit `hover` wird `<g class="chart-hoverable">` mit einem
  vorplatzierten `<g class="chart-tooltip">` (zentriert über dem Punkt, waagrecht auf der Fläche
  gehalten); ein Inline-`<style>` zeigt ihn bei `:hover` — **kein Skript**. Die Klassennamen
  (`chart-hoverable`, `chart-tooltip`, `chart-tooltip-bg`, `chart-tooltip-text`,
  `chart-hover-dot`) bleiben wie in DocLibs, eine Seite kann sie umgestalten.
- `SvgOptions(font_family, mono_family, background, tooltip_fill, tooltip_text)`: Schriften
  standardmäßig `fonts.CSS_FAMILY`/`CSS_MONO_FAMILY` — nur Familiennamen, nichts eingebettet
  (Entscheidung 2026-11-07); Tooltip `TEXT_SLIDES` mit weißer Schrift, ohne Hintergrund
  transparent.
- Text wird nicht gemessen: eine Zeile, die nach `estimate_width()` (0,58 × Größe je Zeichen)
  breiter als `max_width` ist, wird kleiner gesetzt, höchstens auf 70 %. Zahlen haben höchstens
  zwei Nachkommastellen (nie `-0`); Texte werden XML-sicher (Steuerzeichen außer Tab/LF/CR
  entfallen). Eine Farbe, die nicht `RRGGBB` ist, oder eine nicht endliche Zahl wirft
  `ValueError` (Programmierfehler des Renderers).
- Ausgabe als PNG über `pta_documents.svg.to_png(to_svg(drawing))` ([SVG-Bilder](#svg-bilder-e06-s04));
  die Tooltips sind im PNG unsichtbar. Als PowerPoint-Formen seit E06-S02, in Word als Bild seit
  E03-S04, SVG → `Drawing` (Mermaid) seit E06-S03, als PDF-Vektor seit E05-S04.

## SVG-Bilder (E06-S04)

Ein SVG im Markdown (`![Plan](images/plan.svg)`) setzen Word und PowerPoint als **PNG in
doppelter Größe mit dem SVG daneben**: das PNG im `a:blip`, das SVG als eigener Bildteil
(`image/svg+xml`, `…/media/imageN.svg`) in der Erweiterung `asvg:svgBlip`
(`{96DAC541-7B7A-43D3-8B79-37D633B846F1}`). Office 2016 und neuer zeichnet das SVG scharf, ältere
Programme das PNG. Word setzt das Bild in seiner natürlichen Größe (höchstens Satzspiegelbreite)
mit „Abbildung n" wie jedes Bild; PowerPoint wie jedes Bild (Platzhalter, Bildreihe), ohne
Hinweis `image-enlarged`, weil das SVG in jeder Größe scharf ist. Dasselbe SVG steht nur einmal
in der Datei. Braucht das Extra `svg` (resvg-py, fontTools), das `./run.sh setup` installiert.

```python
from pta_documents.svg import PngOptions, SvgImageConverter, clean, is_svg, natural_size, to_png

natural_size(svg)  # (Breite, Höhe) in CSS-Pixeln
png = to_png(svg)  # doppelte Größe, transparent
png = to_png(svg, PngOptions(scale=3, background=colors.WHITE))
png = to_png(svg, PngOptions(width=600))  # Breite in Pixeln, Höhe folgt
```

- **Sicher:** jedes SVG geht vorher durch `clean()` (Port von DocLibs `SvgSanitizer`): entfernt
  `script`, `foreignObject`, DTD und Entitäten (nie aufgelöst, nichts geladen), Processing
  Instructions, Kommentare, jedes `href` außer `#…` und `data:`, externe CSS-`url()` (→ `none`)
  und `@import`. Eingebettet wird ebenfalls das bereinigte SVG. Die Umwandlung braucht kein Netz.
- **Größe:** `width`/`height` in `px` (oder ohne Einheit), `pt`, `pc`, `mm`, `cm`, `in`; fehlt
  eines oder ist es relativ (`%`, `em`), kommt es aus der `viewBox` (bzw. aus ihren Proportionen).
  Ohne Größe ein Fehler `it has no size: give it width and height, or a viewBox`. Höchstens
  `MAX_PIXELS` = 16 384 Pixel je Seite.
- **Schriften:** resvg lädt keine Systemschriften, sondern genau die mitgelieferten aus
  `design.fonts` (Selawik, Inconsolata, Gelasio). `sans-serif`, `serif`, Text ohne Familie und
  jede fehlende Familie (auch „Segoe UI", „Arial") werden Selawik, `monospace` Inconsolata — so
  ergibt dasselbe SVG auf jedem Rechner dasselbe PNG. `PngOptions(system_fonts=True)` bzw.
  `SvgImageConverter(system_fonts=True)` lädt zusätzlich die Systemschriften (z. B. Segoe UI
  unter Windows); das PNG hängt dann vom Rechner ab.
- **Erkennung** (`is_svg`): Typ `image/svg+xml`, Endung `.svg` oder Inhalt, der mit `<svg` bzw.
  `<?xml … <svg` beginnt.
- **Fehler:** `DocumentConversionError` mit Format `svg`; `to_png` meldet `The SVG cannot be
  converted: …`, der Konverter im Generator `The image 'images/plan.svg' cannot be converted: …`.
  Ein Maßstab ≤ 0 oder ein Hintergrund, der nicht `RRGGBB` ist, wirft `ValueError`.
- **PDF** (seit E05-S02): das PNG des Konverters (Maßstab 2, wie in Word) in natürlicher Größe;
  die dreifache Größe (≈ 288 dpi) aus der Antwort in E06-S04 ist noch nicht umgesetzt.

## QR-Codes (E11-S04)

Eine Bildreferenz mit dem Schema `qr:` ist kein Pfad in den Ressourcen, sondern ein QR-Code, den
der Generator selbst erzeugt — in Word und PowerPoint:

```markdown
![Zur Umfrage](qr:https://umfrage.example/abc "https://umfrage.example/abc")
![WLAN](<qr:WIFI:T:WPA;S:Mein Netz;P:geheim;;> "Gäste-WLAN"){scale=0.5}
```

- **Inhalt:** alles nach `qr:` — URL, `mailto:`, `tel:`, WLAN-Zugang (`WIFI:T:WPA;S:…;P:…;;`)
  oder Text; höchstens 1 000 Zeichen. Leerzeichen gehen nur in `<…>` oder als `%20`.
  markdown-it schreibt Linkziele %-kodiert: `http:`, `https:` und `mailto:` bleiben so (gültige
  URLs), alles andere wird dekodiert (`S:Mein%20Netz` → „Mein Netz").
- **Bild:** PNG mit mindestens 1 000 Pixeln Kante, PTA-Blau auf Weiß, Ruhezone 4 Module,
  Fehlerkorrektur mindestens M (segno hebt sie an, wo das nichts kostet), nie ein Micro-QR-Code.
  Das PNG trägt die Auflösung, die es 3 cm breit macht.
- **Word:** 3 × 3 cm, mit „Abbildung n" aus Titel oder Alt-Text wie jedes Bild. Den Link als
  Titel zu schreiben, macht ihn auch gedruckt lesbar.
- **PowerPoint:** wie jedes Bild (Platzhalter des Layouts, Bildreihe, Flow-Folie), aber in den
  Bildplatzhalter **eingepasst und zentriert, nie beschnitten**.
- **`{scale=N}`** nach dem Bild (0 < N ≤ 5, Komma oder Punkt) ändert die Größe: in Word das
  N-Fache von 3 cm (höchstens Satzspiegelbreite), auf Folien das N-Fache der eingepassten Größe
  (höchstens diese). Seit E15-S04 gilt das für jedes Bild (siehe
  [Bildattribute](#bildattribute-e15-s04)); `scale=N` im Titel wirkt noch bis 2027-11, mit
  Hinweis `image-scale-in-title`, und erscheint nicht in der Beschriftung. QR-Codes nehmen weder
  `.round` noch `.grey` (Fehler) und werden immer eingepasst.
- **Fehler mit Zeile:** `Line N: The QR code has 1001 characters, more than 1000. …`,
  `Line N: The QR code has no content …`, `Line N: 'scale=0' is no scale …`. Andere Schemata
  (`foto:…`) bleiben, was sie waren: ein Pfad, den die Ressourcen haben müssen.
- **Prüfen:** `style-image-source` verlangt für QR-Codes keine Quelle.
- **Rundreise:** die Konverter lesen ein gewöhnliches PNG zurück (`![Zur Umfrage](images/…png)`),
  nicht `qr:…`.
- **PDF** setzt das PNG wie Word 3 cm breit, mal `scale`.

```python
from pta_documents.generation.common.generated_images import (
    add_generated, is_generated, qr_png, resolve,
)

is_generated("qr:https://pta.de")  # True
png = qr_png("https://pta.de")  # PNG-Bytes
resource = resolve("qr:https://pta.de", DocumentFormat.DOCX)  # DocumentResource unter "qr:…"
```

Alle Generatoren rufen `add_generated(document, tokens, format, line_offset, notes)` nach
`layout_syntax.check` auf; es liest die Bildattribute, gibt das Dokument mit den erzeugten
Bildern als zusätzliche Ressourcen zurück (eine eigene Ressource mit dem Pfad `qr:…` geht vor)
und legt die Bildstile an (siehe [Bildattribute](#bildattribute-e15-s04)). Der PDF-Generator
übergibt noch keine `notes`.

## Bildattribute (E15-S04)

Geschweifte Klammern **direkt** nach einem Bild (ohne Leerzeichen) steuern den Ausschnitt, die
Größe und den Stil — eine Quelle für alle Formate:

```markdown
![Porträt](images/foto.jpg){focus=top}
![Porträt](images/foto.jpg){focus=30%,20%}
![Plan](images/plan.png){fit=contain}
![Erika Mustermann](images/erika.jpg){.round focus=50%,40%}
![Archivbild](images/alt.jpg){.grey scale=0.5}
```

| Attribut | Werte | Wirkung |
| -------- | ----- | ------- |
| `focus=` | `center` (Standard), `top`, `bottom`, `left`, `right`, `x%,y%` (Punkt von links/oben, auch in `"…"`) | PowerPoint: der Bildplatzhalter beschneidet so, dass der Punkt im Ausschnitt bleibt (am Rand geklemmt); `.round`: Mitte des Kreises. Word/PDF: kein Beschnitt, wirkungslos (kein Fehler) |
| `fit=` | `cover` (Standard, füllen und beschneiden), `contain` | PowerPoint: `contain` passt das ganze Bild zentriert in den Platzhalter ein (der Rest zeigt den weißen Folienhintergrund); Word/PDF wirkungslos |
| `scale=` | 0 < N ≤ 5 | Word/PDF: N-fache Größe (höchstens Satzspiegel); Folien: N-fache eingepasste Größe, nie größer (in Bildreihen, Flow-Folien, eingepasst); ein Platzhalter, der beschneidet, bleibt gefüllt |
| `.round` | – | rund um den Fokus: PowerPoint als Ellipsengeometrie am Bild (quadratischer Ausschnitt über `a:srcRect`, bearbeitbar, kein `image-cropped`); Word/PDF als PNG mit Kreismaske im Alphakanal (`<name>-round.png`) |
| `.grey` | – | Graustufen-PNG (`<name>-grey.png`), in allen Formaten |

Unbekannte Attribute und Werte sind Fehler mit Zeile und den gültigen Werten (`Line 7: Unknown
image attribute '.shadow' in '{.shadow}'. Valid attributes: focus=…, fit=cover|contain, scale=N,
.round, .grey.`); ebenso `scale` im Titel und in den Klammern zugleich, ein Stil an einem
QR-Code und ein Stil an einem Bild, das Pillow nicht liest (SVG: `… .grey takes PNG, JPEG, GIF,
BMP, TIFF and WebP …`). `image-cropped` schlägt `{focus=…}` und `{fit=contain}` nur vor, wenn
kein Fokus gesetzt ist.

- **Bausteine:** `markdown/image_attributes.py` (Inline-Regel nach dem Bild, Text der Klammern in
  `Token.meta[ATTRIBUTES]`; eigene Regel statt `mdit_py_plugins.attrs`, weil dort `%` einen
  Kommentar beginnt und `.`/`,` Anführungszeichen brauchen),
  `generation/common/image_attributes.py` (`ImageAttributes.parse`, `take`, `of`,
  `visible_window` für den Ausschnitt), `generation/common/image_styles.py` (`grey`,
  `round_png`, `apply`: neue `DocumentResource` neben dem Original, der Bild-Token zeigt darauf).
- **Rundreise:** die Konverter lesen das eingebettete Bild, wie es ist (grau bzw. in Word rund);
  Attribute kommen nicht zurück — außer `.round` aus PowerPoint (Bild mit `prst="ellipse"` →
  `![…](images/…){.round}`). PowerPoint bettet das ganze Bild ein; der Ausschnitt geht verloren.

## Zeitstrahl und Gantt (E15-S01)

`::: timeline` macht aus einer Liste von Terminen einen Zeitstrahl, `::: gantt` aus einer Tabelle
einen Projektplan — ohne Extra (außer dem Bild des Zeitstrahls in Word) und im PTA-Design:

```markdown
::: timeline
- 2026-01: Kick-off
- 2026-Q2: Analyse abgeschlossen {.done}
- 15.09.2026: Go-live
- 2027: Betrieb
:::

::: gantt raster=monat
| Vorgang   | Start      | Ende       | Wer   |
| --------- | ---------- | ---------- | ----- |
| Analyse   | 2026-01-12 | 2026-02-27 | PTA   |
| Abnahme   | 2026-07-01 | 2026-07-15 | Kunde |
| Go-live   | 2026-07-20 | 2026-07-20 | PTA   |
:::
```

- **Termine:** Jahr (`2026`), Monat (`2026-03`), Quartal (`2026-Q2`), Tag (`2026-03-15` oder
  `15.03.2026`) oder `heute` (auch `today`). **Heute** ist das Front-Matter-`datum`, ohne
  `datum` der Tag des Erzeugens. Im Gantt ist der Start der erste, das Ende der letzte Tag des
  Termins (`2026-03` bis `2026-04` = 1. März bis 30. April).
- **Zeitstrahl:** eine Liste mit 2–8 Einträgen `Termin: Text`, aufsteigend; `{.done}` am Ende
  markiert Erledigtes. Die Marken stehen gleichmäßig verteilt auf einer Linie `AFAFAF` über die
  volle Breite, erledigte und vergangene (Ende vor heute) in Grau `787878`, die übrigen
  PTA-Blau; der Termin steht 12 pt fett über der Linie, der Text 12 pt darunter (bis drei
  Zeilen). Wäre eine Beschriftung breiter als ihr Platz, stehen die Einträge abwechselnd unter
  und über der Linie (doppelter Platz). Über der Linie stehen die Jahre, ein Strich markiert
  den Jahreswechsel.
- **Gantt:** eine Tabelle Vorgang, Start, Ende und wahlweise eine vierte Spalte (frei benannt,
  z. B. Wer); 1–12 Vorgänge. Start = Ende ist ein **Meilenstein** (Raute `004676`).
  Abhängigkeiten gibt es nicht. Das Raster wird auf ganze Einheiten gerundet (Montag,
  Monatsanfang, Quartalsanfang): Wochen (Kalenderwochen `KW 03`) bis 16 Wochen Gesamtdauer,
  Quartale ab zwei Jahren, sonst Monate (`Jan 26`, `Feb`, …; das Jahr am Anfang und im Januar);
  ergäbe das mehr als 24 Spalten, nimmt es die nächstgröbere Einheit. `raster=woche|monat|quartal`
  erzwingt eine; mehr als 24 Spalten sind dann ein Fehler mit Hinweis.
  Vorgänge, deren vierte Spalte nicht der ersten Zeile gleicht, sind hellblau `9FD8FF` mit
  dunkler Schrift, die übrigen PTA-Blau. Englisch (`sprache: en`): `CW 03`, `Mar`.
- **PowerPoint:** eine Gruppe einzeln verschiebbarer Formen (`Drawing <n>`, Alternativtext =
  die Einträge) über die Breite ihres Platzes auf einer Flow-Folie (`Nur Titel`), gestapelt mit
  Text davor und danach; Höhe nach Inhalt (Zeitstrahl ≈ 3–4 cm, Gantt 0,9 cm je Vorgang plus
  Kopf). Die Größen schrumpfen nie; passt die Folie nicht, geht es auf „(Forts.)" weiter
  (`slide-split`/`slide-overfull`). Gantt: Namen 14 pt links, Rasterlinien `E6E6E6`,
  Kopf 10 pt `787878`, Balken 60 % der Zeilenhöhe, die vierte Spalte im Balken (sonst daneben),
  Heute-Linie `004676` gestrichelt, wenn heute im Raster liegt.
- **Word:** der Zeitstrahl als Bild in Satzspiegelbreite (SVG mit PNG, wie Zeichnungen aus
  E03-S04; braucht das Extra `svg`), der Gantt als **Tabelle** im Tabellenformat „PTA": Vorgang,
  wahlweise die vierte Spalte, dann eine schmale Spalte je Einheit; die Zellen der Laufzeit
  schattiert (`w:shd` `006FB9`, andere Verantwortliche `9FD8FF`), ein Meilenstein `◆` in
  `004676`, die Spalte von heute mit rechtem Rand `004676`.
- **Fehler mit Zeile** (in allen Formaten gleich, aus `layout_syntax.check`):
  `Line N: 'Mai 2026' is no date. …`, `… has 2 to 8 entries, not 9; split …`,
  `… The timeline goes from early to late …`, `… A '::: gantt' has 1 to 12 tasks, not 13; split …`,
  `… The grid of the '::: gantt' has 53 columns (woche), 24 at most; take a coarser grid …`,
  `… ends before it starts`, `Unknown attribute '{.x}' of a timeline entry. Valid: {.done}.`
- **Rundreise:** der PPTX-Konverter lässt die Formgruppe weg (wie alle `Drawing`-Gruppen), der
  DOCX-Konverter liest den Zeitstrahl als Bild und den Gantt als Markdown-Tabelle, gefüllte
  Zellen als `■`, Meilensteine als `◆`.
- **PDF** (seit E05-S04): der Zeitstrahl als Vektorgrafik in Satzspiegelbreite, der Gantt als
  Tabelle wie in Word (Meilenstein als gezeichnete Raute).

```python
from pta_documents.drawing import schedule as drawing
from pta_documents.generation.common import schedule

timeline = schedule.read_timeline(tokens, i, DocumentFormat.PPTX, line_offset, today)
gantt = schedule.read_gantt(tokens, i, DocumentFormat.DOCX, line_offset, today, Language.DE)
picture = drawing.draw(gantt, width=1179)  # Drawing in CSS-Pixeln
```

## Schrittfolge, Harvey Balls und Risikomatrix (E15-S02)

Drei Bausteine der Beratungsfolie, in allen Formaten aus demselben Markdown:

```markdown
::: steps
### Analyse
Interviews und Ist-Aufnahme
### Konzept
### Umsetzung {.current}
In Sprints
:::

| Kriterium | Option A | Option B |
| --------- | -------- | -------- |
| Kosten    | [3/4]    | [1/4]    |

::: riskmatrix green=4 yellow=12
| Nr | Risiko    | Wahrscheinlichkeit | Auswirkung | Maßnahme   |
| -- | --------- | ------------------ | ---------- | ---------- |
| 1  | Ausfall   | 2                  | 4          | Vertretung |
:::
```

- **Schrittfolge `::: steps`:** ein `###` je Schritt, darunter höchstens ein Absatz (der Text);
  3 bis 6 Schritte, sonst Fehler (mehr: auf zwei Folien verteilen). Gezeichnet als Pfeile
  (Chevrons, der erste mit gerader linker Kante) über die volle Breite, 1,6 cm hoch, Titel 16 pt
  fett im Pfeil (bis zwei Zeilen, längere kleiner bis 70 %), Text 12 pt `404040` darunter.
  Füllung Hellblau `9FD8FF` mit Titel `004676`; `{.current}` an einem Schritt (höchstens einem)
  macht ihn PTA-Blau mit weißer Schrift und die Schritte davor Grau `E6E6E6` mit Titel `404040`.
  Auf dunklen Folien ist der Text weiß. **PowerPoint:** Gruppe mit den Autoformen `homePlate`
  und `chevron` (Spitze 35 % der Höhe). **Word:** Bild in Satzspiegelbreite (Extra `svg`); die
  Texte stehen bei 12 pt unter den Pfeilen, sonst bei 10 pt, und passen sie auch so nicht (ein
  Wort breiter als der Pfeil oder mehr als fünf Zeilen), zeigt das Bild nur die Titel und die
  Texte folgen als Aufzählung „**Titel**: Text". **PDF** (seit E05-S04) wie Word, die Zeichnung
  als Vektoren.
- **Harvey Balls:** eine Tabellenzelle (nicht im Kopf), die genau `[n/4]` enthält (`n` 0 bis 4).
  **PowerPoint:** über der leeren, zentrierten Zelle eine Gruppe `harvey-n` aus Kreis Ø 0,45 cm
  mit Rand `004676` 1 pt und PTA-blauer Tortenform (`pie`, ab zwölf Uhr im Uhrzeigersinn),
  `[4/4]` voll, `[0/4]` leer; der PPTX-Konverter liest die Gruppe wieder als `[n/4]` in ihre
  Zelle. **Word:** das Zeichen ○ ◔ ◑ ◕ ● in Segoe UI Symbol, 12 pt, PTA-Blau, zentriert; der
  DOCX-Konverter liest das Zeichen. **PDF:** als kleine Grafik in der Zelle (die PDF-Schriften
  haben die Zeichen nicht).
- **Risikomatrix `::: riskmatrix`:** genau eine Tabelle Nr, Risiko, Wahrscheinlichkeit,
  Auswirkung (je 1 bis 5) und wahlweise Maßnahme, 1 bis 15 Zeilen. Die Nummer ist Pflicht,
  eindeutig und höchstens drei Zeichen lang (`3`, `R3`). Die Überschriften der Spalten 3 und 4
  beschriften die Achsen (Wahrscheinlichkeit nach rechts, Auswirkung nach oben, 10 pt fett
  `787878`, mit Pfeil und den Zahlen 1–5). Zellen 1,6 cm, gefärbt nach dem Produkt W × A: bis
  `green` (Standard 4) grün, bis `yellow` (Standard 12) gelb-orange, darüber rot — die
  Signalfarben zu 35 % auf Weiß (`colors.tint`). Jedes Risiko ist ein Kreis Ø 0,6 cm `004676`
  mit weißer Nummer; mehrere in einer Zelle stehen nebeneinander, bei vielen enger und
  überlappend. `::: riskmatrix green=… yellow=…` (ganze Zahlen 1–24, `green` < `yellow`) stellt
  die Schwellen ein. **PowerPoint:** die Matrix als Formgruppe in natürlicher Größe links, die
  Legende Nr | Risiko | (Maßnahme) als PTA-Tabelle rechts daneben (1 cm Abstand); ist rechts
  weniger als eine Rasterspalte (7 cm) frei, steht sie darunter. **Word:** die Matrix als Bild in
  natürlicher Größe, die Legende als Tabelle „PTA" darunter; **PDF** ebenso, die Matrix als
  Vektoren (seit E05-S04). Rundreise: beide Konverter lesen
  die Legende als Tabelle; die Matrix ist im DOCX ein Bild, im PPTX entfällt sie.
- **Fehler mit Zeile** (in allen Formaten gleich, aus `layout_syntax.check`):
  `… A '::: steps' has 3 to 6 steps, not 7; put the procedure on two slides …`,
  `… Only one step is {.current} …`, `Unknown attribute '{.x}' of a step. Valid: {.current}.`,
  `… The Wahrscheinlichkeit of risk 1 is a whole number from 1 to 5, not '6'.`,
  `… The risk 'Ausfall' has no number …`, `… The number 2 is the risk 'Daten' already.`,
  `… The container '::: riskmatrix' takes green=… and yellow=… …`.

```python
from pta_documents.drawing import harvey, riskmatrix, steps as steps_drawing
from pta_documents.generation.common import risks, steps

read = steps.read_steps(tokens, i, DocumentFormat.PPTX, line_offset)
picture = steps_drawing.draw(read, width=1179)  # Drawing in CSS-Pixeln
matrix = risks.read_risk_matrix(tokens, j, DocumentFormat.DOCX, line_offset)
picture = riskmatrix.draw(matrix)  # natürliche Größe
ball = harvey.ball(3)  # [3/4]
```

Das Zeichenmodell kennt dafür die Formarten `ShapeKind.CHEVRON`, `HOME_PLATE` (Feld
`point_depth`) und `PIE` (Feld `angles`, Grad im Uhrzeigersinn ab drei Uhr); Konstruktoren in
`drawing.shapes` (`chevron`, `pie`). SVG zeichnet sie als Pfad, PowerPoint als Autoform mit
`adj`-Werten.

## Icons (E15-S03)

`:icon-check:` setzt ein Icon aus einer gebündelten Teilmenge der **Tabler Icons** (MIT,
Version in `design.icons.TABLER_VERSION`, Lizenz `design/icons/LICENSE-tabler-icons.txt` im
Paket). Die SVGs liegen unverändert in `src/pta_documents/design/icons/`, die Liste aller Namen
ist `design.icons.ICONS` (alle Namen auch in [ki-anleitung.md](ki-anleitung.md#icons-icon-name-word-und-powerpoint);
ein Test hält beide gleich). Ein neues Icon: die SVG aus `icons/outline/` des npm-Pakets
`@tabler/icons` dazulegen und den Namen in `ICONS` und der KI-Anleitung ergänzen.

```markdown
::: cards
### :icon-rocket: Start
Erste Ergebnisse nach sechs Wochen
:::

- :icon-circle-check: Ist-Aufnahme abgeschlossen
- :icon-clock: Konzept in Abstimmung

Der Server :icon-server: meldet sich stündlich.
```

- **Syntax:** eigene Inline-Regel (`markdown/icon.py`, Token `icon`, Name in `meta["name"]`);
  in Code-Spans und -Blöcken bleibt der Text stehen. `layout_syntax.check` prüft die Namen —
  ein unbekannter ist in allen Formaten ein Fehler mit Zeile und den drei ähnlichsten Namen
  (`Line 5: Unknown icon ':icon-chek:'. Did you mean :icon-check:, …?`).
- **Karte** (PowerPoint): steht das Icon am Anfang des `###`-Titels in `::: cards` (oder am
  Anfang eines Punkts der Listenform), wird es die Figur der Karte: eine Formgruppe
  `icon:<name>` von 1,2 cm über dem Titel, Strich in PTA-Blau, auf dunklen Flächen weiß. Icon
  und Kennzahl (`**26 %**`) in derselben Karte sind ein Fehler.
- **Liste:** beginnt **jeder** Punkt einer `-`-Liste mit einem Icon, wird es das
  Aufzählungssymbol — PowerPoint als Bild-Aufzählungszeichen (`a:buBlip`, PNG, 110 % der
  Schrift), Word als Bild 11 pt vor dem Text mit hängendem Einzug und Tabulator, die
  Nummerierung des Absatzes ausgeschaltet (`numId 0`). Sonst steht das Icon im Text.
- **Im Text:** Word setzt das Icon als Bild 10 pt hoch auf die Grundlinie. Auf Folien ist ein
  Icon im Text (Absatz, Titel, Tabelle, Notizen) ein Fehler mit Hinweis auf Karten und Listen;
  das PDF setzt es wie Word als Bild 10 pt hoch auf die Grundlinie (seit E05-S04); Word lässt
  Icons in Fußnoten mit Hinweis `code-not-drawn` weg.
- **Bilder:** `design.icons.loader.drawing(name, farbe, größe)` liest ein Icon als `Drawing`
  (nur `<path>`, Bögen werden Béziers; das unsichtbare Quadrat jedes Tabler-Icons entfällt),
  `design.icons.raster.png(name, farbe, pixel)` zeichnet es ohne Extra mit Pillow (Béziers in
  16 Stücken, 4-fach überabgetastet, transparent, byte-gleich). Word bekommt dieses PNG und,
  wenn das Extra `svg` installiert ist, die SVG in der Farbe daneben (`asvg:svgBlip`).
- **Rundreise:** Word-Bilder tragen die Bildbeschreibung `icon:<name>`, die Formgruppen auf
  Folien heißen so, die PNGs der Aufzählungszeichen tragen den Namen in einem PNG-Textfeld
  (`pta-documents-icon`) — die Konverter schreiben daraus wieder `:icon-name:`.

## Logos als SVG und PNG (E01-S04)

Die Vorlagen tragen das PTA-Logo nur als EMF. `./run.sh prepare-templates` wandelt es einmal in
SVG und PNG und legt die Dateien als Paketdaten in `src/pta_documents/design/logos/` ab;
`./run.sh prepare-templates --check` meldet, wenn sie nicht mehr zu `source-templates/` passen.
Zur Laufzeit wird nichts gewandelt, das Modul braucht kein Extra:

```python
from pta_documents.design import logos
from pta_documents.design.logos import Logo

logos.svg(Logo.WORD)  # Bytes des SVG
logos.png(Logo.SLIDES)  # 2000 px breit, transparenter Grund
logos.aspect_ratio(Logo.WORD)  # Breite / Höhe, ≈ 1,75
logos.size(Logo.WORD)  # Breite und Höhe der viewBox
logos.shapes(Logo.WORD)  # Vektorpfade (LogoShape: segments, fill, even_odd)
logos.drawing(Logo.WORD)  # als Drawing in viewBox-Einheiten
logos.drawing(Logo.WORD, width=120)  # auf 120 CSS-Pixel Breite skaliert
```

| `Logo` | Datei | Quelle | Farbe |
| ------ | ----- | ------ | ----- |
| `WORD` | `logo-word` | Kopfzeile der Word-Hochformatvorlage (alle vier gleich) | PTA-Blau `006FB9` |
| `SLIDES` | `logo-slides` | Folienlayout `Titelfolie mit Bild 01`, mit Slogan | weiß |
| `SLIDES_PLAIN` | `logo-slides-plain` | Folienlayout `Abbschlussfolie`, ohne Slogan | weiß |

- Gefunden werden die Logos **über die Beziehungen** (Kopfzeilen des Dokuments bzw. das
  EMF-Bild des benannten Layouts), nicht über Dateinamen.
- Der EMF-Leser (`tools/prepare-templates/emf.py`) kennt nur die Datensätze der PTA-Logos
  (Pfade, Bézierkurven, Polygone, Vollton-Pinsel, Null-Stift); alles andere bricht mit der
  Nummer des Datensatzes ab. Bringt eine neue Vorlage ein anderes EMF, muss er erweitert werden.
- Das Word-Logo ist im EMF `026FB9` gefüllt und wird auf das PTA-Blau gesetzt
  (Entscheidung 2026-11-07); jede Füllfarbe muss in `design.colors` stehen.
- Die SVGs enthalten nur `<path>` mit `d` (absolutes `M`/`L`/`C`/`Z`), `fill` und `fill-rule`;
  `shapes()` liest genau diese Teilmenge zurück; `drawing()` macht daraus ein `Drawing` (je
  Pfad eine gefüllte Form ohne Linie, `even_odd` aus `fill-rule`).
- Das englische Logo gibt es weiter nur als PNG (`templates.ENGLISH_LOGO`).
- Die PNGs rastert resvg (Extra `svg`) beim Vorbereiten; `--check` vergleicht PNGs nach Pixeln.

## Zielgruppenfassungen (E16-S01)

Eine Quelle, drei Fassungen (`generation/common/audience.py`, `Audience`):

| Fassung | interne Blöcke | Lösungen |
| ------- | :------------: | :------: |
| `kunde` (Standard) | – | – |
| `intern` | ✓ | – |
| `trainer` | ✓ | ✓ |

Syntax, in allen Formaten gleich:

- `::: internal` … `:::` — nur intern und beim Trainer.
- `{.internal}` als Zeile vor einem Block (Blockmarker wie `{.build}`, E09-S02) — der Block nur
  intern; auch vor `::: notes` erlaubt, nicht vor einer `#`/`##`-Überschrift.
- `{.internal}` als Überschriftenattribut an `#` (ganzes Kapitel bis zum nächsten `#`) und `##`
  (die Folie bzw. der Abschnitt bis zum nächsten `#`/`##`), Sprechernotizen eingeschlossen. Nicht
  an der ersten `#` einer Präsentation (Titelfolie) und nicht an Überschriften in Containern
  oder Zitaten.
- `::: exercise` — steht in jeder Fassung; `::: solution` — nur beim Trainer, steht direkt
  nach einem `::: exercise` oder darin, sonst `Line N: A '::: solution' needs a '::: exercise'
  right before it (or around it).`
- In den drei Containern keine `#`/`##`-Überschrift; ein anderer Blockmarker als `{.internal}`
  kann sie nicht markieren (er gehört hinein, vor den Block).

Die Fassung wählt `DocxOptions`/`PptxOptions`/`PdfOptions`/`HtmlDeckOptions(audience=…)` — sie
**geht dem Front Matter `fassung:` vor** (anders als die übrigen Optionen, damit
`--audience` wirkt); `None` (Standard) nimmt `fassung:`, sonst `kunde`. Ist die Fassung nicht
`kunde` und setzt das Front Matter kein `kennzeichnung:`, wird die Kennzeichnung `intern`
(Word/PDF statt `kein`, PowerPoint statt der Vorgabe der Vorlage).

Umsetzung: jeder Generator ruft nach `layout_syntax.check` (das die Syntax für alle Fassungen
prüft, `audience.check`) `audience.filter_tokens(tokens, audience, notes, format, line_offset)`
auf und arbeitet mit dem Rest weiter. Weggelassene Blöcke sind nicht im Dokument; die drei
Container selbst werden entfernt, ihr Inhalt steht eine Ebene höher, als wäre er ohne Container
geschrieben — Übung und Lösung bekommen **keinen eigenen Kasten**. `{.internal}` wird nach dem
Filtern aus `meta` genommen. Folgen: Kapitelnummern der Trennfolien und Foliennummern zählen
lückenlos, Konverter lesen nur, was da ist. Ein Hinweis `audience-omitted` nennt die Zahl der
weggelassenen Blöcke (ein Kapitel zählt als ein Block).

Werkzeug: `./run.sh generate … --audience kunde|intern|trainer|alle` schreibt `<name>.<format>`
für `kunde`, `<name>-intern.<format>` und `<name>-trainer.<format>` sonst (auch ohne
`--audience`, wenn `fassung:` es sagt; ebenso `generate-samples`); `alle` erzeugt jede Fassung,
deren Token-Strom sich von den vorigen unterscheidet (`audience.versions`), mindestens `kunde`.

## Schulungs-Zeitplan (E16-S02)

Minuten an Folien und Kapiteln ergeben einen Zeitplan (`generation/common/training_schedule.py`,
`Schedule`, `build`, `deck_schedule`; Zahlen und Uhrzeiten in `durations.py`):

```markdown
---
beginn: 09:00
laenge: 4h
---
# Schulung

## Agenda {.agenda dauer=5}

# Grundlagen {dauer=45}

## Begriffe {dauer=10}

## Beispiele

## Pause {.break dauer=15}
```

- `{dauer=…}` an `##`: Minuten der Folie (`5`, `90`, `4h`, `1h30`; auch `dauer="5"`). Eine
  geteilte Folie („(Forts.)") zählt einmal.
- `{dauer=…}` an `#`: Minuten des Kapitels; seine Folien ohne eigene Angabe teilen sich, was
  übrig bleibt, gleichmäßig in ganzen Minuten (Entscheidung 2026-11-07). Bleibt Zeit übrig, endet
  das Kapitel trotzdem erst nach seiner Dauer; brauchen die Folien mehr, gilt deren Summe (Hinweis
  `schedule-length`).
- Folien ohne Angabe in einem Kapitel ohne Angabe zählen 2 Minuten (die Faustregel von `check`)
  — Hinweis `schedule-missing`. Titelfolie, Trennfolien und Abschlussfolie zählen 0.
- `## Pause {.break dauer=15}` ist eine Pausenfolie auf `Zwischenfazit 01` (bzw. `layout="…"`
  der Zwischenfazit-Layouts) mit dem Titel „Pause · 15 min", ohne Inhalt. Eine Pause zählt nicht
  zur `dauer` ihres Kapitels; Pausen am Ende eines Kapitels stehen im Zeitplan hinter ihm.
- Nach der Abschlussfolie (`{.closing}`) und ab dem Backup (`{.backup}`, E16-S04, auch ohne
  Abschlussfolie) ist nichts mehr geplant: Backup-Folien bekommen keine Zeit und zählen nicht zu
  `laenge:`. Eine Pause oder `dauer` dort ist ein Fehler (`… stands in the backup {.backup},
  where nothing is planned any more …` bzw. `… backup slides get no time. Leave out dauer.`),
  ebenso `dauer` an der Abschlussfolie und `.break` ohne `dauer`, an `#` oder mit Inhalt, und
  jeder Wert, der keine Dauer ist (`Line 3: The heading attribute dauer=abc is no length of time; write minutes or
  hours and minutes, like '5', '90', '4h' or '1h30' (more than 0).`).
- Einen Zeitplan hat ein Deck, sobald es `dauer`, eine Pause, `beginn:` oder `laenge:` nennt. Er
  gilt für die Fassung (E16-S01): interne Folien zählen nur intern und beim Trainer.

Wirkung in PowerPoint (und im HTML-Deck):

- **Agenda** (`{.agenda}`, E04-S04) mit `beginn:`: jeder Punkt, der ein Kapitel nennt (Groß- und
  Kleinschreibung egal), bekommt dessen Uhrzeit vorangestellt („09:05 Grundlagen"); jede Pause
  wird ein eigener Punkt vor dem ersten Kapitel danach. Pausen zählen zu den höchstens acht
  Punkten. Eine Liste, die kein Kapitel nennt, bleibt, wie sie ist; ohne `beginn:` ändert sich
  nichts.
- **Sprechernotizen** nur in der Trainerfassung: erste Zeile „Geplant: 09:20–09:25 (5 min)"
  (englisch „Planned: …"), ohne `beginn:` relativ („+0:20–+0:25"); Trennfolien zeigen die Zeit
  ihres Kapitels. Fehlt `::: notes`, entsteht die Notizenseite nur dafür. Kunden- und interne
  Fassung bekommen keine Zeitnotiz. `./run.sh generate --audience alle` schreibt für ein Deck mit
  Zeitplan immer auch die Trainerfassung.
- Word und PDF nehmen `dauer` an und lassen es weg; eine Pause steht in Word als fetter Absatz
  (wie `.interim`), im PDF als Überschrift (wie die übrigen Folienarten).

`Schedule.to_markdown()` liefert die Tabelle Von | Bis | Dauer | Kapitel/Folie | Notizen (leer,
für den Trainer): Kapitel fett, Pausen `==markiert==`, angenommene Dauern „≈ 2 min", zuletzt die
Summe. `schedule_document(schedule, audience)` macht daraus ein Word-Markdown auf
`hoch-ohne-deckblatt` (Überschrift „Zeitplan: <Titel>", Beginn, geplante Länge und Summe;
Kennzeichnung `intern` außer für `kunde`).

Werkzeug:

```sh
./run.sh schedule samples/funktionen/zeitplan-praesentation.md [--out <ordner>] [--markdown] [--strict] [--audience kunde|intern|trainer]
```

schreibt `<name>-zeitplan.docx` neben die Präsentation (Standard: Trainerfassung), zeigt die
Hinweise des Decks und mit `--markdown` das Markdown des Dokuments. Ein genanntes Deck ohne
Zeitplan ist ein Fehler, in einem Ordner wird es übersprungen.

## Backup-Folien und Anhang (E16-S04)

Zwei Attribute an einer `#`-Überschrift machen sie und **jedes Kapitel danach** zu etwas anderem:

| Attribut | PowerPoint, HTML-Deck | Word, PDF |
| -------- | --------------------- | --------- |
| `# Backup {.backup}` | Backup: eine Trennfolie ohne Nummer mit dem Titel, danach die Folien; Kapitel danach ohne Nummer, nicht in der Agenda (`{.agenda}` ohne Liste), Fußzeile „PTA – <Titel> · Backup" | ignoriert, Hinweis `attribute-ignored` |
| `# Glossar {.appendix}` | ignoriert, Hinweis `attribute-ignored` | Anhänge A, B, C statt 1, 2, 3, darunter A.1, A.1.1; die Überschrift ist der erste Anhang (kein eigenes „Anhang"-Kapitel); nicht in der Agenda |

```markdown
# Vielen Dank! {.closing}

# Backup {.backup}

## Reservefolie: Details zur Migration
```

Regeln, in allen Formaten gleich geprüft (`backup.check`, aus `layout_syntax.check`), Fehler mit
`Line N: `:

- Jedes Attribut **höchstens einmal** (`{.backup} is on line 3 already. …`), nur an `#`, nicht an
  Überschriften in Containern.
- `{.closing}` steht **vor** `{.backup}`: Die Abschlussfolie hinter dem Backup ist ein Fehler
  (`The closing slide {.closing} goes before the backup …`). Ein Deck ohne Abschlussfolie darf ein
  Backup haben; es steht dann einfach am Ende.
- Nicht zusammen mit `.closing` oder `.internal` an derselben Überschrift (ohne die interne
  Überschrift wären die Kapitel danach in der Kundenfassung kein Backup bzw. Anhang mehr). Wer das
  Backup nicht beim Kunden zeigen will, markiert dessen Folien bzw. Kapitel nach dem
  `{.backup}`-Kapitel mit `{.internal}`; die Kundenfassung behält das Backup sonst.
- `{.backup}` und `{.appendix}` dürfen an derselben Überschrift stehen (eine Quelle für Deck und
  Bericht); jedes Format meldet dann das andere als `attribute-ignored`.

PowerPoint: Die Trennfolie des Backups heißt `Backup` (`p:cSld/@name`, `design.slides.BACKUP_SLIDE_NAME`);
daran und an „erste Folie hinter der Abschlussfolie" (`design.slides.backup_start`) erkennen das
HTML-Deck, `check` und der PPTX-Konverter, wo das Backup beginnt. Das HTML-Deck zeigt Backup-Folien
nicht in der Kapitelanzeige; die Fortschrittsanzeige ist auf der Abschlussfolie voll (`mainSlides`
im `data-config`), Tastatur und `#n` erreichen die Folien dahinter. `check` zählt sie getrennt
(`DeckStats.backup`, `…, 1 closing, 4 backup`); Wörter, Inhaltsfolien und Minuten zählen sie nicht
— so vergleicht `schedule-estimate` (E16-S02) den Zeitplan, der vor dem Backup endet, mit einer
Schätzung ohne Backup-Folien.
Die Kundenfassung (E16-S01) behält das Backup.

Word: Ab `{.appendix}` hängen die Überschriften 1–3 über ihr eigenes `w:numPr` an eine neue
Nummerierung — eine Kopie der Überschriften-Liste der Vorlage mit `upperLetter` auf Ebene 1, ohne
Bindung an die Formatvorlagen, mit eigener `w:nsid`. Das Inhaltsverzeichnis (Feld `TOC`) zeigt die
Anhänge mit ihren Buchstaben; ein in Word kopierter oder mit Enter fortgesetzter Anhang zählt
weiter (B, C), eine neu mit „Überschrift 1" formatierte Überschrift dagegen in der Hauptzählung.
Abbildungen und Tabellen zählen durch. Das PDF zählt genauso (`A`, `A.1`, Lesezeichen
„A Glossar"; nach Z folgt wie in Word AA, BB).

Rundreise: Der PPTX-Konverter schreibt `# <Titel> {.backup}` statt `## <Titel>` für die
Trennfolie des Backups bzw. `# Backup {.backup}` vor die erste Folie hinter der Abschlussfolie;
der DOCX-Konverter hängt `{.appendix}` an die erste „Überschrift 1" mit Buchstaben-Nummerierung.

## Teilnehmerhandout (E16-S03)

```python
from pta_documents.generation.common.audience import Audience
from pta_documents.handout import (
    HandoutLayout, HandoutOptions, build_handout, slide_pictures, write_handout,
)
from pta_documents.preview import PreviewUnavailableError

try:
    pictures = slide_pictures(deck, Audience.KUNDE)  # [SlidePicture], Extra 'preview'
except PreviewUnavailableError:
    pictures = None  # Text-Handout
handout = build_handout(deck, pictures, HandoutOptions(HandoutLayout.THREE, Audience.KUNDE))
with open("kurs-handout.docx", "wb") as output:
    result = write_handout(handout, output)  # Hinweise des Decks, des Handouts und von Word
```

`./run.sh handout <praesentation.md|ordner> [--layout 2|3|6] [--audience kunde|intern|trainer]
[--out <ordner>] [--markdown] [--strict]` (`tools/handout/handout.py`) schreibt
`<name>-handout.docx` bzw. `<name>-handout-intern.docx`/`-trainer.docx` (Suffix der Fassung wie
bei `generate`); Word-Berichte werden übersprungen. Fehlt die Vorschau, meldet es
`no slide pictures for …` und schreibt das Text-Handout. `--markdown` legt das Markdown als
`<name>-handout.md` und die Bilder in `<name>-handout/` daneben. Danach die Hinweise (Zeilen der
Präsentation); Exit-Code 1 bei Fehlern, mit `--strict` auch bei Hinweisen, 2 bei falschen
Schaltern.

**Ablauf** (`handout/handout.py`): Kein zweiter Word-Writer — `build_handout` erzeugt das Deck
mit `PptxGenerator` in der Fassung (`audience.resolve`: Schalter, sonst `fassung:`, sonst
`kunde`) im Speicher, liest mit python-pptx je Folie Layout, Titel, Text und Notizen
(`read_slides`; Titelfolie = erste Folie auf einem Titel-Layout, `Trennfolie`, `Abbschlussfolie`,
Backup ab `design.slides.backup_start`) und schreibt daraus **Markdown** für den
DOCX-Generator. `write_handout` erzeugt es mit `docx_options()`. Die Folienbilder
(`slide_pictures`: HTML-Deck derselben Fassung → `render_deck`, Maßstab 1) gehören zur
Foliennummer des Decks; das HTML-Deck entsteht aus der PPTX, die Nummern stimmen also überein.

| Teil | Markdown |
| ---- | -------- |
| Front Matter | `vorlage: quer` (Layout 2) bzw. `hoch`; `titel` (Front Matter, sonst Titel der PPTX), `untertitel`, `autor`, `ort`, `datum`, `sprache`, `kennzeichnung` aus der Präsentation, sonst `kennzeichnung: intern` für `intern`/`trainer`; `inhaltsverzeichnis: ja` ohne Zeitplan; `typografie: nein` (der Text ist schon gesetzt) |
| Titelfolie | Bild 6 cm breit nach dem Deckblatt (Trainer: Notizen darunter) |
| Zeitplan | `**Zeitplan**` und `Schedule.to_markdown()` (E16-S02), wenn das Deck einen hat |
| Trennfolie | `# Titel`, dann die Folie selbst wie jede andere |
| Folie, Layout 2 | `::: columns L:R` — links `![Folie n: Titel](handout/folie-NN.png)`, `---`, rechts Notizen bzw. sechs Linien `***` |
| Folie, Layout 3 | Bild, darunter Notizen bzw. zwei Linien |
| Folie, Layout 6 | zwei Bilder in einem Absatz (Bildreihe, E03-S03), darunter `**Folie n:**` mit Notizen bzw. zwei Linien; vor jedem Kapitel und am Ende eine Folie auch allein |
| Abschlussfolie | klein wie die Titelfolie, ohne Linien |
| Backup | nur in der Trainerfassung |
| ohne Bild | `**Folie n: Titel**`, Absätze und Listen der Folie (Agendapunkte als Liste, Subheadline fett), Notizen als Zitat bzw. Linien; Hinweis `handout-without-pictures` |

Linien zum Schreiben sind `***`: in Word „Standard"-Absätze mit Rahmenlinie unten (wie jede
horizontale Linie). Folientexte und Notizen werden escaped (`\[`, `\{`, `\=\=`), Formatierung
der Folie (fett, kursiv) geht verloren.

**Maße** (`geometry`): aus Seite und Formatvorlagen der Vorlage (`design.word_styles`): Höhe
eines Absatzes = Abstand vor + Zeile (Segoe UI 1,33 × Größe, mindestens die Zeilenhöhe) +
Abstand nach. Je Seite bleibt Platz für eine „Überschrift 1" und 18 pt Reserve; der Rest geteilt
durch 2 (Layout 2) bzw. 3 Zeilen ergibt Bild + Beschriftung + Linien. Ergebnis: Layout 2 Bild
7,7 cm und sechs Linien, Layout 3 Bild 7,1 cm und zwei Linien, Layout 6 Bilder 6,7 cm und zwei
Linien je Reihe. `print_picture` verkleinert jedes Bild auf 300 dpi bei dieser Breite, zieht
einen grauen Rahmen (`GREY_MID`, 1/400 der Breite) und setzt die dpi so, dass seine natürliche
Größe genau die Breite ist (der DOCX-Generator nimmt sie).

**Zwei DOCX-Optionen, nur über die API** (`DocxOptions`, kein Front-Matter-Schlüssel):

| Option | Standard | Wirkung |
| ------ | -------- | ------- |
| `figure_numbers` | `True` | `False`: Bildbeschriftungen ohne „Abbildung n:" und ohne `SEQ`-Feld, nur der Text (Tabellen bleiben nummeriert) |
| `side_by_side_columns` | `False` | `True`: `::: columns` wird eine einzeilige Tabelle im Stil „Bildreihe" (ohne Linien, Breiten nach den Gewichten, Zeile nicht trennbar); nur `---` direkt im Container trennt Spalten, `***`/`___` bleiben Linien; Blöcke einer Spalte (auch Tabellen, Bilder bis zur Zellbreite) stehen in ihrer Zelle |

Rundreise: Der DOCX-Konverter liest eine Spalten-Tabelle wie eine Bildreihe (Bilder, dann die
Absätze); Linien gehen verloren.

Tests: `tests/handout/test_handout.py` (Text-Handout mit allen Titeln und der erwarteten Zahl
Linien, Fassungen, Front Matter, Zeitplan/Inhaltsverzeichnis, Layout 2/3/6 mit Bildern ohne
Browser, Beschriftungen, Rundreise `samples/handout.roundtrip.expected.md`, mit Browser die echte
Vorschau, Werkzeug) und `tests/generation/docx/test_handout_options.py`; Handouts zum Ansehen in
`.tmp/review/handout/`.

## Hinweise (`GenerationResult`)

`generate()` beider Generatoren gibt ein `GenerationResult` zurück (`pta_documents.GenerationResult`,
Modul `pta_documents.generation.common.result`):

| Feld | Inhalt |
| ---- | ------ |
| `notes` | Tupel von `GenerationNote(code, line, message)`, nach Zeile sortiert, jeder Hinweis einmal; leer, wenn nichts umgangen werden musste |
| `slides` | Zahl der Folien (PowerPoint), sonst `None` |
| `pages` | Zahl der Seiten (PDF), sonst `None` — Word zählt Seiten erst beim Öffnen |

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
| `image-enlarged` (`IMAGE_ENLARGED`) | PPTX, DOCX, PDF | ein Bild wird mehr als doppelt so groß gezeigt wie seine Pixel bei 96 dpi und wirkt unscharf |
| `raw-html` (`RAW_HTML`) | PPTX, DOCX, PDF | rohes HTML im Markdown; es wird **weggelassen**. HTML-Kommentare `<!-- … -->` fallen ohne Hinweis weg, `<br>` ist ein Zeilenumbruch |
| `code-not-drawn` (`CODE_NOT_DRAWN`) | PPTX, DOCX, PDF | ein Codeblock in `mermaid`, `chart` oder `financial-chart` wurde von keinem Renderer gezeichnet und steht als Code da (`chart` und `financial-chart` zeichnet der `ChartRenderer`, `mermaid` der `MermaidRenderer`, wenn mermaid-cli eingerichtet ist — sonst nennt der Hinweis, was fehlt). Word lässt damit auch Icons in Fußnoten weg |
| `character-missing` (`CHARACTER_MISSING`) | PDF | ein Zeichen fehlt in den Schriften; es erscheint als `?` bzw. als das, was `PdfOptions.replace_unsupported` daraus macht (mit `replace_unsupported=None` ist es ein Fehler) |
| `notes-dropped` (`NOTES_DROPPED`) | DOCX (E09-S01), PDF | Sprechernotizen fallen im Word-Dokument bzw. PDF weg |
| `code-language-unknown` (`CODE_LANGUAGE_UNKNOWN`) | PPTX, DOCX (E17-S02), PDF | die Sprache eines Codeblocks ist unbekannt; er steht einfarbig da |
| `image-scale-in-title` (`IMAGE_SCALE_IN_TITLE`) | PPTX, DOCX (E15-S04) | `scale=N` steht im Bildtitel; wirkt bis 2027-11, gehört aber als `{scale=N}` hinter das Bild |
| `scene-dropped` (`SCENE_DROPPED`) | DOCX (E09-S04) | eine Szene (`::: scene`) fällt im Word-Dokument weg; PowerPoint zeigt sie als Formen, das PDF als Standbild |
| `audience-omitted` (`AUDIENCE_OMITTED`) | PPTX, DOCX, PDF (E16-S01) | die Fassung hat interne Blöcke oder Lösungen weggelassen; **ein** Hinweis ohne Zeile mit den Zahlen („4 internal blocks and 1 solution were left out for the audience 'kunde'; …"), siehe [Zielgruppenfassungen](#zielgruppenfassungen-e16-s01) |
| `schedule-missing` (`SCHEDULE_MISSING`) | PPTX (E16-S02) | ein Deck mit Zeitplan hat Folien ohne `dauer` (und ohne Kapitel mit `dauer`); **ein** Hinweis an der ersten („7 slides have no 'dauer'; the schedule assumes 2 min each. …"), siehe [Schulungs-Zeitplan](#schulungs-zeitplan-e16-s02) |
| `schedule-length` (`SCHEDULE_LENGTH`) | PPTX (E16-S02) | die Summe weicht von `laenge:` ab („Planned 240 min ('laenge:'), slides sum to 265 min."), oder die Folien eines Kapitels brauchen mehr als seine `dauer` (Zeile des `#`) |
| `schedule-estimate` (`SCHEDULE_ESTIMATE`) | nur `check` (E16-S02) | die geplante Sprechzeit (ohne Pausen) weicht um mehr als die Hälfte von der Faustregel des Prüfbefehls ab (2 Minuten je Inhaltsfolie plus Notizen); nur, wenn mindestens eine Folie `dauer` hat |
| `attribute-ignored` (`ATTRIBUTE_IGNORED`) | PPTX, DOCX, PDF (E16-S04) | ein Überschriftenattribut des anderen Dokumenttyps: `{.backup}` in Word/PDF, `{.appendix}` auf Folien; die Kapitel bleiben gewöhnliche Kapitel, siehe [Backup-Folien und Anhang](#backup-folien-und-anhang-e16-s04) |
| `handout-without-pictures` (`HANDOUT_WITHOUT_PICTURES`) | DOCX (E16-S03) | das Handout zeigt den Text der Folien statt ihrer Bilder, weil die Vorschau (Extra `preview`) fehlt; siehe [Teilnehmerhandout](#teilnehmerhandout-e16-s03) |

Die Codes sind stabil; neue kommen mit neuen Funktionen dazu. `./run.sh generate` zeigt die
Hinweise unter jeder Datei und endet mit `--strict` auch bei Hinweisen mit Code 1;
`./run.sh generate-samples` endet mit Code 1, sobald ein Beispiel Hinweise hat.

## Prüfen ohne Erzeugen (`check`)

```sh
./run.sh check <datei-oder-ordner> [...] [--docx | --pptx | --pdf] [--strict] [--skip <code>,…] [--sources] [--json] [--audience kunde|intern|trainer|alle]
```

prüft Markdown-Dateien, **ohne eine Datei zu schreiben**. Dateiauswahl und Formatwahl wie bei
`generate` (PDF nur mit `--pdf`, Extra `pdf`; die Stilregeln sind die von Word). Je Datei:
`OK <datei>` bzw. `ERROR <datei>: <grund>`, dann die Hinweise (`  - line 12: … [code]`), dann zwei Zeilen Statistik. Exit-Code 1 bei Fehlern, mit `--strict`
auch bei Hinweisen; `--json` gibt dasselbe als ein JSON-Objekt aus
(`{"ok": …, "files": [{"file", "ok", "errors", "notes": [{"code", "line", "message"}], "stats"}]}`).

`--audience` prüft diese Fassung (E16-S01) statt der aus `fassung:`; `alle` prüft jede Fassung,
die sich unterscheidet, mit eigener Statistik (`OK <datei> (fassung: intern)`, im JSON
`"audience"`); aus Python `CheckOptions(audience=Audience.TRAINER)`.

Aus Python: `pta_documents.generation.common.check.check(document, format, CheckOptions(...))`
→ `CheckResult(errors, notes, stats)`. Fehler und Hinweise stammen aus einem Probelauf des
Generators in den Speicher — es sind also genau die von `generate`. Dazu kommen die
**Stilhinweise** (`generation/common/style_rules.py`, Grenzen in `StyleLimits`), Code `style-…`:

| `code` (`StyleCodes`) | Format | Wann |
| --------------------- | ------ | ---- |
| `style-bullets` (`BULLETS`) | PPTX | mehr als 7 Aufzählungspunkte auf einer `##`-Folie (alle Ebenen; die Agenda darf 8) oder ein Punkt mit mehr als 20 Wörtern („Fließtext in Aufzählungen") |
| `style-words` (`WORDS`) | PPTX | mehr als 80 Wörter auf einer `##`-Folie (ohne Titel, Sprechernotizen und Codeblöcke) |
| `style-punctuation` (`PUNCTUATION`) | PPTX, DOCX | die Punkte einer Liste enden mit verschiedenen Satzzeichen (`.`/`!`/`?` zählen gleich; eine Aufzählung `…;` `…;` `….` und ein Punkt mit `:` vor Unterpunkten sind erlaubt) |
| `style-title` (`TITLE`) | PPTX | Folientitel über 60 Zeichen oder mit Punkt am Ende (nicht die Titelfolie, `{.quote}`, `{.interim}`) |
| `style-image-source` (`IMAGE_SOURCE`) | PPTX, DOCX | Bild ohne Urheber/Quelle (`Foto:`, `Bild:`, `Quelle:`, `CC …`, `©`, `gemeinfrei` …) im Bildtitel; in PowerPoint auch irgendwo auf der Folie, in Word auch im Absatz des Bildes oder dem danach. Nur, wenn der Ordner der Datei eine `QUELLEN.md` hat oder mit `--sources` (`CheckOptions(sources=True)`); Kontaktfolien nie |
| `style-alt-text` (`ALT_TEXT`) | PPTX, DOCX | Bild ohne Alt-Text (`![](…)`); E13-S03 erweitert die Barrierefreiheitsprüfung |
| `style-heading-numbers` (`HEADING_NUMBERS`) | DOCX | `#`–`###` beginnt mit eigener Nummer (`1. Einleitung`, `2.3 Ziele`), obwohl Word nummeriert |

Abschalten: `--skip style-words,style-title` (`CheckOptions(skip=…)`) oder im Front Matter
`pruefung: aus` (alle Stilregeln) bzw. `pruefung: style-bullets, style-words` (nur diese). Ein
unbekannter Code ist ein Fehler mit der Liste der Codes. Die Generatoren nehmen den Schlüssel an
und ignorieren ihn.

**Statistik** (`CheckResult.stats`, Faustregeln, als solche ausgewiesen):

- PowerPoint (`DeckStats`, gezählt am Probe-Deck): Folien gesamt, Titel-, Kapitel-, Inhalts-
  (davon „(Forts.)") und Abschlussfolien, Backup-Folien (E16-S04, nur gezählt, sonst
  nirgends mitgerechnet); Wörter gesamt (ohne Titel und Fußzeilen) und je
  Inhaltsfolie min/median/max; Wörter der Sprechernotizen (ohne Absätze, die ganz Code sind —
  Codeblöcke werden nicht gesprochen); Dauer `minutes` = 2 Minuten je Inhaltsfolie plus Notizen
  bei 120 Wörtern je Minute.
- Word (`ReportStats`, gezählt am Markdown): Wörter (ohne Code und Notizen), Überschriften,
  Tabellen, Abbildungen; `pages` = Wörter / 350 plus eine halbe Seite je Tabelle und Abbildung —
  die echte Seitenzahl kennt erst Word beim Öffnen.
- PDF (`ReportStats` wie Word, dazu `counted_pages`): `pages` sind die Seiten des Probe-PDFs.

## Beliebiges Dokument → Markdown

```python
from pta_documents.conversions import ConversionOptions, ConverterRegistry, convert, detect

with open("eingang/datei.docx", "rb") as datei:
    document = convert(datei, "datei.docx")  # Format am Inhalt erkannt
detect(daten, "brief.doc")  # nur erkennen: DocumentFormat.DOC

registry = ConverterRegistry.default(mein_konverter)  # eigene Konverter hinten anhängen
registry.convert(daten, options=ConversionOptions(include_images=False))
```

`convert(data, file_name=None, options=None)` liest die Eingabe (Bytes oder Stream, auch nicht
suchbar) einmal, erkennt das Format am Inhalt und gibt sie an den ersten Konverter, der es
annimmt; der Dateiname landet in `options.file_name`. `ConverterRegistry.default()` enthält PDF
(nur mit dem Extra `pdf`, siehe [PDF → Markdown](#pdf--markdown-e07-s04)), DOCX und
PPTX, danach die übergebenen Konverter. Ein eigener Konverter braucht nur
`can_convert(format) -> bool` und `convert(data, options=None) -> MarkdownDocument`
(Protocol `DocumentConverter`).

Erkennung (`detect`, erste 8 KB): ZIP mit `word/document.xml` → `docx`, `xl/workbook.xml` →
`xlsx`, `ppt/presentation.xml` → `pptx`, sonst `zip`; OLE-Signatur → nach Endung `doc`
(`.doc`, `.dot`), `xls` (`.xls`, `.xlt`, `.xla`), `ppt` (`.ppt`, `.pps`, `.pot`), `msg`, sonst
`ole`; `%PDF` → `pdf`; `{\rtf` → `rtf`; ohne NUL-Byte → `text`; sonst `unknown`. Der Inhalt
gewinnt immer über die Endung. Ein Stream für `detect` muss suchbar sein, seine Position bleibt.

Abgelehnt wird mit `DocumentConversionError(format, reason)`, die Meldung sagt, was zu tun ist:

| Format | Meldung (gekürzt) |
| ------ | ----------------- |
| `doc`, `ppt`, `xls`, `msg`, `ole` | „Legacy binary Office files (…) are not supported." + Speichern als `.docx`/`.pptx` |
| `rtf`, `xlsx` | nicht unterstützt, als `.docx` speichern (Excel: Tabellen nach Word kopieren) |
| `pdf` ohne Extra | „PDF needs the optional extra 'pdf' (pip install -e '.[pdf]')." |
| `zip`, `text`, `unknown` | „No converter is registered for this format." + unterstützte Formate |

Markdown- und Textdateien werden nicht konvertiert (Entscheidung zu E07-S01).

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
nach deren Inhalt als `::: notes` … `:::` aus, Listenebenen als `-`-Listen, aufeinanderfolgende
Absätze ganz in Consolas als Zaun ohne Sprache (der Notizzaun wird länger als jede `:::`-Zeile
darin); leere Notizen und
Notizen nur aus dem Aufforderungstext des Notizenmasters entfallen. `ConversionOptions(notes=False)`
lässt sie weg.

Beide Konverter geben den Text so zurück, wie er im Dokument steht — nach der Typografie also
`„…“` statt `"…"`. `ConversionOptions(plain_quotes=True)` setzt außerhalb von Code `„“”` →
`"`, `‚‘’` → `'`, `–` → `-`, `…` → `...` und geschützte Leerzeichen → Leerzeichen zurück, damit
eine Rundreise den geschriebenen Text wiederfindet. Codeblöcke des DOCX-Generators (Vorlage
„Code") kommen als Zaun mit ihrer Sprache zurück.

## PDF → Markdown (E07-S04)

Braucht das Extra `pdf` (pdfplumber und pikepdf); ohne lehnt `convert` PDFs mit der Meldung zum
Extra ab. Das Modul `pta_documents.conversions.pdf` importiert pdfplumber gleich beim Import.

```python
from pta_documents.conversions.pdf import PdfConverter

document = PdfConverter().convert(open("bericht.pdf", "rb"))  # auch bytes, auch nicht suchbar
document.metadata  # pageCount, title/author aus dem Info-Dictionary, skippedImages (> 0)
```

Port des DocLibs-Konverters auf pdfplumber: Gelesen wird nur die Textschicht — gescannte Seiten
ohne Text bleiben leer, OCR gibt es nicht. Jede Seite beginnt mit `## Page n` (englisch wie
`## Slide n` des PPTX-Konverters).

- **Zeilen und Absätze:** Wörter auf derselben Grundlinie (Toleranz halbe Worthöhe) oder mit
  überwiegend gleicher Höhe (hochgestellte Fußnotenzeichen) sind eine Zeile. Ein neuer Absatz
  beginnt bei einem Aufzählungszeichen, einem nummerierten Anfang (`1.`, `2.3 `), am oberen oder
  unteren Rand (8 % der Seitenhöhe), bei einem Abstand über dem üblichen plus 0,35 × Grundgröße,
  nach einer früh endenden Zeile, bei einer Ausrückung und bei einem Größenwechsel über 15 %.
  Gedreht gesetzter Text (das Wasserzeichen „ENTWURF") wird nicht gelesen.
- **Überschriften** werden `###`: kurz (unter 100 Zeichen), keine Verzeichniszeile (`....  3`),
  nicht mit `.`/`:` endend (außer nummeriert) und mindestens 1,15 × Grundgröße groß oder fett und
  nummeriert. Die Ebene lässt sich aus dem PDF nicht sicher lesen.
- **Listen:** Aufzählungszeichen `•▪■◦·●‣⁃➢→` und Wingdings (`U+F000`–`U+F0FF`), mit Leerzeichen
  dahinter auch `-`, `–`, `*`, `o`; dazu als Form gezeichnete Zeichen vor der Zeile, wie sie der
  PDF-Generator setzt (kleines gefülltes Quadrat, kurzer Strich) und Aufgabenkästchen
  (`- [ ] `, mit Haken `- [x] `). Aufeinanderfolgende Punkte bilden eine enge Liste, ohne Ebenen.
  Nummerierte Punkte bleiben Absätze (`1\. Schritt`).
- **Silbentrennung:** „Netz-|nutzung" wird „Netznutzung", „GELI-|Anmeldung" behält den Strich.
- **Kopf- und Fußzeilen:** einer der ersten oder letzten zwei Absätze einer Seite, der ohne
  Ziffern auf mindestens drei Seiten wiederkehrt, entfällt — außer sein Text kommt auf einer
  Seite mehrfach vor (Punkte einer langen Liste unterscheiden sich nur in der Nummer). Der Titel
  auf dem Deckblatt eines PTA-PDFs steht auch in der Kopfzeile und entfällt daher; er steht in
  `metadata["title"]`.
- **Tabellen** werden Pipe-Tabellen: Gitter mit Linien in beiden Richtungen (pdfplumber
  `find_tables`) und Tabellen im PTA-Stil — eine gefüllte Kopfzeile mit einer Linie gleicher
  Breite an ihrer Unterkante, dann je Zeile eine waagerechte Linie, solange der Text der Zeile so
  dicht unter der Linie beginnt wie der Kopftext unter der Füllung; Spalten dort, wo in keiner
  Zeile ein Wort steht. Ausrichtung, Fett und verbundene Zellen gehen verloren.
- **Code:** Zeilen überwiegend in einer Festbreitenschrift (Name mit `Mono`, `Courier`,
  `Consol`, `Inconsolata`, `Cousine`, `Menlo`, `Code`) werden ein Zaun ohne Sprache — eine
  gefüllte Fläche dahinter (der Codeblock des Generators) hält ihn zusammen, Einrückung und
  Leerzeilen kommen aus den Abständen. Eine einzelne solche Zeile ohne Fläche bleibt Text.
- **Bilder** werden Ressourcen `page{n}-image{i}.png` bzw. `.jpg` (JPEG-Daten unverändert,
  sonst PNG über pikepdf) und stehen an ihrer Stelle im Text; ein Bild, das auf jeder Seite
  vorkommt (Logo), entfällt. Nicht dekodierbare Bilder (auch eingebettete Inline-Bilder) zählt
  `skippedImages`. Gezeichnete Logos und Grafiken (Vektoren) erscheinen nicht.
- **Fehler:** ein beschädigtes PDF wirft `DocumentConversionError(pdf, "The PDF could not be read:
  …")`, ein PDF mit Kennwort eine eigene Meldung. Scheitert die Analyse einer Seite, kommt deren
  Text zeilenweise (`extract_text`).
- Kein Rückweg für Fett, Kursiv, Links, Fußnoten (das Zeichen bleibt als Ziffer am Wort), Bild-
  und Tabellenbeschriftungen (bleiben Text), Grafiken und Folien-Syntax.
  `ConversionOptions(plain_quotes=True)` setzt die Typografie zurück wie bei Word.
- **Rundreise:** `tests/generation/pdf/layout/test_samples.py` erzeugt `report.md` und
  `long.md` als PDF mit Deckblatt und Seitenrahmen und vergleicht das Markdown mit
  `report.roundtrip.expected.md`/`long.roundtrip.expected.md` daneben.

## Beispiele

`samples/` enthält Beispielinhalte, z. B. `samples/gsb/` (Hauptbeskidenweg, mit CC-Fotos).
`./run.sh generate-samples [name]` erzeugt daraus DOCX (`*-bericht.md`, `*-dokument.md`) und
PPTX (`*-praesentation.md`, `*-folien.md`) nach `.tmp/samples/<name>/`. Für beliebige Ordner und
Dateien gibt es `./run.sh generate <pfad> [--docx|--pptx|--pdf|--html] [--out <ordner>] [--strict]` (siehe
[anleitung.md](anleitung.md)). Die Beispiele erzeugen ohne Hinweise.

**Funktionsübersicht** (E08-S03): `samples/funktionen/` zeigt jede Funktion; der Word-Bericht
setzt unter jede `##`-Überschrift einen Zaun ```` ```markdown ```` mit dem Quelltext und darunter
denselben Text als Ergebnis, die Präsentation hat den Quelltext jeder `##`-Folie als
```` ```markdown ```` in ihren `::: notes`. `tests/samples/test_funktionen.py` hält das aktuell:

- jede Datei erzeugt im Format, das `tools/generate` aus dem Namen wählt, ohne Hinweise; die
  Dokumente landen in `.tmp/review/funktionen/`, ihre Rundreise durch den Konverter wird mit
  `tests/samples/funktionen/<datei>.roundtrip.expected.md` verglichen
  (`PTA_DOCUMENTS_UPDATE_EXPECTED=1` erneuert);
- jede Datei steht in der Tabelle der `README.md` der Beispiele;
- **Vollständigkeit** je Format: jeder Schlüssel aus `VALID_KEYS` des Generators,
  `status.<kategorie>` jeder Kategorie (auch als Status-Label in einer Tabellenzelle), jede
  `vorlage:`-Variante, jede `sprache:`, jeder Container aus `layout_syntax.CONTAINER_NAMES` (Word
  ohne `notes`), `::: panel dark`, `::: columns` mit Breiten, jeder Alert, `==Markierung==`,
  farbige Wörter jeder Kategorie; nur PowerPoint: jedes Heading-Attribut aus
  `heading_attributes.VALID` und jede `titelfolie:`. Der Test nennt, was fehlt — wer eine neue
  Syntax, einen Schlüssel oder eine Variante einführt, ergänzt die Beispiele;
- Bericht und Präsentation: jede `##`-Funktion hat ihren Quelltext, und jeder Quelltext steht
  außerhalb seines Zauns wortgleich als Ergebnis.
- **Guide ↔ Beispiele** (E02-S05): was die gemeinsamen Abschnitte der Authoring Guides an Syntax
  nennen (`authoring_guides.named_syntax`: `::: name`, `[!KIND]`, `{.attribut`, ```` ```chart ````
  …), muss wortgleich in den Beispielen des Formats stehen
  (`test_the_samples_show_the_syntax_the_guide_names`), siehe
  [Authoring Guides](#authoring-guides-e02-s05).

## Authoring Guides (E02-S05)

Ein Authoring Guide ist die deutsche Anleitung für Schreiber (Menschen und KI-Agenten), wie man
Markdown für einen Generator schreibt — Markdown ab `##`, damit ein Aufrufer ihn unter eine eigene
Überschrift setzen kann, höchstens 2 500 Wörter. Jeder Generator erzeugt ihn aus seinen Optionen
(Word E03-S05, PowerPoint E04-S06, PDF E05-S05; bis dahin bietet noch keiner einen an):

```bash
./run.sh authoring-guide docx      # bzw. pptx, pdf — schreibt den Guide auf die Standardausgabe
./run.sh authoring-guide pptx > guide-praesentation.md
```

Ohne Guide endet das Werkzeug mit Code 1 und einer Meldung, bei falschen Argumenten mit Code 2;
das PDF braucht das Extra `pdf`.

Die gemeinsamen Bausteine in `pta_documents.generation.common.authoring_guides` (kein Extra
nötig) entstehen aus den Listen im Code, damit Guide, Prüfung und Code nicht auseinanderlaufen:

| Baustein | Inhalt |
| -------- | ------ |
| `template(package, name)` | die Vorlage `<package>/authoring_guide/<name>.md` (Paketdaten) |
| `fill(template, values)` | ersetzt `{{name}}`; ein fehlender Wert ist ein `KeyError`, ein leerer Platzhalter allein in seiner Zeile hinterlässt keine Leerzeile; das Ergebnis endet mit genau einem Zeilenumbruch |
| `front_matter_section(keys, valid, example)` | „Front Matter": Syntax mit Beispiel, je `GuideKey(key, values, meaning)` eine Tabellenzeile und `status.<kategorie>`; `keys` muss genau `valid` (die `VALID_KEYS` des Generators) beschreiben, sonst `ValueError`. `common_keys()` liefert die Zeilen, die in allen Formaten gleich sind (`datum`, `sprache`, `typografie`, `syntaxhervorhebung`, `pruefung`, `fassung`) |
| `layout_syntax_section(format, effect)` | „Folien-Syntax": Container, Alerts, `==…==`, farbige Wörter, Status-Labels, Überschriftenattribute (`#`/`##` aus `heading_attributes`), Blockmarker; `effect` ist der eigene Absatz des Guides. Word und PDF nennen, was nur für Folien gilt, als bloße Namen |
| `icons_section(format)`, `notes_section(format)`, `typography_section()` | alle Icon-Namen; die Hinweis-Codes des Formats mit „Was tun"; Typografie und Codefarben |
| `renderers_section(renderers)` | die Abschnitte der Code-Block-Renderer (`CodeBlockRenderer.authoring_guide`), z. B. „Charts" |
| `image_formats(native, converters)` | die Bildformate eines Generators, die der Konverter (`ImageConverter.format`) eingeschlossen |
| `characters_section(text, code, intro)` | nur PDF: die `SYMBOLS` (✓, →, ● …), die den Schriften fehlen, mit dem ersten Ersatz, den alle Schriften haben |
| `words(guide)`, `named_syntax(guide)`, `named_keys(guide)` | Wörter zählen; die Syntax bzw. die Front-Matter-Schlüssel, die ein Guide nennt |

Testhilfen für die Guides der Generatoren in `tests/generation/guides.py`: `examples`,
`assert_examples_generate`, `assert_names_everything`, `assert_under`; den Abgleich mit
`*.expected.md` macht `tests/expected.assert_matches_expected`. Wer einen Container, ein Alert,
ein Überschriftenattribut, einen Blockmarker oder einen Hinweis-Code einführt, trägt seinen Text
in `CONTAINER_TEXTS`, `ALERT_TEXTS`, `ATTRIBUTE_TEXTS`, `MARKER_TEXTS` bzw. `NOTE_TEXTS` ein —
die Tests nennen, was fehlt.
