---
title: "Faying Protocol/1.0 — Annexe C Journal des Modifications"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: fr
part: "Annexe C (journal des modifications)"
---

> Navigation du corps du protocole : [Sommaire](./README.md) | précédent [Annexe B Budgets de Paramètres par Défaut](./Annexe-B-Budgets-de-Parametres-par-Defaut.md)

## Annexe C Journal des Modifications

Ce journal consigne quelles modifications le corps du protocole et les livrables associés de Faying Protocol/1.0 ont connues, du premier jet à la version finalisée du brouillon. Sur le plan formel, il suit les habitudes de regroupement de [Keep a Changelog](https://keepachangelog.com) (Added / Changed / Deprecated / Removed / Security) et explique au préalable comment le numéro de version est fixé.

> Note honnête sur l'origine : le brouillon 1.0 de ce protocole a été produit en une seule passe selon un processus piloté par la spécification (exigences → conception → liste de tâches → implémentation) et n'a pas encore traversé plusieurs réunions indépendantes du Protocol Committee. Ce journal n'invente donc pas de décisions de réunion ligne par ligne ni de dates précises ; il consigne fidèlement seulement « ce qui a été fait, pourquoi et à quelle tâche cela correspond ». Les numéros de tâches cités ci-dessous (p. ex. 1.6, 3.8, 5.6) correspondent à des entrées réelles du plan de tâches d'implémentation et permettent de retracer chaque modification jusqu'à son lieu de production. Si l'on passe ultérieurement à un processus formel de revue par le Committee, des entrées avec date et numéro de décision seront ajoutées ici.

## Comment le numéro de version est fixé

Les **règles faisant autorité de la numérotation des versions du protocole figurent en §1.7 Gestion des versions et compatibilité** du corps du protocole (trois axes orthogonaux : version du protocole `MAJEUR.MINEUR` / statut du document / édition rédactionnelle ; règles de négociation et de compatibilité ; points d'atterrissage du numéro de version et notes pour les implémenteurs). Cette annexe ne redéfinit pas cela ; elle ajoute seulement deux points pertinents pour le journal des modifications :

- Ce journal classe chaque modification selon les critères MAJEUR / MINEUR de §1.7.2 : ce qui casse l'interopérabilité passe en MAJEUR, les ajouts rétrocompatibles passent en MINEUR, les errata purement textuels sont rangés selon §1.7.4 sous `Editorial` et ne changent pas le numéro de protocole.
- Actuellement, c'est `Faying Protocol/1.0`, la première ligne de base, statut Final (publié le 2025-10-25).

Sur le plan du nommage, la prose et le numéro de version utilisent uniformément `Faying Protocol/1.0` ; l'ancienne abréviation `FAP` est abolie. Toutefois, les noms de fichiers de schéma `fap-1.0.cddl` / `fap-1.0.proto` conservent l'ancien préfixe, purement pour garder les noms de fichiers stables et ne pas casser les références existantes — c'est intentionnel, et non une inconsistance de nommage (cohérent avec §1.7.5 « les noms de fichiers de schéma ne changent pas d'une édition rédactionnelle à l'autre »).

## [Faying Protocol/1.0] — Final (2025-10-25)

Il s'agit de la première version officielle de 1.0, migrée dans son ensemble depuis l'espace de travail du brouillon vers le répertoire de publication officiel et finalisée le 2025-10-25. Ci-dessous, regroupé par type de modification, chaque élément étant marqué du numéro de tâche qui l'a produit.

### Added

Corps du protocole (§1–§11 + Annexes A/B) :

- §1 Overview : nommage du protocole, positionnement, huit objectifs de conception G1–G8, objectifs en correspondance un à un avec les Requirements ; §1.5.1 établit l'assertion centrale « tout Faying bidirectionnel ne prend effet qu'avec l'acquittement explicite du HP ». (Tâche 1.2)
- §2 Architecture : quatre diagrammes Mermaid (pile du protocole, relations entre entités, hiérarchie des niveaux, séquence Bootstrap+Heartbeat+Action, y compris le chemin Phase A0 initié par l'IF) et six principes de conception. (Tâche 1.3)
- §3 Components and Interfaces : interfaces et invariants des six composants (MS / PC / AC / RR / LC / BBS). (Tâche 1.4)
- §4 Data Models : définition CDDL faisant autorité, vue lisible TypeScript, machine à états du Mandate avec état Disconnected et réconciliation à la reconnexion, sous-structure endorsement. (Tâche 1.5)
- §5 Protocol Messages : sept classes de messages (BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE / REVOKE / FAYING_REQUEST / DISCLOSURE), enveloppe unifiée, 14 codes d'erreur — dont l'ajout de 1010 `E_HUMAN_WITNESS_REQUIRED`, 1013 `E_ENDORSEMENT_INVALID`, 1014 `E_FAYING_REQUEST_NOT_CONFIRMED`. (Tâche 1.6)
- §6 Cryptography : négociation de la suite d'algorithmes (y compris les bits de négociation PQC), dérivation de clés, format de signature ; le champ endorsement entre dans l'entrée de signature. (Tâche 1.7)
- §7 Authorization Grades : sémantique des cinq niveaux G0–G4, matrice de déclenchement, monotonie d'abaissement, ainsi que les sous-niveaux Endorsement Grades de §7.5 superposés au-dessus de G1–G4. (Tâche 1.8)
- §8 Lifecycle : cycle de vie à sept états (y compris Disconnected), séquence d'attribution de responsabilité, transaction de réconciliation à la reconnexion de §8.4. (Tâche 1.9)
- §9 Security Considerations : STRIDE, anti-rejeu / anti-détournement / anti-hameçonnage, identification de déconnexion, matrice de gestion de la déconnexion, ainsi que le catalogue de menaces adverses de l'ère de l'IA T1–T7 de §9.10. (Tâche 1.10)
- §10 Error Handling, §11 Open Questions, Annexes A/B : scénarios d'erreur et chemins de récupération, questions ouvertes Q1–Q14, glossaire, budgets de paramètres par défaut. (Tâche 1.11)
- Traduction intégrale de la spécification anglaise. (Tâche 1.12)

Livrables associés :

- schema : `schemas/fap-1.0.cddl` (faisant autorité), `schemas/types.ts` (vue lisible TypeScript, Not Normative), `schemas/fap-1.0.proto` (liaison gRPC alternative, Not Normative). (Tâches 2.1–2.3)
- Vecteurs de test `vectors/` : couvrent 11 classes au total — BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE / REVOKE, codes d'erreur, équivalence d'encodage, Endorsement, FAYING_REQUEST, DISCLOSURE, Disconnection. (Tâches 3.1–3.11)
- Tests basés sur les propriétés `pbt/` : couvrent les propriétés principales P1–P15, plus les trois familles P16 (Endorsed_Mandate), P17 (Disconnection), P18 (AI-Era). (Tâches 4.1–4.34)
- Suite de conformité d'interopérabilité `conformance/` : matrice à cinq dimensions encodage × algorithme de signature × hachage × canal × langage d'implémentation, avec deux implémentations de référence en TypeScript et Rust. (Tâches 5.1–5.6)
- Simulation d'attaques de sécurité `conformance/attacks/` : rejeu, détournement, hameçonnage, identification de déconnexion, ainsi que les simulations T1/T3/T4/T5/T6. (Tâches 6.1–6.10)

### Changed

- Le nommage du protocole est passé du premier brouillon « Faying Auth Protocol (FAP) » à **Faying Protocol**, le numéro de version s'écrivant `Faying Protocol/1.0`. (correspond à §11 Q10, résolu)
- L'initiation du Faying est passée d'unidirectionnelle (seul le HP peut initier) à bidirectionnelle (initiée par le HP + initiée par l'IF), mais la condition d'effectivité converge uniformément vers la seule condition « acquittement explicite du HP ». (Tâches 1.6, 3.9)
- La déconnexion est scindée en deux sémantiques « déconnexion réelle » et « déconnexion perçue » ; la décision du protocole ne regarde que la déconnexion perçue, et fait une présomption pessimiste pour la fenêtre d'incohérence. (Tâches 1.10, 3.11)
- L'entrée de signature est unifiée en `H(Deterministic-CBOR(Envelope_without_signature))` ; le format primaire CBOR et le repli JSON sont équivalemment interopérables sous ce barème. (Tâches 3.7, 5.2)

### Deprecated

- Les anciens noms `FAP` / `FAP/1.0` / `Faying Auth Protocol`, ainsi que les anciennes formes de points de terminaison comme `application/fap+json`, `POST /fap/v1/...`, sont tous abolis. La nouvelle écriture utilise `application/faying-protocol+json` et `POST /faying-protocol/v1/{verb}`. Les noms de fichiers de schéma sont la seule exception qui conserve l'ancien préfixe (voir ci-dessus « Comment le numéro de version est fixé »).

### Removed

- Aucun. 1.0 est la première ligne de base ; il n'y a aucun champ ou message existant à supprimer.

### Security

- Nouvelles contraintes au niveau du protocole contre les menaces adverses de l'ère de l'IA : T1 ingénierie sociale, T2 opération boîte noire, T3 divulgation sélective, T4 dérive de l'attention, T5 culture de confiance stéréotypée, T6 déluge d'audit, T7 emplacement extensible, chacune correspondant aux Property P18.1–P18.7 et Requirement 13.1–13.7. (Tâches 1.10, 4.28–4.34, 6.6–6.10)
- Contrainte anti-altération de l'autorisation endossée : l'endorsement entre dans l'entrée de signature ; modifier un sous-champ quelconque fait échouer la vérification de signature du Mandate (`E_ATTESTATION_INVALID` / `E_ENDORSEMENT_INVALID`). (Tâches 1.5, 3.8, 4.17–4.21)
- Révocation symétrique et irréversibilité de la révocation : l'accessibilité du chemin de révocation n'est pas inférieure à celle du chemin d'établissement, `Revoked` est un état absorbant, la révocation en cascade est activée par défaut. (Tâches 3.5, 4.5, 4.11, 4.15)

## Comment cela sera maintenu à l'avenir

- Après l'entrée dans la revue formelle, chaque décision du Committee ajoute ici une ligne, indiquant la date, les sections affectées et le numéro de tâche déclencheur, et un élément lisible par l'humain est ajouté dans le groupe Keep a Changelog correspondant ci-dessus.
- Numéro de version : exécuter selon §1.7 — les ajouts rétrocompatibles passent par MINEUR, les changements cassants par MAJEUR avec remise à zéro de MINEUR, les errata purement textuels par l'édition rédactionnelle (§1.7.4) sans changer le numéro de protocole.
- Les errata ultérieurs et la migration d'édition sont exécutés conformément à §1.7.4 / §1.7.5 ; ce journal est migré conjointement avec le corps du protocole et mis à jour au fil de chaque édition.
- Les modifications de même type sont synchronisées sur le même cycle entre les versions linguistiques ; en cas de divergence, la version de référence fait foi.

---
