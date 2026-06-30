---
title: "Faying Protocol/1.0 — 부록 A 용어 정렬 퀵 레퍼런스"
version: Faying Protocol/1.0
status: Final
part: 부록 A
language: ko
---

> 프로토콜 본문 내비게이션: [장 목차](./README.md) ｜ 이전 장 [§11 미해결 과제](./11-미해결과제.md) ｜ 다음 장 [부록 B 기본 파라미터 예산](./부록B-기본파라미터예산.md)

## 부록 A 용어 정렬 퀵 레퍼런스

> 이 부록은 본 규격의 요구사항 베이스라인 Glossary, 설계 근거 부록 A 셋과 일치를 유지한다. EARS 조항에 등장하는 시스템 명칭은 반드시 여기서 정의된 후에야 사용할 수 있다. 이 부록은 "역할과 엔티티 / 프로토콜 구성요소 / 프로토콜 데이터 객체 / 등급과 정책 / 기본 예산" 다섯 분류로 조직하여 교차 참조에 편하게 한다.

### A.1 역할과 엔티티

| 프로토콜 용어(영문) | 청사진 / 한국어 용어 | 관계 / 설명 |
| --- | --- | --- |
| Human Prime(HP) | 인간 원형 | 동의어. Faying 관계의 유일한 최종 책임 인수 주체이자 폐기권 보유자이며, Faying 상태 변화에 명확한 승인 확인을 내놓을 수 있는 유일한 엔티티이기도 하다 |
| iFay Instance(IF) | iFay 인스턴스 | 동의어. 감호받는 대리 엔티티로 FayID로 고유 식별된다. 자신의 Mandate를 폐기할 권한이 없으며, 모든 상태 변화는 HP의 명확한 승인 확인을 전제로 한다 |
| Supervisory Agent(SA) | 감독 Agent | Prime 외에 프로토콜 계층이 식별할 수 있는 또 다른 종류의 감독 주체. 폐기권을 갖지 않으며 HP를 대신해 Faying 승인 확인을 완료할 수 없다 |
| Relying Party(RP) | 피호출 측 | iFay가 호출하는 단말, 애플리케이션 또는 서비스 |
| Presence Device(PD) | 재현 디바이스 | WebAuthn / FIDO2 자격증명과 생체 인식 능력을 담는 하드웨어로, 재현 신호의 물리적 원천이다 |

### A.2 프로토콜 구성요소

| 프로토콜 용어(영문) | 약어 | 설명 |
| --- | --- | --- |
| Mandate Service | MS | HP를 대표하여 Mandate를 발급 / 갱신 / 강등 / 폐기하는 논리 서비스(§3.1 참조) |
| Presence Channel | PC | PD에서 MS까지의 저지연·재전송 방지 재현 스트림(§3.2 참조) |
| Attestation Chain | AC | HP → MS → IF → 파생 IF의 모든 발급 행위가 형성하는 역추적 가능한 서명 체인(§3.3 참조) |
| Revocation Registry | RR | 실시간 폐기 상태 서비스(§3.4 참조) |
| Liveness Channel | LC | 실연 탐지(실제 실연과 감지된 실연 포함) 스트림(§3.5, §9.9 참조) |
| Behavior Baseline Service | BBS | (HP, IF) 행위 베이스라인을 유지하는 통계 서비스(§3.6 참조) |

### A.3 프로토콜 데이터 객체

| 프로토콜 용어(영문) | 청사진 / 한국어 용어 | 설명 |
| --- | --- | --- |
| Mandate | 인가령 | 프로토콜 계층의 새 개념. `(issuer, subject, scope, grade, presence_req, not_before, not_after, attestation, signature, endorsement?)` 등 필드를 담는다(§4.1 / §4.2 참조) |
| Endorsed_Mandate | 배서식 인가 | Mandate 하위 유형. `endorsement = (enabled, endorsed_scope ⊆ scope, endorsed_grade.autonomy ≤ grade.autonomy, endorsed_lifetime, offline_revocation_policy)`를 명시 선언하여, IF가 물리적 실연 기간에도 한정된 범위 안에서 자치할 수 있게 한다. 책임 인수 주체는 항상 HP다(§7.5, P16.x 참조) |
| PresenceSignal | 재현 신호 | PD가 생성하며 MS가 검증할 수 있는 물리적 재현 단언 |
| Attestation | 증언 | 통일된 검증 가능 단언 운반체(WebAuthn / TPM-quote / Platform-keystore / Self-signed) |
| FayID | FayID | iFay가 iFay 프레임워크에서 갖는 통일된 고유 신원 식별자(ULID-like) |
| Faying_State | 피제어 상태 | Mandate가 Active / Degraded / Disconnected에 있을 때 IF가 처하는 행위 상태 |
| Rogue_Fay | 이탈 상태 | Mandate가 Unpaired / Revoked에 있거나 존재하지 않을 때 IF가 처하는 행위 상태. Faying_State와 이태(二態) 상호 배타(P15). **비고**: `Suspended`는 Rogue_Fay에 귀속되지 않는다 — 그것은 "Faying State 일시 정지"이며(감호 관계는 여전히 있고, Mandate 메타데이터는 보존되며, 새 한 차례 BOOTSTRAP 없이 HP가 명시적으로 복구할 수 있음), 행위 결과 면에서만 Rogue와 마찬가지로 D 차원을 금지한다. §4.3 / §8.2 매핑 표 참조 |
| Faying_Initiation | 양방향 Faying 발기 | Faying 관계(수립 또는 조정)의 발기는 HP가 능동적으로(HP-initiated) 할 수도, IF가 능동적으로 HP에게 구할(IF-initiated / FAYING_REQUEST) 수도 있다. 최종 발효 조건은 모두 HP가 검증 가능한 명확한 승인 확인을 내놓는 것이다(§5.3.6, P16.6 참조) |
| Behavior_Baseline | 행위 베이스라인 | BBS가 유지하는 (HP, IF)의 누적 행위 프로파일로, 돌발 이탈 탐지에 사용된다(§3.6, P18.5 참조) |
| Atomic_Action | 원자 동작 | IF가 대외 실행하는 최소 분리 불가 선언 단위. 한 차례 호출은 정확히 1개의 Atomic_Action에 대응하며 묶음은 금지된다(P18.2 참조) |
| Disclosure_Report | 공개 메시지 | IF가 보고 또는 확인 요청 시 사용하는 구조화 메시지. `mandatory_fields`는 강제로 파싱 가능해야 한다(§5.3.7, P18.3 참조) |
| Ego | 자아 경계 | 동의어. `ego-deviation` 트리거 판정에 사용된다(§3.6, §9.10.4 참조) |
| Human View | 인류 시야 | 가치관. Faying Protocol은 그것의 프로토콜 수준 구현이다(청사진 제11장) |

### A.4 등급과 정책

| 프로토콜 용어(영문) | 설명 |
| --- | --- |
| Authorization_Grade(Grade) | 인가 등급, 값은 `G0..G4`(§7 참조) |
| G0 Emergency_Override | 긴급 탈환 단계. HP가 일방적으로 제어를 강제 회수한다(§7.1, P12 참조) |
| G1 Strict | 가장 엄격한 단계. 고민감 동작의 기본 grade |
| G2 Moderate | 중간 단계 |
| G3 Loose | 느슨한 단계 |
| G4 Autonomous | 가장 자율적인 단계. G4 하트비트 손실은 곧장 → Suspended(§7.3 참조) |
| PresenceRequirement | 재현 요구. grade에 결속되는 `(signal_types, max_staleness_ms, on_loss)` 삼중쌍 |
| Scope | 인가 범위. `(domains, actions, terminals?, budget?)`로 명시 선언하는 최소 권한 집합 |

### A.5 기본 예산(상세 수치는 부록 B 참조)

| 프로토콜 용어(영문) | 약술 |
| --- | --- |
| MaxMandateLifetime | 단일 Mandate 최대 수명(기본 24h, 상한 30d) |
| BootstrapTimeout | BOOTSTRAP / FAYING_REQUEST 등이 HP 입회를 기다리는 타임아웃(기본 60s) |
| RevocationVisibilityBudget | 폐기가 RR 전역에서 가시화되는 예산(기본 1s) |
| StaleBudget | RR 도달 불가 거부 임곗값(기본 5s) |
| HumanReachabilityBudget | HP 실연이 자동 Revoke를 트리거하는 임곗값(기본 30min) |
| LivenessDetectionBudget | 실연 탐지 창 상한. grade에 따라 단조롭게 조임(부록 B, P17.3 참조) |
| AttentionDriftThreshold | HP 시야 유휴가 "주의력 상실"을 트리거하는 임곗값. grade에 따라 조임(부록 B, P18.4 참조) |
| ConfirmationRateLimit | 단위 시간에 HP로 푸시하는 확인 요청 수량 상한. 초과 시 자동 강등 / 일시 정지(부록 B, P18.6 참조) |
| MaxDegradedDuration | Degraded 상태 최대 지속 시간(기본 5min/grade) |
