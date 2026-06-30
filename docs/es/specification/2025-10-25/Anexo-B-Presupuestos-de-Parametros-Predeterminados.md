---
title: "Faying Protocol/1.0 — Anexo B Presupuestos de parámetros predeterminados"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: es
part: "Anexo B (referencia normativa)"
---

> Navegación del cuerpo del protocolo: [Índice](./README.md) | anterior [Anexo A Alineación de terminología](./Anexo-A-Alineacion-de-Terminologia.md) | siguiente [Anexo C Registro de cambios](./Anexo-C-Registro-de-Cambios.md)

## Anexo B Presupuestos de parámetros predeterminados

> Este anexo ofrece los presupuestos de parámetros predeterminados y los límites superiores de Faying Protocol 1.0; los valores concretos pueden ser ajustados por las implementaciones, pero el valor de implementación de cualquier parámetro no debe superar la columna «Límite superior»; debe mantenerse la restricción dura de ajuste monótono por nivel (véase P17.3 LivenessDetectionBudget / P8 frescura de presencia).

### B.1 Presupuestos globales

| Parámetro | Predeterminado | Límite superior | Regla de ajuste por nivel | Fuente |
| --- | --- | --- | --- | --- |
| `MaxMandateLifetime` | 24h | 30d | Debería ser más corto para escenarios de alta sensibilidad (definido por la implementación) | §1.3 G2 / §4.1 / P7 |
| `BootstrapTimeout` | 60s | 5min | — | §5.3.1 / §5.3.6 / §8.2 |
| `RevocationVisibilityBudget` | 1s | 5s | Ajustado por nivel (mayor autonomía → presupuesto más corto) | §3.4 I-RR-1 / §9.6 / P5 |
| `StaleBudget` (umbral de rechazo por RR inalcanzable) | 5s | 30s | — | §3.4 / §EH.1 / §EH.4 |
| `HumanReachabilityBudget` | 30min | 24h | — | §EH derivado / capítulo 11 del blueprint |
| `MaxDegradedDuration` | 5min (por nivel) | 30min | Ajustado por nivel (mayor autonomía → residencia más corta) | §4.3 / §8.2 / P11 |

### B.2 max-staleness de presencia (por nivel)

| Nivel | Predeterminado | Límite superior | Nota |
| --- | --- | --- | --- |
| G1 Strict | 5s | 10s | Nivel predeterminado para las acciones de alta sensibilidad |
| G2 Moderate | 60s | 5min | — |
| G3 Loose | 5min | 30min | — |
| G4 Autonomous | 30min | 2h | La pérdida de heartbeat de G4 directamente → Suspended (§7.3) |

> **Fuente**: §7.1 / P8 frescura de presencia.

### B.3 LivenessDetectionBudget (límite superior de la ventana de detección de desconexión)

> Ajustado al unísono con el max-staleness de presencia; restricción dura P17.3: `max_staleness_ms ≤ LivenessDetectionBudget(grade)` ∧ ajustado monótonamente por nivel (nivel más estricto → ventana de detección más corta).

| Nivel | Predeterminado | Límite superior | Nota |
| --- | --- | --- | --- |
| G1 Strict | 5s | 10s | Ajustado al unísono con el max-staleness de G1 |
| G2 Moderate | 60s | 5min | — |
| G3 Loose | 5min | 30min | — |
| G4 Autonomous | 30min | 2h | La pérdida de heartbeat de G4 directamente → Suspended (§7.3) |

> **Fuente**: §9.9 / P17.3 / Requirement 12.3.

### B.4 AttentionDriftThreshold (umbral de inactividad de la vista del HP)

> La inactividad continua en el canal de vista del HP que supere este umbral se trata como «pérdida de atención»; las acciones de alta sensibilidad están prohibidas durante este periodo (véase §9.10.5 T4, P18.4).

| Nivel | Predeterminado | Límite superior | Nota |
| --- | --- | --- | --- |
| G1 Strict | 30s | 2min | Las acciones de alta sensibilidad deben recaer en autonomía ≤ G1 |
| G2 Moderate | 5min | 15min | — |
| G3 Loose | 15min | 1h | — |
| G4 Autonomous | 1h | 4h | — |

> **Fuente**: §9.10.5 / P18.4 / Requirement 13.4.

### B.5 ConfirmationRateLimit (límite superior de la tasa de confirmación)

> La superación del límite dispara auto-degradación / suspensión; los eventos del cubo crítico deben penetrar y no descartarse silenciosamente; la frecuencia de FAYING_REQUEST se incorpora al mismo presupuesto (coherente con Cuestiones abiertas Q12).

| Parámetro | Predeterminado | Límite superior | Nota |
| --- | --- | --- | --- |
| `ConfirmationRateLimit` (por par HP × IF) | 10 / min | 60 / min | Incluye FAYING_REQUEST, GRADE_SWITCH-up, predivulgación de alta sensibilidad de DISCLOSURE y todos los eventos que requieren confirmación explícita del HP |

> **Fuente**: §9.10.7 / P18.6 / Requirement 13.6.

### B.6 Límite superior blando de Endorsed_Lifetime

> Emparejado con P16.3 (Endorsement_Convergence) / P16.4 (Endorsed_Lifetime_Hard_Stop); no debe superar `Mandate.not_after − Mandate.not_before`; al caducar el Mandate es Revoked, incluso si el IF sigue físicamente desconectado.

| Parámetro | Predeterminado | Límite superior | Nota |
| --- | --- | --- | --- |
| Límite superior blando de `Endorsed_Lifetime` | 4h | 12h | Usado como valor recomendado antes de la resolución de Cuestiones abiertas Q11; el límite superior duro ajustado además por nivel espera resolución de RFC |

> **Fuente**: §7.5 / P16.3 / P16.4 / Requirement 11.3 / Cuestiones abiertas Q11.

### B.7 Restricciones duras de consistencia numérica

- **B.2 y B.3 se ajustan al unísono**: `max_staleness_ms ≤ LivenessDetectionBudget(grade)`; las solicitudes BOOTSTRAP / GRADE_SWITCH fuera de límites se rechazan uniformemente con `E_PROTOCOL` (P17.3).
- **Superación de ConfirmationRateLimit de B.5**: auto-degradación / suspensión conforme a §9.10.7; los eventos del cubo `critical` no deben descartarse silenciosamente y deben penetrar al canal de vista del HP (P18.6).
- **Restricción dura de caducidad de Endorsed_Lifetime de B.6**: al caducar, la máquina de estados del Mandate migra a Revoked, incluso si el IF sigue en Disconnected (P16.4).
- **Regla unificada de ajuste por nivel**: todos los presupuestos ajustados por nivel (B.2 / B.3 / B.4) rechazan las solicitudes BOOTSTRAP / GRADE_SWITCH / DELEGATE fuera de límites uniformemente con `E_PROTOCOL`.
- **Consistencia entre el Anexo A y el Anexo B**: los nombres de presupuesto enumerados en A.5 deben ser estrictamente coherentes con los nombres de parámetro definidos en cada subsección de este anexo; cualquier cambio de nombre requiere actualizaciones sincronizadas en ambos sitios.
