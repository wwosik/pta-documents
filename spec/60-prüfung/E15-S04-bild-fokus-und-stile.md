# E15-S04 Bild-Fokus und Bildstile

> Status: in Prüfung
> Epic: [E15 Visuelle Bausteine](../50-entwurf/E15-visuelle-bausteine.md)
> Milestone: [M03 Grafik, Diagramme und Charts](../50-entwurf/M03-grafik-diagramme-und-charts.md)

## Zusammenfassung

Attribute an Bildern steuern, was der Beschnitt durch die PTA-Bildplatzhalter zeigt
(`{focus=top}`), ob statt Beschnitt eingepasst wird (`{fit=contain}`), und geben Bildern Stile:
`.round` für Kontaktfotos, `.grey` für Graustufen. Der Schreiber behält die Kontrolle über das
Bild, ohne es vorher in einem Bildprogramm zuzuschneiden.

## Kontext

- PowerPoint: Bilder füllen den Platzhalter und werden beschnitten (E04-S02, `visuals.py`,
  `insert_picture` von python-pptx beschneidet mittig über `a:srcRect`). E08-S01 plant den
  Hinweis `image-cropped` ab 25 % Verlust. Kontakt-Layouts (E04-S04) haben runde Bildplatzhalter
  nicht — das Foto ist rechteckig; ein rundes Porträt ist in Beratungsdecks üblich.
- Word: `BodyWriter.picture` setzt Bilder in Satzspiegelbreite (E03-S02); kein Beschnitt.
- Bildtitel tragen heute die Unterschrift und `scale=N` (E04-S02/E11-S04); Attribute in Braces
  nach dem Bild (`![…](a.jpg){focus=top}`) sind in markdown-it über `mdit_py_plugins.attrs`
  verfügbar (E02-S02 schaltet es für Heading-Attribute frei).
- Pillow ist im Kern (Bildmaße, `ImageInfo`), kann beschneiden, Graustufen (`ImageOps.grayscale`)
  und Masken (Kreis als Alphakanal).

## Vorgeschlagener Ansatz

1. **Attribute** in `generation/common/image_attributes.py`: `ImageAttributes.parse(token) ->
   ImageAttributes(focus: Focus, fit: Fit, round: bool, grey: bool, scale: float | None)` aus
   `token.attrs` (attrs-Plugin) **und** aus dem Titel (`scale=` bleibt dort gültig, Umstellung
   mit Hinweis im Guide). `focus`: `center` (Standard), `top`, `bottom`, `left`, `right` oder
   `x%,y%` (Punkt, der im Ausschnitt bleibt, z. B. `30%,20%` für ein Gesicht links oben); `fit`:
   `cover` (Standard, Beschnitt) oder `contain` (einpassen, Rest weiß — nicht transparent, die
   PTA-Layouts haben weiße Flächen). Unbekannte Attribute oder Werte: Fehler mit Zeile und den
   gültigen Werten (wie Heading-Attribute).
2. **Fokus in PowerPoint** (`visuals.py`): statt `insert_picture` eigene Rechnung des
   `a:srcRect` — Seitenverhältnis des Platzhalters, Ausschnitt so verschoben, dass der Fokuspunkt
   im Ausschnitt liegt (an den Rand geklemmt); `fit=contain`: Bild zentriert in den Platzhalter
   eingepasst, Platzhalter weiß gefüllt. Der Hinweis `image-cropped` (E08-S01) bleibt, nennt
   aber `focus=` als Abhilfe nur, wenn keiner gesetzt ist.
3. **Fokus in Word**: Bilder werden nicht beschnitten, `focus` ist dort wirkungslos (kein
   Fehler — dieselbe Quelle für beide Formate); `fit` ebenso. Bildreihen (E03-S03) mit festen
   Zellenmaßen nutzen `focus` künftig für ihren Beschnitt.
4. **Stile** (`generation/common/image_styles.py`, Pillow): `.grey` → Graustufen-PNG; `.round` →
   quadratischer Ausschnitt um den Fokus, Kreismaske als Alphakanal, PNG (JPEG verliert die
   Transparenz); beides vor dem Einfügen, Ergebnis als neue `DocumentResource`
   (`<name>-round.png`), damit Writer und Konverter nichts Neues lernen. In PowerPoint
   alternativ `a:prstGeom ellipse` am Bild (editierbar, verlustfrei) — Vorschlag: in PowerPoint
   die Geometrie, in Word/PDF die Maske.
5. **Konverter (E07)**: liest das eingebettete Bild wie es ist (beschnitten/rund/grau); die
   Rundreise ergibt `![…](images/…png)` ohne Attribute — Abweichung dokumentiert; die PPTX-
   Ellipsengeometrie wird als `{.round}` erkannt und zurückgeschrieben.
6. **Guide und Hinweise**: Abschnitt „Bilder" in den Authoring Guides (E04-S06, E03-S05): Fokus
   setzen statt vorher zuschneiden; `ki-anleitung.md` empfiehlt `focus=` für Fotos mit Personen.
7. **Tests**: `srcRect`-Rechnung für alle Fokuswerte und Seitenverhältnisse (Fokus bleibt im
   Ausschnitt, Klemmung am Rand), `fit=contain` ohne Beschnitt, Graustufen-Pixel, runde Maske
   mit transparenten Ecken, Fehler bei unbekannten Werten, Rundreise; Beispiel in
   `samples/funktionen/` (ein Foto dreimal mit `top`, `center`, `bottom`).

## Akzeptanzkriterien

- [x] `{focus=top}` zeigt im PTA-Bildplatzhalter den oberen Bildteil; `x%,y%` hält den Punkt im
      Ausschnitt; `fit=contain` beschneidet nicht.
- [x] `.round` ergibt ein kreisrundes Bild (PowerPoint: Ellipsengeometrie; Word: Maske),
      `.grey` ein Graustufenbild — in beiden Formaten.
- [x] Unbekannte Attribute und Werte sind Fehler mit Zeile; `scale=` im Titel funktioniert weiter.
- [x] Die Rundreise ist dokumentiert; `.round` kommt aus PowerPoint zurück.

## Offene Fragen

1. `.shadow` (weicher Schatten unter dem Bild) — passt das zum PTA-Stil? Die Vorlagensammlung
   zeigt Bilder ohne Schatten. Vorschlag: nein, weglassen.

> (2026-11-07) Nein, weglassen.

2. Sollen Attribute nur in Braces nach dem Bild stehen (`{focus=top}`) und `scale=` aus dem Titel
   dorthin wandern (eine Stelle, Titel bleibt reine Unterschrift)? Vorschlag: ja, mit Übergang —
   `scale=` im Titel bleibt ein Jahr gültig und löst einen Hinweis aus.

> (2026-11-07) Ja, mit Übergang (ein Jahr, Hinweis).

3. Rundes Bild auch für Kontakt-Layouts (E04-S04) als Standard, oder nur auf Wunsch? Vorschlag:
   nur auf Wunsch — die Vorlage zeigt rechteckige Fotos.

> (2026-11-07) Nur auf Wunsch.

## Notizen

- Abhängigkeit: `mdit_py_plugins.attrs` für Bildattribute (E02-S02); bis dahin nur der Titel.

## Implementierungsnotizen

Umgesetzt von `docs-2` am 2026-11-08. Neu: `markdown/image_attributes.py` (Inline-Regel, Text
der Klammern in `Token.meta[ATTRIBUTES]`), `generation/common/image_attributes.py`
(`ImageAttributes.parse`, `Focus`, `Fit`, `take`, `of`, `visible_window`),
`generation/common/image_styles.py` (`grey`, `round_png`, `apply`). Angepasst:
`markdown/parser.py`, `generation/common/generated_images.py` (`add_generated` liest die
Attribute aller Bilder und legt die Stile an, nimmt `notes`; `scale_of` für alle Bilder),
`generation/common/result.py` (Hinweis `image-scale-in-title`), PPTX `model.py` (`Image.focus`,
`Image.round`), `parser.py`, `visuals.py` (`crop_picture`, `round_picture`, rund in
`draw_pictures`), `writer.py` (`fill_picture`, Hinweis `image-cropped`), Word `writer.py`
(`notes` an `add_generated`), PDF `layout/story.py` (Skalierung aus den Attributen),
Konverter `conversions/pptx.py` (`{.round}` aus `prst="ellipse"`). Tests:
`tests/markdown/test_image_attributes.py`, `tests/generation/common/test_image_attributes.py`,
`tests/generation/common/test_image_styles.py`, `tests/generation/pptx/test_image_attributes.py`,
`tests/generation/docx/test_image_attributes.py`, `tests/generation/pdf/test_image_attributes.py`,
angepasst `tests/generation/common/test_generated_images.py`; `tests/samples/test_funktionen.py`
verlangt `.round`, `.grey` in beiden Beispielen, `scale=` im Bericht und `focus=top|center|bottom`,
`focus=x%,y%`, `fit=contain` in der Präsentation. Beispiele: neues, selbst gezeichnetes Bild
`samples/funktionen/images/portraet.png`; Folien „Bildausschnitt oben/Mitte/unten", „Bild
eingepasst", „Rund und grau", rundes Foto auf der Kontaktfolie; Abschnitt „Bildstile" im Bericht;
QR-Abschnitt auf `{scale=…}` umgestellt; README und Rundreisen. Doku: `docs/verwendung.md`
(Abschnitt „Bildattribute (E15-S04)", Zeilen in der Syntax- und der Hinweistabelle, QR-Codes,
PDF-Bilder), `docs/anleitung.md` (Abschnitt „Bildausschnitt und Bildstile", Tabelle, Fehler),
`docs/ki-anleitung.md` (`focus=` für Fotos mit Personen); `ai/Gedächtnis.md`.

### Entscheidungen

- **Syntax:** `{…}` direkt nach dem Bild, ohne Leerzeichen; Einträge durch Leerzeichen getrennt,
  `.round`, `.grey`, `focus=…`, `fit=…`, `scale=…`, Werte wahlweise in `"…"`. Andere Klammern
  bleiben Text (mit Leerzeichen davor, nach Text).
- **Fokus:** `center`, `top`, `bottom`, `left`, `right` (Groß-/Kleinschreibung egal) oder
  `x%,y%` mit Punkt als Dezimaltrenner, je 0–100 %. Der Ausschnitt ist so groß wie die
  Proportionen erlauben, auf den Punkt zentriert und am Rand geklemmt (`visible_window`); ohne
  Fokus ist das Ergebnis genau der bisherige mittige Beschnitt von python-pptx.
- **`scale=` für alle Bilder** (Antwort 2): in den Klammern, im Titel noch bis 2027-11 mit
  Hinweis `image-scale-in-title` (PPTX, DOCX); beides zugleich ist ein Fehler. Bedeutung wie in
  E11-S04: Word/PDF N-fache Größe (höchstens Satzspiegel), Folien N-fache eingepasste Größe,
  nie größer. Die Sonderregel `_take_scale` in `generated_images` ist entfallen.
- **`.round` in PowerPoint** (Vorschlag aus dem Plan): Ellipsengeometrie
  (`picture.auto_shape_type = OVAL`), dazu ein quadratischer Ausschnitt um den Fokus über
  `srcRect` und ein quadratischer Rahmen (kürzere Seite des Platzhalters, zentriert) — sonst
  wäre der Kreis in einem nicht quadratischen Platzhalter ein Oval. In Bildreihen und auf
  Flow-Folien zählt das Bild als Quadrat der kürzeren Seite.
- **`.round` in Word/PDF:** PNG mit Kreismaske (4-fach überabgetastet, glatter Rand) auf dem
  Quadrat um den Fokus; **`.grey`** überall ein Graustufen-PNG (Transparenz und dpi bleiben).
  Neue Ressourcen heißen `<name>-grey.png`, `<name>-round.png`, `<name>-grey-round.png`
  (bei anderem Inhalt unter demselben Namen `-2`, `-3` …); `src` des Bild-Tokens zeigt darauf.
- **`image-cropped`** nennt `{focus=…}` und `{fit=contain}` nur ohne gesetzten Fokus; bei
  `.round` entfällt der Hinweis (der quadratische Beschnitt ist gewollt).
- **Rundes Foto für Kontakte** nur auf Wunsch (Antwort 3); kein `.shadow` (Antwort 1).

### Abweichungen

- **Eigene Inline-Regel statt `mdit_py_plugins.attrs`:** dort beginnt `%` einen Kommentar und
  Werte mit `.` oder `,` brauchen Anführungszeichen — `{focus=30%,20%}` und `{scale=0.5}` wären
  Text geblieben. Die Regel übernimmt nur den Text der Klammern; geprüft wird mit Zeile in
  `image_attributes`.
- **Prüfung in `add_generated`, nicht in `layout_syntax.check`:** dort laufen ohnehin alle
  Bild-Token aller drei Generatoren durch (auch PDF), und `scale=` muss dort aus dem Titel. So
  blieb der PDF-Generator (`generation/pdf/generator.py`, parallel in E05-S03 in Arbeit)
  unverändert; er übergibt keine `notes`, das PDF meldet `image-scale-in-title` daher nicht.
- **`fit=contain`** nutzt das Einpassen aus E11-S04 (`visuals.fit_picture`): das Bild wird
  verkleinert und zentriert, um es herum zeigt die Folie ihren (weißen) Hintergrund. Ein weiß
  gefüllter Platzhalter, wie im Plan, entsteht nicht — der Platzhalter wird durch das Bild
  ersetzt.
- **`scale` in einem beschneidenden Bildplatzhalter** ist wirkungslos (der Platzhalter bleibt
  gefüllt); es wirkt in Bildreihen, auf Flow-Folien und mit `fit=contain`.
- Statt der Authoring Guides (E04-S06, E03-S05, noch Entwurf) beschreiben `docs/anleitung.md`
  und `docs/ki-anleitung.md` die Attribute.
- Die Bildreihen in Word (E03-S03) beschneiden nicht; `focus` hat dort noch nichts zu tun.

### Warnungen

- **QR-Codes** nehmen weder `.round` noch `.grey` (Fehler: ein runder Code scannt nicht) und
  werden immer eingepasst; `focus` und `fit=cover` sind an ihnen wirkungslos, kein Fehler.
- **Stile an SVG-Bildern** sind ein Fehler mit Zeile (Pillow liest kein SVG; die Bildkonverter
  laufen erst im Writer) — vorsichtigste Wahl statt eines stillen Verlusts der Vektorgrafik.
- **`fit`/`focus` an SVG in PowerPoint** wirken auf das PNG und das angehängte `asvg:svgBlip`
  gleichermaßen über `srcRect`; nicht in Office geprüft.
- **Ohne Office geprüft:** dass PowerPoint die Ellipse mit `srcRect` und den verschobenen
  Ausschnitt wie gedacht zeigt, ist nur im XML geprüft (kein PowerPoint/LibreOffice auf der
  Maschine). Die Word-/PDF-PNGs sind als Bild angesehen.
- **PDF/A und Transparenz:** das runde PNG kommt mit `SMask` ins PDF; PDF/A-2b erlaubt das,
  veraPDF ist hier nicht installiert (nicht geprüft).
- **Rundreise:** Graustufen und Word-Kreis kommen als fertiges Bild zurück, ohne Attribute; aus
  PowerPoint kommt das ganze Originalbild mit `{.round}` (der Fokus geht verloren), `focus=` und
  `fit=` kommen nicht zurück.
- `.grey` macht aus einem JPEG ein (größeres) PNG, wie geplant.

### Prüfpunkte

- `.tmp/review/funktionen/funktionen-praesentation.pptx`, Folien „Bildausschnitt oben", „…
  Mitte", „… unten" (Sonne oben sichtbar bzw. Wiese unten), „Bild eingepasst" (ganzes Bild,
  nicht beschnitten), „Rund und grau" (Kreis um den Kopf, Graustufenbild daneben) und „Ihre
  Ansprechpartner" (rundes Foto bei Erika Mustermann). In PowerPoint: Ellipse anklicken,
  „Zuschneiden" zeigt das ganze Bild.
- `.tmp/review/funktionen/funktionen-bericht.docx`, Abschnitt „Bildstile": rundes Bild mit
  transparenten Ecken, Graustufenbild, beide auf 0,3-fache Größe.
- `./run.sh test tests/markdown/test_image_attributes.py
  tests/generation/common/test_image_attributes.py tests/generation/common/test_image_styles.py
  tests/generation/pptx/test_image_attributes.py tests/generation/docx/test_image_attributes.py
  tests/generation/pdf/test_image_attributes.py`.

### Offene Punkte

- **PDF-Generator** (nach E05-S03): `notes` an `add_generated` übergeben, damit auch das PDF
  `image-scale-in-title` meldet (eine Zeile in `generation/pdf/generator.py`). — *(2026-11-08) Erledigt in E05-S04.*
- 2027-11: `scale=` im Titel entfernen (`image_attributes._title_scale`, Hinweis, Doku).
- Authoring Guides (E04-S06, E03-S05) übernehmen den Abschnitt „Bilder".
- Bildreihen mit festen Zellenmaßen (E03-S03) können `focus` für ihren Beschnitt nutzen, sobald
  es sie gibt.
