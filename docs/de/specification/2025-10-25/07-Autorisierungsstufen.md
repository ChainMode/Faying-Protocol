---
title: "Faying Protocol/1.0 — §7 Autorisierungsstufen"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: de
part: "Kapitel 7 von 11 (Protokolltext)"
---

> Protokolltext-Navigation: [Inhaltsverzeichnis](./README.md) | vorheriges [§6 Kryptografie](./06-Kryptografie.md) | nächstes [§8 Lebenszyklus](./08-Lebenszyklus.md)

## §7 Autorisierungsstufen

Dieses Kapitel beschreibt die gestufte Autorisierungssemantik des Faying Protocol. Das Faying Protocol akzeptiert keine „Allmacht-Einheitsdelegation“ — jedes Mandate muss ausdrücklich eine Stufe deklarieren, und die drei Spalten jeder Stufe `(autonomy, presence requirement, message requirement)` tragen auf der Protokollebene präzise Semantik; ereignisausgelöste Stufenwechsel sind erschöpfend und fest unter der Matrix aus §7.2 kodiert; §7.3 verriegelt das Monotonie-Prinzip „Präsenzverlust → muss verschärfen“; §7.4 beschreibt die zwingenden Unterschiede auf Nachrichtenebene; §7.5 führt die Endorsement-Grades-Unterstufen ein, die als Offline-Autonomie-Berechtigungsschicht über G1–G4 gelegt werden.

> **Orthogonale Beziehung zwischen G0 und G1–G4**: G0 Emergency Override liegt **nicht** innerhalb des kontinuierlichen Stufenspektrums G1 ↔ G4; es ist ein **orthogonaler Override-Kanal**. G1–G4 drücken „die kontinuierliche Achse der Autonomiestärke“ aus; G0 ist der Notfallkanal, über den der Human Prime einseitig die Kontrolle zurückgewinnt, und manifestiert sich nur auf den Ebenen der Ereigniswarteschlangen-Priorität und des Endzustands (Suspended); es nimmt an der „Höherstufungs-/Herabstufungs“-Semantik nicht teil. Jede Implementierung, die G0 als „eine kontinuierliche Stufe strikter als G1“ behandelt, ist mit der Protokollsemantik inkonsistent.

> **Referenz der numerischen Budgets**: Die `max-staleness`-Werte in diesem Kapitel (G1=5 s / G2=60 s / G3=5 min / G4=30 min) entsprechen eins zu eins dem Eintrag `Presence max-staleness (G1..G4)` in Anhang B „Standard-Parameterbudgets“; die Spalte „Default“ in Anhang B ist der in diesem Kapitel verwendete Referenzwert, und die Spalte „Obergrenze“ ist die harte Obergrenze auf Protokollebene, innerhalb derer Implementierungen anpassen dürfen.

### §7.1 Präzise Stufendefinitionen

| Stufe | Autonomie | Präsenzanforderung | Nachrichtenanforderung | Geeignet für |
| --- | --- | --- | --- | --- |
| **G0 Emergency Override** | N/A | N/A | Vom HP einseitig initiiert; einzige Wirkung: das Ziel-Mandate sofort nach Suspended drängen | Notfallübernahme |
| **G1 Strict** | Sehr niedrig | Echtzeit-kontinuierliche Präsenz (Gesicht / WebAuthn UV, max-staleness ≤ 5 s) | Jeder externe Aufruf muss ein PresenceSignal ≤ 5 s tragen | Irreversible Operationen (Überweisungen, Signieren, Datenbank-Drop, Hochprivileg-Endgerätebefehle) |
| **G2 Moderate** | Mittel | Aufgaben-Präsenz (frische Präsenz vor sensiblen Teilaufgaben erforderlich, max-staleness ≤ 60 s) | PresenceSignal vor sensiblen Aktionen | Mittelfrequente Agenten-Operationen (Buchungen, Umplanungen, Formularübermittlungen) |
| **G3 Loose** | Hoch | Rückfrage bei Schlüsselschritten (intent-ticket vor Schlüssel-Entscheidungspunkten) | Einmaliges intent-ticket bei Schlüsselschritten mitgeführt | Langfristiger risikoarmer Agent (E-Mail-Triage, Kalender) |
| **G4 Autonomous** | Sehr hoch | Periodischer Heartbeat (presence-heartbeat, max-staleness ≤ 30 min) | Heartbeat-Aufrechterhaltung + periodische Audit-Rückmeldung | Routine-Autonomie innerhalb des scope |

> **Designentscheidung**: G0 liegt nicht innerhalb des kontinuierlichen Spektrums G1 ↔ G4; es ist ein **orthogonaler Override-Kanal** — sein alleiniger Zweck ist es, dem HP zu erlauben, unter jedem Zustand sofort die Kontrolle zurückzugewinnen.

**Konvention der Autonomieachse**: `G0 < G1 < G2 < G3 < G4` (größere Werte = höhere Autonomie). Alle „Höherstufungs-/Herabstufungs“-Entscheidungen im weiteren Verlauf dieses Kapitels beruhen auf Größenvergleichen zwischen `target.autonomy` und `current.autonomy`; G0 nimmt an diesem Achsenvergleich nicht teil — es wandert über die letzte Zeile der Matrix aus §7.2 einseitig nach Suspended.

**Präsenzanforderung auf Presence_Signal-Typen abgestimmt** (siehe Signaltypen-Tabelle in §3.2):

- **G1 Strict**: typische Signale `face-continuous` oder `webauthn-uv-fresh`, `max_staleness_ms = 5_000`;
- **G2 Moderate**: typisches Signal `fingerprint-tap` (vor sensiblen Teilaufgaben), `max_staleness_ms = 60_000`;
- **G3 Loose**: typisches Signal `intent-ticket` (Einmalverbrauch bei Schlüsselschritten); keine periodische max-staleness-Obergrenze, doch jeder Schlüsselschritt muss ein frisches intent-ticket haben;
- **G4 Autonomous**: typisches Signal `presence-heartbeat-only`, `max_staleness_ms = 1_800_000` (30 min).

**Unterschiede der Nachrichtenanforderung (mit dem Nachrichteninventar aus §5 querverwiesen)**:

- **GRADE_SWITCH in Höherstufungsrichtung bei G1 / G2**: `human_witness` ist zwingend (MUSS), Standard-Bezeugungsform ist eine WebAuthn-UV-Assertion (siehe §6.1 Algorithmen-Suiten);
- **G3 / G4**: Höherstufungen auf diese Stufen (die selbst dann zum „Autonomie-lockernden“ Pfad gehören, wenn target.autonomy unter der Ausgangsstufe liegt) erfordern ebenfalls `human_witness`; nur auf dem „aktiven Herabstufungs“-Pfad degradiert `human_witness` zu MAY;
- **G0**: darf nur einseitig vom HP initiiert werden (von IF / MS / SA ersetztes G0 wird mit `E_PROTOCOL` abgelehnt); erfordert eine überprüfbare `human_witness`; G0-Nachrichten müssen mit höchster Priorität in die Attestation Chain und die Revocation-Registry-Push-Warteschlange geschrieben werden.

### §7.2 Matrix der Auslösebedingungen

Die nachstehende Tabelle ist die 6×4-Zustandsübergangsmatrix für 6 Auslöse-Ereignisklassen × 4 aktuelle Nicht-G0-Stufen; dies ist die zwingende Ereignis-→-Endzustand-Zuordnung auf Protokollebene; es existiert kein Übergangspfad außerhalb dieser Tabelle.

| Ereignis | Aktuell G1 | Aktuell G2 | Aktuell G3 | Aktuell G4 |
| --- | --- | --- | --- | --- |
| Präsenzfrische abgelaufen | → Suspended | → G3 Loose | → Suspended | → Suspended |
| HP-aktive Höherstufung | — | → G1 (Bezeugung erforderlich) | → G2 / G1 (Bezeugung erforderlich) | → G3 / G2 / G1 (Bezeugung erforderlich) |
| HP-aktive Herabstufung | → G2 | → G3 | → G4 | — |
| Ego-Abweichung erkannt | → Revoked | → Revoked | → Revoked | → Revoked |
| Revocation Registry unerreichbar | Aufruf ablehnen | Aufruf ablehnen | Aufruf ablehnen | Aufruf ablehnen |
| G0 Override | → Suspended | → Suspended | → Suspended | → Suspended |

**Semantische Ergänzungen zur Matrix**:

- **Asymmetrie der Zeile „Präsenzfrische abgelaufen“**: G2 → G3 ist die erlaubte „milde Herabstufung“ (weiterhin auf dem Active-Zustandsmaschinen-Zweig); G1 / G3 / G4 → Suspended drücken drei unterschiedliche Entscheidungslogiken aus — G1, weil unter Hochsensitivitäts-Szenarien „keine frische Präsenz → keine Aktion erlaubt“ gilt; G3, weil unter intent-ticket-Szenarien der Heartbeat nicht die primäre Präsenzgrundlage ist und ein anhaltendes Ausbleiben frischer Signale bei Schlüsselschritten als nicht vertrauenswürdig behandelt wird; G4, weil der Heartbeat seine alleinige Präsenzgrundlage ist und ein Heartbeat-Verlust direkt in Suspended absorbiert wird (im Einklang mit der Ausnahmeklausel aus §7.3).
- **Zeile „HP-aktive Höherstufung“**: Das „—“ bei G1 bedeutet, dass G1 bereits die strikteste Stufe ohne höheren Höherstufungsspielraum ist; die übrigen erlauben einmalige Höherstufungen über 1–3 Stufen, alle erfordern `human_witness` (siehe §7.4).
- **Zeile „HP-aktive Herabstufung“**: Das „—“ bei G4 bedeutet, dass G4 bereits die nachgiebigste Stufe ohne nachgiebigeren Herabstufungsspielraum ist; die Herabstufungsrichtung erfordert keine `human_witness`, doch RR-Benachrichtigungen und AC-Kettenaufzeichnungen bleiben zwingend.
- **Zeile „Ego-Abweichung erkannt“**: Alle vier Stufen treten einheitlich in den Endzustand Revoked ein (Revoked ist ein absorbierender Zustand; siehe §8 / Property 10); die diese Zeile auslösende Entscheidungslogik wird gemeinsam von §3.6 Behavior Baseline Service und §9.10.6 T5 vorgegeben.
- **Zeile „Revocation Registry unerreichbar“**: Alle vier Stufen „lehnen den Aufruf ab“; dies ist kein Zustandsübergang — es ist der Default-Deny-Konvergenzpfad für einen einzelnen Aufruf (Fehlercode `E_RR_UNAVAILABLE`); das Mandate selbst verbleibt auf der aktuellen Stufe; diese Zeile ist mit der RR-Invariante I-RR-2 aus §3.4 konsistent.
- **Zeile „G0 Override“**: einseitig vom HP initiiert; alle vier Stufen werden einheitlich in Suspended absorbiert; mit höchster Priorität auf der Ereigniswarteschlange verarbeitet (jedes ausstehende Ereignis weicht).

### §7.3 Herabstufungs-Monotonie-Prinzip

> **Ohne Präsenz strikter** — dies ist die kontraintuitive, aber zwingende Form der Graceful-Degradation: Präsenzsignalverlust bedeutet „die menschliche Sicht verengt sich“, daher muss sich die Autonomie **verschärfen**, nicht lockern. In numerischen Begriffen: Präsenzverlust → Stufenwert sinkt (strikter).

Formaler Ausdruck (auf P11 abgestimmt):

```
∀ M ∈ ActiveMandates. PresenceState(M).stale = true ⟹
    next_state(M) ∈ { Degraded(g'), Suspended }
    where g'.autonomy < M.grade.autonomy
```

Das heißt: Nach Präsenzverlust muss der nächste Zustandsübergang zu einer Stufe mit `strikt niedrigerer Autonomie` (kleinere Zahl, höhere Sicherheit) wandern oder direkt nach Suspended wandern; **das Verbleiben auf der ursprünglichen Stufe ist verboten, das Umschalten zu höherer Autonomie ist verboten**.

**Ausnahmen (Bedingungen absorbierender Zustände)**:

- **G4 Autonomous Heartbeat-Verlust → direkt Suspended**: Da G4 bereits die Stufe höchster Autonomie ohne verfügbare striktere Stufe ist, ist die direkte Absorption in Suspended eine harte Bedingung auf Protokollebene (im Einklang mit der G4-Spalte der ersten Zeile der Matrix aus §7.2).
- **Zustand `Degraded` jenseits von `MaxDegradedDuration` → direkt Suspended**: vermeidet, dass „langfristiges Verweilen in einer Unterstufe“ zu einem impliziten „Lockerungspfad“ wird; der konkrete Schwellenwert steht in Anhang B `MaxDegradedDuration`.

### §7.4 Unterschiede der Stufenwechsel-Nachrichtenanforderungen

Die nachstehende Tabelle gibt für die drei Wechselrichtungen die Unterschiede der zwingenden Felder auf Nachrichtenebene wieder; fehlt ein „MUSS“-Eintrag, wird die zugehörige Wechselnachricht einheitlich mit `E_PROTOCOL` oder `E_HUMAN_WITNESS_REQUIRED` abgelehnt (siehe Fehlercode-Tabelle in §5.4).

| Wechselrichtung | human_witness | RR-Benachrichtigung | AC-Kettenaufzeichnung |
| --- | --- | --- | --- |
| Höherstufung (höhere Autonomie) | MUSS | MUSS | MUSS |
| Herabstufung (niedrigere Autonomie) | MAY | MUSS | MUSS |
| Emergency Override | MUSS | MUSS (Push höchster Priorität) | MUSS |

**Semantische Ergänzungen auf Nachrichtenebene**:

- **Höherstufungsrichtung**: Gilt `GRADE_SWITCH.target_grade.autonomy > current_grade.autonomy`, ist `human_witness` zwingend; fehlende oder ungültige Signatur → `E_HUMAN_WITNESS_REQUIRED` (Fehlercode 1010). Die Bedingung dieser Zeile stimmt vollständig mit Requirement 6.1 überein.
- **Herabstufungsrichtung**: `human_witness` degradiert zu MAY, doch RR-Benachrichtigungen und AC-Kettenaufzeichnungen bleiben zwingend — auch Herabstufungen sind eine Klasse von Zustandsänderungen, die Audit und Beobachtbarkeit erfordern; eine „stille Herabstufung“ ist verboten.
- **Emergency Override (G0)**: `human_witness` ist zwingend; RR-Benachrichtigungen müssen mit höchster Priorität gepusht werden (im Einklang mit dem Prioritätsfeld des RR-Push-Kanals aus §3.4); AC-Kettenaufzeichnungen werden mit höchster Priorität geschrieben.
- **Protokollebene-Semantik von „AC-Kettenaufzeichnung zwingend“**: Jeder GRADE_SWITCH (Höherstufung / Herabstufung / G0 gleichermaßen) erzeugt einen AttestationEvent mit `event_type = "grade-switch"` (siehe §3.3), der von MS unmittelbar nach Abschluss des Wechsels angehängt wird; fehlt er → als Audit-Lücke behandelt, was `E_ATTESTATION_INVALID` auslöst.

### §7.5 Endorsement-Grades-Unterstufen

> **Entwurfshaltung**: Endorsement ist keine neue Stufe, sondern **eine „Offline-Autonomie-Berechtigungsschicht“, die über G1–G4 gelegt wird**. Jede Nicht-G0-Stufe (d. h. G1–G4) darf ein `endorsement`-Overlay haben, das dem Mandate erlaubt, während einer physischen Trennung innerhalb eines eingeschränkten Rahmens autonom zu arbeiten (beurteilt gemäß §3.5 Liveness Channel und §4.3 Zustandsmaschine). G0 Emergency Override erlaubt kein endorsement-Overlay — es ist der Kanal, über den der HP einseitig die Kontrolle zurückgewinnt, gegenseitig ausschließend mit der „Offline-Autonomie“-Semantik.

**Overlay-Semantik**:

| Hauptstufe | Endorsement erlaubt | Standardwirkung des Endorsement |
| --- | --- | --- |
| G0 Emergency Override | **Nicht erlaubt** | — |
| G1 Strict | Erlaubt | Während physischer Trennung → Disconnected; endorsed_scope ist typischerweise die minimale Teilmenge hochsensibler Aktionen; endorsed_grade Standard = G1 (kein Abstieg) |
| G2 Moderate | Erlaubt | endorsed_grade Standard = G2; typische Nutzung: geplante Aufgaben / Abschluss bereits begonnener Transaktionen |
| G3 Loose | Erlaubt | endorsed_grade Standard = G3; typische Nutzung: Informations-Triage / Lese-Klasse-Operationen während der Offline-Fortsetzung |
| G4 Autonomous | Erlaubt | endorsed_grade Standard = G4; typische Nutzung: langzeitige Offline-Stellvertretung + Stapelabgleich nach der Wiederverbindung |

**Harte Bedingungen der Unterstufen** (verzahnt mit Requirement 11.2; letztlich durch P16.3 verriegelt):

- **scope-Konvergenz**: `endorsement.endorsed_scope ⊆ Mandate.scope`;
- **grade-Konvergenz**: `endorsement.endorsed_grade.autonomy ≤ Mandate.grade.autonomy` (d. h. endorsed_grade ist in der Autonomie **nicht schwächer** als die Hauptstufe, Sicherheit ≥ Hauptstufe);
- **lifetime endlich**: `endorsement.endorsed_lifetime` muss endlich sein; `∞` oder fehlend ist verboten, und `≤ (Mandate.not_after − Mandate.not_before)`; Anhang B gibt zusätzlich die weiche Obergrenze `Endorsed_Lifetime` (Standard 4 h, Obergrenze 12 h);
- **Offline-Widerrufsrichtlinie aufzählbar**: `endorsement.offline_revocation_policy ∈ {"stop-and-audit", "stop-only", "graceful-stop"}`; Standard `stop-and-audit`.

Schlägt eine harte Bedingung fehl, wird BOOTSTRAP / DELEGATE einheitlich mit `E_ENDORSEMENT_INVALID` (Fehlercode 1013) abgelehnt (siehe §5.4); bei DELEGATE muss zusätzlich `child.endorsement` innerhalb von `parent.endorsement` konvergieren — das heißt, endorsed_scope / endorsed_grade / endorsed_lifetime des Kind-Mandate dürfen die entsprechenden Felder des Eltern-Mandate nicht überschreiten.

**Koordination mit der Trennungs-Zustandsmaschine** (siehe §4.3, §8.4, §9.8):

- Gilt `PresenceState.stale = true` und ist das Mandate ein Endorsed_Mandate → `Active → Disconnected` (der Nicht-Endorsed-Pfad geht direkt → Suspended);
- Während Disconnected darf die iFay D-Dimension-Aktionen nur innerhalb von `endorsement.endorsed_scope` ausführen, beschränkt durch `endorsement.endorsed_grade`;
- Sobald `endorsement.endorsed_lifetime` abläuft, erfolgt sofort ein Soft-Timeout → Disconnected → Revoked, selbst während die iFay physisch getrennt bleibt (Requirement 11.3 Klausel 3 „Soft-Timeout-Hartbedingung“);
- Der Verantwortungsendpunkt ist stets der `issuer` des Mandate (Human Prime), unverändert durch die Existenz eines endorsement (siehe P16.5 Endorsement_Accountability_Invariant und Requirement 11.4).

**Gegenseitiger Ausschluss von Endorsement und G0**: G0 Emergency Override ist der Kanal, über den der HP einseitig die Kontrolle zurückgewinnt; seine Semantik zielt auf den Zustand Suspended („alle D-Dimension-Aktionen sofort einstellen“). Die Semantik des Endorsement zielt auf „die Teilmenge der während physischer Trennung erlaubten D-Dimension-Aktionen“. Die beiden sind gegenseitig ausschließende Ereignisse auf der Zustandsmaschine — sobald G0 ausgelöst wird, wird das Ziel-Mandate sofort in Suspended absorbiert; während Suspended wendet das Mandate die D-Dimension-Durchlassregeln des endorsement nicht mehr an (selbst wenn das endorsement seinen Lifetime-Soft-Timeout-Punkt noch nicht erreicht hat).

---
