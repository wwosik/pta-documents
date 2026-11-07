# E11-S03 Tabellen und Charts aus CSV- und Excel-Dateien

> Status: Entwurf
> Epic: [E11 Bausteine, Variablen und Datenquellen](E11-bausteine-variablen-datenquellen.md)

## Zusammenfassung

Eine Tabelle im Dokument kommt aus `daten/kosten.csv` oder einem Blatt von `daten/kosten.xlsx`,
statt im Markdown abgetippt zu werden; `chart`-Blöcke (E06-S01) nehmen dieselben Dateien als
Quelle. Zahlen aus dem Controlling landen so unverändert im Statusbericht und in der Präsentation.

## Kontext

- Tabellen schreibt heute der Writer aus dem `table`-Token des Parsers (E03-S02, E04-S02); eine
  Tabelle aus Daten muss denselben Weg nehmen, damit Stil (Tabellenformat „PTA", Kopf `004676` in
  Folien), Titelzeile, Beschriftung und das Teilen zu langer Folientabellen gleich bleiben.
- `chart`-Blöcke (E06-S01) tragen ihre CSV im Zaun; `ChartParser` liest sie. Eine Datei als Quelle
  ist dort nur eine zweite Eingabe für denselben Parser.
- Ressourcen: `tools/generate/generate.py` sammelt nur Bilddateien (`IMAGE_SUFFIXES`).
- Excel lesen: **openpyxl** (MIT, pure Python) für `.xlsx`; `.xls` und `.csv` mit
  Semikolon/Komma und deutschem Dezimalkomma über die Standardbibliothek (`csv`, `locale`-frei).

## Vorgeschlagener Ansatz

1. **Syntax** (Frage 1): ein Zaun
   ```table src=daten/kosten.csv``` bzw. ```table src=daten/kosten.xlsx#Kosten``` (Blattname nach
   `#`, sonst das erste Blatt), optional mit Attributen `bereich=A1:D12`, `kopf=1` (Kopfzeilen),
   `ausrichtung=lrr`. Der Zaun darf leer sein; steht etwas darin, ist es ein Fehler („write the
   table in Markdown or name a file, not both"). Ein fetter Absatz davor und `Tabelle: …` danach
   wirken wie bei Markdown-Tabellen (E03-S02).
2. **Datenmodul** `src/pta_documents/markdown/tabular.py`: `read_table(resource, sheet, range,
   header_rows) -> TableData(rows: list[list[str]], alignments)`; CSV-Dialekt per `csv.Sniffer`
   auf `;`/`,`/Tab, Kodierung UTF-8 mit BOM oder cp1252 (Excel-Export); XLSX über openpyxl im
   `read_only`-Modus, Formeln als zuletzt berechneter Wert (`data_only=True`), leere Zeilen am Ende
   abgeschnitten.
3. **Zahlenformat:** Zahlen werden nach `sprache` formatiert (`1.234,56` / `1,234.56`), ganze
   Zahlen ohne Nachkommastellen, Datumszellen als `TT.MM.JJJJ`; Excel-Zahlenformate (`0,0 %`,
   `#.##0 €`) werden in den häufigen Fällen übernommen (Prozent, Währung, feste Nachkommastellen),
   sonst der Rohwert. Numerische Spalten werden rechtsbündig, wenn `ausrichtung` fehlt.
4. **Einbindung:** ein Schritt vor dem Writer wandelt den `table`-Zaun in dieselben Token, die
   der Parser für eine Markdown-Tabelle liefert (`table_open` … `table_close` mit `map` auf die
   Zaunzeilen), sodass DOCX-, PPTX- und PDF-Writer nichts von der Datei wissen. Fehler nennen
   Datei und Zelle: „Line 40: daten/kosten.xlsx, sheet 'Kosten', cell C7 is not a number".
5. **Charts:** `ChartParser` (E06-S01) nimmt `src=` wie der Tabellenzaun; `read_table` liefert die
   Zeilen, der Rest bleibt gleich. `financial-chart` (E06-S02) ebenso.
6. **Werkzeug:** `generate.py` sammelt zusätzlich `.csv`, `.xlsx` (`DATA_SUFFIXES`) als
   `DocumentResource` mit `text/csv` bzw. dem OOXML-Typ; Extra `data = ["openpyxl>=3.1"]` in
   `pyproject.toml`; ohne das Extra ist eine XLSX-Quelle ein Fehler, der das Extra nennt.
7. **Tests** `tests/markdown/test_tabular.py` (CSV-Dialekte, Dezimalkomma, Blattwahl, Bereich,
   Fehlerzelle) und Rundreise: eine Tabelle aus CSV ergibt beim Rücklesen dieselbe
   Markdown-Tabelle wie ihr abgetipptes Gegenstück. `docs/anleitung.md`, `docs/ki-anleitung.md`
   und `samples/funktionen/` zeigen eine Tabelle und ein Chart aus Datei.

## Akzeptanzkriterien

- [ ] Eine CSV- und eine XLSX-Datei im Dokumentordner ergeben in Word und PowerPoint eine Tabelle
      im PTA-Stil, mit Titelzeile und Beschriftung wie eine Markdown-Tabelle.
- [ ] Zahlen erscheinen deutsch formatiert (englisch bei `sprache: en`), numerische Spalten
      rechtsbündig.
- [ ] Ein `chart`-Block mit `src=` zeichnet dieselbe Grafik wie der mit eingebetteter CSV.
- [ ] Fehler nennen Datei, Blatt und Zelle; eine fehlende Datei ist derselbe Fehler wie ein
      fehlendes Bild.

## Offene Fragen

1. Syntax: Zaun ```` ```table src=… ```` (Vorschlag — eine Form für Tabelle und Chart) oder ein
   Absatz `Tabelle aus: daten/kosten.csv` (lesbarer, aber ohne Platz für Attribute)?

>

2. Sollen große Dateien begrenzt werden (etwa 200 Zeilen, danach Fehler mit Hinweis auf
   `bereich=`)? In einer Folie passt ohnehin wenig; im Bericht wäre eine Tabelle über mehrere
   Seiten denkbar.

>

## Notizen

- Abhängigkeiten: E06-S01/E06-S02 für `src=` in Charts; Tabellen gehen vorher.
