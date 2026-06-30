<!-- Actualizado: 2026-05-25 -->

# Visión Humana y Faying: estrategia de producto y enfoque técnico para la convivencia con iFay

Si, en el futuro, la IA realmente va a hacer cosas en su nombre, operar terminales en su nombre e interactuar con el mundo en su nombre, entonces "cómo los humanos y la IA conviven" deja de ser una discusión filosófica para convertirse en un **protocolo de seguridad que tiene que concretarse**.  
Lo repito: hacer que la IA corra más rápido es fácil; hacer que "actúe con responsabilidad dentro de la sociedad" es la parte difícil.

Por eso lo planteamos con toda claridad:  
**Toda acción de Fay debe ocurrir dentro del rango que su Human Prime puede "ver".**  
"Ver" aquí no es mirar fijamente una pantalla, ni apuntar una cámara hacia un robot — es un compromiso estructural: no hace falta estar mirando todo el tiempo, pero en el momento en que se quiera mirar, se puede confirmar si sigue bajo custodia; en el momento en que se quiera detenerlo, se puede detenerlo.  
A este valor lo llamamos **Human View** dentro del protocolo.  
(Para un tratamiento más detallado de esta idea, lea directamente "Human View": https://ifay.ai/es/docs/Faying-Protocol/blueprint/11-Visi%C3%B3n%20Humana )

En torno a la "gradación de supervisión", la "Human View", la "conexión fuerte / fusión fuerte de Faying" y los escenarios futuros de asunción de terminales, quiero hablar de lo que estamos construyendo más como una "manera de convivir" que como un montón de jerga.  
La posición que quiero expresar es esta: **Faying State es la forma por defecto segura, alineada y extensible en la que humanos e iFay conviven. Una entidad que se ejecuta automáticamente fuera de Faying debe situarse por defecto en la zona insegura — igual que HTTP en Internet.**

---

## Human View: no "ser visto", sino "poder ser visto"

Usamos Human View para capturar este hecho: un humano no puede vigilar todos sus Fays las veinticuatro horas del día. La vista física no se sostiene; debemos introducir una especie de "confirmabilidad estructural".  
Lo que le importa no es "¿estoy mirando ahora mismo?", sino "¿puedo mirar cuando quiera?". Ese es un objetivo de ingeniería completamente distinto.

Quiero trazar una línea clara entre dos conceptos: **Human View** y **Harness** no son lo mismo.  
Harness resuelve "¿el comportamiento del iFay está bien formado?" — ¿el flujo cumple, la acción se mantiene dentro de los límites, la salida respeta las restricciones de seguridad y éticas?  
Human View resuelve "¿hasta qué punto el Human Prime puede mantener al iFay bajo control?" — ¿puedo confirmar en cualquier momento, puedo intervenir en cualquier momento, puedo terminar en cualquier momento?  
Más estrictamente: cada posición a lo largo de la cuerda de la cometa debe venir acompañada de un Harness correspondiente. Cuanto más floja esté la cuerda, mayores son las exigencias sobre Harness; cuanto más tensa esté la cuerda, más se reduce Harness a una consistencia de instrucciones a nivel de ratón.  
La razón por la que insisto en Human View no es enseñar al iFay a portarse bien; es garantizar que, por mucho que dejemos correr la cuerda, siempre se pueda tensar, recoger y ver con claridad.

Más importante aún, Human View no es un campo, una API ni un botón — es una restricción a nivel constitucional:  
**Cualquier diseño de campo, mensaje o máquina de estados que permita a un Fay deslizarse fuera de Human View no se permite a nivel del blueprint, por conveniente que sea en ingeniería.**  
Esa frase no es retórica; es una restricción dura que nos imponemos a nosotros mismos al diseñar tanto el producto como el protocolo.

Human View también prohíbe explícitamente cuatro situaciones (las cuatro antiproposiciones):

- **No Autorizado** (Unauthorized) — actuar sin autorización verificable.  
- **No Intencional** (Unintended) — la autorización existe, pero la presente acción específica no ha sido expresada como intención por el Human Prime; la acción diverge de la intención presente del Human Prime.  
- **Inconsciente** (Unaware) — incluso cuando se sostienen tanto la autorización como la expresión de intención, el Human Prime aún no puede, a un coste razonable, llegar a saber qué está haciendo el Fay.  
- **Fuera de Control** (Out-of-Control) — el Human Prime ya está al tanto, pero no puede intervenir en tiempo real, no puede revocar, no puede ralentizar, no puede destruir.

Notará que estas cuatro son en realidad la línea ética de fondo de la convivencia humano-máquina, pero aquí están escritas como requisitos de protocolo ejecutables: la autorización y la expresión de intención son la entrada y el proceso, el conocimiento es la ruta de realimentación y el control es la última puerta. Si cae cualquiera de las cuatro, a la "custodia" solo le queda el nombre.

---

## Qué significa realmente "bajo custodia": no es un interruptor de dos posiciones, se parece más a la cuerda de la cometa

Mucha gente, al oír "custodia", piensa por defecto en términos de encendido/apagado: o lo tengo bajo control o no lo tengo.  
Pero después de trabajar un tiempo en iFay, descubrimos que ese pensamiento de interruptor empuja a la gente a dos extremos — o se agotan con confirmaciones de grano fino, o sueltan tanto poder que dejan de ver y de poder detener nada.

Prefiero explicar la gradación de supervisión a través de "la cuerda de la cometa": cuanto más se recoge la cuerda, más fuerte es el control; cuanto más se la deja correr, más autonomía tiene iFay.  
La cuestión no es "¿debo soltar cuerda?"; la cuestión es **la cuerda siempre está en su mano** — siempre se puede recoger, intercambiar o cortar.

Dividimos la tensión de esta cuerda aproximadamente en cinco niveles (distintas tareas piden ajustes distintos):

1) **Equivalencia estricta (equivalente al ratón)**  
   Usted hace clic una vez, se mueve una vez; iFay no hace nada por iniciativa propia.  
   Para: acciones de alto riesgo, irreversibles y difíciles de explicar (transferencias, firmas, borrar bases de datos, despedir a alguien).

2) **Bajo supervisión (copiloto)**  
   iFay entiende y planifica, pero los pasos clave deben pedir su consentimiento.  
   Para: flujos de riesgo medio y más largos que pueden confirmarse por etapas (reservas, cambios de reserva, envío de formularios).

3) **Bajo expresión de intención (extensión de su intención)**  
   Usted le da la idea general; completa la tarea con su estilo y devuelve recibos y registros trazables a su vista.  
   Para: tareas de bajo riesgo pero alta frecuencia (organizar el correo, agendar, armar listas de la compra, generar borradores).

4) **Bajo autonomía con alcance acotado (corre por su cuenta dentro de un alcance)**  
   Usted le da un alcance (ventana de tiempo / presupuesto / terminal / dominio de tarea); planifica y ejecuta por su cuenta, pero el proceso siempre es visible, interrumpible y revocable.  
   Para: tareas rutinarias continuas (inspección, monitoreo, recopilación de información, vuelos rutinarios de drones).

5) **Autonomía acotada (simbiosis a largo plazo)**  
   Usted confía en que se conduzca a sí mismo dentro de una frontera más amplia, pero Human View y la ruta de intervención permanecen siempre activos.  
   Para: colaboración de ciclo largo (asistente a largo plazo, colaboración familiar, gestión de salud).

Estos cinco niveles parecen referirse a cuánto poder se delega, pero en lo que realmente insistimos es en una sola cosa:  
**por mucho que se haya dejado correr la cuerda, iFay no puede deslizarse fuera de Human View.**  
La custodia no es "delegar menos"; la custodia es "incluso cuando se delega, permanece dentro de la vista".

---

## Faying: no "simplemente conectado", sino "fusión y fusible" sosteniéndose bajo distintas gradaciones

Si entiende Faying meramente como "estado de conexión", se irá deslizando con naturalidad hacia una dirección peligrosa:  
"Ya que estamos conectados, quedémonos conectados para siempre."

Proponemos Faying no para describir "conectado o no", sino para definir una manera de convivir construida sobre **conexión fuerte y fusión fuerte**:  
cuando un iFay trabaja bajo Faying, ya no es una herramienta externa. Empieza, en grados diversos, a fusionarse con usted — bajo distintas tareas y distintos niveles de riesgo, forma distintas gradaciones de equivalencia:  
algunas gradaciones son equivalentes al ratón — usted hace clic una vez, se mueve una vez;  
algunas gradaciones son de copiloto — entiende y planifica, pero cada paso necesita su asentimiento;  
algunas gradaciones son una extensión de su intención — usted le da la idea general, completa las cosas con su estilo;  
más arriba, es una autonomía con alcance acotado que usted está dispuesto a conceder.  
Pero bajo cualquier gradación, la "fusión" debe satisfacer Human View: confirmable en cualquier momento, trazable en cualquier momento, intervenible en cualquier momento.

Para hacer esta fusión "ingenierizable", no podemos hablar solo de estado — también tenemos que escribir la "entrega de control" en el protocolo. El Faying Protocol descompone Faying en una semántica dual:  
**Faying State (semántica de estado)**: el estado de conexión bajo la custodia del Human Prime (la relación de fusión continuamente en línea).  
**Faying Action (semántica de acción)**: el acto de "entrega de control" por el cual el Fay entra en Faying State desde el estado rogue (la relación de fusión estableciéndose).  
(Para un tratamiento más detallado de este par de semánticas estado + acción, véase "Semántica Dual de Faying": https://ifay.ai/es/docs/Faying-Protocol/blueprint/12-Sem%C3%A1ntica%20Dual%20de%20Faying )

La razón por la que esto importa: solo haciendo de "estado" y "acción" ciudadanos de primera clase se puede garantizar que la atribución de responsabilidad no se borre silenciosamente.

A nivel de producto, trato los requisitos sobre una Faying Action como una "lista de verificación que la entrega de control debe satisfacer":

- **Debe ser iniciada explícitamente por el Human Prime**: no se permite que un Fay decida comenzar por sí mismo.  
- **Debe ser atestiguable**: debe dejar una marca auditable.  
- **Debe ser de alcance acotado**: un Faying ilimitado es un anti-patrón; debe portar fronteras como ventana de tiempo, alcance de tarea, alcance de terminal.  
- **Debe ser revocable simétricamente**: abrir y cerrar son igualmente fáciles; "fácil de abrir, difícil de cerrar" está prohibido.

Faying State, igualmente, no es "conectado y listo" — porta tres propiedades necesarias:

- **La atribución de la acción es única**: el extremo responsable de la acción hacia el exterior no salta.  
- **Visibilidad continua**: Human View puede confirmar en cualquier momento que la custodia sigue surtiendo efecto.  
- **La ruta de intervención está siempre abierta**: revocar / pausar / ralentizar / destruir tienen la prioridad más alta.

El sentido de Faying no es "te autorizo a salir corriendo por ahí"; es "te entrego el control, pero yo siempre estoy dentro de esta relación".  
Una vez que esa relación se sostiene, un iFay puede actuar en su nombre en terminales y aplicaciones más complejas sin empujarle a usted a la zona de peligro de "no se puede ver, no se puede detener, no se puede explicar".

---

## Rogue Fay: fuera de la custodia, ninguna acción hacia el exterior permitida

A nivel de producto elegimos una estrategia más estricta: **una acción de Fay sin una parte responsable clara — mejor que no ocurra.**  
Dicho de otra forma: mientras no esté dentro de Faying, un iFay no puede "actuar hacia el exterior" — no puede operar terminales en su nombre, no puede enviar mensajes en su nombre, no puede ejecutar ninguna acción que afecte al mundo externo.  
Lo que puede hacer queda reducido al vigilar mínimo: esperar a que usted inicie una nueva entrega de control, proteger los datos ya en su poder, levantar alertas cuando se detecten anomalías y devolver claramente "actualmente estoy en estado rogue" a su vista.

Si realmente aterriza este principio en ingeniería, resultará muy contraintuitivo, porque en software estamos acostumbrados a: el sistema corre por defecto, hace algo por defecto, se autorrecupera por defecto.  
Pero los Fays no pueden. Porque en el momento en que un Fay "hace algo", afecta a objetos del mundo real.

Por eso el Faying Protocol define el estado inicial por defecto de un Fay como **Rogue Fay**:  
"existe", pero no se le permite "actuar". Solo cuando el Human Prime inicia explícitamente una Faying Action adquiere la elegibilidad para actuar.  
Este es un principio de bloqueo seguro: cerrado por defecto, abierto solo explícitamente.

Para evitar que la implementación en ingeniería "lo haga sin más porque es conveniente", trazamos las fronteras del estado rogue con mucho detalle: puede escuchar, puede vigilar, puede alertar, pero no debe actuar hacia el exterior.  
Para el conjunto completo de fronteras y condiciones de activación, lea "Estado Rogue y Atribución de Responsabilidad": https://ifay.ai/es/docs/Faying-Protocol/blueprint/13-Estado%20Rogue%20y%20Atribuci%C3%B3n%20de%20Responsabilidad

- Permitimos "escuchar y esperar" (sin impacto externo).  
- Permitimos "autodiagnóstico y alerta" (devolver el riesgo a Human View).  
- Permitimos "vigilancia de datos" (aislamiento cifrado, rechazo de lectura/escritura no autorizadas).  
- Prohibimos explícitamente la "acción hacia el exterior" (cualquier acto que cambie el estado del mundo externo).

Esta es la analogía que conviene tener:  
**Una entidad automática sin Faying es como un sitio sin HTTPS** — se puede visitar, pero el navegador lo marca en rojo, y por instinto se sabe que no debería estar portando comportamiento sensible.  
De la misma forma, un Agent o entidad de ejecución automática fuera de Faying no es necesariamente "malvado de inmediato", pero es estructuralmente inseguro: puede caer en situaciones de "No Autorizado / Inconsciente / Fuera de Control" en cualquier momento, y usted no tiene ninguna compuerta a nivel de protocolo.

---

## Construir Human View a través del protocolo: mantener al Human Prime siempre capaz de ver y de frenar

Human View no es un eslogan; tenemos que convertirlo en una capacidad por defecto dentro del protocolo y del producto: visible, trazable, intervenible.  
El Human Prime al que se hace referencia aquí es el extremo responsable tal como se define dentro del sistema iFay. Para saber más sobre este concepto, véase "Definiciones y Conceptos": https://ifay.ai/es/docs/iFay/blueprint/02-Definiciones%20y%20Conceptos

### 1) Que el estado pueda ser visto: siempre sé si está en Faying

A nivel de producto, exijo:  
**En cualquier momento, el Human Prime debe poder, en una vista de panel único, confirmar: qué Fays se encuentran actualmente en Faying State, cuál es el alcance acotado de cada uno y si hay alertas de anomalía activas.**

Esto no es una funcionalidad opcional; este es el cuerpo de la "vista". Sin ello, Human View es palabrería.

La forma de producto puede tomar muchos aspectos — un widget de teléfono, un centro de notificaciones, un wearable, una bandeja de escritorio, un aviso en el coche — pero el requisito central es "siempre alcanzable".

### 2) Que el comportamiento sea trazable: siempre puedo responder "qué acaba de pasar"

El núcleo de Human View no es la monitorización en tiempo real; es la confirmación trazable.  
Por eso los registros deben ser "comprensibles", no solo trazas para ingenieros. Como mínimo deben responder:

- ¿Quién inició esta acción (orden del Human Prime / expresión de intención / disparo automático)?  
- ¿Dentro de qué alcance de autorización ocurrió?  
- ¿Qué objetos específicos se vieron afectados (terminales / aplicaciones / cuentas / datos)?  
- Cuando ocurrió una anomalía, ¿salió automáticamente de Faying? ¿Disparó una alerta?

Solo cuando estos tres se sostienen juntos algo está "dentro de la vista": se puede ver, se puede consultar y se puede frenar.

### 3) Que la intervención sea alcanzable: siempre puedo hacerle parar, ralentizar o ser revocado

A nivel de producto, la intervención debe llegar al "nivel de memoria muscular".  
No se puede obligar a un usuario a hurgar en ajustes, hojear registros o teclear un comando en un momento crítico. La intervención debe ser como un freno: simple, directa, con realimentación clara.

Fijo la superficie de intervención en cuatro botones:

- Pausar (Pause)  
- Revocar (Revoke / Salir de Faying)  
- Ralentizar (Slow down / exigir confirmaciones)  
- Destruir (Destroy / interruptor de emergencia)

Y su prioridad debe superar a cualquier "razón de negocio". Esta es una restricción dura del protocolo, no una opción del producto.

---

## Aterrizar la "tensión de la cuerda" como reglas: distintas tareas piden distintas gradaciones de supervisión

Convertimos las gradaciones anteriores en un conjunto de reglas: un conjunto que selecciona distintos modos de compuerta de acción según el tipo de tarea, el nivel de riesgo y el tipo de recurso.

### 1) Clasificación de tareas: "reversibilidad × radio de pérdida × sensibilidad de cumplimiento"

- Reversibilidad: revocable / remediable / irreversible (transferencias, firmas, borrar bases de datos)  
- Radio de pérdida: solo le afecta a usted / afecta a otros / afecta a la seguridad pública (drones, vehículos)  
- Sensibilidad de cumplimiento: privacidad personal / finanzas / sanidad / menores / autoridad pública

Estas tres dimensiones deciden la "gradación de supervisión por defecto" y deciden cómo debe fijarse el alcance de una Faying Action (ventana de tiempo, dominio de tarea, dominio de terminal, dominio de presupuesto).

### 2) Separar Autorización e Intención: "¿se permite esto?" vs. "esta cosa concreta"

En las cuatro antiproposiciones de Human View ya hicimos hincapié: la autorización resuelve "¿se permite que se mueva esto?", la expresión de intención resuelve "este movimiento concreto".  
Aterrizadas en el sistema, deben dividirse en dos clases de credenciales / dos clases de registros:

- Authorization Grant (concesión de autorización; a largo o medio plazo): permite al iFay usar una clase de capacidades dentro de algún alcance.  
- Intent Ticket (ticket de intención; a corto plazo, de un solo uso): permite la ejecución de esta acción específica.

Esto evita el desastre de "autorizó la lectura/escritura del correo, así que se puso a enviar correos masivos a todo el mundo". La autorización no es la expresión de intención; la expresión de intención es la compuerta en cada acción.

### 3) Canal de Human View: hacer de "poder ser visto" una restricción dura del protocolo

Esto no es "construir una funcionalidad de notificaciones". Se parece más a una ruta forzada a través del sistema:

- Toda acción hacia el exterior debe producir un evento que fluya de vuelta;  
- Los eventos deben poder llegar al extremo de la vista del Human Prime;  
- Si el extremo de la vista es inalcanzable durante un tiempo prolongado (fuera de línea, rechazando contacto, inalcanzable más allá de un umbral), el sistema debe salir automáticamente de la custodia, volver al estado rogue y detener la acción hacia el exterior.

Human View requiere de manera natural una "infraestructura de observabilidad": los eventos fluyen de vuelta, el estado puede confirmarse, las órdenes pueden interrumpir. Por estratificada que sea la implementación, la "alcanzabilidad de la vista" debe ser una condición dura.

### 4) Compuerta del estado rogue: puede vigilar, no puede actuar hacia el exterior

Para que "ninguna acción hacia el exterior durante el estado rogue" sea realmente ejecutable, la ingeniería debe comprometerse a: durante Rogue Fay, el sistema no persigue "seguir adelante con la tarea", persigue "detener el impacto externo + permanecer recuperable + esperar una entrega de control legítima".

Esto cambiará directamente muchos hábitos de ingeniería: cosas como "reanudación tras desconexión", "reintento de tarea" y "compensación automática" pueden ser peligrosas aquí — facilitan que un Fay siga actuando hacia el exterior estando fuera de la custodia.  
La lógica del Faying Protocol no admite ambigüedad: **mejor detenerse que actuar cuando no hay parte responsable.**

---

## Fusión con el terminal: hacer que un terminal y el Human Prime "se sientan como una misma persona"

Sigo recurriendo a ejemplos como drones, clientes de correo y aplicaciones de compras — no porque sean "geniales", sino porque hacen muy concreto el sentido de Faying:  
cuando un iFay porta cognición, memoria y hábitos alineados con usted y pasa a operar un terminal, el terminal deja de ser una herramienta fría — empieza a fusionarse más estrechamente con usted, y el comportamiento del terminal se parece cada vez más a "usted operándolo en persona".  
Una vez que eso se sostiene, el coste que un humano paga por aprender un terminal baja, la acomodación del terminal al humano se vuelve la opción por defecto y la fricción entre el humano y el mundo digital se elimina de manera sistemática.

Hice una convergencia muy explícita en la hoja de ruta: primero aterrizar la relación de custodia "Human Prime ↔ iFay" como un bucle cerrado mínimo, y luego dejar que terminales y aplicaciones entren en el estado controlado a través de iFay, en lugar de dejar que cada terminal se vincule directamente a una persona.  
Para el cuadro evolutivo más completo, lea "Human Prime ↔ iFay": https://ifay.ai/es/docs/Faying-Protocol/blueprint/05-Phase%201%20Human%20Prime%20y%20iFay

Esta elección mantiene la cadena de responsabilidad simple: ya esté usted controlando un dron, un sistema embarcado, un cliente de correo o una aplicación de compras, el extremo receptor de la responsabilidad nunca se mueve: es el Human Prime.

En lenguaje de producto, lo expresaría así:  
lo que usted posee es un "compañero digital". Puede hacer crecer muchas "extremidades" (derivados de terminal), pero su vista y su freno siempre están ahí.

Esto es lo que la conexión fuerte y la fusión fuerte realmente deberían parecer: no automatización descontrolada, sino simbiosis sostenible.

---

## Una última palabra: trate Faying como el "HTTPS por defecto" de la era de la IA

- **Faying State** es la zona segura de la acción de la IA: hay una parte responsable, hay visibilidad continua, hay una ruta de intervención.  
- **Rogue Fay / Un‑Faying** es la zona insegura por defecto: se permite la escucha y vigilancia mínimas, pero la acción hacia el exterior está prohibida.

En los inicios de Internet, HTTP no era "malvado" de inmediato, pero era inherentemente inseguro; más tarde, toda la sociedad alcanzó un consenso de la industria: el comportamiento sensible, por defecto, debe correr sobre HTTPS.  
La era de la IA llegará al mismo consenso:  
**Las acciones de IA sensibles que producen consecuencias en el mundo real deben, por defecto, ocurrir dentro de Faying.**

Esto no es conservadurismo; es respeto por la estructura de la responsabilidad.  
Lo que queremos no es una entidad automática más rápida. Lo que queremos es una manera de simbiosis que permita a los humanos conservar la vista, conservar el freno y conservar la atribución.

Esto es lo que entiendo que es la manera de convivir con iFay:  
**conexión fuerte, fusión fuerte, pero nunca fuera de Human View.**

---

## Para saber más sobre nuestro pensamiento
- Human View: https://ifay.ai/es/docs/Faying-Protocol/blueprint/11-Visi%C3%B3n%20Humana  
- Semántica Dual de Faying (State y Action): https://ifay.ai/es/docs/Faying-Protocol/blueprint/12-Sem%C3%A1ntica%20Dual%20de%20Faying  
- Estado Rogue y Atribución de Responsabilidad (Rogue Fay): https://ifay.ai/es/docs/Faying-Protocol/blueprint/13-Estado%20Rogue%20y%20Atribuci%C3%B3n%20de%20Responsabilidad  
- Phase 1 Human Prime ↔ iFay: https://ifay.ai/es/docs/Faying-Protocol/blueprint/05-Phase%201%20Human%20Prime%20y%20iFay  
