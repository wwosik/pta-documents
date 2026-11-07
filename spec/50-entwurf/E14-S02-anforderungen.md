# E14-S02 Anforderungen mit stabilen IDs

> Status: Entwurf
> Epic: [E14 Dokumenttypen der Beratung](E14-dokumenttypen-der-beratung.md)
> Milestone: [M06 Inhalte, Dokumenttypen und Dokumentpflege](M06-inhalte-und-dokumentpflege.md)

## Zusammenfassung

`::: requirement` beschreibt eine Anforderung mit Titel, Text, Priorität und Status; der
Generator nummeriert sie (`REQ-001`, Präfix wählbar), zeigt sie als Kasten im Text und erzeugt am
Ende eine Anforderungsliste. Explizite IDs bleiben über Fassungen stabil, Dubletten sind Fehler,
Querverweise verweisen auf die ID.

## Kontext

- Konzepte und Lastenhefte nummerieren Anforderungen heute von Hand; beim Einschieben einer
  Anforderung verschieben sich alle folgenden Nummern, und Verweise im Text oder beim Kunden
  stimmen nicht mehr.
- Container und Attribute: E02-S02 (`layout_syntax`, `heading_attributes`); Querverweise und
  Lesezeichen: E13-S02 (`[](#id)` → Word-`REF`-Feld); Status-Farben: `design.colors.StatusCategory`
  (E02-S02); Front Matter mit Präfix: `status.<kategorie>` als Muster für `anforderungen.<…>`.
- `generation/docx/writer.py` schreibt Tabellen mit Beschriftung und Lesezeichen per lxml.

## Vorgeschlagener Ansatz

1. **Syntax** `::: requirement [ID] {prio=muss|soll|kann status=offen|akzeptiert|umgesetzt|verworfen}`:
   erste Zeile des Inhalts ist der Titel (ein Absatz, kein `#`), danach beliebiger Text, Listen
   und Tabellen. Ohne ID vergibt der Generator die nächste freie Nummer; mit ID (`REQ-007`) wird
   sie übernommen. Lücken sind erlaubt, eine doppelte ID ist ein Fehler mit beiden Zeilen, eine
   ID mit fremdem Präfix ebenso. Standardwerte: `prio=soll`, `status=offen`.
2. **Front Matter** `anforderungen.praefix: ANF` (Standard `REQ`), `anforderungen.liste: ja|nein`
   (Standard `ja`: Liste am Ende), `anforderungen.start: 100` (erste automatische Nummer).
   Registriert als Präfixschlüssel wie `status.*`.
3. **Modell** `generation/common/requirements.py`: `collect(tokens, options, line_offset) ->
   list[Requirement(id, title, priority, status, line, section)]`; `section` ist die Überschrift,
   unter der die Anforderung steht (für die Liste). Vergabe automatischer Nummern erst nach dem
   Sammeln aller expliziten, damit `REQ-007` nie doppelt entsteht.
4. **Darstellung im Text:** DOCX/PDF als Kasten (Tabelle mit einer Zelle im Tabellenformat
   „PTA" ohne Kopfzeile, Rahmen in PTA-Blau): Kopfzeile `REQ-001 · Titel`, rechts Priorität und
   Status als Labels in Statusfarben, darunter der Text. Das Lesezeichen heißt wie die ID, damit
   `[](#REQ-001)` (E13-S02) „REQ-001" bzw. mit Text „siehe REQ-001 Titel" ergibt. PPTX: eine
   Anforderung als Callout (E04-S03) mit Kennung; mehrere nacheinander werden Karten.
5. **Anforderungsliste:** am Dokumentende `## Anforderungen` als Tabelle (ID | Titel | Prio |
   Status | Abschnitt) mit Beschriftung; die ID ist ein Verweis auf den Kasten. Alternativ an
   anderer Stelle über eine Zeile `{.requirements}` (leerer Absatz mit Klasse), die die Liste dort
   einfügt und das automatische Ende abschaltet.
6. **Export:** `./run.sh export documents/<thema>/konzept.md --requirements` schreibt
   `konzept-anforderungen.csv` (UTF-8 mit BOM, Semikolon, für Excel in deutscher Einstellung);
   dasselbe Werkzeug exportiert mit `--tasks` die Aufgaben aus E14-S01. Die Bibliothek liefert
   die Daten als Liste, das Werkzeug schreibt die Datei.
7. **Prüfung** (E08-S02): Anforderung ohne Text (nur Titel) → Hinweis; `status=verworfen` ohne
   Begründungsabsatz → Hinweis; IDs, auf die nichts verweist, sind kein Hinweis.
8. **Tests:** automatische und explizite IDs gemischt, Dublette, fremdes Präfix, Liste am Ende
   und per `{.requirements}`, Lesezeichen im DOCX vorhanden, Rundreise mit eigener Erwartung
   (der Kasten wird als Tabelle zurückgelesen — Abweichung festhalten), CSV-Export.

## Akzeptanzkriterien

- [ ] Anforderungen ohne ID werden lückenlos nummeriert; explizite IDs bleiben, Dubletten und
      fremde Präfixe brechen mit Zeilen ab.
- [ ] Der Kasten zeigt ID, Titel, Priorität, Status in Statusfarben; die Liste am Ende führt
      alle Anforderungen mit Abschnitt und verweist auf die Kästen.
- [ ] `[](#REQ-001)` ergibt einen Querverweis (E13-S02), auch im PDF als Link.
- [ ] `./run.sh export --requirements` schreibt eine CSV, die Excel ohne Nachfrage öffnet.

## Offene Fragen

1. Prioritätswerte: `muss | soll | kann` (Vorschlag, deutsch wie Front-Matter-Werte, nach der
   üblichen MuSS/SOLL/KANN-Einteilung) oder MoSCoW (`must | should | could | won't`)?

> (2026-11-07) `muss | soll | kann`.
2. Soll der CSV-Export Teil dieser Story sein oder in ein eigenes Werkzeug `export` mit mehr
   Zielen (Aufgaben, Historie, Abkürzungen) ausgelagert werden? Vorschlag: hier beginnen, das
   Werkzeug heißt von Anfang an `export`.

> (2026-11-07) Hier beginnen; das Werkzeug heißt `export`.
3. Deutsche Containernamen (`::: anforderung`), falls E02-S02 Frage 1 so entschieden wird?

> (2026-11-07) Englisch — Entscheidung zu E02-S02 Frage 1 vom 2026-11-07 gilt für alle neuen Syntaxnamen.

## Notizen

- Abhängigkeiten: E02-S02 (Container, Attribute, Statusfarben), E03-S02 (Tabellen), E13-S02
  (Querverweise auf die ID). Ohne E13-S02 steht die ID als Text ohne Link.
