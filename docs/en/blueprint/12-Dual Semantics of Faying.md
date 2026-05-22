# Dual Semantics of Faying

By now the word "Faying" has appeared many times: as the name of the contract in Chapter 2, distinguishing iFay from Agent in Chapter 3, carrying the Human View value requirement in Chapter 11. But what Faying actually refers to has been deliberately deferred until now. The reason is that it cannot be described from one face alone.

Faying carries two semantics at once.

**State semantics** — the connection state of a Fay being under a Human Prime's custodianship, called **Faying State**.
**Action semantics** — the "delivery of control" act by which a Fay enters Faying State from rogue state, called **Faying Action**.

The two semantics are inseparable: without a Faying Action, Faying State will never be established; without Faying State, a Faying Action is just an empty operation. This is the **Dual Semantics principle** of Faying.

Any attempt to simplify Faying to a single face — taking it merely as "a connection state," or merely as "a switching action" — quietly erases responsibility attribution at the protocol layer.

## Faying State: the connection state under custodianship

Faying State is the connection state of a Fay being under a specific Human Prime's custodianship. A Fay entering this state has three necessary properties.

**Action attribution is unique** — all outward acts of the Fay in this state are attributed to that Human Prime. Whether the act is decided autonomously by the Fay, explicitly commanded by the Human Prime, or triggered by the external environment, the responsible end does not jump.

**Continuous visibility** — during this state, the Human Prime holds Human View over the Fay's activity, and can confirm at any time whether custodianship is still in effect.

**The intervention path is always open** — during this state, the Human Prime's commands of revocation, pause, slowdown, or destruction over the Fay have the highest priority. The Fay may not override these commands on any "business reason."

Faying State is not a static result; it is a continuously online commitment. It needs to be re-confirmed at every microscopic moment, not held forever once established. Once any of the three above no longer holds, Faying State should enter the exit flow defined in Chapter 13.

> **An important inverse conclusion**: in the state outside Faying State (i.e., Rogue Fay), every outward act of a Fay has no one to receive responsibility. Therefore the only acceptable design choice the Faying Protocol can make at the protocol layer is: **forbid the Fay from acting during Rogue Fay**, rather than "let it act and patch attribution afterward." This principle will be strictly landed in Chapter 13.

## Faying Action: the delivery of control

A Faying Action is a specific, observable, auditable "delivery of control" act.

The most fitting analogy is this everyday scene:

> Jack hands the steering wheel of a car to an AI driver. At this moment, Jack is not simply pressing an "autopilot" button — he is, in a way clearly perceivable to the outside, **handing over control**. Before this, the wheel belonged to Jack; after this, the wheel belongs to that AI driver; meanwhile, all consequences arising from the wheel still fall on Jack, who holds the driver's license.

A Faying Action is the equivalent "handing over the wheel" in the digital world. It moves a Fay, clearly, witnessably, and traceably, from the rogue state of "exists but cannot act" into the Faying State of "acts on behalf of the Human Prime."

This leads to several non-negotiable properties of a Faying Action.

**Must be explicitly initiated by the Human Prime** — a Faying Action does not allow a Fay to decide on its own to begin. A Fay may not enter Faying State autonomously merely because "last time it began this way," "I infer the Human Prime would now wish me to begin," or "I have been authorized for similar acts before." Each entry must be explicitly initiated by the Human Prime.

**Must be witnessable** — a Faying Action must leave a mark observable to the outside (including auditors, regulators, the Fay itself, other Fays, and the Human Prime). A Faying Action that has not been witnessed is equivalent to one that did not occur.

**Must be of bounded scope** — a Faying Action should not be a perpetual "full-power delegation." The blueprint strongly favors a Faying Action carrying explicit scope (e.g., a time window, a task scope, a terminal scope), automatically lapsing on reaching the boundary. Unbounded Faying is an anti-pattern to be avoided.

**Must be symmetrically revocable** — every Faying Action must have a corresponding, symmetric revocation path. Establishing Faying State and exiting Faying State must be **two equally reachable** paths, not an asymmetric design of "easy to open, hard to close."

## Both faces together are Faying

Putting state and action faces together, the full meaning of Faying can be expressed in this paragraph:

> **Faying is a "delivery of control" act (Faying Action) explicitly initiated by the Human Prime, witnessable and symmetrically revocable, that pushes the Fay into a continuously online connection state under custodianship (Faying State); within this state, the Fay may act on behalf of the Human Prime, and the consequences are all borne by that Human Prime; outside this state, the Fay is not permitted to act.**

The same paragraph yields three commitments along the dimension of time. **Past**: Faying State is always entered through some specific Faying Action; there is no Fay that "is just naturally in Faying." **Present**: the validity of Faying State is continuously calibrated at every moment by Human View, not held forever once established. **Future**: Faying State will eventually exit through a symmetric revocation or automatic lapse, returning the Fay to the rogue state defined in Chapter 13.

## Hard constraints on protocol design

This chapter, as a values chapter, does not specify fields or messages, but it imposes several non-negotiable hard constraints on the concrete design of the Faying Protocol:

- the protocol layer must provide first-class expression for **both** State and Action; it may not express only one face;
- the protocol layer forbids any legitimate path "by which a Fay initiates a Faying Action on itself";
- the protocol layer must provide for every Faying Action a witnessable mark and a symmetrically revocable path;
- the protocol layer forbids "unbounded Faying" as a default form; it must enforce that a Faying Action carries bounded scope at the protocol layer;
- the protocol layer must guarantee: when any condition under which Faying State no longer holds is triggered, the Fay automatically transitions into rogue state, not into a "degraded Faying."

How a custodianship relation is established, sustained, and ended has now been fully defined at the values level. The next chapter flips the perspective: when Faying State does not hold, what may, and may not, the Fay do? It is the strictest chapter in this blueprint, the one in which no concession is allowed.
