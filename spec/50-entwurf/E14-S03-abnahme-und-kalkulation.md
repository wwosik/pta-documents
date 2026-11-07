# E14-S03 Unterschriftenblock und rechnende Tabellen

> Status: Entwurf
> Epic: [E14 Dokumenttypen der Beratung](E14-dokumenttypen-der-beratung.md)

## Zusammenfassung

Zwei Bausteine für Angebote und Abnahmen: `::: signatures` setzt einen Unterschriftenblock mit
Linien für Ort, Datum und Unterschrift je Partei; eine Tabelle mit `{.calc}` summiert ihre
Zahlenspalten, ergänzt auf Wunsch Netto, Mehrwertsteuer und Brutto und schreibt alle Zahlen im
deutschen Format. Beides wird beim Erzeugen berechnet und gezeichnet, in Word und PDF.

## Kontext

- Angebote und Abnahmeprotokolle enden mit Unterschriften; heute wird dafür in Word eine
  unsichtbare Tabelle von Hand gebaut. Summen in Angebotstabellen werden im Kopf oder in Excel
  gerechnet und abgetippt — eine Fehlerquelle, die der Kunde findet.
- Tabellen: `DocxWriter.table_block` (E03-S02, Tabellenformat „PTA", Spaltenbreiten aus dem
  Inhalt, Ausrichtung aus der Markdown-Tabelle); Attribute an Tabellen gibt es noch nicht — eine
  Zeile `{.calc}` direkt über der Tabelle folgt dem Muster von `{.build}` über Tabellen in
  vt-tools-libs (E09-S02) und wird in E02-S02 als Blockattribut geführt.
- Zahlenformat: `locale` ist in der Bibliothek tabu (prozessweit); das Format wird selbst
  geschrieben (Tausenderpunkt, Dezimalkomma, geschütztes Leerzeichen vor `€` und `%`), passend
  zu `sprache: en` mit Komma und Punkt getauscht.

## Vorgeschlagener Ansatz

1. **Unterschriftenblock** `::: signatures` mit je einer Zeile pro Partei im Container:
   `Auftraggeber: Muster AG, Erika Muster` / `Auftragnehmer: PTA IT-Beratung, {{autor}}`;
   ohne Inhalt die beiden Standardparteien. Darstellung (DOCX, PDF): rahmenlose Tabelle mit
   einer Spalte je Partei (höchstens drei, sonst Fehler), oben Rolle fett, darunter Firma und
   Name, dann drei Linien mit Unterschriften „Ort, Datum" und „Unterschrift" in „Beschriftung"
   (Stilnamen aus E03-S02); Block bleibt mit `keep together` auf einer Seite und steht nie allein
   auf einer neuen Seite ohne den letzten Absatz davor (`keep with next` am Vorgänger). Texte
   folgen `sprache`. Auf Folien ist der Container ein Fehler („Signatures belong in a document;
   remove the block or write the deck's closing slide").
2. **Rechnende Tabellen:** die Zeile `{.calc}` oder `{.calc mwst=19}` direkt über einer
   Markdown-Tabelle. `generation/common/calc_table.py`:
   - erkennt Zahlenspalten: jede Zelle außer der Kopfzeile ist leer oder eine Zahl in deutscher
     (`1.234,56`, `1234,56`, `12 %`, `99,00 €`) oder englischer Schreibweise; eine Spalte mit
     Text ist keine Zahlenspalte; eine Zahlenspalte mit einer nicht lesbaren Zelle ist ein Fehler
     mit Zeile und Zelle;
   - eine Zeile, deren erste Zelle `**Summe**` (oder `**Gesamt**`, `**Total**`) ist, bekommt die
     Spaltensummen eingetragen; Zellen, die der Autor dort schon gefüllt hat, werden geprüft und
     bei Abweichung als Fehler gemeldet („Line 40: the sum of 'Preis' is 12.300,00 €, not
     12.000,00 €") — so fällt ein Tippfehler auf;
   - fehlt die Summenzeile, wird sie angehängt;
   - `mwst=19` ersetzt die Summenzeile durch drei Zeilen Netto, `zzgl. 19 % MwSt.`, Brutto
     (nur für die Spalte, deren Kopf `Preis`, `Betrag`, `Summe`, `Netto` enthält, oder mit
     `spalte="Gesamt"` benannt); Rundung kaufmännisch (`decimal.ROUND_HALF_UP`) auf zwei Stellen;
   - `menge` × `einzelpreis`: steht `{.calc produkt="Menge*Einzelpreis=Gesamt"}`, wird die
     Spalte `Gesamt` zeilenweise berechnet, bevor summiert wird.
   Ausgabe: alle Zahlen der Zahlenspalten einheitlich formatiert (Stellenzahl der Spalte aus der
   genauesten Eingabe, Währungs- oder Prozentzeichen aus der Kopfzeile oder den Zellen),
   rechtsbündig; Summenzeilen fett. Gilt für DOCX, PDF und Folientabellen gleichermaßen.
3. **Rundreise:** die erzeugten Zeilen stehen als normale Tabellenzeilen im Dokument; der
   Konverter liest sie zurück; Rundreise-Test mit eigener Erwartung.
4. **Beispiel** `samples/angebot/` (Positionstabelle mit Menge, Einzelpreis, Gesamt, MwSt,
   Unterschriftenblock) — auch Grundlage des Skeletts `angebot` in E14-S04.
5. **Tests:** Erkennung der Zahlenspalten, deutsche und englische Eingabe, Summe geprüft und
   ergänzt, MwSt-Zeilen, Produktspalte, Rundung (`0,005`), Fehlerfälle; Unterschriftenblock mit
   einer, zwei, drei Parteien, Fehler bei vier und auf Folien, `keep together` im XML.

## Akzeptanzkriterien

- [ ] `::: signatures` ergibt in Word und PDF einen Block mit Linien je Partei, der nicht über
      eine Seite bricht; auf Folien ein Fehler mit Hinweis.
- [ ] `{.calc}` trägt richtige Summen ein, meldet falsche vom Autor eingetragene Summen und
      formatiert alle Zahlen deutsch (englisch mit `sprache: en`).
- [ ] `mwst=19` ergibt Netto, MwSt und Brutto kaufmännisch gerundet; `produkt=` rechnet
      Zeilenwerte.
- [ ] Das Angebotsbeispiel erzeugt ohne Fehler; das Rücklesen zeigt die berechneten Zeilen.

## Offene Fragen

1. Zusätzlich zu den berechneten Werten ein Word-Feld `=SUM(ABOVE)` in die Summenzellen schreiben,
   damit Word nach einer Änderung mit F9 nachrechnet? Vorschlag: nein — das Feld zeigt bis zur
   Aktualisierung den alten Wert, und PDF kennt es nicht; wer ändert, erzeugt neu.

>

2. Reichen `mwst=19` (und `7`), oder braucht es Rabattzeilen (`rabatt=10`) und Zwischensummen je
   Abschnitt? Vorschlag: mit MwSt beginnen; Rabatt und Zwischensummen als Folge-Story, wenn
   Angebote in Markdown entstehen.

>

3. Deutsche Namen (`::: unterschriften`, `{.rechnen}`), falls E02-S02 Frage 1 so entschieden
   wird?

>

## Notizen

- Abhängigkeiten: E02-S02 (Container, Blockattribut über Tabellen), E03-S02 (Tabellen), E05
  (PDF-Darstellung des Blocks), E11-S01 (`{{autor}}` im Block).
