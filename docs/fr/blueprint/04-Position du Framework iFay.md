# Position du Framework iFay

Ce chapitre ne répond qu'à deux questions : à quoi ressemble grossièrement le framework iFay, et où se situe le Faying Protocol en son sein ?

Le framework iFay lui-même a une couverture large et de nombreuses composantes ; toute composante, même légèrement déployée, mène à des détails techniques de champs, de protocoles et de formats de message. Les trois catégories d'actifs de ce dépôt — blueprint, spécification de protocole et schema — ne portent que le Faying Protocol. Tous les membres de la famille de protocoles iFay autres que le Faying Protocol sont uniformément référencés par un lien vers [ifay.ai](https://ifay.ai) ; ce dépôt ne les reformule, ne les réécrit ni ne les dérive.

## Esquisse du framework iFay

Suivant la conception générale sur [ifay.ai](https://ifay.ai), le framework iFay peut être grossièrement compris comme une structure à quatre couches.

**La couche entité** contient deux sortes d'entités intelligentes liées par le protocole. **iFay** (Individual Fay) est obligatoirement attaché un-pour-un à un Human Prime spécifique — supprimez cette attribution, et ce n'est plus un iFay. **coFay** est un Fay partagé ; il n'est autorisé à fonctionner que lorsqu'il est explicitement attribué à un individu ou une organisation ayant la capacité juridique d'assumer une responsabilité. Qu'il s'agisse d'iFay ou de coFay, le Faying Protocol discuté dans ce blueprint les contraint de manière égale : une fois l'attribution caduque, le Fay doit s'arrêter.

**Les composants du noyau** comprennent plusieurs parties inséparables à l'intérieur de chaque entité Fay. **FayID** est l'identité unifiée et unique d'un Fay, le fondement d'identité pour entrer dans toute relation de tutelle. **Ego** est le paradigme de référence aligné sur le profil d'un individu ou d'un rôle spécifique, contraignant l'espace autonome du Fay selon l'orientation de valeurs, les préférences d'intérêt, les habitudes, les frontières cognitives et de compétences, les frontières de permission et le style de travail. Ego n'est pas un grand modèle AGI ; c'est une « frontière de personnalité ». **Runtime** est le runtime virtuel d'un Fay, permettant à iFay et coFay de fonctionner de manière compatible à travers différents terminaux, systèmes d'exploitation et scénarios applicatifs embarqués. FayID et Ego sont les deux préconditions qui permettent au Faying Protocol de prendre effet — le premier porte l'attribution d'identité, le second porte la frontière du comportement.

**La famille de protocoles** comprend un ensemble de protocoles par lesquels un iFay se connecte, perçoit et collabore avec le monde. Au-delà du sujet de ce blueprint, le **Faying Protocol**, elle inclut au moins : des protocoles de transport bidirectionnels liés au contrôle du terminal, des protocoles UI-friendly tournés vers les interfaces utilisateur humaines, des protocoles de communication sémantique entre iFay et coFay qui dépouillent la couche de traduction UI, des protocoles de diffusion-et-souscription pour les capacités côté cloud, et tout futur membre. Pour les détails techniques de la famille de protocoles, voir [ifay.ai](https://ifay.ai) ; ce dépôt ne les inclut pas.

**La structure de valeur** correspond à un nouveau modèle de structure du travail et de distribution de la valeur. Cette couche inclut des transformations systémiques : sortie du travail humain, aplatissement de la connaissance, garanties de subsistance universelles, nouvelle création de valeur, nouvelle stratification sociale — avec des mécanismes tels que MeriToken portant la mesure de valeur. C'est l'arrière-plan à long terme du framework iFay ; il n'atterrit pas directement sur la spécification du Faying Protocol. Voir [ifay.ai](https://ifay.ai) pour les détails.

## La position du Faying Protocol en son sein

En regroupant les quatre couches, la position du Faying Protocol au sein du framework iFay peut être ancrée précisément comme suit :

> **Le Faying Protocol se situe au-dessus de la « couche entité » et des « composants du noyau » et est le sous-protocole au sein de la famille de protocoles responsable de la sémantique du « contrôle sous tutelle et contrôle délégué ». Il transforme la question racine — « FayID est-il attribué à un Human Prime » — en un ensemble d'états et d'actions de connexion qui peuvent être établis, soutenus et révoqués.**

Ce n'est pas une définition de la capacité d'un Fay, donc il ne spécifie pas ce qu'un Fay peut faire. Ce n'est pas un code de conduite d'un Fay, donc il ne spécifie pas comment un Fay doit le faire. Il ne répond qu'à une seule question :

> **Pour cet acte du Fay, en ce moment, qui est responsable ?**

C'est pour cette raison que le Faying Protocol n'est ni le protocole le plus éblouissant ni le plus profond du framework iFay, mais c'est celui qui ne peut être sauté. Une fois qu'il est manquant, le framework iFay tout entier dégénère immédiatement en un écosystème Agent ordinaire, portant le vide de responsabilité décrit au Chapitre 1 dans la société.

## Frontière entre ce dépôt et le framework iFay

```
                 +-------------------+
                 |  panorama ifay.ai  |
                 |  framework iFay    |
                 |   (quatre couches) |
                 +-------------------+
                          │
                          │  Ce dépôt déploie un membre
                          ▼
            +---------------------------+
            |   Projet Faying Protocol   |
            |  (tous les actifs du dépôt)|
            +---------------------------+
                          │
            ┌─────────────┼──────────────┐
            ▼             ▼              ▼
        Blueprint    Spéc. protocole    Schema
   docs/{lang}/    docs/{lang}/         schema/
    blueprint/    specification/   (non livré cette période)
    (cette spéc) (ultérieurement, spéc séparée)
```

Les trois catégories d'actifs de ce dépôt ne portent que le Faying Protocol. Tout déploiement approfondi des autres membres du framework iFay est hors du périmètre de ce dépôt ; rendez-vous directement sur [ifay.ai](https://ifay.ai).

![Vue d'ensemble du framework iFay (alpha1) : le Faying Protocol se situe au niveau du contrat de la relation de tutelle](../../zh-CN/blueprint/illustration/ifay-framework-alpha1.png)

![Bannière de titre iFay](../../zh-CN/blueprint/illustration/ifay-title-banner.png)
