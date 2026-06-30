---
title: "Faying Protocol/1.0 — §1 Überblick"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: de
part: "Kapitel 1 von 11 (Protokolltext)"
---

> Protokolltext-Navigation: [Inhaltsverzeichnis](./README.md) | nächstes [§2 Architektur](./02-Architektur.md)

## §1 Überblick

Dieses Kapitel legt fest, was das Faying Protocol ist, was es löst und was nicht: die Protokollbenennung, seine Position im Technologie-Stack, das Gerüst der Entwurfsziele, die Kernunterschiede zu bestehenden Verfahren, die Ein-Satz-Definition des Faying Protocol, den Leistungsumfang und die ausdrücklichen Nicht-Ziele dieses Protokolltexts sowie die Regeln für Versionsverwaltung und Kompatibilität. Es ist der semantische Anker für die nachfolgenden §2–§11 und die Anhänge A/B.

> **Hinweis zur EARS-Rückverfolgbarkeit**: Jeder Regel in diesem Kapitel folgt eine `Trace:`-Zeile, die die zugehörigen EARS-Teilklausel-IDs (aus der Anforderungsbasis) in der Form `R<requirement>.<criterion>.<clause>` auflistet.

### §1.1 Protokollbenennung

Name der Protokollspezifikation: **Faying Protocol**. Die Versionsnummer wird einheitlich als **Faying Protocol/1.0** geschrieben.

Dieses Protokoll **schafft die Abkürzung FAP (Faying Auth Protocol) ab** — **der Protokollname lautet Faying Protocol, es gibt keine eigene Abkürzung**; wird eine Kurzform benötigt, ist der vollständige Name „Faying Protocol“ zu verwenden. Dieses Entwurfsdokument und die begleitenden Spezifikationsdokumente enthalten keine historischen Benennungsformen wie `FAP` / `FAP/1.0` / `Faying Auth Protocol` / `application/fap+json` / `POST /fap/v1/...` mehr. Jede frühere `FAP`-Referenz ist als veraltete Bezeichnung für das Faying Protocol zu verstehen und in neuen Dokumenten durch Faying Protocol zu ersetzen.

> **Historisches Benennungs-Erbe**: Frühe Entwürfe verwendeten „Faying Auth Protocol (FAP)“. Diese Benennung ist abgeschafft; jede externe Referenz auf `FAP` ist als veraltete Bezeichnung für das Faying Protocol zu verstehen und darf in neuen Dokumenten nicht wiederverwendet werden.

### §1.2 Protokollpositionierung

> **Das Faying Protocol ist ein „kontinuierliches Autorisierungsschicht“-Protokoll auf Anwendungsebene oberhalb von TLS, das die Semantik trägt, „unter welchem Präsenzzustand, über welchen Umfang, auf welcher Stufe und in welchem Zeitfenster ein Human Prime seine iFay autorisiert“.**

- **Unterhalb von TLS**: Vertraulichkeit des Kanals und Identität der Gegenstelle werden von TLS 1.3 (mit optionalem mTLS) erbracht; das Faying Protocol wiederholt dies nicht.
- **Neben OAuth/OIDC**: OAuth liefert Autorisierung auf Anwendungsebene, OIDC stellt Identitätsaussagen aus; beide sind „Momentaufnahme-Token“-Modelle. Das Faying Protocol löst, was keines von beiden löst — **kontinuierliche Stellvertretung + Präsenzbindung + Stufenwechsel + eindeutige Verantwortungszuordnung**.
- **Oberhalb von WebAuthn**: WebAuthn / FIDO2 liefert während des Bootstrapping hardwarestarke „Benutzerpräsenz“-Nachweise für den Human Prime; das Faying Protocol verwendet dessen Berechtigungsform als Wurzel des abgeleiteten Vertrauens wieder.

Das Faying Protocol ersetzt weder TLS noch erfindet es OAuth neu; es sitzt oberhalb von TLS und unterhalb der Geschäftssemantik und erzwingt, dass **jede ausgehende Aktion einer iFay** das Mandate-Verifikationstor passiert. Jeder ausgehende Aufruf, der dieses Tor umgeht, gilt als Rogue Action und muss von einer Middleware abgewiesen werden, die oberhalb der Transportschicht und unterhalb der Geschäftsschicht angesiedelt ist.

### §1.3 Entwurfsziele

Die folgende Tabelle listet die **8 Entwurfsziele G1–G8 des Faying Protocol** (Kernziele) sowie 2 aus §9 / §5 abgeleitete Engineering-Ziele (Sicherheitseigenschaften / Protokoll-Interoperabilität) auf. **Jedes Ziel ist genau einer Requirement der Anforderungsbasis zugeordnet** und bildet damit den bidirektionalen Rückverfolgbarkeitsanker zwischen diesem Protokolltext und dem Anforderungsdokument.

| Ziel | Bedeutung | Ursprung im Blueprint | Zugehörige Requirement |
| --- | --- | --- | --- |
| **G1 Eindeutige Verantwortungszuordnung** | Zu jedem Zeitpunkt lässt sich die ausgehende Aktion einer iFay eindeutig einem einzigen Human Prime zuordnen | Ethische Grenzlinie Kapitel 13 | Requirement 1 |
| **G2 Default-Deny** | Kein gültiges Mandate → keine ausgehende Aktion; jedes fehlende Feld → Ablehnung | Rogue-Default Kapitel 13 | Requirement 2 |
| **G3 Beobachtbar, auditierbar, widerrufbar** | Zustandsübergänge, Aktionsauslösung sowie Erneuerungs-/Widerrufsereignisse sind sämtlich beobachtbar, auditierbar und unabhängig überprüfbar | Kapitel 11, 13 | Requirement 3 |
| **G4 Symmetrischer Widerruf** | Die Erreichbarkeit der Widerrufspfade ≥ der der Etablierungspfade; Widerruf ist irreversibel | Kapitel 10, 12 | Requirement 4 |
| **G5 Kontinuierliche Kalibrierung** | Präsenzsignale und Mandate-Stufe können in jedem Moment erneut bestätigt werden; Vertrauen verweilt nie über sein Ablaufdatum hinaus | Kapitel 11, 12 | Requirement 5 |
| **G6 Gestufte Autorisierung** | Ein einzelnes Mandate kann nicht alle Stärken abbilden; die Stufe muss ausdrückbar, umschaltbar und herabstufbar sein; Höherstufungen erfordern eine HP-Bezeugung | Briefing-Punkt 3 des Originals | Requirement 6 |
| **G7 Geräteübergreifende Ableitung** | Wenn dieselbe iFay über mehrere Endgeräte arbeitet, darf Vertrauen abgeleitet werden, doch der Verantwortliche ändert sich nie; Umfang/Stufe konvergieren strikt | Evolutionärer Vorbehalt Phase 2/3 | Requirement 7 |
| **G8 Post-Quanten-Evolvierbarkeit** | Algorithmen-Suiten können ausgehandelt und vorwärtsgerollt werden; PQC-Verhandlungs-Bits sind reserviert | Allgemeines Engineering-Erfordernis | Requirement 8 |
| —(abgeleitet) **Sicherheitseigenschaften** | Anti-Replay / Anti-Hijack / Anti-Phishing / Verbindungsabbruch-Erkennung / Adversarial Threats des KI-Zeitalters | §9 Sicherheitsbetrachtungen | Requirement 9 (mit Ableitung Requirement 13) |
| —(abgeleitet) **Protokoll-Interoperabilität** | CBOR / JSON-Äquivalenz, Deterministic CBOR, implementierungsübergreifende Kompatibilitätsmatrix | §5 Protokollnachrichten | Requirement 10 |

> **Prinzip der Eins-zu-eins-Zuordnung von Ziel ↔ Requirement**: Diese Tabelle ist die **alleinige maßgebliche Zuordnung** zwischen dem Protokolltext und dem Anforderungsdokument. Jede in späteren Kapiteln zur Begründung einer Invariante oder eines Mechanismus zitierte EARS-Teilklausel-ID `R<n>.<m>.<k>` muss ihre Wurzel-Requirement-Nummer `<n>` in der Spalte „Zugehörige Requirement“ wiederfinden. Endorsed_Mandate (Requirement 11) abgeleitet aus G6 / G4 / G5 / G7, die Verbindungsabbruch-Richtlinie (Requirement 12) sowie der Schutz im KI-Zeitalter (Requirement 13) wirken als Verfeinerungen von G1–G8 und erhalten ihre protokollseitige Landung jeweils in §4 / §8 / §9.

### §1.4 Kernunterschiede zu bestehenden Verfahren (Einzeiler-Fassung)

| Bestehendes Verfahren | Löst | Löst NICHT — was das Faying Protocol lösen muss |
| --- | --- | --- |
| OAuth 2.0 / 2.1 | Anwendungszugriffs-Autorisierung auf Ressourcen | Einmal-Token, keine Stufe, keine Präsenz, kein symmetrischer Widerruf |
| OIDC SSO | Identitätsaussage (wer) | Keine kontinuierliche Stellvertretung (im Namen handeln), keine Stufe |
| mTLS | Identität der Gegenstellen an beiden Kanalenden | Kann nicht ausdrücken „wer, unter welchem Präsenzzustand, wen womit beauftragt hat“ |
| JWT | Selbsttragende Claims mit Signatur | Kein Widerruf, keine Stufensemantik, lange Lebensdauer kollidiert mit „symmetrischem Widerruf“ |
| FIDO2 / WebAuthn | Hardwarestarker Präsenznachweis für den Human Prime | Deckt nur den Anmeldemoment ab, nicht die kontinuierliche Stellvertretung der iFay |
| Macaroons | Ableitbare Token mit Caveats | Keine Präsenzbindung, keine ausdrückliche Human-Prime-Bezeugung |
| SPIFFE / SPIRE | Workload-Identität | Workload-Perspektive, kein menschlicher Verantwortungsendpunkt |

Das Faying Protocol konkurriert mit keinem der oben Genannten — es sitzt oberhalb von TLS und unterhalb der Geschäftssemantik und liefert die **dedizierte Semantik** von „Human Prime ↔ iFay“: kontinuierliche Stellvertretung + Präsenzbindung + Stufenwechsel + eindeutige Verantwortungszuordnung + symmetrischer Widerruf.

### §1.5 Ein-Satz-Definition

> **Faying Protocol = „Mandate (statt Token) + Presence Signal + Attestation Chain + Revocation Registry“ — vier Elemente, die oberhalb von TLS kooperativ ausgedrückt werden, bidirektional von Human Prime und iFay initiiert, erst durch die ausdrückliche Bestätigung des Human Prime wirksam, kontinuierlich kalibriert und symmetrisch widerrufbar.**

#### §1.5.1 Faying-Zustandsänderungen werden erst mit der ausdrücklichen Bestätigung des Human Prime wirksam (Kernaussage)

Die Initiierung einer Faying-Beziehung (Etablierung oder Anpassung) ist **bidirektional**:

- **HP-initiiert**: Der Human Prime kann Faying proaktiv über den BOOTSTRAP-Kanal initiieren (siehe §2.4 Phase A, §5.3.1).
- **IF-initiiert**: Die iFay kann beim Human Prime proaktiv Faying anstreben (d. h. FAYING_REQUEST) über den Zwei-Schritt-Pfad §2.4 Phase A0 → BOOTSTRAP (siehe §5.3.6).

> **Unabhängig davon, welche Seite initiiert, ist die endgültige Wirksamkeitsbedingung für jede Faying-Zustandsänderung jedoch, dass der Human Prime eine ausdrückliche, ungetäuschte, überprüfbare Bestätigung erteilt** (Standardform ist eine WebAuthn-Benutzerpräsenz-Aussage oder ein gleichwertiger hardwarestarker Nachweis).

Daraus folgen unmittelbar drei unverrückbare harte Bedingungen:

1. **Die iFay allein kann Faying nicht wirksam machen**: Ein IF-initiierter FAYING_REQUEST, der innerhalb von `BootstrapTimeout` (Standard 60 s, siehe Anhang B) keine ausdrückliche HP-Bestätigung erhält, verfällt oder wird abgelehnt und **erzeugt keine Faying-Zustandsänderung**. Mandate_Service muss `E_FAYING_REQUEST_NOT_CONFIRMED` (Fehlercode 1014) zurückgeben und das Ereignis in die Attestation Chain schreiben, um den irreversiblen Nachweis „wer initiiert hat, wann bestätigt wurde, ob es wirksam wurde“ zu bewahren.
   - **Trace**: `R1.3.2` (IF-initiierter Pfad wird erst nach ausdrücklicher HP-Bestätigung wirksam), `R1.3.3` (Ablehnung ohne Zustandsänderung, wenn `BootstrapTimeout` ohne Bestätigung abläuft), `R1.3.4` (Ereignis wird unabhängig von der Wirksamkeit in die AC geschrieben).
2. **Kein Pfad für stellvertretende Bezeugung**: Auf der Protokollebene existiert kein legitimer Pfad, über den iFay, Mandate_Service oder Supervisory_Agent den Human Prime beim Abschluss der Faying-Bestätigung ersetzen könnten. Jeder BOOTSTRAP ohne `human_witness` oder mit fehlgeschlagener `human_witness`-Verifikation muss mit `E_HUMAN_WITNESS_REQUIRED` (Fehlercode 1010) abgelehnt werden.
   - **Trace**: `R1.3.5` (kein legitimer Pfad für IF / MS / SA, um HP beim Abschluss der Faying-Bestätigung zu ersetzen).
3. **Die iFay kann den Widerruf nicht einseitig umgehen**: Die iFay darf eine Nachricht „Anfrage zur Trennung von Faying“ aussenden (als Disclosure_Report behandelt), besitzt jedoch nicht die Befugnis, ihr eigenes Mandate zu widerrufen; jeder Widerruf muss letztlich vom Human Prime oder einer Regulierungs-/Aufsichtsbehörde initiiert und über den HP-Sichtkanal sichtbar gemacht werden (siehe §4 / §10).
   - **Trace**: `R4.1.4` (IF besitzt nicht die Befugnis, das eigene Mandate zu widerrufen), `R4.1.5` (Trennungsanfrage wird als Disclosure_Report in die AC geschrieben und an den HP-Sichtkanal gesendet).

Dieser Unterabschnitt ist im Überblick-Kapitel der einheitliche Anker für §2.4 Phase A0, §5.3.6 FAYING_REQUEST und §5.4 Fehlercodes 1010 / 1014 sowie der Ausgangspunkt aller späteren Argumentationen „ohne HP-Bezeugung kein Faying“.

### §1.6 Leistungsumfang und Nicht-Ziele des Protokolls

#### §1.6.1 Im Umfang (Normative — von diesem Protokolltext getragen)

Dieser Protokolltext spezifiziert **und spezifiziert ausschließlich** Folgendes:

- **Protokoll-Datenobjekte**: das primäre CBOR-Format und das JSON-Fallback-Format für Mandate / Presence_Signal / Attestation / SignatureBundle / Faying Protocol Envelope / Endorsed_Mandate / Disclosure_Report usw. (die CDDL ist maßgeblich; siehe §4 / §5).
  - **Trace**: `R10.1.1`, `R10.1.2`, `R10.2.1`–`R10.2.4`.
- **Protokollkomponenten-Schnittstellen**: Verantwortungsgrenzen und Invarianten von Mandate_Service / Presence_Channel / Attestation_Chain / Revocation_Registry / Liveness_Channel / Behavior_Baseline_Service (siehe §3).
- **Protokollnachrichten**: Felddefinitionen, Fehlercodes und harte Bedingungen auf Protokollebene für die sieben Nachrichtentypen BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE / REVOKE / FAYING_REQUEST / DISCLOSURE (siehe §5).
- **Kryptografische Regeln**: Aushandlung der Algorithmen-Suite, Hierarchie der Schlüsselableitung, Kanonisierung der Signatureingabe (einschließlich des Signatureingabe-Ankers von Endorsed_Mandate; siehe §6).
  - **Trace**: `R8.1.1`–`R8.1.4`, `R8.2.1`–`R8.2.4`.
- **Semantik der Autorisierungsstufen**: präzise Definitionen der fünf Stufen G0–G4, die Matrix der Auslösebedingungen, das Prinzip der Herabstufungs-Monotonie und die Endorsement-Grades-Unterstufen (siehe §7).
  - **Trace**: `R5.1.1`, `R6.1.1`, `R6.1.2`.
- **Lebenszyklus und Zustandsmaschine**: die sieben Zustände Unpaired / Pairing / Active / Degraded / Disconnected / Suspended / Revoked, ihre Übergangsbedingungen und die Abgleichstransaktion (siehe §8).
- **Sicherheitsbetrachtungen**: STRIDE-Bedrohungsmodell, Anti-Replay / Anti-Hijack / Anti-Phishing / Verbindungsabbruch-Erkennung, geräteübergreifende Übertragung abgeleiteten Vertrauens sowie die AI-Era Adversarial Threats T1–T7 (siehe §9).
- **Fehlerbehandlung**: Protokollantworten, Wiederherstellungspfade, Beobachtbarkeitsbedingungen und Default-Deny-Konvergenz für die 14 Fehlercodes (einschließlich 1010 `E_HUMAN_WITNESS_REQUIRED`, 1013 `E_ENDORSEMENT_INVALID`, 1014 `E_FAYING_REQUEST_NOT_CONFIRMED`; siehe §10).
  - **Trace**: `R2.1.1`–`R2.1.4` (Default-Deny), `R3.3.1` (HP-Sichtkanal muss erreichen).
- **Anhänge**: Terminologie-Abgleich-Kurzreferenz (Anhang A), Standard-Parameterbudgets (Anhang B).

#### §1.6.2 Außerhalb des Umfangs (Non-normative — von diesem Protokoll nicht getragen)

Folgendes liegt **nicht** im normativen Umfang dieses Protokolltexts und dient nur als Referenzimplementierung / Engineering-Leitfaden; es steht in keinem Zusammenhang mit der Interoperabilitätskonformität gegenüber diesem Protokolltext:

- **Geschäftssemantik**: das konkrete Geschäftsverhalten der iFay, Endgerätetreiber, Anwendungsintegrationsmuster;
- **UI / UX-Design**: die konkrete Darstellung des Human-Prime-Sichtkanals, Gestaltung von Bestätigungsdialogen, Interaktionen für Mobil-/Desktop-Geräte;
- **Betrieb und Bereitstellung**: hochverfügbare Bereitstellungsmodelle, Skalierungsstrategien, regionsübergreifende Synchronisation für Mandate_Service / Revocation_Registry;
- **Transportschicht-Details**: die Handshake-Details von TLS 1.3 selbst (durch RFC 8446 spezifiziert), spezifische Tuning-Parameter für HTTP/2 / gRPC / QUIC;
- **PD-Implementierungen (Presence Device)**: Hardware-Implementierungen von WebAuthn-Authentifikator / TPM / Platform Keystore (durch W3C / ISO / TCG spezifiziert);
- **Rechtliche und Compliance-Details**: wie Regulierungs-/Compliance-Stellen außerhalb des Protokolls als rechtliche „Behörden“ agieren (die Protokollebene spezifiziert nur ihre Position in der RevokeReason-Enum und die Anforderung an die Signaturkette, nicht ihre rechtliche Verfasstheit);
- **Referenzimplementierungs-Code**: jede Referenzimplementierung dieses Protokolls (etwa die TypeScript-Ansicht [`schemas/types.ts`](../../../../schemas/types.ts) oder die eigenschaftsbasierte Testsuite `pbt/`) ist ausdrücklich als **„Reference Implementation, Not Normative“** gekennzeichnet und stellt nicht den Protokolltext dar;
- **Offene Fragen**: alle Punkte in §11 Offene Fragen mit `status: open`.

#### §1.6.3 Prinzip der Lieferform

Der Protokolltext dieser Spezifikation ist nach Kapiteln aufgeteilt, insgesamt §1–§11 als 11 Dateien zuzüglich der drei Anhänge A/B/C, alle abgelegt unter `docs/de/specification/2025-10-25/`; die Dateinamen mit Kapitelnummern finden sich im [Inhaltsverzeichnis](./README.md). Anhang A (Terminologie-Abgleich) und Anhang B (Standard-Parameterbudgets) sind Referenzen auf Normebene; Anhang C (Änderungsprotokoll) hält die Entwicklung des Protokolls vom Entwurf bis zur Endfassung sowie die Strategie der Versionsnummerierung fest.

Die englische Spezifikation liegt unter `docs/en/specification/2025-10-25/` und hat eine **Einzeldatei-Struktur** — der Protokolltext (§1–§11 + Anhänge A/B) ist vollständig in die eine Datei `Faying-Protocol-1.0.md` eingebettet, und auf englischer Seite werden eigenständige Dateien wie Anhang C (Änderungsprotokoll) nicht gepflegt. Die Entsprechung der beiden Seiten ist eine Entsprechung auf **Abschnittsanker-Ebene**: Abschnittsnummerierung, Mermaid-Diagramme, CDDL-/TypeScript-Codeblöcke, Fehlercode-Tabelle sowie die Anhänge A/B sind einzeln aufeinander abgestimmt, nicht datei-für-datei. Bei Abweichungen ist die maßgebliche Fassung ausschlaggebend.

### §1.7 Versionsverwaltung und Kompatibilität

Dieser Abschnitt ist die **maßgebliche Definition** der Versionsnummerierung des Faying Protocol. Die Versionsnummer ist nicht bloß eine Dokumentationsmarkierung — sie ist **Teil des Interoperabilitätsvertrags**: Sie erscheint im Wire-Envelope, in Schemata und in der Aushandlung und entscheidet unmittelbar, ob zwei unabhängige Implementierungen miteinander kommunizieren können. Dieser Abschnitt ist daher Normative: Implementierungen MÜSSEN Versionsnummern interpretieren und die Versionsaushandlung gemäß den nachstehenden Regeln durchführen. Anhang C (Änderungsprotokoll) hält nur die Historie fest; er definiert diese Regeln nicht neu.

#### §1.7.1 Drei orthogonale Versionsachsen

Das Faying Protocol beschreibt die Version einer Spezifikation mit **drei voneinander unabhängigen Achsen**, die NICHT zu einer einzigen Nummer vermengt werden dürfen:

| Achse | Beantwortete Frage | Form | Träger | Beispiel |
| --- | --- | --- | --- | --- |
| **Protokollversion** (Interoperabilitätsvertrag) | Können zwei Implementierungen kommunizieren | `MAJOR.MINOR` | Prosa / Wire-Envelope-Feld `version` / Schema-Dateiname | `Faying Protocol/1.0` |
| **Dokumentstatus** (Lebenszyklus) | Ist diese Spezifikation final | Enum | Front-Matter `status` | `Draft` / `Final` / `Deprecated` / `Obsolete` |
| **Redaktionelle Ausgabe** (Errata & Klarstellungen) | Welche textliche Revision unter derselben Protokollversion | Veröffentlichungsdatum | Name des Release-Verzeichnisses / Front-Matter `date` | `2025-10-25` |

> **Kernbedingung**: **Nur die „Protokollversion“ `MAJOR.MINOR` gelangt in das Wire-Format** (das Envelope-Feld `version`, Schema-Dateinamen). Dokumentstatus und redaktionelle Ausgabe DÜRFEN NICHT in das Wire-Format gelangen — sie sind Marker der Dokumentenverwaltung und nehmen an Interoperabilitätsentscheidungen nicht teil. Eine Implementierung DARF ihr Nachrichtenverhalten NICHT ändern, weil sich der Dokumentstatus oder die redaktionelle Ausgabe einer Gegenstelle unterscheidet.

#### §1.7.2 Semantik der Protokollversion `MAJOR.MINOR`

Die Protokollversion wird `Faying Protocol/MAJOR.MINOR` geschrieben, mit **nur zwei Ebenen und ohne PATCH** — Wire-Format und Interoperabilitätssemantik unterscheiden nur zwei Kompatibilitätsstufen.

- **MAJOR (brechende Änderung)**: jede Änderung, die eine streng nach der alten Spezifikation implementierte Gegenstelle dazu brächte, neue Nachrichten **abzulehnen oder falsch zu interpretieren**. Beispiele: Änderung der Semantik eines maßgeblichen CDDL-Felds aus §4.2, Entfernen eines Nachrichtentyps, Neudefinition der Fehlercode-Semantik, Änderung eines absorbierenden Zustands der Zustandsmaschine.
  - Regel: MAJOR erhöhen, MINOR auf null zurücksetzen (z. B. `1.4 → 2.0`).
  - Kompatibilität: Interoperabilität über verschiedene MAJOR hinweg ist **nicht garantiert**.
- **MINOR (rückwärtskompatible Ergänzung)**: eine Ergänzung, die eine neue Implementierung in alten Nachrichten verstehen kann und die eine alte Implementierung dort, wo sie optionale Bestandteile nicht erkennt, sicher ignorieren kann. Beispiele: Hinzufügen optionaler Felder, Hinzufügen von Nachrichten oder Fehlercodes, Hinzufügen von Einträgen im KI-Zeitalter-Bedrohungskatalog, Hinzufügen von Anhang-Parametern, Hinzufügen von Correctness Properties.
  - Regel: MINOR inkrementieren (z. B. `1.0 → 1.1`).
  - Kompatibilität: Innerhalb desselben MAJOR MUSS ein höheres MINOR rückwärtskompatibel zu niedrigeren MINORs bleiben.

**Entscheidungstest (Selbstprüfung für Implementierende)**: Würde die Änderung eine streng nach der alten Spezifikation implementierte Gegenstelle dazu bringen, neue Nachrichten abzulehnen oder falsch zu interpretieren?

- Ja → **MAJOR**;
- Nein, aber sie fügt im Wire-Format sichtbaren Inhalt hinzu → **MINOR**;
- Sie ändert nur Text, keine Wire-Format-Semantik (Tippfehlerkorrekturen, ergänzte Beispiele, geklärte Mehrdeutigkeiten) → **Protokollversion nicht ändern**; redaktionelle Ausgabe nach §1.7.4 verwenden.

Die aktuelle Basislinie ist `Faying Protocol/1.0`.

#### §1.7.3 Versionsaushandlung und Kompatibilitätsregeln (Normative)

Die Versionsaushandlung **verwendet denselben Ansatz wie die Aushandlung der Algorithmen-Suite in §6.1 wieder** (jede Seite deklariert, der höchste gemeinsam unterstützte Wert wird gewählt). Implementierungen MÜSSEN:

1. **Deklarieren**: Während des BOOTSTRAP deklarieren Client und Server jeweils ihre unterstützte Protokollversionsmenge (z. B. `supported: [1.0, 1.1]`).
2. **Gleicher MAJOR → höchstes MINOR**: Teilen beide Seiten einen MAJOR, MÜSSEN sie das **höchste gemeinsam unterstützte MINOR** als wirksame Version der Sitzung wählen; eine Implementierung mit höherem MINOR MUSS eine Gegenstelle mit niedrigerem MINOR bedienen können (rückwärtskompatibel bis `MAJOR.0`).
3. **MAJOR-übergreifend → ablehnen**: Existiert kein gemeinsamer MAJOR, findet keine Aushandlung statt; der BOOTSTRAP MUSS mit `E_PROTOCOL` (Fehlercode 1099) abgelehnt werden; keine „Best-Effort“-Degradierungs-Interoperabilität ist erlaubt.
4. **Rollendes Upgrade darf bestehende Mandates nicht brechen**: Wird über die Versionsaushandlung eine neue Standard-Algorithmen-Suite oder ein neues MINOR eingeführt, MÜSSEN bestehende Mandates vor ihrem `not_after` überprüfbar bleiben; ein Versions-Upgrade DARF keine in Bearbeitung befindlichen gültigen Mandates ungültig machen.
   - **Trace**: `R8.2.4` (rollendes Upgrade über Versionsaushandlung ohne Brechen der Überprüfbarkeit bestehender Mandates).
5. **Umgang mit einem unbekannten höheren MINOR**: Beim Empfang einer Nachricht, die als gleicher MAJOR, aber höheres MINOR als das eigene deklariert ist, MUSS eine Implementierung sie mit ihrem eigenen höchsten unterstützten MINOR interpretieren und nicht erkannte optionale Felder **ignorieren** (statt abzulehnen); dies ist die Laufzeitumsetzung des MINOR-Rückwärtskompatibilitätsversprechens.

#### §1.7.4 Redaktionelle Ausgabe und Errata (Non-normative Änderungen)

Nachdem `Faying Protocol/1.0` finalisiert ist (Final), sind rein textliche Errata unvermeidlich — Tippfehlerkorrekturen, ergänzte Beispiele, geklärte Mehrdeutigkeiten, korrigierte interne Verweise. Solche Änderungen:

- DÜRFEN die Protokollversionsnummer NICHT ändern (das würde fälschlich behaupten, der Interoperabilitätsvertrag habe sich geändert);
- werden am **Veröffentlichungsdatum** verankert: z. B. ist `Faying Protocol/1.0 (2025-10-25)` die erste Final-Ausgabe von 1.0; nachfolgende Errata erzeugen ein neues Release-Verzeichnis (z. B. `2026-03-xx/`), während die Protokollversion `1.0` bleibt;
- werden im Änderungsprotokoll des Anhangs C unter einer Kategorie `Editorial` protokolliert, wobei der Ausgabenübergang über ein Front-Matter-Feld `edition` markiert wird;
- **Harte Bedingung**: Eine redaktionelle Ausgabe darf ausschließlich Non-normative Änderungen tragen. Jede Modifikation, die die Wire-Format-Semantik berührt, MUSS MINOR oder MAJOR erhöhen und DARF NICHT als redaktionelles Erratum getarnt veröffentlicht werden.

#### §1.7.5 Wo die Versionsnummer landet und Hinweise für Standard-Implementierende

Die folgende Tabelle gibt genau an, wo die Versionsnummer landet, damit Implementierende beurteilen können, welche Unterschiede die Interoperabilität betreffen und welche nicht:

| Landeplatz | Was geschrieben wird | Hinweise |
| --- | --- | --- |
| Wire-Envelope-Feld `version` (§5.2) | `"Faying Protocol/MAJOR.MINOR"` | **nur MAJOR.MINOR**; kein Ausgabendatum, kein Dokumentstatus |
| Schema-Dateiname (`fap-1.0.cddl` usw.) | folgt `MAJOR.MINOR` | der Dateiname **ändert sich nicht über redaktionelle Ausgaben hinweg** — Errata benennen `fap-1.0.cddl` nicht um, damit bestehende Verweise stabil bleiben (das beibehaltene veraltete `fap`-Präfix folgt derselben Logik; siehe Anhang C) |
| content-type (§5.1) | `application/faying-protocol+cbor` (oder `+json`) | der content-type identifiziert die Protokollfamilie; ein Parameter `version=` DARF zur Gateway-Routing als **Bereitstellungskomfort** angehängt werden, doch dieser Parameter ist nicht Teil der Wire-Format-Semantik und beeinflusst keine Kompatibilitätsentscheidungen |
| Front-Matter `status` / `date` | Dokumentstatus / redaktionelle Ausgabe | Marker der Dokumentenverwaltung; **gelangen nicht in das Wire-Format**; eine Gegenstelle DARF die Nachrichtenbehandlung nicht auf ihrer Grundlage ändern |
| git-Tag | `faying-protocol-v<MAJOR.MINOR>-<status>` | Finalisierung `faying-protocol-v1.0-final`; Ausgaben-Snapshot `faying-protocol-v1.0-2026-03-xx`; ein Tag MUSS gleichzeitig den Text + `vectors/` + `schemas/` abdecken und das Interop-Tripel gemeinsam einfrieren |

**Pflichthinweise für Standard-Implementierende**:

1. **Interoperabilität wird allein an der Protokollversion beurteilt**: Die einzige Grundlage für „können wir kommunizieren“ ist `MAJOR.MINOR`. Der Dokumentstatus einer Gegenstelle (Draft/Final) und die redaktionelle Ausgabe (Veröffentlichungsdatum) ändern das Interoperabilitätsverhalten **nicht** — niemals die gültigen Nachrichten einer Gegenstelle ablehnen, nur weil sie als Draft markiert ist oder eine ältere Ausgabe hat.
2. **Gleicher MAJOR muss rückwärtskompatibel sein**: Beim Implementieren eines höheren MINOR MÜSST ihr auch alle Gegenstellen mit niedrigerem MINOR ab `MAJOR.0` korrekt bedienen.
3. **Errata nicht als Upgrades behandeln**: Eine Änderung des Release-Verzeichnisdatums (redaktionelle Ausgabe) bedeutet nicht, dass sich das Protokoll geändert hat; nur eine Änderung von `MAJOR.MINOR` erfordert die Bewertung der Interoperabilitätsauswirkung.
4. **Stabilität des Schema-Dateinamens**: Verlasst euch nicht darauf, dass der Dateiname die Ausgabe kodiert; Errata desselben `MAJOR.MINOR` verwenden dieselbe Schema-Datei wieder, unterschieden über git-Tag / Release-Verzeichnis.
5. **Kein Kompatibilitätsversprechen während Draft**: Solange `status: Draft`, kann `MAJOR.MINOR` vor dem Einfrieren angepasst werden; die MAJOR/MINOR-Kompatibilitätsversprechen dieses Abschnitts werden erst nach `Final` vollständig wirksam.
