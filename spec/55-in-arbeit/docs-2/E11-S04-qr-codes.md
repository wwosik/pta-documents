# E11-S04 QR-Codes aus Links

> Status: in Bearbeitung (docs-2)
> Epic: [E11 Bausteine, Variablen und Datenquellen](../../50-entwurf/E11-bausteine-variablen-datenquellen.md)
> Milestone: [M03 Grafik, Diagramme und Charts](../../50-entwurf/M03-grafik-diagramme-und-charts.md)

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
