# E10-S02 Vorschau als Bilder

> Status: in Prüfung
> Epic: [E10 HTML-Präsentation und Vorschau](../50-entwurf/E10-html-praesentation-und-vorschau.md)
> Milestone: [M04 Präsentieren und Schulung](../50-entwurf/M04-praesentieren-und-schulung.md)

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

- [x] `./run.sh preview samples/gsb` legt je Folie ein PNG und `uebersicht.png` in
      `samples/gsb/vorschau/gsb-praesentation/` ab; die Bilder zeigen die Folien wie der Browser.
- [x] Ohne das Extra bricht nur `preview` mit einem Installationshinweis ab; `generate` und die
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

## Implementierungsnotizen

### Entscheidungen

- **Modul** `src/pta_documents/preview/` (`deck.py`, öffentlich über `pta_documents.preview`):
  `render_deck(html, *, scale=1, slides=None) -> list[SlidePicture]` (Foliennummer + PNG-Bytes),
  `contact_sheet(pictures, columns=4) -> bytes`, `PreviewUnavailableError`, `INSTALL_HINT`,
  `chromium_available()`. Playwright wird per `importlib` geladen, damit Paket, Typprüfung und
  alle anderen Tests ohne das Extra laufen.
- **Ausliefern ohne Datei:** Das Deck kommt über `context.route` aus dem Speicher unter
  `https://deck.preview/`; jede andere Anfrage wird abgewiesen. Weder `data:`-URL (Decks bis
  8 MB) noch Temp-Datei; Hash-Navigation `#n` funktioniert so wie im Browser.
- **Vorschau-Stil** vor `</head>` (die CSP des Decks erlaubt Inline-Stil): `@font-face` mit den
  Familiennamen „Segoe UI" und „Consolas" auf die eingebetteten Selawik/Inconsolata — eine eigene
  `@font-face` verdeckt eine installierte Schrift gleichen Namens, damit auch ein Rechner mit
  Segoe UI dieselben Bilder liefert (Plan 4). Dazu Bühne unskaliert oben links, Kapitelleiste,
  Fortschritt, Tastenhinweis und Notizen aus, Animationen/Übergänge aus. Chromium mit
  `--font-render-hinting=none`, Kontext mit `reduced_motion="reduce"`, Locale `de-DE`,
  Zeitzone Europe/Berlin. Zwei Läufe geben byte-gleiche PNGs (Test).
- **Builds:** Endzustand (Frage 1): alle `[data-build]` der Folie bekommen `on`; ein Test prüft,
  dass eine Folie mit `{.build}` byte-gleich der ohne ist.
- **Werkzeug** `tools/preview/preview.py`: `--scale n`, `--slides 3,7-9`, `--html` (Deck in den
  Vorschau-Ordner), `--check-browser` (für `setup`). Ausgabe englisch wie `generate`/`check`
  (`wrote …`, `skipped …: there is no preview for Word documents`, `ERROR …`), danach die
  Hinweise des Generators. Exit-Code 1 bei Fehlern/fehlender Vorschau, 2 bei falschen Schaltern.
  Bilder unter `vorschau/` gehen nicht als Ressourcen ins Deck.
- **Setup** (`run.sh`/`run.ps1`, im Gleichschritt): nach den übrigen Extras eigener
  `pip install -e .[preview]`; startet dann kein Chromium (`preview --check-browser`), folgt
  `python -m playwright install chromium`. Jeder Fehler dabei ist nur eine Meldung (Plan 1, Notiz
  zur Remote-Umgebung: vorhandenes Chromium wird nicht neu installiert).
- **Kontaktbogen:** Kacheln 400 px breit, vier je Zeile, 16 px Abstand, Foliennummer darunter in
  Selawik, Hintergrund `GREY_LIGHT`; bei weniger Bildern nur so breit wie nötig.
- `.gitignore`: `samples/*/vorschau/`.
- E08-S03 Punkt 5 erledigt sich mit: der Referenztest rendert die Funktionen-Präsentation, und
  `./run.sh preview samples/funktionen` zeigt sie ohne Office (in `docs/anleitung.md` genannt).

### Abweichungen vom Plan

- **Kein Dateisystem in der Bibliothek:** statt `render_deck(html, folder) -> list[Path]` gibt
  `render_deck` PNG-Bytes zurück und `contact_sheet` nimmt/gibt Bytes; Dateien schreibt nur das
  Werkzeug (Standard „Stream rein, Stream raus").
- **`data-slides`/`data-settled` gibt es nicht** (E10-S01 schreibt sie nicht). Die Folienzahl
  kommt aus `section.slide`, das „Ende der Übergänge" aus reduzierter Bewegung, abgeschalteten
  Animationen, `document.fonts.ready` und zwei Frames. `deck.js` und der Writer bleiben
  unverändert (sonst ändern sich CSP-Hash und Schnappschuss von E10-S01).
- **Schalter englisch** (Frage 4): `--slides` statt `--folien`; Meldungen englisch wie die
  anderen Werkzeuge, nicht „Für Word gibt es keine Vorschau".
- **Referenzbilder in halber Größe:** gerendert wird mit `--scale 1` (1600 × 900), gespeichert
  und verglichen wird auf 800 × 450 herunterskaliert (Lanczos, PNG optimiert): 69 Folien sind so
  5,8 MB statt 13,8 MB. Ein Pixel gilt als abweichend, wenn ein Kanal um mehr als 16/255
  abweicht; erlaubt sind < 0,5 % je Folie. Diagramme nur mit `ChartRenderer` (Mermaid hinge vom
  Rechner ab).
- Tests in `tests/preview/test_deck.py` und `tests/preview/test_preview_tool.py` (Werkzeug
  per Pfad geladen wie in `test_funktionen.py`); Bilder zum Ansehen in `.tmp/review/preview/`.

### Warnungen

- **Warnung:** Die Referenzbilder sind ~5,8 MB Binärdaten im Repo und ändern sich bei jeder
  sichtbaren Änderung an PPTX-Layout, HTML-Writer oder der Funktionsübersicht (dann mit
  `PTA_DOCUMENTS_UPDATE_EXPECTED=1` neu schreiben) — jede Erneuerung lässt das Repo um bis zu
  diese Größe wachsen. Vorsichtigste Wahl zwischen „14 MB" und „nur Struktur" war halbe Größe;
  reicht das nicht, wäre eine Auswahl von Folien der nächste Schritt (Frage an den Menschen).
- **Warnung:** „< 0,5 % auf einer anderen Maschine" (AK 3) ist nur auf dieser Maschine (Linux,
  Playwright 1.64.1, chrome-headless-shell) geprüft. Eine andere Chromium-Version oder ein
  anderes Betriebssystem kann bei Kantenglättung und Fotos stärker abweichen; dann schlägt der
  Referenztest fehl, obwohl die Folien richtig sind.
- **Warnung:** Die Vorschau zeigt das HTML-Deck, also Selawik statt Segoe UI und die
  Vereinfachungen aus E10-S01 (z. B. Morph ohne Bewegung, Zeilenabstand angenähert). Sie ist ein
  Ersatz-Prüfpunkt, nicht der Blick in PowerPoint.
- **Warnung:** `./run.sh setup` wurde nach der Änderung nicht vollständig ausgeführt (es würde
  auch `npm ci` laufen lassen); geprüft sind `bash -n run.sh`, `preview --check-browser` und die
  Installation des Extras aus E10-S01. `run.ps1` ist ungetestet (kein PowerShell hier).
- **Warnung:** Mehrere Präsentationen in einem Lauf starten je Datei ein eigenes Chromium
  (~1 s); die Funktionsübersicht (69 Folien) braucht rund 6 s.

### Prüfpunkte für den Menschen

- `./run.sh preview samples/gsb` und `samples/gsb/vorschau/gsb-praesentation/uebersicht.png`
  ansehen; einzelne Folien mit dem HTML-Deck im Browser vergleichen (AK 1).
- `./run.sh preview samples/funktionen` auf einem Windows-Rechner mit Segoe UI: Bilder müssen
  Selawik zeigen und mit `.tmp/review/preview/funktionen-praesentation/` übereinstimmen; der
  Referenztest `./run.sh test tests/preview` dort grün (AK 3).
- `.\run.ps1 setup` auf Windows: installiert Playwright und Chromium, ohne bei einem Fehler
  abzubrechen.
- Eine KI mit `docs/ki-anleitung.md` (Grundregel 3 und Checkliste) eine Präsentation schreiben
  lassen und prüfen, ob sie die Vorschau ansieht, bevor sie meldet (AK 4).

### Offene Punkte

- Zielgruppenfassungen (E16-S01, parallel in Arbeit) sind im Werkzeug nicht berücksichtigt:
  `preview` erzeugt das Deck wie `generate` ohne Schalter; braucht `generate` künftig Schalter
  für die Fassung, sollte `preview` sie übernehmen.
- Vergleich HTML ↔ PPTX als Differenzbild, sobald LibreOffice verfügbar ist (Notiz im Plan).
