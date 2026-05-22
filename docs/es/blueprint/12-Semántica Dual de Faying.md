# Semántica Dual de Faying

A estas alturas la palabra "Faying" ha aparecido muchas veces: como nombre del contrato en el Capítulo 2, distinguiendo iFay de Agent en el Capítulo 3, portando el requisito de valor del Human View en el Capítulo 11. Pero a qué se refiere realmente Faying se ha aplazado deliberadamente hasta ahora. La razón es que no puede describirse desde una sola cara.

Faying porta dos semánticas a la vez.

**Semántica de estado** — el estado de conexión de un Fay bajo la custodia de un Human Prime, llamado **Faying State**.
**Semántica de acción** — el acto de "entrega de control" por el cual un Fay entra en Faying State desde el estado rogue, llamado **Faying Action**.

Ambas semánticas son inseparables: sin una Faying Action, Faying State nunca se establecerá; sin Faying State, una Faying Action es solo una operación vacía. Este es el **principio de Semántica Dual** de Faying.

Cualquier intento de simplificar Faying a una sola cara — tomándolo simplemente como "un estado de conexión" o simplemente como "una acción de conmutación" — borra silenciosamente la atribución de responsabilidad en la capa de protocolo.

## Faying State: el estado de conexión bajo custodia

Faying State es el estado de conexión de un Fay bajo la custodia de un Human Prime específico. Un Fay que entra en este estado tiene tres propiedades necesarias.

**La atribución de la acción es única** — todos los actos hacia el exterior del Fay en este estado se atribuyen a ese Human Prime. Sea el acto decidido autónomamente por el Fay, ordenado explícitamente por el Human Prime o disparado por el entorno externo, el extremo responsable no salta.

**Visibilidad continua** — durante este estado, el Human Prime mantiene Human View sobre la actividad del Fay y puede confirmar en cualquier momento si la custodia sigue surtiendo efecto.

**La ruta de intervención está siempre abierta** — durante este estado, las órdenes del Human Prime de revocación, pausa, ralentización o destrucción sobre el Fay tienen la prioridad más alta. El Fay no puede anular estas órdenes invocando ninguna "razón de negocio".

Faying State no es un resultado estático; es un compromiso continuamente en línea. Necesita reconfirmarse en cada momento microscópico, no mantenerse para siempre una vez establecido. Una vez que cualquiera de los tres anteriores deja de sostenerse, Faying State debe entrar en el flujo de salida definido en el Capítulo 13.

> **Una conclusión inversa importante**: en el estado fuera de Faying State (es decir, Rogue Fay), todo acto hacia el exterior de un Fay no tiene a nadie que reciba la responsabilidad. Por tanto, la única elección de diseño aceptable que el Faying Protocol puede hacer en la capa de protocolo es: **prohibir al Fay actuar durante Rogue Fay**, en lugar de "dejarlo actuar y parchear la atribución después". Este principio se aterrizará estrictamente en el Capítulo 13.

## Faying Action: la entrega de control

Una Faying Action es un acto específico, observable y auditable de "entrega de control".

La analogía más adecuada es esta escena cotidiana:

> Jack entrega el volante de un coche a un conductor de IA. En este momento, Jack no está simplemente pulsando un botón de "piloto automático" — está, de un modo claramente perceptible para el exterior, **entregando el control**. Antes de esto, el volante era de Jack; después de esto, el volante es de ese conductor de IA; mientras tanto, todas las consecuencias derivadas del volante siguen recayendo sobre Jack, que es quien tiene el carnet de conducir.

Una Faying Action es la equivalente "entrega del volante" en el mundo digital. Mueve a un Fay, de manera clara, atestiguable y trazable, desde el estado rogue de "existe pero no puede actuar" hacia el Faying State de "actúa en nombre del Human Prime".

Esto conduce a varias propiedades innegociables de una Faying Action.

**Debe ser iniciada explícitamente por el Human Prime** — una Faying Action no permite que un Fay decida por sí mismo comenzar. Un Fay no puede entrar en Faying State autónomamente solo porque "la última vez comenzó así", "infiero que el Human Prime ahora desearía que comenzara" o "he sido autorizado para actos similares antes". Cada entrada debe ser iniciada explícitamente por el Human Prime.

**Debe ser atestiguable** — una Faying Action debe dejar una marca observable para el exterior (incluyendo auditores, reguladores, el propio Fay, otros Fays y el Human Prime). Una Faying Action que no ha sido atestiguada equivale a una que no ocurrió.

**Debe ser de alcance acotado** — una Faying Action no debe ser una "delegación de plenos poderes" perpetua. El blueprint favorece fuertemente que una Faying Action porte un alcance explícito (p. ej., una ventana de tiempo, un alcance de tarea, un alcance de terminal), caducando automáticamente al alcanzar el límite. Un Faying ilimitado es un antipatrón a evitar.

**Debe ser revocable simétricamente** — toda Faying Action debe tener una ruta de revocación correspondiente y simétrica. Establecer Faying State y salir de Faying State deben ser **dos rutas igualmente alcanzables**, no un diseño asimétrico de "fácil de abrir, difícil de cerrar".

## Ambas caras juntas son Faying

Juntando las caras de estado y de acción, el sentido completo de Faying puede expresarse en este párrafo:

> **Faying es un acto de "entrega de control" (Faying Action) iniciado explícitamente por el Human Prime, atestiguable y revocable simétricamente, que empuja al Fay hacia un estado de conexión continuamente en línea bajo custodia (Faying State); dentro de este estado, el Fay puede actuar en nombre del Human Prime, y las consecuencias son todas asumidas por ese Human Prime; fuera de este estado, no se permite que el Fay actúe.**

El mismo párrafo arroja tres compromisos a lo largo de la dimensión del tiempo. **Pasado**: a Faying State siempre se entra mediante alguna Faying Action específica; no existe un Fay que "esté simplemente de manera natural en Faying". **Presente**: la validez de Faying State se calibra de manera continua en cada momento por el Human View, no se mantiene para siempre una vez establecida. **Futuro**: Faying State acabará saliendo mediante una revocación simétrica o una caducidad automática, devolviendo al Fay al estado rogue definido en el Capítulo 13.

## Restricciones duras sobre el diseño del protocolo

Este capítulo, como capítulo de valores, no especifica campos ni mensajes, pero impone varias restricciones duras innegociables sobre el diseño concreto del Faying Protocol:

- la capa de protocolo debe proveer expresión de primera clase para **ambos**, State y Action; no puede expresar solo una cara;
- la capa de protocolo prohíbe cualquier ruta legítima "por la cual un Fay inicia una Faying Action sobre sí mismo";
- la capa de protocolo debe proveer para toda Faying Action una marca atestiguable y una ruta revocable simétricamente;
- la capa de protocolo prohíbe el "Faying ilimitado" como forma por defecto; debe forzar que una Faying Action porte un alcance acotado en la capa de protocolo;
- la capa de protocolo debe garantizar: cuando se dispare cualquier condición bajo la cual Faying State deja de sostenerse, el Fay transita automáticamente al estado rogue, no hacia un "Faying degradado".

Cómo se establece, sostiene y termina una relación de custodia ha quedado ahora plenamente definido en el plano de los valores. El siguiente capítulo invierte la perspectiva: cuando Faying State no se sostiene, ¿qué puede y qué no puede hacer el Fay? Es el capítulo más estricto de este blueprint, aquel en el que no se permite ninguna concesión.
