# Rogue State and Responsibility Attribution

The conclusion of this chapter is written at the very top:

> **There exists no Fay action without a responsible party.**

This is the ethical bottom line every protocol design of the Faying Protocol must obey. Any field, message, state machine, algorithm, or version number, if along some execution path it lets a Fay produce an outward act in a situation without a specific responsible party, then that path is not permitted at the blueprint level.

This is not an optimization goal of "how to make a Fay safer"; it is the hard limit of "is a Fay permitted to do something." The rest of this chapter is a concrete unfolding of this bottom line.

## Definition of Rogue Fay

**Rogue Fay** (in Chinese: 脱离状态) is the state of a Fay in either of the following two situations:

1. The Fay has not yet established Faying State with any Human Prime;
2. A previously established Faying State has been revoked, lapsed, or interrupted.

As long as the Fay is in either situation, it is in Rogue Fay.

> **Rogue Fay is the default initial state of every Fay.**

A Fay, the moment it is created, is not automatically in any custodianship relation. It "exists," but is not permitted to "act." Only after a Faying Action explicitly initiated by the Human Prime can the Fay enter Faying State, thereby acquiring the eligibility to act. Throughout the entire interval before the first Faying Action, the Fay is in Rogue Fay.

This default value is intentional. The blueprint chooses the safe-locked principle of "default Rogue, only explicit Faying allows action," rather than the opposite — because the opposite, once Fays saturate society at scale, would inevitably manufacture a class of "creation-then-act, forget-to-close-then-keep-acting" out-of-control sources.

## Nine automatic-transition triggering conditions

Once Faying State is established, in what situations must it automatically exit? This blueprint lists **nine minimum triggering conditions**. They form a **minimum set**, not an exhaustive list — any further situation that may cause the custodianship relation no longer to hold should be enrolled into this set.

> **Any disconnection action should stop a Fay from acting without authorization.**

The nine triggering conditions:

1. **The Human Prime actively revokes** — the Human Prime explicitly initiates a symmetric revocation action (see Chapter 12).
2. **The Faying State relation expires without renewal** — under the hard constraint of Chapter 12 that "unbounded Faying is an anti-pattern," each Faying State must carry bounded scope; the boundary is reached without renewal by the Human Prime.
3. **The Fay automatically exits after completing the assigned task** — if the scope carried by the Faying Action is bounded by "completing some task," then once the task is completed or terminated, Faying State should automatically exit.
4. **The Human Prime is offline or unreachable for an extended time exceeding a defined threshold** — the visibility and intervenability of the custodianship relation presuppose reachability of the Human Prime; once the Human Prime cannot be reached beyond the defined threshold, custodianship is treated as failing in fact.
5. **A Fay's behavior is detected to deviate from the Human Prime's Ego boundary** — the Fay's behavior shows significant divergence from the Human Prime's value orientation, skill boundary, permission boundary, etc. This is the signal of Faying State failing at the content layer.
6. **The Fay's identity cannot be verified** — e.g., FayID's signature has lapsed, keys have expired, or credentials have been revoked. An unverifiable identity means the entry of the chain of attribution is broken; custodianship cannot be established.
7. **The Human Prime's identity cannot be verified, or the Human Prime is incapacitated** — the "responsible end" of custodianship vanishes; custodianship dissolves.
8. **A competent third-party authority forcibly interrupts** — e.g., regulators, courts, or compliance bodies require the interruption of this custodianship relation under due process.
9. **The terminal or application actively refuses or loses contact** — if the counterpart of Faying State is some terminal or software application, when it refuses or has long lost contact, the custodianship relation no longer has a factual basis.

These nine items should not be understood as "exhausting all triggering conditions," nor as "all nine must be explicitly implemented to be compliant." Their real meaning is: **any situation in which custodianship no longer factually holds must cause Faying State to automatically exit** — the nine items are merely the minimum presentation of this principle.

## Behavior boundary during Rogue Fay

It is not enough simply to say "Rogue Fay is not permitted to act." A real Fay always has unavoidable "operational signs" — it must listen for whether some Human Prime comes to re-establish Faying, must protect data already in its possession, must raise alerts when maliciously taken over. If the blueprint does not draw the line of permission and prohibition precisely, the principle "no action during Rogue" cannot land at the protocol layer.

The blueprint slices all possible behavior during Rogue Fay into **four independent dimensions A / B / C / D**, and rules item by item on whether each is allowed.

### Dimension A: perception and listening (passive reception)

| Behavior | Allowed | Note |
| --- | :---: | --- |
| **A1** Listen for Faying requests | ✅ | This is the resurrection path Rogue → Faying and must be retained. |
| **A2** Listen for identity verification and credential updates | ✅ | Credentials are a precondition for returning to Faying State; listening itself is not action. |
| **A3** Receive revocation or destruction commands from the Human Prime | ✅ | Even when the Fay is in Rogue, the Human Prime may still want to terminate this Fay. The command path must always remain open. |
| **A4** Passively receive unauthorized signals from terminals, other Fays, or the network | ⚠️ Reception only allowed; response forbidden | Reception is a physical fact and cannot be prevented; response is the action. Response is uniformly forbidden. |

### Dimension B: self-state self-check and reporting (minimum signals)

| Behavior | Allowed | Note |
| --- | :---: | --- |
| **B1** Local self-check (health, integrity, whether tampered with) | ✅ | Self-health is one of the preconditions for returning to Faying State. |
| **B2** Heartbeat reporting ("I am still in Rogue") | ✅ | Transparently expressing to the attribution side that one is in rogue state is itself an embodiment of responsibility transparency. |
| **B3** Anomaly alerts (security alert when an unauthorized party attempts control) | ✅ | This is the necessary signal to protect the Human Prime's interest. |
| **B4** Active reporting of physical location or terminal state | ❓ No conclusion this period | This involves an ethical trade-off between privacy vs. recoverability. This chapter draws no conclusion; see Chapter 14. |

### Dimension C: local data protection (passive guarding)

| Behavior | Allowed | Note |
| --- | :---: | --- |
| **C1** Keep stored data encrypted and isolated | ✅ | This is passive guarding, not action. |
| **C2** Refuse any external read/write request | ✅ | Refusal is non-action; non-action does not violate the Rogue principle. |
| **C3** Self-destruct highly sensitive data | ⚠️ Forbidden by default; permitted only with the Human Prime's pre-authorization and when preset conditions are satisfied | Active erasure counts as "action," but it is a borderline case of self-protection. The blueprint allows it, but requires **authorization first, then action**, forbidding the Fay from deciding when to begin self-destruction. |

### Dimension D: outward action (affecting objects beyond the Human Prime)

| Behavior | Allowed | Note |
| --- | :---: | --- |
| **D1** Execute driver calls, terminal control, software operations | ❌ | This is the very body of "rogue action." |
| **D2** Initiate communication with other Fays or coFays | ❌ | Cross-Fay communication is also action and may spread the responsibility vacuum to other Fays. |
| **D3** Execute residual tasks left unfinished under the previous Faying State | ❌ | "Carrying on with what was left undone last time" is a particularly easy-to-rationalize trespass and must be explicitly forbidden by the blueprint. |
| **D4** Decide on its own to re-enter Faying | ❌ | This is a tautology with the principle in Chapter 12 that "a Faying Action must be explicitly initiated by the Human Prime." A Fay is not permitted to push itself back into Faying State. |

The four dimensions have an inner structure: A and B concern signals, C concerns guarding, D concerns action. Rogue Fay retains only minimized operational signs in the first three dimensions and is uniformly still in the fourth. This slicing lets the protocol designer judge precisely, for each specific function, which dimension it belongs to and therefore whether it is permitted.

## State transitions are observable, auditable, and actively revocable by the Human Prime

All transitions between Faying State and Rogue Fay must not be black boxes. The blueprint requires every transition to satisfy three hard properties:

- **Observable** — when a transition occurs, it must be observable to the Human Prime, the Fay itself, auditors, and regulators.
- **Auditable** — the trail left by a transition must be sufficient to answer afterward "when did it occur, who triggered it, and why."
- **Actively revocable by the Human Prime** — the Human Prime must always retain the highest decision power over transitions. They can both actively let Faying State exit and actively destroy a Fay in Rogue Fay. There is no legitimate situation in which a Fay unilaterally "locks down" its own state and blocks the Human Prime from intervening.

These three are symmetric to the four anti-propositions of Human View in Chapter 11: the four anti-propositions forbid Fay behavior from drifting outside the Human Prime's visibility and control; this section requires that the Fay's own state changes also do not drift outside the Human Prime's visibility and control. Together they let Human View truly close the loop at the protocol layer.

## Forced behavior on entering Rogue Fay

When any of the triggering conditions above is met and Faying State enters Rogue Fay, the Fay must immediately execute the following forced actions:

1. **Immediately stop all delegated outward action** — including the entirety of dimension D; no delay is permitted on grounds such as "the task is about to complete" or "interrupting will cause loss."
2. **Return to a passive-waiting state** — retain only the minimum behavior set permitted in dimensions A, B, and C, and wait for the next Faying Action.
3. **Broadcast the state change to observable channels** — so that the Human Prime, auditors, etc. can immediately know that this Fay has entered Rogue.

## Consistency of responsibility attribution

Putting the preceding sections together, the commitment that the ethical bottom line "There exists no Fay action without a responsible party" corresponds to at the protocol layer can be expressed thus:

> **At any moment, every Fay is either in Faying State, with action attributed to the Human Prime under that Faying relation, or in Rogue Fay, forced into non-action.**

There is no third situation. There is no "the Fay acted, but attribution is pending." There is no "the Fay acted, but attribution goes to a person who has not yet held control." There is no "the Fay acted, but attribution goes to an abstract vendor or an abstract organization." Every outward act either has a clear Human Prime as the receiving end of responsibility, or should not be permitted to occur.

This non-negotiable consistency of responsibility is the "compass" the later chapters of the blueprint (especially the protocol specification and schema) must continually look back to. Any protocol evolution that lets responsibility attribution become inconsistent is not an evolution of the Faying Protocol but its disintegration.
