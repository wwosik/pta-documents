# E01-S02 Vorlagen bereinigen und einbetten

> Status: in Bearbeitung (port-1)
> Epic: [E01 PTA-Design als einziges Design](../../50-entwurf/E01-pta-design.md)
> Milestone: [M01 PTA-Dokumente aus Markdown](../../50-entwurf/M01-pta-dokumente-aus-markdown.md)

## Zusammenfassung

Die Vorlagen aus `source-templates/` werden einmal bereinigt und als Paketdaten in
`pta_documents/design/templates/` mitgeliefert, sodass die Generatoren keine Datei von außen lesen.

## Kontext

Laut [Designanalyse](../../10-analysen/2026-11-06%20pta-designstandards.md) enthalten alle Vorlagen
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

- [ ] `./run.sh prepare-templates` erzeugt die Paketdaten aus `source-templates/` reproduzierbar.
- [ ] Die eingebetteten Vorlagen enthalten keine Musterfolien, keinen Mustertext, keine
      SharePoint-Kennungen und keine Personennamen.
- [ ] Theme, Formatvorlagen, Master und Layouts sind unverändert.

## Offene Fragen

1. Dürfen die Vorlagen (mit den Hintergrundfotos) im Paket liegen?

> (2026-11-06) Ja, im Paket.

## Notizen

