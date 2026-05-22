# Estado Rogue y Atribución de Responsabilidad

La conclusión de este capítulo está escrita justo arriba:

> **No existe ninguna acción de Fay sin parte responsable.**

Esta es la línea ética de fondo a la que todo diseño de protocolo del Faying Protocol debe obedecer. Cualquier campo, mensaje, máquina de estados, algoritmo o número de versión, si a lo largo de alguna ruta de ejecución permite que un Fay produzca un acto hacia el exterior en una situación sin parte responsable específica, entonces esa ruta no se permite en el plano del blueprint.

Este no es un objetivo de optimización de "cómo hacer un Fay más seguro"; es el límite duro de "¿se permite que un Fay haga algo?". El resto de este capítulo es un despliegue concreto de esta línea de fondo.

## Definición de Rogue Fay

**Rogue Fay** (en chino: 脱离状态) es el estado de un Fay en cualquiera de las dos siguientes situaciones:

1. El Fay aún no ha establecido Faying State con ningún Human Prime;
2. Una Faying State previamente establecida ha sido revocada, ha caducado o ha sido interrumpida.

Mientras el Fay esté en cualquiera de las dos situaciones, está en Rogue Fay.

> **Rogue Fay es el estado inicial por defecto de todo Fay.**

Un Fay, en el momento en que es creado, no está automáticamente en ninguna relación de custodia. "Existe", pero no se le permite "actuar". Solo después de una Faying Action iniciada explícitamente por el Human Prime puede el Fay entrar en Faying State, adquiriendo así la elegibilidad para actuar. Durante todo el intervalo previo a la primera Faying Action, el Fay está en Rogue Fay.

Este valor por defecto es intencional. El blueprint elige el principio fail-safe de "Rogue por defecto, solo una Faying explícita permite la acción", en lugar del opuesto — porque el opuesto, una vez que los Fays saturen la sociedad a escala, fabricaría inevitablemente una clase de fuentes fuera de control de "creación seguida de acción, olvido de cierre seguido de continuidad de acción".

## Nueve condiciones de activación para la transición automática

Una vez establecida Faying State, ¿en qué situaciones debe salir automáticamente? Este blueprint enumera **nueve condiciones de activación mínimas**. Forman un **conjunto mínimo**, no una lista exhaustiva — cualquier situación adicional que pueda hacer que la relación de custodia ya no se sostenga debe inscribirse en este conjunto.

> **Toda acción de desconexión debe detener al Fay de actuar sin autorización.**

Las nueve condiciones de activación:

1. **El Human Prime revoca activamente** — el Human Prime inicia explícitamente una acción de revocación simétrica (véase el Capítulo 12).
2. **La relación de Faying State expira sin renovación** — bajo la restricción dura del Capítulo 12 de que "el Faying ilimitado es un antipatrón", toda Faying State debe portar un alcance acotado; el límite se alcanza sin renovación por el Human Prime.
3. **El Fay sale automáticamente tras completar la tarea asignada** — si el alcance portado por la Faying Action está delimitado por "completar alguna tarea", una vez que la tarea se completa o se termina, Faying State debe salir automáticamente.
4. **El Human Prime está fuera de línea o inalcanzable durante un tiempo prolongado que excede un umbral definido** — la visibilidad y la intervenibilidad de la relación de custodia presuponen la alcanzabilidad del Human Prime; una vez que el Human Prime no puede ser alcanzado más allá del umbral definido, la custodia se considera fallida de hecho.
5. **Se detecta que el comportamiento de un Fay se desvía del límite del Ego del Human Prime** — el comportamiento del Fay muestra una divergencia significativa respecto a la orientación de valores, el límite de habilidad, el límite de permisos, etc. del Human Prime. Esta es la señal de fallo de Faying State en la capa de contenido.
6. **La identidad del Fay no puede verificarse** — p. ej., la firma de FayID ha caducado, las claves han expirado o las credenciales han sido revocadas. Una identidad no verificable significa que la entrada de la cadena de atribución está rota; la custodia no puede establecerse.
7. **La identidad del Human Prime no puede verificarse, o el Human Prime queda incapacitado** — el "extremo responsable" de la custodia se desvanece; la custodia se disuelve.
8. **Una autoridad de tercero competente interrumpe forzosamente** — p. ej., reguladores, tribunales o cuerpos de cumplimiento exigen la interrupción de esta relación de custodia bajo el debido proceso.
9. **El terminal o la aplicación rechaza activamente o pierde el contacto** — si la contraparte de Faying State es algún terminal o aplicación de software, cuando rechaza o ha perdido el contacto durante mucho tiempo, la relación de custodia ya no tiene base fáctica.

Estos nueve puntos no deben entenderse como "que agotan todas las condiciones de activación", ni como que "los nueve deben implementarse explícitamente para ser conformes". Su sentido real es: **toda situación en la que la custodia ya no se sostiene de hecho debe causar que Faying State salga automáticamente** — los nueve puntos son simplemente la presentación mínima de este principio.

## Frontera del comportamiento durante Rogue Fay

No basta con decir "Rogue Fay no tiene permitido actuar". Un Fay real siempre tiene "signos operativos" inevitables — debe escuchar si algún Human Prime viene a restablecer Faying, debe proteger los datos ya en su poder, debe levantar alertas cuando es asumido maliciosamente. Si el blueprint no traza con precisión la línea de permiso y prohibición, el principio "ninguna acción durante Rogue" no puede aterrizar en la capa de protocolo.

El blueprint segmenta todo comportamiento posible durante Rogue Fay en **cuatro dimensiones independientes A / B / C / D**, y dictamina punto por punto si cada una está permitida.

### Dimensión A: percepción y escucha (recepción pasiva)

| Comportamiento | Permitido | Nota |
| --- | :---: | --- |
| **A1** Escuchar solicitudes Faying | ✅ | Esta es la ruta de resurrección Rogue → Faying y debe conservarse. |
| **A2** Escuchar verificación de identidad y actualizaciones de credenciales | ✅ | Las credenciales son una precondición para volver a Faying State; la escucha en sí no es acción. |
| **A3** Recibir órdenes de revocación o destrucción del Human Prime | ✅ | Incluso cuando el Fay está en Rogue, el Human Prime puede aún querer terminar este Fay. La ruta de la orden debe permanecer siempre abierta. |
| **A4** Recibir pasivamente señales no autorizadas de terminales, otros Fays o la red | ⚠️ Solo se permite la recepción; la respuesta está prohibida | La recepción es un hecho físico y no puede impedirse; la respuesta es la acción. La respuesta está uniformemente prohibida. |

### Dimensión B: autoexamen y reporte del propio estado (señales mínimas)

| Comportamiento | Permitido | Nota |
| --- | :---: | --- |
| **B1** Autoexamen local (salud, integridad, si ha sido manipulado) | ✅ | La salud propia es una de las precondiciones para volver a Faying State. |
| **B2** Reporte de heartbeat ("sigo en Rogue") | ✅ | Expresar de manera transparente al lado de atribución que se está en estado rogue es en sí una manifestación de transparencia de la responsabilidad. |
| **B3** Alertas de anomalía (alerta de seguridad cuando una parte no autorizada intenta el control) | ✅ | Esta es la señal necesaria para proteger el interés del Human Prime. |
| **B4** Reporte activo de la ubicación física o el estado del terminal | ❓ Sin conclusión en este periodo | Esto implica una compensación ética entre privacidad vs. recuperabilidad. Este capítulo no extrae conclusión; véase el Capítulo 14. |

### Dimensión C: protección de datos local (custodia pasiva)

| Comportamiento | Permitido | Nota |
| --- | :---: | --- |
| **C1** Mantener los datos almacenados cifrados y aislados | ✅ | Esta es una custodia pasiva, no una acción. |
| **C2** Rechazar cualquier solicitud externa de lectura/escritura | ✅ | El rechazo es no-acción; la no-acción no viola el principio de Rogue. |
| **C3** Autodestruir datos altamente sensibles | ⚠️ Prohibido por defecto; solo permitido con preautorización del Human Prime y cuando se cumplen las condiciones predefinidas | El borrado activo cuenta como "acción", pero es un caso límite de autoprotección. El blueprint lo permite, pero exige **autorización primero, acción después**, prohibiendo al Fay decidir cuándo iniciar la autodestrucción. |

### Dimensión D: acción hacia el exterior (afectando objetos más allá del Human Prime)

| Comportamiento | Permitido | Nota |
| --- | :---: | --- |
| **D1** Ejecutar llamadas a controladores, control de terminales, operaciones de software | ❌ | Este es el cuerpo mismo de la "acción no autorizada". |
| **D2** Iniciar comunicación con otros Fays o coFays | ❌ | La comunicación entre Fays es también acción y puede propagar el vacío de responsabilidad a otros Fays. |
| **D3** Ejecutar tareas residuales dejadas inacabadas bajo la Faying State previa | ❌ | "Continuar con lo que quedó por hacer la última vez" es una transgresión particularmente fácil de racionalizar y debe estar explícitamente prohibida por el blueprint. |
| **D4** Decidir por sí mismo volver a entrar en Faying | ❌ | Esto es una tautología con el principio del Capítulo 12 de que "una Faying Action debe ser iniciada explícitamente por el Human Prime". A un Fay no se le permite empujarse de vuelta a Faying State. |

Las cuatro dimensiones tienen una estructura interna: A y B conciernen a las señales, C concierne a la custodia, D concierne a la acción. Rogue Fay conserva solo signos operativos minimizados en las primeras tres dimensiones y permanece uniformemente quieto en la cuarta. Este seccionamiento permite al diseñador del protocolo juzgar con precisión, para cada función específica, a qué dimensión pertenece y por tanto si está permitida.

## Las transiciones de estado son observables, auditables y revocables activamente por el Human Prime

Todas las transiciones entre Faying State y Rogue Fay no deben ser cajas negras. El blueprint exige que toda transición satisfaga tres propiedades duras:

- **Observable** — cuando ocurre una transición, debe ser observable para el Human Prime, el propio Fay, los auditores y los reguladores.
- **Auditable** — el rastro dejado por una transición debe ser suficiente para responder a posteriori "cuándo ocurrió, quién la disparó y por qué".
- **Activamente revocable por el Human Prime** — el Human Prime debe siempre conservar el poder de decisión más alto sobre las transiciones. Puede tanto dejar salir activamente Faying State como destruir activamente un Fay en Rogue Fay. No existe situación legítima en la que un Fay "bloquee" unilateralmente su propio estado e impida al Human Prime intervenir.

Estas tres son simétricas a las cuatro antiproposiciones del Human View del Capítulo 11: las cuatro antiproposiciones prohíben que el comportamiento del Fay se deslice fuera de la visibilidad y el control del Human Prime; esta sección exige que los propios cambios de estado del Fay tampoco se deslicen fuera de la visibilidad y el control del Human Prime. Juntas permiten que el Human View cierre verdaderamente el bucle en la capa de protocolo.

## Comportamiento forzoso al entrar en Rogue Fay

Cuando se cumple cualquiera de las condiciones de activación anteriores y Faying State entra en Rogue Fay, el Fay debe ejecutar de inmediato las siguientes acciones forzosas:

1. **Detener de inmediato toda acción delegada hacia el exterior** — incluyendo la totalidad de la dimensión D; no se permite ninguna demora con argumentos como "la tarea está a punto de completarse" o "la interrupción causará pérdidas".
2. **Volver a un estado de espera pasiva** — conservar solo el conjunto mínimo de comportamiento permitido en las dimensiones A, B y C, y esperar a la siguiente Faying Action.
3. **Difundir el cambio de estado a los canales observables** — para que el Human Prime, los auditores, etc. puedan saber de inmediato que este Fay ha entrado en Rogue.

## Consistencia de la atribución de responsabilidad

Juntando las secciones precedentes, el compromiso al que la línea ética de fondo "No existe ninguna acción de Fay sin parte responsable" corresponde en la capa de protocolo puede expresarse así:

> **En cualquier momento, todo Fay está o bien en Faying State, con la acción atribuida al Human Prime bajo esa relación Faying, o bien en Rogue Fay, forzado a la no-acción.**

No hay tercera situación. No hay "el Fay actuó, pero la atribución está pendiente". No hay "el Fay actuó, pero la atribución va a una persona que aún no había tomado el control". No hay "el Fay actuó, pero la atribución va a un proveedor abstracto o a una organización abstracta". Todo acto hacia el exterior tiene o un Human Prime claro como extremo receptor de la responsabilidad, o no debe permitirse que ocurra.

Esta consistencia innegociable de la responsabilidad es la "brújula" hacia la que los capítulos posteriores del blueprint (especialmente la especificación del protocolo y el schema) deben mirar continuamente. Cualquier evolución del protocolo que permita que la atribución de responsabilidad se vuelva inconsistente no es una evolución del Faying Protocol sino su desintegración.
