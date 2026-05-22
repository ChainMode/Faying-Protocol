# Credential Management

Credential management sounds highly engineering-flavored — issuance, signing, revocation, and renewal of FayID, each involving specific algorithms and key protocols. But in this blueprint, credential management is placed under values, not technical topics.

The reason is this: the Faying Protocol exists to make "to whom does the act belong" explicit. The technical bearer of this, when landed at the concrete protocol layer, is the credential. The credential answers two questions:

> **Is this Fay, right now, the Fay it claims to be?**
> **Is this Fay, right now, still authorized by its Human Prime?**

Neither is an engineering question; both are responsibility questions. Once credentials can be forged, abused, or quietly issued by some third party outside the Human Prime, the entire value of the Faying Protocol vanishes in an instant — the Human Prime is no longer the true holder of responsibility.

Specific algorithms, signature formats, key protocols, and other technical details belong to the protocol specification document and the schema; this chapter does not unfold them. This chapter only states the few positions on credential management on which no concession is permissible.

## FayID is the identity foundation for entering Faying State

FayID is the unified, unique identity of a Fay within the iFay framework. The entire custodianship contract of the Faying Protocol is built on FayID. A Faying Action must make explicit "which FayID enters Faying State"; the attribution of Faying State must make explicit "which FayID is attributed to which Human Prime"; the exit from Faying State must make explicit "which FayID enters Rogue Fay."

If FayID cannot be trusted, all three judgments above lose meaning.

## Credential failure equals Faying failure

Among the nine triggering conditions for automatic transition from Faying State to Rogue Fay listed in Chapter 13, condition 6 explicitly states:

> **The Fay's identity cannot be verified (e.g., FayID signature has lapsed).**

This item is not a "happens to involve credentials" entry within the nine; it is the concrete landing of credential management at the protocol layer that may not be bypassed. Once the validity of FayID is in question, no matter how continuous or near-complete the Fay's prior work, Faying State must exit immediately:

> **A doubt over credential validity is equivalent to Faying State already failing.**

There is no intermediate case "credential is suspect but Faying State still holds," and there is no engineering compromise of "finish the current task first and then deal with the credential issue."

## Revocation rights must remain on the Human Prime side

Credential management has a seemingly minor but extremely critical trade-off in protocol design — to whom does revocation of a credential ultimately belong? The answer is obvious: to the Human Prime.

The Fay itself should have no legitimate path to revoke its own credential — homologous to D4 in Chapter 13, a Fay cannot decide for itself to leave custodianship, nor can it decide for itself to cut the link of custodianship.

Third-party platforms, the Fay's runtime providers, and the Fay's capability providers must not have the power to revoke its FayID without the Human Prime's consent — unless that third party is a competent authority in the regulatory sense (see triggering condition 8 in Chapter 13).

The Human Prime must always retain a symmetric, reachable, auditable revocation path. The reachability of the revocation action must be no lower than the reachability of initiating a Faying Action. This is the concrete landing at the credential layer of the "symmetry" principle in the Faying Protocol: establishing custodianship and revoking custodianship must be two equally reachable paths. Once revocation becomes harder than establishment, the custodianship relation slides in fact toward "irrevocable delegation," thereby violating the "intervention path always open" requirement of Human View.

## Renewal is not a default behavior

Chapter 12 imposes a hard constraint on Faying State: a Faying State must be of bounded scope, and unbounded Faying is an anti-pattern. The position this constraint corresponds to at the credential layer is — renewal of a credential should not be carried out by default.

Each renewal should be an explicit, witnessable action, not an implicit loop of "Fay submits automatically, the system renews automatically." The blueprint allows engineering-layer conveniences such as "renewal reminders" and "renewal suggestions," but forbids making "renewal" something the Fay can silently complete on its own — that would, in fact, turn Faying into unbounded delegation.

Understood from the responsibility perspective: renewal is the moment when the responsible end re-expresses the intent of custodianship. If even renewal is silently completed by engineering, then "custodianship" is left with only a signature and no intent.

## A few inviolable red lines

The few values positions of credential management are red lines no technical solution may violate when landing:

- FayID is the identity foundation;
- a credential that cannot be trusted means Faying does not hold;
- revocation rights must remain on the Human Prime side;
- renewal is not a default behavior.

Concrete signing algorithms, key hierarchies, propagation of revocation lists, fine-grained design of renewal time windows, the structure of root certificates for cross-vendor mutual trust, and the eventual consistency of revocation — these technical details belong to the protocol specification. This chapter neither restates nor pre-decides them, but any technical solution must first comply with the four positions above.

![Credential management illustration: control of FayID, signing, revocation, and renewal on the Human Prime side](../../zh-CN/blueprint/illustration/credential-management.png)
