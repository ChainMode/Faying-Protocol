---
title: "Faying Protocol/1.0 — Anhang C Änderungsprotokoll"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: de
part: "Anhang C (Änderungsprotokoll)"
---

> Protokolltext-Navigation: [Inhaltsverzeichnis](./README.md) | vorheriges [Anhang B Standard-Parameterbudgets](./Anhang-B-Standard-Parameterbudgets.md)

## Anhang C Änderungsprotokoll

Dieses Protokoll hält fest, welche Änderungen der Protokolltext und die begleitenden Liefergegenstände am Entwurf von Faying Protocol/1.0 vom ersten Federstrich bis zur Endfassung erfahren haben. Formal folgt es den Gruppierungsgewohnheiten von [Keep a Changelog](https://keepachangelog.com) (Added / Changed / Deprecated / Removed / Security) und erläutert vorab, wie die Versionsnummer festgelegt wird.

> Ehrliche Anmerkung zur Herkunft: Der 1.0-Entwurf dieses Protokolls wurde in einem spec-getriebenen Prozess in einem Zug erstellt (Anforderungen → Entwurf → Aufgabenliste → Implementierung) und hat noch keine mehreren unabhängigen Sitzungen des Protocol Committee durchlaufen. Dieses Protokoll erfindet daher keine einzelnen Sitzungsbeschlüsse und exakten Daten, sondern hält wahrheitsgetreu nur fest, „was getan wurde, warum und welcher Aufgabe es entspricht“. Die unten zitierten Aufgabennummern (z. B. 1.6, 3.8, 5.6) entsprechen tatsächlichen Einträgen im Implementierungs-Aufgabenplan und erlauben, jede Änderung an ihre Entstehungsstelle zurückzuverfolgen. Geht es später in einen formellen Committee-Review-Prozess über, werden hier Einträge mit Datum und Beschlussnummer ergänzt.

## Wie die Versionsnummer festgelegt wird

Die **maßgeblichen Regeln der Protokollversionsnummerierung stehen in §1.7 Versionsverwaltung und Kompatibilität** des Protokolltexts (drei orthogonale Achsen: Protokollversion `MAJOR.MINOR` / Dokumentstatus / redaktionelle Ausgabe; Aushandlungs- und Kompatibilitätsregeln; Landeplätze der Versionsnummer und Hinweise für Implementierende). Dieser Anhang definiert das nicht erneut, sondern ergänzt nur zwei für das Änderungsprotokoll relevante Punkte:

- Dieses Protokoll klassifiziert jede Änderung nach den MAJOR-/MINOR-Kriterien aus §1.7.2: was die Interoperabilität bricht, geht in MAJOR; rückwärtskompatible Ergänzungen gehen in MINOR; rein textliche Errata werden nach §1.7.4 unter `Editorial` eingeordnet und ändern die Protokollnummer nicht.
- Aktuell ist `Faying Protocol/1.0`, die erste Basislinie, Status Final (veröffentlicht am 2025-10-25).

Bei der Benennung verwenden Prosa und Versionsnummer einheitlich `Faying Protocol/1.0`; die frühere Abkürzung `FAP` ist abgeschafft. Die Schema-Dateinamen `fap-1.0.cddl` / `fap-1.0.proto` behalten jedoch das alte Präfix bei, rein um die Dateinamen stabil zu halten und bestehende Verweise nicht zu brechen — dies ist beabsichtigt und keine Benennungs-Inkonsistenz (im Einklang mit §1.7.5 „Schema-Dateinamen ändern sich nicht über redaktionelle Ausgaben hinweg“).

## [Faying Protocol/1.0] — Final (2025-10-25)

Dies ist das erste offizielle Release von 1.0, das am 2025-10-25 als Ganzes aus dem Entwurfs-Arbeitsbereich in das offizielle Veröffentlichungsverzeichnis migriert und finalisiert wurde. Im Folgenden nach Änderungstyp gruppiert, jeder Eintrag mit der Aufgabennummer markiert, die ihn hervorgebracht hat.

### Added

Protokolltext (§1–§11 + Anhänge A/B):

- §1 Overview: Protokollbenennung, Positionierung, acht Entwurfsziele G1–G8, Ziele in Eins-zu-eins-Entsprechung zu den Requirements; §1.5.1 etabliert die Kernaussage „jedes bidirektionale Faying wird erst durch die ausdrückliche HP-Bestätigung wirksam“. (Aufgabe 1.2)
- §2 Architecture: vier Mermaid-Diagramme (Protokoll-Stack, Entitätsbeziehungen, Stufenhierarchie, Bootstrap+Heartbeat+Action-Sequenz einschließlich des IF-initiierten Phase-A0-Pfads) und sechs Entwurfsprinzipien. (Aufgabe 1.3)
- §3 Components and Interfaces: Schnittstellen und Invarianten der sechs Komponenten (MS / PC / AC / RR / LC / BBS). (Aufgabe 1.4)
- §4 Data Models: maßgebliche CDDL-Definition, menschenlesbare TypeScript-Ansicht, Mandate-Zustandsmaschine mit Disconnected-Zustand und Wiederverbindungs-Abgleich, endorsement-Teilstruktur. (Aufgabe 1.5)
- §5 Protocol Messages: sieben Nachrichtenklassen (BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE / REVOKE / FAYING_REQUEST / DISCLOSURE), einheitlicher Envelope, 14 Fehlercodes — darunter neu hinzugefügt 1010 `E_HUMAN_WITNESS_REQUIRED`, 1013 `E_ENDORSEMENT_INVALID`, 1014 `E_FAYING_REQUEST_NOT_CONFIRMED`. (Aufgabe 1.6)
- §6 Cryptography: Aushandlung der Algorithmen-Suite (einschließlich PQC-Verhandlungs-Bits), Schlüsselableitung, Signaturformat; das endorsement-Feld geht in die Signatureingabe ein. (Aufgabe 1.7)
- §7 Authorization Grades: Semantik der fünf Stufen G0–G4, Auslösematrix, Herabstufungs-Monotonie sowie die über G1–G4 gelegten Endorsement-Grades-Unterstufen aus §7.5. (Aufgabe 1.8)
- §8 Lifecycle: Sieben-Zustände-Lebenszyklus (einschließlich Disconnected), Sequenz der Verantwortungszuordnung, Wiederverbindungs-Abgleichstransaktion aus §8.4. (Aufgabe 1.9)
- §9 Security Considerations: STRIDE, Anti-Replay / Anti-Hijack / Anti-Phishing, Trennungserkennung, Disconnection-Handling-Matrix sowie der adversariale Bedrohungskatalog des KI-Zeitalters T1–T7 aus §9.10. (Aufgabe 1.10)
- §10 Error Handling, §11 Open Questions, Anhänge A/B: Fehlerszenarien und Wiederherstellungspfade, offene Fragen Q1–Q14, Terminologie-Abgleich, Standard-Parameterbudgets. (Aufgabe 1.11)
- Vollständige Übersetzung der englischen Spezifikation. (Aufgabe 1.12)

Begleitende Liefergegenstände:

- Schema: `schemas/fap-1.0.cddl` (maßgeblich), `schemas/types.ts` (menschenlesbare TypeScript-Ansicht, Not Normative), `schemas/fap-1.0.proto` (alternative gRPC-Bindung, Not Normative). (Aufgaben 2.1–2.3)
- Testvektoren `vectors/`: decken insgesamt 11 Klassen ab — BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE / REVOKE, Fehlercodes, Kodierungsäquivalenz, Endorsement, FAYING_REQUEST, DISCLOSURE, Disconnection. (Aufgaben 3.1–3.11)
- Eigenschaftsbasierte Tests `pbt/`: decken die Hauptproperties P1–P15 ab, zuzüglich der drei Familien P16 (Endorsed_Mandate), P17 (Disconnection), P18 (AI-Era). (Aufgaben 4.1–4.34)
- Interoperabilitätskonformitäts-Suite `conformance/`: fünfdimensionale Matrix Kodierung × Signaturalgorithmus × Hash × Kanal × Implementierungssprache, mit zwei Referenzimplementierungen in TypeScript und Rust. (Aufgaben 5.1–5.6)
- Sicherheits-Angriffssimulation `conformance/attacks/`: Replay, Hijack, Phishing, Trennungserkennung sowie die Simulationen T1/T3/T4/T5/T6. (Aufgaben 6.1–6.10)

### Changed

- Die Protokollbenennung wurde vom frühen Entwurf „Faying Auth Protocol (FAP)“ auf **Faying Protocol** geändert, die Versionsnummer wird als `Faying Protocol/1.0` geschrieben. (entspricht §11 Q10, geklärt)
- Die Faying-Initiierung wurde von einseitig (nur HP kann initiieren) auf bidirektional erweitert (HP-initiiert + IF-initiiert), doch die Wirksamkeitsbedingung konvergiert einheitlich auf die eine Bedingung „ausdrückliche HP-Bestätigung“. (Aufgaben 1.6, 3.9)
- Die Trennung wurde in die zwei Semantiken „tatsächliche Trennung“ und „wahrgenommene Trennung“ aufgeteilt; die Protokollentscheidung zieht ausschließlich die wahrgenommene Trennung heran und trifft für das Inkonsistenzfenster eine pessimistische Annahme. (Aufgaben 1.10, 3.11)
- Die Signatureingabe wurde auf `H(Deterministic-CBOR(Envelope_without_signature))` vereinheitlicht; das CBOR-Primärformat und das JSON-Fallback sind unter diesem Maßstab äquivalent interoperabel. (Aufgaben 3.7, 5.2)

### Deprecated

- Die alten Benennungen `FAP` / `FAP/1.0` / `Faying Auth Protocol` sowie die alten Endpunktformen wie `application/fap+json`, `POST /fap/v1/...` sind sämtlich abgeschafft. Die neue Schreibweise verwendet `application/faying-protocol+json` und `POST /faying-protocol/v1/{verb}`. Die Schema-Dateinamen sind die einzige Ausnahme, die das alte Präfix beibehält (siehe oben „Wie die Versionsnummer festgelegt wird“).

### Removed

- Keine. 1.0 ist die erste Basislinie; es gibt keine zu entfernenden bestehenden Felder oder Nachrichten.

### Security

- Neu hinzugefügte Bedingungen auf Protokollebene gegen adversariale Bedrohungen des KI-Zeitalters: T1 Social Engineering, T2 Black-Box-Operation, T3 Selective Disclosure, T4 Attention Drift, T5 Cultivated Trust Manipulation, T6 Audit Flooding, T7 erweiterbarer Slot, jeweils entsprechend Property P18.1–P18.7 und Requirement 13.1–13.7. (Aufgaben 1.10, 4.28–4.34, 6.6–6.10)
- Manipulationsschutz-Bedingung der bezeugten Autorisierung: Das endorsement geht in die Signatureingabe ein; das Ändern eines beliebigen Teilfelds lässt die Mandate-Signaturverifikation scheitern (`E_ATTESTATION_INVALID` / `E_ENDORSEMENT_INVALID`). (Aufgaben 1.5, 3.8, 4.17–4.21)
- Symmetrischer Widerruf und Widerruf-Irreversibilität: Die Erreichbarkeit des Widerrufspfads ist nicht geringer als die des Etablierungspfads, `Revoked` ist ein absorbierender Zustand, der Kaskaden-Widerruf ist standardmäßig aktiviert. (Aufgaben 3.5, 4.5, 4.11, 4.15)

## Wie es künftig gepflegt wird

- Nach Eintritt in den formellen Review wird hier je Committee-Beschluss eine Zeile ergänzt, die das Datum, die betroffenen Abschnitte und die ausgelöste Aufgabennummer angibt, und in der zugehörigen Keep-a-Changelog-Gruppe oben wird ein menschenlesbarer Eintrag ergänzt.
- Versionsnummer: gemäß §1.7 ausführen — rückwärtskompatible Ergänzungen gehen über MINOR, brechende Änderungen über MAJOR mit Nullsetzung von MINOR, rein textliche Errata über die redaktionelle Ausgabe (§1.7.4) ohne Änderung der Protokollnummer.
- Nachfolgende Errata und Ausgabenmigration werden gemäß §1.7.4 / §1.7.5 ausgeführt; dieses Protokoll wird gemeinsam mit dem Protokolltext migriert und mit der jeweiligen Ausgabe aktualisiert.
- Gleichartige Änderungen werden über die Sprachfassungen hinweg im selben Zyklus synchronisiert; bei Abweichungen ist die maßgebliche Fassung ausschlaggebend.

---
