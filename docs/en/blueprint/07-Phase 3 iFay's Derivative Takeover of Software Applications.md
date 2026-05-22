# Phase 3: iFay's Derivative Takeover of Software Applications

Phase 3 turns the direction of extension from terminal hardware to software applications — local applications, cloud services, and In-APP embedded scenarios.

There is one key difference between software applications and hardware terminals: the state of a hardware terminal is relatively concentrated — a drone or a robot is a single object under custodianship — while the boundary of a software application is often process-based, modular, and cross-network. An e-commerce client taken over by an iFay may collaborate across multiple domains, multiple APIs, and multiple third-party services at once. The difficulty of Phase 3 is not in "the takeover" but in whether the boundary of the takeover is described clearly.

## Derivation structure homologous to Phase 2

Phase 3 is structurally symmetric to Phase 2 and likewise does not introduce "Human Prime ↔ software application" as a direct relation:

> **The software application enters Faying State through the corresponding Human Prime's iFay.**

The responsible end is still the Human Prime. The iFay derivatively takes over the software application through Faying State; the mechanism is homologous to that of taking over a terminal in Phase 2. The software application itself does not stand on its own in Faying State.

## Three key differences

Phase 3 adds three additional complexities that need special handling on top of Phase 2's structure.

**Finer takeover granularity**. An iFay may take over only part of the software's functions — for example, allowed to place orders on someone's behalf, but not to modify the account security policy. Phase 3 must therefore express finer-grained "scope of takeover" at the protocol layer, homologous to the principle in Chapter 12 that "a Faying Action must be of bounded scope."

**Denser cross-boundary collaboration**. The software taken over may internally invoke multiple external services, third-party APIs, and remote cloud functions. Phase 3 must ensure that any call initiated through the taken-over software by the iFay still has its responsibility attributed to the original Human Prime; responsibility may not silently slip away across the cross-service call chain. This requirement directly answers the real-world pain point sketched in Chapter 1 — "no one can say clearly which parties handle data along the call chain."

**Stealthier side effects**. Compared with physical actions, software side effects (data writes, subscription changes, third-party account linkages) are harder for a Human Prime to perceive intuitively. Phase 3 must land the "information reachability" requirement of Chapter 11's Human View more explicitly — side effects must be disclosed in a way the Human Prime can come to know within reasonable cost, not buried deep in the call chain.

## Relation to the current period's scope

**Phase 3 is out of the scope of the current Faying Protocol design.** This chapter sketches Phase 3's existence to explain the direction of the Faying Protocol's evolution, not to commit to its delivery in this period. The concrete protocol form of Phase 3 will be borne by a separate later spec.

After Phase 3, the Faying Protocol covers Fay's relation with both hardware and software execution ends, but the discussion still revolves around "one Human Prime + one iFay." The next stage, Phase 4, extends the perspective to organizations: when there is more than one Fay and the responsible end is no longer a single natural person, how the Faying relation still keeps consistent attribution.

![Phase 3 concept](../../zh-CN/blueprint/illustration/phase3-concept.png)

![Phase 3 architecture](../../zh-CN/blueprint/illustration/phase3-architecture.png)
