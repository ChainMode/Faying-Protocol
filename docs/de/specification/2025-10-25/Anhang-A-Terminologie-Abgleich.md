---
title: "Faying Protocol/1.0 — Anhang A Terminologie-Abgleich-Kurzreferenz"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: de
part: "Anhang A (Norm-Referenz)"
---

> Protokolltext-Navigation: [Inhaltsverzeichnis](./README.md) | vorheriges [§11 Offene Fragen](./11-Offene-Fragen.md) | nächstes [Anhang B Standard-Parameterbudgets](./Anhang-B-Standard-Parameterbudgets.md)

## Anhang A Terminologie-Abgleich-Kurzreferenz

> Dieser Anhang ist mit dem Glossar der Anforderungsbasis und dem Anhang A der Entwurfsbasis konsistent; in EARS-Teilklauseln auftauchende Systemnamen müssen hier definiert sein, bevor sie verwendet werden. Der Anhang ist zur bequemen Querverweisung in fünf Kategorien gegliedert — „Rollen & Entitäten / Protokollkomponenten / Protokoll-Datenobjekte / Stufen & Richtlinien / Standardbudgets“.

### A.1 Rollen und Entitäten

| Protokollbegriff (Englisch) | Blueprint-Begriff (de) | Beziehung / Hinweis |
| --- | --- | --- |
| Human Prime (HP) | Human Prime (menschliches Urbild) | Synonym; der alleinige letztgültige Verantwortungsendpunkt und Inhaber der Widerrufsbefugnis der Faying-Beziehung; zudem die einzige Entität, die eine ausdrückliche Bestätigung von Faying-Zustandsänderungen erteilen kann |
| iFay Instance (IF) | iFay Instance (iFay-Instanz) | Synonym; die beauftragte Agenten-Entität, eindeutig identifiziert durch FayID; besitzt nicht die Befugnis, ihr eigenes Mandate zu widerrufen; alle Zustandsänderungen sind an die ausdrückliche HP-Bestätigung gebunden |
| Supervisory Agent (SA) | Supervisory Agent (Aufsichtsagent) | Eine vom Prime unterschiedene und auf Protokollebene erkennbare Klasse von Regulierungsinstanz; besitzt keine Widerrufsbefugnis; kann HP beim Abschluss der Faying-Bestätigung nicht ersetzen |
| Relying Party (RP) | Relying Party (aufgerufene Partei) | Das von der iFay aufgerufene Endgerät, die Anwendung oder der Dienst |
| Presence Device (PD) | Presence Device (Anwesenheitsgerät) | Hardware, die WebAuthn-/FIDO2-Berechtigungen und biometrische Fähigkeiten trägt; die physische Quelle von Präsenzsignalen |

### A.2 Protokollkomponenten

| Protokollbegriff (Englisch) | Abk. | Beschreibung |
| --- | --- | --- |
| Mandate Service | MS | Der logische Dienst, der Mandates im Namen des HP ausstellt / erneuert / herabstuft / widerruft (siehe §3.1) |
| Presence Channel | PC | Der latenzarme, replay-resistente Präsenzstrom von PD zu MS (siehe §3.2) |
| Attestation Chain | AC | Die rückwärts verfolgbare Signaturkette, die aus allen Ausstellungsaktionen HP → MS → IF → abgeleitete IF gebildet wird (siehe §3.3) |
| Revocation Registry | RR | Echtzeit-Widerrufsstatusdienst (siehe §3.4) |
| Liveness Channel | LC | Trennungserkennungsstrom (einschließlich tatsächlicher Trennung und wahrgenommener Trennung) (siehe §3.5, §9.9) |
| Behavior Baseline Service | BBS | Statistischer Dienst, der die (HP, IF)-Verhaltens-Baseline pflegt (siehe §3.6) |

### A.3 Protokoll-Datenobjekte

| Protokollbegriff (Englisch) | Blueprint-Begriff (de) | Beschreibung |
| --- | --- | --- |
| Mandate | Mandate (Vollmacht) | Ein neues Konzept auf Protokollebene; trägt die Felder `(issuer, subject, scope, grade, presence_req, not_before, not_after, attestation, signature, endorsement?)` (siehe §4.1 / §4.2) |
| Endorsed_Mandate | Endorsed Mandate (bezeugte Autorisierung) | Ein Mandate-Subtyp; deklariert ausdrücklich `endorsement = (enabled, endorsed_scope ⊆ scope, endorsed_grade.autonomy ≤ grade.autonomy, endorsed_lifetime, offline_revocation_policy)` und erlaubt der IF, während einer physischen Trennung innerhalb eines eingeschränkten Rahmens autonom zu arbeiten; der Verantwortungsendpunkt ist stets der HP (siehe §7.5, P16.x) |
| PresenceSignal | Presence Signal (Anwesenheitssignal) | Eine von PD erzeugte und von MS überprüfbare physische Präsenzaussage |
| Attestation | Attestation (Bezeugung) | Einheitlicher Träger überprüfbarer Aussagen (WebAuthn / TPM-quote / Platform-keystore / Self-signed) |
| FayID | FayID | Die einheitliche eindeutige Identität der iFay innerhalb des iFay-Frameworks (ULID-ähnlich) |
| Faying_State | Faying State (kontrollierter Zustand) | Der Verhaltenszustand, in dem sich die IF befindet, wenn das Mandate in Active / Degraded / Disconnected ist |
| Rogue_Fay | Rogue Fay (Loslösungszustand) | Der Verhaltenszustand, in dem sich die IF befindet, wenn das Mandate in Unpaired / Revoked oder abwesend ist; ein zum Faying_State gegenseitig ausschließendes Binär (P15). **Hinweis**: `Suspended` wird *nicht* als Rogue_Fay klassifiziert — es ist „Faying State pausiert“ (die Überwachungsbeziehung besteht fort, die Mandate-Metadaten werden bewahrt, und der HP kann es ohne frischen BOOTSTRAP ausdrücklich wieder aufnehmen); es teilt nur das D-Dimension-Verbot mit Rogue als Verhaltenskonsequenz; siehe die Zuordnungstabelle in §4.3 / §8.2 |
| Faying_Initiation | Bidirectional Faying Initiation (bidirektionale Faying-Initiierung) | Die Initiierung einer Faying-Beziehung (Etablierung oder Anpassung) kann entweder vom HP (HP-initiiert) oder von der IF, die beim HP Faying anstrebt (IF-initiiert / FAYING_REQUEST), initiiert werden; die endgültige Wirksamkeitsbedingung ist, dass der HP eine überprüfbare, ausdrückliche Bestätigung erteilt (siehe §5.3.6, P16.6) |
| Behavior_Baseline | Behaviour Baseline (Verhaltens-Baseline) | Das von BBS gepflegte kumulative (HP, IF)-Verhaltensprofil, genutzt zur Erkennung plötzlicher Abweichungen (siehe §3.6, P18.5) |
| Atomic_Action | Atomic Action (atomare Aktion) | Die kleinste unteilbare Deklarationseinheit, die die IF nach außen ausführt; ein Aufruf entspricht genau 1 Atomic_Action; Bündelung ist verboten (siehe P18.2) |
| Disclosure_Report | Disclosure Report (Offenlegungsnachricht) | Die strukturierte Nachricht, die die IF beim Berichten oder Anfordern einer Bestätigung verwendet; `mandatory_fields` sind zwingend parsbar (siehe §5.3.7, P18.3) |
| Ego | Ego (Selbstgrenze) | Synonym; verwendet für die `ego-deviation`-Entscheidung (siehe §3.6, §9.10.4) |
| Human View | Human View (menschliches Sichtfeld) | Werterahmen; das Faying Protocol ist seine Verkörperung auf Protokollebene (Blueprint-Kapitel 11) |

### A.4 Stufen und Richtlinien

| Protokollbegriff (Englisch) | Beschreibung |
| --- | --- |
| Authorization_Grade (Grade) | Autorisierungsstufe, Wert `G0..G4` (siehe §7) |
| G0 Emergency_Override | Notfallübernahme-Stufe; HP einseitiger Force-Recall (siehe §7.1, P12) |
| G1 Strict | Die strikteste Stufe; die Standardstufe für hochsensible Aktionen |
| G2 Moderate | Mittlere Stufe |
| G3 Loose | Nachgiebige Stufe |
| G4 Autonomous | Die autonomste Stufe; G4-Heartbeat-Verlust direkt → Suspended (siehe §7.3) |
| PresenceRequirement | Präsenzanforderung; das an die Stufe gebundene Tripel `(signal_types, max_staleness_ms, on_loss)` |
| Scope | Autorisierungsumfang; der explizit deklarierte Least-Privilege-Satz `(domains, actions, terminals?, budget?)` |

### A.5 Standardbudgets (detaillierte Werte in Anhang B)

| Protokollbegriff (Englisch) | Kurzbeschreibung |
| --- | --- |
| MaxMandateLifetime | Maximale Lebensdauer eines einzelnen Mandate (Standard 24 h, Obergrenze 30 d) |
| BootstrapTimeout | Timeout, das BOOTSTRAP / FAYING_REQUEST auf die HP-Bezeugung wartet (Standard 60 s) |
| RevocationVisibilityBudget | Budget, bis ein Widerruf im RR-Netzwerk sichtbar ist (Standard 1 s) |
| StaleBudget | RR-Unerreichbarkeits-Ablehnungsschwelle (Standard 5 s) |
| HumanReachabilityBudget | Schwelle, bei der HP-Unerreichbarkeit einen Auto-Revoke auslöst (Standard 30 min) |
| LivenessDetectionBudget | Obergrenze des Trennungserkennungsfensters; je nach Stufe monoton verschärft (siehe Anhang B, P17.3) |
| AttentionDriftThreshold | Schwelle, bei der HP-Sicht-Inaktivität „Aufmerksamkeitsverlust“ auslöst; je nach Stufe verschärft (siehe Anhang B, P18.4) |
| ConfirmationRateLimit | Obergrenze der pro Zeiteinheit an den HP gepushten Bestätigungsanfragen; ein Überschreiten löst eine Auto-Herabstufung / -Suspendierung aus (siehe Anhang B, P18.6) |
| MaxDegradedDuration | Maximale Dauer des Degraded-Zustands (Standard 5 min/Stufe) |

---
