---
title: "Faying Protocol/1.0 — §5 Messages du Protocole"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: fr
part: "Chapitre 5 sur 11 (corps du protocole)"
---

> Navigation du corps du protocole : [Sommaire](./README.md) | précédent [§4 Modèles de Données](./04-Modeles-de-Donnees.md) | suivant [§6 Cryptographie](./06-Cryptographie.md)

## §5 Messages du Protocole

Ce chapitre présente tous les messages de la couche Faying Protocol : règles d'encodage, structure d'enveloppe, l'inventaire des 7 classes de messages métier plus 1 classe de réponse d'erreur, ainsi que la table de correspondance entre codes d'erreur et poussées audit / canal de vue du HP.

> **Note d'autorité de typage** : les types `Mandate / Scope / Grade / PresenceSignal / PresenceRequirement / Endorsement / SignatureBundle / Attestation / WebAuthnAssertion / AtomicAction / RevokeReason` référencés dans les blocs TypeScript de ce chapitre ont leurs **définitions faisant autorité** en §4 Modèles de Données (CDDL) ; la vue TypeScript est une vue **non normative** de lecture humaine, et là où les deux diffèrent, le CDDL de §4 fait foi.

### §5.1 Règles d'encodage

- **Format primaire (CBOR)** : l'encodage par défaut pour toute transmission sur le fil est CBOR ([RFC 8949](https://www.rfc-editor.org/rfc/rfc8949)) ; le `Content-Type` HTTP doit être déclaré comme `application/faying-protocol+cbor`.
- **Repli d'interopérabilité (JSON)** : JSON ([RFC 8259](https://www.rfc-editor.org/rfc/rfc8259)) n'est utilisé que dans les scénarios de débogage / navigateur / revue humaine ; le `Content-Type` HTTP doit être explicitement déclaré comme `application/faying-protocol+json` ; l'équivalence de sécurité est garantie par une sémantique de champ et un format de signature identiques.
- **Encodage déterministe** : tout objet signé doit, avant la signature, être sérialisé en CBOR selon la règle d'encodage déterministe RFC 8949 §4.2.1, évitant l'ambiguïté de la sérialisation JSON ; sous la forme JSON, l'entrée de signature reste le hachage de la chaîne d'octets sérialisée en CBOR déterministe (voir §6.3).
- **Liaison de transport** : par défaut HTTP/1.1 et HTTP/2 ; les points de terminaison de Mandate Service suivent `POST /faying-protocol/v1/{verb}` ; la liaison à gRPC (service `faying-protocol.v1`) ou WebSocket / SSE (flux `faying-protocol.v1`) est également autorisée. Toutes les liaisons de couche transport doivent préserver les signatures et nonces de la couche message ; substituer l'identité du canal TLS de la couche transport aux signatures de niveau message est interdit.

### §5.2 Structure de l'enveloppe

Tous les messages utilisent l'enveloppe unifiée `FayingProtocolEnvelope` :

```typescript
interface FayingProtocolEnvelope<TPayload> {
  header: {
    version:    "Faying Protocol/1.0";
    msg_type:   FayingProtocolMsgType;
    msg_id:     string;        // ULID
    issued_at:  IsoTime;
    expiry:     IsoTime;
    nonce:      Nonce;
    grade:      Grade;         // niveau de session courant (utilisé par la RP pour rejeter les requêtes de bas niveau)
    issuer:     HumanPrimeID | string;
    subject:    FayID;
  };
  claims:      TPayload;
  attestation: Attestation;
  signature:   SignatureBundle;
}

type FayingProtocolMsgType =
  | "BOOTSTRAP"        | "BOOTSTRAP_RESP"
  | "PRESENCE"         | "PRESENCE_ACK"
  | "GRADE_SWITCH"     | "GRADE_SWITCH_RESP"
  | "DELEGATE"         | "DELEGATE_RESP"
  | "REVOKE"           | "REVOKE_RECEIPT"
  | "FAYING_REQUEST"   | "FAYING_REQUEST_RESP"
  | "DISCLOSURE"
  | "ERROR";
```

**Invariants au niveau de l'enveloppe** :

- Tout champ manquant ou de type erroné → rejet uniforme avec `E_PROTOCOL` (voir §5.4).
- Dans une fenêtre de `2 × max_message_lifetime`, `nonce` est accepté au plus une fois pour le même `subject` ; répétition → `E_REPLAY`.
- `expiry` doit être fini et `> issued_at` ; les enveloppes expirées n'entrent pas dans le chemin de vérification métier et sont rejetées directement avec `E_PROTOCOL`.
- L'entrée de `signature` doit être `H( Deterministic-CBOR( Envelope_without_signature ) )` (voir §6.3).

### §5.3 Inventaire des messages

Ce protocole définit 7 classes de messages métier : BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE / REVOKE / FAYING_REQUEST / DISCLOSURE, plus 1 classe de réponse d'erreur ERROR (voir §5.4).

#### §5.3.1 BOOTSTRAP (Faying Action)

**Objet** : le Human Prime établit un Mandate auprès du MS via BOOTSTRAP, émettant l'autorisation de mandat à l'iFay. BOOTSTRAP est **l'unique entrée légitime de Faying Action** de Faying Protocol.

```typescript
interface BootstrapClaims {
  human_prime:   HumanPrimeID;
  fay:           FayID;
  scope:         Scope;
  grade:         Grade;
  presence_req:  PresenceRequirement;
  not_after:     IsoTime;          // doit être fini
  human_witness: WebAuthnAssertion; // user-verification = true
  endorsement?:  Endorsement;       // optionnel ; si présent, émet un Endorsed Mandate (voir §4 / §11)
  faying_request_ref?: string;      // sous le chemin initié par l'IF, référence la FAYING_REQUEST.msg_id correspondante
}
```

**Réponse de succès** : renvoie l'objet `Mandate` complet (y compris `signature_bundle`).

**Contraintes dures au niveau du protocole** :

- `not_after` doit être fini et `> not_before` ; `∞` et les valeurs négatives sont interdits ; violation → rejet uniforme avec `E_PROTOCOL` (cohérent avec §3.1 I-MS-1 / Property 7).
- Champ `human_witness` manquant ou signature invalide → rejet uniforme avec `E_HUMAN_WITNESS_REQUIRED` ; aucun chemin légitime n'existe pour IF / MS / Supervisory Agent de se substituer au HP pour compléter l'acquittement.
- Lorsque BOOTSTRAP répond à une `FAYING_REQUEST` antérieure initiée par l'iFay, `faying_request_ref` doit pointer vers le `msg_id` de cette requête ; le MS doit, sur l'Attestation Chain, relier « initié par l'iFay → témoignage du HP → prise d'effet » en une seule chaîne de preuve indivisible (voir §5.3.6 et §3.3).
- Lorsque le champ `endorsement` est présent, le MS doit, avant la signature, vérifier `endorsed_scope ⊆ scope` ∧ `endorsed_grade.autonomy ≤ grade.autonomy` ∧ `0 < endorsed_lifetime_ms ≤ (not_after − not_before)` ; tout échec → rejet avec `E_ENDORSEMENT_INVALID` (code d'erreur 1013).

#### §5.3.2 PRESENCE (calibration continue)

**Objet** : l'iFay_Instance pousse périodiquement vers le MS les signaux de présence produits par les Presence Devices, rafraîchissant le `PresenceState.last_freshness` du Mandate correspondant.

```typescript
interface PresenceClaims {
  mandate_id:    MandateID;
  signal:        PresenceSignal;
  device_health: {
    secure_element: boolean;
    tampered:       boolean;
    last_boot_at:   IsoTime;
  };
}
```

**Contraintes dures au niveau du protocole** :

- `signal` doit porter le triplet obligatoire §3.2 I-PC-1 (`nonce / produced_at / device_attestation`) et être signé par le Presence Device ; toute absence → `E_PROTOCOL`. La fenêtre de fraîcheur est donnée par le `presence_req.max_staleness_ms` du Mandate correspondant, non portée par le signal.
- Un signal au-delà de `presence_req.max_staleness_ms` → `E_PRESENCE_STALE`, et déclenche un resserrement selon §3.2 I-PC-3 (migration vers un niveau plus strict ou Suspended).
- Le même `(subject, nonce)` se répétant dans une fenêtre de `2 × max_message_lifetime` → `E_REPLAY` uniformément.

#### §5.3.3 GRADE_SWITCH (changement de niveau)

**Objet** : ajuste le niveau d'autorisation (rehaussement / abaissement) au sein du cycle de vie d'un Mandate.

```typescript
interface GradeSwitchClaims {
  mandate_id:    MandateID;
  target_grade:  Grade;
  reason:        "human-initiated" | "presence-loss" | "policy-trigger";
  human_witness?: WebAuthnAssertion;  // obligatoire en direction de rehaussement, optionnel en abaissement
}
```

**Invariant au niveau du protocole (témoignage obligatoire au rehaussement)** : lorsque `target_grade.autonomy > current.autonomy` (c.-à-d. une autonomie strictement supérieure au niveau courant), `human_witness` est **OBLIGATOIRE** ; signature manquante ou invalide → rejet uniforme avec `E_HUMAN_WITNESS_REQUIRED`. La direction d'abaissement (`target_grade.autonomy ≤ current.autonomy`) peut être déclenchée automatiquement par le protocole (p. ex. `presence-loss` / `policy-trigger`) ; `human_witness` n'est pas requis.

#### §5.3.4 DELEGATE (dérivation multi-appareils / sous-agent)

**Objet** : dérive un Mandate enfant d'un Mandate parent, utilisé dans les scénarios multi-appareils ou de sous-agent.

```typescript
interface DelegateClaims {
  parent_mandate: MandateID;
  child_subject:  FayID;            // FayID dérivé
  child_scope:    Scope;            // doit ⊆ parent.scope
  child_grade:    Grade;            // child_grade.autonomy doit ≤ parent.grade.autonomy (autonomie inférieure ou égale, c.-à-d. plus stricte ou égale)
  device_id?:     string;           // lie à un terminal spécifique en dérivation multi-appareils
}
```

**Contraintes dures au niveau du protocole** :

- `child_scope ⊆ parent.scope` ∧ `child_grade.autonomy ≤ parent.grade.autonomy` ; toute expansion dans l'une ou l'autre direction → rejet avec `E_PROTOCOL` (cohérent avec §3.1 I-MS-4 / Property 6).
- Le `signature_bundle.chain` du Mandate enfant doit porter le contreseing du Mandate parent, formant un nœud dérivé sur l'Attestation Chain.
- Lorsque le Mandate parent porte `endorsement`, l'`endorsement` du Mandate enfant (s'il est présent) doit converger au sein de l'endossement parent ; non-convergence → rejet avec `E_ENDORSEMENT_INVALID`.

#### §5.3.5 REVOKE

**Objet** : révoque un Mandate ; optionnellement, cascade pour révoquer tous les Mandate enfants dérivés.

```typescript
interface RevokeClaims {
  mandate_id:   MandateID;
  cascade:      boolean;            // révocation en cascade de tous les Mandate enfants dérivés (par défaut true)
  reason:       RevokeReason;
  effective_at: IsoTime;            // par défaut = now ; révocation planifiée autorisée
}

type RevokeReason =
  | "human-initiated"
  | "expiry"
  | "task-completed"
  | "human-prime-unreachable"
  | "ego-deviation"
  | "fay-credential-invalid"
  | "human-prime-credential-invalid"
  | "regulatory-order"
  | "terminal-disconnected";
```

`RevokeReason` correspond un à un aux neuf conditions de déclenchement du chapitre 13.

**Contraintes dures au niveau du protocole** :

- L'accessibilité de la révocation doit être ≥ l'accessibilité du Bootstrap (cohérent avec Property 4 / R4.1) ; aucun chemin n'existe pour que l'iFay lui-même initie légitimement un REVOKE.
- Lorsque `cascade = true`, tous les Mandate enfants dérivés doivent devenir visibles comme `revoked` dans le délai `RevocationVisibilityBudget` (cohérent avec Property 14).
- La révocation est irréversible : `Revoked` est un état absorbant ; restaurer l'autorisation doit repasser par BOOTSTRAP avec un nouveau `mandate_id` non égal à l'ancien `mandate_id` (cohérent avec Property 10).

#### §5.3.6 FAYING_REQUEST / FAYING_REQUEST_RESP (Faying bidirectionnel initié par l'IF)

**Objet** : l'iFay sollicite proactivement un Faying auprès du Human Prime (demandant l'établissement ou l'ajustement de la relation de mandat). Ce message **ne produit pas directement de Mandate** ; le MS agit seulement comme relais, poussant la requête vers le canal de vue du HP ; le HP complète ensuite l'acquittement et l'effectivité via BOOTSTRAP (voir §2.4 Phase A0).

```typescript
interface FayingRequestClaims {
  initiator:        FayID;          // l'iFay lui-même
  target_human:     HumanPrimeID;   // HP cible
  proposed_scope:   Scope;          // périmètre de mandat proposé
  proposed_grade:   Grade;          // niveau proposé
  reason:           string;         // complément en texte libre
  reason_code:
    | "establish"
    | "adjust-scope"
    | "adjust-grade"
    | "renew"
    | "endorsement-request";
  expected_lifetime_ms?: number;    // durée de vie attendue du Mandate
  proposed_endorsement?: Endorsement; // si l'on sollicite aussi un Endorsed Mandate
}

interface FayingRequestRespClaims {
  request_msg_id: string;           // référence le FAYING_REQUEST.msg_id amont
  status:         "accepted" | "rejected" | "timeout";
  bootstrap_ref?: string;           // lorsque status=accepted, pointe vers le BOOTSTRAP.msg_id complété par le HP
  reject_reason?: string;
}
```

**Contraintes dures au niveau du protocole** :

- Une FAYING_REQUEST initiée par l'IF ne produit **pas** directement de changement d'état Faying ; seul le HP répondant dans le délai `BootstrapTimeout` via BOOTSTRAP (portant `faying_request_ref` et un `human_witness` vérifiable) rend la requête effective.
- Si le HP ne donne pas d'acquittement explicite dans le délai `BootstrapTimeout`, le MS doit renvoyer `FAYING_REQUEST_RESP { status="timeout" }` et inscrire l'événement dans l'Attestation Chain, correspondant au code d'erreur `E_FAYING_REQUEST_NOT_CONFIRMED` (1014).
- Aucun chemin légitime n'existe pour MS / IF / Supervisory Agent de se substituer au HP pour compléter l'acquittement ; `human_witness` manquant → `E_HUMAN_WITNESS_REQUIRED` (1010).
- La fréquence de FAYING_REQUEST pour chaque paire `(HP, IF)` est contrainte par `ConfirmationRateLimit` (voir Annexe B) ; le dépassement est traité selon §9.10.7 T6.

#### §5.3.7 DISCLOSURE (message de divulgation structuré)

**Objet** : un message de divulgation structuré utilisé par l'iFay lorsqu'elle rend compte ou demande confirmation. Les régulateurs et le MS peuvent auditer ce message au niveau du schéma ; utiliser du texte libre pur pour masquer une information clé est interdit (voir §9.10.4 T3).

```typescript
interface DisclosureClaims {
  mandate_id:         MandateID;
  /** mandatory_fields (toute absence → traitée comme une erreur de protocole) */
  action:             AtomicAction;          // une divulgation correspond à exactement un Atomic_Action
  scope_used:         Scope;                 // le sous-ensemble réellement utilisé du scope
  risk_level:         "low" | "normal" | "high" | "critical";
  reversibility:      "reversible" | "partially-reversible" | "irreversible";
  affected_resources: string[];
  uncertainty_flags:  string[];              // p. ex. ["ambiguous-target", "stale-context"]
  /** compléments optionnels */
  free_text?:         string;
  intent?:            "report" | "request-confirmation";
  endorsement_id?:    string;                // si cela s'est produit pendant Disconnected, pointe vers l'endossement correspondant
}
```

**Liste d'application de `mandatory_fields`** (cohérente avec R13.3 / §9.10.4) :

`action` / `scope_used` / `risk_level` / `reversibility` / `affected_resources` / `uncertainty_flags`.

**Contraintes dures au niveau du protocole** :

- Tout `mandatory_fields` manquant ou non analysable → le MS doit rejeter avec `E_PROTOCOL` (1099) et pousser vers le canal de vue du HP ;
- Les actions à haute sensibilité (`risk_level ∈ {high, critical}`) doivent, **avant** l'exécution de dimension D, d'abord émettre DISCLOSURE et attendre la confirmation explicite du HP (sauf si le niveau courant est déjà G4 Autonomous et que l'action relève du périmètre principal ; voir §7) ;
- Si un audit ultérieur constate que les `mandatory_fields` de DISCLOSURE sont incohérents avec l'action réelle, le MS doit révoquer le Mandate avec `RevokeReason="ego-deviation"` ;
- Un DISCLOSURE pour des actions exécutées pendant Disconnected doit porter `endorsement_id`, afin que l'action puisse être tracée de façon indépendante vers un endossement spécifique.

### §5.4 Codes d'erreur

Les réponses d'erreur utilisent uniformément le message `ERROR` (enveloppe `msg_type = "ERROR"`) ; le corps `claims` a la forme `{ code, message, mandate_id?, recovery_hint? }`. Le tableau ci-dessous donne tous les codes d'erreur et leurs contraintes de poussée audit et canal de vue du HP (cohérent avec §EH.3).

| Code | Nom | Signification | Réponse | Doit entrer en audit | Doit entrer en vue du HP |
| ---: | --- | --- | --- | :---: | :---: |
| 1001 | `E_NO_MANDATE` | La requête ne porte aucun Mandate | Rejet | ✗ | ✗ |
| 1002 | `E_MANDATE_EXPIRED` | Mandate expiré | Rejet + déclenche Revoke | ✓ | ✗ |
| 1003 | `E_SCOPE_VIOLATION` | L'appel dépasse le périmètre | Rejet + enregistre suspect | ✓ | ✗ |
| 1004 | `E_GRADE_INSUFFICIENT` | Niveau courant insuffisant pour l'action sensible | Rejet + suggère rehaussement | ✓ | ✗ |
| 1005 | `E_PRESENCE_STALE` | Signal de présence expiré | Rejet + déclenche abaissement | ✓ | ✗ |
| 1006 | `E_REVOKED` | Mandate révoqué | Rejet | ✓ | ✓ |
| 1007 | `E_ATTESTATION_INVALID` | Échec de vérification de l'attestation | Rejet + déclenche Revoke | ✓ | ✓ |
| 1008 | `E_RR_UNAVAILABLE` | Registre de révocation inaccessible | Rejet par Refus par défaut | ✓ | ✗ |
| 1009 | `E_REPLAY` | nonce répété | Rejet + alerte de sécurité | ✓ | ✓ |
| 1010 | `E_HUMAN_WITNESS_REQUIRED` | Rehaussement de niveau / Faying bidirectionnel sans témoignage humain | Rejet | ✓ | ✗ |
| 1011 | `E_ROGUE_DETECTED` | Comportement Rogue détecté | Rejet + Revoke forcé | ✓ | ✓ |
| 1012 | `E_BUDGET_EXCEEDED` | ResourceBudget dépassé | Rejet + déclenche abaissement | ✓ | ✗ |
| 1013 | `E_ENDORSEMENT_INVALID` | Champ endorsement invalide (incl. `endorsed_scope ⊄ scope` / `endorsed_grade.autonomy > grade.autonomy` / `endorsed_lifetime` manquant ou trop long / altéré) | Rejet + déclenche Revoke de ce Mandate | ✓ | ✓ |
| 1014 | `E_FAYING_REQUEST_NOT_CONFIRMED` | FAYING_REQUEST initiée par l'IF non explicitement acquittée par le HP dans `BootstrapTimeout` | Rejet + inscription dans l'Attestation Chain | ✓ | ✗ |
| 1099 | `E_PROTOCOL` | Erreur de niveau protocole (version / format / signature / `mandatory_fields` de DISCLOSURE manquants ou non analysables) | Rejet | ✓ | ✗* |

> **Note `*`** : par défaut, `E_PROTOCOL` n'entre qu'en audit ; mais lorsqu'il est déclenché depuis le chemin de §5.3.7 DISCLOSURE `mandatory_fields` manquants ou non analysables, le MS doit en outre pousser vers le canal de vue du HP (voir §5.3.7 et §9.10.4 T3).
>
> **Notes sémantiques audit / vue du HP** :
>
> - **Doit entrer en audit** : les erreurs doivent être inscrites dans l'Attestation Chain / le journal d'audit sous forme du quintuplet `(error_code, mandate_id, ts, RP_id, reason)` ; sauf `E_NO_MANDATE` (pas de contexte de Mandate), tous les codes d'erreur sont ✓.
> - **Doit entrer en vue du HP** : les erreurs doivent être poussées vers le canal de vue du HP ; la RP ne doit pas les avaler silencieusement. Les quatre de base (`E_REVOKED` / `E_ATTESTATION_INVALID` / `E_REPLAY` / `E_ROGUE_DETECTED`) sont imposés par §EH.3 ; `E_ENDORSEMENT_INVALID`, parce que sa chaîne de déclenchement accompagne inévitablement `E_REVOKED`, est aussi poussé vers le canal de vue du HP.
> - Les réponses d'erreur ont **interdiction** de porter l'état interne du MS, des empreintes de clé privée de Mandate, d'autres identifiants de Human Prime ou toute autre information sensible (voir §EH.3).
