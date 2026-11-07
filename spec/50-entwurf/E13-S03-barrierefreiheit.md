# E13-S03 Barrierefreiheit: Alt-Texte, Struktur, PDF/UA

> Status: Entwurf
> Epic: [E13 Lange Berichte: Abkürzungen, Querverweise, Barrierefreiheit](E13-lange-berichte.md)

## Zusammenfassung

Erzeugte Dokumente erfüllen, was Word's Barrierefreiheitsprüfung und PDF/UA verlangen und der
Generator ohnehin weiß: jedes Bild hat einen Alt-Text oder ist als Dekoration markiert, Tabellen
haben Kopfzeilen, das Dokument eine Sprache und einen Titel, die Lesereihenfolge folgt dem
Markdown. Für PDFs wird geklärt, wie weit PDF/UA-1 mit der Layout-Engine aus E05 geht.

## Kontext

- Der DOCX-Writer schreibt heute `wp:docPr descr` aus dem Alt-Text (`writer.py`, Z. 360 ff.) und
  `w:tblHeader` an der Kopfzeile (Z. 812); Titel und Autor stehen in den Dokumenteigenschaften
  (E03-S01). Ein Bild ohne Alt-Text (`![](bild.png)`) geht ohne Meldung durch.
- Die PPTX-Writer setzen `descr` an Bildern (E04-S02); Folienlayouts der Vorlage bestimmen die
  Lesereihenfolge über die Platzhalterreihenfolge — der Generator füllt sie in Markdown-Reihenfolge.
- Word's Barrierefreiheitsprüfung bemängelt: fehlende Alt-Texte, Tabellen ohne Kopfzeile,
  verbundene Zellen, fehlende Dokumentsprache (`w:lang` in `w:docDefaults`, aus der Vorlage
  `de-DE`), Überschriften als Direktformat (hier nie), Text ohne Kontrast (hier Vorlage).
- PDF/UA-1 (ISO 14289) verlangt getaggtes PDF: Strukturbaum (`/StructTreeRoot`, `H1`, `P`,
  `Table/TR/TH/TD`, `Figure` mit `/Alt`), `/MarkInfo /Marked true`, `/Lang`, Titel in XMP,
  Lesezeichen. reportlab schreibt Tags nur über seine Low-Level-API (`canvas.beginMarkedContent`
  o. Ä. fehlt; Struktur nur mit eigener Erweiterung), pikepdf kann den Baum nachträglich bauen,
  wenn der Inhalt mit `BDC/EMC` markiert ist — das ist der kritische Punkt (Frage 1).
- Hinweise an den Schreiber kommen mit E08-S01; einige Prüfungen hier sind Hinweise, nicht
  Fehler.

## Vorgeschlagener Ansatz

1. **Alt-Texte:** ein Bild ohne Alt-Text und ohne Titel ist ein **Fehler** mit Zeile („Line 23:
   the image 'images/foto.jpg' has no alt text. Describe it in the brackets, or mark it
   decorative with {.deko}."); `![](bild.png){.deko}` (Attribut hinter dem Bild, E02-S02-Syntax)
   markiert Dekoration: Word `wp:docPr` mit `a16:decorative`-Erweiterung (`descr` leer),
   PowerPoint ebenso, PDF `Artifact`. Front Matter `barrierefreiheit: streng | hinweis`
   (Standard `hinweis`, Frage 2): bei `hinweis` ist der fehlende Alt-Text ein Hinweis
   (E08-S01, Code `alt-text-missing`), bei `streng` ein Fehler.
2. **Word-Struktur** (`generation/docx/writer.py`): Dokumentsprache aus `sprache` in
   `w:docDefaults` und an der Vorlage (`de-DE`/`en-GB`); Tabellen: `w:tblHeader` bleibt, dazu
   `w:tblCaption`/`w:tblDescription` aus Titel und Beschriftung; keine leeren Absätze als
   Abstandhalter (Prüfung der Writer-Ausgabe im Test); Hyperlinks mit sprechendem Text — ein
   Link, dessen Text die URL ist, wird Hinweis `link-text-is-url`; Dokumenttitel Pflicht (E03-S01
   verlangt ihn mit Deckblatt schon; ohne Deckblatt wird `titel` Hinweis).
3. **PowerPoint:** Lesereihenfolge im Test prüfen (Platzhalter in Markdown-Reihenfolge im
   `spTree`), Alt-Texte wie Word, Folientitel Pflicht (ist er), Dekoration wie Schritt 1.
4. **PDF** (mit E05): Stufe A — was ohne Tags geht: `/Lang`, Titel in XMP und `/ViewerPreferences
   /DisplayDocTitle true`, Lesezeichen aus Überschriften (E05-S02 plant sie), Alt-Texte an Bildern
   als `/Alt`. Stufe B — getaggtes PDF: Inhalt in der Layout-Engine mit `BDC/EMC` und
   `MCID` markieren, Strukturbaum mit pikepdf nach dem Schreiben aufbauen; Prüfung mit veraPDF
   (Profil PDF/UA-1) und PAC. Stufe B ist eine eigene Entscheidung nach einem Versuch (Frage 1).
5. **Prüfung im Test:** `tests/generation/test_accessibility.py` prüft die erzeugten Dateien von
   `samples/funktionen/` gegen eine Liste der Regeln aus Schritt 2–3 (Alt-Texte, Kopfzeilen,
   Sprache, keine leeren Absätze, Titel); die Word-Barrierefreiheitsprüfung ist Prüfpunkt des
   Menschen. `docs/ki-anleitung.md` bekommt die Regel, immer Alt-Texte zu schreiben, die den
   Inhalt beschreiben (nicht „Bild").

## Akzeptanzkriterien

- [ ] Ein Bild ohne Alt-Text ist bei `barrierefreiheit: streng` ein Fehler, sonst ein Hinweis;
      `{.deko}` markiert Dekoration in Word und PowerPoint.
- [ ] Word's Barrierefreiheitsprüfung meldet für `samples/funktionen/` keine Fehler (Prüfpunkt
      Mensch); Tabellen tragen Kopfzeile, Titel und Beschreibung, das Dokument seine Sprache.
- [ ] Die PDF-Stufe A ist umgesetzt, sobald E05 steht; der Versuch zu Stufe B ist dokumentiert
      und entschieden.

## Offene Fragen

1. PDF/UA (Stufe B): Versuch mit `BDC/EMC` + pikepdf machen (etwa drei Tage), oder bewusst nur
   PDF/A-2b mit Stufe A liefern und auf Word verweisen, das PDF/UA beim Export selbst schreibt?
   Vorschlag: Versuch nach E05-S02, Entscheidung mit Ergebnis in den Notizen.

>

2. Standard `hinweis` (Vorschlag — Bestandsdokumente laufen weiter) oder `streng`?

>

3. Gilt BITV für die Kunden der PTA tatsächlich (öffentliche Stellen), oder reicht die
   Word-Prüfung ohne Befund?

>

## Notizen

- Abhängigkeiten: E02-S02 (Attribute an Bildern), E08-S01 (Hinweise), E05 für den PDF-Teil.
- Die Alt-Text-Regel passt zu `samples/gsb/QUELLEN.md`: Bildunterschrift nennt Urheber und
  Lizenz, Alt-Text beschreibt den Inhalt — zwei verschiedene Dinge.
