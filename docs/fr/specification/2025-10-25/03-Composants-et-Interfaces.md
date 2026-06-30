---
title: "Faying Protocol/1.0 — §3 Composants et Interfaces"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: fr
part: "Chapitre 3 sur 11 (corps du protocole)"
---

> Navigation du corps du protocole : [Sommaire](./README.md) | précédent [§2 Architecture](./02-Architecture.md) | suivant [§4 Modèles de Données](./04-Modeles-de-Donnees.md)

## §3 Composants et Interfaces

Ce chapitre présente les 6 composants centraux de Faying Protocol au niveau du protocole : **Mandate Service (MS) / Presence Channel (PC) / Attestation Chain (AC) / Revocation Registry (RR) / Liveness Channel (LC) / Behavior Baseline Service (BBS)**. Pour chaque composant, le chapitre fournit :

- **Responsabilités** : la position et la frontière du composant dans le protocole ;
- **Squelette d'interface TypeScript** : une vue lisible par l'humain (**non normative**) ; les définitions faisant autorité résident en §4 Modèles de Données et §5 Messages du Protocole ;
- **Invariants** : contraintes dures au niveau du protocole devant toujours tenir ; chaque invariant est traçable vers au moins une sous-clause EARS du §Exigences.

> **Note de traçabilité EARS** : chaque invariant de ce chapitre est suivi d'une ligne `Trace:` qui énumère les identifiants des sous-clauses EARS correspondantes (issues du référentiel des exigences) sous la forme `R<exigence>.<critère>.<clause>`.

### §3.0 Déclarations anticipées de types partagés (non normatif)

Afin que les blocs d'interface TypeScript de ce chapitre puissent passer indépendamment `tsc --noEmit`, le bloc de code suivant déclare par anticipation, sous une forme de squelette minimal, les types de support référencés dans ce chapitre ; les **définitions faisant autorité** de ces types résident en §4 Modèles de Données.

```typescript
// §3.0 — Déclarations anticipées non normatives.
// Les définitions faisant autorité résident en §4 Modèles de Données.

export type IsoTime = string;
export type MandateId = string;
export type FayID = string;
export type HumanPrimeID = string;
export type DeviceId = string;

export type AuthorizationGrade = "G0" | "G1" | "G2" | "G3" | "G4";

export interface Scope {
  readonly domains: readonly string[];
  readonly actions: readonly string[];
  readonly terminals?: readonly string[];
  readonly budget?: ResourceBudget;
}

export interface ResourceBudget {
  readonly max_calls_per_minute?: number;
  readonly max_bytes_per_call?: number;
}

export interface Grade {
  readonly value: AuthorizationGrade;
  readonly autonomy: number; // valeur plus grande = autonomie plus élevée (G0 la plus basse, G4 la plus haute)
}

export interface PresenceRequirement {
  readonly signal_types: readonly PresenceSignalType[];
  readonly max_staleness_ms: number;
  readonly on_loss: "downgrade" | "suspend";
}

export type PresenceSignalType =
  | "webauthn-uv-fresh"
  | "face-continuous"
  | "fingerprint-tap"
  | "presence-heartbeat-only"
  | "intent-ticket";

export interface SignatureBundle {
  readonly alg: string;
  readonly hash: string;
  readonly sig: Uint8Array;
  readonly chain?: readonly SignatureBundle[];
}

export interface Endorsement {
  readonly enabled: boolean;
  readonly endorsed_scope: Scope;
  readonly endorsed_grade: Grade;
  readonly endorsed_lifetime_ms: number;
  readonly offline_revocation_policy:
    | "stop-and-audit"
    | "stop-only"
    | "graceful-stop";
  readonly start_at?: IsoTime;
}

export interface Mandate {
  readonly mandate_id: MandateId;
  readonly issuer: HumanPrimeID;
  readonly subject: FayID;
  readonly scope: Scope;
  readonly grade: Grade;
  readonly presence_req: PresenceRequirement;
  readonly device_id?: DeviceId;
  readonly not_before: IsoTime;
  readonly not_after: IsoTime;
  readonly parent?: MandateId;
  readonly endorsement?: Endorsement;
  readonly signature_bundle: SignatureBundle;
}

export interface PresenceSignal {
  readonly mandate_id: MandateId;
  readonly signal_type: PresenceSignalType;
  readonly nonce: Uint8Array;
  readonly produced_at: IsoTime;
  readonly device_attestation: Uint8Array;
  readonly challenge?: Uint8Array;
  readonly challenge_response?: Uint8Array;
  readonly signature_bundle: SignatureBundle;
}

export interface PresenceVerdict {
  readonly accepted: boolean;
  readonly verdict: "ok" | "stale" | "replay" | "attestation-invalid";
  readonly recommended_next_grade?: AuthorizationGrade;
}

export interface PresenceAck {
  readonly accepted: boolean;
  readonly mandate_id: MandateId;
  readonly observed_at: IsoTime;
}

export interface PresenceState {
  readonly mandate_id: MandateId;
  readonly last_freshness: IsoTime;
  readonly stale: boolean;
  readonly active_signal_types: readonly PresenceSignalType[];
}

export interface BootstrapRequest {
  readonly subject: FayID;
  readonly scope: Scope;
  readonly grade: Grade;
  readonly presence_req: PresenceRequirement;
  readonly not_before: IsoTime;
  readonly not_after: IsoTime;
  readonly human_witness: Uint8Array; // assertion WebAuthn
  readonly endorsement?: Endorsement;
  readonly faying_request_ref?: string;
}

export interface GradeSwitchRequest {
  readonly mandate_id: MandateId;
  readonly target_grade: Grade;
  readonly current_grade: Grade;
  readonly human_witness?: Uint8Array;
  readonly reason: string;
}

export interface DelegateRequest {
  readonly parent_mandate_id: MandateId;
  readonly child_subject: FayID;
  readonly child_scope: Scope;
  readonly child_grade: Grade;
  readonly device_id?: DeviceId;
  readonly not_before: IsoTime;
  readonly not_after: IsoTime;
}

export type RevokeReason =
  | "human-initiated"
  | "expiry"
  | "task-completed"
  | "human-prime-unreachable"
  | "ego-deviation"
  | "fay-credential-invalid"
  | "human-prime-credential-invalid"
  | "regulatory-order"
  | "terminal-disconnected";

export interface RevokeRequest {
  readonly mandate_id: MandateId;
  readonly reason: RevokeReason;
  readonly cascade: boolean;
  readonly human_witness?: Uint8Array;
}

export interface RevokeReceipt {
  readonly mandate_id: MandateId;
  readonly reason: RevokeReason;
  readonly revoked_at: IsoTime;
  readonly cascade_targets: readonly MandateId[];
  readonly signature_bundle: SignatureBundle;
}

export interface RevocationStatus {
  readonly mandate_id: MandateId;
  readonly revoked: boolean;
  readonly revoked_at?: IsoTime;
  readonly reason?: RevokeReason;
  readonly observed_at: IsoTime;
}

export interface ScopeFilter {
  readonly subjects?: readonly FayID[];
  readonly issuers?: readonly HumanPrimeID[];
}

export interface Subscription {
  readonly subscription_id: string;
  readonly close: () => void;
}

export interface AtomicAction {
  readonly action: string;
  readonly target?: string;
  readonly sensitivity: "low" | "normal" | "high" | "critical";
}
```

### §3.1 Mandate Service (MS)

**Responsabilités** : gère le cycle de vie complet des Mandate pour le compte du Human Prime (émission / renouvellement / abaissement / révocation) ; l'unique point d'entrée légitime des Faying Actions.

**Interface (non normative)** :

```typescript
export interface MandateService {
  /** Unique point d'entrée légitime des Faying Actions */
  bootstrap(req: BootstrapRequest): Promise<Mandate>;

  /** Calibration du signal de présence ; renvoie si le Mandate courant reste valide / doit être abaissé */
  verifyPresence(
    mandateId: MandateId,
    signal: PresenceSignal
  ): Promise<PresenceVerdict>;

  /** Changement de niveau : les rehaussements requièrent le témoignage du HP ; les abaissements peuvent être déclenchés automatiquement par le protocole */
  switchGrade(req: GradeSwitchRequest): Promise<Mandate>;

  /** Dérivation multi-appareils : dérive un Mandate enfant d'un Mandate parent, avec scope ⊆ scope du parent, grade ≤ grade du parent */
  delegate(req: DelegateRequest): Promise<Mandate>;

  /** Révocation symétrique : l'accessibilité doit être ≥ celle de l'amorçage */
  revoke(req: RevokeRequest): Promise<RevokeReceipt>;
}
```

**Invariants clés** :

- **I-MS-1 (Bootstrap ancré au HP)** : un demandeur de `bootstrap()` doit porter une attestation HP vérifiable (forme par défaut : assertion de présence utilisateur WebAuthn) ; aucun chemin légitime n'existe pour un « MS décidant lui-même de l'amorçage » ni pour IF / SA de se substituer au HP pour compléter l'acquittement.
  - **Trace** : `R1.3.1` (l'initiation par le HP doit présenter un acquittement explicite vérifiable), `R1.3.5` (aucun chemin fourni pour IF / MS / SA de se substituer au HP pour compléter l'acquittement Faying).

- **I-MS-2 (témoignage du HP obligatoire sur les rehaussements)** : `switchGrade()` doit porter un `human_witness` vérifiable si et seulement si `target.autonomy > current.autonomy` ; signature manquante ou invalide → rejet avec `E_HUMAN_WITNESS_REQUIRED`, et l'IF ne doit pas initier de rehaussement de niveau de façon autonome.
  - **Trace** : `R7.1.1` (convergence `child.scope ⊆ parent.scope` — implique la contrainte de non-expansion au sein de la sémantique de montée/descente de niveau, cohérente avec le principe de monotonie d'abaissement), `R5.1.1` (préalable d'acceptation fondé sur `presence_req`, base sur laquelle la RP vérifie après que `switchGrade` a écrit le champ `presence_req`).
  - Note : cet invariant est aussi couvert de façon autoritaire par R6.1 (les rehaussements doivent porter le témoignage du HP) ; la traçabilité EARS listée dans ce chapitre ne retient que les clauses pertinentes au sein de l'ensemble des Requirements déclaré par cette tâche.

- **I-MS-3 (budget de visibilité de révocation)** : une fois un `revoke()` publié par le RR, tous les appels `query()` RP ultérieurs doivent renvoyer `revoked` dans le délai `RevocationVisibilityBudget` (1 s par défaut, resserré par niveau ; voir §6 / Annexe B) ; le MS ne doit pas fournir de chemin de « passage optimiste ».
  - **Trace** : `R4.2.1` (budget de visibilité de révocation ≤ `RevocationVisibilityBudget`), `R4.2.4` (pas de confirmation dans `StaleBudget` → Refus par défaut).

- **I-MS-4 (périmètre / niveau dérivés strictement convergents)** : un Mandate enfant émis par `delegate()` doit satisfaire `child.scope ⊆ parent.scope` ∧ `child.grade.autonomy ≤ parent.grade.autonomy` ; toute expansion dans l'une ou l'autre direction est rejetée avec `E_PROTOCOL`, et le `signature_bundle.chain` du Mandate enfant doit porter le contreseing du Mandate parent.
  - **Trace** : `R7.1.1` (périmètre enfant ⊆ périmètre parent), `R7.1.2` (autonomie enfant ≤ autonomie parent).

### §3.2 Presence Channel (PC)

**Responsabilités** : délivre de façon sécurisée, à faible latence et résistante au rejeu, les signaux de présence physique produits par les Presence Devices vers le MS, où le MS les transforme en verdicts de « calibration continue » sur le Mandate courant.

**Types de signaux (alignés sur les niveaux §7)** :

| Type | Force | Niveau applicable | Chemin d'abaissement en cas d'échec |
| --- | --- | --- | --- |
| `webauthn-uv-fresh` | Forte | G1 Strict | Échec → Suspended |
| `face-continuous` | Forte | G1 Strict | Échec → abaissement vers G2 Moderate |
| `fingerprint-tap` | Moyenne | G2 Moderate | Échec → abaissement vers G3 Loose |
| `presence-heartbeat-only` | Faible | G3 Loose / G4 Autonomous | Échec → Suspended |
| `intent-ticket` | À usage unique | Complément trans-niveaux | Usage unique ; n'affecte pas le niveau principal |

**Interface (non normative)** :

```typescript
export interface PresenceChannel {
  /** Initié par le PD ; le MS vérifie et écrit dans le PresenceState du Mandate correspondant */
  push(signal: PresenceSignal): Promise<PresenceAck>;

  /** La RP interroge avant chaque appel si la présence courante est fraîche */
  query(mandateId: MandateId): Promise<PresenceState>;
}
```

**Invariants clés** :

- **I-PC-1 (triplet obligatoire par signal + fenêtre de fraîcheur côté Mandate)** : chaque `PresenceSignal` doit porter explicitement `nonce + produced_at + device_attestation`, signé par le Presence_Device ; la fenêtre de fraîcheur n'est **pas portée par le signal** mais donnée par le `presence_req.max_staleness_ms` du Mandate correspondant (lié au niveau, ancré par le HP au BOOTSTRAP, resserré par `LivenessDetectionBudget` selon le niveau). Les signaux avec `produced_at + presence_req.max_staleness_ms < now` sont uniformément traités comme périmés.
  - **Trace** : `R5.1.3` (les champs `nonce / produced_at / device_attestation` sont obligatoires), `R5.1.4` (le PC rejette les signaux expirés pendant la phase de vérification).

- **I-PC-2 (usage unique par nonce)** : le même `(subject, nonce)` est accepté au plus une fois dans une fenêtre TTL de `2 × max_message_lifetime` ; consommation répétée → rejet avec `E_REPLAY`.
  - **Trace** : `R5.1.1` (`last_freshness` doit satisfaire la fraîcheur — implique que la sémantique anti-rejeu nonce + horodatage atterrit au niveau du PC), `R5.1.3` (le champ `nonce` est la poignée de niveau protocole pour l'anti-rejeu).

- **I-PC-3 (la fraîcheur de présence se resserre automatiquement)** : `PresenceState.last_freshness` doit être ≥ `now − presence_req.max_staleness_ms` ; lorsque cela échoue, le PC doit amener la transition d'état suivante à migrer vers `Degraded(grade')` (`grade'.autonomy < current.autonomy`) ou `Suspended` ; rester au niveau d'origine est interdit, basculer vers une autonomie supérieure est interdit.
  - **Trace** : `R5.1.1` (préalable d'acceptation `last_freshness ≥ t − max_staleness_ms`), `R12.2.2` (utiliser la fraîcheur — et non la période d'interrogation du heartbeat — comme base de passage des appels).

### §3.3 Attestation Chain (AC)

**Responsabilités** : organise toutes les actions d'émission de HP → MS → IF → IF dérivé en une chaîne de signatures traçable à rebours, de sorte que tout Mandate puisse être reconstitué par un tiers indépendant jusqu'à sa source d'autorisation.

**Structure de la chaîne (illustrative)** :

```
Root: HP-Public-Key (self-hosted / anchored to WebAuthn credentials)
  └─ MS-Cert (HP-signed, binds MS public key with permissions)
       └─ Mandate M1 (MS-signed)
            ├─ Mandate M2 (derived from M1, MS countersign + parent Mandate countersign)
            └─ Mandate M3 (derived from M1)
```

**Interface (non normative)** :

```typescript
export interface AttestationChain {
  /** Vérifie toute la chaîne de la feuille à la racine */
  verify(mandate: Mandate): Promise<AttestationVerifyResult>;

  /** Ajoute un événement de chaîne unique (Bootstrap / GradeSwitch / Delegate / Revoke) */
  append(event: AttestationEvent): Promise<void>;

  /** Résout le point terminal porteur de responsabilité du Mandate spécifié */
  resolveAccountableParty(mandateId: MandateId): Promise<HumanPrimeID>;
}

export interface AttestationVerifyResult {
  readonly verified: boolean;
  readonly root: HumanPrimeID;
  readonly invalid_node?: string;
}

export interface AttestationEvent {
  readonly event_type: "bootstrap" | "grade-switch" | "delegate" | "revoke";
  readonly mandate_id: MandateId;
  readonly issuer: HumanPrimeID;
  readonly subject: FayID;
  readonly ts: IsoTime;
  readonly signature_bundle: SignatureBundle;
}
```

**Invariants clés** :

- **I-AC-1 (double contrainte signature-parent + fenêtre-de-validité)** : chaque nœud de la chaîne doit être signé par son parent, et l'horodatage de signature doit tomber dans la fenêtre de validité du parent (`[parent.not_before, parent.not_after]`) ; tout échec → rejet avec `E_ATTESTATION_INVALID` et déclenchement du Revoke du Mandate correspondant.
  - **Trace** : `R3.1.2` (vérification de la feuille à la racine, avec des horodatages dans la fenêtre de validité du nœud parent), `R3.1.3` (tout nœud en échec → rejet avec `E_ATTESTATION_INVALID` et déclenchement du Revoke).

- **I-AC-2 (intégrité de la chaîne, aucun nœud ne peut manquer)** : la vérification de la chaîne doit réussir à chaque nœud de la feuille à la racine ; tout nœud manquant ou à signature invalide est traité comme non fiable, et la chaîne entière renvoie `verified = false`.
  - **Trace** : `R3.1.1` (les quatre types d'événements `Bootstrap / GradeSwitch / Delegate / Revoke` doivent entrer dans la chaîne), `R3.1.2` (la vérification de la chaîne renvoie `verify = true` uniquement lorsque tous les nœuds sont valides).

- **I-AC-3 (la convergence de dérivation est irréversiblement non relâchante sur la chaîne)** : lors de la dérivation, le `scope` et la `grade.autonomy` du nœud enfant doivent converger de façon monotone ; aucun nœud dérivé qui relâche le périmètre ou élève l'autonomie n'a de chemin de signature légitime sur la chaîne.
  - **Trace** : `R7.1.1` (périmètre enfant ⊆ périmètre parent), `R7.1.2` (autonomie enfant ≤ autonomie parent).

### §3.4 Revocation Registry (RR)

**Responsabilités** : service d'état de révocation en temps réel. Porte le pivot d'ingénierie du principe de symétrie « accessibilité de la révocation ≥ accessibilité de l'établissement ».

**Conception à double voie** :

- **Pull** : la RP effectue une interrogation courte (type OCSP, stapling recommandé) à chaque appel accepté ;
- **Push** : après révocation par le MS, poussée vers toutes les RP abonnées (WebSocket / SSE / MQTT) ;
- **Repli conservateur** : si la RP ne peut confirmer l'état du RR dans le délai `StaleBudget` (5 s par défaut, resserré par niveau), elle doit rejeter l'appel par Refus par défaut.

**Interface (non normative)** :

```typescript
export interface RevocationRegistry {
  publish(receipt: RevokeReceipt): Promise<void>;
  query(mandateId: MandateId): Promise<RevocationStatus>;
  subscribe(rpId: string, scope: ScopeFilter): Subscription;
}
```

**Invariants clés** :

- **I-RR-1 (la publication de révocation est immédiatement visible)** : une fois `publish()` terminé, tous les appels `query()` ultérieurs doivent immédiatement renvoyer `revoked = true` dans le délai `RevocationVisibilityBudget` (1 s par défaut, resserré par niveau), exhibant une sémantique de cohérence forte.
  - **Trace** : `R4.2.1` (dans `RevocationVisibilityBudget`, `query` renvoie `revoked`).

- **I-RR-2 (inaccessible → Refus par défaut)** : lorsque le RR est inaccessible pendant ≥ `StaleBudget`, la RP doit rejeter les appels avec `E_RR_UNAVAILABLE` ; le « passage optimiste » est interdit.
  - **Trace** : `R2.1.4` (inaccessible dans `StaleBudget` → Refus par défaut + `E_RR_UNAVAILABLE`), `R4.2.4` (la RP traite l'échec de confirmation d'état comme un Refus par défaut).

> **Frontière sémantique** : RR inaccessible ≠ déconnexion propre de l'iFay. RR inaccessible signifie seulement « impossible de déterminer si le Mandate a été révoqué », déclenchant le rejet `E_RR_UNAVAILABLE` ; la déconnexion de l'iFay (incluant Actually-Disconnected / Perceived-Disconnected) est caractérisée séparément par le §3.5 Liveness Channel et PresenceState. Les deux catégories d'événements de déconnexion ne se substituent pas l'une à l'autre — il existe des combinaisons orthogonales « iFay en ligne mais RR inaccessible » et « RR en ligne mais iFay déconnecté », et la couche protocole fait converger les deux vers Refus par défaut.

### §3.5 Liveness Channel (LC)

**Responsabilités** : juge conjointement, via heartbeat à faible surcoût + fraîcheur de présence, la « vivacité perçue » d'une iFay_Instance du point de vue de MS / RP / HP, et caractérise explicitement la fenêtre d'incohérence entre « vivacité réelle » et « vivacité perçue » comme un citoyen de première classe au niveau du protocole.

**Définition à double sémantique** :

- **Actually-Disconnected** : le processus / réseau / appareil de l'iFay_Instance a cessé de fonctionner ou ne peut être atteint par aucune partie externe. Un fait physique objectif, non directement observable au niveau du protocole.
- **Perceived-Disconnected** : du point de vue de MS / RP / HP, sur la base du Presence_Signal le plus récent, du heartbeat et de l'état de poussée du RR, l'iFay_Instance est jugée déconnectée. **La seule sémantique que la couche protocole peut utiliser comme base de décision.**

**Deux fenêtres d'incohérence** :

- **Fenêtre A — Actually-Disconnected ∧ Perceived-Connected** : l'iFay a réellement décroché, mais le Presence_Signal le plus récent est encore dans `max_staleness_ms` → un « angle mort d'observation » dans l'intervalle de heartbeat ;
- **Fenêtre B — Actually-Connected ∧ Perceived-Disconnected** : l'iFay est réellement en ligne, mais le Presence_Signal le plus récent dépasse `max_staleness_ms` (gigue réseau / perte de heartbeat) → la couche protocole converge par présomption pessimiste.

**Principe de présomption pessimiste (règle de convergence unifiée)** :

> La couche protocole n'utilise que Perceived-Disconnected comme base de décision ; toute iFay_Instance « réellement en ligne mais perçue déconnectée » ne doit pas pour autant prétendre à une exemption des conséquences au niveau du protocole. Au sein des deux fenêtres d'incohérence, le protocole doit traiter selon « le côté le plus strict » ; aucun chemin légitime n'existe pour un « traitement selon l'état le plus permissif ».

**Interface (non normative ; partage les signaux sous-jacents avec le §3.2 PC)** :

```typescript
export interface LivenessChannel {
  /** Instantané de la vivacité perçue courante */
  perceived(mandateId: MandateId): PerceivedLiveness;

  /** Déclenche explicitement un verdict pessimiste (p. ex. à la détection d'une perte de heartbeat) */
  declareStale(mandateId: MandateId, reason: string): Promise<void>;
}

export interface PerceivedLiveness {
  readonly is_perceived_connected: boolean;
  readonly last_freshness: IsoTime;
  readonly staleness_ms: number;
  readonly decided_by: "presence-signal" | "heartbeat" | "explicit-declare";
}
```

**Invariants clés** :

- **I-LC-1 (verdict fondé sur la fraîcheur ; passer selon la période d'interrogation du heartbeat est interdit)** : les verdicts de déconnexion perçue doivent reposer sur `last_freshness ≥ now − max_staleness_ms` ; « la période d'interrogation du heartbeat ne s'est pas écoulée » ne doit pas servir de raison pour continuer à laisser passer des appels.
  - **Trace** : `R12.2.2` (utiliser la fraîcheur — et non la période d'interrogation du heartbeat — comme base de passage des appels).

- **I-LC-2 (transition de la machine à états vers Disconnected)** : une fois jugée Perceived-Disconnected, la transition d'état suivante doit suivre la machine à états §4.3 (Active → Disconnected / Active → Suspended, selon la présence ou non d'un Endorsed_Mandate valide) ; aucun chemin légitime n'existe pour rester dans l'état d'origine ou basculer vers un état plus permissif.
  - **Trace** : `R12.1.3` (n'utiliser que la déconnexion perçue comme base de décision au niveau du protocole ; ne pas exempter des conséquences au niveau du protocole).

- **I-LC-3 (la récupération exige une réconciliation transactionnelle)** : la récupération de Perceived-Disconnected vers Perceived-Connected doit passer par la transaction de réconciliation §8.4 ; la récupération automatique est interdite.
  - **Trace** : `R12.1.3` (aucune exemption des conséquences au niveau du protocole pendant la déconnexion perçue — entraîne que « la récupération exige une confirmation transactionnelle explicite », cohérente avec les transactions de réconciliation de R12.4.1 / R12.4.3 ; au sein de l'ensemble des Requirements déclaré par cette tâche, c'est ancré par 12.1).

### §3.6 Behavior Baseline Service (BBS)

**Responsabilités** : maintient un profil comportemental cumulatif pour chaque paire (Human_Prime, iFay_Instance) ; utilisé pour détecter les écarts significatifs par rapport à la ligne de base par des actions à haute sensibilité, et pour déclencher un témoignage humain supplémentaire en cas d'écart (voir protection §9.10.6 T5).

**Interface (non normative)** :

```typescript
export interface BehaviorBaselineService {
  /** Accumule un nouvel échantillon d'action */
  record(sample: BehaviorSample): Promise<void>;

  /** Évalue l'écart de l'action courante par rapport à la ligne de base */
  evaluate(
    hp: HumanPrimeID,
    fay: FayID,
    action: AtomicAction
  ): BaselineDeviation;

  /** Applique la décroissance de réputation (décroissance du score de confiance) */
  decay(hp: HumanPrimeID, fay: FayID): Promise<void>;
}

export interface BehaviorSample {
  readonly hp: HumanPrimeID;
  readonly fay: FayID;
  readonly action: AtomicAction;
  readonly scope_used: Scope;
  readonly risk_level: "low" | "normal" | "high" | "critical";
  readonly affected_resources: readonly string[];
  readonly ts: IsoTime;
}

export interface BaselineDeviation {
  readonly exceeds_threshold: boolean;
  readonly dimensions: readonly (
    | "risk_level"
    | "scope_used"
    | "affected_resources"
  )[];
  readonly recommended_action:
    | "allow"
    | "require-extra-witness"
    | "downgrade"
    | "suspend";
}
```

**Invariants clés** :

- **I-BBS-1 (le score de confiance doit décroître et être plafonné)** : le « score de confiance » de chaque paire (HP, IF) doit décroître au fil du temps et avoir une borne supérieure explicite ; l'accumulation non bornée est interdite, de peur de diluer la force du témoignage humain requis par les futures actions à haute sensibilité.
  - **Trace** : `R13.5.3` (Action Reputation Decay : le score de confiance doit décroître et avoir une borne supérieure explicite).

- **I-BBS-2 (les événements de témoignage hors ligne de base entrent dans la chaîne + poussée vers la vue du HP)** : tout événement « le dépassement de la ligne de base déclenche un témoignage supplémentaire » doit être inscrit dans l'Attestation_Chain et poussé vers le canal de vue du Human_Prime ; avant l'obtention du témoignage supplémentaire, rejeter l'appel avec `E_HUMAN_WITNESS_REQUIRED`.
  - **Trace** : `R13.5.4` (événement « le dépassement de la ligne de base déclenche un témoignage supplémentaire » inscrit dans l'AC + poussé vers la vue du HP), `R13.5.2` (rejet avec `E_HUMAN_WITNESS_REQUIRED` jusqu'à l'obtention du témoignage supplémentaire).

- **I-BBS-3 (les changements de calibration sont aussi des événements d'audit)** : la calibration de calcul de la ligne de base elle-même, une fois déterminée, est inscrite dans l'Attestation_Chain ; les changements de calibration sont traités comme une classe distincte d'événements d'audit, approuvée par le Protocol Committee via le processus établi.
  - **Trace** : `R13.5.1` (le MS maintient Behavior_Baseline), `R3.1.1` (lors du traitement de tout événement d'audit, l'AC doit contenir son nœud signé ; la traçabilité EARS listée dans ce chapitre ne retient que les clauses pertinentes au sein de l'ensemble des Requirements déclaré par cette tâche).
