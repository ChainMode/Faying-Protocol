---
title: "Faying Protocol/1.0 — 부록 B 기본 파라미터 예산"
version: Faying Protocol/1.0
status: Final
part: 부록 B
language: ko
---

> 프로토콜 본문 내비게이션: [장 목차](./README.md) ｜ 이전 장 [부록 A 용어 정렬 퀵 레퍼런스](./부록A-용어정렬퀵레퍼런스.md) ｜ 다음 장 [부록 C 변경 이력](./부록C-변경이력.md)

## 부록 B 기본 파라미터 예산

> 이 부록은 Faying Protocol 1.0의 기본 파라미터 예산과 상한을 제시한다. 구체적 수치는 구현이 조정할 수 있으나, 어떤 파라미터든 구현 취값이 "상한" 열을 초과해서는 안 되며, grade에 따라 단조롭게 조이는 하드 제약(P17.3 LivenessDetectionBudget / P8 재현 신선도 참조)은 반드시 유지되어야 한다.

### B.1 전역 예산

| 파라미터 | 기본값 | 상한 | grade별 조임 규칙 | 출처 |
| --- | --- | --- | --- | --- |
| `MaxMandateLifetime` | 24h | 30d | 고민감 시나리오는 더 짧아야 함(구현 사용자 정의) | §1.3 G2 / §4.1 / P7 |
| `BootstrapTimeout` | 60s | 5min | — | §5.3.1 / §5.3.6 / §8.2 |
| `RevocationVisibilityBudget` | 1s | 5s | grade에 따라 조임(높은 autonomy → 더 짧은 예산) | §3.4 I-RR-1 / §9.6 / P5 |
| `StaleBudget`(RR 도달 불가 거부 임곗값) | 5s | 30s | — | §3.4 / §EH.1 / §EH.4 |
| `HumanReachabilityBudget` | 30min | 24h | — | §EH 파생 / 청사진 제11장 |
| `MaxDegradedDuration` | 5min(grade별) | 30min | grade에 따라 조임(높은 autonomy → 더 짧은 체류) | §4.3 / §8.2 / P11 |

### B.2 Presence max-staleness(grade별)

| Grade | 기본값 | 상한 | 비고 |
| --- | --- | --- | --- |
| G1 Strict | 5s | 10s | 고민감 동작의 기본 grade |
| G2 Moderate | 60s | 5min | — |
| G3 Loose | 5min | 30min | — |
| G4 Autonomous | 30min | 2h | G4 하트비트 손실은 곧장 → Suspended(§7.3) |

> **출처**: §7.1 / P8 재현 신선도.

### B.3 LivenessDetectionBudget(실연 탐지 창 상한)

> Presence max-staleness와 동일 단계로 조임. P17.3 강제약: `max_staleness_ms ≤ LivenessDetectionBudget(grade)` ∧ grade에 따라 단조롭게 조임(더 엄격한 grade → 더 짧은 탐지 창).

| Grade | 기본값 | 상한 | 비고 |
| --- | --- | --- | --- |
| G1 Strict | 5s | 10s | G1 max-staleness와 동일 단계로 조임 |
| G2 Moderate | 60s | 5min | — |
| G3 Loose | 5min | 30min | — |
| G4 Autonomous | 30min | 2h | G4 하트비트 손실은 곧장 → Suspended(§7.3) |

> **출처**: §9.9 / P17.3 / Requirement 12.3.

### B.4 AttentionDriftThreshold(HP 시야 유휴 임곗값)

> HP 시야 통로가 연속으로 이 임곗값을 넘도록 활동이 없으면 "주의력 상실"로 간주하며, 그 기간에는 고민감 동작 발기가 금지된다(§9.10.5 T4, P18.4 참조).

| Grade | 기본값 | 상한 | 비고 |
| --- | --- | --- | --- |
| G1 Strict | 30s | 2min | 고민감 동작은 반드시 ≤ G1 자율성에 떨어져야 함 |
| G2 Moderate | 5min | 15min | — |
| G3 Loose | 15min | 1h | — |
| G4 Autonomous | 1h | 4h | — |

> **출처**: §9.10.5 / P18.4 / Requirement 13.4.

### B.5 ConfirmationRateLimit(확인 속도 상한)

> 초과 시 자동 강등 / 일시 정지. critical 버킷 이벤트의 관통은 조용히 폐기될 수 없음. FAYING_REQUEST 빈도는 동일 예산에 편입(Open Questions Q12와 일치).

| 파라미터 | 기본값 | 상한 | 비고 |
| --- | --- | --- | --- |
| `ConfirmationRateLimit`(각 HP × IF 쌍) | 10회 / min | 60회 / min | FAYING_REQUEST, GRADE_SWITCH-up, DISCLOSURE 고민감 사전 확인 등 HP의 명시적 확인이 필요한 모든 이벤트 포함 |

> **출처**: §9.10.7 / P18.6 / Requirement 13.6.

### B.6 Endorsed_Lifetime 소프트 상한

> P16.3(Endorsement_Convergence) / P16.4(Endorsed_Lifetime_Hard_Stop)과 짝을 이룸. `Mandate.not_after − Mandate.not_before`를 초과할 수 없으며, 만료되는 즉시 Mandate Revoked를 트리거한다 — IF가 여전히 물리적 단절 상태여도 마찬가지다(소프트 타임아웃 강제약).

| 파라미터 | 기본값 | 소프트 상한 | 비고 |
| --- | --- | --- | --- |
| `Endorsed_Lifetime` 소프트 상한 | 4h | 12h | Open Questions Q11 결의 전에는 권장값으로 둠. grade에 따라 추가로 조이는 하드 상한은 RFC 결의에 남김 |

> **출처**: §7.5 / P16.3 / P16.4 / Requirement 11.3 / Open Questions Q11.

### B.7 수치 일관성 하드 제약

- **B.2와 B.3 동일 단계로 조임**: `max_staleness_ms ≤ LivenessDetectionBudget(grade)`. BOOTSTRAP / GRADE_SWITCH 범위 초과 요청은 일률적으로 `E_PROTOCOL`로 거부(P17.3).
- **B.5 ConfirmationRateLimit 초과**: §9.10.7에 따라 자동 강등 / 일시 정지. `critical` 버킷 이벤트는 조용히 폐기될 수 없으며 반드시 HP 시야 통로로 관통해야 함(P18.6).
- **B.6 Endorsed_Lifetime 만료 강제약**: 만료되는 즉시 Mandate 상태 기계가 Revoked로 전이하도록 트리거 — IF가 여전히 Disconnected에 있어도 마찬가지(P16.4).
- **grade별 단조 조임의 통일 규칙**: grade에 따라 조이는 모든 예산(B.2 / B.3 / B.4)은 BOOTSTRAP / GRADE_SWITCH / DELEGATE 범위 초과 요청 시 일률적으로 `E_PROTOCOL`로 거부.
- **부록 A와 부록 B 일관성**: 부록 A.5에 나열된 예산 명칭은 반드시 이 부록의 모든 소절에서 정의한 파라미터 명칭과 엄격히 일치해야 한다. 어느 명칭이든 변경 시 두 곳을 동기 갱신해야 한다.
