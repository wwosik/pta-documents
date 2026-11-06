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
| `source-templates/` | Die offiziellen PTA-Vorlagen (`.dotx`, `.potx`, `.pptx`), unverändert — Quelle der Designstandards (siehe `spec/10-analysen/`) |

## Git

- **Fertige Arbeit wird standardmäßig committet.** Ist eine Aufgabe erledigt, wird sie
  committet. Was im Working Tree liegen bleibt, muss der Mensch selbst bemerken, durchsehen und
  von Hand committen.
- **Committet wird, was die Aufgabe berührt hat — sonst nichts.** Eine unabhängige Korrektur ist
  ein eigener Commit.
- Commit-Nachrichten sind in der Projektsprache, wie die übrige Prosa.
- Commit-Nachrichten niemals um einen `Co-Authored-By`-Trailer ergänzen.
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
| Nur Text und Code im Repo | `source-templates/` enthält binäre Office-Vorlagen, unverändert versioniert; `.gitattributes` markiert sie als binär | Sie sind die verbindliche Quelle des PTA-Designs; Änderungen daran kommen von PTA, nicht aus diesem Repo. |
