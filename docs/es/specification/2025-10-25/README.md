---
title: Faying Protocol/1.0 — Índice de la especificación del protocolo (Borrador)
version: Faying Protocol/1.0
status: Final
editors:
  - Faying Protocol Committee
date: 2025-10-25
language: es
replaces: -
---

# Especificación del protocolo Faying Protocol/1.0

Esta es la especificación oficial en español de Faying Protocol/1.0 (Final, publicada el 2025-10-25). El cuerpo del protocolo está dividido por capítulos en 11 archivos, con numeración de capítulo de dos dígitos y nombres de archivo que portan el nombre del capítulo; la referencia rápida de terminología, los presupuestos de parámetros y los materiales sobre el proceso de gestación del protocolo se incorporan como anexos, de modo que quienes participan en el código abierto puedan tanto entender el protocolo en sí como seguir cómo se fue fijando paso a paso.

La especificación en inglés se encuentra en [`../../../en/specification/2025-10-25/`](../../../en/specification/2025-10-25/) y tiene una **estructura de archivo único** (el cuerpo del protocolo está plenamente incorporado en el único archivo `Faying-Protocol-1.0.md`, con §1–§11 y los Anexos A/B); la correspondencia con la versión española es una correspondencia al **nivel de ancla de sección**, no archivo por archivo. En caso de discrepancia prevalece la versión de referencia.

## Cómo leer

Si entras en contacto por primera vez, conviene leer el cuerpo del protocolo una vez en orden §1 → §11 y consultar después los anexos. Si un término no está claro, búscalo en el Anexo A; para valores concretos como timeouts/presupuestos, consulta el Anexo B.

## Cuerpo del protocolo (§1–§11)

| Capítulo | Archivo | Contenido |
| --- | --- | --- |
| §1 | [01-Vision-General.md](./01-Vision-General.md) | Denominación del protocolo, posicionamiento, objetivos de diseño, diferencias frente a los esquemas existentes, definición en una sola frase, alcance y no-objetivos |
| §2 | [02-Arquitectura.md](./02-Arquitectura.md) | Posición en la pila del protocolo, relaciones entre entidades, jerarquía de niveles, secuencia de interacción central, principios de diseño |
| §3 | [03-Componentes-e-Interfaces.md](./03-Componentes-e-Interfaces.md) | Interfaces e invariantes de los seis componentes centrales (MS / PC / AC / RR / LC / BBS) |
| §4 | [04-Modelos-de-Datos.md](./04-Modelos-de-Datos.md) | Vista de lectura humana en TypeScript, definición autoritativa en CDDL, máquina de estados del Mandate |
| §5 | [05-Mensajes-del-Protocolo.md](./05-Mensajes-del-Protocolo.md) | Reglas de codificación, estructura del envoltorio, siete clases de mensaje, tabla de códigos de error |
| §6 | [06-Criptografia.md](./06-Criptografia.md) | Negociación de suites de algoritmos, derivación de claves, formato de firma |
| §7 | [07-Niveles-de-Autorizacion.md](./07-Niveles-de-Autorizacion.md) | Semántica de los niveles G0–G4, matriz de disparo, monotonía de degradación, subniveles Endorsement |
| §8 | [08-Ciclo-de-Vida.md](./08-Ciclo-de-Vida.md) | Máquina de estados del ciclo de vida de extremo a extremo, secuencia de atribución de responsabilidad, reconciliación de reconexión |
| §9 | [09-Consideraciones-de-Seguridad.md](./09-Consideraciones-de-Seguridad.md) | STRIDE, anti-replay / anti-secuestro / anti-phishing, detección de desconexión, catálogo de amenazas de la era de la IA |
| §10 | [10-Manejo-de-Errores.md](./10-Manejo-de-Errores.md) | Escenarios de error, vías de recuperación, condiciones de observabilidad, convergencia Default-Deny |
| §11 | [11-Cuestiones-Abiertas.md](./11-Cuestiones-Abiertas.md) | Cuestiones abiertas Q1–Q14 dejadas al Protocol Committee para su resolución |

## Anexos

| Anexo | Archivo | Contenido |
| --- | --- | --- |
| A | [Anexo-A-Alineacion-de-Terminologia.md](./Anexo-A-Alineacion-de-Terminologia.md) | Referencia rápida de terminología, fuente terminológica autoritativa para la implementación y la revisión |
| B | [Anexo-B-Presupuestos-de-Parametros-Predeterminados.md](./Anexo-B-Presupuestos-de-Parametros-Predeterminados.md) | Parámetros predeterminados y límites superiores, reglas de ajuste por grade |
| C | [Anexo-C-Registro-de-Cambios.md](./Anexo-C-Registro-de-Cambios.md) | Registro de cambios desde el primer trazo del borrador hasta su finalización y estrategia de versionado |

## Versión

- Nombre del protocolo: Faying Protocol (la abreviatura «FAP» usada en los borradores tempranos queda suprimida)
- Número de versión: Faying Protocol/1.0
- Estado: Final (publicado el 2025-10-25)
- Editores: Faying Protocol Committee

Los números de versión en el front matter de todos los archivos del cuerpo del protocolo concuerdan con lo anterior. Esta es la primera versión oficial 1.0, migrada como un todo desde el espacio de trabajo del borrador a este directorio; las versiones española e inglesa se publicaron conjuntamente en la misma entrega, sin publicación unilateral. Las erratas posteriores se incorporan, conforme a §1.7.4, en una nueva edición con su propia fecha de publicación, sin cambiar el número de versión del protocolo.
