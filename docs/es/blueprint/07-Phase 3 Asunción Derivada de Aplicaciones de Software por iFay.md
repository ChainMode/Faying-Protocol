# Phase 3: Asunción Derivada de Aplicaciones de Software por iFay

Phase 3 dirige la dirección de la extensión desde el hardware terminal hacia las aplicaciones de software — aplicaciones locales, servicios en la nube y escenarios embebidos In-APP.

Hay una diferencia clave entre las aplicaciones de software y los terminales hardware: el estado de un terminal hardware está relativamente concentrado — un dron o un robot es un único objeto bajo custodia — mientras que la frontera de una aplicación de software suele ser basada en procesos, modular y transversal a redes. Un cliente de comercio electrónico asumido por un iFay puede colaborar a la vez a través de múltiples dominios, múltiples APIs y múltiples servicios de terceros. La dificultad de Phase 3 no está en "la asunción", sino en si la frontera de la asunción está descrita con claridad.

## Estructura de derivación homóloga a Phase 2

Phase 3 es estructuralmente simétrica a Phase 2 y, del mismo modo, no introduce "Human Prime ↔ aplicación de software" como relación directa:

> **La aplicación de software entra en Faying State a través del iFay correspondiente del Human Prime.**

El extremo responsable sigue siendo el Human Prime. El iFay asume de forma derivada la aplicación de software a través de Faying State; el mecanismo es homólogo al de la asunción de un terminal en Phase 2. La aplicación de software por sí misma no se sostiene por sí sola en Faying State.

## Tres diferencias clave

Phase 3 añade tres complejidades adicionales que requieren manejo especial sobre la estructura de Phase 2.

**Granularidad más fina de la asunción**. Un iFay puede asumir solo parte de las funciones del software — por ejemplo, se le permite hacer pedidos en nombre de alguien, pero no modificar la política de seguridad de la cuenta. Phase 3 debe por tanto expresar en la capa de protocolo un "alcance de la asunción" más granular, homólogo al principio del Capítulo 12 de que "una Faying Action debe ser de alcance acotado".

**Colaboración transversal a fronteras más densa**. El software asumido puede invocar internamente múltiples servicios externos, APIs de terceros y funciones remotas en la nube. Phase 3 debe garantizar que cualquier llamada iniciada a través del software asumido por el iFay siga teniendo su responsabilidad atribuida al Human Prime original; la responsabilidad no puede escabullirse silenciosamente a través de la cadena de llamadas entre servicios. Este requisito responde directamente al punto doloroso del mundo real esbozado en el Capítulo 1 — "nadie puede decir con claridad qué partes manejan los datos a lo largo de la cadena de llamadas".

**Efectos secundarios más sigilosos**. Comparados con las acciones físicas, los efectos secundarios del software (escrituras de datos, cambios de suscripción, vinculaciones de cuentas de terceros) son más difíciles de percibir intuitivamente por un Human Prime. Phase 3 debe aterrizar el requisito de "alcance de la información" del Human View del Capítulo 11 de forma más explícita — los efectos secundarios deben revelarse de un modo en que el Human Prime pueda llegar a conocerlos a un coste razonable, no enterrados en el fondo de la cadena de llamadas.

## Relación con el alcance del periodo actual

**Phase 3 está fuera del alcance del diseño actual del Faying Protocol.** Este capítulo esboza la existencia de Phase 3 para explicar la dirección de la evolución del Faying Protocol, no para comprometerse con su entrega en este periodo. La forma concreta del protocolo de Phase 3 será portada por una spec separada posterior.

Tras Phase 3, el Faying Protocol cubre la relación de Fay tanto con extremos de ejecución hardware como software, pero la discusión todavía gira en torno a "un Human Prime + un iFay". La siguiente etapa, Phase 4, extiende la perspectiva hacia las organizaciones: cuando hay más de un Fay y el extremo responsable ya no es una única persona física, cómo la relación Faying mantiene aún una atribución consistente.

![Concepto de Phase 3](../../zh-CN/blueprint/illustration/phase3-concept.png)

![Arquitectura de Phase 3](../../zh-CN/blueprint/illustration/phase3-architecture.png)
