# Anleitung für KI-Assistenten: Dokumente erzeugen

Diese Datei ist für eine KI, die im Auftrag eines Anwenders **mit** PTA Documents arbeitet:
Markdown schreiben, daraus PTA-Word-Dokumente und PTA-Präsentationen erzeugen, vorhandene
Dateien nach Markdown lesen. Wer **an** der Bibliothek entwickelt, folgt stattdessen
[AGENTS.md](../AGENTS.md) und `ai/`.

## Grundregeln

1. **Nur in `documents/` arbeiten.** Dort liegen die Dokumente des Anwenders, ein Ordner je
   Thema; der Ordner ist git-ignoriert. Nichts unter `src/`, `tests/`, `tools/`, `spec/`, `ai/`,
   `samples/` oder `source-templates/` ändern, nichts committen oder pushen — der Anwender nutzt
   nur einen Klon.
2. **Das Design kommt von den Vorlagen.** Keine Farben, Schriften, Größen oder eigenen Layouts
   ins Markdown schreiben — es gibt dafür keine Syntax, und das ist Absicht. Das Ergebnis ist
   immer im PTA-Design.
3. **Erst prüfen, dann erzeugen:** `./run.sh check documents/<thema>` schreibt nichts und meldet
   dieselben Fehler und Hinweise wie `generate`, dazu Stilhinweise (`style-…`: zu volle Folien,
   Fließtext in Punkten, gemischte Satzzeichen, lange Titel, Bilder ohne Alt-Text oder Urheber,
   Handnummern in Word-Überschriften) und eine Statistik (Folien, Wörter je Folie, Dauer);
   `--strict` endet bei Hinweisen mit Code 1. Stilhinweise beheben; passt eine Regel bewusst
   nicht, im Front Matter `pruefung: <code>, …` setzen und das dem Anwender sagen.
   Dann `./run.sh generate documents/<thema>`; der Befehl endet mit
   Code ≠ 0, wenn eine Datei einen Fehler hat. Fehlermeldungen (`ERROR <datei>: <grund>`) sind für
   den Schreiber formuliert — den Grund lesen, das Markdown korrigieren, neu erzeugen.
   **Hinweise lesen:** unter `wrote <datei>` stehen eingerückt die Hinweise
   (`  - line 12: …`), was der Generator umgehen musste. Das Markdown so ändern, dass keine mehr
   kommen; `(Forts.)`-Folien (`slide-split`) sind fast immer ein Zeichen für zu viel Inhalt.
   Mit `--strict` endet der Befehl auch bei Hinweisen mit Code 1 — so lässt sich prüfen, ob
   alles sauber ist. Codes: [verwendung.md](verwendung.md#hinweise-generationresult).
   **Dann die Folien ansehen:** `./run.sh preview documents/<thema>` legt je Präsentation ein
   PNG je Folie und `uebersicht.png` in `documents/<thema>/vorschau/<name>/` ab. Zuerst
   `uebersicht.png` ansehen (mit dem Werkzeug, das Bilder lesen kann, z. B. Read), dann die
   auffälligen Folien einzeln. Folien korrigieren, deren Titel umbricht, deren Text verkleinert
   wurde (kleiner als auf den Nachbarfolien), deren Bild Wichtiges abschneidet (`focus=`,
   `fit=contain`) oder die leer oder überfüllt wirken; danach `generate` und `preview` erneut.
   Erst dann den Anwender informieren. Endet `preview` mit „Playwright is not installed" oder
   „Chromium does not start", einmal `./run.sh setup` versuchen; geht es dann nicht, dem
   Anwender sagen, dass die Folien nicht angesehen wurden.
4. **Einmalig einrichten**, falls `.venv/` fehlt: `./run.sh setup` (Windows `.\run.ps1 setup`).
5. **Fakten nicht erfinden.** Inhalte kommen vom Anwender oder aus Quellen, die er nennt. Fremde
   Bilder nur mit passender Lizenz; Urheber und Lizenz in der Bildunterschrift bzw. auf der
   Folie nennen und in `documents/<thema>/QUELLEN.md` festhalten (Muster: `samples/gsb/`).

## Dateien und Namen

```
documents/<thema>/
  <name>-bericht.md         → <name>-bericht.docx        (auch …-dokument.md)
  <name>-praesentation.md   → <name>-praesentation.pptx  (auch …-folien.md)
  images/…                  → Bilder, im Markdown relativ: images/foto.jpg
```

Bilder: PNG, JPEG, GIF, BMP, TIFF und **SVG** (wird scharf eingebettet; braucht `width`/`height`
oder eine `viewBox`, lädt nichts von außen, Text erscheint in der PTA-Schrift). Andere
Dateinamen mit `--docx`/`--pptx`; Ausgabe woanders mit `--out <ordner>`.

Vollständige, funktionierende Beispiele: `samples/gsb/gsb-bericht.md` und
`samples/gsb/gsb-praesentation.md`; jede unterstützte Funktion einmal zeigt
`samples/funktionen/` (siehe dessen `README.md`; `funktionen-bericht.md` zeigt zu jeder
Funktion den Quelltext als ```` ```markdown ```` und darunter das Ergebnis). Bei Unsicherheit an
ihnen orientieren.

## Front Matter

Erster Block der Datei, zwischen `---`-Zeilen, flach `schlüssel: wert` (kein verschachteltes
YAML, keine Listen). Schlüssel und Werte sind **deutsch**; `ja`/`nein`; Datum `JJJJ-MM-TT` oder
`TT.MM.JJJJ`. Unbekannte Schlüssel sind Fehler.

| Schlüssel | Word | PPTX | Werte |
| --------- | :--: | :--: | ----- |
| `vorlage` | ✓ | ✓ | Word `hoch` (Standard) · `hoch-ohne-deckblatt` · `quer` · `quer-ohne-deckblatt`; PPTX `basis` (Standard) · `schulung` |
| `titel` | ✓ | ✓ | Pflicht bei Word-Vorlagen mit Deckblatt |
| `untertitel`, `autor`, `ort`, `datum` | ✓ | ✓ | frei; Datum siehe oben |
| `sprache` | ✓ | ✓ | `de` · `en` (erzeugte Texte, englische Titelfolie) |
| `firma` | ✓ | – | ersetzt „PTA IT-Beratung" in der Fußzeile |
| `inhaltsverzeichnis` | ✓ | – | `ja` · `nein` |
| `fusszeile` | – | ✓ | Fußzeilentext nach „PTA – " |
| `titelfolie` | – | ✓ | `bild-02` (Standard) · `bild-01` · `branchen` · `ohne-bild` |
| `fassung` | ✓ | ✓ | `kunde` (Standard) · `intern` · `trainer` — siehe [Zielgruppenfassungen](#zielgruppenfassungen); `--audience` geht vor |
| `kennzeichnung` | ✓ | ✓ | `vertraulich` · `intern` · `entwurf` · `kein`; PPTX: Sticker, Standard `basis` ohne, `schulung` `intern` (dort ist `kein` ein Fehler); Word/PDF: Text unter dem Logo und auf dem Deckblatt, `entwurf` mit Wasserzeichen, Standard `kein` — vertraulicher Inhalt: `vertraulich`; `entwurf` nur, solange das Dokument nicht verschickt wird |
| `typografie` | ✓ | ✓ | `ja` (Standard) · `nein` — gerade Zeichen behalten |
| `syntaxhervorhebung` | ✓ | ✓ | `ja` (Standard) · `nein` — Codeblöcke einfarbig |
| `pruefung` | ✓ | ✓ | nur `check`: `aus` · Liste von `style-…`-Codes, die nicht geprüft werden |
| `aufbau` | – | ✓ | `listen` (jede Liste Punkt für Punkt) · `nein` (Standard) |
| `uebergang` | – | ✓ | `none` (Standard) · `fade` · `push`/`wipe` (auch `-left`, `-right`, `-up`, `-down`) · `split` · `cover` · `uncover` · `zoom` · `cut` · `morph` |
| `beginn` | – | ✓ | Uhrzeit `09:00` — Beginn der Schulung (Agenda mit Uhrzeiten), siehe [Schulungs-Zeitplan](#schulungs-zeitplan) |
| `laenge` | – | ✓ | Minuten `240` · `4h` · `3h30` — geplante Länge, mit der Summe der `dauer` verglichen |
| `fortschritt`, `kapitelanzeige` | – | nur `--html` | `ja` (Standard) · `nein` — nur im HTML-Deck; PowerPoint lehnt sie ab, also **nicht** in eine Präsentation schreiben, die als PPTX erzeugt wird |

`firma`/`inhaltsverzeichnis` in einer Präsentation oder `fusszeile`/`titelfolie` in einem
Word-Dokument sind Fehler.

**Typografie:** Gerade Anführungszeichen (`"…"`, `'…'`), ` - ` und `...` schreiben — die
Generatoren setzen daraus „…“, ‚…‘, –, … und geschützte Leerzeichen in `z. B.`, `u. a.`,
`d. h.`, `Nr. 3`, `S. 12`, `§ 5`, `10 %`, `5 km`, `3 Mio.`, `1. Januar`. Keine typografischen
Zeichen von Hand tippen, keine `&nbsp;`. Code, Links und Front Matter bleiben unberührt.
**Codeblöcke** immer mit Sprache (```` ```python ````), dann werden sie farbig; unbekannte
Sprache = Hinweis `code-language-unknown`.

## Word-Bericht

- `#` ist **Kapitel** (Überschrift 1, nummeriert), nie der Titel — der Titel steht nur im Front
  Matter. `##`, `###` = Überschrift 2/3; `####`+ = unnummerierte Zwischenüberschrift. Überschriften
  ohne eigene Nummern schreiben (Word nummeriert selbst).
- **Anhänge:** `# Glossar {.appendix}` an das erste Anhangskapitel (einmal, nicht „Anhang" als
  eigenes Kapitel davor) — ab dort heißen die Kapitel A, B, C (A.1, A.1.1), auch im
  Inhaltsverzeichnis und im PDF. Jedes `#` danach ist der nächste Anhang, ohne Attribut.
- Absätze, `-`/`1.`-Listen (bis drei Ebenen), Tabellen, `> Zitat`, Codeblöcke, Links, Fußnoten
  `[^1]`, **fett**, *kursiv*, ~~durchgestrichen~~, `code` gehen.
- Derselbe Bericht geht mit `--pdf` (bei `generate` und `check`) auch als PDF: gleiche Syntax,
  Grafiken als Vektoren, Gantt als Tabelle. Zeichen, die der Schrift fehlen (Emoji, Griechisch,
  Kyrillisch ohne Segoe UI), werden `?` mit Hinweis `character-missing` — in Worten schreiben.
- Tabellenbeschriftung: direkt unter der Tabelle ein Absatz `Tabelle: Beschreibung` →
  „Tabelle n: Beschreibung". Tabellentitel: ein Absatz nur aus `**Titel**` direkt davor.
- Abbildung: Bild allein im Absatz, Unterschrift als Bildtitel:
  `![Alt-Text](images/a.jpg "Unterschrift (Foto: Name, CC BY 4.0)")` → „Abbildung n: …".
- Kein HTML (wird weggelassen, Hinweis `raw-html`; nur `<br>` in Tabellenzellen ist ein
  Zeilenumbruch). Diagramme aus Zahlen: `chart`- und `financial-chart`-Blöcke, Abläufe:
  `mermaid`, siehe unten; Beschriftung dazu mit einem Absatz `Abbildung: …` direkt nach dem
  Block → „Abbildung n: …".
- Folien-Syntax (`:::`-Container, Alerts `> [!NOTE]`, `==Markierung==`, `[Wörter]{.success}`)
  wird angenommen und schlicht gezeigt: Container-Inhalt nacheinander (`###` in Containern wird
  fett, keine Überschrift), Alerts/`conclusion`/`comment` als Hinweisabsatz mit fetter Art,
  Markierung gelb, farbige Wörter und Status-Labels in der Statusfarbe. Mehrere Bilder in einem
  Absatz (`![a](x.png) ![b](y.png)`) stehen nebeneinander (max. vier je Zeile), je mit
  „Abbildung n".
- QR-Code: `![QR-Code zur Umfrage](qr:https://… "https://…")` → QR-Code in PTA-Blau, 3 × 3 cm,
  den Link als Titel (wird „Abbildung n: https://…", gedruckt lesbar). `{scale=0.5}` direkt
  nach dem Bild halbiert ihn (nicht mehr im Titel: Hinweis `image-scale-in-title`). Keine
  Bilddatei nötig, keine Quelle in `QUELLEN.md`.
- Bildattribute direkt nach dem Bild, ohne Leerzeichen: `{.round}` (rund, Kontaktfotos),
  `{.grey}` (Graustufen), `{scale=0.5}` (Größe, 0 < N ≤ 5) — in Word, PowerPoint und PDF;
  mehrere in einer Klammer: `![Erika Mustermann](images/erika.jpg){.round focus=50%,30%}`.
- Zeitstrahl und Projektplan (Word und Präsentation gleich): `::: timeline` mit 2–8 Einträgen
  `- 2026-Q2: Text` (aufsteigend; Termin = `2026`, `2026-03`, `2026-Q2`, `2026-03-15`,
  `15.03.2026` oder `heute`; `{.done}` am Ende = erledigt, grau) und `::: gantt` (Argument
  `raster=woche|monat|quartal` nur bei Bedarf) mit einer Tabelle `| Vorgang | Start | Ende | Wer |`
  (vierte Spalte optional; 1–12 Zeilen; Start = Ende = Meilenstein; höchstens 24 Raster-Spalten).
  Auf Folien: eigene `##`-Folie. In Word wird der Gantt eine Tabelle, der Zeitstrahl ein Bild.
- Schrittfolge, Bewertung, Risiken (Word und Präsentation gleich): `::: steps` mit 3–6
  Schritten, je `### Titel` und höchstens einem kurzen Absatz darunter, `{.current}` an
  höchstens einem `###`. Harvey Balls: eine Tabellenzelle genau `[0/4]` … `[4/4]`
  (Bewertungsmatrix: Kriterien in Zeilen, Optionen in Spalten, `[3/4]` je Zelle). `::: riskmatrix`
  (Argumente `green=4 yellow=12` nur bei Bedarf) mit einer Tabelle
  `| Nr | Risiko | Wahrscheinlichkeit | Auswirkung | Maßnahme |` (Maßnahme optional; 1–15
  Zeilen; Werte ganze Zahlen 1–5; Nummern eindeutig, höchstens 3 Zeichen). Auf Folien je eine
  eigene `##`-Folie.

## Präsentation

Die vollständige Anleitung für Präsentationen (alle Syntax, Schlüssel, Layoutnamen und Icons, aus
dem Code erzeugt) gibt `./run.sh authoring-guide pptx` aus; sie gilt auch für das HTML-Deck.

Gliederung:

```markdown
# Präsentationstitel            ← Titelfolie (erstes #); Text darunter = Untertitel, nur Text
# Kapitel                       ← Trennfolie „01", „02" …  — KEIN Inhalt darunter
## Folientitel                  ← eine Folie (Titel höchstens zwei Zeilen)
# Schlussbotschaft {.closing}   ← Abschlussfolie — KEIN Inhalt darunter
# Backup {.backup}              ← optional: Trennfolie ohne Nummer, dann Reservefolien
```

- **Backup:** Folien für Rückfragen nach der Abschlussfolie hinter `# Backup {.backup}` (einmal,
  immer nach `{.closing}`). Alles danach ist Backup: keine Kapitelnummer, nicht in der Agenda,
  Fußzeile „… · Backup". Für Word heißt das Gegenstück `{.appendix}`; das jeweils andere
  Attribut ergibt den Hinweis `attribute-ignored`.

- Absatz = Einleitungstext, `-`-Listen = Aufzählung (bis drei Ebenen), `1.` = nummeriert,
  `###` = Subheadline. **Fett** erscheint in Segoe UI statt Light (PTA-Hervorhebung).
- Je Folie wenig Text: höchstens etwa 6–8 Aufzählungspunkte. Zu viel wird verkleinert und sonst
  auf „(Forts.)"-Folien geteilt — das sieht schlechter aus als bewusst geteilte Folien.
- **Eine Tabelle, ein Codeblock oder eine Bildreihe je Folie.** Text davor steht oben, Text
  danach unten (gut für Quellenangaben). Ein zweites Visual unter derselben `##` erzeugt eine
  weitere Folie mit demselben Titel. Tabellen höchstens etwa 8 Zeilen, sonst werden sie geteilt.
- Ein `**fetter**` Absatz direkt vor einer Tabelle wird deren Titelzeile.
- Ein Bild + Text → Layout „Titel, Text und Bild 01" (Bild rechts, beschnitten); ein Bild allein →
  „Titel und Bild 01"; mehrere Bilder in einem Absatz → nebeneinander (max. vier je Folie).
  Verliert ein Bild mehr als ein Viertel seiner Fläche an den Rahmen (`image-cropped`) oder wird
  es mehr als doppelt vergrößert (`image-enlarged`), kommt ein Hinweis — dann ein Bild in
  passenden Proportionen bzw. höherer Auflösung ablegen.
- **Bildausschnitt:** Bei Fotos mit Personen immer `{focus=…}` setzen, damit der Rahmen die
  Köpfe nicht abschneidet: `![Team](images/team.jpg){focus=top}` oder ein Punkt
  `{focus=50%,30%}` (von links, von oben); Werte `center` (Standard), `top`, `bottom`, `left`,
  `right`, `x%,y%`. Grafiken und Screenshots mit `{fit=contain}` ganz zeigen statt beschneiden.
  `{.round}` macht ein rundes Bild um den Fokus (Kontaktfotos nur auf Wunsch rund), `{.grey}`
  ein Graustufenbild. Unbekannte Angaben (`{.shadow}`) sind Fehler. Word schneidet nie zu:
  `focus`/`fit` wirken nur auf Folien.
- QR-Code (Umfrage, Unterlagen) auf die letzte Inhaltsfolie, nicht auf die Abschlussfolie:
  `![QR-Code zur Umfrage](qr:https://…)` mit einem Satz daneben; er wird in den Bildrahmen
  eingepasst, nie beschnitten. Den Link zusätzlich als Text auf die Folie schreiben.
- Ein bestimmtes PTA-Layout: `## Titel {layout="Titel und Text (zweispaltig)"}` und den Inhalt mit
  `---` in Spalten teilen. Nur exakte Layoutnamen; die Fehlermeldung listet alle.
- Heading-Attribute: `#` kennt `.closing`, `.backup`, `layout="…"` und `uebergang="…"`, `##` kennt `.dark`,
  `kicker="…"`, `layout="…"`, `uebergang="…"` und die PTA-Folienarten `.agenda`, `.interim`, `.quote`, `.contact` (siehe
  unten); alles andere ist ein Fehler. `kicker` ist eine kleine Zeile über dem Titel,
  `.dark` setzt die Folie auf den Verlauf der Titelfolie mit weißer Schrift (beides macht die
  Folie zur Flow-Folie, siehe unten).

- **Sprechernotizen:** zu **jeder** Folie (auch Titel-, Trenn- und Abschlussfolie) einen Block
  `::: notes` … `:::` unter ihre Überschrift schreiben, zwei bis fünf Sätze, die der
  Vortragende sagt — nicht den Folientext wiederholen. PowerPoint legt sie auf die Notizenseite
  (bei geteilten Folien auf jede), Word lässt sie weg (Hinweis `notes-dropped`, beim
  Word-Bericht also keine Notizen schreiben). Absätze, Listen, fett, kursiv, Code und Links
  bleiben; Tabellen und Bilder darin fallen weg. Nie vor dem ersten `#`.
- **Builds (Klick für Klick):** eine Zeile `{.build}` direkt vor einer Liste, `::: cards`,
  `::: rows`, `::: columns` oder einer Bildreihe lässt die Elemente einzeln erscheinen, vor jedem
  anderen Block (Tabelle, Code, Chart, Container, Absatz) den Block als Ganzes; `{.frag}` immer
  als Ganzes. Eingang wählbar: `{.build=appear}`, `=fly`, `=wipe` (Standard: einblenden).
  `{.exit}` blendet einen Block beim Klick aus, `{.emphasize}` färbt Text (Absatz, Liste) beim
  Klick PTA-blau. Sparsam einsetzen: eine Argumentationsliste oder eine Kartenreihe je Folie,
  nicht jede Folie. Nur unter `##`-Folien — nie auf Titel-, Trenn-, Abschlussfolie oder
  PTA-Folienarten, nie vor `#`/`##`, nie als letzte Zeile; Word und PDF ignorieren die Zeile.
- **Übergänge:** höchstens einer für das ganze Deck (`uebergang: fade` im Kopf) oder je Kapitel
  (`# Kapitel {uebergang="fade"}`, gilt für alle Folien darunter); `{uebergang="…"}` an einem
  `##` nur für eine Folie, die etwas Besonderes zeigt. `none` schaltet ihn ab. `morph` wirkt nur
  in PowerPoint 2019/365 (sonst Überblenden). Ohne Bitte des Menschen keinen Übergang setzen.
- **Szenen:** `::: scene` allein unter einem `##` (nur `::: notes` daneben), eine Form je Zeile
  `- name: art x,y bxh "Text" attr=wert` (Arten `box`, `round`, `pill`, `circle`, `text`, `line`,
  `arrow`, `image`; Raster 160 × 67 über der Inhaltsfläche, nichts darüber hinaus; Farben nur
  die Rollen `primary`, `text`, `muted`, `surface`, `border`, `line`, `background`,
  `accent1`–`accent6`, `success`, `info`, `warning`, `danger`, `neutral`). Für eine Veränderung
  zwei Szenenfolien mit denselben Namen, die zweite `{uebergang="morph"}`. Nur, wenn ein Bild
  sich wirklich von Folie zu Folie verändert; Word lässt Szenen weg.

## PTA-Folienarten (PowerPoint)

Höchstens eine je `##`, nie zusammen mit `.dark`, `kicker` oder Containern/Alerts. Word zeigt
sie schlicht: Agenda als Überschrift mit Liste (ohne Liste die folgenden `#`-Kapitel),
Zwischenfazit fett, Zitat und Quelle als Zitat, Kontakt mit fettem Namen und kleinem Foto.

| Schreiben | Ergebnis |
| --------- | -------- |
| `## Agenda {.agenda}` + **eine** Liste (je Punkt eine Zeile, max. 8) | Agendafolie mit „01" …; ≤ 4 kurz, 5–8 lang; mehr = Fehler → zwei Agendafolien |
| `## Agenda {.agenda}` ohne Inhalt | Agenda aus den `#`-Kapiteln (ohne Titel, `{.closing}` und Backup) |
| `## Aussage {.interim}` — **kein** Inhalt darunter | Zwischenfazit (`layout="Zwischenfazit 02"` für die zweite Variante) |
| `## Pause {.break dauer=15}` — **kein** Inhalt darunter | Pausenfolie „Pause · 15 min" auf dem Zwischenfazit-Layout, siehe [Schulungs-Zeitplan](#schulungs-zeitplan) |
| `## Zitat {.quote}` + höchstens **ein** Absatz (die Quelle) | Zitatfolie (`layout="Zitat 02"`) |
| `## Kontakt {.contact}` + je Person `### Name` und **ein** Absatz mit Foto und Zeilen Funktion / E-Mail (mit `@`) / Telefon (`+` oder Ziffer am Anfang) | Kontakt 01–05 nach Personenzahl (max. 5); genau eine Person + weiterer Text/Liste danach → „Kontakt mit Text" |

- Keine Agenda ohne `{.agenda}` — es gibt keine automatische.
- Jede Kontaktart (Funktion, E-Mail, Telefon) höchstens einmal je Person; Fotos hochkant
  (etwa 7 : 9), sonst kommt `image-cropped`.

## Folien-Syntax (Word und PowerPoint)

Beide Formate nehmen dieselbe Syntax an und melden dieselben Fehler mit Zeilennummer
(`Line 12: …`). **PowerPoint** macht aus einer `##`-Folie mit Container, Alert, Tag-Absatz,
`.dark` oder `kicker` eine **Flow-Folie** auf „Nur Titel"; **Word** zeigt den Inhalt schlicht in
eigenen Formatvorlagen (siehe *Word-Bericht*).

| Schreiben | PowerPoint |
| --------- | ---------- |
| `::: cards` mit `### Titel` je Karte (optional erster Absatz `**26 %**` = Kennzahl) oder einer Liste `- **Titel** – Text` | Karten nebeneinander im Raster, höchstens vier je Zeile |
| `::: rows` mit einer Liste `- **Begriff** – Beschreibung` | Begriff links, Beschreibung rechts, Linien wie die Tabelle |
| `::: panel` / `::: panel dark` | graue / dunkelblaue Fläche |
| `::: statement` | erster Absatz groß und fett, der Rest normal |
| `::: columns` / `::: columns 1:2` / `1:1:2`, Teile durch `---` (Leerzeile davor) getrennt | Spalten; genau zwei gleiche Spalten nur mit Text → Layout „Titel und Text (zweispaltig)" |
| `::: conclusion` (nur Text, höchstens zwei Zeilen, einmal je Folie, nicht in anderen Containern) | PTA-Fazit-Box am Fuß der Folie; länger = Fehler |
| `::: comment` (nur Text, direkt nach dem Block, den sie kommentiert) | PTA-Kommentarbox: Sprechblase rechts oben auf dem Block davor — am besten nach einem Bild |
| `> [!NOTE]` als erste Zeile eines Zitats (`NOTE`, `TIP`, `IMPORTANT`, `WARNING`, `CAUTION`) | graue Fläche, Balken blau bzw. gelb |
| Absatz nur aus `` `a` `b` `` | Chips; in einem Container eine Liste `` - `x` Text `` = Chip mit Text daneben |
| `==Wort==` (alle Folien) | fett auf Gelb; erste Tabellenzelle ganz markiert = Zeile gelb |
| `[im Plan]{.success}` (`.warning`, `.danger`, `.info`, `.neutral`) | fett in der Signalfarbe |
| Front Matter `status.success: Erledigt; Fertig` + Tabellenzelle `` `Erledigt` `` (Flow-Folie) | Ampelpunkt „●" in der Farbe vor dem Text; nicht zugeordnet = grau |

- Flow-Folien nicht überladen: was nicht passt, wird bis zu zweimal um ein Achtel kleiner und
  dann auf „(Forts.)"-Folien geteilt (Hinweis `slide-split`); Karten, Flächen und Spalten
  werden nie geteilt. Mit Flow-Inhalt ist nur `layout="Nur Titel"` erlaubt.
- Signalfarben nur für Status; zur Hervorhebung `==…==` (Gelb).

Andere Namen sind Fehler; die Meldung listet die gültigen. Klammern, die nicht genau so aussehen
(`[a] {.success}`, `## Mengen {a, b}`), bleiben Text.
- Text vor dem ersten `#` wird ignoriert; Fußnoten werden auf Folien weggelassen.

## Icons (`:icon-name:`, Word und PowerPoint)

`:icon-check:` setzt ein gebündeltes Strich-Icon (Tabler Icons, MIT) in PTA-Blau — keine
Bilddatei, keine Quelle in `QUELLEN.md`.

- **Karte** (PowerPoint): `### :icon-rocket: Start` in `::: cards` (oder
  `- :icon-rocket: **Start** – Text`) → Icon als Figur über dem Titel. Icon und `**Kennzahl**` in derselben Karte = Fehler.
- **Aufzählung**: beginnt **jeder** Punkt einer `-`-Liste mit einem Icon, wird es das
  Aufzählungssymbol (Word, PowerPoint und PDF). Sonst steht es im Text.
- **Im Text**: Word und PDF (so hoch wie die Schrift). Auf Folien ist ein Icon im Text, in
  Titeln, Tabellen oder Notizen ein Fehler — dort nur Karten und Listen.
- Nur die gebündelten Namen; ein anderer ist ein Fehler mit den drei ähnlichsten. Die
  vollständige Liste steht im Authoring Guide: `./run.sh authoring-guide pptx`, Abschnitt *Icons*.

## Diagramme aus Daten (`chart`, Word und PowerPoint)

Zahlen als Diagramm: ein Codeblock `chart` mit Einstellungen, einer Zeile `---` und den Daten
als CSV (Kopfzeile: Kategorienspalte, dann je Reihe ein Name; eine Zeile je Kategorie):

````markdown
```chart
type: bar
title: Aufträge je Quartal
unit: Mio. EUR
source: Quelle: Vertrieb
---
Quartal, Plan, Ist
Q1, 12.5, 13.2
Q2, 11.8, 12.1
```
````

- Einstellungen sind **englisch** und freiwillig: `type: bar|line|area` (Standard `bar`),
  `stacked: true|false` (Linien stapeln nie), `title`, `unit`, `source`. Andere Schlüssel sind
  ein Fehler. Nichts hinter ```` ```chart ```` schreiben.
- Zahlen: Trennzeichen `,` → Dezimalpunkt (`12.5`); Trennzeichen `;` → Dezimalkomma (`12,5`).
  Keine Tausenderpunkte, keine Einheiten in den Zellen. Leeres Feld = Lücke. Höchstens etwa
  zwölf Kategorien und fünf Reihen.
- Word: Diagramm über die Textbreite, mit `title` darunter „Abbildung n: Titel", `source`
  darunter, `unit` an der Werteachse; ein Absatz `Abbildung: …` direkt nach dem Block ersetzt
  den Titel als Beschriftung. PowerPoint: ein Chart je Folie (`Titel und Diagramm`),
  Text davor oder danach → `Titel, Text und Diagramm` bzw. `Titel, Diagramm und Text`, zwei
  Charts (gern in `::: columns`) → `Titel und zwei Diagramme`; Titel, Einheit, Quelle in den
  Platzhaltern. Kein Chart auf Folien mit Hinweisboxen, Karten oder `.dark`.
- Ein Fehler im Block bricht mit der Zeilennummer ab — die Meldung sagt, was zu ändern ist.

## Finanzdiagramme (`financial-chart`)

Für Ergebnisübersichten: ein Codeblock `financial-chart` mit **einem JSON-Objekt**. `type` ist
`development`, `growth-by-row`, `actual-vs-reference`, `growth-trend`, `two-year` oder
`summary-table`; die übrigen Schlüssel sind englisch in camelCase. Vorlage für jeden Typ (alle
Felder): `samples/funktionen/funktionen-praesentation.md`, Kapitel „Finanzdiagramme".

- Raten und Anteile als Bruch (`0.052` = 5,2 %), Beträge als Zahl (mit `"options": {"scale":
  1000000, "unit": "Mio. EUR"}` in Millionen gezeigt), `lastActual` ist der Index des letzten
  Ist-Monats ab 0, ein Monat ohne Wert ist `null`.
- Nur bekannte Schlüssel; Tippfehler, Text statt Zahl oder fehlende Pflichtfelder sind Fehler mit
  Zeilennummer. `"options"`: `culture`, `scale`, `unit`, `labels`, `tolerance`, `restShare`,
  `width`.
- Eine Folie je Diagramm, Text davor oder danach geht; nicht auf Flow-Folien (`.dark`, Container).
- Word: ein Bild in natürlicher Größe; für eine Beschriftung direkt nach dem Block einen Absatz
  `Abbildung: …` schreiben (sonst keine).

## Mermaid-Diagramme (`mermaid`)

Abläufe, Sequenzen, Klassen, Zustände, Datenmodelle, Tortendiagramme, Pläne und Mindmaps als
Codeblock `mermaid`; auf der Folie eine Gruppe bearbeitbarer Formen in den PTA-Farben, in Word
ein scharfes Bild (Beschriftung mit einem Absatz `Abbildung: …` direkt nach dem Block). Vorlage
für jede Art: `samples/funktionen/mermaid-praesentation.md`, für Word
`samples/funktionen/mermaid-bericht.md`.

- Nur `flowchart`/`graph`, `sequenceDiagram`, `classDiagram`, `stateDiagram-v2`, `erDiagram`,
  `pie`, `gantt`, `mindmap`; andere Arten bleiben Code. Keine `classDef`/`style`-Farben.
- Klein halten (bis etwa zwölf Knoten, kurze Beschriftungen), eine Folie je Diagramm.
- Braucht mermaid-cli (`./run.sh mermaid` prüft es). Ohne bleibt der Block Code mit Hinweis
  `code-not-drawn`; dann den Menschen fragen, statt das Diagramm anders nachzubauen.
- Ein Syntaxfehler bricht mit Zeilennummer und der Meldung von Mermaid ab.

## Zielgruppenfassungen

Eine Quelle, drei Fassungen: `kunde` (Standard: nichts Internes, keine Lösungen), `intern`
(Internes, keine Lösungen), `trainer` (alles). **Regel: Preise, Tagessätze, interne Bemerkungen
und alles, was der Kunde nicht sehen soll, immer in `::: internal` oder hinter `{.internal}`
schreiben, Lösungen immer in `::: solution`** — dann bleibt die Kundenfassung sauber, ohne dass
eine zweite Datei gepflegt wird.

```markdown
{.internal}
Ein Absatz (Liste, Tabelle, Bild, Container) nur für PTA.

::: internal
Mehrere Blöcke nur für PTA.
:::

::: exercise
Die Aufgabe — steht in jeder Fassung.
:::

::: solution
Die Lösung — nur beim Trainer; direkt nach (oder in) ihrem `::: exercise`.
:::

## Preise {.internal}        ← ganze Folie bzw. ganzes Kapitel (#) samt Notizen
```

- Nie `{.internal}` an das erste `#` (Titelfolie) und keine `#`/`##` in die drei Container.
- `{.internal}` ersetzt keinen anderen Marker: ein `{.build}`-Block, der intern ist, kommt mit
  seinem `{.build}` in ein `::: internal`.
- `./run.sh generate … --audience kunde|intern|trainer|alle`; Dateien `<name>.pptx`,
  `<name>-intern.pptx`, `<name>-trainer.pptx`. Interne Fassungen bekommen von selbst die
  Kennzeichnung `intern`. Der Hinweis `audience-omitted` nennt, wie viel weggelassen wurde — er
  ist erwartet und kein Fehler. Vor der Übergabe an den Kunden die Kundenfassung ansehen.

## Schulungs-Zeitplan

Bei Schulungen (und wenn der Anwender eine Länge nennt) **jeder `##`-Folie oder jedem Kapitel
eine Dauer geben** und `beginn:`/`laenge:` setzen:

```markdown
---
beginn: 09:00
laenge: 4h
---
# Titel

## Agenda {.agenda dauer=5}       ← Agenda zeigt „09:05 Kapitel" und die Pausen

# Kapitel {dauer=45}              ← Folien darin ohne dauer teilen sich den Rest

## Folie {dauer=10}               ← Minuten: 5 · 90 · 4h · 1h30 (ohne Anführungszeichen)

## Pause {.break dauer=15}        ← Pausenfolie „Pause · 15 min", KEIN Inhalt darunter

# Danke {.closing}                ← keine dauer; was danach kommt (auch Backup), ist nicht geplant
```

- Die Summe muss `laenge:` treffen, sonst Hinweis `schedule-length`; Folien ohne Angabe zählen
  2 Minuten (`schedule-missing`); `check` meldet `schedule-estimate`, wenn die Sprechzeit mehr
  als die Hälfte von „2 Minuten je Folie plus Notizen" abweicht — dann Dauern oder Folienzahl
  prüfen.
- `.break` nur an `##`, immer mit `dauer`, nie hinter `{.closing}` oder im Backup (dort auch
  keine `dauer` — Fehler); Pausen zählen zu den höchstens acht Agendapunkten.
- Die Trainerfassung (`--audience trainer`) schreibt „Geplant: 09:20–09:25 (5 min)" als erste
  Notizenzeile; `./run.sh schedule <praesentation.md>` erzeugt `<name>-zeitplan.docx` mit der
  Zeitplantabelle (`--markdown` zeigt sie als Markdown zum Prüfen).

## Teilnehmerhandout

`./run.sh handout documents/<thema>/<name>-praesentation.md` schreibt
`<name>-praesentation-handout.docx` (Word, Deckblatt, Zeitplan, je Folie Bild und Linien für
Notizen; `--layout 2|3|6` Folien je Seite, Standard 3). Für die Teilnehmer ist das die
Kundenfassung — ohne `--audience` also nichts Internes, keine Lösungen, kein Backup.

- **Zur Kontrolle der Sprechernotizen:** `./run.sh handout <praesentation.md> --audience trainer
  --markdown` und in `<name>-praesentation-handout-trainer.md` prüfen, dass **jede** Folie
  Notizen hat (wo keine sind, stehen Linien `***`). Fehlende `::: notes` ergänzen.
- Meldet `handout` „no slide pictures", fehlt die Vorschau (Grundregel 3); das Handout zeigt
  dann den Text der Folien. Dem Anwender sagen, dass `./run.sh setup` die Bilder ermöglicht.
- Das Handout nicht von Hand nachbauen und das `--markdown`-Ergebnis nicht mit `generate`
  erzeugen (dort stünden Bild und Notizen untereinander, die Beschriftungen nummeriert).

## Aus Python statt per Befehl

```python
from pta_documents.errors import DocumentConversionError
from pta_documents.generation.docx.generator import (
    DocxGenerator,
)  # bzw. pptx.generator.PptxGenerator
from pta_documents.markdown import DocumentResource, MarkdownDocument, content_type_of

document = MarkdownDocument(
    markdown, [DocumentResource("images/a.jpg", content_type_of("a.jpg"), data)]
)
try:
    with open("documents/x/x-bericht.docx", "wb") as out:
        result = DocxGenerator().generate(document, out)
    print(result)  # Hinweise als Liste "- line 12: …", sonst "No notes."
except DocumentConversionError as error:
    print(error.reason)  # was im Markdown zu ändern ist
```

Mit `.venv/bin/python` ausführen. Optionen (`DocxOptions`, `PptxOptions`) gibt es auch, das Front
Matter hat aber Vorrang — im Zweifel nur Front Matter verwenden.

## Vorhandene Dateien lesen

Um eine Word- oder PowerPoint-Datei des Anwenders zu verstehen oder zu überarbeiten:

```python
from pta_documents.conversions import convert  # erkennt Word/PowerPoint/PDF am Inhalt

with open("documents/x/alt.docx", "rb") as datei:
    document = convert(datei, "alt.docx")
document.text  # Markdown
document.resources  # Bilder: .path (images/image1.png), .content (bytes)
```

Alte Binärformate (`.doc`, `.xls`, `.ppt`, `.msg`), RTF und Excel lehnt `convert` mit einer
Meldung ab (`DocumentConversionError`): den Anwender bitten, die Datei als `.docx` bzw. `.pptx`
zu speichern. Markdown- und Textdateien direkt lesen, nicht konvertieren.

PDFs liest `convert` nur aus der Textschicht (gescannte Seiten bleiben leer): je Seite
`## Page n`, Überschriften alle als `###`, Kopf- und Fußzeilen und das Logo fallen weg,
Tabellen mit Linien werden Pipe-Tabellen. Gliederungsebenen, Fett, Links und Beschriftungen
kommen nicht zurück — vor dem Neu-Erzeugen die Überschriften (`#`/`##`) neu setzen und die
`## Page n`-Zeilen entfernen.

Sprechernotizen einer Folie kommen als `::: notes` … `:::` nach ihrem Inhalt
(`ConversionOptions(notes=False)` lässt sie weg). Das Ergebnis ist ein Lesestand, kein verlustfreies Abbild: Folien verlieren Ebenen und
Formatierung, Word verliert u. a. Durchstreichung und Fußnoten. Vor dem Neu-Erzeugen das Markdown
nach den Regeln oben aufbereiten (Front Matter, `#`/`##`-Gliederung) und die Bilder nach
`images/` schreiben.

## Checkliste vor der Übergabe

- [ ] `./run.sh check documents/<thema> --strict` endet mit Code 0 (oder verbleibende Hinweise
      sind begründet und dem Anwender genannt).
- [ ] `./run.sh generate documents/<thema>` läuft ohne `ERROR` und möglichst ohne Hinweise
      (`--strict` endet dann mit Code 0); verbleibende Hinweise dem Anwender nennen.
- [ ] Word: `titel` gesetzt (bei Deckblatt-Vorlagen), Kapitel mit `#`, keine Handnummern.
- [ ] Präsentation: kein Inhalt unter Kapitel- und Abschluss-`#`, keine „(Forts.)"-Folien, die
      nicht gewollt sind.
- [ ] Präsentation angesehen, ohne PowerPoint zu haben: `./run.sh preview documents/<thema>`
      und die Bilder in `vorschau/<name>/` geprüft (Grundregel 3). Ein HTML-Deck
      (`generate … --html`) und den Ordner `vorschau/` nicht als Ergebnis ausliefern, sie
      sind nur Vorschau (Weitergabe nur auf Wunsch des Anwenders).
- [ ] Preise, interne Bemerkungen und Lösungen stehen in `::: internal`/`{.internal}` bzw.
      `::: solution`; was an den Kunden geht, ist die Fassung `kunde` (Datei ohne `-intern`/
      `-trainer`).
- [ ] Schulung: `./run.sh handout … --audience trainer --markdown` zeigt zu jeder Folie
      Notizen; das Handout für die Teilnehmer ist `…-handout.docx` (ohne `-trainer`).
- [ ] Fremde Bilder: Lizenz und Urheber genannt, `QUELLEN.md` geschrieben.
- [ ] Dem Anwender die erzeugten Dateien nennen und sagen, dass Word beim Öffnen eines
      Inhaltsverzeichnisses fragt, ob Felder aktualisiert werden sollen („Ja").
