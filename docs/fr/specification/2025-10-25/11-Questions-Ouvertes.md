---
title: "Faying Protocol/1.0 — §11 Questions Ouvertes"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: fr
part: "Chapitre 11 sur 11 (corps du protocole)"
---

> Navigation du corps du protocole : [Sommaire](./README.md) | précédent [§10 Gestion des Erreurs](./10-Gestion-des-Erreurs.md) | suivant [Annexe A Alignement Terminologique](./Annexe-A-Alignement-Terminologique.md)

## §11 Questions Ouvertes

> Ce chapitre énumère honnêtement les sujets qui ne doivent pas nécessairement être tranchés dans le corps du protocole de la Phase 1 mais laissés au Protocol Committee pour résolution au stade RFC. Chaque sujet fournit l'**inclination actuelle du protocole**, des **alternatives** et un **statut de résolution**, afin que les discussions RFC ultérieures aient un point de départ structuré. Les entrées résolues (p. ex. Q10 nommage du protocole) sont conservées comme trace historique.

### Q1 Signalement de localisation du terminal pendant l'état Rogue

- **Sujet** : pendant que l'iFay est en Rogue Fay, le terminal est-il autorisé à continuer de signaler sa localisation physique ? Implique la tension bilatérale « vie privée vs récupérabilité ».
- **Inclination actuelle du protocole** : différencier par `RevokeReason` — `human-initiated` / `task-completed` ne signalent pas ; `fay-credential-invalid` / `regulatory-order` / `terminal-disconnected`, etc. peuvent signaler.
- **Alternatives** : (a) interdiction générale ; (b) autorisation générale ; (c) le HP présélectionne explicitement au moment du BOOTSTRAP.
- **Statut de résolution** : ouvert ; le chapitre 14 de la note de cadrage ne conclut déjà explicitement pas.

### Q2 Chemin non rejetable de G0 Emergency Override

- **Sujet** : dans les cas extrêmes où l'IF a été compromise par un attaquant, comment garantir que le message G0 est tout de même exécuté par le noyau de l'IF ?
- **Inclination actuelle du protocole** : la couche protocole impose que les messages G0 aient la plus haute priorité (voir §7.2 / priorité G0 Override P12), mais reconnaît que les seuls moyens au niveau du protocole sont insuffisants lorsque le noyau de l'IF est compromis.
- **Alternatives** : (a) imposition d'un kill-switch au niveau matériel ; (b) confirmation par double signature TPM-quote ; (c) conserver l'imposition au niveau du protocole et laisser le chemin matériel à la liberté d'implémentation de l'écosystème.
- **Statut de résolution** : ouvert ; profondément couplé à la prise de contrôle de terminal des Phase 2 / Phase 3.

### Q3 Calendrier par défaut du PQC

- **Sujet** : quand l'hybride Ed25519 + ML-DSA-65 passe-t-il d'OPTIONAL à MUST ?
- **Inclination actuelle du protocole** : 1.0 ne déclare qu'OPTIONAL (emplacements de négociation PQC en §6.1) ; le calendrier sera fixé après la publication de tous les standards finaux du NIST.
- **Alternatives** : (a) attendre que tous les standards PQC du NIST soient finalisés ; (b) suivre le premier algorithme de signature standardisé ; (c) différencier par niveau (les scénarios à haute sensibilité MUST d'abord).
- **Statut de résolution** : ouvert ; en attente de la progression de la standardisation PQC du NIST.

### Q4 Coopération iFay ↔ iFay inter-Human-Prime (Phase 4/5)

- **Sujet** : lorsque deux iFays appartenant à des HP différents coopèrent, comment le transfert de responsabilité est-il déterminé ?
- **Inclination actuelle du protocole** : 1.0 ne couvre pas ; à fixer en Phase 4 lorsque coFay sera introduit.
- **Alternatives** : (a) l'initiateur porte ; (b) le destinataire porte ; (c) partagé par règles ; (d) les deux HP doivent co-témoigner.
- **Statut de résolution** : ouvert ; requiert une discussion à double voie juridique-protocole.

### Q5 Détermination objective de la déviation Ego

- **Sujet** : la couche protocole devrait-elle spécifier l'ensemble minimal de signaux de décision pour `ego-deviation` ?
- **Inclination actuelle du protocole** : la couche protocole ne définit que la sémantique de `RevokeReason="ego-deviation"` et les conséquences du déclenchement (§EH.1, §3.6 BBS) ; l'ensemble spécifique de signaux de décision est laissé à la liberté d'implémentation.
- **Alternatives** : (a) la couche protocole impose l'ensemble minimal de signaux ; (b) explicitement contraint par le §3.6 Behavior Baseline Service ; (c) conserver l'ouverture actuelle.
- **Statut de résolution** : ouvert ; couplé à la standardisation de la ligne de base Q13.

### Q6 Politique de renouvellement du Mandate

- **Sujet** : le protocole devrait-il interdire toute forme de « renouvellement automatique » ?
- **Inclination actuelle du protocole** : interdire toutes les formes de renouvellement automatique ; chaque renouvellement doit passer par un témoignage explicite du HP (inclination du chapitre 10 de la note de cadrage).
- **Alternatives** : (a) autoriser un « renouvellement automatique limité requérant une pré-signature périodique du HP » ; (b) autoriser le renouvellement automatique aux niveaux à faible risque (G3/G4) ; (c) conserver l'interdiction.
- **Statut de résolution** : ouvert ; en attente de la décision du Protocol Committee.

### Q7 Environnement hors ligne / à réseau faible

- **Sujet** : dans les scénarios de bord où le RR est inaccessible (déconnexion de drone), un mode affaibli « autonomie bornée dans le temps + réconciliation à la reconnexion » est-il autorisé ?
- **Inclination actuelle du protocole** : modéliser explicitement « autonomie bornée dans le temps + réconciliation à la reconnexion » via Endorsed_Mandate (§7.5, §9.8, §4.3 Disconnected) ; les chemins non-Endorsed sont strictement Refus par défaut (voir présomption pessimiste P17.2).
- **Alternatives** : (a) s'appuyer uniquement sur Endorsed_Mandate ; (b) introduire un « cache RR régional » ; (c) Refus par défaut strict sans aucune exception.
- **Statut de résolution** : partiellement résolu (Endorsed_Mandate déjà concrétisé en §7.5) ; la borne supérieure de la politique hors ligne attend la résolution de Q11.

### Q8 « Niveau supplémentaire » du sous-agent

- **Sujet** : le système à cinq paliers de G0 Emergency_Override et G1 Strict / G2 Moderate / G3 Loose / G4 Autonomous est-il suffisant ?
- **Inclination actuelle du protocole** : 1.0 conserve les cinq paliers (§7.1) ; n'introduit pas de paliers intermédiaires comme G2.5.
- **Alternatives** : (a) introduire un palier intermédiaire « semi-autonome + interruptible » ; (b) autoriser les implémentations à définir des sous-niveaux personnalisés mais à les mapper vers l'un des cinq ; (c) introduire des sous-niveaux Endorsement Grades orthogonaux (déjà concrétisés en §7.5).
- **Statut de résolution** : partiellement résolu (les Endorsement Grades se superposent orthogonalement à G1–G4) ; les paliers intermédiaires restent Ouverts.

### Q9 Frontière de la cascade de révocation

- **Sujet** : comment la visibilité du défaut de révocation en cascade de DELEGATE (`cascade=true`) est-elle garantie sous une dérivation multi-niveaux ?
- **Inclination actuelle du protocole** : défaut `cascade=true` (§5.3.5) ; visibilité contrainte par `RevocationVisibilityBudget` (§9.7, révocation en cascade trans-dérivation P14).
- **Alternatives** : (a) différencier le budget par profondeur de l'arbre de dérivation ; (b) conserver un budget unique + double voie push / pull.
- **Statut de résolution** : ouvert ; en attente que les tests de conformité mesurent la visibilité d'un arbre de dérivation profond.

### Q10 Nommage du protocole (Résolu)

- **Sujet** : nommage officiel du protocole.
- **Conclusion de résolution** : le protocole est officiellement nommé **Faying Protocol** (sans abréviation distincte), version `Faying Protocol/1.0`.
- **Statut de résolution** : résolu ; ce sujet demeure comme trace historique et n'est plus ouvert à la discussion.

### Q11 Borne supérieure maximale de durée de vie de l'Endorsement

- **Sujet** : la couche protocole devrait-elle spécifier la borne supérieure dure de `endorsement.endorsed_lifetime` (p. ex. ≤ 12 h) ? Devrait-elle être encore resserrée par niveau ?
- **Inclination actuelle du protocole** : l'Annexe B donne une valeur recommandée (4 h par défaut, borne supérieure souple 12 h, et ne doit pas dépasser `Mandate.not_after − Mandate.not_before` ; voir P16.3 / P16.4) ; la borne supérieure dure attend la résolution RFC.
- **Alternatives** : (a) coder en dur une borne supérieure de 12 h au niveau du protocole ; (b) différencier par niveau (p. ex. G1 ≤ 1 h, G4 ≤ 24 h) ; (c) conserver la valeur recommandée non obligatoire.
- **Statut de résolution** : ouvert ; couplé à la politique hors ligne Q7.

### Q12 Protection contre l'abus du Faying bidirectionnel

- **Sujet** : les `FAYING_REQUEST` initiées par l'iFay devraient-elles être soumises à une limitation de débit obligatoire au niveau du protocole (au plus N fois par minute par paire (HP, IF)) ? La limite de débit devrait-elle être incorporée dans le même budget `ConfirmationRateLimit` ?
- **Inclination actuelle du protocole** : la fréquence de FAYING_REQUEST est incorporée dans le même budget `ConfirmationRateLimit` (voir §5.3.6, §9.10.7, P18.6) ; le dépassement déclenche un abaissement / une suspension automatique selon §9.10.7.
- **Alternatives** : (a) budget indépendant `FayingRequestRateLimit` ; (b) différencier les budgets par niveau ; (c) conserver le partage actuel avec ConfirmationRateLimit.
- **Statut de résolution** : partiellement résolu (le budget partagé par défaut est déjà concrétisé en §9.10.7) ; la borne supérieure de seuil et la question de savoir si le budget devrait être indépendant attendent la résolution RFC.

### Q13 Standardisation de Behavior_Baseline

- **Sujet** : la granularité de calibration de la ligne de base comportementale (par `action` / `scope_used` / `risk_level` / `affected_resources`, ou conjointement multidimensionnelle) devrait-elle être uniformément spécifiée au niveau du protocole ? Ou les implémentations devraient-elles avoir de la liberté tout en exigeant que la calibration de la ligne de base elle-même soit inscrite dans l'Attestation Chain ?
- **Inclination actuelle du protocole** : liberté d'implémentation + calibration de la ligne de base inscrite dans l'Attestation Chain ; les changements de calibration sont traités comme des événements d'audit (§3.6 I-BBS-3 / P18.5).
- **Alternatives** : (a) imposition au niveau du protocole (conjointement multidimensionnelle sur action / scope_used / risk_level / affected_resources) ; (b) conserver la liberté + audit ; (c) introduire un « registre de schémas de ligne de base » pour unifier la calibration.
- **Statut de résolution** : ouvert ; couplé à la détermination de ego-deviation Q5.

### Q14 Critères objectifs de granularité minimale d'Atomic_Action

- **Sujet** : quelle est la détermination objective au niveau du protocole de l'« action minimale indivisible » ? Un « treillis d'actions » devrait-il être introduit pour que `scope.actions` et l'ensemble d'actions côté RP aient une réduction de granularité minimale formalisable ?
- **Inclination actuelle du protocole** : la couche protocole n'impose que « exactement 1 Atomic_Action par appel / `scope.actions` n'autorisant pas les jokers » (P18.2 Atomic_Action_Strict) ; la détermination objective de la granularité minimale est laissée aux RP et au Protocol Committee selon les conventions sectorielles.
- **Alternatives** : (a) introduire un treillis d'actions général inter-RP ; (b) introduire des treillis distincts par secteur de RP (finance / santé / IoT) ; (c) conserver l'ouverture actuelle.
- **Statut de résolution** : ouvert ; discuté conjointement avec l'emplacement d'extension §9.10.8 T7.
