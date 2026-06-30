---
title: "Faying Protocol/1.0 — §10 Manejo de errores"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: es
part: "Capítulo 10 de 11 (cuerpo del protocolo)"
---

> Navegación del cuerpo del protocolo: [Índice](./README.md) | anterior [§9 Consideraciones de seguridad](./09-Consideraciones-de-Seguridad.md) | siguiente [§11 Cuestiones abiertas](./11-Cuestiones-Abiertas.md)

## §10 Manejo de errores

Este capítulo consolida todos los códigos de error de §5.4 con escenarios de fallo concretos, respuestas del protocolo, transiciones de estado, vías de recuperación y restricciones de observabilidad. Todos los errores se devuelven como mensajes `ERROR` bajo el envoltorio de §5.2, con el cuerpo `claims` de la forma `{ code, message, mandate_id?, recovery_hint? }`; las cuatro secciones de este capítulo constituyen la «única autoridad a nivel de protocolo sobre el manejo de errores» más allá de §5.4.

### EH.1 Escenarios de error y respuestas del protocolo

La tabla siguiente ofrece una vista panorámica de todos los códigos de error enumerados en §5.4 (1001–1014 y 1099); cada fila contiene: escenario de disparo, respuesta del protocolo, si se dispara Revoke, si se dispara degradación, si la entrada en la cadena de auditoría es obligatoria y si el empuje al canal de vista del HP es obligatorio. Esta tabla se corresponde uno a uno con la tabla de códigos de error de §5.4.

| Código | Nombre | Escenario de disparo | Respuesta del protocolo | Dispara Revoke | Dispara degradación | Entra en auditoría | Entra en la vista del HP |
| ---: | --- | --- | --- | :---: | :---: | :---: | :---: |
| 1001 | `E_NO_MANDATE` | La solicitud de negocio no porta cabecera Faying Protocol / Mandate | El RP rechaza inmediatamente; no se establece auditoría | ✗ | ✗ | ✗ | ✗ |
| 1002 | `E_MANDATE_EXPIRED` | `now > Mandate.not_after` | El RP rechaza + el MS dispara Revoke de ese Mandate | ✓ | ✗ | ✓ | ✗ |
| 1003 | `E_SCOPE_VIOLATION` | Acción de la llamada ∉ `Mandate.scope.actions` | El RP rechaza + registra un evento sospechoso; la sospecha acumulada dispara degradación | ✗ | ✓ (acumulativa) | ✓ | ✗ |
| 1004 | `E_GRADE_INSUFFICIENT` | El RP requiere un nivel más estricto que el `Mandate.grade` actual | El RP rechaza + sugiere elevación (la vía de elevación requiere el `human_witness` del HP) | ✗ | ✗ | ✓ | ✗ |
| 1005 | `E_PRESENCE_STALE` | `presence.last_freshness` supera `max_staleness_ms` o `LivenessDetectionBudget` | El RP rechaza; el IF detiene proactivamente la dimensión D, espera la calibración PRESENCE; máquina de estados Active → Degraded | ✗ | ✓ | ✓ | ✗ |
| 1006 | `E_REVOKED` | El RR marca como revocado | El RP rechaza; cascadea el rechazo de las llamadas de la misma cadena; el IF retrocede inmediatamente a Rogue Fay | ✓ (ya revocado) | ✗ | ✓ | ✓ |
| 1007 | `E_ATTESTATION_INVALID` | Falla la verificación de firma de un nodo de la Attestation Chain / marca de tiempo fuera de la ventana de validez del nodo padre / subcampo del endorsement manipulado | El RP rechaza + el MS dispara Revoke de ese Mandate | ✓ | ✗ | ✓ | ✓ |
| 1008 | `E_RR_UNAVAILABLE` | Timeout de consulta del RR ≥ `StaleBudget` | El RP rechaza por Default-Deny; el IF pausa toda la dimensión D; máquina de estados Active → Degraded | ✗ | ✓ | ✓ | ✗ |
| 1009 | `E_REPLAY` | Dentro de `2 × max_message_lifetime`, nonce ya visto para el mismo subject | El RP rechaza + alerta de seguridad; el IF rota inmediatamente las claves de sesión | ✗ | ✗ | ✓ | ✓ |
| 1010 | `E_HUMAN_WITNESS_REQUIRED` | grade-up / FAYING_REQUEST u otros escenarios que requieren testimonio del HP con `human_witness` ausente o cuya verificación falla | El RP / MS rechaza; esperar el testimonio del HP y luego reiniciar | ✗ | ✗ | ✓ | ✗ |
| 1011 | `E_ROGUE_DETECTED` | Violación de dimensión D detectada (`ego-deviation` / superación de umbral de la línea base de comportamiento, etc.) | El RP rechaza + Revoke forzado; el IF retrocede inmediatamente a Rogue Fay | ✓ | ✗ | ✓ | ✓ |
| 1012 | `E_BUDGET_EXCEEDED` | Las llamadas superan acumulativamente `Scope.budget` / `ResourceBudget` | El RP rechaza + dispara degradación o (casos extremos) Revoke | ✓ (extremo) | ✓ | ✓ | ✗ |
| 1013 | `E_ENDORSEMENT_INVALID` | `endorsed_scope ⊄ scope` / `endorsed_grade.autonomy > grade.autonomy` / `endorsed_lifetime` ausente o demasiado largo / subcampo del endorsement manipulado / endoso hijo de DELEGATE que no converge dentro del padre | El MS rechaza la emisión + dispara Revoke de ese Mandate; el IF detiene inmediatamente todas las acciones endosadas | ✓ | ✗ | ✓ | ✓ |
| 1014 | `E_FAYING_REQUEST_NOT_CONFIRMED` | Un FAYING_REQUEST iniciado por IF no reconocido explícitamente por el HP dentro de `BootstrapTimeout` | El MS devuelve `FAYING_REQUEST_RESP { status="timeout" }`; no produce cambio de estado Faying; el evento se escribe en la Attestation Chain | ✗ | ✗ | ✓ | ✗ |
| 1099 | `E_PROTOCOL` | Versión / formato / campo ausente / no analizable / `mandatory_fields` de DISCLOSURE ausentes o no analizables / entrada de firma ilegal / `msg_type` no enumerado explícitamente en §5.3 | El RP / MS rechaza; empuja además a la vista del HP cuando se dispara desde la vía de DISCLOSURE | ✗ | ✗ | ✓ | ✗* (vía DISCLOSURE ✓) |

> **Nota `*`**: por defecto `E_PROTOCOL` solo entra en la cadena de auditoría; cuando se dispara desde la vía de `mandatory_fields` de DISCLOSURE ausentes o no analizables de §5.3.7, el MS debe empujar además al canal de vista del HP (coherente con la nota de §5.4).

**Trace**: `R2.1.1`–`R2.1.4` (Default-Deny), `R3.2.1`–`R3.2.3` (eventos de error en auditoría y vista del HP), `R4.2.1`–`R4.2.3` (presupuesto de visibilidad de la revocación y alcanzabilidad), `R11.1.4` (la manipulación del endorsement dispara `E_ATTESTATION_INVALID` + Revoke), `R11.2.1`–`R11.2.3` (la violación de convergencia del endorsement dispara `E_ENDORSEMENT_INVALID`), `R1.3.3` (el timeout de FAYING_REQUEST sin reconocimiento dispara `E_FAYING_REQUEST_NOT_CONFIRMED`), `R13.3.1` (los `mandatory_fields` de DISCLOSURE ausentes o no analizables disparan `E_PROTOCOL`).

### EH.2 Vías de recuperación

Los códigos de error se agrupan en tres clases de vía de recuperación según «si se necesita restablecer el estado Faying». Todas las vías de recuperación deben ejecutarse dentro de la convergencia Default-Deny de EH.4; no existe ninguna ventana intermedia de paso optimista.

#### EH.2.1 Errores recuperables (sin necesidad de BOOTSTRAP)

| Código | Nombre | Acción de recuperación |
| ---: | --- | --- |
| 1004 | `E_GRADE_INSUFFICIENT` | Disparar GRADE_SWITCH-up (debe portar el `human_witness` del HP; véase §7.4); no se permite la recuperación saltándose el testimonio |
| 1005 | `E_PRESENCE_STALE` | Reenviar el mensaje PRESENCE para refrescar `last_freshness`; si sigue fallando, converger conforme a `LivenessDetectionBudget` a Degraded → Suspended |
| 1008 | `E_RR_UNAVAILABLE` | Dentro de la ventana Default-Deny, reintentar con backoff (no más de `StaleBudget`); superado → entrar en Degraded, esperar la recuperación del RR antes de reconectar |
| 1012 | `E_BUDGET_EXCEEDED` | Disparar GRADE_SWITCH-down o esperar el refresco de la ventana de presupuesto; no se permite la recuperación «ignorando el presupuesto» |

#### EH.2.2 Recuperación que requiere re-testimonio del HP (debe re-ejecutarse BOOTSTRAP)

| Código | Nombre | Acción de recuperación |
| ---: | --- | --- |
| 1002 | `E_MANDATE_EXPIRED` | Re-ejecutar BOOTSTRAP; el nuevo `mandate_id` no debe ser igual al antiguo `mandate_id` (coherente con la irreversibilidad de la revocación P10) |
| 1006 | `E_REVOKED` | No recuperable; solo el HP puede iniciar un nuevo BOOTSTRAP; el nuevo `mandate_id` no debe ser igual al antiguo `mandate_id` |
| 1007 | `E_ATTESTATION_INVALID` | Igual que arriba; nuevo BOOTSTRAP permitido solo tras disparar el Revoke forzado de ese Mandate |
| 1011 | `E_ROGUE_DETECTED` | Igual que arriba; habitualmente acompañado de intervención directa del HP y auditoría de ego-deviation |
| 1013 | `E_ENDORSEMENT_INVALID` | Igual que arriba; tras disparar el Revoke del Mandate, el HP debe iniciar un nuevo BOOTSTRAP (que contenga un campo `endorsement` legítimo) |

#### EH.2.3 No constituye un cambio de estado Faying (sin necesidad de recuperación)

| Código | Nombre | Manejo |
| ---: | --- | --- |
| 1001 | `E_NO_MANDATE` | El llamador debe obtener primero un Mandate y luego iniciar la llamada; no existe vía de «paso temporal sin Mandate» a nivel de protocolo |
| 1003 | `E_SCOPE_VIOLATION` | El llamador debe ajustar la acción para que caiga dentro de `Mandate.scope.actions`; la sospecha acumulada dispara degradación |
| 1009 | `E_REPLAY` | El llamador debe reiniciar con un nuevo nonce; si es comportamiento de ataque, la alerta de seguridad y la vista del HP ya se han escrito |
| 1010 | `E_HUMAN_WITNESS_REQUIRED` | Reiniciar tras obtener el testimonio del HP; no se permite la sustitución por IF / MS / SA |
| 1014 | `E_FAYING_REQUEST_NOT_CONFIRMED` | El iFay puede reiniciar FAYING_REQUEST dentro de los límites de tasa legítimos, pero no debe montar una inundación de confirmaciones por ello (véase §9.10.7, Anexo B `ConfirmationRateLimit`) |
| 1099 | `E_PROTOCOL` | El llamador debe corregir la estructura del mensaje y luego reiniciar |

> **Restricción dura común**: las vías de recuperación no deben eludir la convergencia Default-Deny de §EH.4; ninguna vía de recuperación optimista de «no estoy seguro pero lo dejo pasar primero» existe a nivel de protocolo.

### EH.3 Restricciones de observabilidad sobre las respuestas de error

Todos los mensajes ERROR deben satisfacer las cuatro restricciones duras siguientes:

1. **Quíntupla de auditoría**: salvo `E_NO_MANDATE` (sin contexto de Mandate), todo código de error debe escribirse en la Attestation Chain / registro de auditoría como la quíntupla `(error_code, mandate_id, ts, RP_id, reason)`; esta quíntupla es coherente con §3.2 y la columna «Entra en auditoría» de §EH.1.
2. **El canal de vista del HP debe empujar**: el conjunto de códigos de error `{E_REVOKED (1006), E_ATTESTATION_INVALID (1007), E_REPLAY (1009), E_ROGUE_DETECTED (1011), E_ENDORSEMENT_INVALID (1013)}` debe empujarse al canal de vista del HP; `E_PROTOCOL (1099)` disparado desde la vía de DISCLOSURE debe empujarse igualmente. El RP no debe tragárselos en silencio.
3. **Sin filtración de información sensible**: a las respuestas de error les está **prohibido** portar estado interno del MS, huellas de claves privadas del Mandate, identificadores de otros HP, variables de la máquina de estados interna del IF u otra información sensible; los campos `message` y `recovery_hint` deben ser semántica pública a nivel de protocolo, sin filtrar detalles de implementación.
4. **Cadena de auditoría verificable de forma independiente**: los eventos de error escritos en la Attestation Chain deben portar los nodos de firma requeridos por I-AC-1 / I-AC-2 de §3.3, de modo que un tercero pueda completar la verificación de la cadena de hoja a raíz sin poseer la clave privada del MS (véase §6.3).

**Trace**: `R3.2.1` (quíntupla de código de error escrita en el registro de auditoría), `R3.2.2` (las respuestas de error no deben portar información sensible), `R3.2.3` (los códigos de error especificados deben entrar en la vista del HP), `R3.1.4` (campos trazables de la cadena de auditoría).

### EH.4 Convergencia Default-Deny unificada

> **Cualquier error que no pueda clasificarse de forma inequívoca, cualquier campo no analizable y cualquier llamada durante la inalcanzabilidad del RR se rechazan uniformemente a nivel de protocolo con `E_PROTOCOL` o `E_RR_UNAVAILABLE`; no existe ninguna vía legítima de «no estoy seguro pero lo dejo pasar primero», ni ninguna vía de recuperación optimista de «procesar por el estado más permisivo» (incluida la Ventana B, donde realmente en línea pero percibido como desconectado; véase §9.9).**

**Cuatro expresiones equivalentes de la regla de convergencia**:

1. **Capa de máquina de estados**: cualquier transición no enumerada explícitamente en la máquina de estados del Mandate de §4.3 / la máquina de estados del ciclo de vida de §8.1 se rechaza uniformemente.
2. **Capa de mensaje**: cualquier `msg_type` no enumerado explícitamente en el inventario de mensajes de §5.3, o cualquier campo del envoltorio ausente / con tipo no coincidente, se rechaza uniformemente con `E_PROTOCOL`.
3. **Capa de código de error**: cualquier causa de fallo no enumerada explícitamente en §5.4 / §EH.1 se clasifica uniformemente en el rechazo `E_PROTOCOL`.
4. **Capa de decisión**: la capa de protocolo usa únicamente Perceived-Disconnected como base de decisión; las vías de paso optimista de la Ventana A (realmente desconectado pero percibido como conectado) / Ventana B (realmente conectado pero percibido como desconectado) no existen a nivel de protocolo (véase el principio de presunción pesimista de §9.9, P17.1 / P17.2).

**Trace**: `R2.1.1`–`R2.1.4` (Default-Deny), `R12.1.1`–`R12.1.3` (decisión basada solo en la percepción de semántica dual), `R12.2.1`–`R12.2.3` (presunción pesimista / rechazo durante la desconexión percibida).
