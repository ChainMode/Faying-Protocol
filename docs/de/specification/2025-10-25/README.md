---
title: Faying Protocol/1.0 — Protokollspezifikation (Entwurf) Inhaltsverzeichnis
version: Faying Protocol/1.0
status: Final
editors:
  - Faying Protocol Committee
date: 2025-10-25
language: de
replaces: -
---

# Faying Protocol/1.0 Protokollspezifikation

Dies ist die deutsche offizielle Spezifikation von Faying Protocol/1.0 (Final, veröffentlicht am 2025-10-25). Der Protokolltext ist nach Kapiteln in 11 Dateien aufgeteilt, mit zweistelliger Kapitelnummerierung und Dateinamen, die den Kapitelnamen tragen; die Terminologie-Kurzreferenz, die Parameterbudgets sowie die Materialien zum Entstehungsprozess des Protokolls sind als Anhänge eingebunden, damit Open-Source-Beteiligte sowohl das Protokoll selbst verstehen als auch nachvollziehen können, wie es Schritt für Schritt festgelegt wurde.

Die englische Spezifikation liegt unter [`../../../en/specification/2025-10-25/`](../../../en/specification/2025-10-25/) und hat eine **Einzeldatei-Struktur** (der Protokolltext ist vollständig in die eine Datei `Faying-Protocol-1.0.md` eingebettet, mit §1–§11 und den Anhängen A/B); die Entsprechung zur deutschen Fassung ist eine Entsprechung auf **Abschnittsanker-Ebene**, nicht datei-für-datei. Bei Abweichungen ist die maßgebliche Fassung ausschlaggebend.

## Wie man liest

Wenn du zum ersten Mal damit in Berührung kommst, empfiehlt es sich, den Protokolltext einmal in der Reihenfolge §1 → §11 durchzulesen und dann die Anhänge zu konsultieren. Ist ein Begriff unklar, schlage in Anhang A nach; für konkrete Werte wie Timeouts/Budgets siehe Anhang B.

## Protokolltext (§1–§11)

| Kapitel | Datei | Inhalt |
| --- | --- | --- |
| §1 | [01-Ueberblick.md](./01-Ueberblick.md) | Protokollbenennung, Positionierung, Entwurfsziele, Unterschiede zu bestehenden Verfahren, Ein-Satz-Definition, Umfang und Nicht-Ziele |
| §2 | [02-Architektur.md](./02-Architektur.md) | Position im Protokoll-Stack, Entitätsbeziehungen, Stufenhierarchie, Kern-Interaktionssequenz, Entwurfsprinzipien |
| §3 | [03-Komponenten-und-Schnittstellen.md](./03-Komponenten-und-Schnittstellen.md) | Schnittstellen und Invarianten der sechs Kernkomponenten (MS / PC / AC / RR / LC / BBS) |
| §4 | [04-Datenmodelle.md](./04-Datenmodelle.md) | Menschenlesbare TypeScript-Ansicht, maßgebliche CDDL-Definition, Mandate-Zustandsmaschine |
| §5 | [05-Protokollnachrichten.md](./05-Protokollnachrichten.md) | Kodierungsregeln, Envelope-Struktur, sieben Nachrichtenklassen, Fehlercode-Tabelle |
| §6 | [06-Kryptografie.md](./06-Kryptografie.md) | Aushandlung der Algorithmen-Suite, Schlüsselableitung, Signaturformat |
| §7 | [07-Autorisierungsstufen.md](./07-Autorisierungsstufen.md) | Semantik der Stufen G0–G4, Auslösematrix, Herabstufungs-Monotonie, Endorsement-Unterstufen |
| §8 | [08-Lebenszyklus.md](./08-Lebenszyklus.md) | End-to-End-Lebenszyklus-Zustandsmaschine, Sequenz der Verantwortungszuordnung, Wiederverbindungs-Abgleich |
| §9 | [09-Sicherheitsbetrachtungen.md](./09-Sicherheitsbetrachtungen.md) | STRIDE, Anti-Replay / Anti-Hijack / Anti-Phishing, Trennungserkennung, Bedrohungskatalog des KI-Zeitalters |
| §10 | [10-Fehlerbehandlung.md](./10-Fehlerbehandlung.md) | Fehlerszenarien, Wiederherstellungspfade, Beobachtbarkeitsbedingungen, Default-Deny-Konvergenz |
| §11 | [11-Offene-Fragen.md](./11-Offene-Fragen.md) | Dem Protocol Committee zur Klärung überlassene offene Fragen Q1–Q14 |

## Anhänge

| Anhang | Datei | Inhalt |
| --- | --- | --- |
| A | [Anhang-A-Terminologie-Abgleich.md](./Anhang-A-Terminologie-Abgleich.md) | Terminologie-Kurzreferenz, maßgebliche Terminologiequelle für Implementierung und Review |
| B | [Anhang-B-Standard-Parameterbudgets.md](./Anhang-B-Standard-Parameterbudgets.md) | Standardparameter und Obergrenzen, Verschärfungsregeln nach grade |
| C | [Anhang-C-Aenderungsprotokoll.md](./Anhang-C-Aenderungsprotokoll.md) | Änderungsprotokoll vom ersten Federstrich des Entwurfs bis zur Endfassung und Strategie der Versionsnummerierung |

## Version

- Protokollname: Faying Protocol (die in frühen Entwürfen verwendete Abkürzung „FAP“ ist abgeschafft)
- Versionsnummer: Faying Protocol/1.0
- Status: Final (veröffentlicht am 2025-10-25)
- Editoren: Faying Protocol Committee

Die Versionsnummern in der Front Matter aller Protokolltext-Dateien stimmen hiermit überein. Dies ist das erste offizielle Release-Versionsstand 1.0, der als Ganzes aus dem Entwurfs-Arbeitsbereich in dieses Verzeichnis migriert wurde; die deutsche und die englische Fassung wurden in derselben Übergabe gemeinsam veröffentlicht, ohne einseitige Veröffentlichung. Nachfolgende Errata werden gemäß §1.7.4 von einer neuen Ausgabe mit eigenem Veröffentlichungsdatum getragen, ohne die Protokollversionsnummer zu ändern.
