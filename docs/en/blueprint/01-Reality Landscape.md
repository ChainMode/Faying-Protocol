# Reality Landscape

AI Agent has become a common term in the software world. It refers to a class of intelligent execution instances that can autonomously carry out specific functions — give it a goal, and it plans, calls tools, and produces results on its own.

But across enterprise applications, regulated industries, and cross-sovereign scenarios, the deployment of AI Agents almost always stalls at the same threshold: **when an Agent makes a mistake, oversteps, or breaches contract, responsibility cannot be traced back to a concrete responsible party who can be sued and made to pay damages**. This deadlock is by now an industry consensus. CIOs, legal counsel, insurers, and regulators all see the threshold, but no off-the-shelf technical or legal tool, on its own, can step over it.

The concept of Fay is reverse-engineered from precisely this threshold. The entire distinction between Fay and Agent comes down to one thing: **a Fay must be mandatorily mounted to a responsible entity**.

- **iFay** — Individual Fay. An intelligent entity mandatorily one-to-one mounted to a Human Prime. At the protocol layer, an iFay carries the specific natural person it belongs to; remove that attribution, and it is no longer an iFay.
- **coFay** — A shared Fay. It is permitted to operate only when explicitly attributed to an individual or organization with the legal capacity to bear responsibility. Once that attribution lapses, it must stop.

This definition lifts traceability of the responsible party from a compliance problem patched at the application layer up to a condition of existence at the protocol layer. Under the definition of this blueprint, a Fay that cannot be mounted to a responsible entity is simply not a Fay.

But a definition is just a name. The real problem is engineering: **how do we ensure an AI Agent always operates in a state of unshakable responsibility?** The answer to that question is the Faying Protocol. It defines how the relation of "mounted to a responsible entity" is established, sustained, verified, and revoked, so every action a Fay takes corresponds to a traceable Human Prime or organizational role.

This chapter lays out the concrete shape of this threshold across seven dimensions, and shows why the prevailing combination of engineering and legal tools — IAM, OAuth, product liability law, platform compliance, AI Alignment — cannot bear any one of them.

## Economy and Labor Structure

The takeover of base-level work is largely complete, while the legal framework of responsibility still lives at the level of job codes.

In a mid-sized e-commerce company, the six categories — customer service, operations, procurement, reconciliation, collections, and compliance review — today have sixty to eighty percent of their daily work handled by Fays. The introduction was gradual, mostly framed as "tool upgrades." The result: when regulators retroactively trace an anomalous decision, the responsible person on the job-code chart cannot explain on what day, by which Fay, under which rule that decision was made. She cannot explain it, and she cannot bear it, but the legal system's pursuit of her does not stop on that account.

Labor law, tax law, and job-responsibility regimes have not kept up. They assume the person in the role is the actor. That assumption supported the entire allocation of responsibility for digital labor over the past three decades; today it is silently failing.

One layer deeper, Fays have already begun acting between organizations. A logistics platform's procurement Fay and a warehousing platform's quotation Fay autonomously close a seven-figure contract overnight; both systems record `Fay-Procurement-A and Fay-Quotation-B reached agreement at 03:14:27`. When something goes wrong, both legal teams look for their respective "head of procurement" and get the answer "I don't know about this transaction." Contract law assumes both sides have specific contracting natural persons; that assumption does not hold at the density of Fay-to-Fay collaboration. Each additional contract of this kind adds another piece of legal debt that courts must answer case by case.

## The Physical World

A Fay in physical space is more dangerous than a Fay in information space. The reason is simple: errors in information space can be undone; errors in physical space cannot.

Drone delivery is now routine in many places. Home-service robots have entered the consumer market. Self-driving deployment mileage doubles year over year. None of these devices is a remote-controlled extension — onboard Fay, cloud Fay, and vendor strategy together produce decisions in a three-way mix. When a drone finally hits a curtain wall, no off-the-shelf responsible end can be named: not the onboard Fay, because it is just a program; not the cloud Fay, because it runs on another company's infrastructure; not the manufacturer, because it can produce evidence that "our product showed no such behavior pattern in testing"; not the user, because the user only pressed "go."

Insurance companies have quietly begun, over the past two years, to refuse coverage on several categories of products that contain Fay decision capability. The reason is not that these products are more dangerous — by the statistics, their accident rates are even lower — it is that their accidents cannot be assigned. The essence of insurance is the conversion of assignable risk into a price. Risk that cannot be assigned cannot be priced.

Product Liability Law assumes a product has an identifiable designer, and that the designer is liable for design defects. The "design" of a Fay is distributed: the foundation model from A, fine-tuning from B, runtime from C, integration from D, and invocation pattern decided by E. When something goes wrong, five companies point at one another, and regulators face an unsolvable attribution graph.

Criminal law goes deeper still. Criminal law only pursues those with criminal capacity. A Fay is not such a subject. When a Fay directly causes bodily harm, criminal law can find no concept of "actor" to receive the act. This does not mean no one is at fault — it means the logical chain of criminal law breaks at the Fay.

## Information and Social Trust

Fays speaking on someone's behalf are not the deepfakes of the news; they are already a routine feature for ordinary users. A person has a Fay reply to dozens of comments, post a few entries, and maintain the "warmth" of social ties on social platforms every day. The replies "sound like him," because the Fay continually learns his tone; but the content is generated autonomously by the Fay, and he has not even read it.

Fays writing content carry an ever larger share of the "creative long tail" on creator platforms — vast amounts of product blurbs, campaign promotions, and Q&A answers ride on real-person accounts but are produced by Fays. Fays signing contracts on someone's behalf are now routine in subscription services, energy procurement, and ad-slot bidding. A contract shows "signed by user X at a given moment," yet user X was asleep at that moment.

Platforms have begun feeling the shift. The content moderation systems of major platforms, over the past two years, have been forced to process a new question: was this content written by the user, written by AI at the user's instruction, or generated autonomously by AI under the user's account? The three cases correspond to entirely different responsibility, handling strategy, and compliance risk, and platforms have no technical means to reliably distinguish them. They can only guess from rough statistical features, with mass false positives and mass missed cases at the same time.

A more sensitive but unavoidable category: election-cycle public-opinion data has shown, more than once, that the curve where "support for some topic rises from 18% to 41% in three days" is backed by hundreds of thousands of Fay accounts producing convergent statements in sync. Commercial credit has seen Fay-led mass endorsement: in the reviews of a new brand, four hundred of five hundred entries are generated by Fays through the joint work of three agencies. Each review "looks like the experience of a real user," but every author does not exist.

This rewriting is not a single major attack; it is daily, continuous, and cumulative. Society processes information every day on the implicit assumption "this was posted by such-and-such person." When an ever larger share of that assumption no longer holds, the foundation of social trust is being silently hollowed out, and the hollowing leaves no obvious alarm.

## Privacy and Data

The premise of letting a Fay "act on your behalf" is that it must "know you." It needs to know your preferences, habits, relationships, finances, health records, schedule, location, intent. A Fay is the entity that has known a Human Prime more deeply than anything in history — more than a spouse, because it is by your side every day; more than a doctor, because it can stitch records across all hospitals; more than your employer, because it can stitch work email, personal email, and your calendar.

The premise for all of this is a relationship of trust between the Fay and the Human Prime. Today that "relationship" is usually no more than a checkbox in a user agreement and a toggle inside a product. That form is far short of what is needed to bear knowledge so deep.

Fays do not run in isolation either. A personal Fay handling a task may invoke a cloud-side coFay, which in turn invokes third-party vendor capabilities, which run on yet another company's infrastructure. Along this invocation chain, how many parties does the user's private data pass through? Is the passage by reading, copying, or rewriting? Which parties merely transit, and which retain copies? No one can answer clearly — each party can promise only for its own segment, and there is no global view.

GDPR and PIPL are both built on a tripartite model: data subject, data processor, data controller. The model assumes all three parties are organizations or natural persons, identifiable, accountable, and inspectable by regulators. With Fays in the picture, the tripartite model immediately loses its mapping. Is a Fay a processor or a controller? Or somewhere in between? Or newly classified as "agent of the data subject" — but the concept of agent itself assumes the agent has legal personhood.

Regulators across regions are trying to fill this gap. But one premise cannot be avoided: the protocol layer must first state the facts clearly — which Fay this data flow belongs to, which Human Prime it is attributed to, whether it is in Faying State or in Rogue state, whether it is shared with third parties. Without that, legal docking will always come up empty.

## Cross-Sovereign and Cross-Platform

The early Internet established TCP/IP — a cross-sovereign, cross-vendor transport protocol. It did not solve "what the application layer does," but it solved "how any two parties can exchange data without trusting each other."

The Fay era lacks an equivalent "cross-sovereign, cross-vendor protocol of mutual trust." When a US-side Fay collaborates with a China-side Fay to complete a cross-border e-commerce transaction, three questions have no shared answer: who proves the other side really is the Fay it claims to be? Who proves it is, at this moment, under the custodianship of its Human Prime? Who bears the responsibility when something goes wrong? Today every cross-border Fay collaboration scenario answers these three questions in an ad hoc, bilateral, contractual way. This N²-contract pattern does not scale when the number of Fays explodes.

To make Fays interoperate at all in the absence of a unified protocol, engineers stack temporary measures layer upon layer: each vendor issues its own API key, each platform builds its own OAuth proxy, each cross-vendor integration writes its own compliance covenant. The system is barely workable when Fays number in the hundreds of thousands. When they grow into the hundreds of millions or billions, the total operational cost of this system will far exceed the total benefit Fays themselves bring. This is an exponential curve in engineering terms; it cannot be solved by "throwing more engineers at it" and must be flattened from the root by unifying the basic facts at the protocol layer.

The most subtle pain point is structural vacuum. A Fay serves end users in country A, runs on a cloud in country B, was trained by a vendor in country C, uses a foundation model from country D, and invokes third-party capabilities from country E. Each of the five countries has data protection law, AI regulation law, and product liability law, but the five legal regimes do not interconnect, and each can only reach a small segment of this chain. One day regulators will be forced to compress cross-border Fay operation by administrative measure — at which point the loss is not only to the Fay industry, but to every value society could have obtained from the Fay ecosystem.

## Individual Identity and Agency

Identity authentication systems — two-factor, biometrics, Passkey, OAuth — all assume the two ends of authentication are "application ↔ human user." When a Fay is interposed in the middle, the system starts to feel off: the application sees "this is the user's token," but the request is initiated by the Fay; the user has enabled "fingerprint unlock so the Fay can act for me," but whether each subsequent Fay action still represents the user's present intent cannot be continuously verified; an attacker who captures one of the user's authorization windows can impersonate the Fay and do anything inside that window, with both application and user hard-pressed to detect it.

This is the structural fissure of identity authentication in the Fay era. It cannot be patched by "adding another factor." The question is not "is it the user logging in," but "is this specific behavior occurring under the user's custodianship."

There is a long-standing legal concept called **agency** — one person can authorize another to act on their behalf in certain matters. The agency relation has clear legal rules: scope of agency, term of agency, the agent's duty of care, the legal consequences when an agent exceeds authority.

When Fays enter agency relations, all these rules need to be re-examined. How is a Fay's "duty of care" to be defined — must it stop and ask when the scope of agency is ambiguous? How is "exceeding agency" by a Fay to be detected — how far must its judgment diverge from the principal's true intent before it counts as exceeding? Where is a Fay's boundary of action when the principal is incapacitated? Does the principal's death automatically terminate the Fay's agency, or can some agencies continue into estate administration?

These are not paper exercises for legal scholars. They are surfacing today, case by case, in hospitals, banks, notary offices, and courts; each case is handled by a judge on intuition, and the handlings contradict one another. The premise for the agent legal regime to dock with the Fay era is that the protocol layer can stably tell the legal system: under what Faying relation this Fay action was initiated, what scope and term of agency it corresponds to, and whether it is within its effective period.

## Why Existing Solutions Fall Short

Reading this far, a natural question arises: these pain points are real, but are there no existing tools? IAM, OAuth, API rate limiting, Webhook signing, AI Alignment — aren't they already solving some of this?

The answer is that they solve adjacent problems, not the core problem.

**IAM solves "who is the account," not "to whom does the act belong."** The whole capability of an IAM system orbits account identity — what the account is called, which organization it belongs to, which permissions it has. Its design premise is that there is a person behind the account, and the person's identity is the attribution of the act. A Fay is not an account; it is an entity attached behind an account that takes action. When a Fay initiates action under an account identity, all IAM sees is "this account has the right to do this," but it cannot answer "is the person behind the account doing this right now, or is the Fay doing it."

**OAuth and Webhook signatures solve "the legitimacy of the call," not "the attribution of responsibility."** OAuth solves "is application A authorized to call application B on the user's behalf"; Webhook signing solves "is this callback really from the claimed sender." Both concern the legitimacy of the call chain; neither carries any field expressing "to which specific Human Prime does the underlying act belong." When a Fay calls some API with a token obtained via OAuth, OAuth sees "the token is valid, the call is legitimate," but it does not know whether the call was initiated by the Fay in Faying State or in Rogue state in violation of the rules. OAuth and Webhook do not need to be replaced; they need to be covered by a protocol layer whose dedicated concern is "attribution of the act."

**Agent platform compliance frameworks are closed; platforms do not interoperate.** Each Agent platform builds its own compliance framework — terms of use, content moderation, abuse detection, statements of responsibility. These frameworks are relatively self-consistent within the platform, but they have two fundamental limits: platforms do not interoperate; and granularity stops at the account or application level, never reaching the specific act. A compliance framework can ban an abusive account, but it cannot make a real-time judgment at the level of "should this act happen."

**AI Alignment cares about the inner values of the Fay; it does not solve the attribution of an external responsible party.** Alignment solves "what the Fay wants to do"; the Faying Protocol solves "whether the Fay may act right now, and to whom the act belongs once it acts." A perfectly aligned Fay can still produce action without a Human Prime's custodianship, and that action has no one to receive responsibility. A completely unaligned Fay can still be locked in Rogue state and forced into inaction. Alignment is the inner ethics of a Fay; the Faying Protocol is the outer responsibility regime of a Fay. Both are indispensable; neither can replace the other.

## Closing

The pain points in the seven dimensions span industry, law, and society, but they intersect at the same thing:

> **When a Fay acts, who is responsible for the act?**

The Manual Operation Era had a plain answer that needed no protocol to express: the person whose hand operated. In the Fay era this answer no longer holds by default; it must be expressed clearly by an explicit, machine-readable protocol that can be jointly verified by different sovereigns and different vendors.

This is the entire reason the Faying Protocol exists.
