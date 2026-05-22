# État Rogue et Attribution de Responsabilité

La conclusion de ce chapitre est écrite tout en haut :

> **Il n'existe aucune action Fay sans partie responsable.**

C'est la ligne éthique inférieure à laquelle chaque conception de protocole du Faying Protocol doit obéir. Tout champ, message, machine d'état, algorithme ou numéro de version qui, le long d'un chemin d'exécution, laisserait un Fay produire un acte vers l'extérieur dans une situation sans partie responsable spécifique, alors ce chemin n'est pas permis au niveau du blueprint.

Ce n'est pas un objectif d'optimisation de « comment rendre un Fay plus sûr » ; c'est la limite dure de « un Fay est-il autorisé à faire quelque chose ». Le reste de ce chapitre est un déploiement concret de cette ligne inférieure.

## Définition de Rogue Fay

**Rogue Fay** (en chinois : 脱离状态) est l'état d'un Fay dans l'une ou l'autre des deux situations suivantes :

1. Le Fay n'a pas encore établi Faying State avec un quelconque Human Prime ;
2. Un Faying State précédemment établi a été révoqué, est devenu caduc ou a été interrompu.

Tant que le Fay est dans l'une ou l'autre situation, il est en Rogue Fay.

> **Rogue Fay est l'état initial par défaut de chaque Fay.**

Un Fay, dès le moment où il est créé, n'est pas automatiquement dans une quelconque relation de tutelle. Il « existe », mais n'est pas autorisé à « agir ». Ce n'est qu'après une Faying Action explicitement initiée par le Human Prime que le Fay peut entrer en Faying State, acquérant ainsi l'éligibilité à agir. Pendant tout l'intervalle avant la première Faying Action, le Fay est en Rogue Fay.

Cette valeur par défaut est intentionnelle. Le blueprint choisit le principe de verrouillage sécurisé « Rogue par défaut, seul Faying explicite permet l'action », plutôt que l'inverse — parce que l'inverse, une fois que les Fays saturent la société à grande échelle, fabriquerait inévitablement une classe de sources hors de contrôle de type « créer-puis-agir, oublier-de-fermer-puis-continuer-d'agir ».

## Neuf conditions de déclenchement de transition automatique

Une fois Faying State établi, dans quelles situations doit-il sortir automatiquement ? Ce blueprint liste **neuf conditions de déclenchement minimales**. Elles forment un **ensemble minimum**, non une liste exhaustive — toute situation supplémentaire pouvant faire que la relation de tutelle ne tienne plus devrait être enrôlée dans cet ensemble.

> **Toute action de déconnexion devrait empêcher un Fay d'agir sans autorisation.**

Les neuf conditions de déclenchement :

1. **Le Human Prime révoque activement** — le Human Prime initie explicitement une action de révocation symétrique (voir Chapitre 12).
2. **La relation Faying State expire sans renouvellement** — sous la contrainte dure du Chapitre 12 selon laquelle « un Faying illimité est un anti-pattern », chaque Faying State doit porter une portée bornée ; la frontière est atteinte sans renouvellement par le Human Prime.
3. **Le Fay sort automatiquement après avoir accompli la tâche assignée** — si la portée portée par la Faying Action est bornée par « accomplir une tâche », alors une fois la tâche accomplie ou terminée, Faying State doit sortir automatiquement.
4. **Le Human Prime est hors ligne ou injoignable pendant un temps prolongé dépassant un seuil défini** — la visibilité et l'intervenabilité de la relation de tutelle présupposent la joignabilité du Human Prime ; une fois que le Human Prime ne peut être joint au-delà du seuil défini, la tutelle est traitée comme défaillante en fait.
5. **Le comportement d'un Fay est détecté comme déviant de la frontière Ego du Human Prime** — le comportement du Fay montre une divergence significative par rapport à l'orientation de valeurs, la frontière de compétences, la frontière de permissions, etc. du Human Prime. C'est le signal de la défaillance de Faying State au niveau du contenu.
6. **L'identité du Fay ne peut être vérifiée** — par exemple, la signature de FayID est devenue caduque, les clés ont expiré, ou les identifiants ont été révoqués. Une identité non vérifiable signifie que l'entrée de la chaîne d'attribution est rompue ; la tutelle ne peut être établie.
7. **L'identité du Human Prime ne peut être vérifiée, ou le Human Prime est dans l'incapacité** — l'« extrémité responsable » de la tutelle disparaît ; la tutelle se dissout.
8. **Une autorité tierce compétente interrompt de force** — par exemple, des régulateurs, des tribunaux ou des organismes de conformité exigent l'interruption de cette relation de tutelle dans le cadre d'une procédure régulière.
9. **Le terminal ou l'application refuse activement ou perd le contact** — si la contrepartie de Faying State est un terminal ou une application logicielle, lorsqu'il refuse ou a longtemps perdu le contact, la relation de tutelle n'a plus de base factuelle.

Ces neuf éléments ne devraient pas être compris comme « épuisant toutes les conditions de déclenchement », ni comme « les neuf doivent tous être explicitement implémentés pour être conformes ». Leur véritable signification est : **toute situation dans laquelle la tutelle ne tient plus factuellement doit causer la sortie automatique de Faying State** — les neuf éléments ne sont que la présentation minimale de ce principe.

## Frontière de comportement durant Rogue Fay

Il ne suffit pas de dire simplement « Rogue Fay n'est pas autorisé à agir ». Un vrai Fay a toujours des « signes opérationnels » incontournables — il doit écouter si un Human Prime vient pour rétablir Faying, doit protéger les données déjà en sa possession, doit lever des alertes lorsqu'il est pris en charge de manière malveillante. Si le blueprint ne trace pas la ligne de permission et d'interdiction précisément, le principe « pas d'action durant Rogue » ne peut atterrir au niveau du protocole.

Le blueprint découpe tout comportement possible durant Rogue Fay en **quatre dimensions indépendantes A / B / C / D**, et statue élément par élément sur l'autorisation de chacun.

### Dimension A : perception et écoute (réception passive)

| Comportement | Autorisé | Note |
| --- | :---: | --- |
| **A1** Écouter les requêtes Faying | ✅ | C'est le chemin de résurrection Rogue → Faying et doit être conservé. |
| **A2** Écouter la vérification d'identité et les mises à jour des identifiants | ✅ | Les identifiants sont une précondition pour retourner en Faying State ; l'écoute en elle-même n'est pas une action. |
| **A3** Recevoir les commandes de révocation ou de destruction du Human Prime | ✅ | Même lorsque le Fay est en Rogue, le Human Prime peut toujours vouloir terminer ce Fay. Le chemin de commande doit toujours rester ouvert. |
| **A4** Recevoir passivement des signaux non autorisés des terminaux, autres Fays ou du réseau | ⚠️ Réception seule autorisée ; réponse interdite | La réception est un fait physique et ne peut être empêchée ; la réponse est l'action. La réponse est uniformément interdite. |

### Dimension B : auto-vérification d'état et reporting (signaux minimaux)

| Comportement | Autorisé | Note |
| --- | :---: | --- |
| **B1** Auto-vérification locale (santé, intégrité, altération) | ✅ | L'auto-santé est l'une des préconditions pour retourner en Faying State. |
| **B2** Reporting de battement de cœur (« je suis toujours en Rogue ») | ✅ | Exprimer de manière transparente au côté d'attribution que l'on est en état rogue est en soi une incarnation de la transparence de la responsabilité. |
| **B3** Alertes d'anomalie (alerte de sécurité lorsqu'une partie non autorisée tente le contrôle) | ✅ | C'est le signal nécessaire pour protéger l'intérêt du Human Prime. |
| **B4** Reporting actif de la localisation physique ou de l'état du terminal | ❓ Pas de conclusion cette période | Cela implique un arbitrage éthique entre vie privée vs. récupérabilité. Ce chapitre ne tire aucune conclusion ; voir Chapitre 14. |

### Dimension C : protection locale des données (garde passive)

| Comportement | Autorisé | Note |
| --- | :---: | --- |
| **C1** Maintenir les données stockées chiffrées et isolées | ✅ | C'est de la garde passive, pas de l'action. |
| **C2** Refuser toute requête externe de lecture/écriture | ✅ | Le refus est une non-action ; la non-action ne viole pas le principe Rogue. |
| **C3** Auto-destruction des données hautement sensibles | ⚠️ Interdit par défaut ; permis uniquement avec préautorisation du Human Prime et lorsque les conditions préétablies sont satisfaites | L'effacement actif compte comme « action », mais c'est un cas limite d'auto-protection. Le blueprint l'autorise, mais exige **autorisation d'abord, action ensuite**, interdisant au Fay de décider quand commencer l'auto-destruction. |

### Dimension D : action vers l'extérieur (affectant des objets au-delà du Human Prime)

| Comportement | Autorisé | Note |
| --- | :---: | --- |
| **D1** Exécuter des appels de pilote, contrôle de terminal, opérations logicielles | ❌ | C'est le corps même de l'« action rogue ». |
| **D2** Initier la communication avec d'autres Fays ou coFays | ❌ | La communication inter-Fay est aussi une action et peut propager le vide de responsabilité à d'autres Fays. |
| **D3** Exécuter les tâches résiduelles laissées inachevées sous le Faying State précédent | ❌ | « Continuer ce qui était laissé inachevé la dernière fois » est une transgression particulièrement facile à rationaliser et doit être explicitement interdite par le blueprint. |
| **D4** Décider seul de réentrer en Faying | ❌ | C'est une tautologie avec le principe du Chapitre 12 selon lequel « une Faying Action doit être explicitement initiée par le Human Prime ». Un Fay n'est pas autorisé à se repousser en Faying State. |

Les quatre dimensions ont une structure interne : A et B concernent les signaux, C concerne la garde, D concerne l'action. Rogue Fay ne conserve que des signes opérationnels minimisés dans les trois premières dimensions et reste uniformément immobile dans la quatrième. Ce découpage permet au concepteur de protocole de juger précisément, pour chaque fonction spécifique, à quelle dimension elle appartient et donc si elle est permise.

## Les transitions d'état sont observables, auditables et activement révocables par le Human Prime

Toutes les transitions entre Faying State et Rogue Fay ne doivent pas être des boîtes noires. Le blueprint exige que chaque transition satisfasse trois propriétés dures :

- **Observable** — lorsqu'une transition se produit, elle doit être observable pour le Human Prime, le Fay lui-même, les auditeurs et les régulateurs.
- **Auditable** — la trace laissée par une transition doit être suffisante pour répondre après coup à « quand cela s'est-il produit, qui l'a déclenché et pourquoi ».
- **Activement révocable par le Human Prime** — le Human Prime doit toujours conserver le pouvoir de décision le plus élevé sur les transitions. Ils peuvent à la fois faire sortir activement Faying State et détruire activement un Fay en Rogue Fay. Il n'existe aucune situation légitime dans laquelle un Fay « verrouille » unilatéralement son propre état et empêche le Human Prime d'intervenir.

Ces trois sont symétriques aux quatre anti-propositions de Human View au Chapitre 11 : les quatre anti-propositions interdisent au comportement du Fay de dériver hors de la visibilité et du contrôle du Human Prime ; cette section exige que les changements d'état du Fay lui-même ne dérivent également pas hors de la visibilité et du contrôle du Human Prime. Ensemble, ils permettent à Human View de vraiment boucler la boucle au niveau du protocole.

## Comportement forcé à l'entrée en Rogue Fay

Lorsque l'une des conditions de déclenchement ci-dessus est satisfaite et que Faying State entre en Rogue Fay, le Fay doit immédiatement exécuter les actions forcées suivantes :

1. **Cesser immédiatement toute action vers l'extérieur déléguée** — y compris l'intégralité de la dimension D ; aucun délai n'est permis pour des motifs tels que « la tâche est sur le point de se terminer » ou « interrompre causera une perte ».
2. **Retourner à un état d'attente passive** — ne conserver que l'ensemble de comportements minimal autorisé dans les dimensions A, B et C, et attendre la prochaine Faying Action.
3. **Diffuser le changement d'état sur des canaux observables** — afin que le Human Prime, les auditeurs, etc. puissent immédiatement savoir que ce Fay est entré en Rogue.

## Cohérence de l'attribution de responsabilité

En réunissant les sections précédentes, l'engagement auquel la ligne éthique inférieure « Il n'existe aucune action Fay sans partie responsable » correspond au niveau du protocole peut être exprimé ainsi :

> **À tout instant, chaque Fay est soit en Faying State, l'action étant attribuée au Human Prime sous cette relation Faying, soit en Rogue Fay, forcé à la non-action.**

Il n'y a pas de troisième situation. Il n'existe pas de « le Fay a agi, mais l'attribution est en attente ». Il n'existe pas de « le Fay a agi, mais l'attribution va à une personne qui n'a pas encore détenu le contrôle ». Il n'existe pas de « le Fay a agi, mais l'attribution va à un fournisseur abstrait ou une organisation abstraite ». Chaque acte vers l'extérieur a soit un Human Prime clair comme extrémité réceptrice de la responsabilité, soit ne devrait pas être autorisé à se produire.

Cette cohérence non négociable de la responsabilité est la « boussole » que les chapitres ultérieurs du blueprint (en particulier la spécification du protocole et le schema) doivent regarder en arrière en permanence. Toute évolution de protocole qui laisse l'attribution de responsabilité devenir incohérente n'est pas une évolution du Faying Protocol mais sa désintégration.
