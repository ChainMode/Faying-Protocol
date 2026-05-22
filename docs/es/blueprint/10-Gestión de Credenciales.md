# Gestión de Credenciales

La gestión de credenciales suena fuertemente a ingeniería — emisión, firma, revocación y renovación de FayID, cada una implicando algoritmos específicos y protocolos de claves. Pero en este blueprint, la gestión de credenciales se sitúa bajo los valores, no bajo los temas técnicos.

La razón es esta: el Faying Protocol existe para hacer explícito "a quién pertenece el acto". El portador técnico de esto, cuando aterriza en la capa de protocolo concreta, es la credencial. La credencial responde a dos preguntas:

> **¿Es este Fay, ahora mismo, el Fay que dice ser?**
> **¿Está este Fay, ahora mismo, todavía autorizado por su Human Prime?**

Ninguna de las dos es una pregunta de ingeniería; ambas son preguntas de responsabilidad. Una vez que las credenciales pueden ser falsificadas, abusadas o emitidas en silencio por algún tercero al margen del Human Prime, el valor entero del Faying Protocol se desvanece en un instante — el Human Prime ya no es el verdadero portador de la responsabilidad.

Algoritmos específicos, formatos de firma, protocolos de claves y otros detalles técnicos pertenecen al documento de especificación del protocolo y al schema; este capítulo no los despliega. Este capítulo solo expone las pocas posiciones sobre la gestión de credenciales en las que no se permite ninguna concesión.

## FayID es la base de identidad para entrar en Faying State

FayID es la identidad unificada y única de un Fay dentro del framework iFay. Todo el contrato de custodia del Faying Protocol se construye sobre FayID. Una Faying Action debe explicitar "qué FayID entra en Faying State"; la atribución de Faying State debe explicitar "qué FayID está atribuido a qué Human Prime"; la salida de Faying State debe explicitar "qué FayID entra en Rogue Fay".

Si no se puede confiar en FayID, los tres juicios anteriores pierden sentido.

## El fallo de credencial equivale al fallo de Faying

Entre las nueve condiciones de activación para la transición automática de Faying State a Rogue Fay enumeradas en el Capítulo 13, la condición 6 establece explícitamente:

> **La identidad del Fay no puede verificarse (p. ej., la firma de FayID ha caducado).**

Este punto no es una entrada que "casualmente involucra credenciales" dentro de las nueve; es el aterrizaje concreto de la gestión de credenciales en la capa de protocolo que no puede saltarse. Una vez que la validez de FayID está en duda, no importa cuán continuo o casi completo sea el trabajo previo del Fay, Faying State debe salir de inmediato:

> **Una duda sobre la validez de la credencial equivale a que Faying State ya ha fallado.**

No existe un caso intermedio "la credencial es sospechosa pero Faying State todavía se sostiene", y no existe el compromiso de ingeniería de "termina primero la tarea actual y luego trata el problema de la credencial".

## Los derechos de revocación deben permanecer en el lado del Human Prime

La gestión de credenciales tiene una compensación aparentemente menor pero extremadamente crítica en el diseño del protocolo — ¿a quién pertenece en última instancia la revocación de una credencial? La respuesta es obvia: al Human Prime.

El Fay mismo no debe tener ninguna ruta legítima para revocar su propia credencial — homólogo a D4 del Capítulo 13, un Fay no puede decidir por sí mismo abandonar la custodia, ni puede decidir por sí mismo cortar el vínculo de custodia.

Las plataformas de terceros, los proveedores del Runtime del Fay y los proveedores de capacidades del Fay no deben tener el poder de revocar su FayID sin el consentimiento del Human Prime — a menos que ese tercero sea una autoridad competente en el sentido regulatorio (véase la condición de activación 8 del Capítulo 13).

El Human Prime debe siempre conservar una ruta de revocación simétrica, alcanzable y auditable. La alcanzabilidad de la acción de revocación no debe ser inferior a la alcanzabilidad de iniciar una Faying Action. Este es el aterrizaje concreto en la capa de credencial del principio de "simetría" del Faying Protocol: establecer la custodia y revocar la custodia deben ser dos rutas igualmente alcanzables. Una vez que la revocación se vuelve más difícil que el establecimiento, la relación de custodia se desliza de hecho hacia "delegación irrevocable", violando así el requisito de "ruta de intervención siempre abierta" del Human View.

## La renovación no es un comportamiento por defecto

El Capítulo 12 impone una restricción dura sobre Faying State: una Faying State debe ser de alcance acotado, y un Faying ilimitado es un antipatrón. La posición a la que esta restricción corresponde en la capa de credencial es — la renovación de una credencial no debe llevarse a cabo por defecto.

Cada renovación debe ser una acción explícita, atestiguable, no un bucle implícito de "el Fay envía automáticamente, el sistema renueva automáticamente". El blueprint permite comodidades en la capa de ingeniería como "recordatorios de renovación" y "sugerencias de renovación", pero prohíbe convertir la "renovación" en algo que el Fay pueda completar silenciosamente por sí mismo — eso convertiría, de hecho, Faying en delegación ilimitada.

Entendido desde la perspectiva de la responsabilidad: la renovación es el momento en el que el extremo responsable reexpresa la intención de custodia. Si incluso la renovación es completada silenciosamente por la ingeniería, entonces a la "custodia" solo le queda una firma sin intención.

## Unas cuantas líneas rojas inviolables

Las pocas posiciones de valor de la gestión de credenciales son líneas rojas que ninguna solución técnica puede violar al aterrizar:

- FayID es la base de identidad;
- una credencial en la que no se puede confiar significa que Faying no se sostiene;
- los derechos de revocación deben permanecer en el lado del Human Prime;
- la renovación no es un comportamiento por defecto.

Algoritmos de firma concretos, jerarquías de claves, propagación de listas de revocación, diseño granular de las ventanas temporales de renovación, la estructura de los certificados raíz para confianza mutua entre proveedores y la consistencia eventual de la revocación — estos detalles técnicos pertenecen a la especificación del protocolo. Este capítulo no los reformula ni los predetermina, pero cualquier solución técnica debe primero cumplir con las cuatro posiciones anteriores.

![Ilustración de la gestión de credenciales: control de FayID, firma, revocación y renovación en el lado del Human Prime](../../zh-CN/blueprint/illustration/credential-management.png)
