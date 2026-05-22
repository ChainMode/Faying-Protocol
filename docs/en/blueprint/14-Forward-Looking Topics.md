# Forward-Looking Topics

> **The topics below are out of the scope of the current Faying Protocol design.**

This is the last chapter of the blueprint, and the only chapter whose style differs from all the others. It draws no conclusions; it honestly enumerates the open questions. Doing so has two purposes: to let readers, after finishing the blueprint, know precisely what the current Faying Protocol solves and what it does not; and to leave clear plug-in points for later separate specs.

Every topic in this chapter is **left without conclusion** in this period. If a question that looks simple has not been answered, it is not an oversight; it is restraint.

## Other kinds of Faying relations

This period's Faying Protocol covers only one kind of relation: **Human Prime ↔ iFay**. Beyond it, at least the following four kinds of relations are not yet brought into protocol design.

**A direct Faying relation between human and terminal** — this period's blueprint chooses iFay as the only entity form trusted to bear the custodianship contract; therefore the terminal's "being in the controlled state" must be expressed derivatively through the iFay's Faying State. Whether at some future stage to introduce "a Human Prime establishing a Faying relation directly with a terminal" requires first answering several deep questions: does the terminal have sufficient "identity integrity" to bear a custodianship contract? Will a direct relation, by bypassing iFay at the protocol layer, make the chain of responsibility harder to trace and worsen Human View's visibility instead? When the two paths "direct" and "derivative through iFay" coexist, how is uniqueness of attribution to be guaranteed? These questions have no satisfactory answer in this period.

**A direct Faying relation between human and software application** — homologous to the previous item, but with one extra layer of complexity. A software application is itself often modular, cross-process, and cross-network. When establishing a Faying relation with an application directly, the boundary of "the application" itself must first be precisely defined, and that definition has not yet converged across different ecosystems and deployment forms. The reason this period made Phase 3's extension "derivatively take over the software application through the iFay" is precisely to defer this boundary-definition problem.

**iFay ↔ coFay collaboration and delegation** — this is the core topic of Phase 4. This period does not introduce the protocol form of coFay custodianship for two reasons: the attribution end of a coFay is usually an organization or a role, and how an organization institutionally lands the duty of custodianship onto specific people or roles is itself a complex discussion across institutions, law, and corporate governance; and the protocol form for "responsibility transfer is not lost" in cross-Fay collaboration needs Phases 1 through 3 to be stable before it has a fitting plug-in point.

**iFay ↔ iFay collaboration** — when multiple iFays (each attributed to a different Human Prime) collaborate across custodianship relations to complete one act, it raises the issue of "the multi-person path of action attribution transfer": should the act be attributed to the initiator, the receiver, or both by some apportionment rule? This question is similar to the legal design of "sub-delegation between agents" in real-world society, but the high-frequency density of collaboration in the Fay era makes traditional law's processing speed lag far behind. This topic needs the simultaneous evolution of law, protocol, and social governance before a stable answer can be obtained.

The four kinds of relations above all belong to long-term evolution directions of the Faying Protocol. They will be enrolled progressively in Phases 2 through 5 of the Mission Path, but the protocol form of each is borne by separate later specs and is out of the scope of this period.

## B4: Location reporting during Rogue

Item 4 of dimension B in Chapter 13 (B4) is the only protocol design point in this blueprint explicitly marked "no conclusion this period."

### Description of the topic

When a terminal taken over by an iFay (e.g., a drone) enters Rogue Fay, should it continue actively to report its physical location or terminal state to the attributing Human Prime?

For example: Jack's drone, in the course of a task, loses connection to Jack (satisfying triggering condition 4 in Chapter 13, "the Human Prime is offline or unreachable for an extended time"), and enters Rogue Fay. The drone's physical location is still changing — affected by inertia, wind, autonomous-landing algorithms, and so on. The question is: should this drone keep actively reporting its position, battery level, and other terminal state to Jack's side?

### A two-sided pull

**In favor of continued reporting** — the more a disconnected Fay reports, the easier it is for the Human Prime to find it again and re-establish Faying. From the perspective of recoverability, "location is visible" is a capability that protects the Human Prime's interest.

**Against continued reporting** — once a Fay continues to report its location in Rogue, an attacker may exploit that channel: intercepting location information to grasp the Human Prime's range of activity; forging the reporting channel to impersonate the Human Prime's side and induce Fay action; using "continuous reporting" as a means of attack reconnaissance.

Both sides of the value are legitimate, and both fit the inner spirit of Human View, but they point to opposite protocol design choices. In the rogue state of Rogue Fay, "active reporting" can equally protect the Human Prime or betray the Human Prime.

### Possible middle paths

Possible solutions in the future include but are not limited to the following lines of thought. The blueprint does not pre-select among them.

**Differentiated handling by Rogue cause** — Human Prime actively revoked → conceal location; connection lost / timeout → reveal location; intrusion alert → reveal location. Use "why entered Rogue" as the criterion for whether to report.

**Choose explicitly via pre-authorization** — at the time the Faying Action is initiated, have the Human Prime explicitly declare "if I subsequently lose connection, is this terminal allowed to keep reporting location?"

**Tiered reporting** — do not report precise location, but report minimum signals that do not expose spatial information, such as "I am still in Rogue, health is normal."

None of these three lines of thought is adopted as the conclusion in this period. They belong to topics that need full discussion during the Faying Protocol's evolution in Phases 2 through 5, and should absorb input from privacy, security, and regulatory parties.

### Relation between this topic and Chapter 13

B4 is merely **to be discussed**, not **to be executed**. Before the protocol specification document lands a final choice for B4, all other rules given by Chapter 13 — B1–B3 allowed, the full rules of A1–A4, C1–C3, D1–D4 — remain fully in force. B4's factual position in this period is "the protocol layer neither mandates nor forbids implementation," leaving the decision to specific implementers and future specs.

## End of the blueprint

By this point, you should be able to answer the following three questions about the Faying Protocol on your own:

- **What is it?** A contract that explicitly expresses, between Human Prime and Fay, "how control and responsibility are delivered."
- **What does it carry today?** The ethical bottom line of Chapters 11 through 13 + the minimum contract form of Phase 1.
- **What does it not yet carry?** All the forward-looking topics honestly enumerated in this chapter.

A blueprint that thinks it has answered every question is the most likely to give up things that should not be given up when new scenarios appear. A blueprint that honestly lists the open questions is, on the contrary, more able to keep the bottom line uncompromised through future extensions.
