<!-- Mis à jour : 2026-05-25 -->

# Vision Humaine et Faying : stratégie produit et approche technique pour cohabiter avec iFay

Si, à l'avenir, l'IA fait réellement les choses à votre place, opère les terminaux à votre place, interagit avec le monde à votre place, alors « comment les humains et l'IA cohabitent » n'est plus une discussion philosophique mais un **protocole de sécurité qui doit être rendu concret**.
Je ne cesse de le dire : faire courir l'IA plus vite est facile ; la faire « agir de manière responsable au sein de la société » est la partie difficile.

Alors disons-le très simplement :
**Chaque action Fay doit se produire dans le rayon que son Human Prime peut « voir ».**
« Voir » ici n'est pas fixer un écran, ni pointer une caméra sur un robot — c'est un engagement structurel : vous n'avez pas à regarder en permanence, mais à l'instant où vous voulez regarder, vous pouvez confirmer si elle est toujours sous tutelle ; à l'instant où vous voulez l'arrêter, vous pouvez l'arrêter.
Dans le protocole, nous appelons cette valeur **Human View**.
(Pour un traitement plus détaillé de cette idée, lire directement « Human View » : https://ifay.ai/fr/docs/Faying-Protocol/blueprint/11-Vision%20Humaine )

Autour de la « gradation de tutelle », de « Human View », de la « connexion forte / fusion forte de Faying » et des scénarios futurs de prise en charge des terminaux, je veux parler de ce que nous construisons davantage comme une « manière de cohabiter » que comme un amas de jargon.
La position que je veux exprimer est la suivante : **Faying State est la manière par défaut sûre, alignée et extensible pour les humains et iFay de cohabiter. Une entité s'exécutant automatiquement en dehors de Faying devrait être placée par défaut dans la zone non sûre — tout comme HTTP sur Internet.**

---

## Human View : pas « être vu », mais « pouvoir être vu »

Nous utilisons Human View pour saisir ce fait : un humain ne peut surveiller tous ses Fays 24h/24, 7j/7. La vue physique ne tient pas ; nous devons introduire une sorte de « confirmabilité structurelle ».
Ce qui lui importe, ce n'est pas « est-ce que je regarde en ce moment », mais « puis-je regarder quand je le veux ». C'est un objectif d'ingénierie complètement différent.

Je veux tracer une ligne claire entre deux concepts : **Human View** et **Harness** ne sont pas la même chose.
Harness résout « le comportement de l'iFay est-il bien formé » — le flux est-il conforme, l'action reste-t-elle dans les bornes, la sortie respecte-t-elle les contraintes de sécurité et d'éthique.
Human View résout « dans quelle mesure le Human Prime peut effectivement garder l'iFay sous contrôle » — puis-je confirmer à tout moment, puis-je intervenir à tout moment, puis-je terminer à tout moment.
Plus strictement : chaque position le long de la corde du cerf-volant devrait être appariée à un Harness correspondant. Plus la corde est lâche, plus les exigences sur Harness sont élevées ; plus la corde est tendue, plus Harness se réduit à la cohérence d'instruction au niveau souris.
La raison pour laquelle j'insiste sur Human View n'est pas d'apprendre à iFay à bien se comporter ; c'est de garantir que peu importe jusqu'où nous laissons filer la corde, vous pouvez toujours la tendre, la rembobiner et voir clairement.

Plus important encore, Human View n'est pas un champ, une API ou un bouton — c'est une contrainte de niveau constitutionnel :
**Toute conception de champ, de message ou de machine d'état qui laisse un Fay dériver hors de Human View n'est pas permise au niveau du blueprint, peu importe sa commodité en ingénierie.**
Cette phrase n'est pas de la rhétorique ; c'est une contrainte dure que nous nous imposons à nous-mêmes lorsque nous concevons à la fois le produit et le protocole.

Human View interdit également explicitement quatre situations (les quatre anti-propositions) :

- **Non autorisé** (Unauthorized) — agir sans autorisation vérifiable.
- **Non intentionnel** (Unintended) — l'autorisation existe mais l'action spécifique présente n'a pas été l'objet d'une expression d'intention par le Human Prime ; l'action diverge de l'intention présente du Human Prime.
- **Non conscient** (Unaware) — même lorsque l'autorisation et l'expression d'intention tiennent toutes deux, le Human Prime ne peut toujours pas, à un coût raisonnable, prendre connaissance de ce que fait le Fay.
- **Hors de contrôle** (Out-of-Control) — le Human Prime est déjà conscient mais ne peut intervenir en temps réel, ne peut révoquer, ne peut ralentir, ne peut détruire.

Vous remarquerez que ces quatre sont vraiment la ligne morale inférieure de la cohabitation humain-machine, mais ici elles sont écrites comme des exigences de protocole exécutables : autorisation et expression d'intention sont l'entrée et le processus, la conscience est le chemin de rétroaction, et le contrôle est la dernière barrière. Laissez tomber l'une et la « tutelle » ne conserve que son nom.

---

## Ce que « sous tutelle » signifie réellement : pas un interrupteur à deux positions, plutôt comme la corde du cerf-volant

Beaucoup de gens, en entendant « tutelle », adoptent par défaut une pensée binaire : soit je vous tiens en main, soit je ne le fais pas.
Mais après avoir travaillé sur iFay un certain temps, nous avons constaté que la pensée d'interrupteur tire les gens vers deux extrêmes — soit épuisés par des confirmations à grain fin, soit lâchant le pouvoir si loin qu'ils ne peuvent rien voir ni rien arrêter.

Je préfère expliquer la gradation de tutelle à travers « la corde du cerf-volant » : plus vous rembobinez la corde, plus votre contrôle est fort ; plus vous la laissez filer, plus iFay a d'autonomie.
Le point n'est pas « devrais-je laisser filer la corde » ; le point est **la corde est toujours dans votre main** — vous pouvez toujours la rembobiner, la remplacer ou la couper.

Nous divisons la tension de cette corde en environ cinq niveaux (différentes tâches appellent différents réglages) :

1) **Équivalence stricte (équivalent souris)**
   Vous cliquez une fois, elle bouge une fois ; iFay ne fait rien de sa propre initiative.
   Pour : actions à risque élevé, irréversibles, difficiles à expliquer (virements, signatures, suppression de bases de données, licencier quelqu'un).

2) **Sous supervision (copilote)**
   iFay comprend et planifie, mais les étapes clés doivent solliciter votre consentement.
   Pour : flux de risque moyen, plus longs, qui peuvent être confirmés par étapes (réservation, modification de réservation, soumission de formulaires).

3) **Sous expression d'intention (une extension de votre intention)**
   Vous lui donnez l'idée approximative ; elle accomplit la tâche dans votre style et ramène les reçus et les enregistrements traçables dans votre vue.
   Pour : tâches à faible risque mais à haute fréquence (organiser les e-mails, planifier, construire des listes de courses, générer des brouillons).

4) **Sous autonomie de portée (s'exécuter seul à l'intérieur d'une portée)**
   Vous lui donnez une portée (fenêtre temporelle / budget / terminal / domaine de tâche) ; il planifie et exécute seul, mais le processus est toujours visible, interruptible, révocable.
   Pour : tâches routinières continues (inspection, surveillance, collecte d'informations, vols de drone routiniers).

5) **Autonomie bornée (symbiose à long terme)**
   Vous lui faites confiance pour se piloter seul à l'intérieur d'une frontière plus large, mais Human View et le chemin d'intervention restent toujours actifs.
   Pour : collaboration à long cycle (assistant à long terme, collaboration familiale, gestion de la santé).

Ces cinq niveaux semblent porter sur la quantité de pouvoir que vous déléguez, mais ce sur quoi nous insistons réellement est une seule chose :
**peu importe jusqu'où la corde est laissée filer, iFay ne peut dériver hors de Human View.**
La tutelle n'est pas « déléguer moins » ; la tutelle est « même quand vous déléguez, cela reste dans la vue ».

---

## Faying : pas « juste connecté », mais « fusion et fusible » qui tiennent sous différentes gradations

Si vous comprenez Faying comme étant simplement un « état de connexion », vous dériverez naturellement vers une direction dangereuse :
« Maintenant que nous sommes connectés, restons simplement connectés pour toujours. »

Nous proposons Faying non pour décrire « connecté ou non », mais pour définir une manière de cohabiter construite sur **connexion forte et fusion forte** :
lorsqu'un iFay travaille sous Faying, ce n'est plus un outil externe. Il commence, à des degrés divers, à fusionner avec vous — sous différentes tâches et différents niveaux de risque, il forme différentes gradations d'équivalence :
certaines gradations sont équivalent souris — vous cliquez une fois, il bouge une fois ;
certaines gradations sont copilote — il comprend et planifie, mais chaque étape a besoin de votre acquiescement ;
certaines gradations sont une extension de votre intention — vous donnez l'idée approximative, il accomplit les choses dans votre style ;
plus haut, c'est une autonomie bornée par une portée que vous êtes prêt à accorder.
Mais sous toute gradation, la « fusion » doit satisfaire Human View : confirmable à tout moment, traçable à tout moment, intervenable à tout moment.

Pour rendre cette fusion ingénierable, nous ne pouvons pas seulement parler d'état — nous devons aussi écrire la « remise du contrôle » dans le protocole. Le Faying Protocol décompose Faying en une sémantique duale :
**Faying State (sémantique d'état)** : l'état de connexion sous la tutelle du Human Prime (la relation de fusion continuellement en ligne).
**Faying Action (sémantique d'action)** : l'acte de « remise du contrôle » par lequel le Fay entre en Faying State depuis l'état rogue (la relation de fusion en train d'être établie).
(Pour un traitement plus détaillé de cette paire sémantique état + action, voir « Sémantique Duale de Faying » : https://ifay.ai/fr/docs/Faying-Protocol/blueprint/12-S%C3%A9mantique%20Duale%20de%20Faying )

La raison pour laquelle cela importe : ce n'est qu'en faisant de l'« état » et de l'« action » des éléments de premier rang que vous pouvez garantir que l'attribution de responsabilité n'est pas silencieusement effacée.

Au niveau du produit, je traite les exigences sur une Faying Action comme une « checklist que la remise du contrôle doit satisfaire » :

- **Doit être explicitement initiée par le Human Prime** : un Fay n'est pas autorisé à décider de commencer seul.
- **Doit être témoignable** : elle doit laisser une marque auditable.
- **Doit être de portée bornée** : un Faying illimité est un anti-pattern ; elle doit porter des frontières telles que fenêtre temporelle, portée de tâche, portée de terminal.
- **Doit être symétriquement révocable** : ouvrir et fermer sont également faciles ; « facile à ouvrir, difficile à fermer » est interdit.

Faying State, de même, n'est pas « connecté et terminé » — il porte trois propriétés nécessaires :

- **L'attribution de l'action est unique** : l'extrémité responsable de l'action vers l'extérieur ne saute pas.
- **Visibilité continue** : Human View peut confirmer à tout moment que la tutelle est toujours en effet.
- **Le chemin d'intervention est toujours ouvert** : révoquer / pause / ralentir / détruire portent la priorité la plus élevée.

Le point de Faying n'est pas « je vous autorise à aller courir dehors » ; c'est « je vous remets le contrôle, mais je suis toujours à l'intérieur de cette relation ».
Une fois cette relation établie, un iFay peut agir en votre nom dans des terminaux et des applications plus complexes sans vous pousser dans la zone dangereuse du « ne peut pas voir, ne peut pas arrêter, ne peut pas expliquer ».

---

## Rogue Fay : hors tutelle, aucune action vers l'extérieur permise

Nous avons choisi une stratégie plus stricte au niveau du produit : **une action Fay sans partie responsable claire — mieux vaut qu'elle ne se produise pas.**
Autrement dit : tant qu'il n'est pas dans Faying, un iFay ne peut « agir vers l'extérieur » — il ne peut opérer des terminaux à votre place, ne peut envoyer des messages à votre place, ne peut exécuter aucune action qui affecte le monde extérieur.
Ce qu'il peut faire est réduit à la garde minimale : attendre que vous initiiez une nouvelle remise du contrôle, protéger les données déjà en sa possession, lever des alertes lorsque des anomalies sont détectées, et ramener clairement « je suis actuellement en état rogue » dans votre vue.

Si vous faites réellement atterrir ce principe en ingénierie, cela paraîtra très contre-intuitif, parce qu'en logiciel nous sommes habitués à : le système s'exécute par défaut, fait quelque chose par défaut, se rétablit automatiquement par défaut.
Mais les Fays ne le peuvent pas. Parce qu'à l'instant où un Fay « fait quelque chose », il affecte des objets du monde réel.

Ainsi, le Faying Protocol définit l'état initial par défaut d'un Fay comme **Rogue Fay** :
il « existe » mais n'est pas autorisé à « agir ». Ce n'est que lorsque le Human Prime initie explicitement une Faying Action qu'il acquiert l'éligibilité à agir.
C'est un principe de verrouillage sécurisé : fermé par défaut, ouvert uniquement explicitement.

Pour empêcher l'implémentation d'ingénierie de « le faire simplement parce que c'était commode », nous avons tracé les frontières de l'état rogue très finement : il peut écouter, il peut garder, il peut alerter, mais il ne doit pas agir vers l'extérieur.
Pour l'ensemble complet des frontières et des conditions de déclenchement, lire « État Rogue et Attribution de Responsabilité » : https://ifay.ai/fr/docs/Faying-Protocol/blueprint/13-%C3%89tat%20Rogue%20et%20Attribution%20de%20Responsabilit%C3%A9

- Nous permettons « écouter et attendre » (aucun impact externe).
- Nous permettons « auto-vérification et alerte » (ramener le risque dans Human View).
- Nous permettons « garde des données » (isolement chiffré, refus de lecture/écriture non autorisée).
- Nous interdisons explicitement « action vers l'extérieur » (tout acte qui change l'état du monde extérieur).

Voici l'analogie à retenir :
**Une entité automatique sans Faying est comme un site sans HTTPS** — vous pouvez le visiter, mais le navigateur le signale en rouge, et vous savez d'instinct qu'il ne devrait pas porter de comportement sensible.
De la même manière, un Agent ou une entité s'exécutant automatiquement en dehors de Faying n'est pas nécessairement « malveillant tout de suite », mais il est structurellement non sûr : il peut tomber dans des situations « Non autorisé / Non conscient / Hors de contrôle » à tout moment, et vous n'avez aucune barrière au niveau du protocole.

---

## Construire Human View à travers le protocole : maintenir Human Prime toujours en mesure de voir et de freiner

Human View n'est pas un slogan ; nous devons la transformer en une capacité par défaut à l'intérieur du protocole et du produit : visible, traçable, intervenable.
Le Human Prime référencé ici est l'extrémité responsable telle que définie au sein du système iFay. Pour en savoir plus sur ce concept, voir « Définitions et Concepts » : https://ifay.ai/fr/docs/iFay/blueprint/02-D%C3%A9finitions%20et%20Concepts

### 1) L'état pouvant être vu : je sais toujours si vous êtes en Faying

Au niveau du produit, j'exige :
**À tout moment, le Human Prime doit pouvoir, dans une vue à panneau unique, confirmer : quels Fays sont actuellement en Faying State, quelle est la frontière de portée de chacun, et si des alertes d'anomalie sont actives.**

Ce n'est pas une fonctionnalité optionnelle ; c'est le corps de la « vue ». Sans elle, Human View n'est que paroles vides.

La forme du produit peut prendre de nombreux aspects — un widget de téléphone, un centre de notifications, un wearable, une barre d'état de bureau, une invite embarquée — mais l'exigence centrale est « toujours joignable ».

### 2) Le comportement étant traçable : je peux toujours répondre à « ce qui vient de se passer »

Le cœur de Human View n'est pas la surveillance en temps réel ; c'est la confirmation traçable.
Ainsi, les journaux doivent être « compréhensibles », pas seulement des traces réservées aux ingénieurs. Au minimum, ils doivent répondre à :

- Qui a initié cette action (commande du Human Prime / expression d'intention / déclenchement automatique) ?
- Dans quelle portée d'autorisation s'est-elle produite ?
- Quels objets spécifiques ont été affectés (terminaux / applications / comptes / données) ?
- Lorsqu'une anomalie s'est produite, est-elle automatiquement sortie de Faying ? A-t-elle déclenché une alerte ?

Ce n'est que lorsque ces trois tiennent ensemble que quelque chose est « dans la vue » : vous pouvez le voir, vous pouvez le rechercher, et vous pouvez freiner.

### 3) L'intervention étant joignable : je peux toujours vous faire arrêter, ralentir ou être révoqué

Au niveau du produit, l'intervention doit atteindre le « niveau de mémoire musculaire ».
Vous ne pouvez pas faire creuser un utilisateur dans les paramètres, parcourir les journaux, ou taper une commande à un moment critique. L'intervention doit être comme un frein : simple, directe, avec un retour clair.

Je fixe la surface d'intervention à quatre boutons :

- Pause
- Révoquer (Sortir de Faying)
- Ralentir (exiger des confirmations)
- Détruire (interrupteur d'arrêt)

Et leur priorité doit l'emporter sur toute « raison commerciale ». C'est une contrainte dure du protocole, pas une option du produit.

---

## Faire atterrir la « tension de la corde » comme règles : différentes tâches appellent différentes gradations de tutelle

Nous transformons les gradations ci-dessus en un ensemble de règles : un ensemble de règles sélectionne différents modes de barrière d'action selon le type de tâche, le niveau de risque et le type de ressource.

### 1) Classification des tâches : « réversibilité × rayon de perte × sensibilité de conformité »

- Réversibilité : révocable / remédiable / irréversible (virements, signatures, suppression de bases de données)
- Rayon de perte : n'affecte que vous-même / affecte les autres / affecte la sécurité publique (drones, véhicules)
- Sensibilité de conformité : vie privée personnelle / finance / santé / mineurs / autorité publique

Ces trois dimensions décident de la « gradation de tutelle par défaut » et décident de comment la portée d'une Faying Action devrait être réglée (fenêtre temporelle, domaine de tâche, domaine de terminal, domaine de budget).

### 2) Séparer Autorisation et Intention : « est-ce permis » vs. « cette chose particulière »

Dans les quatre anti-propositions de Human View, nous avons déjà souligné : l'autorisation résout « ceci est-il autorisé à bouger », l'expression d'intention résout « ce mouvement particulier ».
Atterrie dans le système, elles doivent être séparées en deux types d'identifiants / deux types d'enregistrements :

- Authorization Grant (long ou moyen terme) : permet à l'iFay d'utiliser une classe de capacités à l'intérieur d'une portée.
- Intent Ticket (court terme, à usage unique) : permet l'exécution de cette action spécifique.

Cela évite le désastre du « vous avez autorisé la lecture/écriture des e-mails, donc il a commodément envoyé un mail de masse à tout le monde ». L'autorisation n'est pas l'expression d'intention ; l'expression d'intention est la barrière à chaque action.

### 3) Canal Human View : faire de « pouvoir être vu » une contrainte de protocole dure

Ce n'est pas « construire une fonctionnalité de notification ». C'est plutôt comme une route forcée à travers le système :

- Chaque action vers l'extérieur doit produire un événement qui remonte ;
- Les événements doivent pouvoir atteindre l'extrémité de vue du Human Prime ;
- Si l'extrémité de vue est injoignable pendant un temps prolongé (hors ligne, refusant le contact, injoignable au-delà d'un seuil), le système doit automatiquement sortir de tutelle, retourner à l'état rogue, et arrêter l'action vers l'extérieur.

Human View requiert naturellement une « infrastructure d'observabilité » : les événements remontent, l'état peut être confirmé, les commandes peuvent interrompre. Quelle que soit la manière dont l'implémentation est superposée, la « joignabilité de la vue » doit être une condition dure.

### 4) Barrière de l'état rogue : peut garder, ne peut agir vers l'extérieur

Pour rendre « aucune action vers l'extérieur durant l'état rogue » réellement exécutable, l'ingénierie doit s'engager : durant Rogue Fay, le système ne poursuit pas « continuer la tâche », il poursuit « arrêter l'impact externe + rester récupérable + attendre une remise du contrôle légitime ».

Cela changera directement beaucoup d'habitudes d'ingénierie : des choses comme la « reprise après déconnexion », le « réessai de tâche » et la « compensation automatique » peuvent être dangereuses ici — elles laissent facilement un Fay continuer à agir vers l'extérieur alors qu'il est hors tutelle.
La logique du Faying Protocol est sans ambiguïté : **mieux vaut s'arrêter qu'agir lorsqu'il n'y a pas de partie responsable.**

---

## Fusion de terminal : faire qu'un terminal et le Human Prime « semblent ne faire qu'une seule et même personne »

Je continue d'utiliser des exemples comme drones, clients e-mail et applications de shopping — non parce qu'ils sont « cool », mais parce qu'ils rendent le sens de Faying très concret :
lorsqu'un iFay porte une cognition, une mémoire et des habitudes alignées avec vous, et continue à opérer un terminal, le terminal n'est plus un outil froid — il commence à fusionner plus étroitement avec vous, et le comportement du terminal ressemble de plus en plus à « vous l'opérant vous-même ».
Une fois cela établi, le coût qu'un humain paie pour apprendre un terminal baisse, l'accommodation du terminal pour l'humain devient le défaut, et la friction entre les humains et le monde numérique est systématiquement supprimée.

J'ai opéré une convergence très explicite dans la feuille de route : faire d'abord atterrir la relation de tutelle « Human Prime ↔ iFay » comme une boucle fermée minimale, puis laisser les terminaux et les applications entrer dans l'état contrôlé via iFay, plutôt que de laisser chaque terminal lier directement une personne.
Pour la vision évolutive plus complète, lire « Human Prime ↔ iFay » : https://ifay.ai/fr/docs/Faying-Protocol/blueprint/05-Phase%201%20Human%20Prime%20et%20iFay

Ce choix garde la chaîne de responsabilité simple : que vous contrôliez un drone, un système embarqué, un client e-mail ou une application de shopping, l'extrémité réceptrice de la responsabilité ne bouge jamais : c'est le Human Prime.

En langage produit, je le formulerais ainsi :
ce que vous possédez est un « compagnon numérique ». Il peut faire pousser de nombreux « membres » (dérivés de terminaux), mais votre vue et votre frein sont toujours là.

C'est à cela que la connexion forte et la fusion forte devraient réellement ressembler : non une automatisation incontrôlable, mais une symbiose soutenable.

---

## Un dernier mot : traiter Faying comme l'« HTTPS par défaut » de l'ère IA

- **Faying State** est la zone sûre de l'action IA : il y a une partie responsable, il y a une visibilité continue, il y a un chemin d'intervention.
- **Rogue Fay / Un-Faying** est la zone non sûre par défaut : écoute et garde minimales permises, mais action vers l'extérieur interdite.

Aux débuts d'Internet, HTTP n'était pas « malveillant » d'emblée, mais il était intrinsèquement non sûr ; plus tard, toute la société a atteint un consensus de l'industrie : le comportement sensible doit, par défaut, s'exécuter sur HTTPS.
L'ère IA atteindra le même consensus :
**Les actions IA sensibles qui produisent des conséquences dans le monde réel doivent, par défaut, se produire à l'intérieur de Faying.**

Ce n'est pas du conservatisme ; c'est le respect de la structure de la responsabilité.
Ce que nous voulons n'est pas une entité automatique plus rapide. Ce que nous voulons est une manière de symbiose qui laisse les humains garder la vue, garder le frein, et garder l'attribution.

C'est ce que je comprends de la manière de cohabiter avec iFay :
**connexion forte, fusion forte, mais jamais hors de Human View.**

---

## Pour en savoir plus sur notre réflexion
- Human View : https://ifay.ai/fr/docs/Faying-Protocol/blueprint/11-Vision%20Humaine
- Sémantique Duale de Faying (State & Action) : https://ifay.ai/fr/docs/Faying-Protocol/blueprint/12-S%C3%A9mantique%20Duale%20de%20Faying
- État Rogue et Attribution de Responsabilité (Rogue Fay) : https://ifay.ai/fr/docs/Faying-Protocol/blueprint/13-%C3%89tat%20Rogue%20et%20Attribution%20de%20Responsabilit%C3%A9
- Phase 1 Human Prime ↔ iFay : https://ifay.ai/fr/docs/Faying-Protocol/blueprint/05-Phase%201%20Human%20Prime%20et%20iFay
