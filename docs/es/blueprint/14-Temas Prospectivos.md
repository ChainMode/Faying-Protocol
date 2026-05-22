# Temas Prospectivos

> **Los siguientes temas están fuera del alcance del diseño actual del Faying Protocol.**

Este es el último capítulo del blueprint, y el único capítulo cuyo estilo difiere de todos los demás. No saca conclusiones; enumera honestamente las preguntas abiertas. Hacerlo tiene dos propósitos: que el lector, al terminar el blueprint, sepa con precisión qué resuelve el Faying Protocol actual y qué no resuelve; y dejar puntos de inserción claros para specs separadas posteriores.

Cada tema de este capítulo se **deja sin conclusión** en este periodo. Si una pregunta que parece simple no ha sido respondida, no se trata de un descuido; es contención.

## Otros tipos de relaciones Faying

El Faying Protocol de este periodo cubre solamente un tipo de relación: **Human Prime ↔ iFay**. Más allá de ello, al menos los siguientes cuatro tipos de relaciones aún no entran en el diseño del protocolo.

**Una relación Faying directa entre humano y terminal** — el blueprint de este periodo elige iFay como la única forma de entidad en la que se confía para portar el contrato de custodia; por tanto, el "estar en estado controlado" del terminal debe expresarse de forma derivada a través de la Faying State del iFay. Si introducir, en alguna etapa futura, "un Human Prime estableciendo una relación Faying directamente con un terminal" requiere primero responder a varias preguntas profundas: ¿tiene el terminal "integridad de identidad" suficiente para portar un contrato de custodia? ¿Hará una relación directa, al saltarse iFay en la capa de protocolo, que la cadena de responsabilidad sea más difícil de trazar y empeore en cambio la visibilidad del Human View? Cuando coexistan las dos rutas "directa" y "derivada a través del iFay", ¿cómo se garantizará la unicidad de la atribución? Estas preguntas no tienen respuesta satisfactoria en este periodo.

**Una relación Faying directa entre humano y aplicación de software** — homóloga al punto anterior, pero con una capa extra de complejidad. Una aplicación de software es a menudo, por sí misma, modular, transversal a procesos y transversal a redes. Al establecer una relación Faying con una aplicación directamente, debe primero definirse con precisión la frontera de "la aplicación" misma, y esa definición aún no ha convergido entre distintos ecosistemas y formas de despliegue. La razón por la que este periodo hizo que la extensión de Phase 3 fuera "asumir de forma derivada la aplicación de software a través del iFay" es precisamente diferir este problema de definición de frontera.

**Colaboración y delegación iFay ↔ coFay** — este es el tema central de Phase 4. Este periodo no introduce la forma de protocolo de la custodia de coFay por dos razones: el extremo de atribución de un coFay suele ser una organización o un rol, y cómo una organización aterriza institucionalmente el deber de custodia sobre personas o roles específicos es en sí una discusión compleja a través de instituciones, derecho y gobernanza corporativa; y la forma de protocolo para "que la transferencia de responsabilidad no se pierda" en la colaboración entre Fays necesita que las Phases 1 a 3 sean estables antes de tener un punto de inserción adecuado.

**Colaboración iFay ↔ iFay** — cuando múltiples iFays (cada uno atribuido a un Human Prime distinto) colaboran a través de relaciones de custodia para completar un acto, surge la cuestión de "la ruta multipersona de transferencia de la atribución de la acción": ¿debe el acto atribuirse al iniciador, al receptor o a ambos según alguna regla de prorrateo? Esta pregunta es similar al diseño legal de "subdelegación entre apoderados" en la sociedad del mundo real, pero la alta densidad y frecuencia de la colaboración en la era de los Fays hace que la velocidad de procesamiento del derecho tradicional quede muy por detrás. Este tema necesita la evolución simultánea del derecho, el protocolo y la gobernanza social antes de poder obtener una respuesta estable.

Los cuatro tipos de relaciones anteriores pertenecen todos a las direcciones de evolución a largo plazo del Faying Protocol. Se inscribirán progresivamente en las Phases 2 a 5 de la Mission Path, pero la forma de protocolo de cada uno será portada por specs separadas posteriores y está fuera del alcance de este periodo.

## B4: Reporte de ubicación durante Rogue

El punto 4 de la dimensión B del Capítulo 13 (B4) es el único punto de diseño de protocolo en este blueprint marcado explícitamente "sin conclusión en este periodo".

### Descripción del tema

Cuando un terminal asumido por un iFay (p. ej., un dron) entra en Rogue Fay, ¿debe seguir reportando activamente su ubicación física o el estado del terminal al Human Prime al que está atribuido?

Por ejemplo: el dron de Jack, en el curso de una tarea, pierde la conexión con Jack (cumpliendo la condición de activación 4 del Capítulo 13, "el Human Prime está fuera de línea o inalcanzable durante un tiempo prolongado"), y entra en Rogue Fay. La ubicación física del dron sigue cambiando — afectada por la inercia, el viento, los algoritmos de aterrizaje autónomo, etc. La pregunta es: ¿debe este dron seguir reportando activamente su posición, nivel de batería y otros estados del terminal al lado de Jack?

### Una tensión bilateral

**A favor del reporte continuado** — cuanto más reporte un Fay desconectado, más fácil es para el Human Prime encontrarlo de nuevo y restablecer Faying. Desde la perspectiva de la recuperabilidad, "la ubicación es visible" es una capacidad que protege el interés del Human Prime.

**En contra del reporte continuado** — una vez que un Fay sigue reportando su ubicación en Rogue, un atacante puede explotar ese canal: interceptando información de ubicación para captar el rango de actividad del Human Prime; falsificando el canal de reporte para suplantar el lado del Human Prime e inducir acción del Fay; usando el "reporte continuo" como medio de reconocimiento para un ataque.

Ambas caras del valor son legítimas, y ambas encajan con el espíritu interno del Human View, pero apuntan a elecciones de diseño de protocolo opuestas. En el estado rogue de Rogue Fay, el "reporte activo" puede igualmente proteger al Human Prime o traicionar al Human Prime.

### Posibles caminos intermedios

Posibles soluciones en el futuro incluyen, sin limitarse a, las siguientes líneas de pensamiento. El blueprint no las preselecciona.

**Tratamiento diferenciado por causa de Rogue** — el Human Prime revoca activamente → ocultar ubicación; conexión perdida / tiempo expirado → revelar ubicación; alerta de intrusión → revelar ubicación. Usar "por qué se entró en Rogue" como criterio para reportar o no.

**Elegir explícitamente vía preautorización** — en el momento en que se inicia la Faying Action, hacer que el Human Prime declare explícitamente "si pierdo posteriormente la conexión, ¿se permite que este terminal siga reportando ubicación?".

**Reporte por niveles** — no reportar ubicación precisa, sino reportar señales mínimas que no expongan información espacial, como "sigo en Rogue, la salud es normal".

Ninguna de estas tres líneas de pensamiento se adopta como conclusión en este periodo. Pertenecen a temas que necesitan plena discusión durante la evolución del Faying Protocol en las Phases 2 a 5, y deben absorber la entrada de las partes de privacidad, seguridad y regulación.

### Relación entre este tema y el Capítulo 13

B4 es solamente **a discutir**, no **a ejecutar**. Antes de que el documento de especificación del protocolo aterrice una elección final para B4, todas las demás reglas dadas por el Capítulo 13 — B1–B3 permitidos, las reglas completas de A1–A4, C1–C3, D1–D4 — permanecen plenamente en vigor. La posición fáctica de B4 en este periodo es "la capa de protocolo ni obliga ni prohíbe la implementación", dejando la decisión a los implementadores específicos y a specs futuras.

## Final del blueprint

A estas alturas, debería poder responder por sí mismo a las siguientes tres preguntas sobre el Faying Protocol:

- **¿Qué es?** Un contrato que expresa explícitamente, entre Human Prime y Fay, "cómo se entregan el control y la responsabilidad".
- **¿Qué porta hoy?** La línea ética de fondo de los Capítulos 11 a 13 + la forma contractual mínima de Phase 1.
- **¿Qué no porta todavía?** Todos los temas prospectivos honestamente enumerados en este capítulo.

Un blueprint que cree haber respondido a toda pregunta es el más propenso a ceder cosas que no deberían cederse cuando aparecen escenarios nuevos. Un blueprint que enumera honestamente las preguntas abiertas es, por el contrario, más capaz de mantener intacta la línea de fondo a través de extensiones futuras.
