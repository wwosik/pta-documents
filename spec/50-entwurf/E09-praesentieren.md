# E09 Präsentieren: Sprechernotizen, Builds, Übergänge, Szenen

> Status: Entwurf

## Ziel

Was eine Präsentation beim Vortragen braucht und ein Dokument nicht: Sprechernotizen auf der
Notizenseite, Inhalte, die Klick für Klick erscheinen, Folienübergänge und — mit offenem Bedarf —
Szenen aus benannten Formen, die PowerPoint per Morph von Folie zu Folie bewegt.

## Motivation

Die Schwesterbibliothek vt-tools-libs hat das alles seit Plan 00016 („Builds, notes, transitions
and scenes", `~/mvv/vt-tools-libs/src/VtToolsLibs.DocumentGeneration.Pptx/Animations.cs`,
`NotesPages.cs`, `…DocumentGeneration/Scene.cs`, `SceneDrawing.cs`, `SlideTransition.cs`). Das
DocLibs-Release `2610.28.22`, von dem wir portieren, hatte es noch nicht — darum fehlt es in der
[Portierungsanalyse](../10-analysen/2026-11-06%20portierung-doclibs-python.md) und in E04. Eine KI,
die aus Markdown eine PTA-Präsentation schreibt, soll dem Vortragenden auch sagen können, was er
zu jeder Folie sagt.

## Scope

| Story | Inhalt | Status |
| ----- | ------ | ------ |
| [E09-S01](../60-prüfung/E09-S01-sprechernotizen.md) | `::: notes` → Notizenseite der Folie auf dem Notizenmaster der PTA-Vorlage; Rückweg im PPTX-Konverter | in Prüfung |
| [E09-S02](../60-prüfung/E09-S02-builds.md) | `{.build}` / `{.frag}` als Fade-Eingänge in PPTX; Front Matter für „alle Listen" | in Prüfung |
| [E09-S03](E09-S03-uebergaenge.md) | Folienübergänge per Front Matter und Heading-Attribut; Morph mit Fade-Rückfall | Entwurf |
| [E09-S04](E09-S04-szenen.md) | `::: scene`: benannte Formen auf dem Raster, Morph zwischen Szenenfolien | Entwurf |

## Bereichsweite Entscheidungen

- **Nur PTA-Layouts.** Nichts hier legt neue Layouts an; Notizen gehen auf den Notizenmaster, der
  in `slides-basis.pptx` und `slides-schulung.pptx` bereits liegt (`ppt/notesMasters/
  notesMaster1.xml`), Szenen auf `Nur Titel` innerhalb der Inhaltsfläche (E04-S03).
- **Ruhig.** Jeder Build ist ein Fade von einer halben Sekunde, wie PowerPoint ihn selbst
  schreibt; der Standardübergang ist `none`. Keine weiteren Effekte, keine Wahl der Effektart im
  Markdown — das entspricht der PTA-Regel „nur, was die Vorlage vorgibt".
- **Eine Quelle für alle Formate.** Word (E03) und PDF (E05) nehmen dieselbe Syntax an und lassen
  Notizen weg (PDF später mit `notizen: ja`, E05-S04), ignorieren Builds und Übergänge und zeichnen
  eine Szene als Standbild (PDF) bzw. lassen sie weg (Word). Nichts davon ist dort ein Fehler.
- **Syntax wie in vt-tools-libs** (`::: notes`, `{.build}`, `{.frag}`, `::: scene`), weil es
  Syntax ist; Front-Matter-Schlüssel deutsch (E02).
- **Konverter:** E07-S03 liest Notizenseiten als `::: notes` zurück; Animationen und Übergänge
  liest er nicht (sie sind kein Inhalt).

## Akzeptanz

Das Beispiel-Deck um Notizen, Builds, einen Übergang und eine Szene ergänzt öffnet in PowerPoint
ohne Reparatur, zeigt die Notizen in der Notizenansicht, baut Listen per Klick auf und ergibt beim
Rücklesen (E07-S03) die Notizen als `::: notes` wieder.

## Offene Fragen

1. Reichen Fade-Builds und die vier Übergänge, oder braucht die PTA weitere Effekte (Wischen von
   rechts, Erscheinen ohne Fade)? Vorschlag: nein — bewusst klein halten.

> (2026-11-07) Mehr Effekte: Richtungen für `push`/`wipe` (`push-left`, `wipe-up` …), weitere dezente PowerPoint-Übergänge (`split`, `cover`, `uncover`, `zoom`, `cut`), Build-Eingänge außer Fade (`{.build=appear}`, `fly`, `wipe`) sowie Ausgänge und Hervorhebungen (`{.exit}`, `{.emphasize}`). E09-S02 und E09-S03 sind um diese Punkte erweitert.
2. E09-S04 (Szenen) ist aufwendig (vt-tools-libs: ~500 Zeilen plus PPTX-Ausgabe). Gibt es dafür
   bei der PTA einen Anwendungsfall, oder reichen die Flow-Layouts aus E04-S03?

> (2026-11-07) Ja, Szenen werden gebraucht — zusammen mit Notizen, Builds und Übergängen.

## Notizen

- Reihenfolge: S01 zuerst (kleinster Eingriff, größter Nutzen für KI-geschriebene Decks), dann
  S02 und S03; S04 nur nach Antwort auf Frage 2.
