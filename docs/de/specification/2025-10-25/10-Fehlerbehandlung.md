---
title: "Faying Protocol/1.0 — §10 Fehlerbehandlung"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: de
part: "Kapitel 10 von 11 (Protokolltext)"
---

> Protokolltext-Navigation: [Inhaltsverzeichnis](./README.md) | vorheriges [§9 Sicherheitsbetrachtungen](./09-Sicherheitsbetrachtungen.md) | nächstes [§11 Offene Fragen](./11-Offene-Fragen.md)

## §10 Fehlerbehandlung

Dieses Kapitel konsolidiert alle Fehlercodes aus §5.4 mit konkreten Fehlerszenarien, Protokollantworten, Zustandsübergängen, Wiederherstellungspfaden und Beobachtbarkeitsbedingungen. Alle Fehler werden als `ERROR`-Nachrichten unter dem Envelope aus §5.2 zurückgegeben, mit einem `claims`-Körper der Form `{ code, message, mandate_id?, recovery_hint? }`; die vier Abschnitte dieses Kapitels bilden über §5.4 hinaus die „alleinige Protokollebene-Autorität zur Fehlerbehandlung“.

### EH.1 Fehlerszenarien und Protokollantworten

Die nachstehende Tabelle gibt eine Panoramasicht aller in §5.4 aufgeführten Fehlercodes (1001–1014 und 1099); jede Zeile enthält: Auslöseszenario, Protokollantwort, ob Revoke ausgelöst wird, ob eine Herabstufung ausgelöst wird, ob ein Eintrag in die Audit-Kette zwingend ist und ob ein Push an den HP-Sichtkanal zwingend ist. Diese Tabelle entspricht eins zu eins der Fehlercode-Tabelle aus §5.4.

| Code | Name | Auslöseszenario | Protokollantwort | Löst Revoke aus | Löst Herabstufung aus | Ins Audit | In HP-Sicht |
| ---: | --- | --- | --- | :---: | :---: | :---: | :---: |
| 1001 | `E_NO_MANDATE` | Geschäftsanfrage trägt keinen Faying-Protocol-Header / kein Mandate | RP lehnt sofort ab; kein Audit etabliert | ✗ | ✗ | ✗ | ✗ |
| 1002 | `E_MANDATE_EXPIRED` | `now > Mandate.not_after` | RP lehnt ab + MS löst Revoke dieses Mandate aus | ✓ | ✗ | ✓ | ✗ |
| 1003 | `E_SCOPE_VIOLATION` | Aufrufaktion ∉ `Mandate.scope.actions` | RP lehnt ab + protokolliert verdächtiges Ereignis; kumulierter Verdacht löst Herabstufung aus | ✗ | ✓ (kumulativ) | ✓ | ✗ |
| 1004 | `E_GRADE_INSUFFICIENT` | RP erfordert eine Stufe strikter als das aktuelle `Mandate.grade` | RP lehnt ab + schlägt Höherstufung vor (Höherstufungspfad erfordert HP-`human_witness`) | ✗ | ✗ | ✓ | ✗ |
| 1005 | `E_PRESENCE_STALE` | `presence.last_freshness` überschreitet `max_staleness_ms` oder `LivenessDetectionBudget` | RP lehnt ab; IF stoppt die D-Dimension proaktiv, wartet auf PRESENCE-Kalibrierung; Zustandsmaschine Active → Degraded | ✗ | ✓ | ✓ | ✗ |
| 1006 | `E_REVOKED` | RR markiert als widerrufen | RP lehnt ab; lehnt Aufrufe derselben Kette kaskadierend ab; IF fällt sofort zur Rogue Fay zurück | ✓ (bereits widerrufen) | ✗ | ✓ | ✓ |
| 1007 | `E_ATTESTATION_INVALID` | Signaturverifikation eines Attestation-Chain-Knotens schlägt fehl / Zeitstempel nicht im Gültigkeitsfenster des Elternknotens / endorsement-Teilfeld manipuliert | RP lehnt ab + MS löst Revoke dieses Mandate aus | ✓ | ✗ | ✓ | ✓ |
| 1008 | `E_RR_UNAVAILABLE` | RR-Abfrage-Timeout ≥ `StaleBudget` | RP lehnt per Default-Deny ab; IF pausiert die gesamte D-Dimension; Zustandsmaschine Active → Degraded | ✗ | ✓ | ✓ | ✗ |
| 1009 | `E_REPLAY` | Innerhalb von `2 × max_message_lifetime` wurde die nonce für dasselbe subject bereits gesehen | RP lehnt ab + Sicherheitsalarm; IF rotiert sofort die Sitzungsschlüssel | ✗ | ✗ | ✓ | ✓ |
| 1010 | `E_HUMAN_WITNESS_REQUIRED` | grade-up / FAYING_REQUEST oder andere HP-bezeugungspflichtige Szenarien fehlen oder `human_witness`-Verifikation schlägt fehl | RP / MS lehnt ab; HP-Bezeugung abwarten, dann erneut initiieren | ✗ | ✗ | ✓ | ✗ |
| 1011 | `E_ROGUE_DETECTED` | D-Dimension-Verstoß erkannt (`ego-deviation` / Verhaltens-Baseline über Schwellenwert usw.) | RP lehnt ab + Revoke erzwingen; IF fällt sofort zur Rogue Fay zurück | ✓ | ✗ | ✓ | ✓ |
| 1012 | `E_BUDGET_EXCEEDED` | Aufrufe überschreiten kumulativ `Scope.budget` / `ResourceBudget` | RP lehnt ab + Herabstufung oder (im Extremfall) Revoke auslösen | ✓ (Extremfall) | ✓ | ✓ | ✗ |
| 1013 | `E_ENDORSEMENT_INVALID` | `endorsed_scope ⊄ scope` / `endorsed_grade.autonomy > grade.autonomy` / `endorsed_lifetime` fehlt oder zu lang / endorsement-Teilfeld manipuliert / DELEGATE-Kind-endorsement konvergiert nicht innerhalb des Eltern | MS lehnt Ausstellung ab + löst Revoke dieses Mandate aus; IF stoppt sofort alle bezeugten Aktionen | ✓ | ✗ | ✓ | ✓ |
| 1014 | `E_FAYING_REQUEST_NOT_CONFIRMED` | Eine IF-initiierte FAYING_REQUEST innerhalb von `BootstrapTimeout` nicht ausdrücklich vom HP bestätigt | MS gibt `FAYING_REQUEST_RESP { status="timeout" }` zurück; erzeugt keine Faying-Zustandsänderung; Ereignis in die Attestation Chain geschrieben | ✗ | ✗ | ✓ | ✗ |
| 1099 | `E_PROTOCOL` | Version / Format / fehlendes Feld / nicht parsbar / DISCLOSURE-`mandatory_fields` fehlend oder nicht parsbar / illegale Signatureingabe / `msg_type` nicht ausdrücklich in §5.3 gelistet | RP / MS lehnt ab; pusht zusätzlich an die HP-Sicht, wenn über den DISCLOSURE-Pfad ausgelöst | ✗ | ✗ | ✓ | ✗* (DISCLOSURE-Pfad ✓) |

> **`*`-Hinweis**: Standardmäßig gelangt `E_PROTOCOL` nur in die Audit-Kette; wird es über den Pfad „§5.3.7 DISCLOSURE-`mandatory_fields` fehlend oder nicht parsbar“ ausgelöst, muss MS zusätzlich an den HP-Sichtkanal pushen (im Einklang mit dem Hinweis in §5.4).

**Trace**: `R2.1.1`–`R2.1.4` (Default-Deny), `R3.2.1`–`R3.2.3` (Fehlerereignisse in Audit und HP-Sicht), `R4.2.1`–`R4.2.3` (Budget und Erreichbarkeit der Widerrufssichtbarkeit), `R11.1.4` (endorsement-Manipulation löst `E_ATTESTATION_INVALID` + Revoke aus), `R11.2.1`–`R11.2.3` (endorsement-Konvergenzverletzung löst `E_ENDORSEMENT_INVALID` aus), `R1.3.3` (FAYING_REQUEST-Timeout ohne Bestätigung löst `E_FAYING_REQUEST_NOT_CONFIRMED` aus), `R13.3.1` (DISCLOSURE-`mandatory_fields` fehlend oder nicht parsbar löst `E_PROTOCOL` aus).

### EH.2 Wiederherstellungspfade

Die Fehlercodes werden danach, „ob eine erneute Etablierung des Faying-Zustands nötig ist“, in drei Wiederherstellungspfad-Klassen gruppiert. Alle Wiederherstellungspfade müssen innerhalb der Default-Deny-Konvergenz aus EH.4 ausgeführt werden; es existiert kein optimistisches Durchwink-Zwischenfenster.

#### EH.2.1 Wiederherstellbare Fehler (kein BOOTSTRAP nötig)

| Code | Name | Wiederherstellungsaktion |
| ---: | --- | --- |
| 1004 | `E_GRADE_INSUFFICIENT` | GRADE_SWITCH-up auslösen (muss HP-`human_witness` tragen; siehe §7.4); eine Wiederherstellung unter Auslassen der Bezeugung ist nicht erlaubt |
| 1005 | `E_PRESENCE_STALE` | PRESENCE-Nachricht erneut senden, um `last_freshness` aufzufrischen; schlägt es weiterhin fehl, gemäß `LivenessDetectionBudget` nach Degraded → Suspended konvergieren |
| 1008 | `E_RR_UNAVAILABLE` | Innerhalb des Default-Deny-Fensters mit Backoff erneut versuchen (nicht länger als `StaleBudget`); überschritten → Degraded betreten, RR-Wiederherstellung abwarten, bevor neu verbunden wird |
| 1012 | `E_BUDGET_EXCEEDED` | GRADE_SWITCH-down auslösen oder die Budget-Fenster-Auffrischung abwarten; eine Wiederherstellung unter „Ignorieren des Budgets“ ist nicht erlaubt |

#### EH.2.2 Wiederherstellung mit erforderlicher HP-Erneut-Bezeugung (BOOTSTRAP muss erneut durchlaufen werden)

| Code | Name | Wiederherstellungsaktion |
| ---: | --- | --- |
| 1002 | `E_MANDATE_EXPIRED` | BOOTSTRAP erneut durchlaufen; die neue `mandate_id` darf nicht gleich der alten `mandate_id` sein (im Einklang mit der Widerruf-Irreversibilität P10) |
| 1006 | `E_REVOKED` | Nicht wiederherstellbar; nur der HP kann einen frischen BOOTSTRAP initiieren; die neue `mandate_id` darf nicht gleich der alten `mandate_id` sein |
| 1007 | `E_ATTESTATION_INVALID` | Wie oben; ein neuer BOOTSTRAP ist erst erlaubt, nachdem der erzwungene Revoke dieses Mandate ausgelöst wurde |
| 1011 | `E_ROGUE_DETECTED` | Wie oben; üblicherweise begleitet von direktem HP-Eingriff und ego-deviation-Audit |
| 1013 | `E_ENDORSEMENT_INVALID` | Wie oben; nachdem der Mandate-Revoke ausgelöst wurde, muss der HP einen frischen BOOTSTRAP initiieren (mit einem legitimen `endorsement`-Feld) |

#### EH.2.3 Stellt keine Faying-Zustandsänderung dar (keine Wiederherstellung nötig)

| Code | Name | Handhabung |
| ---: | --- | --- |
| 1001 | `E_NO_MANDATE` | Der Aufrufer muss zuerst ein Mandate erlangen und dann den Aufruf initiieren; es existiert auf der Protokollebene kein „Ohne-Mandate-Temporär-Durchwink“-Pfad |
| 1003 | `E_SCOPE_VIOLATION` | Der Aufrufer muss die Aktion so anpassen, dass sie in `Mandate.scope.actions` fällt; kumulierter Verdacht löst Herabstufung aus |
| 1009 | `E_REPLAY` | Der Aufrufer sollte mit einer neuen nonce erneut initiieren; bei Angriffsverhalten wurden Sicherheitsalarm und HP-Sicht geschrieben |
| 1010 | `E_HUMAN_WITNESS_REQUIRED` | Nach Erlangung der HP-Bezeugung erneut initiieren; eine Ersetzung durch IF / MS / SA ist nicht erlaubt |
| 1014 | `E_FAYING_REQUEST_NOT_CONFIRMED` | Die iFay darf FAYING_REQUEST innerhalb legitimer Rate-Limits erneut initiieren, darf dadurch aber keine Bestätigungsflut erzeugen (siehe §9.10.7, Anhang B `ConfirmationRateLimit`) |
| 1099 | `E_PROTOCOL` | Der Aufrufer muss die Nachrichtenstruktur korrigieren und dann erneut initiieren |

> **Gemeinsame harte Bedingung**: Wiederherstellungspfade dürfen die Default-Deny-Konvergenz aus §EH.4 nicht umgehen; jeder „ich bin nicht sicher, aber lasse es erst einmal durch“-Optimistische-Wiederherstellungspfad existiert auf der Protokollebene nicht.

### EH.3 Beobachtbarkeitsbedingungen für Fehlerantworten

Alle ERROR-Nachrichten müssen die folgenden vier harten Bedingungen erfüllen:

1. **Audit-Fünftupel**: Außer bei `E_NO_MANDATE` (kein Mandate-Kontext) muss jeder Fehlercode als Fünftupel `(error_code, mandate_id, ts, RP_id, reason)` in die Attestation Chain / das Audit-Log geschrieben werden; dieses Fünftupel ist mit §3.2 und der Spalte „Ins Audit“ in §EH.1 konsistent.
2. **HP-Sichtkanal muss pushen**: Der Fehlercode-Satz `{E_REVOKED (1006), E_ATTESTATION_INVALID (1007), E_REPLAY (1009), E_ROGUE_DETECTED (1011), E_ENDORSEMENT_INVALID (1013)}` muss an den HP-Sichtkanal gepusht werden; ein über den DISCLOSURE-Pfad ausgelöstes `E_PROTOCOL (1099)` muss ebenso gepusht werden. Die RP darf sie nicht stillschweigend verschlucken.
3. **Kein Durchsickern sensibler Informationen**: Fehlerantworten ist es **verboten**, internen MS-Zustand, Mandate-Private-Key-Fingerabdrücke, andere HP-Identifikatoren, interne IF-Zustandsmaschinen-Variablen oder sonstige sensible Informationen mitzuführen; die Felder `message` und `recovery_hint` müssen öffentliche Semantik auf Protokollebene sein, ohne durchsickernde Implementierungsdetails.
4. **Audit-Kette unabhängig überprüfbar**: In die Attestation Chain geschriebene Fehlerereignisse müssen die von §3.3 I-AC-1 / I-AC-2 geforderten Signaturknoten tragen, damit ein Dritter die Kettenverifikation vom Blatt zur Wurzel abschließen kann, ohne den Private Key des MS zu halten (siehe §6.3).

**Trace**: `R3.2.1` (Fehlercode-Fünftupel ins Audit-Log geschrieben), `R3.2.2` (Fehlerantworten dürfen keine sensiblen Informationen mitführen), `R3.2.3` (festgelegte Fehlercodes müssen in die HP-Sicht gelangen), `R3.1.4` (rückverfolgbare Felder der Audit-Kette).

### EH.4 Einheitliche Default-Deny-Konvergenz

> **Jeder Fehler, der sich nicht eindeutig klassifizieren lässt, jedes nicht parsbare Feld und jeder Aufruf während einer RR-Unerreichbarkeit wird von der Protokollebene einheitlich mit `E_PROTOCOL` oder `E_RR_UNAVAILABLE` abgelehnt; es existiert kein legitimer „ich bin nicht sicher, aber lasse es erst einmal durch“-Pfad und kein optimistischer Wiederherstellungspfad „nach dem nachgiebigeren Zustand verarbeiten“ (einschließlich Fenster B, wo tatsächlich online, aber als getrennt wahrgenommen; siehe §9.9).**

**Vier äquivalente Ausdrücke der Konvergenzregel**:

1. **Zustandsmaschinen-Ebene**: Jeder Übergang, der nicht ausdrücklich in der Mandate-Zustandsmaschine aus §4.3 / der Lebenszyklus-Zustandsmaschine aus §8.1 gelistet ist, wird einheitlich abgelehnt.
2. **Nachrichten-Ebene**: Jeder `msg_type`, der nicht ausdrücklich im Nachrichteninventar aus §5.3 gelistet ist, oder jedes fehlende / typfehlerhafte Envelope-Feld wird einheitlich mit `E_PROTOCOL` abgelehnt.
3. **Fehlercode-Ebene**: Jede Fehlerursache, die nicht ausdrücklich in §5.4 / §EH.1 gelistet ist, wird einheitlich in eine `E_PROTOCOL`-Ablehnung klassifiziert.
4. **Entscheidungs-Ebene**: Die Protokollebene zieht ausschließlich Perceived-Disconnected als Entscheidungsgrundlage heran; die optimistischen Durchwink-Pfade in Fenster A (tatsächlich getrennt, aber als verbunden wahrgenommen) / Fenster B (tatsächlich verbunden, aber als getrennt wahrgenommen) existieren auf der Protokollebene nicht (siehe §9.9 Prinzip der pessimistischen Annahme, P17.1 / P17.2).

**Trace**: `R2.1.1`–`R2.1.4` (Default-Deny), `R12.1.1`–`R12.1.3` (Doppelsemantik-Perceived-only-Entscheidung), `R12.2.1`–`R12.2.3` (pessimistische Annahme / Ablehnung während wahrgenommener Trennung).

---
