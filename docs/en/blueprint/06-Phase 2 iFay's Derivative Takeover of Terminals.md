# Phase 2: iFay's Derivative Takeover of Terminals

After Phase 1 has stabilized the minimal contract form of "Human Prime ↔ iFay," Phase 2 turns its attention to the relation between iFay and terminal devices.

Terminal here is meant in a generalized sense — a drone, a robot, an intelligent vehicle, an IoT gateway, a personal computer, a phone all belong to this class. Their common feature: hardware that can be driven, physical actions that can be initiated, and physical consequences that can result.

The key in Phase 2 is not to let an iFay control more things; it is to enroll every terminal it takes over clearly into the Faying chain of responsibility.

## Derivative, not direct

Phase 2 does not introduce "Human Prime ↔ terminal" as a direct relation. Its way of extension is indirect:

> **The terminal enters Faying State through the corresponding Human Prime's iFay.**

The responsible end is still the Human Prime; that does not change. The iFay is still the entity that bears Faying State, but it now carries an additional duty — to act as custodian on behalf of the terminals it takes over. The terminal does not stand on its own in Faying State; its "being in the controlled state" is derived from the Faying State of the iFay it currently belongs to.

To continue with the analogy introduced in Chapter 12 — Jack handing the wheel to an AI driver — Phase 2 cares about: when this AI driver subsequently drives the car, turns, brakes, and changes lanes, how each "control state" of the wheel, throttle, and turn signals stays consistent at all times with whether Jack is still under custodianship.

## Three core topics

**Visibility of takeover**: when an iFay takes over a terminal, this must be observable in real time by the Human Prime and by the outside — which terminal, in which time window, taken over by which iFay. This is the extension of Human View at the terminal layer.

**Chained exit**: when an iFay enters Rogue Fay, all terminals it has taken over must simultaneously lose the derivative effect of Faying. A terminal must not be permitted to keep executing previously unfinished physical actions while the iFay has already left custodianship — this corresponds exactly to the prohibition under D3 in Chapter 13.

**Irreversibility of physical action**: actions in the physical world are strongly irreversible. A drone has already delivered, a robotic arm has already moved, a vehicle has already turned — after-the-fact audit cannot undo it. Phase 2 must take "rather not act than wrongly act" as the default bias at the protocol layer, not patched up by audit later.

The third item is especially critical. The moment any uncertainty about Faying State arises, the terminal defaults to "passive waiting" rather than "optimistic execution."

## Relation to the current period's scope

**Phase 2 is out of the scope of the current Faying Protocol design.** The Faying Protocol in this period covers only Phase 1. The concrete protocol form by which "an iFay derivatively takes over a terminal through Faying" in Phase 2 will be defined in a separate spec after Phase 1 has stabilized. This chapter sketches the existence and direction of Phase 2 so that the Mission Path has a complete picture of evolution.

Phase 2 is the first step where Faying walks out from "between software" into the "software-physical" boundary. From here on, Faying relations no longer concern only bits but begin to concern the physical consequences pushed by bits. This fact is the "gravity" that Phases 3 through 5 must look back to from time to time.

![Phase 2 concept](../../zh-CN/blueprint/illustration/phase2-concept.png)

![Phase 2 architecture](../../zh-CN/blueprint/illustration/phase2-architecture.png)
