# T01-S01 Python-Projektgerüst

> Status: in Bearbeitung (port-1)
> Epic: T01 (technisch)
> Milestone: [M01 PTA-Dokumente aus Markdown](../../50-entwurf/M01-pta-dokumente-aus-markdown.md)

## Zusammenfassung

Das Repo bekommt das Gerüst eines Python-3-Pakets — Paketstruktur, Abhängigkeiten, Tests,
Linting, Launcher — und die Python-Konventionen in `ai/Standards.md`, auf denen alle weiteren
Stories aufbauen.

## Kontext

Der Projektkatalog `projekt-init` hat keine Python-Komponente; das Repo wurde nur mit `core` und
`spec-workflow` angelegt. Die .NET-Konventionen von DocLibs (`src/*.slnx`, zentrale Paketversionen,
Geschwister-Testprojekte, `run.ps1`/`run.sh`, Werkzeuge als Single-File-Apps) werden hier
sinngemäß auf Python übertragen. Siehe
[Portierungsanalyse](../../10-analysen/2026-11-06%20portierung-doclibs-python.md).

## Vorgeschlagener Ansatz

1. **venv + pip** (Entscheidung 2026-11-06, uv ist nicht vorhanden): `pyproject.toml` im
   Repo-Root mit Build-Backend **hatchling**, virtuelle Umgebung in `.venv/` über
   `python3 -m venv`, Installation mit `pip install -e '.[dev]'`; die Launcher richten die
   Umgebung bei Bedarf selbst ein. Mindestversion **Python 3.12**.
2. Ein Distributionspaket `pta-documents`, Importname `pta_documents`, im `src/`-Layout:

   ```
   src/pta_documents/
     __init__.py
     errors.py                 # DocumentConversionError (Reason, Format)
     markdown/                 # MarkdownDocument, Ressourcen, Hilfen, Front Matter
     conversions/              # pdf, docx, pptx -> Markdown
     design/                   # PTA-Designmodell + eingebettete Vorlagen (E01)
     generation/
       common/                 # Parser, Folien-Syntax, Drawing, SVG, Authoring Guides
       docx/  pptx/  pdf/
       diagrams/  charts/
     svg/                      # SVG -> PNG
   tests/                      # spiegelt src/pta_documents/, mit samples/ je Bereich
   ```

   Optionale Abhängigkeiten als Extras (`[pdf]`, `[diagrams]`, `[svg]`), damit der Kern
   (DOCX/PPTX) schlank bleibt. Es wird **nichts veröffentlicht**: kein Feed, keine Tags als
   Versionen; das Paket wird aus dem Repo heraus verwendet (als Pfad-
   Abhängigkeit, `pip install -e <pfad>`).
3. **pytest** für Tests, **ruff** für Linting und Formatierung, **pyright** (strict) für Typen;
   vollständige Typannotationen, `py.typed`.
4. `run.sh` / `run.ps1` mit den Verben `setup`, `test`, `lint`, `format`, `typecheck`, `build`
   (beide Launcher im Gleichschritt, ohne Argumente listen sie die Verben).
5. `.gitignore` um `.venv/`, `__pycache__/`, `dist/`, `.pytest_cache/`, `.ruff_cache/` ergänzen.
6. `ai/Standards.md`: Abschnitte *Werkzeuge* und *Python-Konventionen* ergänzen (Bibliotheken
   halten keinen Laufzeitzustand, Stream rein/Stream raus, englischer Code, Tests neben dem Code
   als Spiegelbaum in `tests/`, Beispieldateien in `tests/**/samples/` und als binär markiert,
   `PTA_DOCUMENTS_UPDATE_EXPECTED=1` zum Erneuern der Erwartungsdateien). Die Abweichung
   „kein Katalogbaustein für Python" in die Abweichungstabelle.
7. `ai/Gedächtnis.md`: Überblick mit Stack und Paketstruktur.

## Akzeptanzkriterien

- [ ] `./run.sh setup` richtet `.venv/` ein; `./run.sh test` läuft grün (ein Rauchtest).
- [ ] `./run.sh lint` und `./run.sh typecheck` laufen fehlerfrei.
- [ ] `./run.sh build` erzeugt ein Wheel, das die PTA-Vorlagen als Paketdaten enthält (Prüfung, dass
      das Paket vollständig ist — veröffentlicht wird es nicht).
- [ ] `ai/Standards.md` beschreibt die Python-Konventionen in sich geschlossen.

## Offene Fragen

1. Mindestversion Python 3.12 — oder gibt es bei der PTA ältere Zielumgebungen (z. B. 3.10)?

> (2026-11-06) Python 3.12.

2. Ein Distributionspaket mit Extras — oder, wie DocLibs, mehrere getrennte Pakete?

> (2026-11-06) Ein Distributionspaket mit Extras.

3. Wie wird verteilt: internes Paket-Repository der PTA (welches?), Installation aus Git, oder
   gar nicht (nur Quellcode)?

> (2026-11-06) Gar nicht veröffentlichen — nur Quellcode im Repo.

4. Wohin kommt das Git-Remote dieses Repos, und gibt es dort CI (GitHub Actions, Azure DevOps,
   Forgejo Actions)?

> (2026-11-06) Vorerst kein Remote und kein CI; kommt später.

5. uv ist auf dieser Maschine nicht installiert — uv installieren oder ohne uv arbeiten?

> (2026-11-06) Ohne uv: venv + pip.

## Notizen

