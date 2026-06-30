---
title: "Faying Protocol/1.0 — §3 Componentes e interfaces"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: es
part: "Capítulo 3 de 11 (cuerpo del protocolo)"
---

> Navegación del cuerpo del protocolo: [Índice](./README.md) | anterior [§2 Arquitectura](./02-Arquitectura.md) | siguiente [§4 Modelos de datos](./04-Modelos-de-Datos.md)

## §3 Componentes e interfaces

Este capítulo presenta los 6 componentes centrales de la capa de protocolo del Faying Protocol: **Mandate Service (MS) / Presence Channel (PC) / Attestation Chain (AC) / Revocation Registry (RR) / Liveness Channel (LC) / Behavior Baseline Service (BBS)**. Para cada componente, el capítulo proporciona:

- **Responsabilidades**: la posición y el límite del componente en el protocolo;
- **Esqueleto de interfaz TypeScript**: una vista legible por humanos (**No normativa**); las definiciones autoritativas residen en §4 Modelos de datos y §5 Mensajes del protocolo;
- **Invariantes**: restricciones duras a nivel de protocolo que deben cumplirse siempre; cada invariante es trazable a al menos una subcláusula EARS en §Requirements.

> **Nota sobre la trazabilidad EARS**: cada invariante de este capítulo va seguida de una línea `Trace:` que enumera los identificadores de subcláusula EARS correspondientes (de la base de requisitos) con la forma `R<requirement>.<criterion>.<clause>`.

### §3.0 Declaraciones anticipadas de tipos compartidos (No normativo)

Para que los bloques de interfaz TypeScript de este capítulo puedan pasar de forma independiente `tsc --noEmit`, el bloque de código siguiente declara anticipadamente, en forma de esqueleto mínimo, los tipos de apoyo referenciados en este capítulo; las **definiciones autoritativas** de estos tipos residen en §4 Modelos de datos.

```typescript
// §3.0 — Declaraciones anticipadas no normativas.
// Las definiciones autoritativas residen en §4 Modelos de datos.

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
  readonly autonomy: number; // valor mayor = mayor autonomía (G0 la más baja, G4 la más alta)
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
  readonly human_witness: Uint8Array; // aserción WebAuthn
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

**Responsabilidades**: gestiona el ciclo de vida completo de los Mandates en nombre del Human Prime (emitir / renovar / degradar / revocar); el único punto de entrada legítimo para las Faying Actions.

**Interfaz (No normativa)**:

```typescript
export interface MandateService {
  /** Único punto de entrada legítimo para las Faying Actions */
  bootstrap(req: BootstrapRequest): Promise<Mandate>;

  /** Calibración de la señal de presencia; devuelve si el Mandate actual sigue siendo válido / debe degradarse */
  verifyPresence(
    mandateId: MandateId,
    signal: PresenceSignal
  ): Promise<PresenceVerdict>;

  /** Conmutación de nivel: las elevaciones requieren testimonio del HP; las degradaciones pueden ser disparadas automáticamente por el protocolo */
  switchGrade(req: GradeSwitchRequest): Promise<Mandate>;

  /** Derivación entre dispositivos: deriva un Mandate hijo de un Mandate padre, con scope ⊆ scope del padre, grade ≤ grade del padre */
  delegate(req: DelegateRequest): Promise<Mandate>;

  /** Revocación simétrica: la alcanzabilidad debe ser ≥ bootstrap */
  revoke(req: RevokeRequest): Promise<RevokeReceipt>;
}
```

**Invariantes clave**:

- **I-MS-1 (Bootstrap anclado en el HP)**: un solicitante de `bootstrap()` debe portar una atestación del HP verificable (forma predeterminada: aserción de presencia de usuario WebAuthn); no existe vía legítima para «MS decidir el bootstrap por sí mismo» ni para que IF / SA sustituyan al HP en completar el reconocimiento.
  - **Trace**: `R1.3.1` (lo iniciado por HP debe presentar un reconocimiento explícito verificable), `R1.3.5` (no se proporciona vía para que IF / MS / SA sustituyan al HP en completar el reconocimiento Faying).

- **I-MS-2 (testimonio del HP obligatorio en las elevaciones)**: `switchGrade()` debe portar un `human_witness` verificable si y solo si `target.autonomy > current.autonomy`; ausencia o firma inválida → rechazo con `E_HUMAN_WITNESS_REQUIRED`, y el IF no debe iniciar elevaciones de nivel de forma autónoma.
  - **Trace**: `R7.1.1` (convergencia `child.scope ⊆ parent.scope` — implica la restricción de no expansión dentro de la semántica de subida/bajada de nivel, coherente con el principio de monotonía de degradación), `R5.1.1` (precondición de aceptación basada en `presence_req`, base sobre la que el RP verifica tras que `switchGrade` escriba el campo `presence_req`).
  - Nota: esta invariante también está cubierta autoritativamente por R6.1 (las elevaciones deben portar testimonio del HP); la trazabilidad EARS enumerada en este capítulo toma solo las cláusulas pertinentes dentro del conjunto de Requirements declarado por esta tarea.

- **I-MS-3 (presupuesto de visibilidad de la revocación)**: una vez que un `revoke()` es publicado por el RR, todas las llamadas `query()` posteriores del RP deben devolver `revoked` dentro de `RevocationVisibilityBudget` (predeterminado 1 s, ajustado por nivel; véase §6 / Anexo B); el MS no debe proporcionar una vía de «paso optimista».
  - **Trace**: `R4.2.1` (presupuesto de visibilidad de la revocación ≤ `RevocationVisibilityBudget`), `R4.2.4` (sin confirmación dentro de `StaleBudget` → Default-Deny).

- **I-MS-4 (alcance / nivel derivados que convergen estrictamente)**: un Mandate hijo emitido por `delegate()` debe satisfacer `child.scope ⊆ parent.scope` ∧ `child.grade.autonomy ≤ parent.grade.autonomy`; cualquier expansión en cualquier dirección se rechaza con `E_PROTOCOL`, y el `signature_bundle.chain` del Mandate hijo debe portar la contrafirma del Mandate padre.
  - **Trace**: `R7.1.1` (scope del hijo ⊆ scope del padre), `R7.1.2` (autonomía del hijo ≤ autonomía del padre).

### §3.2 Presence Channel (PC)

**Responsabilidades**: entrega, con baja latencia y resistencia a repetición, las señales de presencia física producidas por los Presence Devices al MS, donde el MS las convierte en veredictos de «calibración continua» sobre el Mandate actual.

**Tipos de señal (alineados con los niveles de §7)**:

| Tipo | Intensidad | Nivel aplicable | Vía de degradación en caso de fallo |
| --- | --- | --- | --- |
| `webauthn-uv-fresh` | Fuerte | G1 Strict | Fallo → Suspended |
| `face-continuous` | Fuerte | G1 Strict | Fallo → degradar a G2 Moderate |
| `fingerprint-tap` | Media | G2 Moderate | Fallo → degradar a G3 Loose |
| `presence-heartbeat-only` | Débil | G3 Loose / G4 Autonomous | Fallo → Suspended |
| `intent-ticket` | De un solo uso | Suplemento entre niveles | De un solo uso; no afecta al nivel principal |

**Interfaz (No normativa)**:

```typescript
export interface PresenceChannel {
  /** Iniciada por el PD; el MS verifica y escribe en el PresenceState del Mandate correspondiente */
  push(signal: PresenceSignal): Promise<PresenceAck>;

  /** El RP consulta antes de cada llamada si la Presence actual está fresca */
  query(mandateId: MandateId): Promise<PresenceState>;
}
```

**Invariantes clave**:

- **I-PC-1 (tripleta obligatoria por señal + ventana de frescura del lado del Mandate)**: toda `PresenceSignal` debe portar explícitamente `nonce + produced_at + device_attestation`, firmada por el Presence_Device; la ventana de frescura **no la porta la señal** sino que la da el `presence_req.max_staleness_ms` del Mandate correspondiente (ligado al nivel, anclado por el HP en BOOTSTRAP, ajustado por `LivenessDetectionBudget` por nivel). Las señales con `produced_at + presence_req.max_staleness_ms < now` se tratan uniformemente como obsoletas.
  - **Trace**: `R5.1.3` (los campos `nonce / produced_at / device_attestation` son obligatorios), `R5.1.4` (el PC rechaza las señales caducadas durante la fase de verificación).

- **I-PC-2 (un solo uso por nonce)**: el mismo `(subject, nonce)` se acepta como máximo una vez dentro de una ventana TTL de `2 × max_message_lifetime`; consumo repetido → rechazo con `E_REPLAY`.
  - **Trace**: `R5.1.1` (`last_freshness` debe satisfacer la frescura — implica que la semántica anti-replay de nonce + marca de tiempo aterriza en la capa PC), `R5.1.3` (el campo `nonce` es el asidero a nivel de protocolo para el anti-replay).

- **I-PC-3 (la frescura de presencia se ajusta automáticamente)**: `PresenceState.last_freshness` debe ser ≥ `now − presence_req.max_staleness_ms`; cuando esto falla, el PC debe hacer que la siguiente transición de estado migre a `Degraded(grade')` (`grade'.autonomy < current.autonomy`) o `Suspended`; permanecer en el nivel original está prohibido, conmutar hacia mayor autonomía está prohibido.
  - **Trace**: `R5.1.1` (precondición de aceptación `last_freshness ≥ t − max_staleness_ms`), `R12.2.2` (usar la frescura — no el periodo de sondeo del heartbeat — como base para dejar pasar las llamadas).

### §3.3 Attestation Chain (AC)

**Responsabilidades**: organiza todas las acciones de emisión de HP → MS → IF → IF derivado en una cadena de firmas trazable en reverso, de modo que cualquier Mandate individual pueda ser reconstruido por un tercero independiente hasta su fuente de autorización.

**Estructura de la cadena (ilustrativa)**:

```
Root: HP-Public-Key (self-hosted / anchored to WebAuthn credentials)
  └─ MS-Cert (HP-signed, binds MS public key with permissions)
       └─ Mandate M1 (MS-signed)
            ├─ Mandate M2 (derived from M1, MS countersign + parent Mandate countersign)
            └─ Mandate M3 (derived from M1)
```

**Interfaz (No normativa)**:

```typescript
export interface AttestationChain {
  /** Verifica la cadena completa de hoja a raíz */
  verify(mandate: Mandate): Promise<AttestationVerifyResult>;

  /** Anexa un único evento de cadena (Bootstrap / GradeSwitch / Delegate / Revoke) */
  append(event: AttestationEvent): Promise<void>;

  /** Resuelve el punto final que asume la responsabilidad del Mandate especificado */
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

**Invariantes clave**:

- **I-AC-1 (restricción dual de firma del padre + ventana de validez)**: cada nodo de la cadena debe estar firmado por su padre, y la marca de tiempo de la firma debe caer dentro de la ventana de validez del padre (`[parent.not_before, parent.not_after]`); cualquier fallo → rechazo con `E_ATTESTATION_INVALID` y disparo de Revoke del Mandate correspondiente.
  - **Trace**: `R3.1.2` (verificación de hoja a raíz, con marcas de tiempo dentro de la ventana de validez del nodo padre), `R3.1.3` (cualquier nodo que falle → rechazo con `E_ATTESTATION_INVALID` y disparo de Revoke).

- **I-AC-2 (integridad de la cadena, ningún nodo puede faltar)**: la verificación de la cadena debe pasar en cada nodo de hoja a raíz; cualquier nodo ausente o con firma inválida se trata como no confiable, y la cadena entera devuelve `verified = false`.
  - **Trace**: `R3.1.1` (los cuatro tipos de evento `Bootstrap / GradeSwitch / Delegate / Revoke` deben entrar en la cadena), `R3.1.2` (la verificación de la cadena devuelve `verify = true` solo cuando todos los nodos son válidos).

- **I-AC-3 (la convergencia de derivación no se relaja de forma irreversible en la cadena)**: durante la derivación, el `scope` y la `grade.autonomy` del nodo hijo deben converger monótonamente; ningún nodo derivado que relaje el alcance o eleve la autonomía tiene una vía de firma legítima en la cadena.
  - **Trace**: `R7.1.1` (scope del hijo ⊆ scope del padre), `R7.1.2` (autonomía del hijo ≤ autonomía del padre).

### §3.4 Revocation Registry (RR)

**Responsabilidades**: servicio de estado de revocación en tiempo real. Soporta el pivote de ingeniería del principio de simetría «alcanzabilidad de la revocación ≥ alcanzabilidad del establecimiento».

**Diseño de doble vía**:

- **Pull**: el RP realiza sondeo corto (tipo OCSP, se recomienda stapling) en cada llamada aceptada;
- **Push**: tras la revocación del MS, empuje a todos los RP suscritos (WebSocket / SSE / MQTT);
- **Reserva conservadora**: si el RP no puede confirmar el estado del RR dentro de `StaleBudget` (predeterminado 5 s, ajustado por nivel), debe rechazar la llamada por Default-Deny.

**Interfaz (No normativa)**:

```typescript
export interface RevocationRegistry {
  publish(receipt: RevokeReceipt): Promise<void>;
  query(mandateId: MandateId): Promise<RevocationStatus>;
  subscribe(rpId: string, scope: ScopeFilter): Subscription;
}
```

**Invariantes clave**:

- **I-RR-1 (la publicación de la revocación es inmediatamente visible)**: una vez que `publish()` se completa, todas las llamadas `query()` posteriores deben devolver inmediatamente `revoked = true` dentro de `RevocationVisibilityBudget` (predeterminado 1 s, ajustado por nivel), exhibiendo semántica de consistencia fuerte.
  - **Trace**: `R4.2.1` (dentro de `RevocationVisibilityBudget`, `query` devuelve `revoked`).

- **I-RR-2 (inalcanzable → Default-Deny)**: cuando el RR es inalcanzable durante ≥ `StaleBudget`, el RP debe rechazar las llamadas con `E_RR_UNAVAILABLE`; el «paso optimista» está prohibido.
  - **Trace**: `R2.1.4` (inalcanzable dentro de `StaleBudget` → Default-Deny + `E_RR_UNAVAILABLE`), `R4.2.4` (el RP trata el fallo de confirmación de estado como Default-Deny).

> **Frontera semántica**: RR inalcanzable ≠ desconexión propia del iFay. RR inalcanzable solo significa «no se puede determinar si el Mandate ha sido revocado», disparando el rechazo `E_RR_UNAVAILABLE`; la desconexión del iFay (incluidas Actually-Disconnected / Perceived-Disconnected) se caracteriza por separado mediante el Liveness Channel de §3.5 y PresenceState. Las dos categorías de evento de desconexión no se sustituyen entre sí — existen las combinaciones ortogonales «iFay en línea pero RR inalcanzable» e «RR en línea pero iFay desconectado», y la capa de protocolo converge ambas a Default-Deny.

### §3.5 Liveness Channel (LC)

**Responsabilidades**: juzga conjuntamente, mediante heartbeat de bajo coste + frescura de presencia, la «vitalidad percibida» de un iFay_Instance desde la perspectiva de MS / RP / HP, y caracteriza explícitamente la ventana de inconsistencia entre la «vitalidad real» y la «vitalidad percibida» como un ciudadano de primera clase a nivel de protocolo.

**Definición de semántica dual**:

- **Actually-Disconnected**: el proceso / la red / el dispositivo del iFay_Instance ha dejado de funcionar o no puede ser alcanzado por ninguna parte externa. Un hecho físico objetivo, no directamente observable a nivel de protocolo.
- **Perceived-Disconnected**: desde la perspectiva de MS / RP / HP, basándose en la Presence_Signal más reciente, el heartbeat y el estado de empuje del RR, se juzga que el iFay_Instance está desconectado. **La única semántica que la capa de protocolo puede usar como base de decisión.**

**Dos ventanas de inconsistencia**:

- **Ventana A — Actually-Disconnected ∧ Perceived-Connected**: el iFay realmente cayó, pero la Presence_Signal más reciente sigue dentro de `max_staleness_ms` → un «punto ciego de observación» dentro del intervalo del heartbeat;
- **Ventana B — Actually-Connected ∧ Perceived-Disconnected**: el iFay realmente está en línea, pero la Presence_Signal más reciente supera `max_staleness_ms` (jitter de red / pérdida de heartbeat) → la capa de protocolo converge por presunción pesimista.

**Principio de presunción pesimista (regla de convergencia unificada)**:

> La capa de protocolo usa únicamente Perceived-Disconnected como base de decisión; ningún iFay_Instance que esté «realmente en línea pero percibido como desconectado» puede reclamar exención de las consecuencias a nivel de protocolo por ello. Dentro de las dos ventanas de inconsistencia, el protocolo debe procesar por «el lado más estricto»; no existe vía legítima para «procesar por el estado más permisivo».

**Interfaz (No normativa; comparte señales subyacentes con el PC de §3.2)**:

```typescript
export interface LivenessChannel {
  /** Instantánea de la vitalidad percibida actual */
  perceived(mandateId: MandateId): PerceivedLiveness;

  /** Dispara explícitamente el veredicto pesimista (p. ej. al detectar pérdida de heartbeat) */
  declareStale(mandateId: MandateId, reason: string): Promise<void>;
}

export interface PerceivedLiveness {
  readonly is_perceived_connected: boolean;
  readonly last_freshness: IsoTime;
  readonly staleness_ms: number;
  readonly decided_by: "presence-signal" | "heartbeat" | "explicit-declare";
}
```

**Invariantes clave**:

- **I-LC-1 (veredicto basado en la frescura; está prohibido dejar pasar por el periodo de sondeo del heartbeat)**: los veredictos de desconexión percibida deben basarse en `last_freshness ≥ now − max_staleness_ms`; «el periodo de sondeo del heartbeat aún no ha transcurrido» no debe usarse como razón para seguir dejando pasar las llamadas.
  - **Trace**: `R12.2.2` (usar la frescura — no el periodo de sondeo del heartbeat — como base para dejar pasar las llamadas).

- **I-LC-2 (transición de la máquina de estados a Disconnected)**: una vez juzgado Perceived-Disconnected, la siguiente transición de estado debe seguir la máquina de estados de §4.3 (Active → Disconnected / Active → Suspended, según haya o no un Endorsed_Mandate válido); no existe vía legítima para permanecer en el estado original ni conmutar a uno más permisivo.
  - **Trace**: `R12.1.3` (usar solo la desconexión percibida como base de decisión a nivel de protocolo; no eximir de las consecuencias a nivel de protocolo).

- **I-LC-3 (la recuperación requiere una reconciliación transaccional)**: la recuperación de Perceived-Disconnected a Perceived-Connected debe pasar por la transacción de reconciliación de §8.4; la recuperación automática está prohibida.
  - **Trace**: `R12.1.3` (sin exención de las consecuencias a nivel de protocolo durante la desconexión percibida — entraña que «la recuperación requiere confirmación transaccional explícita», coherente con las transacciones de reconciliación de R12.4.1 / R12.4.3; dentro del conjunto de Requirements declarado por esta tarea, esto se ancla en 12.1).

### §3.6 Behavior Baseline Service (BBS)

**Responsabilidades**: mantiene un perfil de comportamiento acumulativo para cada par (Human_Prime, iFay_Instance); se usa para detectar desviaciones significativas respecto a la línea base por parte de acciones de alta sensibilidad, y para disparar testimonio humano adicional ante una desviación (véase la protección T5 de §9.10.6).

**Interfaz (No normativa)**:

```typescript
export interface BehaviorBaselineService {
  /** Acumula una nueva muestra de acción */
  record(sample: BehaviorSample): Promise<void>;

  /** Evalúa la desviación de la acción actual respecto a la línea base */
  evaluate(
    hp: HumanPrimeID,
    fay: FayID,
    action: AtomicAction
  ): BaselineDeviation;

  /** Aplica el decaimiento de la reputación (decaimiento de la puntuación de confianza) */
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

**Invariantes clave**:

- **I-BBS-1 (la puntuación de confianza debe decaer y estar acotada)**: la «puntuación de confianza» de cada par (HP, IF) debe decaer con el tiempo y tener un límite superior explícito; la acumulación ilimitada está prohibida, no sea que diluya la intensidad de testimonio humano que requieren las futuras acciones de alta sensibilidad.
  - **Trace**: `R13.5.3` (Action Reputation Decay: la puntuación de confianza debe decaer y tener un límite superior explícito).

- **I-BBS-2 (los eventos de testimonio por superación de la línea base entran en la cadena + empuje a la vista del HP)**: todo evento de «la superación de la línea base dispara testimonio adicional» debe escribirse en la Attestation_Chain y empujarse al canal de vista del Human_Prime; antes de obtener el testimonio adicional, rechazar la llamada con `E_HUMAN_WITNESS_REQUIRED`.
  - **Trace**: `R13.5.4` (el evento «la superación de la línea base dispara testimonio adicional» se escribe en la AC + se empuja a la vista del HP), `R13.5.2` (rechazo con `E_HUMAN_WITNESS_REQUIRED` hasta obtener el testimonio adicional).

- **I-BBS-3 (los cambios de calibración también son eventos de auditoría)**: la propia calibración del cálculo de la línea base, una vez determinada, se escribe en la Attestation_Chain; los cambios de calibración se tratan como una clase separada de evento de auditoría, aprobados por el Protocol Committee a través del proceso establecido.
  - **Trace**: `R13.5.1` (el MS mantiene Behavior_Baseline), `R3.1.1` (al procesar cualquier evento de auditoría, la AC debe contener su nodo firmado; la trazabilidad EARS enumerada en este capítulo toma solo las cláusulas pertinentes dentro del conjunto de Requirements declarado por esta tarea).
