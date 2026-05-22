# Phase 3 : Prise en Charge Dérivée des Applications Logicielles par iFay

La Phase 3 tourne la direction d'extension du matériel terminal vers les applications logicielles — applications locales, services cloud et scénarios In-APP embarqués.

Il y a une différence clé entre les applications logicielles et les terminaux matériels : l'état d'un terminal matériel est relativement concentré — un drone ou un robot est un objet unique sous tutelle — tandis que la frontière d'une application logicielle est souvent processuelle, modulaire et inter-réseau. Un client e-commerce pris en charge par un iFay peut collaborer à travers plusieurs domaines, plusieurs API et plusieurs services tiers à la fois. La difficulté de la Phase 3 n'est pas dans « la prise en charge » mais dans le fait que la frontière de la prise en charge soit décrite clairement.

## Structure de dérivation homologue à la Phase 2

La Phase 3 est structurellement symétrique à la Phase 2 et n'introduit pas non plus « Human Prime ↔ application logicielle » comme relation directe :

> **L'application logicielle entre en Faying State via l'iFay correspondant du Human Prime.**

L'extrémité responsable est toujours le Human Prime. L'iFay prend en charge dérivativement l'application logicielle via Faying State ; le mécanisme est homologue à celui de la prise en charge d'un terminal en Phase 2. L'application logicielle elle-même ne tient pas seule en Faying State.

## Trois différences clés

La Phase 3 ajoute trois complexités supplémentaires qui nécessitent un traitement spécial par-dessus la structure de la Phase 2.

**Granularité de prise en charge plus fine**. Un iFay peut ne prendre en charge qu'une partie des fonctions du logiciel — par exemple, autorisé à passer des commandes au nom de quelqu'un, mais pas à modifier la politique de sécurité du compte. La Phase 3 doit donc exprimer une « portée de prise en charge » à granularité plus fine au niveau du protocole, homologue au principe du Chapitre 12 selon lequel « une Faying Action doit être de portée bornée ».

**Collaboration trans-frontières plus dense**. Le logiciel pris en charge peut invoquer en interne plusieurs services externes, API tierces et fonctions cloud distantes. La Phase 3 doit garantir que tout appel initié via le logiciel pris en charge par l'iFay voit toujours sa responsabilité attribuée au Human Prime original ; la responsabilité ne peut s'esquiver silencieusement à travers la chaîne d'appels inter-services. Cette exigence répond directement au point douloureux du monde réel esquissé au Chapitre 1 — « personne ne peut dire clairement quelles parties traitent les données le long de la chaîne d'appels ».

**Effets de bord plus furtifs**. Comparés aux actions physiques, les effets de bord logiciels (écritures de données, changements d'abonnement, liaisons de comptes tiers) sont plus difficiles à percevoir intuitivement par un Human Prime. La Phase 3 doit faire atterrir l'exigence de « joignabilité de l'information » de Human View du Chapitre 11 plus explicitement — les effets de bord doivent être divulgués d'une manière que le Human Prime peut connaître à un coût raisonnable, et non enfouis profondément dans la chaîne d'appels.

## Relation avec le périmètre de la période actuelle

**La Phase 3 est hors du périmètre de la conception actuelle du Faying Protocol.** Ce chapitre esquisse l'existence de la Phase 3 pour expliquer la direction de l'évolution du Faying Protocol, et non pour s'engager sur sa livraison dans cette période. La forme concrète du protocole de la Phase 3 sera portée par une spécification séparée ultérieure.

Après la Phase 3, le Faying Protocol couvre la relation du Fay avec les extrémités d'exécution matérielle et logicielle, mais la discussion tourne toujours autour de « un Human Prime + un iFay ». La prochaine étape, la Phase 4, étend la perspective aux organisations : lorsqu'il y a plus d'un Fay et que l'extrémité responsable n'est plus une seule personne physique, comment la relation Faying maintient-elle toujours une attribution cohérente.

![Concept Phase 3](../../zh-CN/blueprint/illustration/phase3-concept.png)

![Architecture Phase 3](../../zh-CN/blueprint/illustration/phase3-architecture.png)
