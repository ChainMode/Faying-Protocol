---
title: "Faying Protocol/1.0 — Anexo A Referencia rápida de alineación de terminología"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: es
part: "Anexo A (referencia normativa)"
---

> Navegación del cuerpo del protocolo: [Índice](./README.md) | anterior [§11 Cuestiones abiertas](./11-Cuestiones-Abiertas.md) | siguiente [Anexo B Presupuestos de parámetros predeterminados](./Anexo-B-Presupuestos-de-Parametros-Predeterminados.md)

## Anexo A Referencia rápida de alineación de terminología

> Este anexo es coherente con el glosario de la base de requisitos y con el Anexo A de la base de diseño; los nombres de sistema que aparecen en las subcláusulas EARS deben estar definidos aquí antes de su uso. El anexo se organiza en cinco categorías — «Roles y entidades / Componentes del protocolo / Objetos de datos del protocolo / Niveles y políticas / Presupuestos predeterminados» — para comodidad de la referencia cruzada.

### A.1 Roles y entidades

| Término del protocolo (inglés) | Término del blueprint | Relación / nota |
| --- | --- | --- |
| Human Prime (HP) | Human Prime (人类原型) | Sinónimo; el único punto final último que asume la responsabilidad y el poseedor del poder de revocación de la relación Faying; también la única entidad que puede dar un reconocimiento explícito de los cambios de estado Faying |
| iFay Instance (IF) | iFay Instance (iFay 实例) | Sinónimo; la entidad agente mandatada, identificada de forma única por FayID; no posee el poder de revocar su propio Mandate; todos los cambios de estado están condicionados al reconocimiento explícito del HP |
| Supervisory Agent (SA) | Supervisory Agent | Una clase de regulador distinta del Prime y reconocible a nivel de protocolo; no posee poder de revocación; no puede sustituir al HP en completar el reconocimiento Faying |
| Relying Party (RP) | Relying Party (受调用方) | El terminal, aplicación o servicio llamado por el iFay |
| Presence Device (PD) | Presence Device (在场设备) | Hardware que porta las credenciales WebAuthn / FIDO2 y las capacidades biométricas; la fuente física de las señales de presencia |

### A.2 Componentes del protocolo

| Término del protocolo (inglés) | Abrev. | Descripción |
| --- | --- | --- |
| Mandate Service | MS | El servicio lógico que emite / renueva / degrada / revoca Mandates en nombre del HP (véase §3.1) |
| Presence Channel | PC | El flujo de presencia de baja latencia y resistente a repetición desde el PD al MS (véase §3.2) |
| Attestation Chain | AC | La cadena de firmas trazable en reverso formada por todas las acciones de emisión HP → MS → IF → IF derivado (véase §3.3) |
| Revocation Registry | RR | Servicio de estado de revocación en tiempo real (véase §3.4) |
| Liveness Channel | LC | Flujo de detección de desconexión (incluidas la desconexión real y la desconexión percibida) (véase §3.5, §9.9) |
| Behavior Baseline Service | BBS | Servicio estadístico que mantiene la línea base de comportamiento (HP, IF) (véase §3.6) |

### A.3 Objetos de datos del protocolo

| Término del protocolo (inglés) | Término del blueprint | Descripción |
| --- | --- | --- |
| Mandate | Mandate (授权令) | Un concepto nuevo a nivel de protocolo; porta los campos `(issuer, subject, scope, grade, presence_req, not_before, not_after, attestation, signature, endorsement?)` (véase §4.1 / §4.2) |
| Endorsed_Mandate | Endorsed Mandate (背书式授权) | Un subtipo de Mandate; declara explícitamente `endorsement = (enabled, endorsed_scope ⊆ scope, endorsed_grade.autonomy ≤ grade.autonomy, endorsed_lifetime, offline_revocation_policy)`, permitiendo al IF operar de forma autónoma dentro de un envoltorio restringido durante la desconexión física; el punto final que asume la responsabilidad es siempre el HP (véase §7.5, P16.x) |
| PresenceSignal | Presence Signal (在场信号) | Una aserción de presencia física producida por el PD y verificable por el MS |
| Attestation | Attestation (证言) | Portador unificado de aserciones verificables (WebAuthn / TPM-quote / Platform-keystore / Self-signed) |
| FayID | FayID | La identidad única unificada del iFay dentro del marco iFay (similar a ULID) |
| Faying_State | Faying State (受控状态) | El estado de comportamiento en que se encuentra el IF cuando el Mandate está en Active / Degraded / Disconnected |
| Rogue_Fay | Rogue Fay (脱离状态) | El estado de comportamiento en que se encuentra el IF cuando el Mandate está en Unpaired / Revoked o ausente; binario mutuamente excluyente con Faying_State (P15). **Nota**: `Suspended` *no* se clasifica como Rogue_Fay — es «Faying State en pausa» (la relación de supervisión persiste, los metadatos del Mandate se retienen y el HP puede reanudarlo explícitamente sin un nuevo BOOTSTRAP); solo comparte con Rogue la prohibición de dimensión D como consecuencia de comportamiento; véase la tabla de correspondencia de §4.3 / §8.2 |
| Faying_Initiation | Iniciación Faying bidireccional (双向 Faying 发起) | La iniciación de la relación Faying (establecimiento o ajuste) puede iniciarse bien por el HP (iniciada por HP) o por el IF buscando Faying ante el HP (iniciada por IF / FAYING_REQUEST); la condición de efectividad final es que el HP dé un reconocimiento explícito y verificable (véase §5.3.6, P16.6) |
| Behavior_Baseline | Línea base de comportamiento (行为基线) | El perfil acumulativo de comportamiento (HP, IF) mantenido por el BBS, usado para detectar desviaciones súbitas (véase §3.6, P18.5) |
| Atomic_Action | Acción atómica (原子动作) | La unidad de declaración indivisible más pequeña que el IF ejecuta hacia el exterior; una llamada corresponde a exactamente 1 Atomic_Action; el empaquetado está prohibido (véase P18.2) |
| Disclosure_Report | Mensaje de divulgación (披露报文) | El mensaje estructurado que el IF usa al informar o solicitar confirmación; los `mandatory_fields` son obligatoriamente analizables (véase §5.3.7, P18.3) |
| Ego | Ego (自我边界) | Sinónimo; usado para la decisión de `ego-deviation` (véase §3.6, §9.10.4) |
| Human View | Human View (人类视野) | Marco de valores; el Faying Protocol es su materialización a nivel de protocolo (capítulo 11 del blueprint) |

### A.4 Niveles y políticas

| Término del protocolo (inglés) | Descripción |
| --- | --- |
| Authorization_Grade (Grade) | Nivel de autorización, valor `G0..G4` (véase §7) |
| G0 Emergency_Override | Nivel de toma de control de emergencia; recuperación forzada unilateral del HP (véase §7.1, P12) |
| G1 Strict | El escalón más estricto; el nivel predeterminado para las acciones de alta sensibilidad |
| G2 Moderate | Escalón medio |
| G3 Loose | Escalón laxo |
| G4 Autonomous | El escalón más autónomo; la pérdida de heartbeat de G4 directamente → Suspended (véase §7.3) |
| PresenceRequirement | Requisito de presencia; la tripleta `(signal_types, max_staleness_ms, on_loss)` ligada al nivel |
| Scope | Alcance de la autorización; el conjunto de mínimo privilegio de declaración explícita `(domains, actions, terminals?, budget?)` |

### A.5 Presupuestos predeterminados (valores detallados en el Anexo B)

| Término del protocolo (inglés) | Resumen |
| --- | --- |
| MaxMandateLifetime | Vigencia máxima de un único Mandate (predeterminado 24 h, límite superior 30 d) |
| BootstrapTimeout | Timeout que BOOTSTRAP / FAYING_REQUEST espera el testimonio del HP (predeterminado 60 s) |
| RevocationVisibilityBudget | Presupuesto para que la revocación sea visible en la red del RR (predeterminado 1 s) |
| StaleBudget | Umbral de rechazo por RR inalcanzable (predeterminado 5 s) |
| HumanReachabilityBudget | Umbral en el que la inalcanzabilidad del HP dispara Revoke automático (predeterminado 30 min) |
| LivenessDetectionBudget | Límite superior de la ventana de detección de desconexión; ajustado monótonamente por nivel (véase el Anexo B, P17.3) |
| AttentionDriftThreshold | Umbral en el que la inactividad en la vista del HP dispara la «pérdida de atención»; ajustado por nivel (véase el Anexo B, P18.4) |
| ConfirmationRateLimit | Límite superior de solicitudes de confirmación empujadas al HP por unidad de tiempo; la superación del límite dispara auto-degradación / suspensión (véase el Anexo B, P18.6) |
| MaxDegradedDuration | Duración máxima del estado Degraded (predeterminado 5 min/nivel) |
