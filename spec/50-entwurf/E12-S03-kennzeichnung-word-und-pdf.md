# E12-S03 Kennzeichnung „Vertraulich" und „Entwurf" in Word und PDF

> Status: Entwurf
> Epic: [E12 Dokumentpflege: Historie, Vergleich, Kennzeichnung](E12-dokumentpflege.md)

## Zusammenfassung

Front Matter `kennzeichnung: vertraulich | intern | entwurf | kein` setzt in Word und PDF eine
Kennzeichnung in die Kopfzeile — „Vertraulich" oder „Für den internen Gebrauch" in PTA-Blau neben
dem Logo — und bei `entwurf` zusätzlich ein Wasserzeichen „ENTWURF" über jede Seite. In
PowerPoint entspricht das dem Sticker aus E04-S05; beide sollen über denselben Schlüssel laufen.

## Kontext

- E04-S05 plant für Folien `sticker: vertraulich | intern | kein` nach dem Muster der
  Schulungsvorlage („Für den internen Gebrauch", „VERTRAULICH"). Für Word gibt es in den
  Vorlagen kein Muster; die Designanalyse zeigt Kopfzeile mit Logo oben rechts (2,22 × 1,28 cm,
  Hochformat) und Verlaufslinie darunter, Varianten mit Deckblatt haben eine eigene erste
  Kopfzeile.
- Der DOCX-Writer übernimmt Kopf- und Fußzeilen der Vorlage und ersetzt nur Texte (`firma`,
  Datum; E03-S01). Eine Kennzeichnung ist ein weiterer Absatz in der Kopfzeile oder eine Form.
- Ein Word-Wasserzeichen ist technisch ein WordArt-Shape (`v:shape` mit `v:textpath`, Stil
  `mso-position-horizontal:center`, Drehung −45°, hellgraue Füllung, `o:allowincell="f"`) im
  Kopfzeilenteil; Word zeigt es hinter dem Text jeder Seite des Abschnitts.
- Im PDF (E05-S03) zeichnet die Layout-Engine Kopf- und Fußzeile selbst; Text und Wasserzeichen
  sind dort gewöhnliche Zeichenbefehle (reportlab `saveState/rotate/setFillAlpha`).
- Texte folgen `sprache` (`GeneratedTexts`, E01-S01): „Vertraulich"/„Confidential", „Für den
  internen Gebrauch"/„For internal use only", „Entwurf"/„Draft".

## Vorgeschlagener Ansatz

1. **Schlüssel:** `kennzeichnung` in `front_matter.Keys`, Werte `vertraulich`, `intern`,
   `entwurf`, `kein`; `Marking` als `StrEnum` in `design/variants.py`, verwendet von
   `DocxOptions.marking`, `PdfOptions.marking` und — statt `sticker` — `PptxOptions.marking`
   (Frage 1). Standard: Word/PDF `kein`; PPTX wie E04-S05 (`schulung` → `intern`).
2. **Word, Text in der Kopfzeile** (`generation/docx/writer.py`, `_marking(header)`): ein
   rechtsbündiger Absatz unter dem Logo in jeder Kopfzeile des Dokuments (erste Seite
   eingeschlossen), Formatvorlage „Kopfzeile" der Vorlage, 9 pt, Versalien, PTA-Blau `006FB9`
   über die Theme-Farbe (`w:color w:themeColor="accent1"`), kein Hex. Maß und Abstand im
   Designmodell (`design/word.py`, `MARKING_AREA`), geprüft im Vergleichstest mit der Vorlage
   (E01-S01). Auf dem Deckblatt steht die Kennzeichnung zusätzlich unter der Zeile „Autor, Ort,
   Datum" (E03-S01), damit ein ausgedrucktes Deckblatt sie zeigt.
3. **Word, Wasserzeichen** bei `entwurf`: ein `v:shape` „PowerPlusWaterMarkObject" in jeder
   Kopfzeile — Text „ENTWURF"/„DRAFT", Segoe UI, Füllung `AFAFAF` (Akzent 5 der Palette) mit 50 %
   Deckkraft, diagonal, so groß wie die Diagonale des Satzspiegels zulässt. Das Markup ist fest
   als Vorlage in `design/word.py` hinterlegt (VML, von Word 365 getestet) und wird nur mit Text
   gefüllt. `entwurf` setzt außerdem den Text „Entwurf" nach Schritt 2.
4. **PDF** (E05-S03): die Layout-Engine zeichnet denselben Text an derselben Stelle und das
   Wasserzeichen als gedrehten Text mit 50 % Alpha hinter dem Inhalt; die PDF/A-2b-Prüfung
   (veraPDF) bleibt grün (Transparenz ist in PDF/A-2 erlaubt).
5. **PowerPoint:** E04-S05 schreibt den Sticker; hier nur die Umstellung auf den gemeinsamen
   Schlüssel und der neue Wert `entwurf` (Sticker „ENTWURF"/„DRAFT" im selben Muster) — mit
   dem Hinweis im Authoring Guide, dass ein Entwurfs-Deck beim Kunden den Sticker trägt.
6. **Tests** `tests/generation/docx/test_marking.py`: Text in allen Kopfzeilen und auf dem
   Deckblatt, Wasserzeichen nur bei `entwurf`, englische Texte, `kein` ändert nichts an der
   Vorlage (Byte-Vergleich der Kopfzeilenteile), Rundreise unverändert (E07-S02 liest Kopfzeilen
   nicht). `docs/anleitung.md`, `docs/ki-anleitung.md` und `samples/funktionen/varianten-dokument.md`
   zeigen `kennzeichnung`.

## Akzeptanzkriterien

- [ ] `kennzeichnung: vertraulich` zeigt „VERTRAULICH" in PTA-Blau in der Kopfzeile jeder Seite
      und auf dem Deckblatt; `entwurf` zusätzlich das Wasserzeichen; `kein` lässt die Vorlage
      unverändert.
- [ ] Texte folgen `sprache`; Farbe über Theme-Farbe, kein Hex.
- [ ] Word öffnet das Dokument ohne Reparatur; das Wasserzeichen steht hinter dem Text und lässt
      sich in Word über *Entwurf → Wasserzeichen entfernen* löschen (Prüfpunkt Mensch).
- [ ] Derselbe Schlüssel wirkt in PowerPoint als Sticker (nach E04-S05).

## Offene Fragen

1. Ein gemeinsamer Schlüssel `kennzeichnung` für alle Formate (Vorschlag; E04-S05 wird dann
   angepasst, `sticker` entfällt) — oder `sticker` für Folien behalten, weil die PTA den
   Begriff so verwendet?

> (2026-11-07) Gemeinsamer Schlüssel `kennzeichnung` für alle Formate; E04-S05 ist angepasst,
> `sticker` entfällt.

2. Wasserzeichen auch für `vertraulich` (groß über die Seite) oder nur der Text in der
   Kopfzeile? Vorschlag: nur Text — ein Wasserzeichen „VERTRAULICH" stört beim Lesen eines
   fertigen Dokuments, „ENTWURF" soll stören.

>

## Notizen

- Abhängigkeiten: E04-S05 (Sticker), E05-S03 (PDF-Seitenrahmen) für den PDF-Teil.
