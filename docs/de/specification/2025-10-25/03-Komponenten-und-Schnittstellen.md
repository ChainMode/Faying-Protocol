---
title: "Faying Protocol/1.0 — §3 Komponenten und Schnittstellen"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: de
part: "Kapitel 3 von 11 (Protokolltext)"
---

> Protokolltext-Navigation: [Inhaltsverzeichnis](./README.md) | vorheriges [§2 Architektur](./02-Architektur.md) | nächstes [§4 Datenmodelle](./04-Datenmodelle.md)

## §3 Komponenten und Schnittstellen

Dieses Kapitel beschreibt die 6 Kernkomponenten der Faying-Protocol-Ebene: **Mandate Service (MS) / Presence Channel (PC) / Attestation Chain (AC) / Revocation Registry (RR) / Liveness Channel (LC) / Behavior Baseline Service (BBS)**. Zu jeder Komponente liefert das Kapitel:

- **Zuständigkeiten**: die Position und die Grenze der Komponente im Protokoll;
- **TypeScript-Schnittstellengerüst**: eine menschenlesbare Ansicht (**Non-normative**); die maßgeblichen Definitionen liegen in §4 Datenmodelle und §5 Protokollnachrichten;
- **Invarianten**: harte Bedingungen auf Protokollebene, die stets gelten müssen; jede Invariante ist auf mindestens eine EARS-Teilklausel der Anforderungen rückverfolgbar.

> **Hinweis zur EARS-Rückverfolgbarkeit**: Jeder Invariante in diesem Kapitel folgt eine `Trace:`-Zeile, die die zugehörigen EARS-Teilklausel-IDs (aus der Anforderungsbasis) in der Form `R<requirement>.<criterion>.<clause>` auflistet.

### §3.0 Vorabdeklarationen gemeinsamer Typen (Non-normative)

Damit die TypeScript-Schnittstellenblöcke dieses Kapitels eigenständig `tsc --noEmit` bestehen, deklariert der folgende Codeblock die in diesem Kapitel referenzierten Hilfstypen vorab in minimaler Gerüstform; die **maßgeblichen Definitionen** dieser Typen liegen in §4 Datenmodelle.

```typescript
// §3.0 — Non-normative Vorabdeklarationen.
// Maßgebliche Definitionen liegen in §4 Datenmodelle.

export type IsoTime = string;
export type MandateId = string;
export type FayID = string;
export type HumanPrimeID = string;
export type DeviceId = string;

export type AuthorizationGrade = "G0" | "G1" | "G2" | "G3" | "G4";

export interface Scope {
  readonly domains: readonly string[];
  readonly actions: readonly string[];
  readonly terminals?: readonly string[];
  readonly budget?: ResourceBudget;
}

export interface ResourceBudget {
  readonly max_calls_per_minute?: number;
  readonly max_bytes_per_call?: number;
}

export interface Grade {
  readonly value: AuthorizationGrade;
  readonly autonomy: number; // größerer Wert = höhere Autonomie (G0 niedrigste, G4 höchste)
}

export interface PresenceRequirement {
  readonly signal_types: readonly PresenceSignalType[];
  readonly max_staleness_ms: number;
  readonly on_loss: "downgrade" | "suspend";
}

export type PresenceSignalType =
  | "webauthn-uv-fresh"
  | "face-continuous"
  | "fingerprint-tap"
  | "presence-heartbeat-only"
  | "intent-ticket";

export interface SignatureBundle {
  readonly alg: string;
  readonly hash: string;
  readonly sig: Uint8Array;
  readonly chain?: readonly SignatureBundle[];
}

export interface Endorsement {
  readonly enabled: boolean;
  readonly endorsed_scope: Scope;
  readonly endorsed_grade: Grade;
  readonly endorsed_lifetime_ms: number;
  readonly offline_revocation_policy:
    | "stop-and-audit"
    | "stop-only"
    | "graceful-stop";
  readonly start_at?: IsoTime;
}

export interface Mandate {
  readonly mandate_id: MandateId;
  readonly issuer: HumanPrimeID;
  readonly subject: FayID;
  readonly scope: Scope;
  readonly grade: Grade;
  readonly presence_req: PresenceRequirement;
  readonly device_id?: DeviceId;
  readonly not_before: IsoTime;
  readonly not_after: IsoTime;
  readonly parent?: MandateId;
  readonly endorsement?: Endorsement;
  readonly signature_bundle: SignatureBundle;
}

export interface PresenceSignal {
  readonly mandate_id: MandateId;
  readonly signal_type: PresenceSignalType;
  readonly nonce: Uint8Array;
  readonly produced_at: IsoTime;
  readonly device_attestation: Uint8Array;
  readonly challenge?: Uint8Array;
  readonly challenge_response?: Uint8Array;
  readonly signature_bundle: SignatureBundle;
}

export interface PresenceVerdict {
  readonly accepted: boolean;
  readonly verdict: "ok" | "stale" | "replay" | "attestation-invalid";
  readonly recommended_next_grade?: AuthorizationGrade;
}

export interface PresenceAck {
  readonly accepted: boolean;
  readonly mandate_id: MandateId;
  readonly observed_at: IsoTime;
}

export interface PresenceState {
  readonly mandate_id: MandateId;
  readonly last_freshness: IsoTime;
  readonly stale: boolean;
  readonly active_signal_types: readonly PresenceSignalType[];
}

export interface BootstrapRequest {
  readonly subject: FayID;
  readonly scope: Scope;
  readonly grade: Grade;
  readonly presence_req: PresenceRequirement;
  readonly not_before: IsoTime;
  readonly not_after: IsoTime;
  readonly human_witness: Uint8Array; // WebAuthn-Assertion
  readonly endorsement?: Endorsement;
  readonly faying_request_ref?: string;
}

export interface GradeSwitchRequest {
  readonly mandate_id: MandateId;
  readonly target_grade: Grade;
  readonly current_grade: Grade;
  readonly human_witness?: Uint8Array;
  readonly reason: string;
}

export interface DelegateRequest {
  readonly parent_mandate_id: MandateId;
  readonly child_subject: FayID;
  readonly child_scope: Scope;
  readonly child_grade: Grade;
  readonly device_id?: DeviceId;
  readonly not_before: IsoTime;
  readonly not_after: IsoTime;
}

export type RevokeReason =
  | "human-initiated"
  | "expiry"
  | "task-completed"
  | "human-prime-unreachable"
  | "ego-deviation"
  | "fay-credential-invalid"
  | "human-prime-credential-invalid"
  | "regulatory-order"
  | "terminal-disconnected";

export interface RevokeRequest {
  readonly mandate_id: MandateId;
  readonly reason: RevokeReason;
  readonly cascade: boolean;
  readonly human_witness?: Uint8Array;
}

export interface RevokeReceipt {
  readonly mandate_id: MandateId;
  readonly reason: RevokeReason;
  readonly revoked_at: IsoTime;
  readonly cascade_targets: readonly MandateId[];
  readonly signature_bundle: SignatureBundle;
}

export interface RevocationStatus {
  readonly mandate_id: MandateId;
  readonly revoked: boolean;
  readonly revoked_at?: IsoTime;
  readonly reason?: RevokeReason;
  readonly observed_at: IsoTime;
}

export interface ScopeFilter {
  readonly subjects?: readonly FayID[];
  readonly issuers?: readonly HumanPrimeID[];
}

export interface Subscription {
  readonly subscription_id: string;
  readonly close: () => void;
}

export interface AtomicAction {
  readonly action: string;
  readonly target?: string;
  readonly sensitivity: "low" | "normal" | "high" | "critical";
}
```

### §3.1 Mandate Service (MS)

**Zuständigkeiten**: verwaltet im Namen des Human Prime den vollständigen Lebenszyklus von Mandates (Ausstellen / Erneuern / Herabstufen / Widerrufen); der alleinige legitime Einstiegspunkt für Faying Actions.

**Schnittstelle (Non-normative)**:

```typescript
export interface MandateService {
  /** Alleiniger legitimer Einstiegspunkt für Faying Actions */
  bootstrap(req: BootstrapRequest): Promise<Mandate>;

  /** Kalibrierung des Präsenzsignals; liefert, ob das aktuelle Mandate gültig bleibt / herabgestuft werden soll */
  verifyPresence(
    mandateId: MandateId,
    signal: PresenceSignal
  ): Promise<PresenceVerdict>;

  /** Stufenwechsel: Höherstufungen erfordern eine HP-Bezeugung; Herabstufungen dürfen vom Protokoll automatisch ausgelöst werden */
  switchGrade(req: GradeSwitchRequest): Promise<Mandate>;

  /** Geräteübergreifende Ableitung: leitet aus einem Eltern-Mandate ein Kind-Mandate ab, mit scope ⊆ parent scope, grade ≤ parent grade */
  delegate(req: DelegateRequest): Promise<Mandate>;

  /** Symmetrischer Widerruf: Erreichbarkeit muss ≥ Bootstrap sein */
  revoke(req: RevokeRequest): Promise<RevokeReceipt>;
}
```

**Schlüsselinvarianten**:

- **I-MS-1 (HP-verankerter Bootstrap)**: Ein `bootstrap()`-Aufrufer muss eine überprüfbare HP-Attestation tragen (Standardform: WebAuthn-Benutzerpräsenz-Aussage); es existiert kein legitimer Pfad für „MS-Selbstentscheidung über Bootstrap“ oder für IF / SA, um HP beim Abschluss der Bestätigung zu ersetzen.
  - **Trace**: `R1.3.1` (HP-initiiert muss eine überprüfbare ausdrückliche Bestätigung vorlegen), `R1.3.5` (kein bereitgestellter Pfad für IF / MS / SA, um HP beim Abschluss der Faying-Bestätigung zu ersetzen).

- **I-MS-2 (zwingende HP-Bezeugung bei Höherstufungen)**: `switchGrade()` muss genau dann eine überprüfbare `human_witness` tragen, wenn `target.autonomy > current.autonomy`; fehlende oder ungültige Signatur → Ablehnung mit `E_HUMAN_WITNESS_REQUIRED`, und IF darf Höherstufungen nicht autonom initiieren.
  - **Trace**: `R7.1.1` (`child.scope ⊆ parent.scope`-Konvergenz — impliziert die Nicht-Erweiterungsbedingung innerhalb der Stufen-Auf-/Abwärtssemantik, im Einklang mit dem Herabstufungs-Monotonie-Prinzip), `R5.1.1` (Akzeptanz-Vorbedingung auf Basis von `presence_req`, die Grundlage, auf der die RP verifiziert, nachdem `switchGrade` das Feld `presence_req` geschrieben hat).
  - Hinweis: Diese Invariante wird zudem maßgeblich durch R6.1 abgedeckt (Höherstufungen müssen eine HP-Bezeugung tragen); die in diesem Kapitel aufgeführte EARS-Rückverfolgbarkeit greift nur die relevanten Klauseln innerhalb der von dieser Aufgabe deklarierten Anforderungsmenge auf.

- **I-MS-3 (Budget für die Widerrufssichtbarkeit)**: Sobald ein `revoke()` von der RR veröffentlicht ist, müssen alle nachfolgenden RP-`query()`-Aufrufe innerhalb von `RevocationVisibilityBudget` (Standard 1 s, je nach Stufe verschärft; siehe §6 / Anhang B) `revoked` zurückgeben; MS darf keinen „optimistischen Durchwink“-Pfad bereitstellen.
  - **Trace**: `R4.2.1` (Budget für die Widerrufssichtbarkeit ≤ `RevocationVisibilityBudget`), `R4.2.4` (keine Bestätigung innerhalb von `StaleBudget` → Default-Deny).

- **I-MS-4 (strikt konvergierender abgeleiteter scope / grade)**: Ein durch `delegate()` ausgestelltes Kind-Mandate muss `child.scope ⊆ parent.scope` ∧ `child.grade.autonomy ≤ parent.grade.autonomy` erfüllen; jede Erweiterung in eine der beiden Richtungen wird mit `E_PROTOCOL` abgelehnt, und das `signature_bundle.chain` des Kind-Mandate muss die Gegensignatur des Eltern-Mandate tragen.
  - **Trace**: `R7.1.1` (child scope ⊆ parent scope), `R7.1.2` (child autonomy ≤ parent autonomy).

### §3.2 Presence Channel (PC)

**Zuständigkeiten**: liefert die von Presence Devices erzeugten physischen Präsenzsignale sicher, latenzarm und replay-resistent an MS, wo MS sie in „kontinuierliche Kalibrierungs“-Urteile über das aktuelle Mandate überführt.

**Signaltypen (auf die Stufen aus §7 abgestimmt)**:

| Typ | Stärke | Anwendbare Stufe | Herabstufungspfad bei Fehlschlag |
| --- | --- | --- | --- |
| `webauthn-uv-fresh` | Stark | G1 Strict | Fehlschlag → Suspended |
| `face-continuous` | Stark | G1 Strict | Fehlschlag → Herabstufung auf G2 Moderate |
| `fingerprint-tap` | Mittel | G2 Moderate | Fehlschlag → Herabstufung auf G3 Loose |
| `presence-heartbeat-only` | Schwach | G3 Loose / G4 Autonomous | Fehlschlag → Suspended |
| `intent-ticket` | Einmalig | Stufenübergreifende Ergänzung | Einmalig nutzbar; beeinflusst die Hauptstufe nicht |

**Schnittstelle (Non-normative)**:

```typescript
export interface PresenceChannel {
  /** PD-initiiert; MS verifiziert und schreibt in den PresenceState des zugehörigen Mandate */
  push(signal: PresenceSignal): Promise<PresenceAck>;

  /** Die RP fragt vor jedem Aufruf ab, ob die aktuelle Presence frisch ist */
  query(mandateId: MandateId): Promise<PresenceState>;
}
```

**Schlüsselinvarianten**:

- **I-PC-1 (zwingendes Dreitupel je Signal + mandate-seitiges Frischefenster)**: Jedes `PresenceSignal` muss ausdrücklich `nonce + produced_at + device_attestation` tragen, signiert von Presence_Device; das Frischefenster wird **nicht vom Signal getragen**, sondern durch `presence_req.max_staleness_ms` des zugehörigen Mandate vorgegeben (an die Stufe gebunden, zum BOOTSTRAP-Zeitpunkt vom HP verankert, je Stufe durch `LivenessDetectionBudget` verschärft). Signale mit `produced_at + presence_req.max_staleness_ms < now` gelten einheitlich als veraltet.
  - **Trace**: `R5.1.3` (Felder `nonce / produced_at / device_attestation` sind zwingend), `R5.1.4` (PC weist während der Verifikationsphase abgelaufene Signale ab).

- **I-PC-2 (Einmalnutzung je nonce)**: Dasselbe `(subject, nonce)` wird innerhalb eines TTL-Fensters von `2 × max_message_lifetime` höchstens einmal akzeptiert; wiederholter Verbrauch → Ablehnung mit `E_REPLAY`.
  - **Trace**: `R5.1.1` (`last_freshness` muss die Frische erfüllen — impliziert, dass die nonce-+-Zeitstempel-Anti-Replay-Semantik auf der PC-Ebene landet), `R5.1.3` (das Feld `nonce` ist der Protokoll-Handle für Anti-Replay).

- **I-PC-3 (Präsenzfrische verschärft sich automatisch)**: `PresenceState.last_freshness` muss ≥ `now − presence_req.max_staleness_ms` sein; schlägt dies fehl, muss PC den nächsten Zustandsübergang nach `Degraded(grade')` (`grade'.autonomy < current.autonomy`) oder `Suspended` wandern lassen; das Verbleiben auf der ursprünglichen Stufe ist verboten, das Umschalten zu höherer Autonomie ist verboten.
  - **Trace**: `R5.1.1` (Akzeptanz-Vorbedingung `last_freshness ≥ t − max_staleness_ms`), `R12.2.2` (die Frische — nicht die Heartbeat-Polling-Periode — als Grundlage für das Durchlassen von Aufrufen verwenden).

### §3.3 Attestation Chain (AC)

**Zuständigkeiten**: organisiert alle Ausstellungsaktionen HP → MS → IF → abgeleitete IF zu einer rückwärts verfolgbaren Signaturkette, sodass jedes einzelne Mandate von einem unabhängigen Dritten bis zu seiner Autorisierungsquelle rekonstruiert werden kann.

**Kettenstruktur (illustrativ)**:

```
Root: HP-Public-Key (selbst gehostet / an WebAuthn-Berechtigungen verankert)
  └─ MS-Cert (HP-signiert, bindet MS-Public-Key an Berechtigungen)
       └─ Mandate M1 (MS-signiert)
            ├─ Mandate M2 (abgeleitet aus M1, MS-Gegensignatur + Eltern-Mandate-Gegensignatur)
            └─ Mandate M3 (abgeleitet aus M1)
```

**Schnittstelle (Non-normative)**:

```typescript
export interface AttestationChain {
  /** Verifiziert die vollständige Kette vom Blatt bis zur Wurzel */
  verify(mandate: Mandate): Promise<AttestationVerifyResult>;

  /** Hängt ein einzelnes Kettenereignis an (Bootstrap / GradeSwitch / Delegate / Revoke) */
  append(event: AttestationEvent): Promise<void>;

  /** Löst den Verantwortungsendpunkt des angegebenen Mandate auf */
  resolveAccountableParty(mandateId: MandateId): Promise<HumanPrimeID>;
}

export interface AttestationVerifyResult {
  readonly verified: boolean;
  readonly root: HumanPrimeID;
  readonly invalid_node?: string;
}

export interface AttestationEvent {
  readonly event_type: "bootstrap" | "grade-switch" | "delegate" | "revoke";
  readonly mandate_id: MandateId;
  readonly issuer: HumanPrimeID;
  readonly subject: FayID;
  readonly ts: IsoTime;
  readonly signature_bundle: SignatureBundle;
}
```

**Schlüsselinvarianten**:

- **I-AC-1 (Doppelbedingung Eltern-Signatur + Gültigkeitsfenster)**: Jeder Knoten der Kette muss von seinem Elternknoten signiert sein, und der Signaturzeitstempel muss in das Gültigkeitsfenster des Elternknotens fallen (`[parent.not_before, parent.not_after]`); jeder Fehlschlag → Ablehnung mit `E_ATTESTATION_INVALID` und Auslösung des Widerrufs des zugehörigen Mandate.
  - **Trace**: `R3.1.2` (Verifikation vom Blatt zur Wurzel, mit Zeitstempeln innerhalb des Gültigkeitsfensters des Elternknotens), `R3.1.3` (jeder fehlschlagende Knoten → Ablehnung mit `E_ATTESTATION_INVALID` und Auslösung des Widerrufs).

- **I-AC-2 (Kettenintegrität, kein Knoten darf fehlen)**: Die Kettenverifikation muss an jedem Knoten vom Blatt bis zur Wurzel bestehen; jeder fehlende oder signaturungültige Knoten gilt als nicht vertrauenswürdig, und die gesamte Kette liefert `verified = false`.
  - **Trace**: `R3.1.1` (die vier Ereignistypen `Bootstrap / GradeSwitch / Delegate / Revoke` müssen in die Kette gelangen), `R3.1.2` (die Kettenverifikation liefert `verify = true` nur, wenn alle Knoten gültig sind).

- **I-AC-3 (Ableitungskonvergenz ist auf der Kette irreversibel nicht-lockernd)**: Bei der Ableitung müssen `scope` und `grade.autonomy` des Kindknotens monoton konvergieren; kein abgeleiteter Knoten, der den scope lockert oder die Autonomie anhebt, besitzt einen legitimen Signaturpfad auf der Kette.
  - **Trace**: `R7.1.1` (child scope ⊆ parent scope), `R7.1.2` (child autonomy ≤ parent autonomy).

### §3.4 Revocation Registry (RR)

**Zuständigkeiten**: Echtzeit-Widerrufsstatusdienst. Trägt den Engineering-Angelpunkt des Symmetrieprinzips „Widerrufserreichbarkeit ≥ Etablierungserreichbarkeit“.

**Zweigleisiges Design**:

- **Pull**: Die RP führt bei jedem akzeptierten Aufruf ein Kurz-Polling durch (OCSP-ähnlich, Stapling empfohlen);
- **Push**: Nach einem MS-Widerruf erfolgt ein Push an alle abonnierten RPs (WebSocket / SSE / MQTT);
- **Konservatives Fallback**: Kann die RP den RR-Status nicht innerhalb von `StaleBudget` (Standard 5 s, je nach Stufe verschärft) bestätigen, muss sie den Aufruf per Default-Deny ablehnen.

**Schnittstelle (Non-normative)**:

```typescript
export interface RevocationRegistry {
  publish(receipt: RevokeReceipt): Promise<void>;
  query(mandateId: MandateId): Promise<RevocationStatus>;
  subscribe(rpId: string, scope: ScopeFilter): Subscription;
}
```

**Schlüsselinvarianten**:

- **I-RR-1 (Widerrufsveröffentlichung ist sofort sichtbar)**: Sobald `publish()` abgeschlossen ist, müssen alle nachfolgenden `query()`-Aufrufe innerhalb von `RevocationVisibilityBudget` (Standard 1 s, je nach Stufe verschärft) sofort `revoked = true` zurückgeben und damit eine Strong-Consistency-Semantik aufweisen.
  - **Trace**: `R4.2.1` (innerhalb von `RevocationVisibilityBudget` liefert `query` `revoked`).

- **I-RR-2 (unerreichbar → Default-Deny)**: Ist die RR für ≥ `StaleBudget` unerreichbar, muss die RP Aufrufe mit `E_RR_UNAVAILABLE` ablehnen; ein „optimistischer Durchwink“ ist verboten.
  - **Trace**: `R2.1.4` (unerreichbar innerhalb von `StaleBudget` → Default-Deny + `E_RR_UNAVAILABLE`), `R4.2.4` (die RP behandelt ein Fehlschlagen der Statusbestätigung als Default-Deny).

> **Semantische Grenze**: RR unerreichbar ≠ eigene Trennung der iFay. RR unerreichbar bedeutet nur „lässt sich nicht feststellen, ob das Mandate widerrufen wurde“ und löst eine `E_RR_UNAVAILABLE`-Ablehnung aus; die Trennung der iFay (einschließlich Actually-Disconnected / Perceived-Disconnected) wird separat durch §3.5 Liveness Channel und PresenceState charakterisiert. Die beiden Trennungs-Ereignisklassen ersetzen einander nicht — es existieren die orthogonalen Kombinationen „iFay online, aber RR unerreichbar“ und „RR online, aber iFay getrennt“, und die Protokollebene konvergiert beide zu Default-Deny.

### §3.5 Liveness Channel (LC)

**Zuständigkeiten**: beurteilt mittels ressourcenschonendem Heartbeat + Präsenzfrische gemeinsam die „wahrgenommene Lebendigkeit“ einer iFay_Instance aus der Perspektive von MS / RP / HP und charakterisiert das Inkonsistenzfenster zwischen „tatsächlicher Lebendigkeit“ und „wahrgenommener Lebendigkeit“ ausdrücklich als erstklassigen Bestandteil der Protokollebene.

**Definition der Doppelsemantik**:

- **Actually-Disconnected**: Der Prozess / das Netzwerk / das Gerät der iFay_Instance hat die Arbeit eingestellt oder ist für keine externe Partei erreichbar. Eine objektive physische Tatsache, auf der Protokollebene nicht direkt beobachtbar.
- **Perceived-Disconnected**: Aus der Perspektive von MS / RP / HP wird die iFay_Instance auf Basis des jüngsten Presence_Signal, Heartbeats und RR-Push-Zustands als getrennt beurteilt. **Die einzige Semantik, die die Protokollebene als Entscheidungsgrundlage heranziehen darf.**

**Zwei Inkonsistenzfenster**:

- **Fenster A — Actually-Disconnected ∧ Perceived-Connected**: Die iFay ist tatsächlich abgefallen, doch das jüngste Presence_Signal liegt noch innerhalb von `max_staleness_ms` → ein „Beobachtungs-Blindfleck“ innerhalb des Heartbeat-Intervalls;
- **Fenster B — Actually-Connected ∧ Perceived-Disconnected**: Die iFay ist tatsächlich online, doch das jüngste Presence_Signal überschreitet `max_staleness_ms` (Netzwerk-Jitter / Heartbeat-Verlust) → die Protokollebene konvergiert über eine pessimistische Annahme.

**Prinzip der pessimistischen Annahme (einheitliche Konvergenzregel)**:

> Die Protokollebene zieht ausschließlich Perceived-Disconnected als Entscheidungsgrundlage heran; keine iFay_Instance, die „tatsächlich online, aber als getrennt wahrgenommen“ ist, darf sich dadurch von den Konsequenzen der Protokollebene befreien. Innerhalb der beiden Inkonsistenzfenster muss das Protokoll nach „der strikteren Seite“ verarbeiten; es existiert kein legitimer Pfad für „Verarbeitung nach dem nachgiebigeren Zustand“.

**Schnittstelle (Non-normative; teilt sich die zugrunde liegenden Signale mit §3.2 PC)**:

```typescript
export interface LivenessChannel {
  /** Momentaufnahme der aktuell wahrgenommenen Lebendigkeit */
  perceived(mandateId: MandateId): PerceivedLiveness;

  /** Löst ausdrücklich ein pessimistisches Urteil aus (z. B. bei erkanntem Heartbeat-Verlust) */
  declareStale(mandateId: MandateId, reason: string): Promise<void>;
}

export interface PerceivedLiveness {
  readonly is_perceived_connected: boolean;
  readonly last_freshness: IsoTime;
  readonly staleness_ms: number;
  readonly decided_by: "presence-signal" | "heartbeat" | "explicit-declare";
}
```

**Schlüsselinvarianten**:

- **I-LC-1 (frische-basiertes Urteil; das Durchlassen anhand der Heartbeat-Polling-Periode ist verboten)**: Urteile über die wahrgenommene Trennung müssen auf `last_freshness ≥ now − max_staleness_ms` beruhen; „die Heartbeat-Polling-Periode ist noch nicht abgelaufen“ darf nicht als Grund herangezogen werden, Aufrufe weiter durchzulassen.
  - **Trace**: `R12.2.2` (die Frische — nicht die Heartbeat-Polling-Periode — als Grundlage für das Durchlassen von Aufrufen verwenden).

- **I-LC-2 (Zustandsmaschinen-Übergang nach Disconnected)**: Sobald als Perceived-Disconnected beurteilt, muss der nächste Zustandsübergang der Zustandsmaschine aus §4.3 folgen (Active → Disconnected / Active → Suspended, je nachdem, ob ein gültiges Endorsed_Mandate vorliegt); es existiert kein legitimer Pfad für das Verbleiben im ursprünglichen Zustand oder das Umschalten zu einem nachgiebigeren Zustand.
  - **Trace**: `R12.1.3` (ausschließlich die wahrgenommene Trennung als Entscheidungsgrundlage der Protokollebene heranziehen; nicht von den Konsequenzen der Protokollebene befreien).

- **I-LC-3 (Wiederherstellung erfordert eine transaktionale Abgleichung)**: Die Wiederherstellung von Perceived-Disconnected nach Perceived-Connected muss die Abgleichstransaktion aus §8.4 durchlaufen; eine automatische Wiederherstellung ist verboten.
  - **Trace**: `R12.1.3` (keine Befreiung von den Konsequenzen der Protokollebene während der wahrgenommenen Trennung — impliziert, dass „die Wiederherstellung eine ausdrückliche transaktionale Bestätigung erfordert“, im Einklang mit den Abgleichstransaktionen in R12.4.1 / R12.4.3; innerhalb der von dieser Aufgabe deklarierten Anforderungsmenge ist dies an 12.1 verankert).

### §3.6 Behavior Baseline Service (BBS)

**Zuständigkeiten**: pflegt für jedes Paar (Human_Prime, iFay_Instance) ein kumulatives Verhaltensprofil; dient dazu, signifikante Abweichungen von der Baseline durch hochsensible Aktionen zu erkennen und bei Abweichung eine zusätzliche menschliche Bezeugung auszulösen (siehe §9.10.6 T5-Schutz).

**Schnittstelle (Non-normative)**:

```typescript
export interface BehaviorBaselineService {
  /** Akkumuliert ein neues Aktions-Sample */
  record(sample: BehaviorSample): Promise<void>;

  /** Bewertet die Abweichung der aktuellen Aktion relativ zur Baseline */
  evaluate(
    hp: HumanPrimeID,
    fay: FayID,
    action: AtomicAction
  ): BaselineDeviation;

  /** Wendet den Reputationszerfall an (Zerfall des Vertrauenswerts) */
  decay(hp: HumanPrimeID, fay: FayID): Promise<void>;
}

export interface BehaviorSample {
  readonly hp: HumanPrimeID;
  readonly fay: FayID;
  readonly action: AtomicAction;
  readonly scope_used: Scope;
  readonly risk_level: "low" | "normal" | "high" | "critical";
  readonly affected_resources: readonly string[];
  readonly ts: IsoTime;
}

export interface BaselineDeviation {
  readonly exceeds_threshold: boolean;
  readonly dimensions: readonly (
    | "risk_level"
    | "scope_used"
    | "affected_resources"
  )[];
  readonly recommended_action:
    | "allow"
    | "require-extra-witness"
    | "downgrade"
    | "suspend";
}
```

**Schlüsselinvarianten**:

- **I-BBS-1 (Vertrauenswert muss zerfallen und gedeckelt sein)**: Der „Vertrauenswert“ jedes Paares (HP, IF) muss über die Zeit zerfallen und eine ausdrückliche Obergrenze haben; eine unbegrenzte Akkumulation ist verboten, damit sie nicht die von künftigen hochsensiblen Aktionen geforderte menschliche Bezeugungsstärke verwässert.
  - **Trace**: `R13.5.3` (Action Reputation Decay: Vertrauenswert muss zerfallen und eine ausdrückliche Obergrenze haben).

- **I-BBS-2 (Über-Baseline-Bezeugungsereignisse gelangen in die Kette + Push an HP-Sicht)**: Jedes Ereignis „Über-Baseline löst zusätzliche Bezeugung aus“ muss in die Attestation_Chain geschrieben und an den Human_Prime-Sichtkanal gepusht werden; bevor die zusätzliche Bezeugung vorliegt, ist der Aufruf mit `E_HUMAN_WITNESS_REQUIRED` abzulehnen.
  - **Trace**: `R13.5.4` (Ereignis „Über-Baseline löst zusätzliche Bezeugung aus“ in die AC geschrieben + an HP-Sicht gepusht), `R13.5.2` (Ablehnung mit `E_HUMAN_WITNESS_REQUIRED`, bis die zusätzliche Bezeugung vorliegt).

- **I-BBS-3 (Kalibrierungsänderungen sind ebenfalls Audit-Ereignisse)**: Die Kalibrierung der Baseline-Berechnung selbst wird, einmal festgelegt, in die Attestation_Chain geschrieben; Kalibrierungsänderungen werden als eigene Klasse von Audit-Ereignis behandelt und vom Protocol Committee über den etablierten Prozess genehmigt.
  - **Trace**: `R13.5.1` (MS pflegt die Behavior_Baseline), `R3.1.1` (bei der Verarbeitung jedes Audit-Ereignisses muss die AC dessen signierten Knoten enthalten; die in diesem Kapitel aufgeführte EARS-Rückverfolgbarkeit greift nur die relevanten Klauseln innerhalb der von dieser Aufgabe deklarierten Anforderungsmenge auf).

---
