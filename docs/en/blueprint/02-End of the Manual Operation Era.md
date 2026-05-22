# End of the Manual Operation Era

Chapter 1 sketched the present-day pain points of the Fay era. This chapter places them back into historical context to see one and the same thing clearly: the responsibility-allocation mechanism that has supported three decades of digital society in the Manual Operation Era is silently exiting.

## "Operation is responsibility" is an invisible old chain

Before Fays, every interaction between humans and the digital world stood on a plain fact: **the person who operates is the person who is responsible**.

Open an application, type text, press a button, light up a lamp at a remote endpoint, transfer a sum from an account — every action was initiated by a specific person, and every consequence eventually fell back on that person. Whether at the operating system layer, the web form layer, or the IoT terminal layer, human fingers, eyes, and judgment were embedded in the chain of every act. In auditing, the system needed to record only one fact: this account, at this time, did this thing. The person behind the account was the terminus of responsibility.

This plain chain of responsibility ran through the entire digital era. User agreements pinned responsibility to the registered account, enterprise internal control pinned it to the job code, financial regulation pinned it to the real-name identity, and criminal law, when tracing cyber crime, eventually traced back to the specific person sitting at the screen. The "data subject — processor — controller" tripartite model of GDPR and PIPL, OAuth's "user authorizes the application" logic, and IAM's "account binds permission" assumption all stand on this same invisible chain.

Every pain point in Chapter 1 essentially stands on this old chain. They are unsettling because people still subconsciously presume "the actor is the responsible party." Once a Fay enters, that presumption quietly stops holding, and the entire social infrastructure built upon it has yet to notice — that is the real source of the unease.

## Where the chain is broken

When a Fay acts on a terminal in place of a Human Prime, three things happen at the same time that never used to:

- the initiator of the action is no longer the Human Prime, but the Fay;
- the content of the action is no longer dictated step by step by the Human Prime, but inferred autonomously by the Fay;
- the consequences of the action still fall on the Human Prime and the persons and organizations to which they belong.

A structural fissure opens between the first two and the third. This fissure is not a technical fault, nor the "loss of control" of an individual Fay. It is the structural side effect that necessarily follows when this new species, the Fay, comes into being: **for the first time, the initiator of action and the bearer of responsibility are systematically separated**.

When a drone goes out of control, the initiator is the onboard Fay, and the consequences cannot be apportioned among user, manufacturer, and city authorities; in speech-on-someone's-behalf, the initiator is the Fay, and the consequences land on the person whose account hosts it; in privacy holding, what "holds the data and acts" is the Fay, and the consequences for any infringement have no clear destination; in regulatory vacuum, every country sees part of the act, and no country sees the full chain of responsibility. Whichever dimension you look at, the body of the fissure is the same: the initiator of the act no longer equals the bearer of responsibility.

The state produced by this systemic separation is the **responsibility vacuum**.

Once a responsibility vacuum is tolerated, it rapidly erodes the foundation on which the entire digital society runs. Law, insurance, credit, public opinion, regulation — all are built on the premise that "an act can be traced to some responsible subject." When Fays saturate society at scale, this premise no longer holds by default; it must be rebuilt.

## Three theoretical paths, only one is walkable

Faced with the responsibility vacuum, there are in theory three paths.

The first is to forbid Fays from acting. This is equivalent to forbidding cars on roads, electricity on grids, the spread of the Internet. It is engineerable, but in civilizational terms it is regression — every value of the Fay era described in Chapter 1 is abandoned along this path. The Faying Protocol does not adopt it.

The second is to let the Fay bear responsibility itself. That requires the Fay to have legal personhood, financial capacity, independent credit, and a mechanism for shared emotional accountability. As a philosophical proposition it is interesting, but for the foreseeable future no jurisprudence or social infrastructure can receive an "intelligent entity that is neither natural person nor legal person yet bears responsibility independently." This path is out of view for the current period.

The third is to bind control and responsibility together with an **explicit contract** — as long as the Fay is within this contract, its acts are attributed to a specific Human Prime; once it leaves the contract, it must immediately stop acting.

The third path does not require rewriting the law, inventing new personhood, or waiting for social consensus to reform. It only requires upgrading the old "operation is responsibility" chain of the Manual Operation Era into a contract chain that can be explicitly switched between human and Fay.

This path is not optimal. It is the **only walkable path** that can land today, that does not abandon Fay value, and that can stop the responsibility vacuum from spreading. That contract is the Faying Protocol.

## What it does, and what it does not do

The Faying Protocol is not a definition of Fay capability, nor a code of Fay conduct. It is the sub-protocol within the iFay protocol family responsible for the semantics of "control under custodianship and delegated control," answering a question that looks simple but has been silently answered for thousands of years in the Manual Operation Era:

> **For this act, right now, who is finally responsible?**

The Manual Operation Era's answer was obvious — the person whose hand operated. In the Fay era this answer no longer holds by default; a contract must explicitly, verifiably, and revocably make the answer clear.

The Faying Protocol abstracts the core of this contract into two interdependent primitives. **Faying** denotes that a Fay, a terminal, or a software application is under the custodianship of some Human Prime; once Faying is established, all of the Fay's acts are attributed to that Human Prime. **Rogue State (Rogue Fay)** denotes that a Fay is currently not in any Faying relation; in this state the Fay must immediately stop all outward action — its existence is permitted, its action is not.

The relation between these two primitives is not a technical "switch"; it is an ethical bottom line that may not be tolerated to break:

> **There exists no Fay action without a responsible party.**

The entire purpose for which the Faying Protocol exists is to keep this bottom line technically faithfully discharged even after Fays saturate society at scale. What the later chapters answer is not "do we need this contract" — that has been answered by reality — but "how do we land this contract at the protocol layer, in engineering practice, and across sovereigns and vendors in production environments."

![Manual Operation Era illustration: humans operate terminals and software directly, themselves the responsible subject](../../zh-CN/blueprint/illustration/human-operation-era.png)
