# E11-S04 QR-Codes aus Links

> Status: in Prüfung
> Epic: [E11 Bausteine, Variablen und Datenquellen](../50-entwurf/E11-bausteine-variablen-datenquellen.md)
> Milestone: [M03 Grafik, Diagramme und Charts](../50-entwurf/M03-grafik-diagramme-und-charts.md)

## Zusammenfassung

`![Zur Umfrage](qr:https://umfrage.example/abc "Feedback zur Schulung")` erzeugt einen QR-Code
in PTA-Blau als Bild — in Word, PowerPoint und PDF, mit Beschriftung wie jedes andere Bild.
Teilnehmer einer Schulung oder Leser eines Berichts kommen so ohne Abtippen zum Link.

## Kontext

- Bilder sind heute Ressourcen (`MarkdownDocument.resources`); der Writer prüft, dass jedes
  `![…](pfad)` eine Ressource hat, sonst Fehler (`docs/anleitung.md`, Kapitel 8). Ein Bild, das
  erst beim Erzeugen entsteht, braucht einen zweiten Weg neben den Ressourcen.
- E02-S04 plant Bildkonverter (`IImageConverter` in DocLibs: SVG → PNG). Ein QR-Code ist der
  umgekehrte Fall — kein Konverter einer Datei, sondern ein Erzeuger aus einer URL — passt aber
  in dieselbe Stelle des Writers: „gib mir für diese Bildreferenz PNG-Bytes und Maße".
- Farbe: PTA-Blau `006FB9` aus dem Designmodell (E01-S01), Hintergrund weiß; QR-Leser kommen mit
  dunklem Blau auf Weiß zurecht, hellere Farben (`9FD8FF`) nicht.
- Paket: **segno** (BSD-3, pure Python, ohne Abhängigkeiten) erzeugt QR-Codes als PNG und SVG;
  Fehlerkorrektur und Ruhezone sind einstellbar.

## Vorgeschlagener Ansatz

1. **Erkennung** in `src/pta_documents/generation/common/generated_images.py`: eine Bildreferenz
   mit dem Schema `qr:` ist ein erzeugtes Bild; `GeneratedImage.resolve(reference) ->
   DocumentResource | None` liefert für `qr:<inhalt>` ein PNG (`segno.make(inhalt, error="m")`,
   `scale` so, dass 1 000 px Kante entstehen, `dark="#006FB9"`, Ruhezone 4 Module) mit dem Pfad
   der Referenz, sodass der Rest des Writers nichts Neues lernt. Andere Schemata bleiben Fehler
   wie heute.
2. **Inhalt:** alles nach `qr:` wörtlich — URL, `mailto:`, `tel:`, WLAN-Zugang
   (`WIFI:T:WPA;S:…;P:…;;`) oder Text; Leerzeichen URL-kodiert. Länger als 1 000 Zeichen ist ein
   Fehler mit Zeile.
3. **Größe:** ohne Angabe 3 × 3 cm in Word, auf Folien die Bildregeln des Layouts (E04-S02; ein
   QR-Code wird nicht beschnitten, sondern eingepasst); `scale=0.5` im Titel halbiert wie bei
   Bildern (E04-S02/E05-S02). Bildunterschrift aus dem Titel (`"…"`), sonst aus dem Alt-Text —
   wie bei Bildern; für QR-Codes empfiehlt der Authoring Guide, den Link als Unterschrift zu
   zeigen, damit er auch gedruckt lesbar ist.
4. **PDF (E05):** das PNG wie jedes Bild; später SVG aus segno als Vektor, wenn E02-S03/E06-S04
   stehen (Notiz).
5. **Konverter (E07):** liest ein PNG zurück; die Rundreise ergibt also `![…](images/qr-1.png)`
   statt `qr:…`. Die Abweichung wird in den Erwartungsdateien festgehalten; ein Test prüft, dass
   das zurückgelesene Bild einen lesbaren QR-Code enthält (Dekodierung im Test über `segno`
   selbst nicht möglich — Frage 1).
6. **Tests** `tests/generation/test_generated_images.py`: PNG-Maße, Farbe, Fehler bei zu langem
   Inhalt, Rundreise DOCX/PPTX; Beispiel in `samples/funktionen/` (Abschlussfolie mit QR-Code)
   und ein Absatz in `docs/anleitung.md`, `docs/ki-anleitung.md`.

## Akzeptanzkriterien

- [ ] `![…](qr:https://…)` ergibt in Word und PowerPoint einen QR-Code in PTA-Blau mit
      Beschriftung, den ein Handy-Scanner liest.
- [ ] Größe und Beschriftung verhalten sich wie bei Bildern; `scale` wirkt.
- [ ] Zu langer Inhalt oder ein unbekanntes Schema sind Fehler mit Zeile.
- [ ] Die Rundreise liefert ein normales Bild; die Abweichung ist dokumentiert.

## Offene Fragen

1. Soll ein Test den erzeugten Code tatsächlich dekodieren? Dafür bräuchte es einen Decoder
   (`pyzbar` hängt an der C-Bibliothek zbar; `opencv-python-headless` ist groß). Vorschlag: nein —
   segno ist geprüft, der Test vergleicht das PNG mit einer Erwartungsdatei.

> (2026-11-07) Nein, kein Decoder; PNG gegen Erwartungsdatei.
2. Weitere erzeugte Bilder nach demselben Muster — etwa `barcode:` oder ein Platzhalterbild
   `platzhalter:16x9` für Layout-Entwürfe? Vorschlag: `platzhalter:` als zweites Schema, weil
   Entwürfe oft noch keine Fotos haben.

> (2026-11-07) Nein, vorerst kein `platzhalter:`.

## Notizen

- Abhängigkeiten: keine; QR-Codes als SVG-Vektor erst mit E02-S03/E06-S04.

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08: neu `generation/common/generated_images.py`
(`is_generated`, `qr_content`, `qr_png`, `resolve`, `add_generated`, `scale_of`); angepasst
`generation/docx/writer.py` (`write` ruft `add_generated`, `scale` durch `place_picture` →
`insert_picture` → `_image_size`), `generation/pptx/parser.py` (`parse` ruft `add_generated`,
neu `_image` mit `fit`/`scale`; `_placeable` behält die Felder per `replace`),
`generation/pptx/model.py` (`Image.fit`, `Image.scale`), `generation/pptx/visuals.py` (neu
`fit_picture`, `draw_pictures` mit `scale`), `generation/pptx/writer.py` (`fill_picture` passt
ein), `generation/common/style_rules.py` (`needs_source`), `pyproject.toml` (segno). Tests: neu
`tests/generation/common/test_generated_images.py` (36 Fälle) mit Erwartungsdatei
`tests/generation/common/samples/qr-umfrage.expected.png`; `tests/samples/test_funktionen.py`
verlangt jedes Schema aus `SCHEMES` im Beispiel. Beispiele: Abschnitt „QR-Code" in
`samples/funktionen/funktionen-bericht.md` und Folie „QR-Code" in
`funktionen-praesentation.md`, README-Tabelle, Rundreisen. Doku: `docs/verwendung.md` (Abschnitt
„QR-Codes (E11-S04)"), `docs/anleitung.md` (Tabelle Word, Präsentation, Abschnitt „QR-Codes",
Fehler), `docs/ki-anleitung.md`; `ai/Gedächtnis.md` (Eintrag „QR-Codes", Stack).

### Entscheidungen

- **Ein Durchgang über die Token** statt eines neuen Wegs im Writer: `add_generated` läuft in
  beiden Generatoren direkt nach `layout_syntax.check` (vor der Typografie) und gibt das
  Dokument mit den erzeugten PNGs als zusätzliche Ressourcen zurück, Pfad = die Referenz
  (`qr:…`). Danach finden Writer, Bildreihen, Kontaktfotos und Flow-Folien den QR-Code wie jedes
  Bild. Eine vom Aufrufer mitgegebene Ressource mit demselben Pfad geht vor; derselbe Code
  zweimal ergibt eine Ressource.
- **PNG** nach Plan: `segno.make(inhalt, error="m", micro=False)`, Modulgröße
  `ceil(1000 / Module)` → mindestens 1 000 px Kante (eine glatte Kante von genau 1 000 px ginge
  nur mit gebrochenen Modulen), PTA-Blau (`colors.PTA_BLUE`) auf Weiß, Ruhezone 4 Module. Die
  **3 cm in Word** stecken in der Auflösung des PNG (dpi = Kante / 3 cm), die `_image_size`
  ohnehin liest — dafür musste Word nichts Neues lernen.
- **Inhalt:** markdown-it %-kodiert Linkziele (Leerzeichen nur in `<…>`). `http:`, `https:`,
  `mailto:` bleiben kodiert (gültige URLs), alles andere (`WIFI:`, `tel:`, Text) wird dekodiert,
  damit `S:Mein Netz` als „Mein Netz" gescannt wird. Länge > 1 000 Zeichen und leerer Inhalt
  sind Fehler `Line N: …` (Format wie `layout_syntax.check`).
- **Unbekanntes Schema** (`foto:…`) bleibt, was es war: ein Pfad, den die Ressourcen haben
  müssen — Fehler „… is not among the document's resources" mit Zeile (Word „(line N)", PPTX
  „(line N)"); dieselbe Meldung wie für jedes fehlende Bild.
- **PowerPoint:** Bildplatzhalter beschneiden (python-pptx `insert_picture`); für QR-Codes
  (`Image.fit`) nimmt `visuals.fit_picture` den Beschnitt zurück und passt das Bild zentriert in
  den Platzhalter ein. Flow-Folien und Bildreihen passen ohnehin ein. Natürliche Größe = die
  Pixel des PNG, darum kein `image-enlarged`-Hinweis.
- **`style-image-source`** verlangt für erzeugte Bilder keine Quelle — ein QR-Code hat keinen
  Urheber.
- **segno** (1.6.6, BSD-3-Clause, pure Python, ohne Abhängigkeiten, mit Typinformationen) ist
  **Kernabhängigkeit**, kein Extra: QR-Codes sind Teil von Word und PowerPoint, und der Kern
  braucht laut Standards keine Extras.
- Entscheidungen zu den Fragen: kein Decoder im Test; das PNG wird Pixel für Pixel mit der
  Erwartungsdatei verglichen (neu schreiben mit `PTA_DOCUMENTS_UPDATE_EXPECTED=1`). Kein
  `platzhalter:`.

### Abweichungen

- Tests liegen nach dem Spiegelbaum in `tests/generation/common/test_generated_images.py`
  (Plan: `tests/generation/test_generated_images.py`); dort stehen auch die Fälle für Word,
  PowerPoint und die Rundreise.
- `GeneratedImage.resolve(reference)` heißt `resolve(reference, format, line)` (Modulfunktion,
  weil sie für Fehlermeldungen Format und Zeile braucht); die Erkennung läuft über
  `add_generated`.
- Das Beispiel steht nicht auf der Abschlussfolie (Plan Punkt 6): `{.closing}` nimmt keinen
  Inhalt an. Es ist eine eigene Folie „QR-Code" im Kapitel „Bilder".

### Warnungen

- **`scale=` gibt es bisher für kein Bild** — der Plan setzt es aus E04-S02/E05-S02 voraus,
  E04-S02 hat es aber nicht gebaut (E08-S01 hält fest: „`scale=1` im Bildtitel gibt es hier
  nicht"); erst E15-S04 plant es für alle Bilder. Vorsichtigste Lösung, damit das
  Akzeptanzkriterium „`scale` wirkt" erfüllt ist, ohne eine Bildsyntax vorwegzunehmen: `scale=N`
  wirkt **nur bei QR-Codes**, wird dort aus dem Titel genommen (erscheint nicht in der
  Beschriftung) und gilt als Faktor — Word: auf 3 cm (höchstens Satzspiegelbreite),
  PowerPoint: auf die eingepasste Größe, nie größer als der Rahmen. Erlaubt 0 < N ≤ 5, sonst
  Fehler mit Zeile. In Titeln gewöhnlicher Bilder bleibt `scale=…` Text wie bisher. E15-S04 muss
  das übernehmen oder angleichen (dort ist `scale` auf Folien eine Obergrenze der Vergrößerung,
  wie in vt-tools-libs).
- **Bildunterschrift auf Folien:** PowerPoint zeigt für Bilder keine Unterschrift aus dem Titel
  (auch nicht für Fotos); „wie bei Bildern" heißt dort: keine. Der Authoring Guide rät deshalb,
  den Link als Text auf die Folie zu schreiben.
- **Fehlerkorrektur:** segno hebt `M` auf `Q`/`H` an, wo das die Version nicht vergrößert
  (Standard `boost_error`); der Code ist dadurch robuster, nie größer.
- **Lesbarkeit mit dem Handy nicht geprüft:** Einmalig außerhalb der Tests mit OpenCV
  (`cv2.QRCodeDetector`, in einer Wegwerf-Umgebung unter `.tmp/`) dekodiert: die URL der
  Erwartungsdatei, `https://www.pta.de` aus dem Beispiel, ein WLAN-Zugang mit Leerzeichen und
  „A" (kein Micro-QR) werden gelesen. Ein echter Handy-Scanner fehlt.
- **Ohne Office geprüft:** Dass PowerPoint das eingepasste Bild im Platzhalter (eigene
  `a:xfrm`, `srcRect` 0) ohne Reparaturmeldung zeigt, ist nicht geprüft (kein
  PowerPoint/LibreOffice auf der Maschine).

### Prüfpunkte

- `.tmp/review/funktionen/funktionen-bericht.docx`, Abschnitt „QR-Code": 3 × 3 cm, PTA-Blau,
  „Abbildung 7: https://www.pta.de"; mit dem Handy scannen.
- `.tmp/review/funktionen/funktionen-praesentation.pptx`, Folie „QR-Code": im Bildrahmen rechts
  eingepasst und zentriert, nicht beschnitten; scannen, auch vom Beamer.
- `./run.sh test tests/generation/common/test_generated_images.py`.

### Offene Punkte

- **PDF** (E05-S04): das PNG wie jedes Bild setzen; `add_generated` muss der PDF-Generator nach
  `layout_syntax.check` ebenso aufrufen, und `scale_of` für die Größe lesen (3 cm aus der
  Auflösung). Später SVG aus segno als Vektor (Notiz im Plan).
- **E15-S04** (Bildattribute): `scale=` für alle Bilder; dann die QR-Sonderregel in
  `generated_images._take_scale` dorthin verlagern.
- Die Rundreise gibt `images/imageN.png` statt `qr:…` zurück (Akzeptanzkriterium,
  dokumentiert in `docs/verwendung.md`); den Link könnte der Konverter aus dem Alt-Text/Titel
  nicht sicher wiederherstellen.
