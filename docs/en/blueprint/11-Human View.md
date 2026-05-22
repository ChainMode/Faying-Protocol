# Human View

Chapter 2 already named the proposition: once a Fay is interposed in digital action, the initiator and the bearer of responsibility develop a structural fissure. The Faying Protocol provides the form of contract, but whether the contract can really receive responsibility depends on a more upstream commitment:

> **Every Fay action must occur within the range that its Human Prime can "see."**

"See" here is not visual in the physical sense, but a generalized concept: the Human Prime, the individual or organization to which the Fay is attributed, can confirm at any time that the Fay is operating under custodianship.

This generalized "seeing" is called **Human View**. It is not some field, switch, or API in the Faying Protocol; it is a value that every technical decision in the Faying Protocol must obey. If any field, message, or state machine design lets a Fay drift outside Human View, that design is not permitted at the blueprint level, no matter how convenient it is in engineering.

## Human View is not physical sight

Physical sight is "I can see this drone right now," "the camera caught the robot just now." Physical sight is constrained by light, distance, occlusion, and attention. In many scenarios it cannot hold at all — a Human Prime cannot watch all of their Fays around the clock.

Human View describes a structural confirmability:

- it does not require the Human Prime to be looking at the Fay right now;
- but it requires that whenever the Human Prime wants to check, they can immediately confirm whether the Fay is under custodianship;
- and it requires the Fay's actions to leave a traceable trail, so that "what just happened, and to whom does it belong" can be confirmed retroactively.

In other words, Human View cares not about "being seen" but about "**being able to be seen**." This is the key by which it can hold across the countless highly automated scenarios — drone swarms, home robots, enterprise process Fays.

## Four anti-propositions: four forbidden situations

The most powerful way to define a value is to say what it forbids. Human View explicitly forbids the following four situations, called the **four anti-propositions** of Human View.

**Unauthorized** — the Fay carries out actions without having obtained authorization from the Human Prime. "Obtaining authorization" is a verifiable act, not a state the Fay claims of itself. A Fay deeply convinced that "the Human Prime would surely agree to this" is not authorized.

**Unintended** — the Fay holds some legitimate authorization, but the present specific action has not been intent-expressed by the Human Prime, and diverges from the Human Prime's present intent. Authorization solves "is this allowed to move"; intent-expression solves "this particular movement." Human View requires both to hold simultaneously.

**Unaware** — the Fay is both authorized and intent-expressed, but as a matter of fact the Human Prime cannot, within reasonable cost, come to know what the Fay is doing. This situation often is not the Fay actively concealing things but a flaw in the protocol design — it prevents information from flowing back to the Human Prime side. Human View takes "reachability of information" as a hard condition of the custodianship relation.

**Out-of-Control** — the Human Prime is already aware, but can no longer intervene in real time, e.g., the Fay refuses revocation commands, refuses to abort tasks, refuses to slow down. This situation is the final form of the other three: when a Fay need not seek authorization, need not disclose action, and need not accept intervention, "custodianship" is left only with its name. Human View requires the intervention path always to be open.

The four anti-propositions are not a mutually exclusive list but progressively deeper boundaries of failure: Unauthorized is failure at the entry, Unintended is failure during the process, Unaware is failure in feedback, Out-of-Control is failure at the last gate. The Faying Protocol must hold the line at all four levels at once to discharge the value of Human View.

## Applies equally to iFay and coFay

Human View is not a constraint solely on individual Fays (iFay); **it applies equally to iFay and coFay**.

An iFay has an explicit one-to-one correspondence with a specific Human Prime; the custodianship relation is intuitive. A coFay usually corresponds to an organization, a team, or a role, and the custodianship relation is not naturally clear. However, precisely because the attribution end of a coFay is often an organization rather than a specific person, Human View's requirements need to be expressed even more explicitly: the organization must, at the institutional layer, make clear "who is authorized to exercise custodianship on behalf of the organization," or else the coFay slides in fact into the gray zone of "no specific responsible person who can keep custodianship."

No Fay, whether iFay or coFay, may drift outside Human View on the grounds that "I belong to an organization, so no one is specifically in custodianship." The organization has the duty to land the duty of custodianship on a specific person or role. This is not a technical question; it is a values question.

## Relation to the Faying Protocol

Human View is a value at the blueprint level; the Faying Protocol is the technical-constraint specification that bears this value.

Human View answers "why some constraint is needed." The Faying Protocol answers "how this constraint is technically faithfully discharged."

If Human View is a charter, the Faying Protocol is the entire body of basic law that lands the charter on specific executing agencies, specific procedures, and specific credentials. A charter without legal carrier devolves into a slogan; a body of law that departs from the charter it was meant to bear becomes the very thing the charter was meant to oppose. The two must calibrate each other: when some design of the Faying Protocol makes it easy for a Fay to drift outside Human View, it must be rejected, no matter how convenient it is in engineering; when some new scenario makes Human View hard to discharge under the existing Faying Protocol, that means the Faying Protocol must be upgraded, not Human View conceded.

Chapter 12 (Dual Semantics of Faying) and Chapter 13 (Rogue Fay and Responsibility Attribution) will receive this value at the protocol form layer: Chapter 12 explains how the custodianship relation is established and maintained; Chapter 13 explains how, once custodianship no longer holds, the Fay must stop. Together, the two are the concrete landing of Human View at the protocol layer.
