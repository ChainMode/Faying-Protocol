---
title: "Faying Protocol/1.0 — §11 Cuestiones abiertas"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: es
part: "Capítulo 11 de 11 (cuerpo del protocolo)"
---

> Navegación del cuerpo del protocolo: [Índice](./README.md) | anterior [§10 Manejo de errores](./10-Manejo-de-Errores.md) | siguiente [Anexo A Alineación de terminología](./Anexo-A-Alineacion-de-Terminologia.md)

## §11 Cuestiones abiertas

> Este capítulo enumera con honestidad temas que no es necesario responder obligatoriamente en el cuerpo del protocolo de la fase 1, sino que se dejan al Protocol Committee para su resolución en la etapa de RFC. Cada tema ofrece la **inclinación actual del protocolo**, las **alternativas** y el **estado de resolución**, de modo que las discusiones de RFC posteriores tengan un punto de partida estructurado. Las entradas resueltas (p. ej. Q10 denominación del protocolo) se conservan como registro histórico.

### Q1 Reporte de ubicación del terminal durante el estado Rogue

- **Tema**: mientras el iFay está en Rogue Fay, ¿se le permite al terminal seguir reportando la ubicación física? Implica la tensión bidireccional «privacidad vs recuperabilidad».
- **Inclinación actual del protocolo**: diferenciar por `RevokeReason` — `human-initiated` / `task-completed` no reportan; `fay-credential-invalid` / `regulatory-order` / `terminal-disconnected`, etc., pueden reportar.
- **Alternativas**: (a) prohibición general; (b) permiso general; (c) el HP preselecciona explícitamente en el momento de BOOTSTRAP.
- **Estado de resolución**: abierta; el capítulo 14 del blueprint ya declara explícitamente que no concluye.

### Q2 Vía no rechazable de G0 Emergency Override

- **Tema**: en casos extremos en los que el IF ha sido comprometido por un atacante, ¿cómo asegurar que el mensaje G0 siga siendo ejecutado por el núcleo del IF?
- **Inclinación actual del protocolo**: la capa de protocolo exige que los mensajes G0 tengan la máxima prioridad (véase §7.2 / P12 prioridad de G0 Override), pero reconoce que los medios puramente a nivel de protocolo son insuficientes cuando el núcleo del IF está comprometido.
- **Alternativas**: (a) aplicación de un kill-switch a nivel de hardware; (b) confirmación por doble firma TPM-quote; (c) mantener la aplicación a nivel de protocolo y dejar la vía hardware a la libertad de implementación del ecosistema.
- **Estado de resolución**: abierta; profundamente acoplada con la toma de control de terminales de la fase 2 / fase 3.

### Q3 Calendario predeterminado de PQC

- **Tema**: ¿cuándo se promueve el híbrido Ed25519 + ML-DSA-65 de OPTIONAL a MUST?
- **Inclinación actual del protocolo**: 1.0 solo declara OPTIONAL (ranuras de negociación PQC en §6.1); el calendario se fijará tras la publicación de todos los estándares finales del NIST.
- **Alternativas**: (a) esperar a que se finalicen todos los estándares PQC del NIST; (b) seguir el primer algoritmo de firma estandarizado; (c) diferenciar por nivel (escenarios de alta sensibilidad MUST primero).
- **Estado de resolución**: abierta; pendiente del progreso de estandarización PQC del NIST.

### Q4 Cooperación iFay ↔ iFay entre distintos Human Prime (Fase 4/5)

- **Tema**: cuando dos iFays pertenecientes a distintos HP cooperan, ¿cómo se determina la transferencia de responsabilidad?
- **Inclinación actual del protocolo**: 1.0 no lo cubre; se fijará en la fase 4 cuando se introduzca coFay.
- **Alternativas**: (a) la asume el iniciador; (b) la asume el receptor; (c) compartida por reglas; (d) ambos HP deben co-testimoniar.
- **Estado de resolución**: abierta; requiere discusión de doble vía legal-protocolo.

### Q5 Determinación objetiva de la desviación Ego

- **Tema**: ¿debe la capa de protocolo especificar el conjunto mínimo de señales de decisión para `ego-deviation`?
- **Inclinación actual del protocolo**: la capa de protocolo solo define la semántica de `RevokeReason="ego-deviation"` y las consecuencias de su disparo (§EH.1, §3.6 BBS); el conjunto concreto de señales de decisión se deja a la libertad de implementación.
- **Alternativas**: (a) la capa de protocolo exige el conjunto mínimo de señales; (b) explícitamente restringido por el Behavior Baseline Service de §3.6; (c) mantener la apertura actual.
- **Estado de resolución**: abierta; acoplada con la estandarización de la línea base de Q13.

### Q6 Política de renovación del Mandate

- **Tema**: ¿debe el protocolo prohibir todas las formas de «renovación automática»?
- **Inclinación actual del protocolo**: prohibir todas las formas de renovación automática; toda renovación debe pasar por el testimonio explícito del HP (inclinación del capítulo 10 del blueprint).
- **Alternativas**: (a) permitir «renovación automática limitada que requiera prefirma periódica del HP»; (b) permitir renovación automática en niveles de bajo riesgo (G3/G4); (c) mantener la prohibición.
- **Estado de resolución**: abierta; pendiente de decisión del Protocol Committee.

### Q7 Entorno offline / de red débil

- **Tema**: en escenarios de borde donde el RR es inalcanzable (desconexión de un dron), ¿se permite un modo debilitado de «autonomía acotada en el tiempo + reconciliación al reconectar»?
- **Inclinación actual del protocolo**: modelar explícitamente «autonomía acotada en el tiempo + reconciliación de reconexión» mediante el Endorsed_Mandate (§7.5, §9.8, §4.3 Disconnected); las vías no-Endorsed son estrictamente Default-Deny (véase P17.2 presunción pesimista).
- **Alternativas**: (a) confiar únicamente en el Endorsed_Mandate; (b) introducir una «caché de RR regional»; (c) Default-Deny estricto sin ninguna excepción.
- **Estado de resolución**: parcialmente resuelta (el Endorsed_Mandate ya aterrizó en §7.5); el límite superior de la política offline espera la resolución de Q11.

### Q8 «Nivel suplementario» del subagente

- **Tema**: ¿es suficiente el sistema de cinco escalones de G0 Emergency_Override y G1 Strict / G2 Moderate / G3 Loose / G4 Autonomous?
- **Inclinación actual del protocolo**: 1.0 mantiene los cinco escalones (§7.1); no introduce escalones intermedios como G2.5.
- **Alternativas**: (a) introducir un escalón intermedio «semiautónomo + interrumpible»; (b) permitir que las implementaciones definan subniveles personalizados pero mapeados de vuelta a uno de los cinco; (c) introducir subniveles ortogonales Endorsement Grades (ya aterrizados en §7.5).
- **Estado de resolución**: parcialmente resuelta (los Endorsement Grades se superponen ortogonalmente a G1–G4); los escalones intermedios siguen abiertos.

### Q9 Frontera de la cascada de revocación

- **Tema**: ¿cómo se garantiza la visibilidad de la cascada de revocación predeterminada de DELEGATE (`cascade=true`) bajo derivación multinivel?
- **Inclinación actual del protocolo**: predeterminado `cascade=true` (§5.3.5); visibilidad restringida por `RevocationVisibilityBudget` (§9.7, P14 cascada de revocación entre derivaciones).
- **Alternativas**: (a) diferenciar el presupuesto por la profundidad del árbol de derivación; (b) mantener un único presupuesto + doble vía push / pull.
- **Estado de resolución**: abierta; a la espera de que las pruebas de conformidad midan la visibilidad de árboles de derivación profundos.

### Q10 Denominación del protocolo (Resuelta)

- **Tema**: denominación oficial del protocolo.
- **Conclusión de la resolución**: el protocolo se denomina oficialmente **Faying Protocol** (sin abreviatura propia), versión `Faying Protocol/1.0`.
- **Estado de resolución**: resuelta; este tema permanece como registro histórico y ya no está abierto a discusión.

### Q11 Límite superior máximo de vigencia del Endorsement

- **Tema**: ¿debe la capa de protocolo especificar el límite superior duro de `endorsement.endorsed_lifetime` (p. ej. ≤12 h)? ¿Debe ajustarse aún más por nivel?
- **Inclinación actual del protocolo**: el Anexo B ofrece un valor recomendado (predeterminado 4 h, límite superior blando 12 h, y no debe superar `Mandate.not_after − Mandate.not_before`; véase P16.3 / P16.4); el límite superior duro espera resolución de RFC.
- **Alternativas**: (a) codificar de forma rígida un límite superior de 12 h a nivel de protocolo; (b) diferenciar por nivel (p. ej. G1 ≤ 1 h, G4 ≤ 24 h); (c) mantener el valor recomendado no obligatorio.
- **Estado de resolución**: abierta; acoplada con la política offline de Q7.

### Q12 Protección contra el abuso del Faying bidireccional

- **Tema**: ¿deben los `FAYING_REQUEST` iniciados por iFay estar sujetos a una limitación de tasa obligatoria a nivel de protocolo (como máximo N veces por minuto por par (HP, IF))? ¿Debe incorporarse el límite de tasa al mismo presupuesto `ConfirmationRateLimit`?
- **Inclinación actual del protocolo**: la frecuencia de FAYING_REQUEST se incorpora al mismo presupuesto `ConfirmationRateLimit` (véase §5.3.6, §9.10.7, P18.6); la superación del límite dispara auto-degradación / suspensión conforme a §9.10.7.
- **Alternativas**: (a) presupuesto independiente `FayingRequestRateLimit`; (b) diferenciar presupuestos por nivel; (c) mantener el reparto actual con ConfirmationRateLimit.
- **Estado de resolución**: parcialmente resuelta (el presupuesto compartido predeterminado ya aterrizó en §9.10.7); el límite superior del umbral y si el presupuesto debe ser independiente esperan resolución de RFC.

### Q13 Estandarización de Behavior_Baseline

- **Tema**: ¿debe especificarse uniformemente a nivel de protocolo la granularidad de calibración de la línea base de comportamiento (por `action` / `scope_used` / `risk_level` / `affected_resources`, o conjunta multidimensional)? ¿O deben las implementaciones tener libertad exigiendo que la propia calibración de la línea base se escriba en la Attestation Chain?
- **Inclinación actual del protocolo**: libertad de implementación + calibración de la línea base escrita en la Attestation Chain; los cambios de calibración se tratan como eventos de auditoría (§3.6 I-BBS-3 / P18.5).
- **Alternativas**: (a) aplicación a nivel de protocolo (conjunta multidimensional sobre action / scope_used / risk_level / affected_resources); (b) mantener la libertad + auditoría; (c) introducir un «registro de esquemas de línea base» para unificar la calibración.
- **Estado de resolución**: abierta; acoplada con la determinación de ego-deviation de Q5.

### Q14 Criterios objetivos para la granularidad mínima del Atomic_Action

- **Tema**: ¿cuál es la determinación objetiva a nivel de protocolo de «acción indivisible mínima»? ¿Debe introducirse una «red de acciones» de modo que `scope.actions` y el conjunto de acciones del lado del RP tengan una reducción de granularidad mínima formalizable?
- **Inclinación actual del protocolo**: la capa de protocolo exige únicamente «exactamente 1 Atomic_Action por llamada / `scope.actions` sin permitir comodines» (P18.2 Atomic_Action_Strict); la determinación objetiva de la granularidad mínima se deja a los RP y al Protocol Committee según las convenciones de cada dominio industrial.
- **Alternativas**: (a) introducir una red de acciones general entre RP; (b) introducir redes separadas por industria del RP (finanzas / sanidad / IoT); (c) mantener la apertura actual.
- **Estado de resolución**: abierta; discutida junto con la ranura de extensión T7 de §9.10.8.
