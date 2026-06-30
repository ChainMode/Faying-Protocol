---
title: "Faying Protocol/1.0 — §5 Mensajes del protocolo"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: es
part: "Capítulo 5 de 11 (cuerpo del protocolo)"
---

> Navegación del cuerpo del protocolo: [Índice](./README.md) | anterior [§4 Modelos de datos](./04-Modelos-de-Datos.md) | siguiente [§6 Criptografía](./06-Criptografia.md)

## §5 Mensajes del protocolo

Este capítulo presenta todos los mensajes de la capa del Faying Protocol: reglas de codificación, estructura del envoltorio (envelope), inventario de 7 clases de mensaje de negocio más 1 clase de respuesta de error, y la tabla de correspondencia entre códigos de error y los empujes de auditoría / canal de vista del HP.

> **Nota sobre la autoritatividad de los tipos**: los tipos `Mandate / Scope / Grade / PresenceSignal / PresenceRequirement / Endorsement / SignatureBundle / Attestation / WebAuthnAssertion / AtomicAction / RevokeReason` referenciados en los bloques TypeScript de este capítulo tienen sus **definiciones autoritativas** en §4 Modelos de datos (CDDL); la vista TypeScript es una vista de lectura humana **No normativa**, y donde ambas difieran prevalece la CDDL de §4.

### §5.1 Reglas de codificación

- **Formato primario (CBOR)**: la codificación predeterminada para toda transmisión en la red es CBOR ([RFC 8949](https://www.rfc-editor.org/rfc/rfc8949)); el `Content-Type` de HTTP debe declararse como `application/faying-protocol+cbor`.
- **Reserva de interoperabilidad (JSON)**: JSON ([RFC 8259](https://www.rfc-editor.org/rfc/rfc8259)) se usa solo en escenarios de depuración / navegador / revisión humana; el `Content-Type` de HTTP debe declararse explícitamente como `application/faying-protocol+json`; la equivalencia de seguridad se garantiza mediante semántica de campos y formato de firma idénticos.
- **Codificación determinista**: todo objeto firmado debe, antes de firmarse, serializarse en CBOR conforme a la regla de Deterministic Encoding de RFC 8949 §4.2.1, evitando la ambigüedad de la serialización JSON; bajo la forma JSON, la entrada de firma sigue siendo el hash de la cadena de bytes serializada en Deterministic CBOR (véase §6.3).
- **Vinculación de transporte**: por defecto HTTP/1.1 y HTTP/2; los puntos finales de Mandate Service siguen `POST /faying-protocol/v1/{verb}`; también se permite la vinculación a gRPC (servicio `faying-protocol.v1`) o WebSocket / SSE (streaming `faying-protocol.v1`). Todas las vinculaciones de la capa de transporte deben preservar las firmas y los nonces de la capa de mensaje; sustituir las firmas de nivel de mensaje por la identidad del canal TLS de la capa de transporte está prohibido.

### §5.2 Estructura del envoltorio (envelope)

Todos los mensajes usan el envoltorio unificado `FayingProtocolEnvelope`:

```typescript
interface FayingProtocolEnvelope<TPayload> {
  header: {
    version:    "Faying Protocol/1.0";
    msg_type:   FayingProtocolMsgType;
    msg_id:     string;        // ULID
    issued_at:  IsoTime;
    expiry:     IsoTime;
    nonce:      Nonce;
    grade:      Grade;         // nivel de la sesión actual (usado por el RP para rechazar solicitudes de nivel bajo)
    issuer:     HumanPrimeID | string;
    subject:    FayID;
  };
  claims:      TPayload;
  attestation: Attestation;
  signature:   SignatureBundle;
}

type FayingProtocolMsgType =
  | "BOOTSTRAP"        | "BOOTSTRAP_RESP"
  | "PRESENCE"         | "PRESENCE_ACK"
  | "GRADE_SWITCH"     | "GRADE_SWITCH_RESP"
  | "DELEGATE"         | "DELEGATE_RESP"
  | "REVOKE"           | "REVOKE_RECEIPT"
  | "FAYING_REQUEST"   | "FAYING_REQUEST_RESP"
  | "DISCLOSURE"
  | "ERROR";
```

**Invariantes a nivel de envoltorio**:

- Cualquier campo ausente o con tipo incorrecto → rechazo uniforme con `E_PROTOCOL` (véase §5.4).
- Dentro de una ventana de `2 × max_message_lifetime`, el `nonce` se acepta como máximo una vez para el mismo `subject`; repetición → `E_REPLAY`.
- `expiry` debe ser finito y `> issued_at`; los envoltorios caducados no entran en la vía de verificación de negocio y se rechazan directamente con `E_PROTOCOL`.
- La entrada de `signature` debe ser `H( Deterministic-CBOR( Envelope_without_signature ) )` (véase §6.3).

### §5.3 Inventario de mensajes

Este protocolo define 7 clases de mensajes de negocio: BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE / REVOKE / FAYING_REQUEST / DISCLOSURE, más 1 clase de respuesta de error ERROR (véase §5.4).

#### §5.3.1 BOOTSTRAP (Faying Action)

**Propósito**: el Human Prime establece un Mandate en el MS mediante BOOTSTRAP, emitiendo la autorización mandatada al iFay. BOOTSTRAP es **la única entrada legítima de Faying Action** del Faying Protocol.

```typescript
interface BootstrapClaims {
  human_prime:   HumanPrimeID;
  fay:           FayID;
  scope:         Scope;
  grade:         Grade;
  presence_req:  PresenceRequirement;
  not_after:     IsoTime;          // debe ser finito
  human_witness: WebAuthnAssertion; // user-verification = true
  endorsement?:  Endorsement;       // opcional; si está presente, emitir un Endorsed Mandate (véase §4 / §11)
  faying_request_ref?: string;      // en la vía iniciada por IF, referencia el FAYING_REQUEST.msg_id correspondiente
}
```

**Respuesta de éxito**: devuelve el objeto `Mandate` completo (incluido `signature_bundle`).

**Restricciones duras a nivel de protocolo**:

- `not_after` debe ser finito y `> not_before`; `∞` y los valores negativos están prohibidos; violación → rechazo uniforme con `E_PROTOCOL` (coherente con I-MS-1 de §3.1 / Property 7).
- Campo `human_witness` ausente o firma inválida → rechazo uniforme con `E_HUMAN_WITNESS_REQUIRED`; no existe vía legítima para que IF / MS / Supervisory Agent sustituyan al HP en completar el reconocimiento.
- Cuando BOOTSTRAP responde a un `FAYING_REQUEST` anterior iniciado por el iFay, `faying_request_ref` debe apuntar al `msg_id` de esa solicitud; el MS debe, en la Attestation Chain, enlazar «iniciado por iFay → testimonio del HP → cobra efecto» como una cadena de evidencia indivisible (véase §5.3.6 y §3.3).
- Cuando el campo `endorsement` está presente, el MS debe, antes de firmar, verificar `endorsed_scope ⊆ scope` ∧ `endorsed_grade.autonomy ≤ grade.autonomy` ∧ `0 < endorsed_lifetime_ms ≤ (not_after − not_before)`; cualquier fallo → rechazo con `E_ENDORSEMENT_INVALID` (código de error 1013).

#### §5.3.2 PRESENCE (calibración continua)

**Propósito**: el iFay_Instance empuja periódicamente al MS las señales de presencia producidas por los Presence Devices, refrescando el `PresenceState.last_freshness` del Mandate correspondiente.

```typescript
interface PresenceClaims {
  mandate_id:    MandateID;
  signal:        PresenceSignal;
  device_health: {
    secure_element: boolean;
    tampered:       boolean;
    last_boot_at:   IsoTime;
  };
}
```

**Restricciones duras a nivel de protocolo**:

- `signal` debe portar la tripleta obligatoria de I-PC-1 de §3.2 (`nonce / produced_at / device_attestation`) y estar firmada por el Presence Device; la ausencia de cualquiera → `E_PROTOCOL`. La ventana de frescura la da el `presence_req.max_staleness_ms` del Mandate correspondiente, no la porta la señal.
- Una señal que supere `presence_req.max_staleness_ms` → `E_PRESENCE_STALE`, y dispara el ajuste conforme a I-PC-3 de §3.2 (migrar a un nivel más estricto o a Suspended).
- El mismo `(subject, nonce)` repitiéndose dentro de una ventana de `2 × max_message_lifetime` → `E_REPLAY` uniformemente.

#### §5.3.3 GRADE_SWITCH (conmutación de nivel)

**Propósito**: ajusta el nivel de autorización (elevación / degradación) dentro del ciclo de vida de un Mandate.

```typescript
interface GradeSwitchClaims {
  mandate_id:    MandateID;
  target_grade:  Grade;
  reason:        "human-initiated" | "presence-loss" | "policy-trigger";
  human_witness?: WebAuthnAssertion;  // obligatorio en la dirección de elevación, opcional en la de degradación
}
```

**Invariante a nivel de protocolo (testimonio obligatorio en la elevación)**: cuando `target_grade.autonomy > current.autonomy` (es decir, autonomía estrictamente superior a la del nivel actual), `human_witness` es **MUST**; ausencia o firma inválida → rechazo uniforme con `E_HUMAN_WITNESS_REQUIRED`. La dirección de degradación (`target_grade.autonomy ≤ current.autonomy`) puede ser disparada automáticamente por el protocolo (p. ej. `presence-loss` / `policy-trigger`); no se requiere `human_witness`.

#### §5.3.4 DELEGATE (derivación entre dispositivos / subagente)

**Propósito**: deriva un Mandate hijo de un Mandate padre, usado en escenarios entre dispositivos o de subagente.

```typescript
interface DelegateClaims {
  parent_mandate: MandateID;
  child_subject:  FayID;            // FayID derivado
  child_scope:    Scope;            // debe ⊆ parent.scope
  child_grade:    Grade;            // child_grade.autonomy debe ≤ parent.grade.autonomy (autonomía menor o igual, es decir, más estricto o igual)
  device_id?:     string;           // vincular a un terminal específico en la derivación entre dispositivos
}
```

**Restricciones duras a nivel de protocolo**:

- `child_scope ⊆ parent.scope` ∧ `child_grade.autonomy ≤ parent.grade.autonomy`; cualquier expansión en cualquier dirección → rechazo con `E_PROTOCOL` (coherente con I-MS-4 de §3.1 / Property 6).
- El `signature_bundle.chain` del Mandate hijo debe portar la contrafirma del Mandate padre, formando un nodo derivado en la Attestation Chain.
- Cuando el Mandate padre porta `endorsement`, el `endorsement` del Mandate hijo (si está presente) debe converger dentro del endoso del padre; no convergencia → rechazo con `E_ENDORSEMENT_INVALID`.

#### §5.3.5 REVOKE

**Propósito**: revoca un Mandate; opcionalmente cascadea para revocar todos los Mandates hijos derivados.

```typescript
interface RevokeClaims {
  mandate_id:   MandateID;
  cascade:      boolean;            // revocación en cascada de todos los Mandates hijos derivados (predeterminado true)
  reason:       RevokeReason;
  effective_at: IsoTime;            // predeterminado = now; se permite revocación programada
}

type RevokeReason =
  | "human-initiated"
  | "expiry"
  | "task-completed"
  | "human-prime-unreachable"
  | "ego-deviation"
  | "fay-credential-invalid"
  | "human-prime-credential-invalid"
  | "regulatory-order"
  | "terminal-disconnected";
```

`RevokeReason` se corresponde uno a uno con las nueve condiciones de disparo del capítulo 13.

**Restricciones duras a nivel de protocolo**:

- La alcanzabilidad de la revocación debe ser ≥ la alcanzabilidad del Bootstrap (coherente con Property 4 / R4.1); no existe vía para que el propio iFay inicie REVOKE legítimamente.
- Cuando `cascade = true`, todos los Mandates hijos derivados deben hacerse visibles como `revoked` dentro de `RevocationVisibilityBudget` (coherente con Property 14).
- La revocación es irreversible: `Revoked` es un estado absorbente; restaurar la autorización debe pasar de nuevo por BOOTSTRAP con un nuevo `mandate_id` distinto del antiguo `mandate_id` (coherente con Property 10).

#### §5.3.6 FAYING_REQUEST / FAYING_REQUEST_RESP (Faying bidireccional iniciado por IF)

**Propósito**: el iFay busca Faying de forma proactiva ante el Human Prime (solicitando el establecimiento o ajuste de la relación mandatada). Este mensaje **no produce directamente un Mandate**; el MS actúa solo como reenviador, empujando la solicitud al canal de vista del HP; el HP completa luego el reconocimiento y la efectividad mediante BOOTSTRAP (véase §2.4 Fase A0).

```typescript
interface FayingRequestClaims {
  initiator:        FayID;          // el propio iFay
  target_human:     HumanPrimeID;   // HP objetivo
  proposed_scope:   Scope;          // alcance mandatado propuesto
  proposed_grade:   Grade;          // nivel propuesto
  reason:           string;         // complemento de texto libre
  reason_code:
    | "establish"
    | "adjust-scope"
    | "adjust-grade"
    | "renew"
    | "endorsement-request";
  expected_lifetime_ms?: number;    // vigencia esperada del Mandate
  proposed_endorsement?: Endorsement; // si también se busca un Endorsed Mandate
}

interface FayingRequestRespClaims {
  request_msg_id: string;           // referencia el FAYING_REQUEST.msg_id de aguas arriba
  status:         "accepted" | "rejected" | "timeout";
  bootstrap_ref?: string;           // cuando status=accepted, apunta al BOOTSTRAP.msg_id que completó el HP
  reject_reason?: string;
}
```

**Restricciones duras a nivel de protocolo**:

- Un FAYING_REQUEST iniciado por IF **no** produce directamente ningún cambio de estado Faying; solo cuando el HP responde dentro de `BootstrapTimeout` mediante BOOTSTRAP (portando `faying_request_ref` y un `human_witness` verificable) la solicitud cobra efecto.
- Si el HP no da un reconocimiento explícito dentro de `BootstrapTimeout`, el MS debe devolver `FAYING_REQUEST_RESP { status="timeout" }` y escribir el evento en la Attestation Chain, correspondiente al código de error `E_FAYING_REQUEST_NOT_CONFIRMED` (1014).
- No existe vía legítima para que MS / IF / Supervisory Agent sustituyan al HP en completar el reconocimiento; `human_witness` ausente → `E_HUMAN_WITNESS_REQUIRED` (1010).
- La frecuencia de FAYING_REQUEST para cada par `(HP, IF)` está restringida por `ConfirmationRateLimit` (véase el Anexo B); la superación del límite se maneja conforme a §9.10.7 T6.

#### §5.3.7 DISCLOSURE (mensaje de divulgación estructurado)

**Propósito**: un mensaje de divulgación estructurado usado por el iFay al informar o solicitar confirmación. Los reguladores y el MS pueden auditar este mensaje a nivel de esquema; usar texto libre puro para ocultar información clave está prohibido (véase §9.10.4 T3).

```typescript
interface DisclosureClaims {
  mandate_id:         MandateID;
  /** mandatory_fields (la ausencia de cualquiera → tratada como error de protocolo) */
  action:             AtomicAction;          // una divulgación corresponde a exactamente un Atomic_Action
  scope_used:         Scope;                 // el subconjunto realmente usado del alcance
  risk_level:         "low" | "normal" | "high" | "critical";
  reversibility:      "reversible" | "partially-reversible" | "irreversible";
  affected_resources: string[];
  uncertainty_flags:  string[];              // p. ej. ["ambiguous-target", "stale-context"]
  /** complementos opcionales */
  free_text?:         string;
  intent?:            "report" | "request-confirmation";
  endorsement_id?:    string;                // si ocurrió durante Disconnected, apunta al endoso correspondiente
}
```

**Lista de cumplimiento obligatorio de `mandatory_fields`** (coherente con R13.3 / §9.10.4):

`action` / `scope_used` / `risk_level` / `reversibility` / `affected_resources` / `uncertainty_flags`.

**Restricciones duras a nivel de protocolo**:

- Cualquier `mandatory_fields` ausente o no analizable → el MS debe rechazar con `E_PROTOCOL` (1099) y empujar al canal de vista del HP;
- Las acciones de alta sensibilidad (`risk_level ∈ {high, critical}`) deben, **antes** de la ejecución de dimensión D, emitir primero DISCLOSURE y esperar la confirmación explícita del HP (a menos que el nivel actual sea ya G4 Autonomous y la acción caiga dentro del alcance principal; véase §7);
- Si la auditoría posterior descubre que los `mandatory_fields` de DISCLOSURE son incoherentes con la acción real, el MS debe revocar el Mandate con `RevokeReason="ego-deviation"`;
- El DISCLOSURE de acciones ejecutadas durante Disconnected debe portar `endorsement_id`, de modo que la acción pueda trazarse de forma independiente a un endoso específico.

### §5.4 Códigos de error

Las respuestas de error usan uniformemente el mensaje `ERROR` (envoltorio `msg_type = "ERROR"`); el cuerpo `claims` tiene la forma `{ code, message, mandate_id?, recovery_hint? }`. La tabla siguiente ofrece todos los códigos de error y sus restricciones de auditoría y de empuje al canal de vista del HP (coherente con §EH.3).

| Código | Nombre | Significado | Respuesta | Debe entrar en auditoría | Debe entrar en la vista del HP |
| ---: | --- | --- | --- | :---: | :---: |
| 1001 | `E_NO_MANDATE` | La solicitud no porta Mandate | Rechazo | ✗ | ✗ |
| 1002 | `E_MANDATE_EXPIRED` | Mandate caducado | Rechazo + disparo de Revoke | ✓ | ✗ |
| 1003 | `E_SCOPE_VIOLATION` | La llamada excede el alcance | Rechazo + registro de sospechoso | ✓ | ✗ |
| 1004 | `E_GRADE_INSUFFICIENT` | Nivel actual insuficiente para la acción sensible | Rechazo + sugerir elevación | ✓ | ✗ |
| 1005 | `E_PRESENCE_STALE` | Señal de presencia caducada | Rechazo + disparo de degradación | ✓ | ✗ |
| 1006 | `E_REVOKED` | Mandate revocado | Rechazo | ✓ | ✓ |
| 1007 | `E_ATTESTATION_INVALID` | Falla la verificación de la atestación | Rechazo + disparo de Revoke | ✓ | ✓ |
| 1008 | `E_RR_UNAVAILABLE` | Registro de revocación inalcanzable | Rechazo por Default-Deny | ✓ | ✗ |
| 1009 | `E_REPLAY` | nonce repetido | Rechazo + alerta de seguridad | ✓ | ✓ |
| 1010 | `E_HUMAN_WITNESS_REQUIRED` | La elevación de nivel / Faying bidireccional carece de testimonio humano | Rechazo | ✓ | ✗ |
| 1011 | `E_ROGUE_DETECTED` | Comportamiento Rogue detectado | Rechazo + Revoke forzado | ✓ | ✓ |
| 1012 | `E_BUDGET_EXCEEDED` | ResourceBudget superado | Rechazo + disparo de degradación | ✓ | ✗ |
| 1013 | `E_ENDORSEMENT_INVALID` | Campo endorsement inválido (incl. `endorsed_scope ⊄ scope` / `endorsed_grade.autonomy > grade.autonomy` / `endorsed_lifetime` ausente o demasiado largo / manipulado) | Rechazo + disparo de Revoke de ese Mandate | ✓ | ✓ |
| 1014 | `E_FAYING_REQUEST_NOT_CONFIRMED` | FAYING_REQUEST iniciado por IF no reconocido explícitamente por el HP dentro de `BootstrapTimeout` | Rechazo + escritura en la Attestation Chain | ✓ | ✗ |
| 1099 | `E_PROTOCOL` | Error a nivel de protocolo (versión / formato / firma / `mandatory_fields` de DISCLOSURE ausentes o no analizables) | Rechazo | ✓ | ✗* |

> **Nota `*`**: por defecto `E_PROTOCOL` entra solo en la auditoría; pero cuando se dispara desde la vía de `mandatory_fields` de DISCLOSURE ausentes o no analizables de §5.3.7, el MS debe empujar además al canal de vista del HP (véase §5.3.7 y §9.10.4 T3).
>
> **Notas semánticas sobre auditoría / vista del HP**:
>
> - **Debe entrar en auditoría**: los errores deben escribirse en la Attestation Chain / registro de auditoría como la quíntupla `(error_code, mandate_id, ts, RP_id, reason)`; salvo `E_NO_MANDATE` (sin contexto de Mandate), todos los códigos de error son ✓.
> - **Debe entrar en la vista del HP**: los errores deben empujarse al canal de vista del HP; el RP no debe tragárselos en silencio. Los cuatro básicos (`E_REVOKED` / `E_ATTESTATION_INVALID` / `E_REPLAY` / `E_ROGUE_DETECTED`) son obligatorios por §EH.3; `E_ENDORSEMENT_INVALID`, dado que su cadena de disparo acompaña inevitablemente a `E_REVOKED`, también se empuja al canal de vista del HP.
> - A las respuestas de error les está **prohibido** portar estado interno del MS, huellas de claves privadas del Mandate, identificadores de otros Human Prime u otra información sensible (véase §EH.3).
