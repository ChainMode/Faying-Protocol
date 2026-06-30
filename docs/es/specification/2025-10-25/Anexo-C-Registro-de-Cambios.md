---
title: "Faying Protocol/1.0 — Anexo C Registro de cambios"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: es
part: "Anexo C (registro de cambios)"
---

> Navegación del cuerpo del protocolo: [Índice](./README.md) | anterior [Anexo B Presupuestos de parámetros predeterminados](./Anexo-B-Presupuestos-de-Parametros-Predeterminados.md)

## Anexo C Registro de cambios

Este registro documenta qué cambios han experimentado el cuerpo de la especificación y los entregables que la acompañan en el borrador de Faying Protocol/1.0 desde el primer trazo hasta su finalización. En cuanto al formato, sigue las convenciones de agrupación de [Keep a Changelog](https://keepachangelog.com) (Added / Changed / Deprecated / Removed / Security), y explica de antemano cómo se fija el número de versión.

> Nota honesta sobre el origen: el borrador 1.0 de este protocolo se produjo de una sola vez siguiendo un flujo dirigido por la especificación (requisitos → diseño → lista de tareas → implementación), y aún no ha pasado por varias rondas de reuniones independientes del Protocol Committee. Por ello este registro no falsea resoluciones de reunión punto por punto ni fechas precisas, sino que documenta con fidelidad «qué se hizo, por qué y a qué tarea corresponde». Los números de tarea citados a continuación (como 1.6, 3.8, 5.6) corresponden a entradas reales del plan de tareas de implementación, lo que permite retrotraer la ubicación de producción de cada cambio. Si más adelante se entra en un proceso formal de revisión del comité, se añadirán aquí entradas con fecha y número de resolución.

## Cómo se fija el número de versión

Las **reglas autoritativas del versionado del protocolo están en §1.7 Gestión de versiones y compatibilidad** (tres ejes ortogonales: versión del protocolo `MAJOR.MINOR` / estado del documento / edición editorial; reglas de negociación y compatibilidad; aterrizajes del número de versión y notas para los implementadores). Este anexo no las redefine, solo añade dos puntos relacionados con el registro de cambios:

- Este registro clasifica cada cambio según el criterio MAJOR / MINOR de §1.7.2: lo que rompe la interoperabilidad va a MAJOR, las adiciones compatibles hacia atrás van a MINOR, y las erratas puramente textuales se agrupan, conforme a §1.7.4, en `Editorial` sin tocar el número de protocolo.
- Actualmente es `Faying Protocol/1.0`, la primera línea base, en estado Final (publicado el 2025-10-25).

En cuanto a la denominación, la prosa y el número de versión usan de forma uniforme `Faying Protocol/1.0`; la antigua abreviatura `FAP` queda suprimida. Pero los nombres de archivo de esquema `fap-1.0.cddl` / `fap-1.0.proto` conservan el prefijo antiguo, puramente para mantener estables los nombres de archivo y no romper las referencias existentes — esto es intencionado, no una vacilación de nomenclatura (coherente con §1.7.5 «el nombre de archivo de esquema no se renombra entre ediciones editoriales»).

## [Faying Protocol/1.0] — Final (2025-10-25)

Este es el primer lanzamiento oficial de 1.0, migrado como un todo el 2025-10-25 desde el espacio de trabajo del borrador al directorio oficial de publicación y finalizado. A continuación se clasifica por tipo de cambio, anotando cada elemento con el número de tarea que lo produjo.

### Added

Cuerpo del protocolo (§1–§11 + Anexos A/B):

- §1 Overview: denominación del protocolo, posicionamiento, ocho objetivos de diseño G1–G8, correspondencia uno a uno entre objetivos y Requirement; §1.5.1 establece la aserción central de que «todo Faying bidireccional necesita el reconocimiento explícito del HP para cobrar efecto». (tarea 1.2)
- §2 Architecture: cuatro diagramas Mermaid (pila del protocolo, relaciones entre entidades, jerarquía de niveles, secuencia Bootstrap+Heartbeat+Action, incluida la vía Fase A0 iniciada por IF) y seis principios de diseño. (tarea 1.3)
- §3 Components and Interfaces: las interfaces e invariantes de los seis componentes (MS / PC / AC / RR / LC / BBS). (tarea 1.4)
- §4 Data Models: definición autoritativa en CDDL, vista de lectura humana en TypeScript, máquina de estados del Mandate con el estado Disconnected y la reconciliación de reconexión, subestructura endorsement. (tarea 1.5)
- §5 Protocol Messages: siete clases de mensaje (BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE / REVOKE / FAYING_REQUEST / DISCLOSURE), envoltorio unificado, 14 códigos de error — entre ellos los nuevos 1010 `E_HUMAN_WITNESS_REQUIRED`, 1013 `E_ENDORSEMENT_INVALID`, 1014 `E_FAYING_REQUEST_NOT_CONFIRMED`. (tarea 1.6)
- §6 Cryptography: negociación de suites de algoritmos (incluida la ranura de negociación PQC), derivación de claves, formato de firma; el campo endorsement se incorpora a la entrada de firma. (tarea 1.7)
- §7 Authorization Grades: semántica de los cinco niveles G0–G4, matriz de disparo, monotonía de degradación, y los subniveles §7.5 Endorsement Grades superpuestos a G1–G4. (tarea 1.8)
- §8 Lifecycle: ciclo de vida de siete estados (incluido Disconnected), secuencia de atribución de responsabilidad, transacción de reconciliación de reconexión de §8.4. (tarea 1.9)
- §9 Security Considerations: STRIDE, anti-replay / anti-secuestro / anti-phishing, identificación del estado de desconexión, matriz de manejo de pérdida de conexión, y el catálogo de amenazas adversarias de la era de la IA T1–T7 de §9.10. (tarea 1.10)
- §10 Error Handling, §11 Open Questions, Anexos A/B: escenarios de error y vías de recuperación, cuestiones abiertas Q1–Q14, glosario, presupuestos de parámetros predeterminados. (tarea 1.11)
- Traducción completa de la especificación en inglés. (tarea 1.12)

Entregables que acompañan:

- esquema: `schemas/fap-1.0.cddl` (autoritativo), `schemas/types.ts` (vista de lectura humana en TypeScript, Not Normative), `schemas/fap-1.0.proto` (vinculación gRPC alternativa, Not Normative). (tareas 2.1–2.3)
- vectores de prueba `vectors/`: cubren BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE / REVOKE, códigos de error, equivalencia de codificación, Endorsement, FAYING_REQUEST, DISCLOSURE, Disconnection, 11 clases en total. (tareas 3.1–3.11)
- pruebas basadas en propiedades `pbt/`: cubren las propiedades principales P1–P15, más las tres familias P16 (Endorsed_Mandate), P17 (Disconnection), P18 (AI-Era). (tareas 4.1–4.34)
- conjunto de conformidad de interoperabilidad `conformance/`: matriz de cinco dimensiones codificación × algoritmo de firma × hash × canal × lenguaje de implementación, con dos implementaciones de referencia en TypeScript y Rust. (tareas 5.1–5.6)
- simulación de ataques de seguridad `conformance/attacks/`: repetición, secuestro, phishing, identificación del estado de desconexión, y simulaciones de T1/T3/T4/T5/T6. (tareas 6.1–6.10)

### Changed

- La denominación del protocolo pasó de la del borrador temprano «Faying Auth Protocol (FAP)» a **Faying Protocol**, con el número de versión escrito como `Faying Protocol/1.0`. (corresponde a §11 Q10, resuelta)
- La iniciación de Faying se amplió de unidireccional (solo el HP podía iniciar) a bidireccional (iniciada por HP + iniciada por IF), pero la condición de efectividad converge de forma uniforme a «el reconocimiento explícito del HP». (tareas 1.6, 3.9)
- La desconexión se desdobló en dos semánticas, «desconexión real» y «desconexión percibida»; la decisión del protocolo solo mira la desconexión percibida y aplica presunción pesimista a las ventanas de inconsistencia. (tareas 1.10, 3.11)
- La entrada de firma se unificó como `H(Deterministic-CBOR(Envelope_without_signature))`; el formato primario CBOR y el de reserva JSON son equivalentes e interoperables bajo este criterio. (tareas 3.7, 5.2)

### Deprecated

- Las antiguas denominaciones `FAP` / `FAP/1.0` / `Faying Auth Protocol`, así como las antiguas formas de punto final `application/fap+json`, `POST /fap/v1/...`, quedan todas suprimidas. La nueva escritura usa `application/faying-protocol+json` y `POST /faying-protocol/v1/{verb}`. Los nombres de archivo de esquema son la única excepción que conserva el prefijo antiguo (véase arriba «Cómo se fija el número de versión»).

### Removed

- Ninguno. 1.0 es la primera línea base, no hay campos ni mensajes existentes que retirar.

### Security

- Nuevas restricciones a nivel de protocolo para las amenazas adversarias de la era de la IA: T1 ingeniería social, T2 operación de caja negra, T3 divulgación selectiva, T4 deriva de atención, T5 cultivo de confianza estereotipada, T6 inundación de auditoría, T7 ranura extensible, cada una correspondiente a las Property P18.1–P18.7 y a los Requirement 13.1–13.7. (tareas 1.10, 4.28–4.34, 6.6–6.10)
- Restricción anti-manipulación de la autorización endosada: el endorsement se incorpora a la entrada de firma, y cambiar cualquier subcampo hará fallar la verificación de firma del Mandate (`E_ATTESTATION_INVALID` / `E_ENDORSEMENT_INVALID`). (tareas 1.5, 3.8, 4.17–4.21)
- Revocación simétrica e irreversibilidad de la revocación: la alcanzabilidad de la vía de revocación no es inferior a la de la vía de establecimiento, `Revoked` es un estado absorbente, y la revocación en cascada está activada por defecto. (tareas 3.5, 4.5, 4.11, 4.15)

## Cómo se mantendrá en el futuro

- Tras entrar en la revisión formal, se añadirá aquí una línea por cada resolución del comité, indicando la fecha, las secciones afectadas y el número de tarea disparado, y se añadirá una entrada de lectura humana en el grupo de Keep a Changelog correspondiente de arriba.
- Número de versión: ejecutar conforme a §1.7 — las adiciones compatibles hacia atrás van por MINOR, los cambios rompedores van por MAJOR con reinicio de MINOR a cero, y las erratas puramente textuales van por la edición editorial (§1.7.4) sin tocar el número de protocolo.
- Las erratas posteriores y la migración de ediciones se ejecutan conforme a §1.7.4 / §1.7.5; este registro se migra junto con el cuerpo del protocolo y se actualiza con cada edición.
- Los cambios análogos en los distintos idiomas se sincronizan en el mismo ciclo; en caso de discrepancia prevalece la versión de referencia.
