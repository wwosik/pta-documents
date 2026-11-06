# E03-S01 DOCX auf der PTA-Vorlage

> Status: Entwurf
> Epic: [E03 DOCX-Generator auf den PTA-Word-Vorlagen](E03-docx-generator.md)
> Milestone: [M01 PTA-Dokumente aus Markdown](M01-pta-dokumente-aus-markdown.md)

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
| `bps-pta-datis` | `BPS-PTA-DATIS-Dokument.dotx` | A4 hoch | nein | fester Text + Gruppenlogo | „PTA Gruppe" · … |

Die Vorlagen enthalten SharePoint-Ballast: `customXml/` (Dokument-ID, ContentType),
`[trash]/`-Teile und benutzerdefinierte Eigenschaften (`_dlc_DocIdItemGuid`, `Wert der
Dokument-ID`).

## Vorgeschlagener Ansatz

1. **Vorlage laden** aus den Paketdaten, bereinigt nach [E01-S02](E01-S02-vorlagen-einbetten.md)
   (ohne SharePoint-Ballast, Inhaltstyp `.docx`).
2. **Körper leeren** bis auf das abschließende `w:sectPr` (Seitenformat, Ränder, Kopf-/
   Fußzeilenbezüge bleiben).
3. **Deckblatt** (nur Varianten mit Deckblatt): `#`-Überschrift → `Titel`, erster Absatz direkt
   darunter oder Front Matter `subtitle` → `Untertitel`, `author` + Ort/Datum → `Autor`, dann
   Seitenumbruch. Ohne Deckblatt-Variante wandert der Titel in die Kopfzeile.
4. **Kopfzeile:** in Varianten mit `STYLEREF` übernimmt Word den Titel selbst; in den anderen
   werden „Titel des Dokuments"/„Untertitel des Dokuments" durch Titel/Untertitel ersetzt.
5. **Fußzeile:** „Stand: xx.xx.xxxx" → Datum (`date` im Front Matter, sonst heute, Format
   `TT.MM.JJJJ`); Firmenzeile aus der Vorlage bleibt („PTA IT-Beratung" bzw. „PTA Gruppe"),
   überschreibbar per Front Matter `company`.
6. **Inhaltsverzeichnis:** Front Matter `toc: true` (Standard bei Dokumenten mit mehr als
   … Überschriften — siehe Offene Fragen) setzt „Inhalt" (`Zwischenüberschrift`) und ein
   TOC-Feld `\o "1-2" \h \z \u` wie in der Vorlage, mit `w:updateFields` in `settings.xml`, damit
   Word es beim Öffnen füllt.
7. **Dokumenteigenschaften:** `dc:title`, `dc:subject` (Untertitel), `dc:creator`,
   `cp:lastModifiedBy`, Zeitstempel; „Robert Fischer"/„PTA GmbH" aus der Vorlage werden ersetzt
   bzw. geleert.
8. API: `DocxGenerator.generate(document: MarkdownDocument, output: BinaryIO, options:
   DocxOptions | None)`; Optionen: `variant`, `date`, `company`, `toc`, `language`.

## Akzeptanzkriterien

- [ ] Für jede Variante entsteht aus einem Markdown mit Titel und zwei Kapiteln ein `.docx`,
      das Word und LibreOffice ohne Reparaturmeldung öffnen.
- [ ] Kein Lorem-ipsum, kein „Titel des Dokuments", kein „xx.xx.xxxx" bleibt im Ergebnis.
- [ ] Keine SharePoint-Kennungen und keine `[trash]`-Teile im Ergebnis.
- [ ] Seitenformat, Ränder, Logo, Kopf-/Fußzeilenlinie entsprechen der Vorlage unverändert.

## Offene Fragen

1. Ab wann automatisch ein Inhaltsverzeichnis — nie (nur mit `toc: true`), immer, oder ab z. B.
   drei `##`-Kapiteln?

>

2. Firmenzeile in der Fußzeile: „PTA IT-Beratung" (vier PTA-Vorlagen) vs. „PTA Gruppe"
   (BPS-PTA-DATIS) — ist das je Vorlage fest, oder je nach Gesellschaft wählbar (z. B. „PTA GmbH")?

>

3. Die Zeile `Autor` lautet in der Vorlage „Name Nachname, Ort, Datum". Woher kommt der Ort —
   Front Matter `location`?

>

4. Dürfen die bereinigten Vorlagen im Paket liegen (Weitergabe innerhalb der PTA), oder muss das
   Paket sie zur Laufzeit von einem Ort der PTA laden?

>

## Notizen

