# Posición del Framework iFay

Este capítulo responde solo a dos preguntas: ¿qué aspecto tiene aproximadamente el framework iFay, y dónde se sitúa el Faying Protocol dentro de él?

El framework iFay tiene en sí mismo una cobertura amplia y muchos componentes; cualquiera de ellos, incluso ligeramente desplegado, conduce a detalles técnicos de campos, protocolos y formatos de mensaje. Las tres categorías de activos en este repositorio — blueprint, especificación de protocolo y schema — portan únicamente el Faying Protocol. Todos los miembros de la familia de protocolos iFay distintos del Faying Protocol son referenciados de manera uniforme enlazando a [ifay.ai](https://ifay.ai); este repositorio no los reformula, reescribe ni deriva.

## Esquema del framework iFay

Siguiendo el diseño global en [ifay.ai](https://ifay.ai), el framework iFay puede entenderse aproximadamente como una estructura de cuatro capas.

**La capa de entidades** contiene dos clases de entidades inteligentes vinculadas por el protocolo. **iFay** (Individual Fay) está montado obligatoriamente uno-a-uno a un Human Prime específico — quite esa atribución, y deja de ser un iFay. **coFay** es un Fay compartido; solo se le permite operar cuando está atribuido explícitamente a un individuo u organización con la capacidad legal de asumir responsabilidad. Ya sea iFay o coFay, el Faying Protocol discutido en este blueprint los restringe por igual: una vez que la atribución caduca, el Fay debe detenerse.

**Los componentes del núcleo** incluyen varias partes inseparables dentro de cada entidad Fay. **FayID** es la identidad unificada y única de un Fay, la base de identidad para entrar en cualquier relación de custodia. **Ego** es el paradigma de referencia alineado con el perfil de un individuo o rol específico, restringiendo el espacio autónomo del Fay a lo largo de la orientación de valores, las preferencias de interés, los hábitos, los límites cognitivos y de habilidad, los límites de permisos y el estilo de trabajo. Ego no es un modelo gigante de AGI; es un "límite de personalidad". **Runtime** es el runtime virtual de un Fay, que permite que iFay y coFay se ejecuten de forma compatible en distintos terminales, sistemas operativos y escenarios de aplicación embebida. FayID y Ego son las dos precondiciones que permiten que el Faying Protocol surta efecto — el primero porta la atribución de identidad, el segundo porta el límite del comportamiento.

**La familia de protocolos** incluye un conjunto de protocolos por los cuales un iFay se conecta, percibe y colabora con el mundo. Más allá del tema de este blueprint, el **Faying Protocol**, incluye al menos: protocolos de transporte bidireccional relacionados con el control de terminales, protocolos amigables a la UI orientados a interfaces de usuario humanas, protocolos de comunicación semántica entre iFay y coFay que despojan la capa de traducción de UI, protocolos de difusión y suscripción para capacidades del lado de la nube, y cualquier miembro futuro. Para detalles técnicos de la familia de protocolos, véase [ifay.ai](https://ifay.ai); este repositorio no los incluye.

**La estructura de valor** corresponde a un nuevo modelo de estructura laboral y distribución de valor. Esta capa incluye desplazamientos sistémicos: la salida del trabajo humano del trabajo, el aplanamiento del conocimiento, las garantías universales de subsistencia, la nueva creación de valor, la nueva estratificación social — con mecanismos como MeriToken portando la medición de valor. Este es el trasfondo de largo plazo del framework iFay; no aterriza directamente en la especificación del Faying Protocol. Véase [ifay.ai](https://ifay.ai) para detalles.

## La posición del Faying Protocol dentro de él

Juntando las cuatro capas, la posición del Faying Protocol dentro del framework iFay puede anclarse con precisión así:

> **El Faying Protocol se sitúa por encima de la "capa de entidades" y los "componentes del núcleo" y es el subprotocolo dentro de la familia de protocolos responsable de la semántica de "control bajo custodia y control delegado". Convierte la pregunta raíz — "¿está atribuido FayID a algún Human Prime?" — en un conjunto de estados de conexión y acciones que pueden establecerse, sostenerse y revocarse.**

No es una definición de capacidad Fay, así que no especifica qué puede hacer un Fay. No es un código de conducta Fay, así que no especifica cómo debería hacerlo un Fay. Responde solo a una pregunta:

> **Para este acto Fay, ahora mismo, ¿quién es responsable?**

Por esta razón, el Faying Protocol no es ni el protocolo más deslumbrante ni el más profundo del framework iFay, pero es el que no puede saltarse. Una vez que falte, el framework iFay entero degrada inmediatamente a un ecosistema Agent corriente, llevando el vacío de responsabilidad descrito en el Capítulo 1 a la sociedad.

## Frontera entre este repositorio y el framework iFay

```
                 +-------------------+
                 |  Panorámica ifay.ai|
                 |   Framework iFay   |
                 |   (cuatro capas)   |
                 +-------------------+
                          │
                          │  Este repo despliega un miembro
                          ▼
            +---------------------------+
            |   Proyecto Faying Protocol |
            | (todos los activos del repo)|
            +---------------------------+
                          │
            ┌─────────────┼──────────────┐
            ▼             ▼              ▼
        Blueprint  Especificación      Schema
   docs/{lang}/   docs/{lang}/         schema/
    blueprint/    specification/  (no entregado este período)
   (esta spec)  (después, spec separada)
```

Las tres categorías de activos en este repositorio portan únicamente el Faying Protocol. Cualquier despliegue en profundidad de otros miembros del framework iFay queda fuera del alcance de este repositorio; por favor diríjase directamente a [ifay.ai](https://ifay.ai).

![Visión general del framework iFay (alpha1): el Faying Protocol se sitúa en la capa contractual de la relación de custodia](../../zh-CN/blueprint/illustration/ifay-framework-alpha1.png)

![Banner del título iFay](../../zh-CN/blueprint/illustration/ifay-title-banner.png)
