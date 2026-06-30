---
title: "Faying Protocol/1.0 — Annexe B Budgets de Paramètres par Défaut"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: fr
part: "Annexe B (référence normative)"
---

> Navigation du corps du protocole : [Sommaire](./README.md) | précédent [Annexe A Alignement Terminologique](./Annexe-A-Alignement-Terminologique.md) | suivant [Annexe C Journal des Modifications](./Annexe-C-Journal-des-Modifications.md)

## Annexe B Budgets de Paramètres par Défaut

> Cette annexe donne les budgets de paramètres par défaut et les bornes supérieures de Faying Protocol 1.0 ; des valeurs spécifiques peuvent être ajustées par les implémentations, mais la valeur d'implémentation de tout paramètre ne doit pas dépasser la colonne « Borne supérieure » ; la contrainte dure de resserrement monotone par niveau (voir P17.3 LivenessDetectionBudget / P8 fraîcheur de présence) doit être maintenue.

### B.1 Budgets globaux

| Paramètre | Par défaut | Borne supérieure | Règle de resserrement par niveau | Source |
| --- | --- | --- | --- | --- |
| `MaxMandateLifetime` | 24 h | 30 j | Devrait être plus court pour les scénarios à haute sensibilité (défini par l'implémentation) | §1.3 G2 / §4.1 / P7 |
| `BootstrapTimeout` | 60 s | 5 min | — | §5.3.1 / §5.3.6 / §8.2 |
| `RevocationVisibilityBudget` | 1 s | 5 s | Resserré par niveau (autonomie plus élevée → budget plus court) | §3.4 I-RR-1 / §9.6 / P5 |
| `StaleBudget` (seuil de rejet pour RR inaccessible) | 5 s | 30 s | — | §3.4 / §EH.1 / §EH.4 |
| `HumanReachabilityBudget` | 30 min | 24 h | — | §EH dérivé / chapitre 11 de la note de cadrage |
| `MaxDegradedDuration` | 5 min (par niveau) | 30 min | Resserré par niveau (autonomie plus élevée → résidence plus courte) | §4.3 / §8.2 / P11 |

### B.2 Presence max-staleness (par niveau)

| Niveau | Par défaut | Borne supérieure | Note |
| --- | --- | --- | --- |
| G1 Strict | 5 s | 10 s | Niveau par défaut des actions à haute sensibilité |
| G2 Moderate | 60 s | 5 min | — |
| G3 Loose | 5 min | 30 min | — |
| G4 Autonomous | 30 min | 2 h | La perte de heartbeat G4 → Suspended directement (§7.3) |

> **Source** : §7.1 / P8 fraîcheur de présence.

### B.3 LivenessDetectionBudget (borne supérieure de la fenêtre de détection de déconnexion)

> Resserré en synchronisation avec Presence max-staleness ; contrainte dure P17.3 : `max_staleness_ms ≤ LivenessDetectionBudget(grade)` ∧ resserré de façon monotone par niveau (niveau plus strict → fenêtre de détection plus courte).

| Niveau | Par défaut | Borne supérieure | Note |
| --- | --- | --- | --- |
| G1 Strict | 5 s | 10 s | Resserré en synchronisation avec le max-staleness G1 |
| G2 Moderate | 60 s | 5 min | — |
| G3 Loose | 5 min | 30 min | — |
| G4 Autonomous | 30 min | 2 h | La perte de heartbeat G4 → Suspended directement (§7.3) |

> **Source** : §9.9 / P17.3 / Requirement 12.3.

### B.4 AttentionDriftThreshold (seuil d'inactivité de la vue du HP)

> Une inactivité continue sur le canal de vue du HP dépassant ce seuil est traitée comme une « perte d'attention » ; les actions à haute sensibilité sont interdites pendant cette période (voir §9.10.5 T4, P18.4).

| Niveau | Par défaut | Borne supérieure | Note |
| --- | --- | --- | --- |
| G1 Strict | 30 s | 2 min | Les actions à haute sensibilité doivent relever d'une autonomie ≤ G1 |
| G2 Moderate | 5 min | 15 min | — |
| G3 Loose | 15 min | 1 h | — |
| G4 Autonomous | 1 h | 4 h | — |

> **Source** : §9.10.5 / P18.4 / Requirement 13.4.

### B.5 ConfirmationRateLimit (borne supérieure du débit de confirmation)

> Le dépassement déclenche un abaissement / une suspension automatique ; les événements du bucket critical doivent pénétrer et ne pas être éliminés silencieusement ; la fréquence de FAYING_REQUEST est incorporée dans le même budget (cohérent avec Questions ouvertes Q12).

| Paramètre | Par défaut | Borne supérieure | Note |
| --- | --- | --- | --- |
| `ConfirmationRateLimit` (par paire HP × IF) | 10 / min | 60 / min | Inclut FAYING_REQUEST, GRADE_SWITCH-rehaussement, pré-confirmation à haute sensibilité de DISCLOSURE, et tous les événements requérant une confirmation explicite du HP |

> **Source** : §9.10.7 / P18.6 / Requirement 13.6.

### B.6 Borne supérieure souple d'Endorsed_Lifetime

> Appariée avec P16.3 (Endorsement_Convergence) / P16.4 (Endorsed_Lifetime_Hard_Stop) ; ne doit pas dépasser `Mandate.not_after − Mandate.not_before` ; à l'expiration, le Mandate est Revoked, même si l'IF est encore physiquement déconnectée (contrainte dure de dépassement de délai léger).

| Paramètre | Par défaut | Borne supérieure souple | Note |
| --- | --- | --- | --- |
| Borne supérieure souple d'`Endorsed_Lifetime` | 4 h | 12 h | Utilisée comme valeur recommandée avant la résolution de Questions ouvertes Q11 ; la borne supérieure dure encore resserrée par niveau attend la résolution RFC |

> **Source** : §7.5 / P16.3 / P16.4 / Requirement 11.3 / Questions ouvertes Q11.

### B.7 Contraintes dures de cohérence numérique

- **B.2 et B.3 se resserrent en synchronisation** : `max_staleness_ms ≤ LivenessDetectionBudget(grade)` ; les requêtes BOOTSTRAP / GRADE_SWITCH hors limites sont rejetées uniformément avec `E_PROTOCOL` (P17.3).
- **Dépassement de B.5 ConfirmationRateLimit** : abaissement / suspension automatique selon §9.10.7 ; les événements du bucket `critical` ne doivent pas être éliminés silencieusement et doivent pénétrer jusqu'au canal de vue du HP (P18.6).
- **Contrainte dure d'expiration de B.6 Endorsed_Lifetime** : à l'expiration, la machine à états du Mandate migre vers Revoked, même si l'IF est encore en Disconnected (P16.4).
- **Règle unifiée de resserrement par niveau** : tous les budgets resserrés par niveau (B.2 / B.3 / B.4) rejettent les requêtes BOOTSTRAP / GRADE_SWITCH / DELEGATE hors limites uniformément avec `E_PROTOCOL`.
- **Cohérence Annexe A et Annexe B** : les noms de budgets listés en Annexe A.5 doivent être strictement cohérents avec les noms de paramètres définis dans chaque sous-section de cette annexe ; tout changement de nom requiert des mises à jour synchronisées aux deux endroits.
