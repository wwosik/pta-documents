# E15-S04 Bild-Fokus und Bildstile

> Status: in Bearbeitung (docs-2)
> Epic: [E15 Visuelle Bausteine](../../50-entwurf/E15-visuelle-bausteine.md)
> Milestone: [M03 Grafik, Diagramme und Charts](../../50-entwurf/M03-grafik-diagramme-und-charts.md)

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

- [ ] `{focus=top}` zeigt im PTA-Bildplatzhalter den oberen Bildteil; `x%,y%` hält den Punkt im
      Ausschnitt; `fit=contain` beschneidet nicht.
- [ ] `.round` ergibt ein kreisrundes Bild (PowerPoint: Ellipsengeometrie; Word: Maske),
      `.grey` ein Graustufenbild — in beiden Formaten.
- [ ] Unbekannte Attribute und Werte sind Fehler mit Zeile; `scale=` im Titel funktioniert weiter.
- [ ] Die Rundreise ist dokumentiert; `.round` kommt aus PowerPoint zurück.

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
