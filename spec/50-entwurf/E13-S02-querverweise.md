# E13-S02 Querverweise auf Kapitel, Tabellen und Abbildungen

> Status: Entwurf
> Epic: [E13 Lange Berichte: Abkürzungen, Querverweise, Barrierefreiheit](E13-lange-berichte.md)

## Zusammenfassung

Überschriften, Tabellen und Abbildungen bekommen Anker (`{#kosten}`), und ein Link darauf wird
zum Verweis mit Nummer: `[](#kosten)` → „Tabelle 3", `[siehe](#architektur)` → „siehe 2.1
Architektur". In Word sind das `REF`-Felder auf Lesezeichen, die Word beim Aktualisieren
nachführt; im PDF interne Links; in PowerPoint der Text ohne Nummer.

## Kontext

- Heading-Attribute (`generation/common/heading_attributes.py`) kennen `.closing` und
  `layout="…"`; `{#id}` ist dort heute ein Fehler („Unknown heading attribute"). E02-S02 erweitert
  die Attribute; `#id` kommt hinzu.
- Beschriftungen schreibt der DOCX-Writer als `SEQ`-Felder (`writer.py`, Z. 325: `SEQ {label}
  \* ARABIC`) mit dem aktuellen Wert als Feldergebnis; Überschriften sind nummeriert über die
  Nummerierung der Vorlage (E03-S02). Word kann auf beides mit `REF <lesezeichen> \h` (Text),
  `\n` (Nummer der Überschrift) und `\p` (oben/unten) verweisen, wenn ein Lesezeichen
  (`w:bookmarkStart`/`w:bookmarkEnd`) um den Zielabsatz liegt.
- Links schreibt der Writer als Hyperlinks (E03-S02); ein Link auf `#…` ist heute ein externer
  Hyperlink mit leerem Ziel — schlecht.
- Der Konverter (E07-S02) liest `REF`-Felder als ihren Ergebnistext zurück; die Rundreise verliert
  den Verweis (Erwartungsdatei).

## Vorgeschlagener Ansatz

1. **Anker:**
   - Überschriften: `## Architektur {#architektur}` (Attribut `#id` in `heading_attributes.py`,
     für alle Formate; `id` nach `[a-z][a-z0-9-]*`). Ohne Attribut bekommt jede Überschrift einen
     automatischen Anker aus ihrem Text (`architektur`, Umlaute transliteriert, Duplikate mit
     `-2`), damit `[](#architektur)` ohne Zusatz geht;
   - Tabellen: `Tabelle: Kosten je Phase {#kosten}` an der Beschriftung (E03-S02);
   - Abbildungen: `![Alt](bild.png "Unterschrift {#ueberblick}")` im Titel, oder `{#id}` als
     eigener Absatz direkt unter dem Bild (Frage 1).

   Doppelte Anker sind Fehler mit beiden Zeilen.
2. **Verweise:** ein Link mit Ziel `#id`:
   - leerer Linktext `[](#kosten)` → „Tabelle 3" / „Abbildung 2" / „2.1" (Überschriftennummer),
     bei `sprache: en` „Table 3", „Figure 2";
   - Linktext vorhanden `[siehe](#architektur)` → „siehe 2.1 Architektur": Text, Leerzeichen,
     Nummer und Titel — Frage 2 zur Form;
   - `[](#architektur "titel")` → nur der Überschriftentext, `"nummer"` → nur die Nummer,
     `"seite"` → „S. 12" (Word `\p`/`PAGEREF`, PDF Seitenzahl, PowerPoint Foliennummer).

   Ein Verweis auf einen unbekannten Anker ist ein Fehler mit Zeile und den bekannten Ankern.
3. **Word** (`generation/docx/writer.py`): Lesezeichen `_Ref_<id>` um den Zielabsatz
   (Überschrift) bzw. um das `SEQ`-Feld der Beschriftung; Verweis als komplexes Feld
   `REF _Ref_kosten \h` (Text der Beschriftung bis zum Doppelpunkt: `\# ""`, bei Beschriftungen
   das Feld „nur Bezeichnung und Nummer" über `\r`? — Word nutzt dafür `REF … \r \h` auf das
   Lesezeichen um `Tabelle` + `SEQ`), mit berechnetem Feldergebnis, sodass das Dokument vor dem
   Aktualisieren stimmt; `\h` macht den Verweis anklickbar. Nummern berechnet der Writer wie
   Word (Nummerierungsdefinition der Vorlage, `SEQ`-Zähler), eine Hilfsklasse `Numbering` in
   `generation/common/`.
4. **PDF** (E05-S02): Layout-Engine kennt Anker als Ziele und schreibt interne Links
   (`/Dest`), Nummern aus denselben Zählern; „S. 12" erst im zweiten Durchlauf (Seitenzahlen
   stehen nach dem Umbruch fest).
5. **PowerPoint:** Verweis als Text ohne Nummer („siehe Architektur"), `"seite"` → „Folie 7"
   mit Hyperlink auf die Folie (`a:hlinkClick` mit `ppaction://hlinksldjump`).
6. **Tests** `tests/generation/docx/test_cross_references.py`: Anker automatisch und explizit,
   Duplikate, unbekanntes Ziel, alle Verweisformen, Feldergebnis gleich Word-Berechnung (ein
   Prüfpunkt Mensch: *Alles aktualisieren* in Word ändert nichts); Rundreise mit Abweichung.
   Anleitungen und `samples/funktionen/funktionen-bericht.md` zeigen Verweise.

## Akzeptanzkriterien

- [ ] `[](#kosten)` auf eine Tabellenbeschriftung ergibt „Tabelle 3" als `REF`-Feld mit
      richtigem Ergebnis; *Alles aktualisieren* in Word ändert nichts.
- [ ] Verweise auf Überschriften zeigen Nummer und Titel, mit Linktext davor.
- [ ] Doppelte Anker und unbekannte Ziele sind Fehler mit Zeile.
- [ ] In PowerPoint erscheinen Verweise als Text, Folienverweise als Sprung.

## Offene Fragen

1. Anker an Abbildungen: im Bildtitel (`"Unterschrift {#id}"`, Vorschlag — eine Zeile) oder als
   eigener Absatz `{#id}` unter dem Bild?

> (2026-11-07) Im Bildtitel.
2. Form eines Überschriftenverweises mit Text: „siehe 2.1 Architektur" (Vorschlag), „siehe
   Kapitel 2.1" oder „siehe Abschnitt »Architektur«"? Vielleicht als Option
   `querverweise: nummer-und-titel | kapitel | titel`.

> (2026-11-07) „siehe 2.1 Architektur“; die Option `querverweise:` kann es ändern.

## Notizen

- Abhängigkeiten: E02-S02 (Heading-Attribute), E03-S02 (Beschriftungen); PDF mit E05-S02.
- Die Zähler-Hilfsklasse `Numbering` dient auch dem Abbildungs- und Tabellenverzeichnis aus
  Epic-Frage 1.
