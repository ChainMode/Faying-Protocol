---
title: "Faying Protocol/1.0 — Annexe A Alignement Terminologique (aide-mémoire)"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: fr
part: "Annexe A (référence normative)"
---

> Navigation du corps du protocole : [Sommaire](./README.md) | précédent [§11 Questions Ouvertes](./11-Questions-Ouvertes.md) | suivant [Annexe B Budgets de Paramètres par Défaut](./Annexe-B-Budgets-de-Parametres-par-Defaut.md)

## Annexe A Aide-mémoire d'alignement terminologique

> Cette annexe est cohérente avec le glossaire du référentiel des exigences et l'Annexe A du référentiel de conception ; les noms de systèmes apparaissant dans les sous-clauses EARS doivent être définis ici avant usage. L'annexe est organisée en cinq catégories — « Rôles et entités / Composants du protocole / Objets de données du protocole / Niveaux et politiques / Budgets par défaut » — pour la commodité des renvois.

### A.1 Rôles et entités

| Terme du protocole (anglais) | Terme de la note de cadrage | Relation / note |
| --- | --- | --- |
| Human Prime (HP) | Human Prime (人类原型) | Synonyme ; l'unique point terminal ultime porteur de responsabilité et détenteur du pouvoir de révocation de la relation Faying ; aussi la seule entité qui peut donner un acquittement explicite des changements d'état Faying |
| iFay Instance (IF) | iFay Instance (iFay 实例) | Synonyme ; l'entité agente mandatée, identifiée de façon unique par FayID ; ne détient pas le pouvoir de révoquer son propre Mandate ; tous les changements d'état sont conditionnés par l'acquittement explicite du HP |
| Supervisory Agent (SA) | Supervisory Agent | Une classe de régulateur distincte du Prime et reconnaissable au niveau du protocole ; ne détient pas le pouvoir de révocation ; ne peut se substituer au HP pour compléter l'acquittement Faying |
| Relying Party (RP) | Relying Party (受调用方) | Le terminal, l'application ou le service appelé par l'iFay |
| Presence Device (PD) | Presence Device (在场设备) | Matériel portant les identifiants WebAuthn / FIDO2 et les capacités biométriques ; la source physique des signaux de présence |

### A.2 Composants du protocole

| Terme du protocole (anglais) | Abrév. | Description |
| --- | --- | --- |
| Mandate Service | MS | Le service logique qui émet / renouvelle / abaisse / révoque les Mandate pour le compte du HP (voir §3.1) |
| Presence Channel | PC | Le flux de présence à faible latence et anti-rejeu du PD vers le MS (voir §3.2) |
| Attestation Chain | AC | La chaîne de signatures traçable à rebours formée par toutes les actions d'émission HP → MS → IF → IF dérivé (voir §3.3) |
| Revocation Registry | RR | Service d'état de révocation en temps réel (voir §3.4) |
| Liveness Channel | LC | Flux de détection de déconnexion (incluant déconnexion réelle et déconnexion perçue) (voir §3.5, §9.9) |
| Behavior Baseline Service | BBS | Service statistique maintenant la ligne de base comportementale (HP, IF) (voir §3.6) |

### A.3 Objets de données du protocole

| Terme du protocole (anglais) | Terme de la note de cadrage | Description |
| --- | --- | --- |
| Mandate | Mandate (授权令) | Un nouveau concept au niveau du protocole ; porte les champs `(issuer, subject, scope, grade, presence_req, not_before, not_after, attestation, signature, endorsement?)` (voir §4.1 / §4.2) |
| Endorsed_Mandate | Endorsed Mandate (背书式授权) | Un sous-type de Mandate ; déclare explicitement `endorsement = (enabled, endorsed_scope ⊆ scope, endorsed_grade.autonomy ≤ grade.autonomy, endorsed_lifetime, offline_revocation_policy)`, permettant à l'IF d'opérer de façon autonome dans une enveloppe contrainte pendant une déconnexion physique ; le point terminal porteur de responsabilité est toujours le HP (voir §7.5, P16.x) |
| PresenceSignal | Presence Signal (在场信号) | Une assertion de présence physique produite par le PD et vérifiable par le MS |
| Attestation | Attestation (证言) | Porteur unifié d'assertion vérifiable (WebAuthn / TPM-quote / Platform-keystore / Self-signed) |
| FayID | FayID | L'identité unique unifiée de l'iFay au sein du cadre iFay (de type ULID) |
| Faying_State | Faying State (受控状态) | L'état comportemental dans lequel se trouve l'IF lorsque le Mandate est en Active / Degraded / Disconnected |
| Rogue_Fay | Rogue Fay (脱离状态) | L'état comportemental dans lequel se trouve l'IF lorsque le Mandate est en Unpaired / Revoked ou absent ; binaire mutuellement exclusif avec Faying_State (P15). **Note** : `Suspended` n'est *pas* classé comme Rogue_Fay — c'est une « Faying State en pause » (la relation de supervision persiste, les métadonnées du Mandate sont conservées, et le HP peut le reprendre explicitement sans nouveau BOOTSTRAP) ; il ne partage avec Rogue que l'interdiction de dimension D comme conséquence comportementale ; voir la table de correspondance §4.3 / §8.2 |
| Faying_Initiation | Bidirectional Faying Initiation (双向 Faying 发起) | L'initiation d'une relation Faying (établissement ou ajustement) peut être initiée soit par le HP (HP-initiated) soit par l'IF sollicitant un Faying auprès du HP (IF-initiated / FAYING_REQUEST) ; la condition d'effectivité finale est que le HP donne un acquittement explicite et vérifiable (voir §5.3.6, P16.6) |
| Behavior_Baseline | Behaviour Baseline (行为基线) | Le profil comportemental cumulatif (HP, IF) maintenu par le BBS, utilisé pour détecter une déviation soudaine (voir §3.6, P18.5) |
| Atomic_Action | Atomic Action (原子动作) | La plus petite unité de déclaration indivisible que l'IF exécute vers l'extérieur ; un appel correspond à exactement 1 Atomic_Action ; le regroupement est interdit (voir P18.2) |
| Disclosure_Report | Disclosure Report (披露报文) | Le message structuré que l'IF utilise lors du compte rendu ou de la demande de confirmation ; les `mandatory_fields` sont obligatoirement analysables (voir §5.3.7, P18.3) |
| Ego | Ego (自我边界) | Synonyme ; utilisé pour la décision `ego-deviation` (voir §3.6, §9.10.4) |
| Human View | Human View (人类视野) | Cadre de valeurs ; Faying Protocol en est l'incarnation au niveau du protocole (chapitre 11 de la note de cadrage) |

### A.4 Niveaux et politiques

| Terme du protocole (anglais) | Description |
| --- | --- |
| Authorization_Grade (Grade) | Niveau d'autorisation, valeur `G0..G4` (voir §7) |
| G0 Emergency_Override | Niveau de reprise d'urgence ; rappel forcé unilatéral du HP (voir §7.1, P12) |
| G1 Strict | Le palier le plus strict ; le niveau par défaut des actions à haute sensibilité |
| G2 Moderate | Palier moyen |
| G3 Loose | Palier souple |
| G4 Autonomous | Le palier le plus autonome ; la perte de heartbeat G4 → Suspended directement (voir §7.3) |
| PresenceRequirement | Exigence de présence ; le triplet `(signal_types, max_staleness_ms, on_loss)` lié au niveau |
| Scope | Périmètre d'autorisation ; l'ensemble de moindre privilège à déclaration explicite `(domains, actions, terminals?, budget?)` |

### A.5 Budgets par défaut (valeurs détaillées en Annexe B)

| Terme du protocole (anglais) | Brève description |
| --- | --- |
| MaxMandateLifetime | Durée de vie maximale d'un seul Mandate (24 h par défaut, borne supérieure 30 j) |
| BootstrapTimeout | Délai d'attente du témoignage du HP par BOOTSTRAP / FAYING_REQUEST (60 s par défaut) |
| RevocationVisibilityBudget | Budget pour que la révocation soit visible sur le réseau RR (1 s par défaut) |
| StaleBudget | Seuil de rejet pour RR inaccessible (5 s par défaut) |
| HumanReachabilityBudget | Seuil auquel l'inaccessibilité du HP déclenche un Revoke automatique (30 min par défaut) |
| LivenessDetectionBudget | Borne supérieure de la fenêtre de détection de déconnexion ; resserrée de façon monotone par niveau (voir Annexe B, P17.3) |
| AttentionDriftThreshold | Seuil auquel l'inactivité de la vue du HP déclenche une « perte d'attention » ; resserré par niveau (voir Annexe B, P18.4) |
| ConfirmationRateLimit | Borne supérieure des requêtes de confirmation poussées vers le HP par unité de temps ; le dépassement déclenche un abaissement / une suspension automatique (voir Annexe B, P18.6) |
| MaxDegradedDuration | Durée maximale de l'état Degraded (5 min/niveau par défaut) |
