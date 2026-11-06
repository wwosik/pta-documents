# Konventionen dieses Repos

Diese Datei ist in sich geschlossen: alles, was ein Agent braucht, steht hier — nicht hinter
einem Verweis auf ein anderes Repo oder ein lokales Laufwerk.

## Repository

- Die gesamte Anwendung liegt in **einem Git-Repo**.
- Das gesamte Projektgedächtnis ist **gemeinsam** in `ai/` — nie geräte-lokal.
- **Temporäre Dateien und Scratch-Dateien** gehören ins `.tmp/` im Repo-Root (git-ignoriert) —
  nie ins System-Temp, nie nach AppData.
- Programmdaten liegen im git-ignorierten `data/`.
- Logs rollen täglich ins git-ignorierte `logs/` im Repo-Root.
- `AGENTS.md` bleibt klein und verweist nach `ai/`; `CLAUDE.md` verweist ausschließlich auf
  `AGENTS.md`.

## Ordnerstruktur

| Pfad | Zweck |
| ---- | ----- |
| `ai/` | KI-Vorgaben und gemeinsames Projektgedächtnis |
| `docs/` | Dokumentation, wie das Programm tatsächlich funktioniert |
| `data/` | Programmdaten (git-ignoriert) |
| `logs/` | Täglich rollierende Logs (git-ignoriert) |
| `.tmp/` | Scratchpad (git-ignoriert) |
| `spec/` | Spezifikationen und der Aufgaben-Lebenszyklus (siehe [Arbeitsablauf.md](Arbeitsablauf.md)) |
| `src/pta_documents/` | Das Python-Paket (`src`-Layout) |
| `tests/` | Tests, Spiegelbaum von `src/pta_documents/`, Beispieldateien in `tests/**/samples/` |
| `tools/` | Werkzeuge des Repos, je eines in `tools/<name>/<name>.py`, gestartet über `run.sh <name>` |
| `samples/` | Beispielinhalte zum Ausprobieren der Generatoren, je Thema ein Ordner mit Markdown, `images/` und `QUELLEN.md` (Lizenzen); erzeugt mit `./run.sh generate-samples` nach `.tmp/samples/` |
| `source-templates/` | Die offiziellen PTA-Vorlagen (`.dotx`, `.potx`, `.pptx`), unverändert — Quelle der Designstandards (siehe `spec/10-analysen/`) |

## Werkzeuge

- **Python ≥ 3.12**, virtuelle Umgebung in `.venv/` (git-ignoriert), Abhängigkeiten in
  `pyproject.toml` (Build-Backend hatchling). Kein uv, kein Lockfile: `pip install -e '.[dev,pdf,svg]'`.
- **Launcher** `run.sh` und `run.ps1` — beide im Gleichschritt, ohne Argumente listen sie Verben
  und Werkzeuge:

  | Verb | Wirkung |
  | ---- | ------- |
  | `setup` | `.venv/` anlegen bzw. aktualisieren, Paket editierbar mit allen Extras installieren |
  | `test` | pytest (Argumente werden durchgereicht) |
  | `lint` | `ruff check` |
  | `format` | Importe sortieren und `ruff format` |
  | `typecheck` | pyright im Modus `strict` |
  | `build` | Wheel nach `dist/` (nur zur Prüfung, dass das Paket vollständig ist — es wird nichts veröffentlicht) |
  | `<werkzeug>` | `tools/<werkzeug>/<werkzeug>.py` in der `.venv` |

  Jedes andere Verb richtet `.venv/` bei Bedarf selbst ein.
- Vor jedem Commit laufen `test`, `lint` und `typecheck` grün.

## Python-Konventionen

- **Ein Distributionspaket** `pta-documents`, Importname `pta_documents`; optionale Teile als
  Extras (`pdf`, `svg`, `diagrams`). Der Kern (DOCX, PPTX, Konverter) braucht keine Extras.
- **Englischer Code:** Bezeichner, Kommentare, Docstrings, Fehlermeldungstexte der API sind
  englisch; was ein Schreiber von Markdown liest (Front-Matter-Schlüssel und -Werte, erzeugte
  Texte wie „Seite"/„Tabelle"), ist deutsch.
- **Bibliotheken halten keinen Laufzeitzustand.** Kein globaler veränderlicher Zustand, keine
  Caches, die das Ergebnis ändern; jeder Aufruf ist unabhängig.
- **Stream rein, Stream raus.** Öffentliche Funktionen nehmen `bytes`/`BinaryIO` bzw.
  `MarkdownDocument` und schreiben in einen übergebenen Stream; Dateizugriffe gibt es nur in
  Werkzeugen und Tests. Paketdaten werden über `importlib.resources` gelesen.
- **Ein Fehlertyp:** Fehler in einem Dokument sind `DocumentConversionError(format, reason)`;
  `reason` sagt dem Schreiber, was er ändern muss (mit Liste der gültigen Werte, wo es eine gibt).
  Programmierfehler bleiben gewöhnliche Python-Ausnahmen.
- **Vollständige Typannotationen**, `py.typed`; pyright `strict`. Nur unbekannte Typen *aus*
  python-docx, python-pptx und markdown-it werden hingenommen (Einstellungen in
  `pyproject.toml`).
- **Tests** spiegeln `src/pta_documents/` in `tests/`. Beispieldateien liegen in
  `tests/**/samples/`; Erwartungsdateien heißen `*.expected.md` und werden mit
  `PTA_DOCUMENTS_UPDATE_EXPECTED=1 ./run.sh test` neu geschrieben — der Diff ist dann zu prüfen,
  bevor er committet wird. Erzeugte Dateien zum Ansehen schreiben Tests nach `.tmp/review/`.
- Formatierung und Importreihenfolge macht ruff (Zeilenlänge 100); keine Handformatierung
  dagegen.

## Git

- **Fertige Arbeit wird standardmäßig committet.** Ist eine Aufgabe erledigt, wird sie
  committet. Was im Working Tree liegen bleibt, muss der Mensch selbst bemerken, durchsehen und
  von Hand committen.
- **Committet wird, was die Aufgabe berührt hat — sonst nichts.** Eine unabhängige Korrektur ist
  ein eigener Commit.
- Commit-Nachrichten sind in der Projektsprache, wie die übrige Prosa.
- Commit-Nachrichten niemals um einen `Co-Authored-By`-Trailer ergänzen.
  Der versionierte Hook `.githooks/commit-msg` weist solche Commits ab; in jedem frischen Klon
  einmal `git config core.hooksPath .githooks` setzen.
- Autor und Committer aller Commits: `Wojciech Wosik <wojciech.wosik@pta.de>` — im Klon per
  `git config user.email wojciech.wosik@pta.de` setzen.
- **Niemals Secrets, Build-Ausgaben oder etwas committen, das `.gitignore` abdeckt.** Muss etwas
  Ignoriertes wirklich versioniert werden, ist das eine Frage an den Menschen und keine eigene
  Entscheidung.
- **Keinen kaputten Stand committen.** Schlägt der Build oder ein Test fehl, wird das gemeldet
  und angehalten — ein roter Commit kostet mehr, als er spart.
- Niemals Hooks überspringen (`--no-verify`) oder die Signatur umgehen. Ein fehlschlagender Hook
  ist ein Problem, das behoben und nicht umgangen wird.

### Nach einer größeren Aufgabe

Eine größere Aufgabe ist ein umgesetzter Plan, der nach `spec/60-prüfung/` verschoben wurde —
oder, ohne diesen Ablauf, jede in sich abgeschlossene Arbeit, um die der Mensch gebeten hat.
Nicht jeder Commit unterwegs.

1. **Rebase** auf den getrackten Upstream-Branch (`git pull --rebase`).
2. **Konflikte auflösen.** Ist die richtige Auflösung nicht offensichtlich, **anhalten und
   nachfragen** — nie raten, was jemand anderes gemeint hat.
3. **Pushen.**

`git pull --rebase` spielt die noch nicht gepushten Commits oben auf den Upstream, ein normaler
`git push` genügt danach. Werden Commits rebast, die **bereits** gepusht waren, wird Historie
umgeschrieben: der Push braucht dann `--force-with-lease` — in Ordnung auf einem Branch, auf den
nur du pushst, und eine Rückfrage wert auf jedem Branch, den noch jemand nutzt. Niemals ein
einfaches `--force`.

## Abweichungen

Wo dieses Repo von den obigen Konventionen abweicht — weil es älter ist als sie, oder weil etwas
Konkretes es erfordert hat. Was hier steht, ist Absicht: nicht ohne Rückfrage „reparieren".

| Konvention | Was dieses Repo stattdessen tut | Warum |
| ---------- | ------------------------------- | ----- |
| Projektgerüst aus dem Katalog `projekt-init` | Der Katalog hat keine Python-Komponente; Gerüst und Python-Konventionen stammen aus T01-S01 | Der Katalog kennt nur .NET-Projekte. |
| Nur Text und Code im Repo | `source-templates/` enthält binäre Office-Vorlagen, unverändert versioniert; `.gitattributes` markiert sie als binär | Sie sind die verbindliche Quelle des PTA-Designs; Änderungen daran kommen von PTA, nicht aus diesem Repo. |
