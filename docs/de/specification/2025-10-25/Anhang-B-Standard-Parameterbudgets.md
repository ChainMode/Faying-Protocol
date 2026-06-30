---
title: "Faying Protocol/1.0 — Anhang B Standard-Parameterbudgets"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: de
part: "Anhang B (Norm-Referenz)"
---

> Protokolltext-Navigation: [Inhaltsverzeichnis](./README.md) | vorheriges [Anhang A Terminologie-Abgleich](./Anhang-A-Terminologie-Abgleich.md) | nächstes [Anhang C Änderungsprotokoll](./Anhang-C-Aenderungsprotokoll.md)

## Anhang B Standard-Parameterbudgets

> Dieser Anhang gibt die Standard-Parameterbudgets und Obergrenzen von Faying Protocol 1.0; konkrete Werte dürfen von Implementierungen angepasst werden, doch der Implementierungswert jedes Parameters darf die Spalte „Obergrenze“ nicht überschreiten; die harte Bedingung der monotonen Verschärfung nach Stufe (siehe P17.3 LivenessDetectionBudget / P8 Präsenzfrische) muss gewahrt bleiben.

### B.1 Globale Budgets

| Parameter | Default | Obergrenze | Verschärfungsregel nach Stufe | Quelle |
| --- | --- | --- | --- | --- |
| `MaxMandateLifetime` | 24 h | 30 d | Sollte für hochsensible Szenarien kürzer sein (implementierungsdefiniert) | §1.3 G2 / §4.1 / P7 |
| `BootstrapTimeout` | 60 s | 5 min | — | §5.3.1 / §5.3.6 / §8.2 |
| `RevocationVisibilityBudget` | 1 s | 5 s | Nach Stufe verschärft (höhere Autonomie → kürzeres Budget) | §3.4 I-RR-1 / §9.6 / P5 |
| `StaleBudget` (RR-Unerreichbarkeits-Ablehnungsschwelle) | 5 s | 30 s | — | §3.4 / §EH.1 / §EH.4 |
| `HumanReachabilityBudget` | 30 min | 24 h | — | §EH abgeleitet / Blueprint-Kapitel 11 |
| `MaxDegradedDuration` | 5 min (je Stufe) | 30 min | Nach Stufe verschärft (höhere Autonomie → kürzeres Verweilen) | §4.3 / §8.2 / P11 |

### B.2 Presence max-staleness (nach Stufe)

| Stufe | Default | Obergrenze | Hinweis |
| --- | --- | --- | --- |
| G1 Strict | 5 s | 10 s | Standardstufe für hochsensible Aktionen |
| G2 Moderate | 60 s | 5 min | — |
| G3 Loose | 5 min | 30 min | — |
| G4 Autonomous | 30 min | 2 h | G4-Heartbeat-Verlust direkt → Suspended (§7.3) |

> **Quelle**: §7.1 / P8 Präsenzfrische.

### B.3 LivenessDetectionBudget (Obergrenze des Trennungserkennungsfensters)

> Im Gleichschritt mit Presence max-staleness verschärft; P17.3-Hartbedingung: `max_staleness_ms ≤ LivenessDetectionBudget(grade)` ∧ je nach Stufe monoton verschärft (striktere Stufe → kürzeres Erkennungsfenster).

| Stufe | Default | Obergrenze | Hinweis |
| --- | --- | --- | --- |
| G1 Strict | 5 s | 10 s | Im Gleichschritt mit G1 max-staleness verschärft |
| G2 Moderate | 60 s | 5 min | — |
| G3 Loose | 5 min | 30 min | — |
| G4 Autonomous | 30 min | 2 h | G4-Heartbeat-Verlust direkt → Suspended (§7.3) |

> **Quelle**: §9.9 / P17.3 / Requirement 12.3.

### B.4 AttentionDriftThreshold (HP-Sicht-Leerlaufschwelle)

> Anhaltende Inaktivität auf dem HP-Sichtkanal jenseits dieser Schwelle wird als „Aufmerksamkeitsverlust“ behandelt; hochsensible Aktionen sind in diesem Zeitraum verboten (siehe §9.10.5 T4, P18.4).

| Stufe | Default | Obergrenze | Hinweis |
| --- | --- | --- | --- |
| G1 Strict | 30 s | 2 min | Hochsensible Aktionen müssen auf eine Autonomie ≤ G1 fallen |
| G2 Moderate | 5 min | 15 min | — |
| G3 Loose | 15 min | 1 h | — |
| G4 Autonomous | 1 h | 4 h | — |

> **Quelle**: §9.10.5 / P18.4 / Requirement 13.4.

### B.5 ConfirmationRateLimit (Bestätigungsraten-Obergrenze)

> Ein Überschreiten löst eine Auto-Herabstufung / -Suspendierung aus; Ereignisse des critical-Buckets müssen durchdringen und dürfen nicht stillschweigend fallengelassen werden; die FAYING_REQUEST-Frequenz wird in dasselbe Budget einbezogen (im Einklang mit Offene Fragen Q12).

| Parameter | Default | Obergrenze | Hinweis |
| --- | --- | --- | --- |
| `ConfirmationRateLimit` (je Paar HP × IF) | 10 / min | 60 / min | Umfasst FAYING_REQUEST, GRADE_SWITCH-up, DISCLOSURE-Hochsensitivitäts-Vorbestätigung und alle Ereignisse, die eine ausdrückliche HP-Bestätigung erfordern |

> **Quelle**: §9.10.7 / P18.6 / Requirement 13.6.

### B.6 Endorsed_Lifetime weiche Obergrenze

> Gepaart mit P16.3 (Endorsement_Convergence) / P16.4 (Endorsed_Lifetime_Hard_Stop); darf `Mandate.not_after − Mandate.not_before` nicht überschreiten; bei Ablauf wird das Mandate Revoked, selbst wenn die IF physisch noch getrennt ist (Soft-Timeout-Hartbedingung).

| Parameter | Default | Weiche Obergrenze | Hinweis |
| --- | --- | --- | --- |
| `Endorsed_Lifetime` weiche Obergrenze | 4 h | 12 h | Als empfohlener Wert verwendet, bevor Offene Fragen Q11 geklärt ist; die weiter nach Stufe verschärfte harte Obergrenze erwartet eine RFC-Klärung |

> **Quelle**: §7.5 / P16.3 / P16.4 / Requirement 11.3 / Offene Fragen Q11.

### B.7 Harte Bedingungen der numerischen Konsistenz

- **B.2 und B.3 verschärfen sich im Gleichschritt**: `max_staleness_ms ≤ LivenessDetectionBudget(grade)`; Grenzwert-überschreitende BOOTSTRAP- / GRADE_SWITCH-Anfragen werden einheitlich mit `E_PROTOCOL` abgelehnt (P17.3).
- **B.5 ConfirmationRateLimit-Überschreitung**: Auto-Herabstufung / -Suspendierung gemäß §9.10.7; Ereignisse des `critical`-Buckets dürfen nicht stillschweigend fallengelassen werden und müssen zum HP-Sichtkanal durchdringen (P18.6).
- **B.6 Endorsed_Lifetime-Ablauf-Hartbedingung**: Bei Ablauf wandert die Mandate-Zustandsmaschine nach Revoked, selbst wenn die IF noch in Disconnected ist (P16.4).
- **Einheitliche Regel zur Verschärfung nach Stufe**: Alle nach Stufe verschärften Budgets (B.2 / B.3 / B.4) lehnen Grenzwert-überschreitende BOOTSTRAP- / GRADE_SWITCH- / DELEGATE-Anfragen einheitlich mit `E_PROTOCOL` ab.
- **Konsistenz von Anhang A und Anhang B**: Die in Anhang A.5 aufgeführten Budgetnamen müssen strikt mit den in jedem Unterabschnitt dieses Anhangs definierten Parameternamen konsistent sein; jede Namensänderung erfordert synchronisierte Aktualisierungen an beiden Stellen.

---
