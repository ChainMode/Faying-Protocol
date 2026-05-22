# Gestion des Identifiants

La gestion des identifiants sonne très technique — émission, signature, révocation et renouvellement de FayID, chacun impliquant des algorithmes spécifiques et des protocoles de clés. Mais dans ce blueprint, la gestion des identifiants est placée sous les valeurs, et non sous les sujets techniques.

La raison en est la suivante : le Faying Protocol existe pour rendre explicite « à qui appartient l'acte ». Le porteur technique de cela, lorsqu'il atterrit au niveau concret du protocole, est l'identifiant. L'identifiant répond à deux questions :

> **Ce Fay, en ce moment, est-il le Fay qu'il prétend être ?**
> **Ce Fay, en ce moment, est-il toujours autorisé par son Human Prime ?**

Aucune n'est une question d'ingénierie ; les deux sont des questions de responsabilité. Une fois que les identifiants peuvent être falsifiés, abusés ou émis discrètement par un tiers extérieur au Human Prime, la valeur entière du Faying Protocol s'évanouit en un instant — le Human Prime n'est plus le véritable détenteur de la responsabilité.

Les algorithmes spécifiques, les formats de signature, les protocoles de clés et autres détails techniques appartiennent au document de spécification du protocole et au schema ; ce chapitre ne les déploie pas. Ce chapitre n'énonce que les quelques positions sur la gestion des identifiants sur lesquelles aucune concession n'est permise.

## FayID est le fondement d'identité pour entrer en Faying State

FayID est l'identité unifiée et unique d'un Fay au sein du framework iFay. Le contrat de tutelle entier du Faying Protocol est construit sur FayID. Une Faying Action doit rendre explicite « quel FayID entre en Faying State » ; l'attribution de Faying State doit rendre explicite « quel FayID est attribué à quel Human Prime » ; la sortie de Faying State doit rendre explicite « quel FayID entre en Rogue Fay ».

Si FayID ne peut être digne de confiance, les trois jugements ci-dessus perdent leur sens.

## La défaillance de l'identifiant équivaut à la défaillance de Faying

Parmi les neuf conditions de déclenchement pour la transition automatique de Faying State vers Rogue Fay listées au Chapitre 13, la condition 6 énonce explicitement :

> **L'identité du Fay ne peut être vérifiée (par exemple, la signature FayID est devenue caduque).**

Cet élément n'est pas une entrée parmi les neuf qui « concerne accidentellement les identifiants » ; c'est l'atterrissage concret de la gestion des identifiants au niveau du protocole qui ne peut être contourné. Une fois que la validité de FayID est mise en doute, peu importe à quel point le travail antérieur du Fay est continu ou presque complet, Faying State doit sortir immédiatement :

> **Un doute sur la validité de l'identifiant équivaut à ce que Faying State ait déjà défailli.**

Il n'existe aucun cas intermédiaire « l'identifiant est suspect mais Faying State tient toujours », et il n'existe aucun compromis d'ingénierie de « finir d'abord la tâche en cours puis traiter le problème de l'identifiant ».

## Les droits de révocation doivent rester du côté du Human Prime

La gestion des identifiants comporte un arbitrage en apparence mineur mais extrêmement critique dans la conception du protocole — à qui appartient ultimement la révocation d'un identifiant ? La réponse est évidente : au Human Prime.

Le Fay lui-même ne devrait avoir aucun chemin légitime pour révoquer son propre identifiant — homologue à D4 du Chapitre 13, un Fay ne peut décider seul de quitter la tutelle, ni décider seul de couper le lien de tutelle.

Les plateformes tierces, les fournisseurs de runtime du Fay et les fournisseurs de capacités du Fay ne doivent pas avoir le pouvoir de révoquer son FayID sans le consentement du Human Prime — à moins que ce tiers ne soit une autorité compétente au sens réglementaire (voir la condition de déclenchement 8 du Chapitre 13).

Le Human Prime doit toujours conserver un chemin de révocation symétrique, joignable et auditable. La joignabilité de l'action de révocation ne doit pas être inférieure à la joignabilité de l'initiation d'une Faying Action. C'est l'atterrissage concret au niveau de l'identifiant du principe de « symétrie » du Faying Protocol : établir la tutelle et révoquer la tutelle doivent être deux chemins également joignables. Une fois que la révocation devient plus difficile que l'établissement, la relation de tutelle glisse en fait vers une « délégation irrévocable », violant ainsi l'exigence du « chemin d'intervention toujours ouvert » de Human View.

## Le renouvellement n'est pas un comportement par défaut

Le Chapitre 12 impose une contrainte dure à Faying State : un Faying State doit être de portée bornée, et un Faying illimité est un anti-pattern. La position que cette contrainte correspond au niveau de l'identifiant est — le renouvellement d'un identifiant ne devrait pas être effectué par défaut.

Chaque renouvellement devrait être une action explicite et témoignable, et non une boucle implicite de « le Fay soumet automatiquement, le système renouvelle automatiquement ». Le blueprint autorise des commodités au niveau de l'ingénierie telles que les « rappels de renouvellement » et les « suggestions de renouvellement », mais interdit de faire du « renouvellement » quelque chose que le Fay peut compléter silencieusement par lui-même — cela transformerait en fait Faying en délégation illimitée.

Compris du point de vue de la responsabilité : le renouvellement est le moment où l'extrémité responsable réexprime l'intention de tutelle. Si même le renouvellement est silencieusement complété par l'ingénierie, alors la « tutelle » n'a plus qu'une signature et plus d'intention.

## Quelques lignes rouges inviolables

Les quelques positions de valeurs de la gestion des identifiants sont des lignes rouges qu'aucune solution technique ne peut violer lors de l'atterrissage :

- FayID est le fondement d'identité ;
- un identifiant qui ne peut être digne de confiance signifie que Faying ne tient pas ;
- les droits de révocation doivent rester du côté du Human Prime ;
- le renouvellement n'est pas un comportement par défaut.

Les algorithmes de signature concrets, les hiérarchies de clés, la propagation des listes de révocation, la conception fine des fenêtres temporelles de renouvellement, la structure des certificats racines pour la confiance mutuelle inter-fournisseurs et la cohérence à terme de la révocation — ces détails techniques appartiennent à la spécification du protocole. Ce chapitre ne les reformule ni ne les pré-décide, mais toute solution technique doit d'abord se conformer aux quatre positions ci-dessus.

![Illustration de gestion des identifiants : contrôle de FayID, signature, révocation et renouvellement du côté du Human Prime](../../zh-CN/blueprint/illustration/credential-management.png)
