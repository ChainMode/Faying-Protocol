# Sémantique Duale de Faying

À ce stade, le mot « Faying » est apparu de nombreuses fois : comme nom du contrat au Chapitre 2, distinguant iFay d'Agent au Chapitre 3, portant l'exigence de valeur de Human View au Chapitre 11. Mais ce à quoi Faying se réfère réellement a été délibérément différé jusqu'ici. La raison est qu'il ne peut être décrit d'une seule face.

Faying porte deux sémantiques à la fois.

**Sémantique d'état** — l'état de connexion d'un Fay sous la tutelle d'un Human Prime, appelé **Faying State**.
**Sémantique d'action** — l'acte de « remise du contrôle » par lequel un Fay entre en Faying State depuis l'état rogue, appelé **Faying Action**.

Les deux sémantiques sont inséparables : sans une Faying Action, Faying State ne sera jamais établi ; sans Faying State, une Faying Action n'est qu'une opération vide. C'est le **principe de Sémantique Duale** de Faying.

Toute tentative de simplifier Faying à une seule face — le prendre simplement comme « un état de connexion », ou simplement comme « une action de basculement » — efface silencieusement l'attribution de responsabilité au niveau du protocole.

## Faying State : l'état de connexion sous tutelle

Faying State est l'état de connexion d'un Fay sous la tutelle d'un Human Prime spécifique. Un Fay entrant dans cet état possède trois propriétés nécessaires.

**L'attribution de l'action est unique** — tous les actes vers l'extérieur du Fay dans cet état sont attribués à ce Human Prime. Que l'acte soit décidé de manière autonome par le Fay, explicitement commandé par le Human Prime, ou déclenché par l'environnement externe, l'extrémité responsable ne saute pas.

**Visibilité continue** — durant cet état, le Human Prime détient Human View sur l'activité du Fay, et peut confirmer à tout moment si la tutelle est toujours en effet.

**Le chemin d'intervention est toujours ouvert** — durant cet état, les commandes de révocation, pause, ralentissement ou destruction du Human Prime sur le Fay ont la priorité la plus élevée. Le Fay ne peut écraser ces commandes pour aucune « raison commerciale ».

Faying State n'est pas un résultat statique ; c'est un engagement en ligne continu. Il a besoin d'être reconfirmé à chaque instant microscopique, et non détenu à jamais une fois établi. Une fois que l'un quelconque des trois ci-dessus ne tient plus, Faying State devrait entrer dans le flux de sortie défini au Chapitre 13.

> **Une conclusion inverse importante** : dans l'état hors de Faying State (c'est-à-dire Rogue Fay), chaque acte vers l'extérieur d'un Fay n'a personne pour recevoir la responsabilité. Par conséquent, le seul choix de conception acceptable que le Faying Protocol peut faire au niveau du protocole est : **interdire au Fay d'agir durant Rogue Fay**, plutôt que de « le laisser agir et rapiécer l'attribution après ». Ce principe sera strictement atterri au Chapitre 13.

## Faying Action : la remise du contrôle

Une Faying Action est un acte spécifique, observable, auditable de « remise du contrôle ».

L'analogie la plus appropriée est cette scène quotidienne :

> Jack remet le volant d'une voiture à un AI driver. À cet instant, Jack ne presse pas simplement un bouton « pilote automatique » — il est, d'une manière clairement perceptible à l'extérieur, **en train de remettre le contrôle**. Avant cela, le volant appartenait à Jack ; après cela, le volant appartient à cet AI driver ; pendant ce temps, toutes les conséquences découlant du volant retombent toujours sur Jack, qui détient le permis de conduire.

Une Faying Action est l'équivalent « remettre le volant » dans le monde numérique. Elle déplace un Fay, clairement, témoignablement et traçablement, depuis l'état rogue de « existe mais ne peut agir » vers le Faying State de « agit au nom du Human Prime ».

Cela conduit à plusieurs propriétés non négociables d'une Faying Action.

**Doit être explicitement initiée par le Human Prime** — une Faying Action ne permet pas à un Fay de décider seul de commencer. Un Fay ne peut entrer en Faying State de manière autonome simplement parce que « la dernière fois ça a commencé comme ça », « j'infère que le Human Prime souhaiterait que je commence maintenant », ou « j'ai déjà été autorisé pour des actes similaires auparavant ». Chaque entrée doit être explicitement initiée par le Human Prime.

**Doit être témoignable** — une Faying Action doit laisser une marque observable à l'extérieur (y compris auditeurs, régulateurs, le Fay lui-même, d'autres Fays et le Human Prime). Une Faying Action qui n'a pas été témoignée équivaut à une qui ne s'est pas produite.

**Doit être de portée bornée** — une Faying Action ne devrait pas être une « délégation à pleins pouvoirs » perpétuelle. Le blueprint favorise fortement une Faying Action portant une portée explicite (par exemple, une fenêtre temporelle, une portée de tâche, une portée de terminal), s'éteignant automatiquement à l'atteinte de la frontière. Un Faying illimité est un anti-pattern à éviter.

**Doit être symétriquement révocable** — chaque Faying Action doit avoir un chemin de révocation correspondant et symétrique. Établir Faying State et sortir de Faying State doivent être **deux chemins également joignables**, et non une conception asymétrique de « facile à ouvrir, difficile à fermer ».

## Les deux faces ensemble sont Faying

En réunissant les faces d'état et d'action, le sens complet de Faying peut être exprimé dans ce paragraphe :

> **Faying est un acte de « remise du contrôle » (Faying Action) explicitement initié par le Human Prime, témoignable et symétriquement révocable, qui pousse le Fay dans un état de connexion en ligne continu sous tutelle (Faying State) ; au sein de cet état, le Fay peut agir au nom du Human Prime, et les conséquences sont toutes assumées par ce Human Prime ; en dehors de cet état, le Fay n'est pas autorisé à agir.**

Le même paragraphe rend trois engagements le long de la dimension du temps. **Passé** : Faying State est toujours entré via une Faying Action spécifique ; il n'existe aucun Fay qui « est juste naturellement en Faying ». **Présent** : la validité de Faying State est continuellement calibrée à chaque instant par Human View, et non détenue à jamais une fois établie. **Futur** : Faying State sortira finalement par une révocation symétrique ou une caducité automatique, ramenant le Fay à l'état rogue défini au Chapitre 13.

## Contraintes dures sur la conception du protocole

Ce chapitre, en tant que chapitre de valeurs, ne spécifie pas de champs ou de messages, mais il impose plusieurs contraintes dures non négociables sur la conception concrète du Faying Protocol :

- le niveau du protocole doit fournir une expression de premier rang pour **les deux**, État et Action ; il ne peut exprimer une seule face ;
- le niveau du protocole interdit tout chemin légitime « par lequel un Fay initie une Faying Action sur lui-même » ;
- le niveau du protocole doit fournir pour chaque Faying Action une marque témoignable et un chemin symétriquement révocable ;
- le niveau du protocole interdit le « Faying illimité » comme forme par défaut ; il doit imposer qu'une Faying Action porte une portée bornée au niveau du protocole ;
- le niveau du protocole doit garantir : lorsqu'une condition quelconque sous laquelle Faying State ne tient plus est déclenchée, le Fay transite automatiquement en état rogue, et non en un « Faying dégradé ».

Comment une relation de tutelle est établie, soutenue et terminée a maintenant été pleinement défini au niveau des valeurs. Le chapitre suivant retourne la perspective : lorsque Faying State ne tient pas, que peut, et que ne peut pas le Fay faire ? C'est le chapitre le plus strict de ce blueprint, celui dans lequel aucune concession n'est permise.
