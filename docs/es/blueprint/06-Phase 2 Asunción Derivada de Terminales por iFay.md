# Phase 2: Asunción Derivada de Terminales por iFay

Tras estabilizar Phase 1 la forma contractual mínima de "Human Prime ↔ iFay", Phase 2 dirige su atención a la relación entre iFay y los dispositivos terminales.

Aquí el término terminal se entiende en sentido generalizado — un dron, un robot, un vehículo inteligente, una pasarela IoT, un ordenador personal, un teléfono pertenecen todos a esta clase. Su rasgo común: hardware que puede ser accionado, acciones físicas que pueden iniciarse y consecuencias físicas que pueden producirse.

La clave en Phase 2 no es permitir que un iFay controle más cosas; es inscribir con claridad cada terminal del que se hace cargo en la cadena de responsabilidad Faying.

## Derivada, no directa

Phase 2 no introduce "Human Prime ↔ terminal" como relación directa. Su modo de extensión es indirecto:

> **El terminal entra en Faying State a través del iFay correspondiente del Human Prime.**

El extremo responsable sigue siendo el Human Prime; eso no cambia. El iFay sigue siendo la entidad que porta Faying State, pero ahora carga con un deber adicional — actuar como custodio en nombre de los terminales de los que se hace cargo. El terminal no se sostiene por sí solo en Faying State; su "estar en estado controlado" se deriva de la Faying State del iFay al que pertenece en ese momento.

Para continuar con la analogía introducida en el Capítulo 12 — Jack entregando el volante a un conductor de IA — Phase 2 se ocupa de: cuando posteriormente este conductor de IA conduce el coche, gira, frena y cambia de carril, cómo cada "estado de control" del volante, el acelerador y los intermitentes permanece consistente en todo momento con que Jack siga bajo custodia.

## Tres temas centrales

**Visibilidad de la asunción**: cuando un iFay asume un terminal, esto debe ser observable en tiempo real por el Human Prime y por el exterior — qué terminal, en qué ventana de tiempo, asumido por qué iFay. Esta es la extensión del Human View en la capa de terminal.

**Salida encadenada**: cuando un iFay entra en Rogue Fay, todos los terminales de los que se ha hecho cargo deben perder simultáneamente el efecto derivado de Faying. No se debe permitir que un terminal siga ejecutando acciones físicas previamente inacabadas mientras el iFay ya ha abandonado la custodia — esto corresponde exactamente con la prohibición bajo D3 del Capítulo 13.

**Irreversibilidad de la acción física**: las acciones en el mundo físico son fuertemente irreversibles. Un dron ya ha entregado, un brazo robótico ya se ha movido, un vehículo ya ha girado — la auditoría a posteriori no puede deshacerlo. Phase 2 debe asumir "más vale no actuar que actuar mal" como sesgo por defecto en la capa de protocolo, no parcheado por auditoría posterior.

El tercer punto es especialmente crítico. En el momento en que surge cualquier incertidumbre sobre Faying State, el terminal pasa por defecto a "espera pasiva" en lugar de "ejecución optimista".

## Relación con el alcance del periodo actual

**Phase 2 está fuera del alcance del diseño actual del Faying Protocol.** El Faying Protocol de este periodo cubre solo Phase 1. La forma concreta del protocolo por la cual "un iFay asume de forma derivada un terminal a través de Faying" en Phase 2 se definirá en una spec separada después de que Phase 1 se haya estabilizado. Este capítulo esboza la existencia y la dirección de Phase 2 para que la Mission Path tenga una imagen completa de la evolución.

Phase 2 es el primer paso en el que Faying sale de "entre software" hacia la frontera "software-físico". A partir de aquí, las relaciones Faying ya no conciernen solo a los bits, sino que comienzan a concernir las consecuencias físicas empujadas por los bits. Este hecho es la "gravedad" hacia la que las Phases 3 a 5 deben volver la mirada de tanto en tanto.

![Concepto de Phase 2](../../zh-CN/blueprint/illustration/phase2-concept.png)

![Arquitectura de Phase 2](../../zh-CN/blueprint/illustration/phase2-architecture.png)
