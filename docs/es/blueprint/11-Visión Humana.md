# Human View

El Capítulo 2 ya nombró la proposición: una vez que se interpone un Fay en la acción digital, el iniciador y el portador de la responsabilidad desarrollan una fisura estructural. El Faying Protocol provee la forma del contrato, pero si el contrato puede realmente recibir la responsabilidad depende de un compromiso aún más previo:

> **Toda acción de Fay debe ocurrir dentro del rango que su Human Prime puede "ver".**

"Ver" aquí no es visual en el sentido físico, sino un concepto generalizado: el Human Prime, el individuo u organización al que el Fay está atribuido, puede confirmar en cualquier momento que el Fay está operando bajo custodia.

A esta "visión" generalizada se le llama **Human View**. No es un campo, un interruptor o una API en el Faying Protocol; es un valor que toda decisión técnica del Faying Protocol debe obedecer. Si cualquier diseño de campo, mensaje o máquina de estados permite que un Fay se deslice fuera del Human View, ese diseño no se permite en el plano del blueprint, por conveniente que sea en ingeniería.

## El Human View no es vista física

La vista física es "puedo ver este dron ahora mismo", "la cámara captó al robot hace un instante". La vista física está restringida por la luz, la distancia, la oclusión y la atención. En muchos escenarios no puede sostenerse en absoluto — un Human Prime no puede vigilar todos sus Fays las veinticuatro horas del día.

El Human View describe una confirmabilidad estructural:

- no requiere que el Human Prime esté mirando al Fay ahora mismo;
- pero requiere que cuando el Human Prime quiera comprobarlo, pueda confirmar de inmediato si el Fay está bajo custodia;
- y requiere que las acciones del Fay dejen un rastro trazable, de modo que "qué acaba de ocurrir, y a quién pertenece" pueda confirmarse de manera retroactiva.

En otras palabras, al Human View no le importa "ser visto" sino "**poder ser visto**". Esta es la clave por la que puede sostenerse en los innumerables escenarios altamente automatizados — enjambres de drones, robots domésticos, Fays de procesos empresariales.

## Cuatro antiproposiciones: cuatro situaciones prohibidas

La forma más poderosa de definir un valor es decir lo que prohíbe. El Human View prohíbe explícitamente las siguientes cuatro situaciones, llamadas las **cuatro antiproposiciones** del Human View.

**No Autorizado** — el Fay lleva a cabo acciones sin haber obtenido autorización del Human Prime. "Obtener autorización" es un acto verificable, no un estado que el Fay se atribuye a sí mismo. Un Fay profundamente convencido de que "el Human Prime seguramente estaría de acuerdo con esto" no está autorizado.

**No Intencional** — el Fay tiene alguna autorización legítima, pero la presente acción específica no ha sido expresada como intención por el Human Prime, y diverge de la intención presente del Human Prime. La autorización resuelve "¿se permite que se mueva esto?"; la expresión de intención resuelve "este movimiento concreto". El Human View requiere que ambas se sostengan simultáneamente.

**Inconsciente** — el Fay está autorizado y la intención ha sido expresada, pero, de hecho, el Human Prime no puede, a un coste razonable, llegar a saber qué está haciendo el Fay. Esta situación con frecuencia no es el Fay ocultando cosas activamente, sino una falla en el diseño del protocolo — impide que la información fluya de vuelta al lado del Human Prime. El Human View asume el "alcance de la información" como una condición dura de la relación de custodia.

**Fuera de Control** — el Human Prime ya está al tanto, pero ya no puede intervenir en tiempo real, p. ej., el Fay rechaza órdenes de revocación, rechaza abortar tareas, rechaza ralentizar. Esta situación es la forma final de las otras tres: cuando un Fay no necesita pedir autorización, no necesita revelar la acción y no necesita aceptar intervención, a la "custodia" solo le queda el nombre. El Human View requiere que la ruta de intervención esté siempre abierta.

Las cuatro antiproposiciones no son una lista mutuamente excluyente sino fronteras de fallo progresivamente más profundas: No Autorizado es fallo en la entrada, No Intencional es fallo durante el proceso, Inconsciente es fallo en la realimentación, Fuera de Control es fallo en la última puerta. El Faying Protocol debe mantener la línea en los cuatro niveles a la vez para cumplir con el valor del Human View.

## Aplica por igual a iFay y coFay

El Human View no es una restricción solo sobre los Fays individuales (iFay); **aplica por igual a iFay y coFay**.

Un iFay tiene una correspondencia explícita uno a uno con un Human Prime específico; la relación de custodia es intuitiva. Un coFay habitualmente corresponde a una organización, un equipo o un rol, y la relación de custodia no es naturalmente clara. Sin embargo, precisamente porque el extremo de atribución de un coFay suele ser una organización en lugar de una persona específica, los requisitos del Human View deben expresarse de forma aún más explícita: la organización debe, en la capa institucional, dejar claro "quién está autorizado para ejercer la custodia en nombre de la organización", o de lo contrario el coFay se desliza de hecho hacia la zona gris de "ninguna persona responsable específica que pueda mantener la custodia".

Ningún Fay, ya sea iFay o coFay, puede deslizarse fuera del Human View con el argumento de que "pertenezco a una organización, así que nadie está específicamente bajo custodia". La organización tiene el deber de aterrizar el deber de custodia sobre una persona o rol específico. Esta no es una pregunta técnica; es una pregunta de valores.

## Relación con el Faying Protocol

El Human View es un valor en el plano del blueprint; el Faying Protocol es la especificación de restricción técnica que porta este valor.

El Human View responde "por qué se necesita alguna restricción". El Faying Protocol responde "cómo se cumple esa restricción técnicamente con fidelidad".

Si el Human View es una carta, el Faying Protocol es todo el cuerpo de derecho básico que aterriza la carta sobre agencias ejecutoras específicas, procedimientos específicos y credenciales específicas. Una carta sin portador legal degenera en un eslogan; un cuerpo de derecho que se aparta de la carta que estaba destinada a portar se convierte en aquello mismo a lo que la carta debía oponerse. Ambos deben calibrarse mutuamente: cuando algún diseño del Faying Protocol facilita que un Fay se deslice fuera del Human View, debe ser rechazado, por conveniente que sea en ingeniería; cuando algún escenario nuevo hace difícil cumplir con el Human View bajo el Faying Protocol existente, eso significa que el Faying Protocol debe actualizarse, no que se deba conceder en el Human View.

El Capítulo 12 (Semántica Dual de Faying) y el Capítulo 13 (Rogue Fay y Atribución de Responsabilidad) recibirán este valor en la capa de la forma del protocolo: el Capítulo 12 explica cómo se establece y se mantiene la relación de custodia; el Capítulo 13 explica cómo, una vez que la custodia ya no se sostiene, el Fay debe detenerse. Juntos, los dos son el aterrizaje concreto del Human View en la capa de protocolo.
