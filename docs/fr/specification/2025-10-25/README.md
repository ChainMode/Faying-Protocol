---
title: Faying Protocol/1.0 — Sommaire de la spécification du protocole (Brouillon)
version: Faying Protocol/1.0
status: Final
editors:
  - Faying Protocol Committee
date: 2025-10-25
language: fr
replaces: -
---

# Spécification du protocole Faying Protocol/1.0

Ceci est la spécification officielle en français de Faying Protocol/1.0 (Final, publié le 2025-10-25). Le corps du protocole est scindé par chapitres en 11 fichiers, avec une numérotation de chapitre à deux chiffres et des noms de fichiers portant le nom du chapitre ; l'aide-mémoire terminologique, les budgets de paramètres et les éléments relatifs au processus de genèse du protocole sont intégrés comme annexes, afin que les contributeurs open source comprennent à la fois le protocole lui-même et la manière dont il a été établi pas à pas.

La spécification anglaise se trouve sous [`../../../en/specification/2025-10-25/`](../../../en/specification/2025-10-25/) et a une **structure en fichier unique** (le corps du protocole est entièrement intégré dans le seul fichier `Faying-Protocol-1.0.md`, avec §1–§11 et les Annexes A/B) ; la correspondance avec la version française est une correspondance au **niveau de l'ancre de section**, non fichier par fichier. En cas de divergence, la version de référence fait foi.

## Comment lire

Si vous y êtes confronté pour la première fois, il est recommandé de lire une fois le corps du protocole dans l'ordre §1 → §11, puis de consulter les annexes. Si un terme n'est pas clair, cherchez dans l'Annexe A ; pour des valeurs concrètes comme les délais d'attente / budgets, voir l'Annexe B.

## Corps du protocole (§1–§11)

| Chapitre | Fichier | Contenu |
| --- | --- | --- |
| §1 | [01-Vue-d-ensemble.md](./01-Vue-d-ensemble.md) | Nommage du protocole, positionnement, objectifs de conception, différences avec les schémas existants, définition en une phrase, périmètre et non-objectifs |
| §2 | [02-Architecture.md](./02-Architecture.md) | Position dans la pile du protocole, relations entre entités, hiérarchie des niveaux, séquence d'interaction principale, principes de conception |
| §3 | [03-Composants-et-Interfaces.md](./03-Composants-et-Interfaces.md) | Interfaces et invariants des six composants centraux (MS / PC / AC / RR / LC / BBS) |
| §4 | [04-Modeles-de-Donnees.md](./04-Modeles-de-Donnees.md) | Vue lisible TypeScript, définition CDDL faisant autorité, machine à états du Mandate |
| §5 | [05-Messages-du-Protocole.md](./05-Messages-du-Protocole.md) | Règles d'encodage, structure d'enveloppe, sept classes de messages, table des codes d'erreur |
| §6 | [06-Cryptographie.md](./06-Cryptographie.md) | Négociation de la suite d'algorithmes, dérivation de clés, format de signature |
| §7 | [07-Niveaux-d-Autorisation.md](./07-Niveaux-d-Autorisation.md) | Sémantique des niveaux G0–G4, matrice de déclenchement, monotonie d'abaissement, sous-niveaux Endorsement |
| §8 | [08-Cycle-de-Vie.md](./08-Cycle-de-Vie.md) | Machine à états du cycle de vie de bout en bout, séquence d'attribution de responsabilité, réconciliation à la reconnexion |
| §9 | [09-Considerations-de-Securite.md](./09-Considerations-de-Securite.md) | STRIDE, anti-rejeu / anti-détournement / anti-hameçonnage, détection de déconnexion, catalogue de menaces de l'ère de l'IA |
| §10 | [10-Gestion-des-Erreurs.md](./10-Gestion-des-Erreurs.md) | Scénarios d'erreur, chemins de récupération, conditions d'observabilité, convergence Refus par défaut |
| §11 | [11-Questions-Ouvertes.md](./11-Questions-Ouvertes.md) | Questions ouvertes Q1–Q14 laissées au Protocol Committee pour clarification |

## Annexes

| Annexe | Fichier | Contenu |
| --- | --- | --- |
| A | [Annexe-A-Alignement-Terminologique.md](./Annexe-A-Alignement-Terminologique.md) | Aide-mémoire terminologique, source terminologique faisant autorité pour l'implémentation et la revue |
| B | [Annexe-B-Budgets-de-Parametres-par-Defaut.md](./Annexe-B-Budgets-de-Parametres-par-Defaut.md) | Paramètres par défaut et bornes supérieures, règles de resserrement par niveau |
| C | [Annexe-C-Journal-des-Modifications.md](./Annexe-C-Journal-des-Modifications.md) | Journal des modifications depuis le premier jet du brouillon jusqu'à la version finalisée, et stratégie de numérotation des versions |

## Version

- Nom du protocole : Faying Protocol (l'abréviation « FAP » utilisée dans les premiers brouillons est abolie)
- Numéro de version : Faying Protocol/1.0
- Statut : Final (publié le 2025-10-25)
- Editors : Faying Protocol Committee

Les numéros de version dans le front matter de tous les fichiers du corps du protocole concordent avec ceci. Il s'agit du premier état de publication officiel de la version 1.0, migré dans son ensemble depuis l'espace de travail du brouillon vers ce répertoire ; les versions française et anglaise ont été publiées conjointement dans la même remise, sans publication unilatérale. Les errata ultérieurs sont portés, conformément à §1.7.4, par une nouvelle édition dotée de sa propre date de publication, sans changer le numéro de version du protocole.
