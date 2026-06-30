---
title: "Faying Protocol/1.0 — §5 Protokollnachrichten"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: de
part: "Kapitel 5 von 11 (Protokolltext)"
---

> Protokolltext-Navigation: [Inhaltsverzeichnis](./README.md) | vorheriges [§4 Datenmodelle](./04-Datenmodelle.md) | nächstes [§6 Kryptografie](./06-Kryptografie.md)

## §5 Protokollnachrichten

Dieses Kapitel beschreibt alle Nachrichten der Faying-Protocol-Ebene: die Kodierungsregeln, die Envelope-Struktur, das Inventar von 7 Geschäftsnachrichtenklassen zuzüglich 1 Fehlerantwortklasse sowie die Zuordnungstabelle zwischen Fehlercodes und Audit-/HP-Sichtkanal-Pushes.

> **Hinweis zur Maßgeblichkeit der Typen**: Die in den TypeScript-Blöcken dieses Kapitels referenzierten Typen `Mandate / Scope / Grade / PresenceSignal / PresenceRequirement / Endorsement / SignatureBundle / Attestation / WebAuthnAssertion / AtomicAction / RevokeReason` haben ihre **maßgeblichen Definitionen** in §4 Datenmodelle (CDDL); die TypeScript-Ansicht ist eine **Non-normative** menschenlesbare Ansicht, und wo die beiden voneinander abweichen, ist §4 CDDL maßgeblich.

### §5.1 Kodierungsregeln

- **Primärformat (CBOR)**: Die Standardkodierung für jede Übertragung auf der Leitung ist CBOR ([RFC 8949](https://www.rfc-editor.org/rfc/rfc8949)); der HTTP-`Content-Type` muss als `application/faying-protocol+cbor` deklariert werden.
- **Interoperabilitäts-Fallback (JSON)**: JSON ([RFC 8259](https://www.rfc-editor.org/rfc/rfc8259)) wird nur in Debugging-/Browser-/Human-Review-Szenarien verwendet; der HTTP-`Content-Type` muss ausdrücklich als `application/faying-protocol+json` deklariert werden; die Sicherheitsäquivalenz wird durch identische Feldsemantik und identisches Signaturformat gewährleistet.
- **Deterministische Kodierung**: Jedes signierte Objekt muss vor dem Signieren gemäß der Deterministic-Encoding-Regel aus RFC 8949 §4.2.1 CBOR-serialisiert werden, um Mehrdeutigkeiten der JSON-Serialisierung zu vermeiden; auch unter der JSON-Form bleibt die Signatureingabe der Hash der Deterministic-CBOR-serialisierten Bytefolge (siehe §6.3).
- **Transportbindung**: standardmäßig HTTP/1.1 und HTTP/2; Mandate-Service-Endpunkte folgen `POST /faying-protocol/v1/{verb}`; eine Bindung an gRPC (`faying-protocol.v1`-Dienst) oder WebSocket / SSE (`faying-protocol.v1`-Streaming) ist ebenfalls erlaubt. Alle Transportschicht-Bindungen müssen die Nachrichtenschicht-Signaturen und Nonces bewahren; das Ersetzen von Signaturen auf Nachrichtenebene durch die TLS-Kanalidentität der Transportschicht ist verboten.

### §5.2 Envelope-Struktur

Alle Nachrichten verwenden den einheitlichen Envelope `FayingProtocolEnvelope`:

```typescript
interface FayingProtocolEnvelope<TPayload> {
  header: {
    version:    "Faying Protocol/1.0";
    msg_type:   FayingProtocolMsgType;
    msg_id:     string;        // ULID
    issued_at:  IsoTime;
    expiry:     IsoTime;
    nonce:      Nonce;
    grade:      Grade;         // aktuelle Sitzungsstufe (von der RP genutzt, um Anfragen niedriger Stufe abzulehnen)
    issuer:     HumanPrimeID | string;
    subject:    FayID;
  };
  claims:      TPayload;
  attestation: Attestation;
  signature:   SignatureBundle;
}

type FayingProtocolMsgType =
  | "BOOTSTRAP"        | "BOOTSTRAP_RESP"
  | "PRESENCE"         | "PRESENCE_ACK"
  | "GRADE_SWITCH"     | "GRADE_SWITCH_RESP"
  | "DELEGATE"         | "DELEGATE_RESP"
  | "REVOKE"           | "REVOKE_RECEIPT"
  | "FAYING_REQUEST"   | "FAYING_REQUEST_RESP"
  | "DISCLOSURE"
  | "ERROR";
```

**Invarianten auf Envelope-Ebene**:

- Jedes fehlende oder typfalsche Feld → einheitliche Ablehnung mit `E_PROTOCOL` (siehe §5.4).
- Innerhalb eines Fensters von `2 × max_message_lifetime` wird `nonce` für dasselbe `subject` höchstens einmal akzeptiert; Wiederholung → `E_REPLAY`.
- `expiry` muss endlich und `> issued_at` sein; abgelaufene Envelopes gelangen nicht in den Geschäftsverifikationspfad und werden direkt mit `E_PROTOCOL` abgelehnt.
- Die Eingabe für `signature` muss `H( Deterministic-CBOR( Envelope_without_signature ) )` sein (siehe §6.3).

### §5.3 Nachrichteninventar

Dieses Protokoll definiert 7 Klassen von Geschäftsnachrichten: BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE / REVOKE / FAYING_REQUEST / DISCLOSURE, zuzüglich 1 Fehlerantwortklasse ERROR (siehe §5.4).

#### §5.3.1 BOOTSTRAP (Faying Action)

**Zweck**: Der Human Prime etabliert über BOOTSTRAP ein Mandate beim MS und stellt der iFay eine Mandatsautorisierung aus. BOOTSTRAP ist **der alleinige legitime Faying-Action-Einstieg** des Faying Protocol.

```typescript
interface BootstrapClaims {
  human_prime:   HumanPrimeID;
  fay:           FayID;
  scope:         Scope;
  grade:         Grade;
  presence_req:  PresenceRequirement;
  not_after:     IsoTime;          // muss endlich sein
  human_witness: WebAuthnAssertion; // user-verification = true
  endorsement?:  Endorsement;       // optional; falls vorhanden, wird ein Endorsed Mandate ausgestellt (siehe §4 / §11)
  faying_request_ref?: string;      // unter dem IF-initiierten Pfad referenziert dies die zugehörige FAYING_REQUEST.msg_id
}
```

**Erfolgsantwort**: liefert das vollständige `Mandate`-Objekt zurück (einschließlich `signature_bundle`).

**Harte Bedingungen auf Protokollebene**:

- `not_after` muss endlich und `> not_before` sein; `∞` und negative Werte sind verboten; Verstoß → einheitliche Ablehnung mit `E_PROTOCOL` (im Einklang mit §3.1 I-MS-1 / Property 7).
- Fehlendes `human_witness`-Feld oder ungültige Signatur → einheitliche Ablehnung mit `E_HUMAN_WITNESS_REQUIRED`; es existiert kein legitimer Pfad für IF / MS / Supervisory Agent, um HP beim Abschluss der Bestätigung zu ersetzen.
- Antwortet BOOTSTRAP auf eine zuvor von der iFay initiierte `FAYING_REQUEST`, muss `faying_request_ref` auf die `msg_id` dieser Anfrage verweisen; MS muss auf der Attestation Chain „IF-initiiert → HP-Bezeugung → wirksam“ zu einer unteilbaren Beweiskette verknüpfen (siehe §5.3.6 und §3.3).
- Ist das `endorsement`-Feld vorhanden, muss MS vor dem Signieren `endorsed_scope ⊆ scope` ∧ `endorsed_grade.autonomy ≤ grade.autonomy` ∧ `0 < endorsed_lifetime_ms ≤ (not_after − not_before)` verifizieren; jeder Fehlschlag → Ablehnung mit `E_ENDORSEMENT_INVALID` (Fehlercode 1013).

#### §5.3.2 PRESENCE (kontinuierliche Kalibrierung)

**Zweck**: Die iFay_Instance pusht periodisch die von Presence Devices erzeugten Präsenzsignale an MS und aktualisiert damit den `PresenceState.last_freshness` des zugehörigen Mandate.

```typescript
interface PresenceClaims {
  mandate_id:    MandateID;
  signal:        PresenceSignal;
  device_health: {
    secure_element: boolean;
    tampered:       boolean;
    last_boot_at:   IsoTime;
  };
}
```

**Harte Bedingungen auf Protokollebene**:

- `signal` muss das zwingende Dreitupel aus §3.2 I-PC-1 (`nonce / produced_at / device_attestation`) tragen und von Presence Device signiert sein; fehlt eines → `E_PROTOCOL`. Das Frischefenster wird durch `presence_req.max_staleness_ms` des zugehörigen Mandate vorgegeben, nicht vom Signal getragen.
- Ein Signal jenseits von `presence_req.max_staleness_ms` → `E_PRESENCE_STALE` und löst eine Verschärfung gemäß §3.2 I-PC-3 aus (Wanderung zu einer strikteren Stufe oder Suspended).
- Dasselbe `(subject, nonce)`, das sich innerhalb eines Fensters von `2 × max_message_lifetime` wiederholt → einheitlich `E_REPLAY`.

#### §5.3.3 GRADE_SWITCH (Stufenwechsel)

**Zweck**: passt die Autorisierungsstufe (Höherstufung / Herabstufung) innerhalb des Lebenszyklus eines Mandate an.

```typescript
interface GradeSwitchClaims {
  mandate_id:    MandateID;
  target_grade:  Grade;
  reason:        "human-initiated" | "presence-loss" | "policy-trigger";
  human_witness?: WebAuthnAssertion;  // zwingend in Höherstufungsrichtung, optional bei Herabstufung
}
```

**Invariante auf Protokollebene (zwingende Bezeugung bei Höherstufung)**: Gilt `target_grade.autonomy > current.autonomy` (d. h. streng höhere Autonomie als die aktuelle Stufe), ist `human_witness` ein **MUSS**; fehlende oder ungültige Signatur → einheitliche Ablehnung mit `E_HUMAN_WITNESS_REQUIRED`. Die Herabstufungsrichtung (`target_grade.autonomy ≤ current.autonomy`) darf vom Protokoll automatisch ausgelöst werden (z. B. `presence-loss` / `policy-trigger`); `human_witness` ist nicht erforderlich.

#### §5.3.4 DELEGATE (geräteübergreifende / Sub-Agent-Ableitung)

**Zweck**: leitet aus einem Eltern-Mandate ein Kind-Mandate ab, verwendet in geräteübergreifenden oder Sub-Agent-Szenarien.

```typescript
interface DelegateClaims {
  parent_mandate: MandateID;
  child_subject:  FayID;            // abgeleitete FayID
  child_scope:    Scope;            // muss ⊆ parent.scope sein
  child_grade:    Grade;            // child_grade.autonomy muss ≤ parent.grade.autonomy sein (niedrigere oder gleiche Autonomie, d. h. strikter oder gleich)
  device_id?:     string;           // bei geräteübergreifender Ableitung an ein bestimmtes Endgerät binden
}
```

**Harte Bedingungen auf Protokollebene**:

- `child_scope ⊆ parent.scope` ∧ `child_grade.autonomy ≤ parent.grade.autonomy`; jede Erweiterung in eine der beiden Richtungen → Ablehnung mit `E_PROTOCOL` (im Einklang mit §3.1 I-MS-4 / Property 6).
- Das `signature_bundle.chain` des Kind-Mandate muss die Gegensignatur des Eltern-Mandate tragen und so einen abgeleiteten Knoten auf der Attestation Chain bilden.
- Trägt das Eltern-Mandate ein `endorsement`, muss das `endorsement` des Kind-Mandate (falls vorhanden) innerhalb des Eltern-Endorsement konvergieren; Nicht-Konvergenz → Ablehnung mit `E_ENDORSEMENT_INVALID`.

#### §5.3.5 REVOKE

**Zweck**: widerruft ein Mandate; widerruft optional kaskadierend alle abgeleiteten Kind-Mandates.

```typescript
interface RevokeClaims {
  mandate_id:   MandateID;
  cascade:      boolean;            // kaskadierender Widerruf aller abgeleiteten Kind-Mandates (Standard true)
  reason:       RevokeReason;
  effective_at: IsoTime;            // Standard = now; geplanter Widerruf erlaubt
}

type RevokeReason =
  | "human-initiated"
  | "expiry"
  | "task-completed"
  | "human-prime-unreachable"
  | "ego-deviation"
  | "fay-credential-invalid"
  | "human-prime-credential-invalid"
  | "regulatory-order"
  | "terminal-disconnected";
```

`RevokeReason` entspricht eins zu eins den neun Auslösebedingungen aus Kapitel 13.

**Harte Bedingungen auf Protokollebene**:

- Die Widerrufserreichbarkeit muss ≥ der Bootstrap-Erreichbarkeit sein (im Einklang mit Property 4 / R4.1); es existiert kein Pfad, über den die iFay selbst legitim einen REVOKE initiieren könnte.
- Bei `cascade = true` müssen alle abgeleiteten Kind-Mandates innerhalb von `RevocationVisibilityBudget` als `revoked` sichtbar werden (im Einklang mit Property 14).
- Der Widerruf ist irreversibel: `Revoked` ist ein absorbierender Zustand; die Wiederherstellung der Autorisierung muss erneut über BOOTSTRAP mit einer neuen `mandate_id` ungleich der alten `mandate_id` erfolgen (im Einklang mit Property 10).

#### §5.3.6 FAYING_REQUEST / FAYING_REQUEST_RESP (IF-initiiertes bidirektionales Faying)

**Zweck**: Die iFay strebt beim Human Prime proaktiv Faying an (Anfrage zur Etablierung oder Anpassung der Mandatsbeziehung). Diese Nachricht **erzeugt nicht direkt ein Mandate**; MS agiert nur als Weiterleiter und pusht die Anfrage an den HP-Sichtkanal; danach schließt der HP die Bestätigung und Wirksamkeit über BOOTSTRAP ab (siehe §2.4 Phase A0).

```typescript
interface FayingRequestClaims {
  initiator:        FayID;          // die iFay selbst
  target_human:     HumanPrimeID;   // Ziel-HP
  proposed_scope:   Scope;          // vorgeschlagener Mandatsumfang
  proposed_grade:   Grade;          // vorgeschlagene Stufe
  reason:           string;         // Freitext-Ergänzung
  reason_code:
    | "establish"
    | "adjust-scope"
    | "adjust-grade"
    | "renew"
    | "endorsement-request";
  expected_lifetime_ms?: number;    // erwartete Mandate-Lebensdauer
  proposed_endorsement?: Endorsement; // falls zugleich ein Endorsed Mandate angestrebt wird
}

interface FayingRequestRespClaims {
  request_msg_id: string;           // referenziert die vorgelagerte FAYING_REQUEST.msg_id
  status:         "accepted" | "rejected" | "timeout";
  bootstrap_ref?: string;           // bei status=accepted verweist dies auf die vom HP abgeschlossene BOOTSTRAP.msg_id
  reject_reason?: string;
}
```

**Harte Bedingungen auf Protokollebene**:

- Eine IF-initiierte FAYING_REQUEST erzeugt **keine** direkte Faying-Zustandsänderung; erst wenn der HP innerhalb von `BootstrapTimeout` über BOOTSTRAP antwortet (unter Mitführung von `faying_request_ref` und einer überprüfbaren `human_witness`), wird die Anfrage wirksam.
- Erteilt der HP innerhalb von `BootstrapTimeout` keine ausdrückliche Bestätigung, muss MS `FAYING_REQUEST_RESP { status="timeout" }` zurückgeben und das Ereignis in die Attestation Chain schreiben, entsprechend dem Fehlercode `E_FAYING_REQUEST_NOT_CONFIRMED` (1014).
- Es existiert kein legitimer Pfad für MS / IF / Supervisory Agent, um HP beim Abschluss der Bestätigung zu ersetzen; fehlende `human_witness` → `E_HUMAN_WITNESS_REQUIRED` (1010).
- Die FAYING_REQUEST-Frequenz für jedes Paar `(HP, IF)` ist durch `ConfirmationRateLimit` beschränkt (siehe Anhang B); ein Überschreiten wird gemäß §9.10.7 T6 behandelt.

#### §5.3.7 DISCLOSURE (strukturierte Offenlegungsnachricht)

**Zweck**: eine strukturierte Offenlegungsnachricht, die die iFay beim Berichten oder Anfordern einer Bestätigung verwendet. Regulierungsbehörden und MS dürfen diese Nachricht auf Schema-Ebene auditieren; das Verschleiern von Schlüsselinformationen mittels reinen Freitexts ist verboten (siehe §9.10.4 T3).

```typescript
interface DisclosureClaims {
  mandate_id:         MandateID;
  /** mandatory_fields (fehlt eines → als Protokollfehler behandelt) */
  action:             AtomicAction;          // eine Offenlegung entspricht genau einer Atomic_Action
  scope_used:         Scope;                 // die tatsächlich genutzte Teilmenge des scope
  risk_level:         "low" | "normal" | "high" | "critical";
  reversibility:      "reversible" | "partially-reversible" | "irreversible";
  affected_resources: string[];
  uncertainty_flags:  string[];              // z. B. ["ambiguous-target", "stale-context"]
  /** optionale Ergänzungen */
  free_text?:         string;
  intent?:            "report" | "request-confirmation";
  endorsement_id?:    string;                // falls es während Disconnected auftrat, verweist dies auf das zugehörige endorsement
}
```

**`mandatory_fields`-Durchsetzungsliste** (im Einklang mit R13.3 / §9.10.4):

`action` / `scope_used` / `risk_level` / `reversibility` / `affected_resources` / `uncertainty_flags`.

**Harte Bedingungen auf Protokollebene**:

- Jedes fehlende oder nicht parsbare `mandatory_fields` → MS muss mit `E_PROTOCOL` (1099) ablehnen und an den HP-Sichtkanal pushen;
- Hochsensible Aktionen (`risk_level ∈ {high, critical}`) müssen **vor** der D-Dimension-Ausführung zuerst eine DISCLOSURE aussenden und auf die ausdrückliche Bestätigung des HP warten (es sei denn, die aktuelle Stufe ist bereits G4 Autonomous und die Aktion fällt in den Haupt-scope; siehe §7);
- Stellt ein nachfolgendes Audit fest, dass die `mandatory_fields` der DISCLOSURE mit der tatsächlichen Aktion inkonsistent sind, muss MS das Mandate mit `RevokeReason="ego-deviation"` widerrufen;
- DISCLOSURE für während Disconnected ausgeführte Aktionen muss `endorsement_id` tragen, damit die Aktion unabhängig auf ein bestimmtes endorsement zurückverfolgt werden kann.

### §5.4 Fehlercodes

Fehlerantworten verwenden einheitlich die `ERROR`-Nachricht (Envelope `msg_type = "ERROR"`); der `claims`-Körper hat die Form `{ code, message, mandate_id?, recovery_hint? }`. Die nachstehende Tabelle gibt alle Fehlercodes sowie ihre Audit- und HP-Sichtkanal-Push-Bedingungen wieder (im Einklang mit §EH.3).

| Code | Name | Bedeutung | Antwort | Muss ins Audit | Muss in HP-Sicht |
| ---: | --- | --- | --- | :---: | :---: |
| 1001 | `E_NO_MANDATE` | Anfrage trägt kein Mandate | Ablehnen | ✗ | ✗ |
| 1002 | `E_MANDATE_EXPIRED` | Mandate abgelaufen | Ablehnen + Revoke auslösen | ✓ | ✗ |
| 1003 | `E_SCOPE_VIOLATION` | Aufruf überschreitet den scope | Ablehnen + verdächtig protokollieren | ✓ | ✗ |
| 1004 | `E_GRADE_INSUFFICIENT` | Aktuelle Stufe reicht für die sensible Aktion nicht aus | Ablehnen + Höherstufung vorschlagen | ✓ | ✗ |
| 1005 | `E_PRESENCE_STALE` | Präsenzsignal abgelaufen | Ablehnen + Herabstufung auslösen | ✓ | ✗ |
| 1006 | `E_REVOKED` | Mandate widerrufen | Ablehnen | ✓ | ✓ |
| 1007 | `E_ATTESTATION_INVALID` | Attestation-Verifikation fehlgeschlagen | Ablehnen + Revoke auslösen | ✓ | ✓ |
| 1008 | `E_RR_UNAVAILABLE` | Revocation Registry unerreichbar | Ablehnen per Default-Deny | ✓ | ✗ |
| 1009 | `E_REPLAY` | nonce wiederholt | Ablehnen + Sicherheitsalarm | ✓ | ✓ |
| 1010 | `E_HUMAN_WITNESS_REQUIRED` | Stufen-Höherstufung / bidirektionalem Faying fehlt die menschliche Bezeugung | Ablehnen | ✓ | ✗ |
| 1011 | `E_ROGUE_DETECTED` | Rogue-Verhalten erkannt | Ablehnen + Revoke erzwingen | ✓ | ✓ |
| 1012 | `E_BUDGET_EXCEEDED` | ResourceBudget überschritten | Ablehnen + Herabstufung auslösen | ✓ | ✗ |
| 1013 | `E_ENDORSEMENT_INVALID` | endorsement-Feld ungültig (inkl. `endorsed_scope ⊄ scope` / `endorsed_grade.autonomy > grade.autonomy` / `endorsed_lifetime` fehlt oder zu lang / manipuliert) | Ablehnen + Revoke dieses Mandate auslösen | ✓ | ✓ |
| 1014 | `E_FAYING_REQUEST_NOT_CONFIRMED` | IF-initiierte FAYING_REQUEST innerhalb von `BootstrapTimeout` nicht ausdrücklich vom HP bestätigt | Ablehnen + in die Attestation Chain schreiben | ✓ | ✗ |
| 1099 | `E_PROTOCOL` | Fehler auf Protokollebene (Version / Format / Signatur / DISCLOSURE-`mandatory_fields` fehlend oder nicht parsbar) | Ablehnen | ✓ | ✗* |

> **`*`-Hinweis**: Standardmäßig gelangt `E_PROTOCOL` nur ins Audit; wird es jedoch über den Pfad „§5.3.7 DISCLOSURE-`mandatory_fields` fehlend oder nicht parsbar“ ausgelöst, muss MS zusätzlich an den HP-Sichtkanal pushen (siehe §5.3.7 und §9.10.4 T3).
>
> **Semantische Hinweise zu Audit / HP-Sicht**:
>
> - **Muss ins Audit**: Fehler müssen als Fünftupel `(error_code, mandate_id, ts, RP_id, reason)` in die Attestation Chain / das Audit-Log geschrieben werden; außer `E_NO_MANDATE` (kein Mandate-Kontext) sind alle Fehlercodes ✓.
> - **Muss in HP-Sicht**: Fehler müssen an den HP-Sichtkanal gepusht werden; die RP darf sie nicht stillschweigend verschlucken. Die Basis-Vier (`E_REVOKED` / `E_ATTESTATION_INVALID` / `E_REPLAY` / `E_ROGUE_DETECTED`) sind durch §EH.3 vorgeschrieben; `E_ENDORSEMENT_INVALID` wird, weil seine Auslösekette unweigerlich `E_REVOKED` begleitet, ebenfalls an den HP-Sichtkanal gepusht.
> - Fehlerantworten ist es **verboten**, internen MS-Zustand, Mandate-Private-Key-Fingerabdrücke, andere Human-Prime-Identifikatoren oder sonstige sensible Informationen mitzuführen (siehe §EH.3).

---
