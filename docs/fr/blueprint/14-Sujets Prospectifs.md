# Sujets Prospectifs

> **Les sujets ci-dessous sont hors du périmètre de la conception actuelle du Faying Protocol.**

C'est le dernier chapitre du blueprint, et le seul chapitre dont le style diffère de tous les autres. Il ne tire aucune conclusion ; il énumère honnêtement les questions ouvertes. Faire cela a deux objectifs : permettre aux lecteurs, après avoir terminé le blueprint, de savoir précisément ce que le Faying Protocol actuel résout et ce qu'il ne résout pas ; et laisser des points de plug-in clairs pour des spécifications séparées ultérieures.

Chaque sujet de ce chapitre est **laissé sans conclusion** dans cette période. Si une question qui semble simple n'a pas été répondue, ce n'est pas un oubli ; c'est de la retenue.

## Autres sortes de relations Faying

Le Faying Protocol de cette période ne couvre qu'une seule sorte de relation : **Human Prime ↔ iFay**. Au-delà, au moins les quatre sortes de relations suivantes ne sont pas encore introduites dans la conception du protocole.

**Une relation Faying directe entre humain et terminal** — le blueprint de cette période choisit iFay comme la seule forme d'entité digne de confiance pour porter le contrat de tutelle ; par conséquent, l'« être à l'état contrôlé » du terminal doit être exprimé dérivativement à travers le Faying State de l'iFay. Introduire à un stade futur « un Human Prime établissant une relation Faying directement avec un terminal » nécessite d'abord de répondre à plusieurs questions profondes : le terminal a-t-il une « intégrité d'identité » suffisante pour porter un contrat de tutelle ? Une relation directe, en contournant l'iFay au niveau du protocole, ne rendrait-elle pas la chaîne de responsabilité plus difficile à tracer et n'aggraverait-elle pas plutôt la visibilité de Human View ? Lorsque les deux chemins « direct » et « dérivé via iFay » coexistent, comment garantir l'unicité de l'attribution ? Ces questions n'ont pas de réponse satisfaisante dans cette période.

**Une relation Faying directe entre humain et application logicielle** — homologue à l'élément précédent, mais avec une couche de complexité supplémentaire. Une application logicielle est elle-même souvent modulaire, inter-processus et inter-réseau. Lors de l'établissement d'une relation Faying avec une application directement, la frontière de « l'application » elle-même doit d'abord être précisément définie, et cette définition n'a pas encore convergé à travers différents écosystèmes et formes de déploiement. La raison pour laquelle cette période a fait que l'extension de la Phase 3 « prend en charge dérivativement l'application logicielle via l'iFay » est précisément de différer ce problème de définition de frontière.

**Collaboration et délégation iFay ↔ coFay** — c'est le sujet central de la Phase 4. Cette période n'introduit pas la forme protocolaire de la tutelle de coFay pour deux raisons : l'extrémité d'attribution d'un coFay est généralement une organisation ou un rôle, et la manière dont une organisation fait atterrir institutionnellement le devoir de tutelle sur des personnes ou des rôles spécifiques est elle-même une discussion complexe à travers les institutions, le droit et la gouvernance d'entreprise ; et la forme protocolaire pour « le transfert de responsabilité n'est pas perdu » dans la collaboration inter-Fay nécessite que les Phases 1 à 3 soient stables avant d'avoir un point de plug-in approprié.

**Collaboration iFay ↔ iFay** — lorsque plusieurs iFays (chacun attribué à un Human Prime différent) collaborent à travers les relations de tutelle pour accomplir un acte, cela soulève la question du « chemin multi-personne de transfert d'attribution d'action » : l'acte devrait-il être attribué à l'initiateur, au récepteur, ou aux deux selon une règle de répartition ? Cette question est similaire à la conception juridique de la « sous-délégation entre agents » dans la société du monde réel, mais la haute densité de fréquence de la collaboration à l'ère des Fays fait que la vitesse de traitement du droit traditionnel est loin derrière. Ce sujet a besoin de l'évolution simultanée du droit, du protocole et de la gouvernance sociale avant qu'une réponse stable puisse être obtenue.

Les quatre sortes de relations ci-dessus appartiennent toutes aux directions d'évolution à long terme du Faying Protocol. Elles seront enrôlées progressivement dans les Phases 2 à 5 du Chemin de Mission, mais la forme protocolaire de chacune est portée par des spécifications séparées ultérieures et est hors du périmètre de cette période.

## B4 : Reporting de localisation durant Rogue

L'élément 4 de la dimension B au Chapitre 13 (B4) est le seul point de conception de protocole de ce blueprint explicitement marqué « pas de conclusion cette période ».

### Description du sujet

Lorsqu'un terminal pris en charge par un iFay (par exemple, un drone) entre en Rogue Fay, devrait-il continuer activement à reporter sa localisation physique ou son état de terminal au Human Prime d'attribution ?

Par exemple : le drone de Jack, au cours d'une tâche, perd la connexion avec Jack (satisfaisant la condition de déclenchement 4 du Chapitre 13, « le Human Prime est hors ligne ou injoignable pendant un temps prolongé »), et entre en Rogue Fay. La localisation physique du drone change toujours — affectée par l'inertie, le vent, les algorithmes d'atterrissage autonome, et ainsi de suite. La question est : ce drone devrait-il continuer activement à reporter sa position, son niveau de batterie et autre état de terminal au côté de Jack ?

### Une traction bilatérale

**En faveur du reporting continu** — plus un Fay déconnecté reporte, plus il est facile pour le Human Prime de le retrouver et de rétablir Faying. Du point de vue de la récupérabilité, « la localisation est visible » est une capacité qui protège l'intérêt du Human Prime.

**Contre le reporting continu** — une fois qu'un Fay continue à reporter sa localisation en Rogue, un attaquant peut exploiter ce canal : intercepter les informations de localisation pour saisir le rayon d'activité du Human Prime ; falsifier le canal de reporting pour se faire passer pour le côté du Human Prime et induire l'action du Fay ; utiliser le « reporting continu » comme moyen de reconnaissance d'attaque.

Les deux côtés de la valeur sont légitimes, et tous deux s'inscrivent dans l'esprit intérieur de Human View, mais ils pointent vers des choix de conception de protocole opposés. Dans l'état rogue de Rogue Fay, le « reporting actif » peut également protéger le Human Prime ou trahir le Human Prime.

### Voies médianes possibles

Les solutions possibles à l'avenir incluent mais ne sont pas limitées aux lignes de pensée suivantes. Le blueprint ne pré-sélectionne aucune d'entre elles.

**Traitement différencié selon la cause Rogue** — Human Prime a activement révoqué → cacher la localisation ; connexion perdue / timeout → révéler la localisation ; alerte d'intrusion → révéler la localisation. Utiliser « pourquoi est-on entré en Rogue » comme critère pour reporter ou non.

**Choisir explicitement via préautorisation** — au moment où la Faying Action est initiée, faire que le Human Prime déclare explicitement « si je perds ensuite la connexion, ce terminal est-il autorisé à continuer à reporter la localisation ? »

**Reporting hiérarchisé** — ne pas reporter de localisation précise, mais reporter des signaux minimaux qui n'exposent pas d'information spatiale, tels que « je suis toujours en Rogue, la santé est normale ».

Aucune de ces trois lignes de pensée n'est adoptée comme conclusion dans cette période. Elles appartiennent à des sujets qui ont besoin d'une discussion complète durant l'évolution du Faying Protocol dans les Phases 2 à 5, et devraient absorber les contributions des parties de la vie privée, de la sécurité et de la régulation.

### Relation entre ce sujet et le Chapitre 13

B4 est seulement **à discuter**, non **à exécuter**. Avant que le document de spécification du protocole ne fasse atterrir un choix final pour B4, toutes les autres règles données par le Chapitre 13 — B1–B3 autorisés, l'ensemble complet des règles A1–A4, C1–C3, D1–D4 — restent pleinement en vigueur. La position factuelle de B4 dans cette période est « le niveau du protocole ne mandate ni n'interdit l'implémentation », laissant la décision aux implémenteurs spécifiques et aux spécifications futures.

## Fin du blueprint

À ce stade, vous devriez être en mesure de répondre par vous-même aux trois questions suivantes sur le Faying Protocol :

- **Qu'est-ce ?** Un contrat qui exprime explicitement, entre Human Prime et Fay, « comment le contrôle et la responsabilité sont remis ».
- **Que porte-t-il aujourd'hui ?** La ligne éthique inférieure des Chapitres 11 à 13 + la forme contractuelle minimale de la Phase 1.
- **Que ne porte-t-il pas encore ?** Tous les sujets prospectifs honnêtement énumérés dans ce chapitre.

Un blueprint qui pense avoir répondu à toutes les questions est le plus susceptible d'abandonner des choses qui ne devraient pas être abandonnées lorsque de nouveaux scénarios apparaissent. Un blueprint qui liste honnêtement les questions ouvertes est, au contraire, plus à même de maintenir la ligne inférieure non compromise à travers les extensions futures.
