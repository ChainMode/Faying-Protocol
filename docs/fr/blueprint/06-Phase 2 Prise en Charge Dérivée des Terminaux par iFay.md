# Phase 2 : Prise en Charge Dérivée des Terminaux par iFay

Après que la Phase 1 a stabilisé la forme contractuelle minimale de « Human Prime ↔ iFay », la Phase 2 tourne son attention vers la relation entre iFay et les appareils terminaux.

Le terminal s'entend ici dans un sens généralisé — un drone, un robot, un véhicule intelligent, une passerelle IoT, un ordinateur personnel, un téléphone appartiennent tous à cette classe. Leur caractéristique commune : du matériel qui peut être piloté, des actions physiques qui peuvent être initiées et des conséquences physiques qui peuvent en résulter.

La clé de la Phase 2 n'est pas de laisser un iFay contrôler plus de choses ; c'est d'enrôler clairement chaque terminal qu'il prend en charge dans la chaîne de responsabilité Faying.

## Dérivé, non direct

La Phase 2 n'introduit pas « Human Prime ↔ terminal » comme relation directe. Sa manière d'étendre est indirecte :

> **Le terminal entre en Faying State via l'iFay correspondant du Human Prime.**

L'extrémité responsable est toujours le Human Prime ; cela ne change pas. L'iFay est toujours l'entité qui porte Faying State, mais il porte désormais un devoir supplémentaire — agir comme tuteur au nom des terminaux qu'il prend en charge. Le terminal ne tient pas seul en Faying State ; son « être à l'état contrôlé » est dérivé du Faying State de l'iFay auquel il appartient actuellement.

Pour poursuivre l'analogie introduite au Chapitre 12 — Jack remettant le volant à un AI driver — la Phase 2 se soucie de : lorsque cet AI driver conduit ensuite la voiture, tourne, freine et change de file, comment chaque « état de contrôle » du volant, de l'accélérateur et des clignotants reste cohérent à tout moment avec le fait que Jack soit toujours sous tutelle.

## Trois sujets centraux

**Visibilité de la prise en charge** : lorsqu'un iFay prend en charge un terminal, cela doit être observable en temps réel par le Human Prime et par l'extérieur — quel terminal, dans quelle fenêtre temporelle, pris en charge par quel iFay. C'est l'extension de Human View au niveau du terminal.

**Sortie en chaîne** : lorsqu'un iFay entre en Rogue Fay, tous les terminaux qu'il a pris en charge doivent simultanément perdre l'effet dérivé de Faying. Un terminal ne doit pas être autorisé à continuer à exécuter des actions physiques précédemment inachevées alors que l'iFay a déjà quitté la tutelle — cela correspond exactement à l'interdiction sous D3 au Chapitre 13.

**Irréversibilité de l'action physique** : les actions dans le monde physique sont fortement irréversibles. Un drone a déjà livré, un bras robotisé a déjà bougé, un véhicule a déjà tourné — l'audit après coup ne peut l'annuler. La Phase 2 doit prendre « plutôt ne pas agir que mal agir » comme biais par défaut au niveau du protocole, et ne pas le rapiécer par un audit ultérieur.

Le troisième élément est particulièrement critique. Au moment où la moindre incertitude sur Faying State surgit, le terminal se met par défaut en « attente passive » plutôt qu'en « exécution optimiste ».

## Relation avec le périmètre de la période actuelle

**La Phase 2 est hors du périmètre de la conception actuelle du Faying Protocol.** Le Faying Protocol de cette période ne couvre que la Phase 1. La forme concrète du protocole par laquelle « un iFay prend en charge dérivativement un terminal via Faying » en Phase 2 sera définie dans une spécification séparée après la stabilisation de la Phase 1. Ce chapitre esquisse l'existence et la direction de la Phase 2 afin que le Chemin de Mission ait une image complète de l'évolution.

La Phase 2 est le premier pas où Faying sort « entre logiciels » vers la frontière « logiciel-physique ». À partir d'ici, les relations Faying ne concernent plus seulement les bits mais commencent à concerner les conséquences physiques poussées par les bits. Ce fait est la « gravité » que les Phases 3 à 5 doivent regarder en arrière de temps en temps.

![Concept Phase 2](../../zh-CN/blueprint/illustration/phase2-concept.png)

![Architecture Phase 2](../../zh-CN/blueprint/illustration/phase2-architecture.png)
