---
title: "Faying Protocol/1.0 — §1 Visión general"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: es
part: "Capítulo 1 de 11 (cuerpo del protocolo)"
---

> Navegación del cuerpo del protocolo: [Índice](./README.md) | siguiente [§2 Arquitectura](./02-Arquitectura.md)

## §1 Visión general

Este capítulo define qué es el Faying Protocol, qué resuelve y qué no: la denominación del protocolo, su posición en la pila tecnológica, el esqueleto de los objetivos de diseño, las diferencias esenciales frente a los esquemas existentes, la definición en una sola frase del Faying Protocol, el alcance entregable y los no-objetivos de este cuerpo del protocolo, y las reglas de gestión de versiones y compatibilidad. Es el ancla semántica de los §2–§11 y los Anexos A/B que siguen.

> **Nota sobre la trazabilidad EARS**: cada regla de este capítulo va seguida de una línea `Trace:` que enumera los identificadores de subcláusula EARS correspondientes (de la base de requisitos) con la forma `R<requirement>.<criterion>.<clause>`.

### §1.1 Denominación del protocolo

Nombre de la especificación del protocolo: **Faying Protocol**. El número de versión se escribe de forma uniforme como **Faying Protocol/1.0**.

Este protocolo **suprime la abreviatura FAP (Faying Auth Protocol)** — **el nombre del protocolo es Faying Protocol, sin abreviatura propia**; si se necesita una forma corta, debe usarse el nombre completo «Faying Protocol». Este documento de diseño y las especificaciones que lo acompañan ya no contienen formas históricas de denominación como `FAP` / `FAP/1.0` / `Faying Auth Protocol` / `application/fap+json` / `POST /fap/v1/...`. Cualquier referencia anterior a `FAP` debe entenderse como una referencia heredada al Faying Protocol y sustituirse por Faying Protocol en los documentos nuevos.

> **Herencia histórica de denominación**: los borradores tempranos usaban «Faying Auth Protocol (FAP)». Esa denominación queda suprimida; toda referencia externa a `FAP` debe entenderse como una referencia heredada al Faying Protocol y no debe reutilizarse en documentos nuevos.

### §1.2 Posicionamiento del protocolo

> **El Faying Protocol es un protocolo de «capa de autorización continua» de nivel de aplicación situado sobre TLS, que porta la semántica de «bajo qué estado de presencia, sobre qué alcance, en qué nivel y durante qué ventana de tiempo un Human Prime autoriza a su iFay».**

- **Por debajo de TLS**: la confidencialidad del canal y la identidad del extremo remoto las aporta TLS 1.3 (con mTLS opcional); el Faying Protocol no las rehace.
- **Junto a OAuth/OIDC**: OAuth proporciona autorización de nivel de aplicación, OIDC emite aserciones de identidad; ambos son modelos de «token instantáneo». El Faying Protocol resuelve lo que ninguno de los dos resuelve — **agencia continua + vinculación de presencia + conmutación de nivel + responsabilidad única**.
- **Por encima de WebAuthn**: WebAuthn / FIDO2 proporciona pruebas de «presencia de usuario» de nivel hardware para el Human Prime durante el arranque (bootstrapping); el Faying Protocol reutiliza su forma de credencial como raíz de la confianza derivada.

El Faying Protocol no sustituye a TLS, ni reinventa OAuth; se sitúa sobre TLS y por debajo de la semántica de negocio, obligando a que **toda acción saliente de un iFay** atraviese la puerta de verificación del Mandate. Cualquier llamada saliente que eluda esta puerta se trata como una Rogue Action y debe ser rechazada por un middleware situado por encima de la capa de transporte y por debajo de la capa de negocio.

### §1.3 Objetivos de diseño

La tabla siguiente enumera los **8 objetivos de diseño G1–G8 del Faying Protocol** (objetivos centrales) y 2 objetivos de ingeniería derivados de §9 / §5 (propiedades de seguridad / interoperabilidad del protocolo). **Cada objetivo se alinea con exactamente un Requirement de la base de requisitos**, formando el ancla de trazabilidad bidireccional entre este cuerpo del protocolo y el documento de Requirements.

| Objetivo | Significado | Origen en el blueprint | Requirement correspondiente |
| --- | --- | --- | --- |
| **G1 Responsabilidad única** | En cualquier instante, la acción saliente de un iFay puede atribuirse inequívocamente a un único Human Prime | Línea ética de fondo del capítulo 13 | Requirement 1 |
| **G2 Default-Deny** | Sin Mandate válido → ninguna acción saliente; cualquier campo ausente → rechazo | Default Rogue del capítulo 13 | Requirement 2 |
| **G3 Observable, auditable, revocable** | Las transiciones de estado, la iniciación de acciones y los eventos de renovación/revocación son todos observables, auditables y verificables de forma independiente | Capítulos 11, 13 | Requirement 3 |
| **G4 Revocación simétrica** | La alcanzabilidad de las vías de revocación ≥ la de las vías de establecimiento; la revocación es irreversible | Capítulos 10, 12 | Requirement 4 |
| **G5 Calibración continua** | Las señales de presencia y el nivel del Mandate pueden reconfirmarse en todo momento; la confianza nunca persiste más allá de su caducidad | Capítulos 11, 12 | Requirement 5 |
| **G6 Autorización graduada** | Un único Mandate no puede representar todas las intensidades; el nivel debe ser expresable, conmutable y degradable; las elevaciones requieren testimonio del HP | Punto 3 del brief original | Requirement 6 |
| **G7 Derivación entre dispositivos** | Cuando el mismo iFay trabaja en varios terminales, la confianza puede derivarse pero el responsable nunca cambia; alcance/nivel convergen estrictamente | Reserva evolutiva de la fase 2/3 | Requirement 7 |
| **G8 Evolucionabilidad poscuántica** | Las suites de algoritmos pueden negociarse y avanzarse (roll forward); bits de negociación PQC reservados | Requisito común de ingeniería | Requirement 8 |
| —(derivado) **Propiedades de seguridad** | Anti-replay / anti-secuestro / anti-phishing / detección de desconexión / amenazas adversarias de la era de la IA | §9 Consideraciones de seguridad | Requirement 9 (con derivación de Requirement 13) |
| —(derivado) **Interoperabilidad del protocolo** | Equivalencia CBOR / JSON, Deterministic CBOR, matriz de compatibilidad entre implementaciones | §5 Mensajes del protocolo | Requirement 10 |

> **Principio de correspondencia uno-a-uno objetivo ↔ Requirement**: esta tabla es la **única correspondencia autoritativa** entre el cuerpo del protocolo y el documento de Requirements. Todo identificador de subcláusula EARS `R<n>.<m>.<k>` citado en capítulos posteriores al enunciar una invariante o un mecanismo debe tener su número de Requirement raíz `<n>` dentro de la columna «Requirement correspondiente». Endorsed_Mandate (Requirement 11) derivado de G6 / G4 / G5 / G7, la política de desconexión (Requirement 12) y la protección de la era de la IA (Requirement 13) actúan como refinamientos de G1–G8 y reciben su aterrizaje a nivel de protocolo en §4 / §8 / §9 respectivamente.

### §1.4 Diferencias esenciales frente a los esquemas existentes (edición de una línea)

| Esquema existente | Resuelve | NO resuelve — lo que el Faying Protocol debe resolver |
| --- | --- | --- |
| OAuth 2.0 / 2.1 | Autorización de acceso de aplicación sobre recursos | Token de un solo uso, sin nivel, sin presencia, sin revocación simétrica |
| OIDC SSO | Aserción de identidad (quién) | Sin agencia continua (actuar en nombre de), sin nivel |
| mTLS | Identidad del extremo en ambos lados del canal | No puede expresar «quién, bajo qué estado de presencia, delegó en quién para hacer qué» |
| JWT | Reclamaciones autocontenidas con firma | Sin revocación, sin semántica de nivel, la larga vigencia choca con la «revocación simétrica» |
| FIDO2 / WebAuthn | Prueba de presencia de nivel hardware para el Human Prime | Cubre solo el momento del inicio de sesión, no la agencia continua del iFay |
| Macaroons | Tokens derivables con caveats | Sin vinculación de presencia, sin testimonio explícito del Human Prime |
| SPIFFE / SPIRE | Identidad de carga de trabajo | Vista del lado de la carga de trabajo, sin punto final de responsabilidad humana |

El Faying Protocol no compite con ninguno de los anteriores — se sitúa sobre TLS y por debajo de la semántica de negocio, aportando la **semántica dedicada** de «Human Prime ↔ iFay»: agencia continua + vinculación de presencia + conmutación de nivel + responsabilidad única + revocación simétrica.

### §1.5 Definición en una sola frase

> **Faying Protocol = «Mandate (en lugar de token) + Presence Signal + Attestation Chain + Revocation Registry» — cuatro elementos expresados de forma cooperativa sobre TLS, iniciados bidireccionalmente por el Human Prime y el iFay, que solo cobran efectividad mediante el reconocimiento explícito del Human Prime, calibrados de forma continua y revocables simétricamente.**

#### §1.5.1 Los cambios de estado Faying solo cobran efecto con el reconocimiento explícito del Human Prime (aserción central)

La iniciación de la relación Faying (establecimiento o ajuste) es **bidireccional**:

- **Iniciada por HP**: el Human Prime puede iniciar Faying de forma proactiva a través del canal BOOTSTRAP (véase §2.4 Fase A, §5.3.1).
- **Iniciada por IF**: el iFay puede buscar Faying de forma proactiva ante el Human Prime (es decir, FAYING_REQUEST) a través de la vía de dos pasos §2.4 Fase A0 → BOOTSTRAP (véase §5.3.6).

> **Sin embargo, sea cual sea el lado que inicia, la condición de efectividad final de cualquier cambio de estado Faying es que el Human Prime emita un reconocimiento explícito, no engañado y verificable** (cuya forma predeterminada es una aserción de presencia de usuario WebAuthn o una prueba equivalente de nivel hardware).

De inmediato se siguen tres restricciones duras inquebrantables:

1. **El iFay por sí solo no puede hacer efectivo Faying**: un FAYING_REQUEST iniciado por IF que no reciba el reconocimiento explícito del HP dentro de `BootstrapTimeout` (predeterminado 60 s, véase el Anexo B) caduca o es rechazado y **no produce ningún cambio de estado Faying**. Mandate_Service debe devolver `E_FAYING_REQUEST_NOT_CONFIRMED` (código de error 1014) y escribir el evento en la Attestation Chain para preservar evidencia irreversible de «quién inició, cuándo se confirmó, si fue efectivo».
   - **Trace**: `R1.3.2` (la vía iniciada por IF solo cobra efecto tras el reconocimiento explícito del HP), `R1.3.3` (rechazo sin cambio de estado cuando transcurre `BootstrapTimeout` sin reconocimiento), `R1.3.4` (evento escrito en la AC independientemente de la efectividad).
2. **Ninguna vía de testimonio por sustitución**: en la capa de protocolo no existe ninguna vía legítima para que el iFay, Mandate_Service o Supervisory_Agent sustituyan al Human Prime en completar el reconocimiento Faying. Cualquier BOOTSTRAP que carezca de `human_witness` o cuyo `human_witness` falle la verificación debe rechazarse con `E_HUMAN_WITNESS_REQUIRED` (código de error 1010).
   - **Trace**: `R1.3.5` (ninguna vía legítima para que IF / MS / SA sustituyan al HP en completar el reconocimiento Faying).
3. **El iFay no puede eludir unilateralmente la revocación**: el iFay puede emitir un mensaje de «solicitud de desconexión de Faying» (tratado como un Disclosure_Report), pero el iFay no posee el poder de revocar su propio Mandate; cualquier revocación debe iniciarla en última instancia el Human Prime o un regulador/autoridad y hacerse visible a través del canal de vista del HP (véase §4 / §10).
   - **Trace**: `R4.1.4` (IF no posee el poder de revocar su propio Mandate), `R4.1.5` (la solicitud de desconexión se registra como Disclosure_Report en la AC y se empuja al canal de vista del HP).

Esta subsección es el ancla unificada del capítulo de Visión general para §2.4 Fase A0, §5.3.6 FAYING_REQUEST y §5.4 códigos de error 1010 / 1014, y el punto de partida de los argumentos de todos los capítulos posteriores de que «sin testimonio del HP, no hay Faying».

### §1.6 Alcance entregable del protocolo y no-objetivos

#### §1.6.1 En el alcance (Normativo — soportado por este cuerpo del protocolo)

Este cuerpo del protocolo (es decir, este único archivo) especifica, **y solo especifica**, lo siguiente:

- **Objetos de datos del protocolo**: el formato primario CBOR y el formato de reserva JSON para Mandate / Presence_Signal / Attestation / SignatureBundle / Faying Protocol Envelope / Endorsed_Mandate / Disclosure_Report, etc. (CDDL es autoritativo; véase §4 / §5).
  - **Trace**: `R10.1.1`, `R10.1.2`, `R10.2.1`–`R10.2.4`.
- **Interfaces de los componentes del protocolo**: límites de responsabilidad e invariantes de Mandate_Service / Presence_Channel / Attestation_Chain / Revocation_Registry / Liveness_Channel / Behavior_Baseline_Service (véase §3).
- **Mensajes del protocolo**: definiciones de campos, códigos de error y restricciones duras a nivel de protocolo para los siete tipos de mensaje BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE / REVOKE / FAYING_REQUEST / DISCLOSURE (véase §5).
- **Reglas criptográficas**: negociación de suites de algoritmos, jerarquía de derivación de claves, canonicalización de la entrada de firma (incluido el ancla de entrada de firma del Endorsed_Mandate; véase §6).
  - **Trace**: `R8.1.1`–`R8.1.4`, `R8.2.1`–`R8.2.4`.
- **Semántica de los niveles de autorización**: definiciones precisas de los cinco niveles G0–G4, la matriz de condiciones de disparo, el principio de monotonía de degradación y los subniveles Endorsement Grades (véase §7).
  - **Trace**: `R5.1.1`, `R6.1.1`, `R6.1.2`.
- **Ciclo de vida y máquina de estados**: los siete estados Unpaired / Pairing / Active / Degraded / Disconnected / Suspended / Revoked, sus condiciones de transición y la transacción de reconciliación (véase §8).
- **Consideraciones de seguridad**: modelo de amenazas STRIDE, anti-replay / anti-secuestro / anti-phishing / detección de desconexión, transferencia de confianza derivada entre dispositivos y las amenazas adversarias de la era de la IA T1–T7 (véase §9).
- **Manejo de errores**: respuestas del protocolo, vías de recuperación, restricciones de observabilidad y convergencia Default-Deny para los 14 códigos de error (incluidos 1010 `E_HUMAN_WITNESS_REQUIRED`, 1013 `E_ENDORSEMENT_INVALID`, 1014 `E_FAYING_REQUEST_NOT_CONFIRMED`; véase §10).
  - **Trace**: `R2.1.1`–`R2.1.4` (Default-Deny), `R3.3.1` (el canal de vista del HP debe alcanzarse).
- **Anexos**: referencia rápida de alineación de terminología (Anexo A), presupuestos de parámetros predeterminados (Anexo B).

#### §1.6.2 Fuera del alcance (No normativo — no soportado por este protocolo)

Lo siguiente **no** está en el alcance normativo de este cuerpo del protocolo y sirve únicamente como implementación de referencia / guía de ingeniería; no guarda relación con la conformidad de interoperabilidad frente a este cuerpo del protocolo:

- **Semántica de negocio**: el comportamiento de negocio concreto del iFay, los controladores de terminal, los patrones de integración de aplicaciones;
- **Diseño de UI / UX**: la presentación concreta del canal de vista del Human Prime, el diseño de los diálogos de confirmación, las interacciones móviles / de escritorio;
- **Operaciones y despliegue**: modelos de despliegue de alta disponibilidad, estrategias de escalado, sincronización entre regiones para Mandate_Service / Revocation_Registry;
- **Detalles de la capa de transporte**: los detalles del handshake del propio TLS 1.3 (especificado por RFC 8446), los parámetros de ajuste concretos para HTTP/2 / gRPC / QUIC;
- **Implementaciones de PD (Presence Device)**: las implementaciones hardware del autenticador WebAuthn / TPM / Platform Keystore (especificadas por W3C / ISO / TCG);
- **Detalles legales y de cumplimiento**: cómo actúan los reguladores / organismos de cumplimiento como «autoridades» legales fuera del protocolo (la capa de protocolo especifica solo su posición en el enum RevokeReason y el requisito de cadena de firmas, no su constitución legal);
- **Código de implementación de referencia**: cualquier implementación de referencia de este protocolo (como la vista TypeScript [`schemas/types.ts`](../../../../schemas/types.ts) o el conjunto de pruebas basadas en propiedades `pbt/`) está explícitamente etiquetada como **«Implementación de referencia, no normativa»** y no constituye el cuerpo del protocolo;
- **Cuestiones abiertas**: todos los puntos de §11 Cuestiones abiertas cuyo `status: open`.

#### §1.6.3 Principio de entrega en archivo único

> **El cuerpo del protocolo es este único archivo `docs/en/specification/2025-10-25/Faying-Protocol-1.0.md`.**

Los demás archivos Markdown bajo `docs/en/specification/2025-10-25/` son documentos auxiliares únicamente (README / CHANGELOG) y **no constituyen el cuerpo del protocolo**. Conviene observar que ambos lados son **estructuralmente asimétricos**: el lado inglés es un único archivo (`Faying-Protocol-1.0.md`, con §1–§11 y los Anexos A/B incorporados), mientras que el lado chino en `docs/zh-CN/specification/2025-10-25/` se divide en 11 archivos de capítulo más los Anexos A/B/C. El archivo único inglés se alinea, por tanto, con el conjunto de capítulos chino al **nivel de ancla de sección** (numeración de secciones, diagramas Mermaid, bloques de código CDDL / TypeScript, tabla de códigos de error y Anexos A / B), no archivo por archivo; el registro de cambios (Anexo C) se mantiene solo en el lado chino. Cuando surja ambigüedad entre la redacción china e inglesa, en caso de discrepancia prevalece la versión de referencia, y la versión inglesa se corrige en la siguiente reunión de revisión.

### §1.7 Gestión de versiones y compatibilidad

Esta sección es la **definición autoritativa** del versionado del Faying Protocol. El número de versión no es un simple marcador documental — es **parte del contrato de interoperabilidad**: aparece en el envoltorio (envelope) de transmisión, en los esquemas y en la negociación, y determina directamente si dos implementaciones independientes pueden comunicarse entre sí. Por ello esta sección es Normativa: las implementaciones DEBEN interpretar los números de versión y realizar la negociación de versión conforme a las reglas siguientes. El Anexo C (registro de cambios) solo registra el histórico; no redefine estas reglas.

#### §1.7.1 Tres ejes de versión ortogonales

El Faying Protocol describe la versión de una especificación con **tres ejes mutuamente independientes** que NO DEBEN fundirse en un solo número:

| Eje | Pregunta que responde | Forma | Portador | Ejemplo |
| --- | --- | --- | --- | --- |
| **Versión del protocolo** (contrato de interoperabilidad) | ¿Pueden comunicarse dos implementaciones? | `MAJOR.MINOR` | prosa / campo `version` del envelope de transmisión / nombre de archivo del esquema | `Faying Protocol/1.0` |
| **Estado del documento** (ciclo de vida) | ¿Está finalizada esta especificación? | enum | `status` del front matter | `Draft` / `Final` / `Deprecated` / `Obsolete` |
| **Edición editorial** (erratas y aclaraciones) | ¿Qué revisión textual bajo la misma versión del protocolo? | fecha de publicación | nombre del directorio de publicación / `date` del front matter | `2025-10-25` |

> **Restricción central**: **solo la «versión del protocolo» `MAJOR.MINOR` entra en el formato de transmisión** (el campo `version` del envelope, los nombres de archivo de esquema). El estado del documento y la edición editorial NO DEBEN entrar en el formato de transmisión — son marcadores de gobernanza documental y no participan en las decisiones de interoperabilidad. Una implementación NO DEBE cambiar su comportamiento de manejo de mensajes porque el estado del documento o la edición editorial de un par difieran.

#### §1.7.2 Semántica de la versión del protocolo `MAJOR.MINOR`

La versión del protocolo se escribe `Faying Protocol/MAJOR.MINOR`, con **solo dos niveles y sin PATCH** — el formato de transmisión y la semántica de interoperabilidad distinguen solo dos escalones de compatibilidad.

- **MAJOR (cambio rompedor)**: cualquier cambio que haría que un par implementado estrictamente según la especificación antigua **rechazara o malinterpretara** los mensajes nuevos. Ejemplos: cambiar la semántica de un campo CDDL autoritativo de §4.2, eliminar un tipo de mensaje, redefinir la semántica de un código de error, cambiar un estado absorbente de la máquina de estados.
  - Regla: incrementar MAJOR, reiniciar MINOR a cero (p. ej. `1.4 → 2.0`).
  - Compatibilidad: la interoperabilidad entre distintos MAJOR **no está garantizada**.
- **MINOR (adición compatible hacia atrás)**: una adición que una implementación nueva puede entender en mensajes antiguos y que una implementación antigua puede ignorar de forma segura donde no reconoce elementos opcionales. Ejemplos: añadir campos opcionales, añadir mensajes o códigos de error, añadir entradas al catálogo de amenazas de la era de la IA, añadir parámetros de anexo, añadir Correctness Properties.
  - Regla: incrementar MINOR (p. ej. `1.0 → 1.1`).
  - Compatibilidad: dentro del mismo MAJOR, un MINOR superior **DEBE** seguir siendo compatible hacia atrás con los MINOR inferiores.

**Prueba de decisión (autoverificación del implementador)**: ¿el cambio haría que un par implementado estrictamente según la especificación antigua rechazara o malinterpretara los mensajes nuevos?

- Sí → **MAJOR**;
- No, pero añade contenido visible en la transmisión → **MINOR**;
- Solo cambia el texto, no ninguna semántica del formato de transmisión (corrección de erratas, ejemplos añadidos, ambigüedad aclarada) → **no cambiar la versión del protocolo**; usar la edición editorial de §1.7.4.

La línea base actual es `Faying Protocol/1.0`.

#### §1.7.3 Negociación de versión y reglas de compatibilidad (Normativo)

La negociación de versión **reutiliza el mismo enfoque que la negociación de suites de algoritmos de §6.1** (cada lado declara, se elige el valor más alto soportado en común). Las implementaciones DEBEN:

1. **Declarar**: durante BOOTSTRAP, cliente y servidor declaran cada uno su conjunto de versiones de protocolo soportadas (p. ej. `supported: [1.0, 1.1]`).
2. **Mismo MAJOR → MINOR más alto**: cuando ambos lados comparten un MAJOR, DEBEN seleccionar el **MINOR más alto** soportado en común como la versión efectiva para la sesión; una implementación de MINOR superior DEBE poder atender a un par de MINOR inferior (compatible hacia atrás hasta `MAJOR.0`).
3. **Cruce de MAJOR → rechazo**: cuando no existe un MAJOR común, no se produce negociación; el BOOTSTRAP DEBE rechazarse con `E_PROTOCOL` (código de error 1099); no se permite ninguna interoperabilidad degradada de «mejor esfuerzo».
4. **La actualización progresiva no debe romper los Mandates existentes**: cuando se introduce una nueva suite de algoritmos predeterminada o un nuevo MINOR mediante la negociación de versión, los Mandates existentes DEBEN seguir siendo verificables antes de su `not_after`; una actualización de versión NO DEBE invalidar los Mandates válidos en curso.
   - **Trace**: `R8.2.4` (actualización progresiva mediante negociación de versión sin romper la verificabilidad de los Mandates existentes).
5. **Manejo de un MINOR superior desconocido**: al recibir un mensaje declarado con el mismo MAJOR pero un MINOR superior al propio, una implementación DEBE interpretarlo a su MINOR soportado más alto e **ignorar** los campos opcionales que no reconozca (en lugar de rechazarlo); este es el aterrizaje en tiempo de ejecución de la promesa de compatibilidad hacia atrás de MINOR.

#### §1.7.4 Edición editorial y erratas (cambios no normativos)

Tras finalizar (Final) `Faying Protocol/1.0`, las erratas puramente textuales son inevitables — corrección de erratas, ejemplos añadidos, ambigüedad aclarada, enlaces internos corregidos. Tales cambios:

- NO DEBEN cambiar el número de versión del protocolo (hacerlo afirmaría falsamente que el contrato de interoperabilidad cambió);
- se anclan por **fecha de publicación**: p. ej. `Faying Protocol/1.0 (2025-10-25)` es la primera edición Final de 1.0; las erratas posteriores producen un nuevo directorio de publicación (p. ej. `2026-03-xx/`) mientras la versión del protocolo permanece en `1.0`;
- se registran en el registro de cambios del Anexo C bajo una categoría `Editorial`, marcando la transición de edición mediante un campo `edition` del front matter;
- **Restricción dura**: una edición editorial solo puede portar cambios no normativos. Cualquier modificación que toque la semántica del formato de transmisión DEBE incrementar MINOR o MAJOR y NO DEBE publicarse disfrazada de errata editorial.

#### §1.7.5 Dónde aterriza el número de versión y notas para los implementadores estándar

La tabla siguiente indica exactamente dónde aterriza el número de versión, para que los implementadores puedan juzgar qué diferencias afectan a la interoperabilidad y cuáles no:

| Aterrizaje | Qué se escribe | Notas |
| --- | --- | --- |
| Campo `version` del envelope de transmisión (§5.2) | `"Faying Protocol/MAJOR.MINOR"` | **solo MAJOR.MINOR**; sin fecha de edición, sin estado de documento |
| Nombre de archivo de esquema (`fap-1.0.cddl`, etc.) | sigue a `MAJOR.MINOR` | el nombre de archivo **no cambia entre ediciones editoriales** — las erratas no renombran `fap-1.0.cddl`, manteniendo estables las referencias existentes (el prefijo heredado `fap` conservado sigue el mismo razonamiento; véase el Anexo C) |
| content-type (§5.1) | `application/faying-protocol+cbor` (o `+json`) | el content-type identifica la familia del protocolo; puede adjuntarse un parámetro `version=` para el enrutamiento a nivel de pasarela como **comodidad de despliegue**, pero ese parámetro no forma parte de la semántica del formato de transmisión y no afecta a las decisiones de compatibilidad |
| `status` / `date` del front matter | estado del documento / edición editorial | marcadores de gobernanza documental; **no entran en el formato de transmisión**; un par NO DEBE alterar el manejo de mensajes basándose en ellos |
| etiqueta git | `faying-protocol-v<MAJOR.MINOR>-<status>` | finalización `faying-protocol-v1.0-final`; instantánea de edición `faying-protocol-v1.0-2026-03-xx`; una etiqueta DEBE cubrir simultáneamente el cuerpo + `vectors/` + `schemas/`, congelando juntos el trío de interoperabilidad |

**Notas obligatorias para los implementadores estándar**:

1. **La interoperabilidad se juzga solo por la versión del protocolo**: la única base para «¿podemos comunicarnos?» es `MAJOR.MINOR`. El estado del documento de un par (Draft/Final) y la edición editorial (fecha de publicación) **no** cambian el comportamiento de interoperabilidad — nunca rechaces los mensajes válidos de un par solo porque esté marcado como Draft o tenga una edición más antigua.
2. **El mismo MAJOR debe ser compatible hacia atrás**: al implementar un MINOR superior, DEBES atender también correctamente a todos los pares de MINOR inferior a partir de `MAJOR.0`.
3. **No trates las erratas como actualizaciones**: un cambio en la fecha del directorio de publicación (edición editorial) no significa que el protocolo haya cambiado; solo un cambio en `MAJOR.MINOR` requiere evaluar el impacto en la interoperabilidad.
4. **Estabilidad del nombre de archivo de esquema**: no te apoyes en el nombre de archivo para codificar la edición; las erratas del mismo `MAJOR.MINOR` reutilizan el archivo de esquema homónimo, distinguido por etiqueta git / directorio de publicación.
5. **Sin promesa de compatibilidad durante Draft**: mientras `status: Draft`, `MAJOR.MINOR` puede ajustarse antes de la congelación; las promesas de compatibilidad MAJOR/MINOR de esta sección solo cobran pleno efecto tras `Final`.
