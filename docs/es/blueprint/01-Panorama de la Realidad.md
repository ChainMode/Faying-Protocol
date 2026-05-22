# Panorama de la Realidad

AI Agent se ha convertido en un término común en el mundo del software. Hace referencia a una clase de instancias de ejecución inteligente capaces de llevar a cabo de forma autónoma funciones específicas: usted le da un objetivo, y planifica, invoca herramientas y produce resultados por su cuenta.

Sin embargo, en aplicaciones empresariales, sectores regulados y escenarios transoberanos, el despliegue de AI Agents casi siempre se detiene en el mismo umbral: **cuando un Agent comete un error, se excede o incumple un contrato, la responsabilidad no puede rastrearse hasta una parte responsable concreta a la que se pueda demandar y obligar a pagar daños**. Este bloqueo es ya consenso en la industria. Los CIO, los asesores legales, las aseguradoras y los reguladores ven todos el umbral, pero ninguna herramienta técnica o jurídica disponible, por sí sola, puede atravesarlo.

El concepto de Fay está diseñado por ingeniería inversa precisamente desde este umbral. Toda la distinción entre Fay y Agent se reduce a una sola cosa: **un Fay debe estar montado de manera obligatoria a una entidad responsable**.

- **iFay** — Individual Fay. Una entidad inteligente montada obligatoriamente uno-a-uno a un Human Prime (Prime Humano). En la capa de protocolo, un iFay porta la persona física específica a la que pertenece; si se elimina esa atribución, deja de ser un iFay.
- **coFay** — Un Fay compartido. Solo se le permite operar cuando está atribuido explícitamente a un individuo u organización con la capacidad legal de asumir responsabilidad. Una vez que esa atribución caduca, debe detenerse.

Esta definición eleva la trazabilidad de la parte responsable desde un problema de cumplimiento parcheado en la capa de aplicación hasta una condición de existencia en la capa de protocolo. Bajo la definición de este blueprint, un Fay que no pueda ser montado a una entidad responsable simplemente no es un Fay.

Pero una definición es solo un nombre. El problema real es de ingeniería: **¿cómo aseguramos que un AI Agent opere siempre en un estado de responsabilidad inquebrantable?** La respuesta a esa pregunta es el Faying Protocol. Define cómo se establece, se sostiene, se verifica y se revoca la relación de "montado a una entidad responsable", de modo que cada acción que tome un Fay corresponda a un Human Prime trazable o a un rol organizacional.

Este capítulo expone la forma concreta de este umbral en siete dimensiones, y muestra por qué la combinación predominante de herramientas de ingeniería y jurídicas — IAM, OAuth, derecho de responsabilidad por producto, cumplimiento de plataforma, AI Alignment — no puede sostener ninguna de ellas.

## Economía y estructura laboral

La asunción del trabajo de base está en gran medida completada, mientras que el marco jurídico de responsabilidad sigue viviendo en el nivel de los códigos de puesto.

En una empresa de comercio electrónico de tamaño medio, las seis categorías — atención al cliente, operaciones, compras, conciliación, cobros y revisión de cumplimiento — tienen hoy entre el sesenta y el ochenta por ciento de su trabajo diario gestionado por Fays. La introducción fue gradual, presentada en su mayor parte como "actualizaciones de herramientas". El resultado: cuando los reguladores rastrean retroactivamente una decisión anómala, la persona responsable en el organigrama de códigos de puesto no puede explicar en qué día, por qué Fay, bajo qué regla se tomó esa decisión. No puede explicarlo, y no puede asumirlo, pero la persecución del sistema legal hacia ella no se detiene por ello.

El derecho laboral, el derecho tributario y los regímenes de responsabilidad de puesto no han ido al mismo ritmo. Asumen que la persona en el rol es la actuante. Esa asunción sostuvo toda la asignación de responsabilidad del trabajo digital durante las últimas tres décadas; hoy está fallando silenciosamente.

Una capa más profunda, los Fays ya han comenzado a actuar entre organizaciones. El Fay de compras de una plataforma logística y el Fay de cotización de una plataforma de almacenaje cierran de forma autónoma un contrato de siete cifras durante la noche; ambos sistemas registran `Fay-Compras-A y Fay-Cotización-B alcanzaron acuerdo a las 03:14:27`. Cuando algo sale mal, ambos equipos legales buscan a su respectivo "responsable de compras" y obtienen la respuesta "no sé nada de esta transacción". El derecho contractual asume que ambas partes tienen personas físicas contratantes específicas; esa asunción no se sostiene en la densidad de colaboración Fay-a-Fay. Cada contrato adicional de este tipo añade otra pieza de deuda jurídica que los tribunales deberán resolver caso por caso.

## El mundo físico

Un Fay en el espacio físico es más peligroso que un Fay en el espacio de información. La razón es simple: los errores en el espacio de información pueden deshacerse; los errores en el espacio físico no.

La entrega con drones es ya rutina en muchos lugares. Los robots de servicio doméstico han entrado en el mercado de consumo. El kilometraje de despliegue de la conducción autónoma se duplica año tras año. Ninguno de estos dispositivos es una extensión teleoperada: el Fay a bordo, el Fay en la nube y la estrategia del proveedor producen conjuntamente decisiones en una mezcla a tres bandas. Cuando un dron acaba estrellándose contra un muro cortina, no se puede nombrar un extremo responsable disponible: ni el Fay a bordo, porque solo es un programa; ni el Fay en la nube, porque corre sobre la infraestructura de otra empresa; ni el fabricante, porque puede aportar pruebas de que "nuestro producto no mostró tal patrón de comportamiento en pruebas"; ni el usuario, porque el usuario solo pulsó "ir".

Las compañías de seguros han comenzado discretamente, en los últimos dos años, a rechazar la cobertura de varias categorías de productos que contienen capacidad de decisión Fay. La razón no es que estos productos sean más peligrosos: según las estadísticas, sus tasas de accidentes son incluso menores; es que sus accidentes no pueden asignarse. La esencia del seguro es la conversión del riesgo asignable en un precio. El riesgo que no puede asignarse no puede valorarse.

La ley de Responsabilidad por Producto asume que un producto tiene un diseñador identificable, y que el diseñador es responsable por defectos de diseño. El "diseño" de un Fay es distribuido: el modelo fundacional de A, el ajuste fino de B, el Runtime de C, la integración de D, y el patrón de invocación decidido por E. Cuando algo sale mal, cinco empresas se señalan unas a otras, y los reguladores se enfrentan a un grafo de atribución insoluble.

El derecho penal va aún más profundo. El derecho penal solo persigue a quienes tienen capacidad penal. Un Fay no es tal sujeto. Cuando un Fay causa directamente daño corporal, el derecho penal no puede encontrar concepto alguno de "actor" que reciba el acto. Esto no significa que nadie tenga la culpa; significa que la cadena lógica del derecho penal se rompe en el Fay.

## Información y confianza social

Los Fays que hablan en nombre de alguien no son los deepfakes de las noticias; son ya una característica rutinaria para usuarios comunes. Una persona tiene un Fay que responde a docenas de comentarios, publica unas pocas entradas y mantiene la "calidez" de los lazos sociales en plataformas sociales cada día. Las respuestas "suenan como ella", porque el Fay aprende continuamente su tono; pero el contenido lo genera de forma autónoma el Fay, y ella ni siquiera lo ha leído.

Los Fays que escriben contenido cargan una porción cada vez mayor de la "cola larga creativa" en plataformas de creadores: enormes cantidades de descripciones de productos, promociones de campañas y respuestas de preguntas frecuentes viajan sobre cuentas de personas reales pero las producen Fays. Los Fays que firman contratos en nombre de alguien son ya rutina en servicios de suscripción, contratación de energía y subasta de espacios publicitarios. Un contrato muestra "firmado por el usuario X en un momento dado", pero el usuario X estaba dormido en ese momento.

Las plataformas han comenzado a percibir el cambio. Los sistemas de moderación de contenido de las grandes plataformas, en los últimos dos años, han sido forzados a procesar una nueva pregunta: ¿este contenido fue escrito por el usuario, escrito por IA bajo instrucción del usuario, o generado de forma autónoma por IA bajo la cuenta del usuario? Los tres casos corresponden a responsabilidades, estrategias de gestión y riesgos de cumplimiento totalmente distintos, y las plataformas no tienen medios técnicos para distinguirlos de manera fiable. Solo pueden adivinar a partir de rasgos estadísticos burdos, con falsos positivos masivos y casos no detectados masivos al mismo tiempo.

Una categoría más sensible pero ineludible: los datos de opinión pública en ciclos electorales han mostrado, más de una vez, que la curva en la que "el apoyo a algún tema sube del 18 % al 41 % en tres días" está respaldada por cientos de miles de cuentas Fay produciendo declaraciones convergentes en sincronía. El crédito comercial ha visto endosos masivos liderados por Fays: en las reseñas de una marca nueva, cuatrocientas de quinientas entradas son generadas por Fays mediante el trabajo conjunto de tres agencias. Cada reseña "parece la experiencia de un usuario real", pero ningún autor existe.

Esta reescritura no es un único gran ataque; es diaria, continua y acumulativa. La sociedad procesa información cada día con la asunción implícita de "esto lo publicó tal persona". Cuando una porción cada vez mayor de esa asunción deja de sostenerse, los cimientos de la confianza social se vacían silenciosamente, y el vaciado no deja alarma evidente.

## Privacidad y datos

La premisa para dejar que un Fay "actúe en su nombre" es que debe "conocerle". Necesita conocer sus preferencias, hábitos, relaciones, finanzas, historial médico, agenda, ubicación, intención. Un Fay es la entidad que ha conocido a un Human Prime más profundamente que cualquier cosa en la historia: más que un cónyuge, porque está a su lado cada día; más que un médico, porque puede unir registros entre todos los hospitales; más que su empleador, porque puede unir el correo de trabajo, el correo personal y su calendario.

La premisa para todo esto es una relación de confianza entre el Fay y el Human Prime. Hoy esa "relación" es por lo general nada más que una casilla en un acuerdo de usuario y un interruptor dentro de un producto. Esa forma queda muy por debajo de lo necesario para sostener un conocimiento tan profundo.

Los Fays tampoco corren de forma aislada. Un Fay personal manejando una tarea puede invocar a un coFay del lado de la nube, que a su vez invoca capacidades de proveedores externos, que corren sobre la infraestructura de otra empresa más. A lo largo de esta cadena de invocación, ¿por cuántas partes pasan los datos privados del usuario? ¿El paso es por lectura, copia o reescritura? ¿Qué partes solo transitan, y cuáles retienen copias? Nadie puede responder con claridad; cada parte solo puede prometer por su segmento, y no hay vista global.

GDPR y PIPL están construidos sobre un modelo tripartito: titular del dato, encargado del tratamiento, responsable del tratamiento. El modelo asume que las tres partes son organizaciones o personas físicas, identificables, exigibles e inspeccionables por los reguladores. Con Fays en escena, el modelo tripartito pierde inmediatamente su correspondencia. ¿Es un Fay un encargado o un responsable? ¿O algo intermedio? ¿O una nueva clasificación como "agente del titular del dato"? Pero el concepto de agente asume a su vez que el agente posee personalidad jurídica.

Los reguladores de distintas regiones están intentando llenar este hueco. Pero una premisa no puede evitarse: la capa de protocolo debe primero declarar los hechos con claridad — a qué Fay pertenece este flujo de datos, a qué Human Prime está atribuido, si está en Faying State o en estado Rogue, si se comparte con terceros. Sin eso, el acoplamiento jurídico siempre quedará vacío.

## Transoberano y entre plataformas

La Internet temprana estableció TCP/IP — un protocolo de transporte transoberano y entre proveedores. No resolvió "qué hace la capa de aplicación", pero sí "cómo dos partes cualesquiera pueden intercambiar datos sin confiar la una en la otra".

A la era Fay le falta un equivalente "protocolo de confianza mutua transoberano y entre proveedores". Cuando un Fay del lado de EE. UU. colabora con un Fay del lado de China para completar una transacción de comercio electrónico transfronterizo, tres preguntas no tienen respuesta compartida: ¿quién prueba que el otro lado es realmente el Fay que dice ser? ¿Quién prueba que está, en este momento, bajo la custodia de su Human Prime? ¿Quién asume la responsabilidad cuando algo sale mal? Hoy cada escenario de colaboración Fay transfronteriza responde estas tres preguntas de forma ad hoc, bilateral y contractual. Este patrón de N² contratos no escala cuando el número de Fays explota.

Para que los Fays puedan interoperar siquiera en ausencia de un protocolo unificado, los ingenieros apilan medidas temporales una sobre otra: cada proveedor emite su propia API key, cada plataforma construye su propio proxy OAuth, cada integración entre proveedores escribe su propio pacto de cumplimiento. El sistema apenas funciona cuando los Fays se cuentan por cientos de miles. Cuando crecen a cientos de millones o miles de millones, el coste operativo total de este sistema superará con mucho el beneficio total que los propios Fays aporten. Esta es una curva exponencial en términos de ingeniería; no puede resolverse "metiendo más ingenieros" y debe aplanarse desde la raíz unificando los hechos básicos en la capa de protocolo.

El punto de dolor más sutil es el vacío estructural. Un Fay sirve a usuarios finales en el país A, corre sobre una nube en el país B, fue entrenado por un proveedor en el país C, usa un modelo fundacional del país D, e invoca capacidades de terceros del país E. Cada uno de los cinco países tiene legislación de protección de datos, regulación de IA y derecho de responsabilidad por producto, pero los cinco regímenes legales no se interconectan, y cada uno solo puede alcanzar un pequeño segmento de esta cadena. Algún día los reguladores se verán forzados a comprimir la operación Fay transfronteriza por medida administrativa — momento en el cual la pérdida no será solo para la industria Fay, sino para todo valor que la sociedad pudiera haber obtenido del ecosistema Fay.

## Identidad individual y agencia

Los sistemas de autenticación de identidad — doble factor, biometría, Passkey, OAuth — asumen todos que los dos extremos de la autenticación son "aplicación ↔ usuario humano". Cuando un Fay se interpone en medio, el sistema empieza a sentirse desviado: la aplicación ve "este es el token del usuario", pero la solicitud la inicia el Fay; el usuario ha habilitado "desbloqueo por huella para que el Fay actúe por mí", pero si cada acción Fay subsiguiente sigue representando la intención presente del usuario no se puede verificar de manera continua; un atacante que capture una de las ventanas de autorización del usuario puede suplantar al Fay y hacer cualquier cosa dentro de esa ventana, con la aplicación y el usuario en serias dificultades para detectarlo.

Esta es la fisura estructural de la autenticación de identidad en la era Fay. No puede parchearse "añadiendo otro factor". La pregunta no es "¿es el usuario quien inicia sesión?", sino "¿está ocurriendo este comportamiento específico bajo la custodia del usuario?".

Existe un concepto jurídico de larga tradición llamado **agencia** — una persona puede autorizar a otra a actuar en su nombre en ciertos asuntos. La relación de agencia tiene reglas legales claras: alcance de la agencia, plazo de la agencia, deber de diligencia del agente, consecuencias legales cuando un agente excede su autoridad.

Cuando los Fays entran en relaciones de agencia, todas estas reglas necesitan ser reexaminadas. ¿Cómo se define el "deber de diligencia" de un Fay — debe detenerse y preguntar cuando el alcance de la agencia es ambiguo? ¿Cómo se detecta el "exceso de agencia" por parte de un Fay — cuánto debe divergir su juicio de la intención verdadera del mandante para que cuente como exceso? ¿Dónde está el límite de acción de un Fay cuando el mandante está incapacitado? ¿La muerte del mandante termina automáticamente la agencia del Fay, o algunas agencias pueden continuar en la administración de la herencia?

Estos no son ejercicios sobre papel para juristas académicos. Están aflorando hoy, caso por caso, en hospitales, bancos, notarías y tribunales; cada caso es resuelto por un juez según su intuición, y las resoluciones se contradicen entre sí. La premisa para que el régimen jurídico del agente se acople con la era Fay es que la capa de protocolo pueda decir de forma estable al sistema legal: bajo qué relación Faying se inició esta acción Fay, a qué alcance y plazo de agencia corresponde, y si está dentro de su período efectivo.

## Por qué las soluciones existentes no bastan

Llegado a este punto, surge una pregunta natural: estos puntos de dolor son reales, pero ¿no hay herramientas existentes? IAM, OAuth, limitación de tasa de API, firma de Webhook, AI Alignment — ¿no resuelven ya algo de esto?

La respuesta es que resuelven problemas adyacentes, no el problema central.

**IAM resuelve "quién es la cuenta", no "a quién pertenece el acto".** Toda la capacidad de un sistema IAM orbita en torno a la identidad de la cuenta — cómo se llama la cuenta, a qué organización pertenece, qué permisos tiene. Su premisa de diseño es que hay una persona detrás de la cuenta, y la identidad de la persona es la atribución del acto. Un Fay no es una cuenta; es una entidad acoplada detrás de una cuenta que toma acción. Cuando un Fay inicia una acción bajo la identidad de una cuenta, todo lo que ve IAM es "esta cuenta tiene derecho a hacer esto", pero no puede responder "¿es la persona detrás de la cuenta quien lo hace ahora mismo, o lo hace el Fay?".

**OAuth y las firmas Webhook resuelven "la legitimidad de la llamada", no "la atribución de la responsabilidad".** OAuth resuelve "¿está la aplicación A autorizada a llamar a la aplicación B en nombre del usuario?"; la firma Webhook resuelve "¿este callback proviene realmente del remitente declarado?". Ambos atañen a la legitimidad de la cadena de llamada; ninguno porta campo alguno que exprese "a qué Human Prime específico pertenece el acto subyacente". Cuando un Fay llama a alguna API con un token obtenido vía OAuth, OAuth ve "el token es válido, la llamada es legítima", pero no sabe si la llamada fue iniciada por el Fay en Faying State o en estado Rogue violando las reglas. OAuth y Webhook no necesitan ser reemplazados; necesitan ser cubiertos por una capa de protocolo cuya preocupación dedicada sea "la atribución del acto".

**Los marcos de cumplimiento de plataformas Agent son cerrados; las plataformas no interoperan.** Cada plataforma Agent construye su propio marco de cumplimiento: términos de uso, moderación de contenido, detección de abuso, declaraciones de responsabilidad. Estos marcos son relativamente coherentes consigo mismos dentro de la plataforma, pero tienen dos limitaciones fundamentales: las plataformas no interoperan; y la granularidad se detiene en el nivel de cuenta o aplicación, sin alcanzar nunca el acto específico. Un marco de cumplimiento puede prohibir una cuenta abusiva, pero no puede emitir un juicio en tiempo real al nivel de "¿debería ocurrir este acto?".

**AI Alignment se ocupa de los valores internos del Fay; no resuelve la atribución de una parte responsable externa.** Alignment resuelve "qué quiere hacer el Fay"; el Faying Protocol resuelve "si el Fay puede actuar ahora mismo, y a quién pertenece el acto una vez que actúa". Un Fay perfectamente alineado puede aún producir acción sin la custodia de un Human Prime, y esa acción no tiene a nadie que reciba la responsabilidad. Un Fay completamente desalineado puede aún ser bloqueado en estado Rogue y forzado a la inacción. Alignment es la ética interna de un Fay; el Faying Protocol es el régimen externo de responsabilidad de un Fay. Ambos son indispensables; ninguno puede reemplazar al otro.

## Cierre

Los puntos de dolor en las siete dimensiones abarcan industria, derecho y sociedad, pero se cruzan en lo mismo:

> **Cuando un Fay actúa, ¿quién es responsable del acto?**

La Era de la Operación Manual tenía una respuesta llana que no necesitaba protocolo para expresarse: la persona cuya mano operaba. En la era Fay esta respuesta ya no se sostiene por defecto; debe expresarse con claridad mediante un protocolo explícito, legible por máquina, que pueda ser verificado conjuntamente por distintos soberanos y distintos proveedores.

Esta es la razón entera por la que existe el Faying Protocol.
