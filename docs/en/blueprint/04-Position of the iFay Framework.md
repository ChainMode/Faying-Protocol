# Position of the iFay Framework

This chapter answers only two questions: roughly what does the iFay framework look like, and where does the Faying Protocol sit within it?

The iFay framework itself has broad coverage and many components; any one of them, even slightly unfolded, leads into technical details of fields, protocols, and message formats. The three categories of assets in this repository — blueprint, protocol specification, and schema — carry only the Faying Protocol. All members of the iFay protocol family other than the Faying Protocol are uniformly referenced by linking to [ifay.ai](https://ifay.ai); this repository does not restate, rewrite, or derive them.

## Outline of the iFay framework

Following the overall design at [ifay.ai](https://ifay.ai), the iFay framework can be roughly understood as a four-layer structure.

**The entity layer** contains two kinds of intelligent entities bound by the protocol. **iFay** (Individual Fay) is mandatorily one-to-one mounted to a specific Human Prime — remove that attribution, and it is no longer an iFay. **coFay** is a shared Fay; it is permitted to operate only when explicitly attributed to an individual or organization with the legal capacity to bear responsibility. Whether iFay or coFay, the Faying Protocol discussed in this blueprint constrains them equally: once attribution lapses, the Fay must stop.

**The core components** include several inseparable parts inside every Fay entity. **FayID** is the unified, unique identity of a Fay, the identity foundation for entering any custodianship relation. **Ego** is the baseline paradigm aligned with a specific individual's or role's profile, constraining the Fay's autonomous space along value orientation, interest preferences, habits, cognitive and skill boundaries, permission boundaries, and working style. Ego is not a giant AGI model; it is a "personality boundary." **Runtime** is the virtual runtime of a Fay, allowing iFay and coFay to run compatibly across different terminals, operating systems, and embedded application scenarios. FayID and Ego are the two preconditions that allow the Faying Protocol to take effect — the former carries identity attribution, the latter carries the boundary of behavior.

**The protocol family** includes a set of protocols by which an iFay connects, perceives, and collaborates with the world. Beyond the subject of this blueprint, the **Faying Protocol**, it includes at least: bidirectional transport protocols related to terminal control, UI-friendly protocols facing human user interfaces, semantic communication protocols between iFay and coFay that strip the UI translation layer, broadcast-and-subscribe protocols for cloud-side capabilities, and any future members. For technical details of the protocol family, see [ifay.ai](https://ifay.ai); this repository does not include them.

**The value structure** corresponds to a new model of labor structure and value distribution. This layer includes systemic shifts: human labor exiting work, flattening of knowledge, universal subsistence guarantees, new value creation, new social stratification — with mechanisms such as MeriToken bearing value measurement. This is the long-term backdrop of the iFay framework; it does not land directly on the Faying Protocol specification. See [ifay.ai](https://ifay.ai) for details.

## The position of the Faying Protocol within it

Putting the four layers together, the position of the Faying Protocol within the iFay framework can be precisely anchored as follows:

> **The Faying Protocol sits above the "entity layer" and "core components" and is the sub-protocol within the protocol family responsible for the semantics of "control under custodianship and delegated control." It turns the root question — "is FayID attributed to some Human Prime" — into a set of connection states and actions that can be established, sustained, and revoked.**

It is not a definition of Fay capability, so it does not specify what a Fay can do. It is not a code of Fay conduct, so it does not specify how a Fay should do it. It answers only one question:

> **For this Fay's act, right now, who is responsible?**

For this reason, the Faying Protocol is neither the most dazzling nor the most profound protocol in the iFay framework, but it is the one that may not be skipped. Once it is missing, the entire iFay framework immediately degrades into an ordinary Agent ecosystem, carrying the responsibility vacuum described in Chapter 1 into society.

## Boundary between this repository and the iFay framework

```
                 +-------------------+
                 |   ifay.ai panorama |
                 |   iFay framework   |
                 |     (four layers)  |
                 +-------------------+
                          │
                          │  This repo unfolds one member
                          ▼
            +---------------------------+
            |   Faying Protocol project  |
            |   (all assets of this repo)|
            +---------------------------+
                          │
            ┌─────────────┼──────────────┐
            ▼             ▼              ▼
        Blueprint    Protocol Spec      Schema
   docs/{lang}/    docs/{lang}/         schema/
    blueprint/    specification/   (not delivered this period)
   (this spec)  (later, separate spec)
```

All three categories of assets in this repository carry only the Faying Protocol. Any in-depth unfolding of other members of the iFay framework is out of the scope of this repository; please go to [ifay.ai](https://ifay.ai) directly.

![iFay framework (alpha1) overview: the Faying Protocol sits at the contract layer of the custodianship relation](../../zh-CN/blueprint/illustration/ifay-framework-alpha1.png)

![iFay title banner](../../zh-CN/blueprint/illustration/ifay-title-banner.png)
