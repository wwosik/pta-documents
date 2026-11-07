# E13 Lange Berichte: Abkürzungen, Querverweise, Barrierefreiheit

> Status: Entwurf

## Ziel

Was ein Konzept oder Fachbericht von zwanzig Seiten braucht, aber eine Folie nicht: ein
Abkürzungsverzeichnis und ein Glossar aus dem Text, Querverweise mit Nummern („siehe Tabelle 3",
„Kapitel 2.1"), die Word selbst aktualisiert, und ein Dokument, das Screenreader und
Prüfwerkzeuge für Barrierefreiheit annehmen.

## Motivation

DocLibs und vt-tools-libs sind aus Präsentationen heraus entstanden; ihre PDFs sind kurze
Berichte ohne Verzeichnisse und Verweise. Die PTA schreibt für Kunden Fachkonzepte,
Architekturbeschreibungen und Prüfberichte, in denen Abkürzungen erklärt, Tabellen referenziert
und Kapitel verwiesen werden — heute von Hand, mit Nummern, die beim Umstellen falsch werden.
Öffentliche Auftraggeber verlangen nach BITV 2.0 / EN 301 549 zunehmend barrierefreie Dokumente;
wer das vom Generator bekommt, muss es nicht nachträglich in Word reparieren.

## Scope

| Story | Inhalt | Status |
| ----- | ------ | ------ |
| [E13-S01](E13-S01-abkuerzungen-und-glossar.md) | `*[PTA]: …`-Abkürzungen, Abkürzungsverzeichnis, Glossar aus `::: glossar` | Entwurf |
| [E13-S02](E13-S02-querverweise.md) | Anker auf Überschriften, Tabellen, Abbildungen; `REF`-Felder in Word, Links im PDF | Entwurf |
| [E13-S03](E13-S03-barrierefreiheit.md) | Alt-Texte, Dekorationsbilder, Dokumentsprache, Tabellenköpfe, Lesereihenfolge; PDF/UA prüfen | Entwurf |

## Bereichsweite Entscheidungen

- **Word rechnet, nicht der Generator:** Nummern in Querverweisen und Verzeichnissen sind
  Word-Felder (`REF`, `SEQ`, `TOC`), wie heute schon Beschriftungen und Inhaltsverzeichnis
  (E03-S02). Der Generator schreibt den aktuellen Wert als Feldergebnis mit, damit das Dokument
  auch vor dem Aktualisieren richtig aussieht; im PDF (E05) berechnet die Layout-Engine die
  Nummern selbst.
- **Alle drei Stories gelten für Word und PDF**; PowerPoint nimmt, was ohne Nummern geht
  (Abkürzungen ausgeschrieben, Verweise als Text, Alt-Texte).
- Keine neue Syntax, wo Markdown eine hat: Abkürzungen nach dem verbreiteten `*[ABK]: Text`,
  Anker nach `{#id}`, Verweise als normale Links `[…](#id)`.
- Fehlende Verweisziele, doppelte Anker und Bilder ohne Alt-Text sind **Fehler**, keine Hinweise
  — bis auf Bilder, die als Dekoration markiert sind (E13-S03).

## Akzeptanz

`samples/funktionen/funktionen-bericht.md` erweitert um Abkürzungen, Glossar und Querverweise
ergibt ein Word-Dokument, dessen Felder nach *Alles aktualisieren* unverändert bleiben, und ein
PDF (nach E05), das veraPDF als PDF/A-2b und — soweit E13-S03 es erreicht — PDF/UA-1 bestätigt.

## Offene Fragen

1. Haben PTA-Konzepte eine feste Gliederung der Verzeichnisse (Inhalt, Abbildungen, Tabellen,
   Abkürzungen — in welcher Reihenfolge, vor oder nach dem Text)? Vorschlag: Inhalt vorn,
   Abkürzungen und Glossar am Ende, Abbildungs- und Tabellenverzeichnis nur auf Wunsch
   (`abbildungsverzeichnis: ja`, `tabellenverzeichnis: ja`, als `TOC \c`-Felder — kleine
   Ergänzung zu E13-S02).

>

2. Verlangen Kunden der PTA tatsächlich PDF/UA oder BITV-Konformität? Davon hängt ab, wie weit
   E13-S03 im PDF gehen muss.

>

## Notizen
