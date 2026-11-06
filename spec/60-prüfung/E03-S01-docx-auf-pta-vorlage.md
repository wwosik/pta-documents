# E03-S01 DOCX auf der PTA-Vorlage

> Status: in Prüfung
> Epic: [E03 DOCX-Generator auf den PTA-Word-Vorlagen](../50-entwurf/E03-docx-generator.md)
> Milestone: [M01 PTA-Dokumente aus Markdown](../50-entwurf/M01-pta-dokumente-aus-markdown.md)

## Zusammenfassung

Der Rahmen des DOCX-Generators: die gewählte PTA-Vorlage laden, ihren Beispielinhalt entfernen,
Deckblatt, Kopf- und Fußzeile, Inhaltsverzeichnis und Dokumenteigenschaften aus dem Markdown
füllen und als `.docx` (nicht `.dotx`) speichern.

## Kontext

Die Vorlagen (Werte in der [Designanalyse](../10-analysen/2026-11-06%20pta-designstandards.md)):

| Variante | Datei | Seite | Deckblatt | Kopfzeile Folgeseiten | Fußzeile |
| -------- | ----- | ----- | --------- | --------------------- | -------- |
| `hoch` | `PTA-Dokument_Hochformat_mit-Deckblatt.dotx` | A4 hoch | ja (`Titel`, `Untertitel`, `Autor`) | `STYLEREF Titel` / `STYLEREF Untertitel` + Logo | „PTA IT-Beratung" · „Stand: …" · „Seite x \| y" |
| `hoch-ohne-deckblatt` | `PTA-Dokument_Hochformat_ohne-Deckblatt.dotx` | A4 hoch | nein | Titel/Untertitel als fester Text | wie oben |
| `quer` | `PTA-Dokument_Querformat_mit-Deckblatt.dotx` | A4 quer | ja | wie `hoch` | wie oben |
| `quer-ohne-deckblatt` | `PTA-Dokument_Querformat_ohne-Deckblatt.dotx` | A4 quer | nein | fester Text | wie oben |

Die Vorlagen enthalten SharePoint-Ballast: `customXml/` (Dokument-ID, ContentType),
`[trash]/`-Teile und benutzerdefinierte Eigenschaften (`_dlc_DocIdItemGuid`, `Wert der
Dokument-ID`).

## Vorgeschlagener Ansatz

1. **Vorlage laden** aus den Paketdaten, bereinigt nach [E01-S02](../60-prüfung/E01-S02-vorlagen-einbetten.md)
   (ohne SharePoint-Ballast, Inhaltstyp `.docx`).
2. **Körper leeren** bis auf das abschließende `w:sectPr` (Seitenformat, Ränder, Kopf-/
   Fußzeilenbezüge bleiben).
3. **Deckblatt** (nur Varianten mit Deckblatt) aus dem Front Matter: `titel` → `Titel`,
   `untertitel` → `Untertitel`, `autor`, `ort`, `datum` → `Autor` („Autor, Ort, Datum"; fehlende
   Teile entfallen samt Komma), dann Seitenumbruch. `#` im Text ist „Überschrift 1", nie der
   Titel. Fehlt `titel` in einer Variante mit Deckblatt, wirft der Generator
   `DocumentConversionError`. Ohne Deckblatt-Variante wandern Titel und Untertitel in die
   Kopfzeile.
4. **Kopfzeile:** in Varianten mit `STYLEREF` übernimmt Word den Titel selbst; in den anderen
   werden „Titel des Dokuments"/„Untertitel des Dokuments" durch Titel/Untertitel ersetzt.
5. **Fußzeile:** „Stand: xx.xx.xxxx" → Datum (`datum` im Front Matter, sonst heute, Format
   `TT.MM.JJJJ`); Firmenzeile aus der Vorlage bleibt („PTA IT-Beratung"), überschreibbar per
   Front Matter `firma`. Mit `sprache: en` „As of"/„Page".
6. **Inhaltsverzeichnis** nur auf Wunsch: Front Matter `inhaltsverzeichnis: ja` setzt „Inhalt" (`Zwischenüberschrift`) und ein
   TOC-Feld `\o "1-2" \h \z \u` wie in der Vorlage, mit `w:updateFields` in `settings.xml`, damit
   Word es beim Öffnen füllt.
7. **Dokumenteigenschaften:** `dc:title`, `dc:subject` (Untertitel), `dc:creator`,
   `cp:lastModifiedBy`, Zeitstempel; „Robert Fischer"/„PTA GmbH" aus der Vorlage werden ersetzt
   bzw. geleert.
8. API: `DocxGenerator.generate(document: MarkdownDocument, output: BinaryIO, options:
   DocxOptions | None)`; Optionen: `variant`, `date`, `company`, `toc`, `language` (englisch im
   Code, deutsch im Front Matter; Front Matter überschreibt die Optionen).

## Akzeptanzkriterien

- [ ] Für jede der vier Varianten entsteht aus einem Markdown mit Titel und zwei Kapiteln ein `.docx`,
      das Word und LibreOffice ohne Reparaturmeldung öffnen.
- [x] Kein Lorem-ipsum, kein „Titel des Dokuments", kein „xx.xx.xxxx" bleibt im Ergebnis.
- [x] Keine SharePoint-Kennungen und keine `[trash]`-Teile im Ergebnis.
- [x] Seitenformat, Ränder, Logo, Kopf-/Fußzeilenlinie entsprechen der Vorlage unverändert.

## Offene Fragen

1. Ab wann automatisch ein Inhaltsverzeichnis — nie (nur mit `toc: true`), immer, oder ab z. B.
   drei `##`-Kapiteln?

> (2026-11-06) Nur auf Wunsch (`inhaltsverzeichnis: ja`).

2. Firmenzeile in der Fußzeile: „PTA IT-Beratung" (vier PTA-Vorlagen) vs. „PTA Gruppe"
   (BPS-PTA-DATIS) — ist das je Vorlage fest, oder je nach Gesellschaft wählbar (z. B. „PTA GmbH")?

> (2026-11-06) Aus der Vorlage, per `firma:` überschreibbar.

3. Die Zeile `Autor` lautet in der Vorlage „Name Nachname, Ort, Datum". Woher kommt der Ort —
   Front Matter `location`?

> (2026-11-06) Front Matter `ort:`, optional.

4. Dürfen die bereinigten Vorlagen im Paket liegen (Weitergabe innerhalb der PTA), oder muss das
   Paket sie zur Laufzeit von einem Ort der PTA laden?

> (2026-11-06) Ja, im Paket.

## Notizen


## Implementierungsnotizen

- `generation/docx/generator.py` (`DocxGenerator.generate(document, output, options)`),
  `generation/docx/options.py` (`DocxOptions`: `variant`, `language`, `date`, `company`, `toc`),
  `generation/docx/writer.py` (Inhalt, in E03-S02 ausgebaut), Hilfen für WordprocessingML in
  `generation/common/openxml.py` (Text über mehrere Runs ersetzen, Feldcodes, `updateFields`
  an der schemagerechten Stelle).
- Gültige Front-Matter-Schlüssel: `vorlage`, `titel`, `untertitel`, `autor`, `ort`, `datum`,
  `firma`, `sprache`, `inhaltsverzeichnis` (+ `status.*` für E03-S03). `titelfolie` und
  `fusszeile` gehören nur zu den Folien und werden in Word abgelehnt.
- Titel und Autor fallen auf die Metadaten des `MarkdownDocument` zurück (wie DocLibs).
- **Deckblatt:** `Titel`, `Untertitel` (nur wenn angegeben), `Autor` mit „Autor, Ort, Datum" —
  das Datum erscheint dort nur, wenn `datum` (oder `DocxOptions.date`) gesetzt ist; die Fußzeile
  nimmt sonst das heutige Datum. Danach ein Seitenumbruch wie in der Vorlage.
- **Kopfzeile ohne Untertitel:** Der Absatz mit `STYLEREF Untertitel` wird entfernt, weil Word
  sonst „Fehler! Kein Text mit angegebener Formatvorlage …" anzeigt. Ohne Deckblatt wird ein
  fehlender Titel zu leerem Text.
- **Inhaltsverzeichnis:** „Inhalt"/„Contents" in `Zwischenüberschrift`, ein leeres TOC-Feld in
  `toc 1` und `w:updateFields` — Word füllt es beim Öffnen (mit der üblichen Rückfrage, ob Felder
  aktualisiert werden sollen). Danach ein Seitenumbruch.
- `sprache: en` ersetzt „Stand:" → „As of:" und „Seite " → „Page "; `firma` ersetzt
  „PTA IT-Beratung".
- Die Querformat-Vorlagen erhalten `Hyperlink`, `toc 1`, `toc 2` aus der Hochformat-Vorlage
  (`borrow_styles`).
- Eigenschaften: Titel, Betreff (= Untertitel), Autor, zuletzt geändert von (= Autor), Revision 1,
  Zeitstempel jetzt (UTC). „Firma" in `app.xml` bleibt „PTA GmbH" aus der Vorlage.
- **Prüfpunkt (offen):** Auf dieser Maschine gibt es weder Word noch LibreOffice. Geprüft ist,
  dass python-docx jedes Ergebnis wieder öffnet und dass Abschnittseigenschaften und Medien
  der Vorlage unverändert sind. Ein Test konvertiert mit LibreOffice nach PDF, wenn `soffice`
  vorhanden ist (sonst übersprungen). Bitte die Dateien aus `.tmp/review/frame-*.docx` einmal in
  Word öffnen — erstes Akzeptanzkriterium daher noch nicht abgehakt.
