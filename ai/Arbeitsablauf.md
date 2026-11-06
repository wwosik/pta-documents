# Wie in diesem Repo gearbeitet wird

Idee → Epic/Story → Iteration → Claim → Umsetzung → Verifikation → Ablage. Jeden Übergang stößt
der Mensch an; nichts rückt von allein weiter.

## 1. Ideen — `spec/00-ideensammlung/`

Vom Menschen geschrieben, eine Datei je Idee oder Thema, frei formuliert. Eine Idee aus einem
externen Ticketsystem behält ihre Referenz, damit der Weg zurück nie verloren geht.

## 2. Plan — `spec/50-entwurf/`

Aus einer akzeptierten Idee wird ein Feature-Epic mit Stories oder eine technische Story, wenn
sie keinem Feature-Bereich angehört. Geschrieben wird in der Projektsprache; als Vorlage für
Stories dient [../spec/_vorlage.md](../spec/_vorlage.md).

- **Feature-Epic:** `E01-kurztitel.md`. Für jeden Produkt- oder Fachbereich die nächste freie
  `E`-Nummer verwenden. Das Epic enthält auf hoher Ebene Ziel, Motivation, eine Scope-Tabelle mit
  Stories und deren Status, bereichsweite Entscheidungen, Akzeptanz und offene Fragen. Bereichs-
  übergreifende Entscheidungen gehören hierher, nicht in eine einzelne Story.
- **Feature-Story:** `E01-S01-kurztitel.md`. Die Storynummer zählt innerhalb ihres Epics; die
  nächste freie Nummer verwenden. Jede Story gehört zu genau einem Feature-Epic oder technischen
  Container. Im Kopf steht das Epic: `> Epic: [E01 Titel](E01-kurztitel.md)`.
- **Technische Story:** `T01-S01-kurztitel.md`, mit `> Epic: T01 (technisch)`. `T01` ist ein
  Container, keine Datei und kein Feature-Epic. Nach `Tnn-S99` beginnt der nächste Container;
  jeder enthält höchstens 99 Stories. Dient technische Arbeit einem Feature-Epic, gehört sie in
  dieses Epic.
- **Meilenstein:** `M01-kurztitel.md`. Er gruppiert Stories aus mehreren Epics, die gemeinsam
  ausgeliefert werden. Die Stories bleiben in ihrem Epic und nennen den Meilenstein im Kopf:
  `> Milestone: [M01 Titel](M01-kurztitel.md)`.

Eine bekannte externe Referenz `W-nnnn` steht nach der Story-ID und vor dem Slug.
IDs bleiben beim Verschieben stabil und sind in allen Projektsprachen gleich.

Jede Story endet mit **Offene Fragen** (jede Frage mit einer leeren Zitatzeile als Antwortplatz)
und **Notizen** (freier Raum für Anmerkungen, die keine Antworten auf die Fragen sind).

## 3. Iterieren

Der Mensch trägt Antworten ein; die Datei wird überarbeitet, bis der Mensch den Plan akzeptiert.
Nicht akzeptierte Pläne werden nicht umgesetzt.

## 4. Eine Story claimen

Vor der Umsetzung wird die Story geclaimt — siehe [Eine Story claimen](#eine-story-claimen).
Epics und Meilensteine sind Planungsdokumente; geclaimt werden Stories.

## 5. Umsetzen

Sobald der Plan akzeptiert ist, die Story von dieser Sitzung geclaimt wurde und die Umsetzung
angefragt ist:

1. Die Story umsetzen, möglichst in einem Worktree auf Basis des Claim-Commits.
2. Die Story im Arbeitsbranch von `spec/55-in-arbeit/<agent-id>/` nach `spec/60-prüfung/`
   **verschieben** — gleicher Dateiname. Leeren Agent-Ordner entfernen und Links in Story,
   Epic und Meilenstein korrigieren.
3. Den Status in der Epic-Scope-Tabelle auf `in Prüfung` setzen und **Implementierungs-
   notizen** anhängen: Entscheidungen, Kompromisse, Abweichungen, Warnungen, Prüfpunkte und
   offene Punkte.
4. Umsetzung und verschobene Story zusammen committen, gemäß den Git-Regeln des Repos.
5. Nach einer erledigten Aufgabe rebasen und pushen; Konflikte auflösen und nachfragen, wenn
   die richtige Lösung nicht offensichtlich ist.
6. Im Chat nur melden, dass die Aufgabe erledigt ist. **Keine Zusammenfassung** — die
   Einzelheiten stehen in der Datei.

## 6. Verifizieren

Der Mensch verifiziert. Nach Freigabe die Story nach
`spec/70-fertig/<epic-id>-<epic-slug>/` **verschieben** und den Status auf `abgeschlossen` setzen.
Alle Stories eines Feature-Epics liegen dort zusammen. Wenn alle Stories fertig sind, kommt auch
die Epic-Datei dorthin. Technische Stories kommen nach `T01-technisch/` (oder in den passenden
`T`-Container).

## Eine Story claimen

Mehrere Agents können in getrennten Worktrees arbeiten. Ein Claim zeigt allen anderen, dass eine
Story und der dazugehörige Code bereits übernommen sind.

**Agent-ID.** Für alle Claims einer Sitzung eine kurze, kleingeschriebene kebab-case-ID nutzen
(z. B. `nebel-2`). Fehlt der Sitzung noch eine ID, vor dem ersten Claim den Menschen um eine
bitten. Eine neue Sitzung fragt erneut; der Mensch kann eine ID zur Fortsetzung wiederverwenden.

**Vor jeder Implementierungsarbeit claimen:**

1. Auf `main` im Haupt-Checkout arbeiten, nicht in einem Worktree, und sicherstellen, dass die
   betroffenen Dateien keine uncommitteten Änderungen haben. Prüfen, ob die Story noch in
   `spec/50-entwurf/` liegt. Liegt sie bereits in `spec/55-in-arbeit/<andere-id>/`, anhalten und
   den Menschen fragen; die Story nicht übernehmen.
2. Die Story mit gleichem Dateinamen nach `spec/55-in-arbeit/<agent-id>/` verschieben. Im Kopf
  `> Status: in Bearbeitung (<agent-id>)` setzen.
3. Durch das Verschieben ungültige Links korrigieren. Die Story liegt eine Ebene tiefer, daher
  ändern sich ihre relativen Links; Links in Epic-Scope-Tabelle und Meilenstein ebenfalls
  aktualisieren. Den Story-Status im Epic auf `in Bearbeitung (<agent-id>)` setzen.
4. Nur den Claim auf `main` committen, z. B. `Übernimm E01-S01 für <agent-id>`. Keine anderen
   Änderungen einbeziehen.
5. Die Umsetzung beginnen, möglichst in einem Worktree auf Basis dieses Claim-Commits.

**Während die Story geclaimt ist:**

- Eine Story eines anderen Agents weder bearbeiten noch verschieben oder umsetzen; auch den
  betroffenen Code dem Owner überlassen. Bei nötigen Änderungen den Menschen fragen.
- Der Claim endet, wenn die Story im Branch des Agents nach `spec/60-prüfung/` verschoben wurde
  und dieser Branch `main` erreicht.
- Zum Freigeben ohne Umsetzung die Story zurück nach `spec/50-entwurf/` verschieben, Status und
  Links wiederherstellen und nur diese Freigabe auf `main` committen, z. B.
  `Gib E01-S01 frei für <agent-id>`.

## Epics, technische Container und Meilensteine

- **Feature-Epics `E01`, `E02`, ...** gruppieren Stories eines Produkt- oder Fachbereichs. Die
  Epic-Datei liegt in `spec/50-entwurf/`; wenn alle Stories abgeschlossen sind, zieht sie mit
  ihnen nach `spec/70-fertig/<epic-id>-<slug>/`. Die nächste freie `E`-Nummer verwenden.
- **Technische Container `T01`, `T02`, ...** gruppieren Stories ohne Feature-Epic, etwa Hosting,
  Storage, Deployment, Authentifizierung oder Tooling. Sie haben keine Datei und keine eigenen
  Anforderungen; Entscheidungen stehen in den Stories. Höchstens 99 Stories pro Container;
  nach `T01-S99` folgt `T02-S01`.
- **Meilensteine `M01`, `M02`, ...** gruppieren Stories aus mehreren Epics für eine gemeinsame
  Lieferung. Ihre Datei liegt in `spec/50-entwurf/`; die Stories bleiben ihrem Epic zugeordnet.
- Stories per ID referenzieren (`E02-S03`, `E02-S03 §2.4`) und Epics per ID (`E04`).

## Analysen — `spec/10-analysen/`

Angefragte Analysen kommen in eine Datei `spec/10-analysen/JJJJ-MM-TT <slug>.md`, niemals in
den Chat. Im Chat nur mitteilen, dass sie fertig ist und wo sie liegt. Analysen stellen fest,
was ist; Pläne schlagen vor, was sich ändern soll.

## Feste Regeln

- Nie direkt aus einer Idee umsetzen; mit dem Menschen iterieren und zuerst die Story claimen.
- Niemals eine von einem anderen Agent geclaimte Story oder deren Code anfassen.
- Fertige Arbeit committen und nach Abschluss rebasen und pushen — siehe Git in
  [Standards.md](Standards.md).
- Temporäre Dateien und Scratch-Dateien gehören ins `.tmp/` im Repo-Root, nie ins System-Temp
  oder nach AppData.
- Das gesamte Projektgedächtnis bleibt gemeinsam in `ai/`.

