---
title: "Faying Protocol/1.0 — §7 Niveaux d'Autorisation"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: fr
part: "Chapitre 7 sur 11 (corps du protocole)"
---

> Navigation du corps du protocole : [Sommaire](./README.md) | précédent [§6 Cryptographie](./06-Cryptographie.md) | suivant [§8 Cycle de Vie](./08-Cycle-de-Vie.md)

## §7 Niveaux d'Autorisation

Ce chapitre présente la sémantique d'autorisation graduée de Faying Protocol. Faying Protocol n'accepte pas la « délégation uniforme de tous pouvoirs » — chaque Mandate doit déclarer explicitement un niveau, et les trois colonnes `(autonomie, exigence de présence, exigence de message)` de chaque niveau portent une sémantique précise au niveau du protocole ; les changements de niveau déclenchés par événement sont exhaustivement codés en dur sous la matrice §7.2 ; §7.3 verrouille le principe de monotonie « perte de présence → doit resserrer » ; §7.4 donne les différences obligatoires de la couche message ; §7.5 introduit les sous-niveaux Endorsement Grades superposés au-dessus de G1–G4 comme couche de permission d'autonomie hors ligne.

> **Relation orthogonale entre G0 et G1–G4** : G0 Emergency Override n'est **pas** dans le spectre continu de niveaux G1 ↔ G4 ; c'est un **canal de surpassement orthogonal**. G1–G4 expriment « l'axe continu de la force d'autonomie » ; G0 est le canal d'urgence permettant au Human Prime de reprendre unilatéralement le contrôle, manifesté uniquement aux niveaux de la priorité de la file d'événements et de l'état terminal (Suspended) ; il ne participe pas à la sémantique « rehaussement / abaissement ». Toute implémentation qui traite G0 comme « un palier continu plus strict que G1 » est incohérente avec la sémantique du protocole.

> **Référence des budgets numériques** : les nombres `max-staleness` de ce chapitre (G1=5s / G2=60s / G3=5min / G4=30min) correspondent un à un à l'entrée `Presence max-staleness (G1..G4)` de l'Annexe B « Budgets de paramètres par défaut » ; la colonne « Par défaut » de l'Annexe B est la valeur de référence utilisée dans ce chapitre, et la colonne « Borne supérieure » est la borne supérieure dure au niveau du protocole à l'intérieur de laquelle les implémentations peuvent ajuster.

### §7.1 Définitions précises des niveaux

| Niveau | Autonomie | Exigence de présence | Exigence de message | Adapté à |
| --- | --- | --- | --- | --- |
| **G0 Emergency Override** | S.O. | S.O. | Initié unilatéralement par le HP ; seul effet : pousser immédiatement le Mandate cible vers Suspended | Reprise d'urgence |
| **G1 Strict** | Très faible | Présence continue en temps réel (face / WebAuthn UV, max-staleness ≤ 5 s) | Chaque appel externe doit porter un PresenceSignal ≤ 5 s | Opérations irréversibles (virements, signature, suppression de base de données, commandes de terminal à privilège élevé) |
| **G2 Moderate** | Moyenne | Présence au niveau de la tâche (présence fraîche requise avant les sous-tâches sensibles, max-staleness ≤ 60 s) | PresenceSignal avant les actions sensibles | Opérations d'agent à fréquence moyenne (réservation, replanification, soumission de formulaires) |
| **G3 Loose** | Élevée | Sollicitation aux étapes clés (intent-ticket avant les points de décision clés) | intent-ticket à usage unique porté aux étapes clés | Agent à long terme à faible risque (tri des courriels, calendrier) |
| **G4 Autonomous** | Très élevée | Heartbeat périodique (presence-heartbeat, max-staleness ≤ 30 min) | Maintien du heartbeat + retour d'audit périodique | Autonomie de routine dans le périmètre |

> **Choix de conception** : G0 n'est pas dans le spectre continu G1 ↔ G4 ; c'est un **canal de surpassement orthogonal** — son unique but est de permettre au HP de migrer immédiatement le Mandate cible vers Suspended ; il ne participe pas aux comparaisons numériques de l'axe d'autonomie.

**Convention de l'axe d'autonomie** : `G0 < G1 < G2 < G3 < G4` (valeurs plus grandes = autonomie plus élevée). Toutes les décisions « rehaussement / abaissement » dans le reste de ce chapitre reposent sur des comparaisons de taille entre `target.autonomy` et `current.autonomy` ; G0 ne participe pas à cette comparaison d'axe — il migre unilatéralement vers Suspended via la dernière ligne de la matrice §7.2.

**Exigence de présence alignée sur les types de Presence_Signal** (voir la table des signal-types §3.2) :

- **G1 Strict** : signaux typiques `face-continuous` ou `webauthn-uv-fresh`, `max_staleness_ms = 5_000` ;
- **G2 Moderate** : signal typique `fingerprint-tap` (avant les sous-tâches sensibles), `max_staleness_ms = 60_000` ;
- **G3 Loose** : signal typique `intent-ticket` (consommation à usage unique aux étapes clés) ; aucune borne supérieure périodique de max-staleness, mais chaque étape clé doit avoir un intent-ticket frais ;
- **G4 Autonomous** : signal typique `presence-heartbeat-only`, `max_staleness_ms = 1_800_000` (30 min).

**Différences d'exigence de message (référencées avec l'inventaire de messages §5)** :

- **GRADE_SWITCH en direction de rehaussement à G1 / G2** : `human_witness` est obligatoire (MUST), la forme de témoignage par défaut étant une assertion WebAuthn UV (voir suites d'algorithmes §6.1) ;
- **G3 / G4** : les rehaussements vers ces paliers (qui relèvent encore du chemin « relâcher l'autonomie » même lorsque target.autonomy est inférieure au niveau source) requièrent aussi `human_witness` ; ce n'est que sur le chemin d'« abaissement actif » que `human_witness` se dégrade en MAY ;
- **G0** : ne peut être initié unilatéralement que par le HP (un G0 substitué par IF / MS / SA est rejeté avec `E_PROTOCOL`) ; requiert un `human_witness` vérifiable ; les messages G0 doivent être inscrits dans l'Attestation Chain et la file de poussée du Revocation Registry à la plus haute priorité.

### §7.2 Matrice des conditions de déclenchement

Le tableau ci-dessous est la matrice de transition d'état 6×4 pour 6 classes d'événements déclencheurs × 4 niveaux courants non-G0 ; c'est la correspondance obligatoire événement → état terminal au niveau du protocole ; aucun chemin de transition hors de ce tableau n'existe.

| Événement | G1 courant | G2 courant | G3 courant | G4 courant |
| --- | --- | --- | --- | --- |
| Fraîcheur de présence expirée | → Suspended | → G3 Loose | → Suspended | → Suspended |
| Rehaussement actif par le HP | — | → G1 (témoignage requis) | → G2 / G1 (témoignage requis) | → G3 / G2 / G1 (témoignage requis) |
| Abaissement actif par le HP | → G2 | → G3 | → G4 | — |
| Déviation Ego détectée | → Revoked | → Revoked | → Revoked | → Revoked |
| Registre de révocation inaccessible | Rejeter l'appel | Rejeter l'appel | Rejeter l'appel | Rejeter l'appel |
| G0 Override | → Suspended | → Suspended | → Suspended | → Suspended |

**Compléments sémantiques de la matrice** :

- **Asymétrie de la ligne « fraîcheur de présence expirée »** : G2 → G3 est l'« abaissement léger » autorisé (encore sur la branche Active de la machine à états) ; G1 / G3 / G4 → Suspended expriment trois logiques de décision différentes — G1 parce que sous des scénarios à haute sensibilité « pas de présence fraîche → aucune action permise » ; G3 parce que sous les scénarios intent-ticket le heartbeat n'est pas la base de présence principale, et l'absence continue de signaux frais aux étapes clés est traitée comme non fiable ; G4 parce que le heartbeat est sa seule base de présence, et la perte de heartbeat est absorbée directement dans Suspended (cohérent avec la clause d'exception §7.3).
- **Ligne « rehaussement actif par le HP »** : le « — » à G1 signifie que G1 est déjà le palier le plus strict sans espace de rehaussement supérieur ; les autres autorisent des rehaussements à usage unique sur 1 à 3 paliers, tous requérant `human_witness` (voir §7.4).
- **Ligne « abaissement actif par le HP »** : le « — » à G4 signifie que G4 est déjà le palier le plus souple sans espace d'abaissement plus souple ; la direction d'abaissement ne requiert pas `human_witness`, mais les notifications RR et les enregistrements de chaîne AC restent obligatoires.
- **Ligne « déviation Ego détectée »** : les quatre paliers entrent uniformément dans l'état terminal Revoked (Revoked est un état absorbant ; voir §8 / Property 10) ; la logique de décision qui déclenche cette ligne est donnée conjointement par §3.6 Behavior Baseline Service et §9.10.6 T5.
- **Ligne « registre de révocation inaccessible »** : les quatre paliers « rejettent l'appel » uniformément ; ce n'est pas une transition d'état — c'est le chemin de convergence Refus par défaut pour un appel unique (code d'erreur `E_RR_UNAVAILABLE`) ; le Mandate lui-même demeure au niveau courant ; cette ligne est cohérente avec l'invariant RR §3.4 I-RR-2.
- **Ligne « G0 Override »** : initiée unilatéralement par le HP ; les quatre paliers sont uniformément absorbés dans Suspended ; traitée à la plus haute priorité sur la file d'événements (tout événement en attente cède).

### §7.3 Principe de monotonie d'abaissement

> **Sans présence, plus strict** — c'est la forme contre-intuitive mais obligatoire de la Dégradation gracieuse : la perte du signal de présence signifie « la vue humaine se rétrécit », donc l'autonomie doit **se resserrer**, non se relâcher. En termes numériques : perte de présence → la valeur du niveau diminue (plus strict).

Expression formelle (alignée sur P11) :

```
∀ M ∈ ActiveMandates. PresenceState(M).stale = true ⟹
    next_state(M) ∈ { Degraded(g'), Suspended }
    where g'.autonomy < M.grade.autonomy
```

C'est-à-dire : après une perte de présence, la transition d'état suivante doit migrer vers un niveau d'`autonomie strictement inférieure` (nombre plus petit, sécurité plus élevée), ou migrer directement vers Suspended ; **rester au niveau d'origine est interdit, basculer vers une autonomie supérieure est interdit**.

**Exceptions (contraintes d'état absorbant)** :

- **Perte de heartbeat G4 Autonomous → Suspended directement** : parce que G4 est déjà le palier d'autonomie la plus élevée sans palier plus strict disponible, l'absorption directe dans Suspended est une contrainte dure au niveau du protocole (cohérent avec la colonne G4 de la première ligne de la matrice §7.2).
- **État `Degraded` dépassant `MaxDegradedDuration` → Suspended directement** : évite que la « résidence à long terme dans un sous-palier » devienne un « chemin de relâchement » implicite ; le seuil spécifique est dans l'Annexe B `MaxDegradedDuration`.

### §7.4 Différences d'exigence des messages de changement de niveau

Le tableau ci-dessous donne, pour les trois directions de changement, les différences de champs obligatoires au niveau message ; si une entrée « MUST » manque, le message de changement correspondant est rejeté uniformément avec `E_PROTOCOL` ou `E_HUMAN_WITNESS_REQUIRED` (voir la table des codes d'erreur §5.4).

| Direction de changement | human_witness | Notification RR | Enregistrement de chaîne AC |
| --- | --- | --- | --- |
| Rehaussement (autonomie supérieure) | MUST | MUST | MUST |
| Abaissement (autonomie inférieure) | MAY | MUST | MUST |
| Emergency Override | MUST | MUST (poussée prioritaire) | MUST |

**Compléments sémantiques de la couche message** :

- **Direction de rehaussement** : lorsque `GRADE_SWITCH.target_grade.autonomy > current_grade.autonomy`, `human_witness` est obligatoire ; signature manquante ou invalide → `E_HUMAN_WITNESS_REQUIRED` (code d'erreur 1010). La contrainte de cette ligne s'aligne pleinement sur la Requirement 6.1.
- **Direction d'abaissement** : `human_witness` se dégrade en MAY, mais les notifications RR et les enregistrements de chaîne AC restent obligatoires — les abaissements sont aussi une classe de changements d'état qui requièrent audit et observabilité ; l'« abaissement silencieux » est interdit.
- **Emergency Override (G0)** : `human_witness` est obligatoire ; les notifications RR doivent être poussées à la plus haute priorité (cohérent avec le champ de priorité du canal de poussée RR §3.4) ; les enregistrements de chaîne AC sont écrits à la plus haute priorité.
- **Sémantique au niveau du protocole de « enregistrement de chaîne AC obligatoire »** : chaque GRADE_SWITCH (rehaussement / abaissement / G0 confondus) produit un AttestationEvent avec `event_type = "grade-switch"` (voir §3.3), ajouté par le MS immédiatement après l'achèvement du changement ; absence → traité comme une lacune d'audit, déclenchant `E_ATTESTATION_INVALID`.

### §7.5 Sous-niveaux Endorsement Grades

> **Posture de conception** : l'Endorsement n'est pas un nouveau niveau mais **une « couche de permission d'autonomie hors ligne » superposée au-dessus de G1–G4**. Chaque niveau non-G0 (c.-à-d. G1–G4) peut avoir une surcouche `endorsement`, permettant au Mandate d'opérer de façon autonome dans une enveloppe contrainte pendant une déconnexion physique (jugée selon §3.5 Liveness Channel et la machine à états §4.3). G0 Emergency Override ne permet pas de surcouche d'endossement — c'est le canal permettant au HP de reprendre unilatéralement le contrôle, mutuellement exclusif avec la sémantique d'« autonomie hors ligne ».

**Sémantique de surcouche** :

| Niveau principal | Endossement autorisé | Effet par défaut de l'endossement |
| --- | --- | --- |
| G0 Emergency Override | **Non autorisé** | — |
| G1 Strict | Autorisé | Pendant une déconnexion physique → Disconnected ; endorsed_scope est typiquement le sous-ensemble minimal d'actions à haute sensibilité ; endorsed_grade par défaut = G1 (pas de descente) |
| G2 Moderate | Autorisé | endorsed_grade par défaut = G2 ; usage typique : tâches planifiées / achèvement de transactions déjà entamées |
| G3 Loose | Autorisé | endorsed_grade par défaut = G3 ; usage typique : tri d'informations / opérations de lecture pendant la continuation hors ligne |
| G4 Autonomous | Autorisé | endorsed_grade par défaut = G4 ; usage typique : agence hors ligne de longue durée + réconciliation par lots après reconnexion |

**Contraintes dures des sous-niveaux** (verrouillées avec la Requirement 11.2 ; en fin de compte verrouillées par P16.3) :

- **convergence du périmètre** : `endorsement.endorsed_scope ⊆ Mandate.scope` ;
- **convergence du niveau** : `endorsement.endorsed_grade.autonomy ≤ Mandate.grade.autonomy` (c.-à-d. endorsed_grade n'est **pas plus faible** que le niveau principal en autonomie, sécurité ≥ niveau principal) ;
- **durée de vie finie** : `endorsement.endorsed_lifetime` doit être fini ; `∞` ou manquant est interdit, et `≤ (Mandate.not_after − Mandate.not_before)` ; l'Annexe B donne en outre la borne supérieure souple `Endorsed_Lifetime` (4 h par défaut, borne supérieure 12 h) ;
- **politique de révocation hors ligne énumérable** : `endorsement.offline_revocation_policy ∈ {"stop-and-audit", "stop-only", "graceful-stop"}` ; par défaut `stop-and-audit`.

Si une contrainte dure échoue, BOOTSTRAP / DELEGATE est rejeté uniformément avec `E_ENDORSEMENT_INVALID` (code d'erreur 1013) (voir §5.4) ; sur DELEGATE, en outre, `child.endorsement` doit converger au sein de `parent.endorsement` — c'est-à-dire que les endorsed_scope / endorsed_grade / endorsed_lifetime du Mandate enfant ne doivent pas dépasser les champs correspondants du Mandate parent.

**Coordination avec la machine à états de déconnexion** (voir §4.3, §8.4, §9.8) :

- Lorsque `PresenceState.stale = true` et que le Mandate est un Endorsed_Mandate → `Active → Disconnected` (le chemin non-Endorsed va directement → Suspended) ;
- Pendant Disconnected, l'iFay est autorisée à effectuer des actions de dimension D uniquement dans `endorsement.endorsed_scope`, contraintes par `endorsement.endorsed_grade` ;
- Une fois `endorsement.endorsed_lifetime` expiré, dépassement de délai léger immédiatement → Disconnected → Revoked, même si l'iFay reste physiquement déconnectée (Requirement 11.3 clause 3 « contrainte dure de dépassement de délai léger ») ;
- Le point terminal porteur de responsabilité est toujours l'`issuer` du Mandate (Human Prime), non changé par l'existence de l'endossement (voir P16.5 Endorsement_Accountability_Invariant et Requirement 11.4).

**Exclusion mutuelle entre Endorsement et G0** : G0 Emergency Override est le canal permettant au HP de reprendre unilatéralement le contrôle ; sa sémantique vise l'état Suspended (« arrêter immédiatement toutes les actions de dimension D »). La sémantique de l'Endorsement vise « le sous-ensemble d'actions de dimension D autorisées pendant une déconnexion physique ». Les deux sont des événements mutuellement exclusifs sur la machine à états — une fois G0 déclenché, le Mandate cible est immédiatement absorbé dans Suspended ; pendant Suspended, le Mandate n'applique plus les règles de passage de dimension D de l'endossement (même si l'endossement n'a pas encore atteint son point de dépassement de délai léger de durée de vie).
