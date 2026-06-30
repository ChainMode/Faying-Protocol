---
title: "Faying Protocol/1.0 — §1 Vue d'ensemble"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: fr
part: "Chapitre 1 sur 11 (corps du protocole)"
---

> Navigation du corps du protocole : [Sommaire](./README.md) | suivant [§2 Architecture](./02-Architecture.md)

## §1 Vue d'ensemble

Ce chapitre présente le nommage du protocole, son positionnement, la trame des objectifs de conception, les différences fondamentales avec les schémas existants, la définition en une phrase de Faying Protocol, le périmètre livrable et les non-objectifs de ce corps de protocole, ainsi que les règles de gestion des versions et de compatibilité. Il constitue l'ancrage sémantique des §2–§11 et des Annexes A/B qui suivent.

> **Note de traçabilité EARS** : chaque règle de ce chapitre est suivie d'une ligne `Trace:` qui énumère les identifiants des sous-clauses EARS correspondantes (issues du référentiel des exigences) sous la forme `R<exigence>.<critère>.<clause>`.

### §1.1 Nommage du protocole

Nom de la spécification du protocole : **Faying Protocol**. Le numéro de version s'écrit uniformément **Faying Protocol/1.0**.

Ce protocole **abolit l'abréviation FAP (Faying Auth Protocol)** — **le nom du protocole est Faying Protocol, sans abréviation distincte** ; si une forme courte est nécessaire, on emploie le nom complet « Faying Protocol ». Ce document de conception et les documents de spécification associés ne contiennent plus aucune forme de nommage historique telle que `FAP` / `FAP/1.0` / `Faying Auth Protocol` / `application/fap+json` / `POST /fap/v1/...`. Toute référence antérieure à `FAP` doit être comprise comme une référence héritée à Faying Protocol et remplacée par Faying Protocol dans les nouveaux documents.

> **Héritage de nommage historique** : les premiers brouillons utilisaient « Faying Auth Protocol (FAP) ». Ce nommage est aboli ; toute référence externe à `FAP` doit être comprise comme une référence héritée à Faying Protocol et ne doit pas être réutilisée dans les nouveaux documents.

### §1.2 Positionnement du protocole

> **Faying Protocol est un protocole de « couche d'autorisation continue » de niveau applicatif posé au-dessus de TLS, qui porte la sémantique « sous quel état de présence, sur quel périmètre, à quel niveau et pendant quelle fenêtre temporelle un Human Prime autorise son iFay ».**

- **Sous TLS** : la confidentialité du canal et l'identité du pair sont prises en charge par TLS 1.3 (avec mTLS optionnel) ; Faying Protocol ne refait pas ce travail.
- **À côté d'OAuth/OIDC** : OAuth fournit l'autorisation au niveau applicatif, OIDC émet des assertions d'identité ; tous deux relèvent de modèles à « jeton instantané ». Faying Protocol résout ce qu'aucun des deux ne résout — **l'agence continue + la liaison à la présence + le changement de niveau + l'imputabilité unique**.
- **Au-dessus de WebAuthn** : WebAuthn / FIDO2 fournit, lors de l'amorçage, des preuves de « présence utilisateur » de force matérielle pour le Human Prime ; Faying Protocol réutilise sa forme d'identifiant comme racine de la confiance dérivée.

Faying Protocol ne remplace pas TLS et ne réinvente pas OAuth ; il se situe au-dessus de TLS et sous la sémantique métier, et impose que **chaque action sortante d'un iFay** franchisse la porte de vérification du Mandate. Tout appel sortant qui contourne cette porte est traité comme une Rogue Action et doit être rejeté par un intergiciel placé au-dessus de la couche de transport et sous la couche métier.

### §1.3 Objectifs de conception

Le tableau ci-dessous énumère les **8 objectifs de conception G1–G8 de Faying Protocol** (objectifs fondamentaux) ainsi que 2 objectifs d'ingénierie dérivés de §9 / §5 (propriétés de sécurité / interopérabilité du protocole). **Chaque objectif s'aligne sur exactement une Requirement du référentiel des exigences**, formant l'ancrage de traçabilité bidirectionnelle entre ce corps de protocole et le document d'exigences.

| Objectif | Signification | Origine dans la note de cadrage | Requirement correspondante |
| --- | --- | --- | --- |
| **G1 Imputabilité unique** | À tout instant, l'action sortante d'un iFay peut être attribuée sans ambiguïté à un unique Human Prime | Limite éthique du chapitre 13 | Requirement 1 |
| **G2 Refus par défaut** | Aucun Mandate valide → aucune action sortante ; tout champ manquant → rejet | Défaut Rogue du chapitre 13 | Requirement 2 |
| **G3 Observable, auditable, révocable** | Les transitions d'état, l'initiation d'action, les événements de renouvellement/révocation sont tous observables, auditables et vérifiables de façon indépendante | Chapitres 11, 13 | Requirement 3 |
| **G4 Révocation symétrique** | L'accessibilité des chemins de révocation ≥ celle des chemins d'établissement ; la révocation est irréversible | Chapitres 10, 12 | Requirement 4 |
| **G5 Calibration continue** | Les signaux de présence et le niveau du Mandate peuvent être reconfirmés à tout instant ; la confiance ne survit jamais à son expiration | Chapitres 11, 12 | Requirement 5 |
| **G6 Autorisation graduée** | Un seul Mandate ne peut représenter toutes les forces ; le niveau doit être exprimable, commutable, abaissable ; les rehaussements requièrent le témoignage du HP | Point 3 de la note d'origine | Requirement 6 |
| **G7 Dérivation multi-appareils** | Lorsqu'un même iFay opère sur plusieurs terminaux, la confiance peut être dérivée mais le responsable ne change jamais ; le périmètre/niveau converge strictement | Réserve évolutive Phase 2/3 | Requirement 7 |
| **G8 Évolutivité post-quantique** | Les suites d'algorithmes peuvent être négociées et avancées par paliers ; bits de négociation PQC réservés | Exigence d'ingénierie courante | Requirement 8 |
| —(dérivé) **Propriétés de sécurité** | Anti-rejeu / anti-détournement / anti-hameçonnage / détection de déconnexion / menaces adverses de l'ère de l'IA | §9 Considérations de sécurité | Requirement 9 (avec la dérivée Requirement 13) |
| —(dérivé) **Interopérabilité du protocole** | Équivalence CBOR / JSON, CBOR déterministe, matrice de compatibilité inter-implémentations | §5 Messages du Protocole | Requirement 10 |

> **Principe de correspondance un-à-un Objectif ↔ Requirement** : ce tableau est **l'unique correspondance faisant autorité** entre le corps du protocole et le document d'exigences. Tout identifiant de sous-clause EARS `R<n>.<m>.<k>` cité dans les chapitres ultérieurs lors de l'énoncé d'un invariant ou d'un mécanisme doit avoir son numéro de Requirement racine `<n>` figurant dans la colonne « Requirement correspondante ». Endorsed_Mandate (Requirement 11) dérivé de G6 / G4 / G5 / G7, la politique de déconnexion (Requirement 12) et la protection de l'ère de l'IA (Requirement 13) agissent comme des raffinements de G1–G8 et reçoivent un ancrage au niveau du protocole respectivement en §4 / §8 / §9.

### §1.4 Différences fondamentales avec les schémas existants (édition en une ligne)

| Schéma existant | Résout | Ne résout PAS — ce que Faying Protocol doit résoudre |
| --- | --- | --- |
| OAuth 2.0 / 2.1 | Autorisation d'accès applicatif sur des ressources | Jeton unique, sans niveau, sans présence, sans révocation symétrique |
| OIDC SSO | Assertion d'identité (qui) | Pas d'agence continue (agir pour le compte de), pas de niveau |
| mTLS | Identité du pair aux deux extrémités du canal | Ne peut exprimer « qui, sous quel état de présence, a délégué à qui de faire quoi » |
| JWT | Revendications autoportées avec signature | Pas de révocation, pas de sémantique de niveau, une longue durée de vie entre en conflit avec la « révocation symétrique » |
| FIDO2 / WebAuthn | Preuve de présence de force matérielle pour le Human Prime | Ne couvre que l'instant de connexion, pas l'agence continue de l'iFay |
| Macaroons | Jetons dérivables avec caveats | Pas de liaison à la présence, pas de témoignage explicite du Human Prime |
| SPIFFE / SPIRE | Identité de charge de travail | Vue côté charge de travail, pas de point terminal de responsabilité humaine |

Faying Protocol n'entre en concurrence avec aucun des schémas ci-dessus — il se situe au-dessus de TLS et sous la sémantique métier, fournissant la **sémantique dédiée** de « Human Prime ↔ iFay » : agence continue + liaison à la présence + changement de niveau + imputabilité unique + révocation symétrique.

### §1.5 Définition en une phrase

> **Faying Protocol = « Mandate (au lieu de jeton) + Presence Signal + Attestation Chain + Revocation Registry » — quatre éléments exprimés de façon coopérative au-dessus de TLS, initiés de manière bidirectionnelle par Human Prime et iFay, rendus effectifs uniquement par l'acquittement explicite du Human Prime, calibrés en continu et révocables de façon symétrique.**

#### §1.5.1 Un changement d'état Faying ne prend effet qu'avec l'acquittement explicite du Human Prime (assertion centrale)

L'initiation d'une relation Faying (établissement ou ajustement) est **bidirectionnelle** :

- **Initiée par le HP** : le Human Prime peut initier proactivement le Faying via le canal BOOTSTRAP (voir §2.4 Phase A, §5.3.1).
- **Initiée par l'IF** : l'iFay peut proactivement solliciter un Faying auprès du Human Prime (c.-à-d. FAYING_REQUEST) via le chemin en deux étapes §2.4 Phase A0 → BOOTSTRAP (voir §5.3.6).

> **Pourtant, quel que soit le côté qui initie, la condition d'effectivité finale de tout changement d'état Faying est que le Human Prime émette un acquittement explicite, non trompé et vérifiable** (la forme par défaut étant une assertion de présence utilisateur WebAuthn ou une preuve équivalente de force matérielle).

Trois contraintes dures incassables en découlent immédiatement :

1. **L'iFay seul ne peut rendre un Faying effectif** : une FAYING_REQUEST initiée par l'IF qui ne reçoit pas l'acquittement explicite du HP dans le délai `BootstrapTimeout` (60 s par défaut, voir Annexe B) expire ou est rejetée et **ne produit aucun changement d'état Faying**. Mandate_Service doit renvoyer `E_FAYING_REQUEST_NOT_CONFIRMED` (code d'erreur 1014) et inscrire l'événement dans l'Attestation Chain afin de préserver la preuve irréversible de « qui a initié, quand a-t-on confirmé, est-ce devenu effectif ».
   - **Trace** : `R1.3.2` (le chemin initié par l'IF ne prend effet qu'après l'acquittement explicite du HP), `R1.3.3` (rejet sans changement d'état lorsque `BootstrapTimeout` s'écoule sans acquittement), `R1.3.4` (événement inscrit dans l'AC quelle que soit l'effectivité).
2. **Aucun chemin de témoignage par substitution** : au niveau du protocole, il n'existe aucun chemin légitime permettant à l'iFay, à Mandate_Service ou à Supervisory_Agent de se substituer au Human Prime pour compléter l'acquittement Faying. Tout BOOTSTRAP dépourvu de `human_witness`, ou dont le `human_witness` échoue à la vérification, doit être rejeté avec `E_HUMAN_WITNESS_REQUIRED` (code d'erreur 1010).
   - **Trace** : `R1.3.5` (aucun chemin légitime permettant à IF / MS / SA de se substituer au HP pour compléter l'acquittement Faying).
3. **L'iFay ne peut contourner unilatéralement la révocation** : l'iFay peut émettre un message de « demande de déconnexion du Faying » (traité comme un Disclosure_Report), mais l'iFay ne détient pas le pouvoir de révoquer son propre Mandate ; toute révocation doit en définitive être initiée par le Human Prime ou un régulateur/une autorité et rendue visible via le canal de vue du HP (voir §4 / §10).
   - **Trace** : `R4.1.4` (l'IF ne détient pas le pouvoir de révoquer son propre Mandate), `R4.1.5` (la demande de déconnexion est enregistrée comme Disclosure_Report dans l'AC et poussée vers le canal de vue du HP).

Cette sous-section est l'ancrage unifié du chapitre Vue d'ensemble pour §2.4 Phase A0, §5.3.6 FAYING_REQUEST et §5.4 codes d'erreur 1010 / 1014, ainsi que le point de départ de toutes les argumentations des chapitres ultérieurs selon lesquelles « pas de témoignage du HP, pas de Faying ».

### §1.6 Périmètre livrable du protocole et non-objectifs

#### §1.6.1 Dans le périmètre (Normatif — porté par ce corps de protocole)

Ce corps de protocole (c.-à-d. ce fichier unique) spécifie, **et spécifie uniquement**, ce qui suit :

- **Objets de données du protocole** : le format primaire CBOR et le format de repli JSON pour Mandate / Presence_Signal / Attestation / SignatureBundle / Faying Protocol Envelope / Endorsed_Mandate / Disclosure_Report, etc. (le CDDL fait autorité ; voir §4 / §5).
  - **Trace** : `R10.1.1`, `R10.1.2`, `R10.2.1`–`R10.2.4`.
- **Interfaces des composants du protocole** : frontières de responsabilité et invariants de Mandate_Service / Presence_Channel / Attestation_Chain / Revocation_Registry / Liveness_Channel / Behavior_Baseline_Service (voir §3).
- **Messages du protocole** : définitions de champs, codes d'erreur et contraintes dures au niveau du protocole pour les sept types de messages BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE / REVOKE / FAYING_REQUEST / DISCLOSURE (voir §5).
- **Règles cryptographiques** : négociation de la suite d'algorithmes, hiérarchie de dérivation de clés, canonicalisation de l'entrée de signature (y compris l'ancrage de l'entrée de signature de l'Endorsed_Mandate ; voir §6).
  - **Trace** : `R8.1.1`–`R8.1.4`, `R8.2.1`–`R8.2.4`.
- **Sémantique des niveaux d'autorisation** : définitions précises des cinq niveaux G0–G4, matrice des conditions de déclenchement, principe de monotonie d'abaissement et sous-niveaux Endorsement Grades (voir §7).
  - **Trace** : `R5.1.1`, `R6.1.1`, `R6.1.2`.
- **Cycle de vie et machine à états** : les sept états Unpaired / Pairing / Active / Degraded / Disconnected / Suspended / Revoked, leurs conditions de transition et la transaction de réconciliation (voir §8).
- **Considérations de sécurité** : modèle de menace STRIDE, anti-rejeu / anti-détournement / anti-hameçonnage / détection de déconnexion, transfert de confiance dérivée entre appareils et les menaces adverses de l'ère de l'IA T1–T7 (voir §9).
- **Gestion des erreurs** : réponses du protocole, chemins de récupération, contraintes d'observabilité et convergence par Refus par défaut pour les 14 codes d'erreur (dont 1010 `E_HUMAN_WITNESS_REQUIRED`, 1013 `E_ENDORSEMENT_INVALID`, 1014 `E_FAYING_REQUEST_NOT_CONFIRMED` ; voir §10).
  - **Trace** : `R2.1.1`–`R2.1.4` (Refus par défaut), `R3.3.1` (le canal de vue du HP doit être atteint).
- **Annexes** : aide-mémoire d'alignement terminologique (Annexe A), budgets de paramètres par défaut (Annexe B).

#### §1.6.2 Hors périmètre (Non normatif — non porté par ce protocole)

Les éléments suivants ne relèvent **pas** du périmètre normatif de ce corps de protocole et servent uniquement d'implémentations de référence / d'orientation d'ingénierie ; ils sont sans rapport avec la conformité d'interopérabilité à ce corps de protocole :

- **Sémantique métier** : comportement métier spécifique de l'iFay, pilotes de terminaux, schémas d'intégration applicative ;
- **Conception UI / UX** : présentation concrète du canal de vue du Human Prime, conception des boîtes de dialogue de confirmation, interactions mobiles / bureau ;
- **Exploitation et déploiement** : modèles de déploiement haute disponibilité, stratégies de mise à l'échelle, synchronisation inter-régions pour Mandate_Service / Revocation_Registry ;
- **Détails de la couche de transport** : les détails du handshake de TLS 1.3 lui-même (spécifié par RFC 8446), paramètres d'ajustement spécifiques à HTTP/2 / gRPC / QUIC ;
- **Implémentations de PD (Presence Device)** : implémentations matérielles de l'authentificateur WebAuthn / TPM / Platform Keystore (spécifiées par W3C / ISO / TCG) ;
- **Détails juridiques et de conformité** : la manière dont les régulateurs / organismes de conformité agissent comme « autorités » légales hors du protocole (la couche protocole spécifie uniquement leur position dans l'énumération RevokeReason et l'exigence de chaîne de signatures, non leur constitution juridique) ;
- **Code d'implémentation de référence** : toute implémentation de référence de ce protocole (telle que la vue TypeScript [`schemas/types.ts`](../../../../schemas/types.ts) ou la suite de tests basés sur les propriétés `pbt/`) est explicitement étiquetée **« Implémentation de référence, non normative »** et ne constitue pas le corps du protocole ;
- **Questions ouvertes** : tous les éléments de §11 Questions ouvertes dont le `status: open`.

#### §1.6.3 Principe de livraison en fichier unique

> **Le corps du protocole est ce fichier unique `docs/en/specification/2025-10-25/Faying-Protocol-1.0.md`.**

Les autres fichiers Markdown sous `docs/en/specification/2025-10-25/` sont uniquement des documents auxiliaires (README / CHANGELOG) et **ne constituent pas le corps du protocole**. Notez que les deux côtés sont **structurellement asymétriques** : le côté anglais est un fichier unique (`Faying-Protocol-1.0.md`, avec §1–§11 et les Annexes A/B intégrées), tandis que le côté chinois à `docs/zh-CN/specification/2025-10-25/` est scindé en 11 fichiers de chapitre plus les Annexes A/B/C. Le fichier unique anglais est donc aligné avec l'ensemble des chapitres chinois au **niveau de l'ancre de section** (numérotation des sections, diagrammes Mermaid, blocs de code CDDL / TypeScript, tableau des codes d'erreur et Annexes A / B), non fichier par fichier ; le journal des modifications (Annexe C) n'est maintenu que du côté chinois. En cas d'ambiguïté entre les formulations chinoise et anglaise, **la version de référence fait foi** et la version anglaise est corrigée lors de la prochaine réunion de revue.

### §1.7 Gestion des versions et compatibilité

Cette section est la **définition faisant autorité** de la numérotation des versions de Faying Protocol. Le numéro de version n'est pas un simple marqueur documentaire — il fait **partie du contrat d'interopérabilité** : il apparaît dans l'enveloppe de transmission, dans les schémas et dans la négociation, et il détermine directement si deux implémentations indépendantes peuvent dialoguer. Cette section est donc Normative : les implémentations DOIVENT interpréter les numéros de version et effectuer la négociation de version selon les règles ci-dessous. L'Annexe C (journal des modifications) ne fait qu'enregistrer l'historique ; elle ne redéfinit pas ces règles.

#### §1.7.1 Trois axes de version orthogonaux

Faying Protocol décrit la version d'une spécification avec **trois axes mutuellement indépendants** qui NE DOIVENT PAS être amalgamés en un seul numéro :

| Axe | Question à laquelle il répond | Forme | Support | Exemple |
| --- | --- | --- | --- | --- |
| **Version du protocole** (contrat d'interopérabilité) | Deux implémentations peuvent-elles dialoguer | `MAJEUR.MINEUR` | prose / champ `version` de l'enveloppe de transmission / nom de fichier de schéma | `Faying Protocol/1.0` |
| **Statut du document** (cycle de vie) | Cette spécification est-elle finalisée | énumération | `status` du front matter | `Draft` / `Final` / `Deprecated` / `Obsolete` |
| **Édition rédactionnelle** (errata et clarifications) | Quelle révision textuelle sous la même version de protocole | date de publication | nom du répertoire de publication / `date` du front matter | `2025-10-25` |

> **Contrainte fondamentale** : **seule la « version du protocole » `MAJEUR.MINEUR` entre dans le format de transmission** (le champ `version` de l'enveloppe, les noms de fichiers de schéma). Le statut du document et l'édition rédactionnelle NE DOIVENT PAS entrer dans le format de transmission — ce sont des marqueurs de gouvernance documentaire qui ne participent pas aux décisions d'interopérabilité. Une implémentation NE DOIT PAS modifier son traitement des messages parce que le statut de document ou l'édition rédactionnelle d'un pair diffère.

#### §1.7.2 Sémantique de la version de protocole `MAJEUR.MINEUR`

La version du protocole s'écrit `Faying Protocol/MAJEUR.MINEUR`, avec **seulement deux niveaux et aucun PATCH** — le format de transmission et la sémantique d'interopérabilité ne distinguent que deux paliers de compatibilité.

- **MAJEUR (changement cassant)** : tout changement qui amènerait un pair implémenté strictement selon l'ancienne spécification à **rejeter ou mal interpréter** de nouveaux messages. Exemples : modifier la sémantique d'un champ CDDL faisant autorité en §4.2, supprimer un type de message, redéfinir la sémantique d'un code d'erreur, changer un état absorbant de la machine à états.
  - Règle : incrémenter MAJEUR, remettre MINEUR à zéro (p. ex. `1.4 → 2.0`).
  - Compatibilité : l'interopérabilité entre MAJEUR différents n'est **pas garantie**.
- **MINEUR (ajout rétrocompatible)** : un ajout qu'une nouvelle implémentation peut comprendre dans d'anciens messages et qu'une ancienne implémentation peut ignorer sans danger là où elle ne reconnaît pas les éléments optionnels. Exemples : ajout de champs optionnels, ajout de messages ou de codes d'erreur, ajout d'entrées au catalogue de menaces de l'ère de l'IA, ajout de paramètres d'annexe, ajout de Correctness Properties.
  - Règle : incrémenter MINEUR (p. ex. `1.0 → 1.1`).
  - Compatibilité : au sein d'un même MAJEUR, un MINEUR supérieur **DOIT** rester rétrocompatible avec les MINEUR inférieurs.

**Test de décision (auto-vérification de l'implémenteur)** : le changement amènerait-il un pair implémenté strictement selon l'ancienne spécification à rejeter ou mal interpréter de nouveaux messages ?

- Oui → **MAJEUR** ;
- Non, mais il ajoute du contenu visible sur le fil → **MINEUR** ;
- Il ne modifie que le texte, et non la sémantique du format de transmission (corrections de coquilles, ajout d'exemples, clarification d'ambiguïté) → **ne pas changer la version du protocole** ; utiliser l'édition rédactionnelle de §1.7.4.

La ligne de base actuelle est `Faying Protocol/1.0`.

#### §1.7.3 Négociation de version et règles de compatibilité (Normatif)

La négociation de version **réutilise la même approche que la négociation de suite d'algorithmes de §6.1** (chaque partie déclare, la plus haute valeur communément prise en charge est choisie). Les implémentations DOIVENT :

1. **Déclarer** : pendant le BOOTSTRAP, le client et le serveur déclarent chacun l'ensemble des versions de protocole qu'ils prennent en charge (p. ex. `supported: [1.0, 1.1]`).
2. **Même MAJEUR → MINEUR le plus haut** : lorsque les deux parties partagent un MAJEUR, elles DOIVENT sélectionner le **MINEUR le plus haut** communément pris en charge comme version effective de la session ; une implémentation à MINEUR supérieur DOIT pouvoir servir un pair à MINEUR inférieur (rétrocompatible jusqu'à `MAJEUR.0`).
3. **MAJEUR croisé → rejet** : lorsqu'aucun MAJEUR commun n'existe, aucune négociation n'a lieu ; le BOOTSTRAP DOIT être rejeté avec `E_PROTOCOL` (code d'erreur 1099) ; aucune interopérabilité dégradée « au mieux » n'est autorisée.
4. **Une mise à niveau progressive ne doit pas casser les Mandate existants** : lorsqu'une nouvelle suite d'algorithmes par défaut ou un nouveau MINEUR est introduit via la négociation de version, les Mandate existants DOIVENT rester vérifiables avant leur `not_after` ; une montée de version NE DOIT PAS invalider les Mandate valides en cours.
   - **Trace** : `R8.2.4` (mise à niveau progressive via négociation de version sans casser la vérifiabilité des Mandate existants).
5. **Traitement d'un MINEUR supérieur inconnu** : à la réception d'un message déclaré comme étant du même MAJEUR mais d'un MINEUR supérieur au sien, une implémentation DOIT l'interpréter à son MINEUR le plus élevé pris en charge et **ignorer** les champs optionnels qu'elle ne reconnaît pas (plutôt que de rejeter) ; c'est la concrétisation à l'exécution de la promesse de rétrocompatibilité MINEUR.

#### §1.7.4 Édition rédactionnelle et errata (changements non normatifs)

Après la finalisation de `Faying Protocol/1.0` (Final), des errata purement textuels sont inévitables — corrections de coquilles, ajout d'exemples, clarification d'ambiguïté, correction de liens internes. De tels changements :

- NE DOIVENT PAS changer le numéro de version du protocole (le faire prétendrait à tort que le contrat d'interopérabilité a changé) ;
- sont ancrés par la **date de publication** : p. ex. `Faying Protocol/1.0 (2025-10-25)` est la première édition Final de 1.0 ; les errata ultérieurs produisent un nouveau répertoire de publication (p. ex. `2026-03-xx/`) tandis que la version du protocole demeure `1.0` ;
- sont consignés dans le journal des modifications de l'Annexe C sous une catégorie `Editorial`, avec la transition d'édition marquée via un champ de front matter `edition` ;
- **Contrainte dure** : une édition rédactionnelle ne peut porter que des changements non normatifs. Toute modification qui touche à la sémantique du format de transmission DOIT incrémenter MINEUR ou MAJEUR et NE DOIT PAS être publiée sous le déguisement d'errata rédactionnels.

#### §1.7.5 Où atterrit le numéro de version, et notes pour les implémenteurs du standard

Le tableau ci-dessous indique exactement où atterrit le numéro de version, afin que les implémenteurs puissent juger quelles différences affectent l'interopérabilité et lesquelles non :

| Point d'atterrissage | Ce qui est écrit | Notes |
| --- | --- | --- |
| Champ `version` de l'enveloppe de transmission (§5.2) | `"Faying Protocol/MAJEUR.MINEUR"` | **MAJEUR.MINEUR uniquement** ; pas de date d'édition, pas de statut de document |
| Nom de fichier de schéma (`fap-1.0.cddl`, etc.) | suit `MAJEUR.MINEUR` | le nom de fichier **ne change pas d'une édition rédactionnelle à l'autre** — les errata ne renomment pas `fap-1.0.cddl`, ce qui maintient stables les références existantes (le préfixe hérité `fap` conservé suit le même raisonnement ; voir Annexe C) |
| content-type (§5.1) | `application/faying-protocol+cbor` (ou `+json`) | le content-type identifie la famille de protocole ; un paramètre `version=` PEUT être ajouté pour le routage au niveau passerelle comme **commodité de déploiement**, mais ce paramètre ne fait pas partie de la sémantique du format de transmission et n'affecte pas les décisions de compatibilité |
| `status` / `date` du front matter | statut du document / édition rédactionnelle | marqueurs de gouvernance documentaire ; **n'entrent pas dans le format de transmission** ; un pair NE DOIT PAS modifier le traitement des messages en fonction d'eux |
| balise git | `faying-protocol-v<MAJEUR.MINEUR>-<statut>` | finalisation `faying-protocol-v1.0-final` ; instantané d'édition `faying-protocol-v1.0-2026-03-xx` ; une balise DOIT couvrir simultanément le corps + `vectors/` + `schemas/`, figeant ensemble le triplet d'interopérabilité |

**Notes obligatoires pour les implémenteurs du standard** :

1. **L'interopérabilité se juge uniquement à la version du protocole** : l'unique base pour « pouvons-nous dialoguer » est `MAJEUR.MINEUR`. Le statut de document d'un pair (Draft/Final) et l'édition rédactionnelle (date de publication) ne changent **pas** le comportement d'interopérabilité — ne jamais rejeter les messages valides d'un pair simplement parce qu'il est marqué Draft ou qu'il a une édition plus ancienne.
2. **Le même MAJEUR doit être rétrocompatible** : en implémentant un MINEUR supérieur, vous DEVEZ aussi servir correctement tous les pairs à MINEUR inférieur depuis `MAJEUR.0`.
3. **Ne pas traiter les errata comme des mises à niveau** : un changement de date de répertoire de publication (édition rédactionnelle) ne signifie pas que le protocole a changé ; seul un changement de `MAJEUR.MINEUR` impose d'évaluer l'impact sur l'interopérabilité.
4. **Stabilité du nom de fichier de schéma** : ne vous appuyez pas sur le nom de fichier pour encoder l'édition ; les errata d'un même `MAJEUR.MINEUR` réutilisent le même fichier de schéma, distingués par la balise git / le répertoire de publication.
5. **Aucune promesse de compatibilité pendant Draft** : tant que `status: Draft`, `MAJEUR.MINEUR` peut être ajusté avant le gel ; les promesses de compatibilité MAJEUR/MINEUR de cette section ne prennent pleinement effet qu'après `Final`.
