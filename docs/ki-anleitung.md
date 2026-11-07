# Anleitung für KI-Assistenten: Dokumente erzeugen

Diese Datei ist für eine KI, die im Auftrag eines Anwenders **mit** PTA Documents arbeitet:
Markdown schreiben, daraus PTA-Word-Dokumente und PTA-Präsentationen erzeugen, vorhandene
Dateien nach Markdown lesen. Wer **an** der Bibliothek entwickelt, folgt stattdessen
[AGENTS.md](../AGENTS.md) und `ai/`.

## Grundregeln

1. **Nur in `documents/` arbeiten.** Dort liegen die Dokumente des Anwenders, ein Ordner je
   Thema; der Ordner ist git-ignoriert. Nichts unter `src/`, `tests/`, `tools/`, `spec/`, `ai/`,
   `samples/` oder `source-templates/` ändern, nichts committen oder pushen — der Anwender nutzt
   nur einen Klon.
2. **Das Design kommt von den Vorlagen.** Keine Farben, Schriften, Größen oder eigenen Layouts
   ins Markdown schreiben — es gibt dafür keine Syntax, und das ist Absicht. Das Ergebnis ist
   immer im PTA-Design.
3. **Erzeugen und prüfen:** `./run.sh generate documents/<thema>`; der Befehl endet mit
   Code ≠ 0, wenn eine Datei einen Fehler hat. Fehlermeldungen (`ERROR <datei>: <grund>`) sind für
   den Schreiber formuliert — den Grund lesen, das Markdown korrigieren, neu erzeugen.
   **Hinweise lesen:** unter `wrote <datei>` stehen eingerückt die Hinweise
   (`  - line 12: …`), was der Generator umgehen musste. Das Markdown so ändern, dass keine mehr
   kommen; `(Forts.)`-Folien (`slide-split`) sind fast immer ein Zeichen für zu viel Inhalt.
   Mit `--strict` endet der Befehl auch bei Hinweisen mit Code 1 — so lässt sich prüfen, ob
   alles sauber ist. Codes: [verwendung.md](verwendung.md#hinweise-generationresult).
4. **Einmalig einrichten**, falls `.venv/` fehlt: `./run.sh setup` (Windows `.\run.ps1 setup`).
5. **Fakten nicht erfinden.** Inhalte kommen vom Anwender oder aus Quellen, die er nennt. Fremde
   Bilder nur mit passender Lizenz; Urheber und Lizenz in der Bildunterschrift bzw. auf der
   Folie nennen und in `documents/<thema>/QUELLEN.md` festhalten (Muster: `samples/gsb/`).

## Dateien und Namen

```
documents/<thema>/
  <name>-bericht.md         → <name>-bericht.docx        (auch …-dokument.md)
  <name>-praesentation.md   → <name>-praesentation.pptx  (auch …-folien.md)
  images/…                  → Bilder, im Markdown relativ: images/foto.jpg
```

Bilder: PNG, JPEG, GIF, BMP, TIFF. **SVG wird abgelehnt** — vorher nach PNG wandeln. Andere
Dateinamen mit `--docx`/`--pptx`; Ausgabe woanders mit `--out <ordner>`.

Vollständige, funktionierende Beispiele: `samples/gsb/gsb-bericht.md` und
`samples/gsb/gsb-praesentation.md`; jede unterstützte Funktion einmal zeigt
`samples/funktionen/` (siehe dessen `README.md`). Bei Unsicherheit an ihnen orientieren.

## Front Matter

Erster Block der Datei, zwischen `---`-Zeilen, flach `schlüssel: wert` (kein verschachteltes
YAML, keine Listen). Schlüssel und Werte sind **deutsch**; `ja`/`nein`; Datum `JJJJ-MM-TT` oder
`TT.MM.JJJJ`. Unbekannte Schlüssel sind Fehler.

| Schlüssel | Word | PPTX | Werte |
| --------- | :--: | :--: | ----- |
| `vorlage` | ✓ | ✓ | Word `hoch` (Standard) · `hoch-ohne-deckblatt` · `quer` · `quer-ohne-deckblatt`; PPTX `basis` (Standard) · `schulung` |
| `titel` | ✓ | ✓ | Pflicht bei Word-Vorlagen mit Deckblatt |
| `untertitel`, `autor`, `ort`, `datum` | ✓ | ✓ | frei; Datum siehe oben |
| `sprache` | ✓ | ✓ | `de` · `en` (erzeugte Texte, englische Titelfolie) |
| `firma` | ✓ | – | ersetzt „PTA IT-Beratung" in der Fußzeile |
| `inhaltsverzeichnis` | ✓ | – | `ja` · `nein` |
| `fusszeile` | – | ✓ | Fußzeilentext nach „PTA – " |
| `titelfolie` | – | ✓ | `bild-02` (Standard) · `bild-01` · `branchen` · `ohne-bild` |

`firma`/`inhaltsverzeichnis` in einer Präsentation oder `fusszeile`/`titelfolie` in einem
Word-Dokument sind Fehler.

## Word-Bericht

- `#` ist **Kapitel** (Überschrift 1, nummeriert), nie der Titel — der Titel steht nur im Front
  Matter. `##`, `###` = Überschrift 2/3; `####`+ = unnummerierte Zwischenüberschrift. Überschriften
  ohne eigene Nummern schreiben (Word nummeriert selbst).
- Absätze, `-`/`1.`-Listen (bis drei Ebenen), Tabellen, `> Zitat`, Codeblöcke, Links, Fußnoten
  `[^1]`, **fett**, *kursiv*, ~~durchgestrichen~~, `code` gehen.
- Tabellenbeschriftung: direkt unter der Tabelle ein Absatz `Tabelle: Beschreibung` →
  „Tabelle n: Beschreibung". Tabellentitel: ein Absatz nur aus `**Titel**` direkt davor.
- Abbildung: Bild allein im Absatz, Unterschrift als Bildtitel:
  `![Alt-Text](images/a.jpg "Unterschrift (Foto: Name, CC BY 4.0)")` → „Abbildung n: …".
- Kein HTML (wird weggelassen, Hinweis `raw-html`; nur `<br>` in Tabellenzellen ist ein
  Zeilenumbruch), keine Diagramme/Mermaid/`chart`-Blöcke (werden als Code gezeigt, Hinweis
  `code-not-drawn`).
- Folien-Syntax (`:::`-Container, Alerts `> [!NOTE]`, `==Markierung==`, `[Wörter]{.success}`)
  wird angenommen und schlicht gezeigt: Container-Inhalt nacheinander (`###` in Containern wird
  fett, keine Überschrift), Alerts/`conclusion`/`comment` als Hinweisabsatz mit fetter Art,
  Markierung gelb, farbige Wörter und Status-Labels in der Statusfarbe. Mehrere Bilder in einem
  Absatz (`![a](x.png) ![b](y.png)`) stehen nebeneinander (max. vier je Zeile), je mit
  „Abbildung n".

## Präsentation

Gliederung:

```markdown
# Präsentationstitel            ← Titelfolie (erstes #); Text darunter = Untertitel, nur Text
# Kapitel                       ← Trennfolie „01", „02" …  — KEIN Inhalt darunter
## Folientitel                  ← eine Folie (Titel höchstens zwei Zeilen)
# Schlussbotschaft {.closing}   ← Abschlussfolie — KEIN Inhalt darunter
```

- Absatz = Einleitungstext, `-`-Listen = Aufzählung (bis drei Ebenen), `1.` = nummeriert,
  `###` = Subheadline. **Fett** erscheint in Segoe UI statt Light (PTA-Hervorhebung).
- Je Folie wenig Text: höchstens etwa 6–8 Aufzählungspunkte. Zu viel wird verkleinert und sonst
  auf „(Forts.)"-Folien geteilt — das sieht schlechter aus als bewusst geteilte Folien.
- **Eine Tabelle, ein Codeblock oder eine Bildreihe je Folie.** Text davor steht oben, Text
  danach unten (gut für Quellenangaben). Ein zweites Visual unter derselben `##` erzeugt eine
  weitere Folie mit demselben Titel. Tabellen höchstens etwa 8 Zeilen, sonst werden sie geteilt.
- Ein `**fetter**` Absatz direkt vor einer Tabelle wird deren Titelzeile.
- Ein Bild + Text → Layout „Titel, Text und Bild 01" (Bild rechts, beschnitten); ein Bild allein →
  „Titel und Bild 01"; mehrere Bilder in einem Absatz → nebeneinander (max. vier je Folie).
  Verliert ein Bild mehr als ein Viertel seiner Fläche an den Rahmen (`image-cropped`) oder wird
  es mehr als doppelt vergrößert (`image-enlarged`), kommt ein Hinweis — dann ein Bild in
  passenden Proportionen bzw. höherer Auflösung ablegen.
- Ein bestimmtes PTA-Layout: `## Titel {layout="Titel und Text (zweispaltig)"}` und den Inhalt mit
  `---` in Spalten teilen. Nur exakte Layoutnamen; die Fehlermeldung listet alle.
- Heading-Attribute: `#` kennt `.closing` und `layout="…"`, `##` kennt `.dark`, `kicker="…"`,
  `layout="…"` und die PTA-Folienarten `.agenda`, `.interim`, `.quote`, `.contact` (siehe
  unten); alles andere ist ein Fehler. `kicker` ist eine kleine Zeile über dem Titel,
  `.dark` setzt die Folie auf den Verlauf der Titelfolie mit weißer Schrift (beides macht die
  Folie zur Flow-Folie, siehe unten).

- **Sprechernotizen:** zu **jeder** Folie (auch Titel-, Trenn- und Abschlussfolie) einen Block
  `::: notes` … `:::` unter ihre Überschrift schreiben, zwei bis fünf Sätze, die der
  Vortragende sagt — nicht den Folientext wiederholen. PowerPoint legt sie auf die Notizenseite
  (bei geteilten Folien auf jede), Word lässt sie weg (Hinweis `notes-dropped`, beim
  Word-Bericht also keine Notizen schreiben). Absätze, Listen, fett, kursiv, Code und Links
  bleiben; Tabellen und Bilder darin fallen weg. Nie vor dem ersten `#`.

## PTA-Folienarten (PowerPoint)

Höchstens eine je `##`, nie zusammen mit `.dark`, `kicker` oder Containern/Alerts. Word zeigt
sie schlicht: Agenda als Überschrift mit Liste (ohne Liste die folgenden `#`-Kapitel),
Zwischenfazit fett, Zitat und Quelle als Zitat, Kontakt mit fettem Namen und kleinem Foto.

| Schreiben | Ergebnis |
| --------- | -------- |
| `## Agenda {.agenda}` + **eine** Liste (je Punkt eine Zeile, max. 8) | Agendafolie mit „01" …; ≤ 4 kurz, 5–8 lang; mehr = Fehler → zwei Agendafolien |
| `## Agenda {.agenda}` ohne Inhalt | Agenda aus den `#`-Kapiteln (ohne Titel und `{.closing}`) |
| `## Aussage {.interim}` — **kein** Inhalt darunter | Zwischenfazit (`layout="Zwischenfazit 02"` für die zweite Variante) |
| `## Zitat {.quote}` + höchstens **ein** Absatz (die Quelle) | Zitatfolie (`layout="Zitat 02"`) |
| `## Kontakt {.contact}` + je Person `### Name` und **ein** Absatz mit Foto und Zeilen Funktion / E-Mail (mit `@`) / Telefon (`+` oder Ziffer am Anfang) | Kontakt 01–05 nach Personenzahl (max. 5); genau eine Person + weiterer Text/Liste danach → „Kontakt mit Text" |

- Keine Agenda ohne `{.agenda}` — es gibt keine automatische.
- Jede Kontaktart (Funktion, E-Mail, Telefon) höchstens einmal je Person; Fotos hochkant
  (etwa 7 : 9), sonst kommt `image-cropped`.

## Folien-Syntax (Word und PowerPoint)

Beide Formate nehmen dieselbe Syntax an und melden dieselben Fehler mit Zeilennummer
(`Line 12: …`). **PowerPoint** macht aus einer `##`-Folie mit Container, Alert, Tag-Absatz,
`.dark` oder `kicker` eine **Flow-Folie** auf „Nur Titel"; **Word** zeigt den Inhalt schlicht in
eigenen Formatvorlagen (siehe *Word-Bericht*).

| Schreiben | PowerPoint |
| --------- | ---------- |
| `::: cards` mit `### Titel` je Karte (optional erster Absatz `**26 %**` = Kennzahl) oder einer Liste `- **Titel** – Text` | Karten nebeneinander im Raster, höchstens vier je Zeile |
| `::: rows` mit einer Liste `- **Begriff** – Beschreibung` | Begriff links, Beschreibung rechts, Linien wie die Tabelle |
| `::: panel` / `::: panel dark` | graue / dunkelblaue Fläche |
| `::: statement` | erster Absatz groß und fett, der Rest normal |
| `::: columns` / `::: columns 1:2` / `1:1:2`, Teile durch `---` (Leerzeile davor) getrennt | Spalten; genau zwei gleiche Spalten nur mit Text → Layout „Titel und Text (zweispaltig)" |
| `::: conclusion` (nur Text, höchstens zwei Zeilen, einmal je Folie, nicht in anderen Containern) | PTA-Fazit-Box am Fuß der Folie; länger = Fehler |
| `::: comment` (nur Text, direkt nach dem Block, den sie kommentiert) | PTA-Kommentarbox: Sprechblase rechts oben auf dem Block davor — am besten nach einem Bild |
| `> [!NOTE]` als erste Zeile eines Zitats (`NOTE`, `TIP`, `IMPORTANT`, `WARNING`, `CAUTION`) | graue Fläche, Balken blau bzw. gelb |
| Absatz nur aus `` `a` `b` `` | Chips; in einem Container eine Liste `` - `x` Text `` = Chip mit Text daneben |
| `==Wort==` (alle Folien) | fett auf Gelb; erste Tabellenzelle ganz markiert = Zeile gelb |
| `[im Plan]{.success}` (`.warning`, `.danger`, `.info`, `.neutral`) | fett in der Signalfarbe |
| Front Matter `status.success: Erledigt; Fertig` + Tabellenzelle `` `Erledigt` `` (Flow-Folie) | Ampelpunkt „●" in der Farbe vor dem Text; nicht zugeordnet = grau |

- Flow-Folien nicht überladen: was nicht passt, wird bis zu zweimal um ein Achtel kleiner und
  dann auf „(Forts.)"-Folien geteilt (Hinweis `slide-split`); Karten, Flächen und Spalten
  werden nie geteilt. Mit Flow-Inhalt ist nur `layout="Nur Titel"` erlaubt.
- Signalfarben nur für Status; zur Hervorhebung `==…==` (Gelb).

Andere Namen sind Fehler; die Meldung listet die gültigen. Klammern, die nicht genau so aussehen
(`[a] {.success}`, `## Mengen {a, b}`), bleiben Text.
- Text vor dem ersten `#` wird ignoriert; Fußnoten werden auf Folien weggelassen.

## Aus Python statt per Befehl

```python
from pta_documents.errors import DocumentConversionError
from pta_documents.generation.docx.generator import (
    DocxGenerator,
)  # bzw. pptx.generator.PptxGenerator
from pta_documents.markdown import DocumentResource, MarkdownDocument, content_type_of

document = MarkdownDocument(
    markdown, [DocumentResource("images/a.jpg", content_type_of("a.jpg"), data)]
)
try:
    with open("documents/x/x-bericht.docx", "wb") as out:
        result = DocxGenerator().generate(document, out)
    print(result)  # Hinweise als Liste "- line 12: …", sonst "No notes."
except DocumentConversionError as error:
    print(error.reason)  # was im Markdown zu ändern ist
```

Mit `.venv/bin/python` ausführen. Optionen (`DocxOptions`, `PptxOptions`) gibt es auch, das Front
Matter hat aber Vorrang — im Zweifel nur Front Matter verwenden.

## Vorhandene Dateien lesen

Um eine Word- oder PowerPoint-Datei des Anwenders zu verstehen oder zu überarbeiten:

```python
from pta_documents.conversions.docx import DocxConverter  # bzw. conversions.pptx.PptxConverter

document = DocxConverter().convert(open("documents/x/alt.docx", "rb"))
document.text  # Markdown
document.resources  # Bilder: .path (images/image1.png), .content (bytes)
```

Sprechernotizen einer Folie kommen als `::: notes` … `:::` nach ihrem Inhalt
(`ConversionOptions(notes=False)` lässt sie weg). Das Ergebnis ist ein Lesestand, kein verlustfreies Abbild: Folien verlieren Ebenen und
Formatierung, Word verliert u. a. Durchstreichung und Fußnoten. Vor dem Neu-Erzeugen das Markdown
nach den Regeln oben aufbereiten (Front Matter, `#`/`##`-Gliederung) und die Bilder nach
`images/` schreiben.

## Checkliste vor der Übergabe

- [ ] `./run.sh generate documents/<thema>` läuft ohne `ERROR` und möglichst ohne Hinweise
      (`--strict` endet dann mit Code 0); verbleibende Hinweise dem Anwender nennen.
- [ ] Word: `titel` gesetzt (bei Deckblatt-Vorlagen), Kapitel mit `#`, keine Handnummern.
- [ ] Präsentation: kein Inhalt unter Kapitel- und Abschluss-`#`, keine „(Forts.)"-Folien, die
      nicht gewollt sind.
- [ ] Fremde Bilder: Lizenz und Urheber genannt, `QUELLEN.md` geschrieben.
- [ ] Dem Anwender die erzeugten Dateien nennen und sagen, dass Word beim Öffnen eines
      Inhaltsverzeichnisses fragt, ob Felder aktualisiert werden sollen („Ja").
