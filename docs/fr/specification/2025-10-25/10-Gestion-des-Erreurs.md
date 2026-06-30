---
title: "Faying Protocol/1.0 — §10 Gestion des Erreurs"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: fr
part: "Chapitre 10 sur 11 (corps du protocole)"
---

> Navigation du corps du protocole : [Sommaire](./README.md) | précédent [§9 Considérations de Sécurité](./09-Considerations-de-Securite.md) | suivant [§11 Questions Ouvertes](./11-Questions-Ouvertes.md)

## §10 Gestion des Erreurs

Ce chapitre consolide tous les codes d'erreur de §5.4 avec des scénarios de défaillance concrets, les réponses du protocole, les transitions d'état, les chemins de récupération et les contraintes d'observabilité. Toutes les erreurs sont renvoyées sous forme de messages `ERROR` sous l'enveloppe §5.2, avec un corps `claims` de la forme `{ code, message, mandate_id?, recovery_hint? }` ; les quatre sections de ce chapitre constituent l'« unique autorité au niveau du protocole sur la gestion des erreurs » au-delà de §5.4.

### EH.1 Scénarios d'erreur et réponses du protocole

Le tableau ci-dessous donne une vue panoramique de tous les codes d'erreur listés en §5.4 (1001–1014 et 1099) ; chaque ligne contient : scénario de déclenchement, réponse du protocole, déclenchement ou non du Revoke, déclenchement ou non de l'abaissement, entrée obligatoire ou non dans la chaîne d'audit, et poussée obligatoire ou non vers le canal de vue du HP. Ce tableau correspond un à un à la table des codes d'erreur §5.4.

| Code | Nom | Scénario de déclenchement | Réponse du protocole | Déclenche Revoke | Déclenche abaissement | Entre en audit | Entre en vue du HP |
| ---: | --- | --- | --- | :---: | :---: | :---: | :---: |
| 1001 | `E_NO_MANDATE` | La requête métier ne porte aucun en-tête Faying Protocol / Mandate | La RP rejette immédiatement ; aucun audit établi | ✗ | ✗ | ✗ | ✗ |
| 1002 | `E_MANDATE_EXPIRED` | `now > Mandate.not_after` | La RP rejette + le MS déclenche le Revoke de ce Mandate | ✓ | ✗ | ✓ | ✗ |
| 1003 | `E_SCOPE_VIOLATION` | Action d'appel ∉ `Mandate.scope.actions` | La RP rejette + enregistre un événement suspect ; la suspicion cumulée déclenche un abaissement | ✗ | ✓ (cumulatif) | ✓ | ✗ |
| 1004 | `E_GRADE_INSUFFICIENT` | La RP exige un niveau plus strict que le `Mandate.grade` courant | La RP rejette + suggère un rehaussement (le chemin de rehaussement requiert le `human_witness` du HP) | ✗ | ✗ | ✓ | ✗ |
| 1005 | `E_PRESENCE_STALE` | `presence.last_freshness` dépasse `max_staleness_ms` ou `LivenessDetectionBudget` | La RP rejette ; l'IF arrête proactivement la dimension D, attend la calibration PRESENCE ; machine à états Active → Degraded | ✗ | ✓ | ✓ | ✗ |
| 1006 | `E_REVOKED` | Le RR marque révoqué | La RP rejette ; rejette en cascade les appels de même chaîne ; l'IF retombe immédiatement à Rogue Fay | ✓ (déjà révoqué) | ✗ | ✓ | ✓ |
| 1007 | `E_ATTESTATION_INVALID` | Échec de vérification de signature d'un nœud de l'Attestation Chain / horodatage hors de la fenêtre de validité du nœud parent / sous-champ endorsement altéré | La RP rejette + le MS déclenche le Revoke de ce Mandate | ✓ | ✗ | ✓ | ✓ |
| 1008 | `E_RR_UNAVAILABLE` | Délai d'interrogation RR ≥ `StaleBudget` | La RP rejette par Refus par défaut ; l'IF met en pause toute la dimension D ; machine à états Active → Degraded | ✗ | ✓ | ✓ | ✗ |
| 1009 | `E_REPLAY` | Dans `2 × max_message_lifetime`, nonce déjà vu pour le même subject | La RP rejette + alerte de sécurité ; l'IF tourne immédiatement les clés de session | ✗ | ✗ | ✓ | ✓ |
| 1010 | `E_HUMAN_WITNESS_REQUIRED` | rehaussement de niveau / FAYING_REQUEST ou autre scénario requérant le témoignage du HP, `human_witness` manquant ou échec de vérification | La RP / le MS rejette ; attendre le témoignage du HP puis réinitier | ✗ | ✗ | ✓ | ✗ |
| 1011 | `E_ROGUE_DETECTED` | Violation de dimension D détectée (`ego-deviation` / dépassement de seuil de la ligne de base comportementale, etc.) | La RP rejette + Revoke forcé ; l'IF retombe immédiatement à Rogue Fay | ✓ | ✗ | ✓ | ✓ |
| 1012 | `E_BUDGET_EXCEEDED` | Les appels dépassent cumulativement `Scope.budget` / `ResourceBudget` | La RP rejette + déclenche un abaissement ou (cas extrêmes) Revoke | ✓ (extrême) | ✓ | ✓ | ✗ |
| 1013 | `E_ENDORSEMENT_INVALID` | `endorsed_scope ⊄ scope` / `endorsed_grade.autonomy > grade.autonomy` / `endorsed_lifetime` manquant ou trop long / sous-champ endorsement altéré / endossement enfant DELEGATE ne convergeant pas au sein du parent | Le MS rejette l'émission + déclenche le Revoke de ce Mandate ; l'IF arrête immédiatement toutes les actions endossées | ✓ | ✗ | ✓ | ✓ |
| 1014 | `E_FAYING_REQUEST_NOT_CONFIRMED` | Une FAYING_REQUEST initiée par l'IF non explicitement acquittée par le HP dans `BootstrapTimeout` | Le MS renvoie `FAYING_REQUEST_RESP { status="timeout" }` ; ne produit aucun changement d'état Faying ; événement inscrit dans l'Attestation Chain | ✗ | ✗ | ✓ | ✗ |
| 1099 | `E_PROTOCOL` | Version / format / champ manquant / non analysable / `mandatory_fields` de DISCLOSURE manquants ou non analysables / entrée de signature illégale / `msg_type` non explicitement listé en §5.3 | La RP / le MS rejette ; pousse en outre vers la vue du HP lorsqu'il est déclenché depuis le chemin DISCLOSURE | ✗ | ✗ | ✓ | ✗* (chemin DISCLOSURE ✓) |

> **Note `*`** : par défaut, `E_PROTOCOL` n'entre que dans la chaîne d'audit ; lorsqu'il est déclenché depuis le chemin de §5.3.7 DISCLOSURE `mandatory_fields` manquants ou non analysables, le MS doit en outre pousser vers le canal de vue du HP (cohérent avec la note §5.4).

**Trace** : `R2.1.1`–`R2.1.4` (Refus par défaut), `R3.2.1`–`R3.2.3` (événements d'erreur vers audit et vue du HP), `R4.2.1`–`R4.2.3` (budget de visibilité de révocation et accessibilité), `R11.1.4` (l'altération d'endossement déclenche `E_ATTESTATION_INVALID` + Revoke), `R11.2.1`–`R11.2.3` (la violation de convergence d'endossement déclenche `E_ENDORSEMENT_INVALID`), `R1.3.3` (le dépassement de délai de FAYING_REQUEST sans acquittement déclenche `E_FAYING_REQUEST_NOT_CONFIRMED`), `R13.3.1` (les `mandatory_fields` de DISCLOSURE manquants ou non analysables déclenchent `E_PROTOCOL`).

### EH.2 Chemins de récupération

Les codes d'erreur sont regroupés en trois classes de chemins de récupération selon « la nécessité ou non de rétablir l'état Faying ». Tous les chemins de récupération doivent s'exécuter dans la convergence Refus par défaut EH.4 ; aucune fenêtre intermédiaire de passage optimiste n'existe.

#### EH.2.1 Erreurs récupérables (pas besoin de BOOTSTRAP)

| Code | Nom | Action de récupération |
| ---: | --- | --- |
| 1004 | `E_GRADE_INSUFFICIENT` | Déclencher GRADE_SWITCH-rehaussement (doit porter le `human_witness` du HP ; voir §7.4) ; la récupération en sautant le témoignage n'est pas autorisée |
| 1005 | `E_PRESENCE_STALE` | Renvoyer un message PRESENCE pour rafraîchir `last_freshness` ; en cas d'échec persistant, converger selon `LivenessDetectionBudget` vers Degraded → Suspended |
| 1008 | `E_RR_UNAVAILABLE` | Dans la fenêtre Refus par défaut, réessayer avec recul (pas plus long que `StaleBudget`) ; dépassé → entrer en Degraded, attendre la récupération du RR avant de se reconnecter |
| 1012 | `E_BUDGET_EXCEEDED` | Déclencher GRADE_SWITCH-abaissement ou attendre le rafraîchissement de la fenêtre de budget ; la récupération « ignorer le budget » n'est pas autorisée |

#### EH.2.2 Récupération requérant un re-témoignage du HP (doit relancer BOOTSTRAP)

| Code | Nom | Action de récupération |
| ---: | --- | --- |
| 1002 | `E_MANDATE_EXPIRED` | Relancer BOOTSTRAP ; le nouveau `mandate_id` ne doit pas être égal à l'ancien `mandate_id` (cohérent avec l'irréversibilité de révocation P10) |
| 1006 | `E_REVOKED` | Non récupérable ; seul le HP peut initier un nouveau BOOTSTRAP ; le nouveau `mandate_id` ne doit pas être égal à l'ancien `mandate_id` |
| 1007 | `E_ATTESTATION_INVALID` | Comme ci-dessus ; nouveau BOOTSTRAP autorisé uniquement après le déclenchement du Revoke forcé de ce Mandate |
| 1011 | `E_ROGUE_DETECTED` | Comme ci-dessus ; habituellement accompagné d'une intervention directe du HP et d'un audit ego-deviation |
| 1013 | `E_ENDORSEMENT_INVALID` | Comme ci-dessus ; après le déclenchement du Revoke du Mandate, le HP doit initier un nouveau BOOTSTRAP (contenant un champ `endorsement` légitime) |

#### EH.2.3 Ne constituant pas un changement d'état Faying (pas de récupération nécessaire)

| Code | Nom | Traitement |
| ---: | --- | --- |
| 1001 | `E_NO_MANDATE` | L'appelant doit d'abord obtenir un Mandate puis initier l'appel ; aucun chemin de « passage temporaire sans Mandate » n'existe au niveau du protocole |
| 1003 | `E_SCOPE_VIOLATION` | L'appelant doit ajuster l'action pour qu'elle relève de `Mandate.scope.actions` ; la suspicion cumulée déclenche un abaissement |
| 1009 | `E_REPLAY` | L'appelant devrait réinitier avec un nouveau nonce ; s'il s'agit d'un comportement d'attaque, l'alerte de sécurité et la vue du HP ont déjà été inscrites |
| 1010 | `E_HUMAN_WITNESS_REQUIRED` | Réinitier après l'obtention du témoignage du HP ; la substitution par IF / MS / SA n'est pas autorisée |
| 1014 | `E_FAYING_REQUEST_NOT_CONFIRMED` | l'iFay peut réinitier une FAYING_REQUEST dans les limites de débit légitimes, mais ne doit pas pour autant monter un déluge de confirmations (voir §9.10.7, Annexe B `ConfirmationRateLimit`) |
| 1099 | `E_PROTOCOL` | L'appelant doit corriger la structure du message puis réinitier |

> **Contrainte dure commune** : les chemins de récupération ne doivent pas contourner la convergence Refus par défaut §EH.4 ; aucun chemin de récupération optimiste « je ne suis pas sûr mais laissons passer d'abord » n'existe au niveau du protocole.

### EH.3 Contraintes d'observabilité sur les réponses d'erreur

Tous les messages ERROR doivent satisfaire les quatre contraintes dures suivantes :

1. **Quintuplet d'audit** : sauf pour `E_NO_MANDATE` (pas de contexte de Mandate), chaque code d'erreur doit être inscrit dans l'Attestation Chain / le journal d'audit sous forme du quintuplet `(error_code, mandate_id, ts, RP_id, reason)` ; ce quintuplet est cohérent avec §3.2 et la colonne « Entre en audit » de §EH.1.
2. **Le canal de vue du HP doit pousser** : l'ensemble de codes d'erreur `{E_REVOKED (1006), E_ATTESTATION_INVALID (1007), E_REPLAY (1009), E_ROGUE_DETECTED (1011), E_ENDORSEMENT_INVALID (1013)}` doit être poussé vers le canal de vue du HP ; `E_PROTOCOL (1099)` déclenché depuis le chemin DISCLOSURE doit également être poussé. La RP ne doit pas les avaler silencieusement.
3. **Aucune fuite d'information sensible** : les réponses d'erreur ont **interdiction** de porter l'état interne du MS, des empreintes de clé privée de Mandate, d'autres identifiants de HP, des variables de la machine à états interne de l'IF ou toute autre information sensible ; les champs `message` et `recovery_hint` doivent être une sémantique publique au niveau du protocole, sans aucune fuite de détail d'implémentation.
4. **Chaîne d'audit vérifiable de façon indépendante** : les événements d'erreur inscrits dans l'Attestation Chain doivent porter les nœuds de signature requis par §3.3 I-AC-1 / I-AC-2, de sorte qu'un tiers puisse compléter la vérification de chaîne feuille-à-racine sans détenir la clé privée du MS (voir §6.3).

**Trace** : `R3.2.1` (quintuplet de code d'erreur inscrit dans le journal d'audit), `R3.2.2` (les réponses d'erreur ne doivent pas porter d'information sensible), `R3.2.3` (les codes d'erreur spécifiés doivent entrer en vue du HP), `R3.1.4` (champs traçables de la chaîne d'audit).

### EH.4 Convergence Refus par défaut unifiée

> **Toute erreur qui ne peut être classée sans ambiguïté, tout champ non analysable et tout appel pendant une inaccessibilité du RR est uniformément rejeté par la couche protocole avec `E_PROTOCOL` ou `E_RR_UNAVAILABLE` ; aucun chemin légitime « je ne suis pas sûr mais laissons passer d'abord » n'existe, ni aucun chemin de récupération optimiste « traiter selon l'état le plus permissif » (y compris la Fenêtre B où réellement en ligne mais perçue déconnectée ; voir §9.9).**

**Quatre expressions équivalentes de la règle de convergence** :

1. **Couche machine à états** : toute transition non explicitement listée dans la machine à états du Mandate §4.3 / la machine à états du cycle de vie §8.1 est uniformément rejetée.
2. **Couche message** : tout `msg_type` non explicitement listé dans l'inventaire de messages §5.3, ou tout champ d'enveloppe manquant / de type incohérent, est uniformément rejeté avec `E_PROTOCOL`.
3. **Couche code d'erreur** : toute cause de défaillance non explicitement listée en §5.4 / §EH.1 est uniformément classée en rejet `E_PROTOCOL`.
4. **Couche décision** : la couche protocole n'utilise que Perceived-Disconnected comme base de décision ; les chemins de passage optimiste de la Fenêtre A (réellement déconnectée mais perçue connectée) / Fenêtre B (réellement connectée mais perçue déconnectée) n'existent pas au niveau du protocole (voir le principe de présomption pessimiste §9.9, P17.1 / P17.2).

**Trace** : `R2.1.1`–`R2.1.4` (Refus par défaut), `R12.1.1`–`R12.1.3` (décision à double sémantique Perceived-only), `R12.2.1`–`R12.2.3` (présomption pessimiste / rejet pendant la déconnexion perçue).
