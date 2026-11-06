# E01-S02 Vorlagen bereinigen und einbetten

> Status: in Prüfung
> Epic: [E01 PTA-Design als einziges Design](../50-entwurf/E01-pta-design.md)
> Milestone: [M01 PTA-Dokumente aus Markdown](../50-entwurf/M01-pta-dokumente-aus-markdown.md)

## Zusammenfassung

Die Vorlagen aus `source-templates/` werden einmal bereinigt und als Paketdaten in
`pta_documents/design/templates/` mitgeliefert, sodass die Generatoren keine Datei von außen lesen.

## Kontext

Laut [Designanalyse](../10-analysen/2026-11-06%20pta-designstandards.md) enthalten alle Vorlagen
SharePoint-Kennungen (`customXml/`, `_dlc_DocIdItemGuid`, `Wert der Dokument-ID`), `[trash]/`-Teile
und Bearbeiternamen; die PowerPoint-Dateien zusätzlich 39–93 Musterfolien (Vorlagensammlung
~20 MB, mit think-cell-Objekten) und Bildschirmfotos der Anleitungsfolien.

## Vorgeschlagener Ansatz

1. Werkzeug `tools/prepare-templates/` (Python, über `run.sh prepare-templates`), das aus
   `source-templates/` die Paketdaten erzeugt:
   - **Word** (die vier PTA-Vorlagen; BPS-PTA-DATIS nicht): `[trash]/`, `customXml/` samt Beziehungen, SharePoint-Eigenschaften
     entfernen; Kerneigenschaften leeren; Körper bis auf `w:sectPr` leeren; Inhaltstyp auf
     Dokument (`.docx`) umstellen.
   - **PowerPoint** (Basis, Schulung, Titelfolie EN für `sprache: en`): alle Musterfolien entfernen (Teile, Beziehungen,
     `sldIdLst`, Notizen), nicht mehr referenzierte Medien löschen (Anleitungs-Screenshots), die
     35 Layouts, Master, Theme und die Layout-Medien behalten; Inhaltstyp auf Präsentation
     (`.pptx`). Die Vorlagensammlung wird nicht eingebettet (gleiche Layouts wie die Basis).
2. Das Werkzeug ist deterministisch (feste Zeitstempel in den ZIP-Einträgen), damit ein erneuter
   Lauf ohne Vorlagenänderung keinen Diff erzeugt; die Ergebnisse werden versioniert.
3. Test: jede eingebettete Vorlage öffnet sich mit python-docx bzw. python-pptx; Theme,
   Formatvorlagen, Master und Layouts sind bytegleich zum Original; keine SharePoint-Kennung,
   kein Personenname im Paket.
4. Größe prüfen und im Plan notieren (Basisvorlage ohne Musterfolien geschätzt 3–5 MB wegen der
   Hintergrundfotos).

## Akzeptanzkriterien

- [x] `./run.sh prepare-templates` erzeugt die Paketdaten aus `source-templates/` reproduzierbar.
- [x] Die eingebetteten Vorlagen enthalten keine Musterfolien, keinen Mustertext, keine
      SharePoint-Kennungen und keine Personennamen.
- [x] Theme, Formatvorlagen, Master und Layouts sind unverändert.

## Offene Fragen

1. Dürfen die Vorlagen (mit den Hintergrundfotos) im Paket liegen?

> (2026-11-06) Ja, im Paket.

## Notizen


## Implementierungsnotizen

- Werkzeug `tools/prepare-templates/prepare-templates.py` (`./run.sh prepare-templates`,
  `--check` vergleicht nur). Es arbeitet generisch auf dem OPC-Paket: Beziehungen der Typen
  `customXml`, `custom-properties`, `thumbnail`, `commentAuthors`, `slide`, `attachedTemplate`
  werden entfernt, danach werden alle Teile gelöscht, die keine Beziehung mehr erreicht
  (dadurch verschwinden `customXml/`, `[trash]/`, Musterfolien, Notizen, Diagramme, OLE-Objekte
  und nicht mehr genutzte Medien), und `[Content_Types].xml` wird bereinigt.
- Word: Körper bis auf `w:sectPr` geleert, Inhaltstyp `document.main+xml`. PowerPoint:
  `sldIdLst`, `custShowLst` und die Abschnittsliste (`p14:sectionLst`) entfernt, Inhaltstyp
  `presentation.main+xml`.
- `core.xml` wird ersetzt (leerer Titel/Autor/Bearbeiter, Zeitstempel 2000-01-01);
  `app.xml` wird neu geschrieben mit Firma „PTA GmbH" (Word) bzw. „PTA Unternehmensberatung"
  (PowerPoint), ohne Vorlagenname, Seiten- und Folientitel.
- Deterministisch: feste ZIP-Zeitstempel, Reihenfolge der Einträge wie in der Quelle; ein
  zweiter Lauf schreibt nichts (Test `test_embedded_templates_are_up_to_date`).
- **Größen:** Word je 25–30 KB; PowerPoint je ~5,8 MB (Hintergrundfotos der Titel-, Agenda-,
  Trenn- und Abschlusslayouts), zusammen ~18 MB im Paket und im Repo.
- **Englisches Logo:** In `PTA-Powerpoint-Titelfolie EN.pptx` liegt das englische Logo nur auf der
  Musterfolie, nicht im Layout. Das Werkzeug legt es zusätzlich als `slides-logo-en.png` ab
  (`templates.ENGLISH_LOGO`), damit E04-S05 es auf die Titelfolie setzen kann (Position auf der
  Musterfolie: 1,40 / 1,30 cm, 6,35 × 3,59 cm).
- Zugriff im Code über `pta_documents.design.templates` (`importlib.resources`).
- Tests: keine SharePoint-/Papierkorbteile, keine Personennamen, Formatvorlagen, Nummerierung,
  Theme, Kopf-/Fußzeilen, Master und Layouts bytegleich zur Quelle; Öffnen mit python-docx und
  python-pptx; das Wheel enthält alle Vorlagen (erfüllt das offene Kriterium aus T01-S01).
- pyright und ruff prüfen jetzt auch `tools/`.
