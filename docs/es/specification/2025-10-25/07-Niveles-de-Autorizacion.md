---
title: "Faying Protocol/1.0 — §7 Niveles de autorización"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: es
part: "Capítulo 7 de 11 (cuerpo del protocolo)"
---

> Navegación del cuerpo del protocolo: [Índice](./README.md) | anterior [§6 Criptografía](./06-Criptografia.md) | siguiente [§8 Ciclo de vida](./08-Ciclo-de-Vida.md)

## §7 Niveles de autorización

Este capítulo presenta la semántica de autorización graduada del Faying Protocol. El Faying Protocol no acepta «delegación universal de todos los poderes» — todo Mandate debe declarar explícitamente un nivel, y las tres columnas de cada nivel `(autonomía, requisito de presencia, requisito de mensaje)` portan semántica precisa a nivel de protocolo; las conmutaciones de nivel disparadas por eventos están exhaustiva y rígidamente codificadas bajo la matriz de §7.2; §7.3 fija el principio de monotonía «pérdida de presencia → debe ajustarse»; §7.4 ofrece las diferencias obligatorias a nivel de mensaje; §7.5 introduce los subniveles Endorsement Grades superpuestos a G1–G4 como capa de permiso de autonomía offline.

> **Relación ortogonal entre G0 y G1–G4**: G0 Emergency Override **no** está dentro del espectro continuo de niveles G1 ↔ G4; es un **canal de anulación ortogonal**. G1–G4 expresan «el eje continuo de la intensidad de autonomía»; G0 es el canal de emergencia para que el Human Prime recupere unilateralmente el control, manifestado solo a los niveles de prioridad de la cola de eventos y del estado terminal (Suspended); no participa en la semántica de «elevación / degradación». Cualquier implementación que trate G0 como «un nivel continuo más estricto que G1» es incoherente con la semántica del protocolo.

> **Referencia de presupuestos numéricos**: los números de `max-staleness` de este capítulo (G1=5 s / G2=60 s / G3=5 min / G4=30 min) se corresponden uno a uno con la entrada `Presence max-staleness (G1..G4)` del Anexo B «Presupuestos de parámetros predeterminados»; la columna «Predeterminado» del Anexo B es el valor de referencia usado en este capítulo, y la columna «Límite superior» es el límite superior duro a nivel de protocolo dentro del cual las implementaciones pueden ajustar.

### §7.1 Definiciones precisas de los niveles

| Nivel | Autonomía | Requisito de presencia | Requisito de mensaje | Adecuado para |
| --- | --- | --- | --- | --- |
| **G0 Emergency Override** | N/A | N/A | Iniciado unilateralmente por el HP; único efecto: empujar inmediatamente el Mandate objetivo a Suspended | Toma de control de emergencia |
| **G1 Strict** | Muy baja | Presencia continua en tiempo real (face / WebAuthn UV, max-staleness ≤ 5 s) | Toda llamada externa debe portar una PresenceSignal ≤ 5 s | Operaciones irreversibles (transferencias, firma, borrado de base de datos, comandos de alto privilegio de terminal) |
| **G2 Moderate** | Media | Presencia a nivel de tarea (presencia fresca requerida antes de subtareas sensibles, max-staleness ≤ 60 s) | PresenceSignal antes de las acciones sensibles | Operaciones de agente de frecuencia media (reservas, reprogramaciones, envío de formularios) |
| **G3 Loose** | Alta | Consulta en pasos clave (intent-ticket antes de los puntos de decisión clave) | intent-ticket de un solo uso portado en los pasos clave | Agente de bajo riesgo a largo plazo (clasificación de correo, calendario) |
| **G4 Autonomous** | Muy alta | Heartbeat periódico (presence-heartbeat, max-staleness ≤ 30 min) | Mantenimiento de heartbeat + retorno de auditoría periódico | Autonomía rutinaria dentro del alcance |

> **Elección de diseño**: G0 no está dentro del espectro continuo G1 ↔ G4; es un **canal de anulación ortogonal** — su único propósito es permitir que el HP recupere inmediatamente el control bajo cualquier estado.

**Convención del eje de autonomía**: `G0 < G1 < G2 < G3 < G4` (valores mayores = mayor autonomía). Todas las decisiones de «elevación / degradación» del resto de este capítulo se basan en comparaciones de tamaño entre `target.autonomy` y `current.autonomy`; G0 no participa en esta comparación de eje — migra unilateralmente a Suspended mediante la última fila de la matriz de §7.2.

**Requisito de presencia alineado con los tipos de Presence_Signal** (véase la tabla de tipos de señal de §3.2):

- **G1 Strict**: señales típicas `face-continuous` o `webauthn-uv-fresh`, `max_staleness_ms = 5_000`;
- **G2 Moderate**: señal típica `fingerprint-tap` (antes de subtareas sensibles), `max_staleness_ms = 60_000`;
- **G3 Loose**: señal típica `intent-ticket` (consumo de un solo uso en los pasos clave); sin límite superior periódico de max-staleness, pero todo paso clave debe tener un intent-ticket fresco;
- **G4 Autonomous**: señal típica `presence-heartbeat-only`, `max_staleness_ms = 1_800_000` (30 min).

**Diferencias en el requisito de mensaje (referenciadas con el inventario de mensajes de §5)**:

- **GRADE_SWITCH en dirección de elevación en G1 / G2**: `human_witness` es obligatorio (MUST), la forma de testimonio predeterminada es una aserción WebAuthn UV (véanse las suites de algoritmos de §6.1);
- **G3 / G4**: las elevaciones a estos niveles (que siguen perteneciendo a la vía de «aflojar la autonomía» incluso cuando target.autonomy está por debajo del nivel de origen) también requieren `human_witness`; solo en la vía de «degradación activa» `human_witness` se reduce a MAY;
- **G0**: solo puede iniciarse unilateralmente por el HP (un G0 sustituido por IF / MS / SA se rechaza con `E_PROTOCOL`); requiere un `human_witness` verificable; los mensajes G0 deben escribirse en la Attestation Chain y en la cola de empuje del Revocation Registry con la máxima prioridad.

### §7.2 Matriz de condiciones de disparo

La tabla siguiente es la matriz de transición de estados 6×4 para 6 clases de evento de disparo × 4 niveles actuales no-G0; esta es la correspondencia obligatoria evento → estado terminal a nivel de protocolo; no existe ninguna vía de transición fuera de esta tabla.

| Evento | G1 actual | G2 actual | G3 actual | G4 actual |
| --- | --- | --- | --- | --- |
| Frescura de presencia caducada | → Suspended | → G3 Loose | → Suspended | → Suspended |
| Elevación activa del HP | — | → G1 (testimonio requerido) | → G2 / G1 (testimonio requerido) | → G3 / G2 / G1 (testimonio requerido) |
| Degradación activa del HP | → G2 | → G3 | → G4 | — |
| Desviación Ego detectada | → Revoked | → Revoked | → Revoked | → Revoked |
| Registro de revocación inalcanzable | Rechazar llamada | Rechazar llamada | Rechazar llamada | Rechazar llamada |
| G0 Override | → Suspended | → Suspended | → Suspended | → Suspended |

**Complementos semánticos de la matriz**:

- **Asimetría de la fila «frescura de presencia caducada»**: G2 → G3 es la «degradación suave» permitida (sigue en la rama Active de la máquina de estados); G1 / G3 / G4 → Suspended expresan tres lógicas de decisión distintas — G1 porque bajo escenarios de alta sensibilidad «sin presencia fresca → no se permite acción»; G3 porque bajo escenarios de intent-ticket el heartbeat no es la base principal de presencia, y la ausencia continua de señales frescas en los pasos clave se trata como no confiable; G4 porque el heartbeat es su única base de presencia, y la pérdida de heartbeat se absorbe directamente en Suspended (coherente con la cláusula de excepción de §7.3).
- **Fila «elevación activa del HP»**: el «—» en G1 significa que G1 ya es el nivel más estricto sin espacio de elevación superior; el resto permite elevaciones de un solo paso a través de 1–3 niveles, todas requiriendo `human_witness` (véase §7.4).
- **Fila «degradación activa del HP»**: el «—» en G4 significa que G4 ya es el nivel más laxo sin espacio de degradación más laxo; la dirección de degradación no requiere `human_witness`, pero las notificaciones al RR y los registros en la cadena AC siguen siendo obligatorios.
- **Fila «desviación Ego detectada»**: los cuatro niveles entran uniformemente en el estado terminal Revoked (Revoked es un estado absorbente; véase §8 / Property 10); la lógica de decisión que dispara esta fila la dan conjuntamente el Behavior Baseline Service de §3.6 y §9.10.6 T5.
- **Fila «registro de revocación inalcanzable»**: los cuatro niveles «rechazan la llamada» uniformemente; esto no es una transición de estado — es la vía de convergencia Default-Deny para una única llamada (código de error `E_RR_UNAVAILABLE`); el propio Mandate permanece en el nivel actual; esta fila es coherente con la invariante I-RR-2 del RR de §3.4.
- **Fila «G0 Override»**: iniciada unilateralmente por el HP; los cuatro niveles se absorben uniformemente en Suspended; procesada con la máxima prioridad en la cola de eventos (cualquier evento pendiente cede el paso).

### §7.3 Principio de monotonía de degradación

> **Sin presencia, más estricto** — esta es la forma contraintuitiva pero obligatoria de Graceful-Degradation: la pérdida de la señal de presencia significa «el campo de visión humano se estrecha», por lo que la autonomía debe **ajustarse**, no aflojarse. En términos numéricos: pérdida de presencia → el valor del nivel disminuye (más estricto).

Expresión formal (alineada con P11):

```
∀ M ∈ ActiveMandates. PresenceState(M).stale = true ⟹
    next_state(M) ∈ { Degraded(g'), Suspended }
    where g'.autonomy < M.grade.autonomy
```

Es decir: tras la pérdida de presencia, la siguiente transición de estado debe migrar a un nivel con `autonomía estrictamente inferior` (número menor, mayor seguridad), o migrar directamente a Suspended; **permanecer en el nivel original está prohibido, conmutar hacia mayor autonomía está prohibido**.

**Excepciones (restricciones de estado absorbente)**:

- **Pérdida de heartbeat de G4 Autonomous → directamente Suspended**: dado que G4 ya es el nivel de mayor autonomía sin un nivel más estricto disponible, la absorción directa en Suspended es una restricción dura a nivel de protocolo (coherente con la columna G4 de la primera fila de la matriz de §7.2).
- **Estado `Degraded` que supera `MaxDegradedDuration` → directamente Suspended**: evita que la «residencia prolongada en un subnivel» se convierta en una «vía de aflojamiento» implícita; el umbral concreto está en `MaxDegradedDuration` del Anexo B.

### §7.4 Diferencias en los requisitos de mensaje de la conmutación de nivel

La tabla siguiente ofrece, para las tres direcciones de conmutación, las diferencias en los campos obligatorios a nivel de mensaje; si falta cualquier entrada «MUST», el mensaje de conmutación correspondiente se rechaza uniformemente con `E_PROTOCOL` o `E_HUMAN_WITNESS_REQUIRED` (véase la tabla de códigos de error de §5.4).

| Dirección de conmutación | human_witness | Notificación al RR | Registro en cadena AC |
| --- | --- | --- | --- |
| Elevación (mayor autonomía) | MUST | MUST | MUST |
| Degradación (menor autonomía) | MAY | MUST | MUST |
| Emergency Override | MUST | MUST (empuje de máxima prioridad) | MUST |

**Complementos semánticos a nivel de mensaje**:

- **Dirección de elevación**: cuando `GRADE_SWITCH.target_grade.autonomy > current_grade.autonomy`, `human_witness` es obligatorio; ausencia o firma inválida → `E_HUMAN_WITNESS_REQUIRED` (código de error 1010). La restricción de esta fila se alinea plenamente con el Requirement 6.1.
- **Dirección de degradación**: `human_witness` se reduce a MAY, pero las notificaciones al RR y los registros en la cadena AC siguen siendo obligatorios — las degradaciones también son una clase de cambio de estado que requiere auditoría y observabilidad; la «degradación silenciosa» está prohibida.
- **Emergency Override (G0)**: `human_witness` es obligatorio; las notificaciones al RR deben empujarse con la máxima prioridad (coherente con el campo de prioridad del canal de empuje del RR de §3.4); los registros en la cadena AC se escriben con la máxima prioridad.
- **Semántica a nivel de protocolo de «registro en cadena AC obligatorio»**: todo GRADE_SWITCH (elevación / degradación / G0 por igual) produce un AttestationEvent con `event_type = "grade-switch"` (véase §3.3), anexado por el MS inmediatamente después de que la conmutación se complete; la ausencia → se trata como un vacío de auditoría, disparando `E_ATTESTATION_INVALID`.

### §7.5 Subniveles Endorsement Grades

> **Postura de diseño**: Endorsement no es un nivel nuevo sino **una «capa de permiso de autonomía offline» superpuesta a G1–G4**. Cada nivel no-G0 (es decir, G1–G4) puede tener una superposición `endorsement`, que permite al Mandate operar de forma autónoma dentro de un envoltorio restringido durante la desconexión física (juzgada conforme al Liveness Channel de §3.5 y la máquina de estados de §4.3). G0 Emergency Override no permite superposición de endoso — es el canal para que el HP recupere unilateralmente el control, mutuamente excluyente con la semántica de «autonomía offline».

**Semántica de superposición**:

| Nivel principal | Endoso permitido | Efecto predeterminado del endoso |
| --- | --- | --- |
| G0 Emergency Override | **No permitido** | — |
| G1 Strict | Permitido | Durante la desconexión física → Disconnected; endorsed_scope es típicamente el subconjunto mínimo de acciones de alta sensibilidad; endorsed_grade por defecto = G1 (sin descenso) |
| G2 Moderate | Permitido | endorsed_grade por defecto = G2; uso típico: tareas programadas / completar transacciones ya iniciadas |
| G3 Loose | Permitido | endorsed_grade por defecto = G3; uso típico: clasificación de información / operaciones de lectura durante la continuación offline |
| G4 Autonomous | Permitido | endorsed_grade por defecto = G4; uso típico: agencia offline de larga duración + reconciliación por lotes tras la reconexión |

**Restricciones duras de los subniveles** (entrelazadas con el Requirement 11.2; finalmente fijadas por P16.3):

- **convergencia de scope**: `endorsement.endorsed_scope ⊆ Mandate.scope`;
- **convergencia de grade**: `endorsement.endorsed_grade.autonomy ≤ Mandate.grade.autonomy` (es decir, endorsed_grade **no es más débil** que el nivel principal en autonomía, seguridad ≥ nivel principal);
- **vigencia finita**: `endorsement.endorsed_lifetime` debe ser finito; `∞` o ausente está prohibido, y `≤ (Mandate.not_after − Mandate.not_before)`; el Anexo B ofrece además el límite superior blando `Endorsed_Lifetime` (predeterminado 4 h, límite superior 12 h);
- **política de revocación offline enumerable**: `endorsement.offline_revocation_policy ∈ {"stop-and-audit", "stop-only", "graceful-stop"}`; predeterminado `stop-and-audit`.

Si falla cualquier restricción dura, BOOTSTRAP / DELEGATE se rechaza uniformemente con `E_ENDORSEMENT_INVALID` (código de error 1013) (véase §5.4); en DELEGATE, además `child.endorsement` debe converger dentro de `parent.endorsement` — es decir, el endorsed_scope / endorsed_grade / endorsed_lifetime del Mandate hijo no debe exceder los campos correspondientes del Mandate padre.

**Coordinación con la máquina de estados de desconexión** (véase §4.3, §8.4, §9.8):

- Cuando `PresenceState.stale = true` y el Mandate es un Endorsed_Mandate → `Active → Disconnected` (la vía no-Endorsed va directamente → Suspended);
- Durante Disconnected, el iFay solo puede realizar acciones de dimensión D dentro de `endorsement.endorsed_scope`, restringido por `endorsement.endorsed_grade`;
- Una vez que `endorsement.endorsed_lifetime` caduca, soft-timeout inmediato → Disconnected → Revoked, incluso mientras el iFay sigue físicamente desconectado (cláusula 3 del Requirement 11.3 «restricción dura de soft-timeout»);
- El punto final que asume la responsabilidad es siempre el `issuer` del Mandate (Human Prime), sin verse alterado por la existencia del endoso (véase P16.5 Endorsement_Accountability_Invariant y el Requirement 11.4).

**Exclusión mutua entre Endorsement y G0**: G0 Emergency Override es el canal para que el HP recupere unilateralmente el control; su semántica apunta al estado Suspended («detener inmediatamente todas las acciones de dimensión D»). La semántica de Endorsement apunta al «subconjunto de acciones de dimensión D permitidas durante la desconexión física». Ambos son eventos mutuamente excluyentes en la máquina de estados — una vez disparado G0, el Mandate objetivo se absorbe inmediatamente en Suspended; durante Suspended, el Mandate ya no aplica las reglas de paso de dimensión D del endoso (aunque el endoso aún no haya alcanzado su punto de soft-timeout de vigencia).
