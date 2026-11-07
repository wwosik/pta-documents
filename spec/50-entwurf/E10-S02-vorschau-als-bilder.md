# E10-S02 Vorschau als Bilder

> Status: Entwurf
> Epic: [E10 HTML-Präsentation und Vorschau](E10-html-praesentation-und-vorschau.md)
> Milestone: [M04 Präsentieren und Schulung](M04-praesentieren-und-schulung.md)

## Zusammenfassung

`./run.sh preview documents/<thema>` rendert das HTML-Deck einer Präsentation mit Playwright zu
einem PNG je Folie und einem Kontaktbogen und legt sie in `documents/<thema>/vorschau/` ab.
Damit sehen Anwender ohne PowerPoint und eine KI, die das Deck geschrieben hat, das Ergebnis —
überlange Titel, abgeschnittene Bilder, leere Folien — bevor jemand die PPTX öffnet.

## Kontext

- vt-tools-libs hat kein solches Werkzeug; dort dient `docs/tour.html` dem Menschen im Browser.
  Hier fehlt auf der Entwicklungsmaschine jedes Office (`ai/Gedächtnis.md`, *Überblick*), und die
  Stories in `spec/60-prüfung/` tragen „öffnet in PowerPoint ohne Reparatur" als offenen
  Prüfpunkt. Eine KI im Klon (`docs/ki-anleitung.md`) kann heute nur den Rückgabecode von
  `generate` prüfen.
- Playwright für Python (`playwright`, Apache-2.0) bringt Chromium per `playwright install
  chromium` (~150 MB) mit; `page.screenshot(clip=…)` und `page.pdf()` rendern eine Seite
  deterministisch. Das HTML-Deck aus E10-S01 bietet Hash-Navigation `#n` und eine Bühne fester
  Größe (1600 × 900 px), was Screenshots je Folie einfach macht.
- Für Word gibt es keinen Renderer ohne Office oder LibreOffice (Frage 2).
- `run.sh`/`run.ps1` führen jedes `tools/<name>/<name>.py` als Verb aus (`generate`,
  `generate-samples`, `prepare-templates`), ohne Eintrag im Skript; `pyproject.toml` hat die
  Extras `pdf`, `svg`, `diagrams`, `dev`.

## Vorgeschlagener Ansatz

1. **Extra** `preview = ["playwright>=1.48"]` in `pyproject.toml`; `./run.sh setup` installiert
   es mit und ruft `playwright install chromium` auf, wenn kein Chromium gefunden wird (Fehler
   dabei sind eine Warnung, kein Abbruch — ohne Vorschau läuft alles andere).
2. **Modul** `src/pta_documents/preview/deck.py` (öffentlich, damit Tests und Werkzeug es
   teilen): `render_deck(html: bytes, folder: Path, *, scale: int = 1) -> list[Path]` startet
   Chromium headless, lädt das Deck als `data:`-URL oder aus einer Temp-Datei im `.tmp/`, setzt
   Viewport 1600 × 900, springt per `#n` durch alle Folien (Anzahl aus `data-slides` im `<body>`,
   das E10-S01 schreibt), wartet auf das Ende der Übergänge (`deck.js` setzt `data-settled`),
   zeigt bei Builds den **Endzustand** (alle Schritte), und schreibt `folie-01.png` …;
   `contact_sheet(images, columns=4) -> Path` setzt mit Pillow `uebersicht.png` mit
   Foliennummern zusammen. Fehlt Playwright oder Chromium, wirft `PreviewUnavailableError` mit
   dem Installationshinweis.
3. **Werkzeug** `tools/preview/preview.py` (damit `./run.sh preview` ohne Änderung an
   `run.sh`/`run.ps1` läuft; der Dateiname ist der Verbname, deshalb ausnahmsweise deutsch wie
   `generate` englisch — Frage 4): nimmt
   Markdown-Dateien oder Ordner wie `generate`, erzeugt das HTML-Deck im Speicher (E10-S01, ohne
   es abzulegen, außer mit `--html`), rendert nach `<ordner>/vorschau/<name>/` (vorher geleert),
   gibt die Pfade aus und am Ende die Hinweise des Generators (E08, falls vorhanden). `--scale 2`
   für scharfe Bilder, `--folien 3,7-9` für eine Auswahl. Für `…-bericht.md` meldet es „Für Word
   gibt es keine Vorschau" (Frage 2).
4. **Deterministisch:** feste Schriften (Selawik eingebettet, Segoe UI unterdrückt per
   `--font-render-hinting=none` und einer CSS-Überschreibung im Vorschaumodus, damit
   Screenshots auf jedem Rechner gleich sind), `prefers-reduced-motion` erzwungen, Datum aus dem
   Front Matter oder ein festes im Test.
5. **Tests** (`tests/preview/test_deck.py`, `skip` ohne Extra): `deck.md` rendert so viele PNGs
   wie Folien; Maße 1600 × 900; der Kontaktbogen hat so viele Kacheln; ein Vergleich gegen
   `samples/funktionen` als Referenzbilder in `tests/preview/expected/` mit Toleranz
   (Pillow `ImageChops`, < 0,5 % abweichende Pixel), erneuert mit
   `PTA_DOCUMENTS_UPDATE_EXPECTED=1`. In der Verifikation (`spec/60-prüfung/`) dient die Vorschau
   als Ersatz-Prüfpunkt, wo kein PowerPoint ist — nicht als Ersatz für das Öffnen in PowerPoint.
6. **Doku:** `docs/anleitung.md` neuer Abschnitt *Vorschau ohne PowerPoint*;
   `docs/ki-anleitung.md` ergänzt die Grundregel 3: nach `generate` die Vorschau erzeugen, die
   Bilder ansehen (Read) und Folien korrigieren, deren Titel umbricht, deren Text verkleinert
   wurde oder deren Bild wichtige Teile abschneidet; `.gitignore` braucht nichts, weil
   `documents/` ignoriert ist, `samples/*/vorschau/` kommt dazu.

## Akzeptanzkriterien

- [ ] `./run.sh preview samples/gsb` legt je Folie ein PNG und `uebersicht.png` in
      `samples/gsb/vorschau/gsb-praesentation/` ab; die Bilder zeigen die Folien wie der Browser.
- [ ] Ohne das Extra bricht nur `preview` mit einem Installationshinweis ab; `generate` und die
      Tests laufen unverändert (Vorschautests werden übersprungen).
- [ ] Zwei Läufe auf derselben Maschine ergeben identische Bilder; auf einer anderen Maschine
      weichen sie um weniger als 0,5 % der Pixel ab.
- [ ] Eine KI, die `docs/ki-anleitung.md` folgt, sieht ihre Folien an, bevor sie den Anwender
      informiert.

## Offene Fragen

1. Soll die Vorschau bei Builds den Endzustand zeigen (Vorschlag) oder je Schritt ein Bild
   (`folie-03-2.png`)?

> (2026-11-07) Endzustand.
2. Word: soll optional **LibreOffice** (wenn `soffice` im Pfad ist) für `…-bericht.md` eine
   Vorschau liefern (DOCX → PDF → PNG über pypdfium2 aus dem Extra `pdf`)? Es wäre nie Pflicht,
   zeigt aber nicht genau, was Word zeigt. Vorschlag: ja, als `preview --libreoffice`, klar als
   Näherung beschriftet; sonst gar keine Word-Vorschau.

> (2026-11-07) Nein — keine Word-Vorschau, kein LibreOffice.
3. Dürfen Referenzbilder (`tests/preview/expected/`, einige MB) ins Repo? Alternative: nur
   Struktur prüfen (Anzahl, Maße, nicht leer). Vorschlag: nur `samples/funktionen` als Referenz,
   `--scale 1`, PNG optimiert.

> (2026-11-07) Nur `samples/funktionen` als Referenz, `--scale 1`, optimiert.
4. Verbname `preview` (deutsch, wie der Anwender es liest) oder `preview` (englisch, wie
   `generate` und `generate-samples`)? Vorschlag: `preview`, damit alle Verben eine Sprache haben;
   die Anleitung erklärt ihn.

> (2026-11-07) `preview`. Alle Verben und Schalter der Werkzeuge sind englisch (`check`, `compare`, `--strict`, `--sources`); die Anleitungen erklären sie.

## Notizen

- In der Remote-Umgebung von Claude Code ist Chromium mit Playwright vorinstalliert; dort darf
  `playwright install` nicht erneut laufen (`executablePath` aus der Umgebung). `setup` prüft
  deshalb zuerst, ob ein Chromium erreichbar ist.
- Die Vorschau ist die Grundlage für einen späteren Vergleich HTML ↔ PPTX, falls einmal
  LibreOffice verfügbar ist: beide zu PNG, Differenzbild.
