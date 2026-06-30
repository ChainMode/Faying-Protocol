---
title: "Faying Protocol/1.0 — 부록 C 변경 이력"
version: Faying Protocol/1.0
status: Final
part: 부록 C
language: ko
---

> 프로토콜 본문 내비게이션: [장 목차](./README.md) ｜ 이전 장 [부록 B 기본 파라미터 예산](./부록B-기본파라미터예산.md)

# 부록 C 변경 이력

이 이력은 Faying Protocol/1.0 초안이 집필 착수부터 확정에 이르기까지, 규격 본문과 부속 산출물에 어떤 변화가 있었는지 기록한다. 형식은 [Keep a Changelog](https://keepachangelog.com)의 분류 관습(Added / Changed / Deprecated / Removed / Security)을 따르며, 앞부분에서 버전 번호를 어떻게 정하는지 먼저 설명한다.

> 출처에 대한 정직한 안내: 본 프로토콜의 1.0 초안은 spec 주도 흐름으로 한 번에 산출되었다(요구사항 → 설계 → 작업 목록 → 구현). 아직 여러 차례의 독립적인 프로토콜 위원회 회의를 거치지 않았다. 따라서 이 이력은 항목별 회의 결의와 정확한 날짜를 꾸며내지 않고, "무엇을 했는지, 왜 했는지, 어느 작업에 대응하는지"만 사실대로 기록한다. 아래 인용된 작업 번호(예: 1.6, 3.8, 5.6)는 구현 작업 계획의 실제 항목에 대응하며, 이를 근거로 각 변경의 산출 위치를 되짚을 수 있다. 이후 정식 위원회 평가 절차에 들어가면, 날짜와 결의 번호가 붙은 항목을 여기에 추가한다.

## 버전 번호를 어떻게 정하는가

프로토콜 버전 번호 매김의 **권위 규칙은 본문 §1.7 버전 관리와 호환성을 참조한다**(세 개의 직교 축: 프로토콜 버전 `MAJOR.MINOR` / 문서 상태 / 편집 판차. 협상과 호환성 규칙. 버전 번호 낙점과 실행자 주의사항). 이 부록은 이를 중복 정의하지 않고, 변경 이력과 관련된 두 가지만 보충한다:

- 이 이력은 §1.7.2의 MAJOR / MINOR 판단 기준에 따라 각 변경을 분류한다: 상호운용을 깨는 것은 MAJOR에, 하위 호환 증보는 MINOR에, 순수 텍스트 정오는 §1.7.4에 따라 `Editorial`로 귀속시키며 프로토콜 번호는 건드리지 않는다.
- 현재는 `Faying Protocol/1.0`, 첫 번째 베이스라인이며 상태는 Final(2025-10-25 공개)이다.

명명에서, 산문과 버전 번호는 통일적으로 `Faying Protocol/1.0`을 쓰고, 초기의 `FAP` 약어는 이미 폐기되었다. 다만 schema 파일명 `fap-1.0.cddl` / `fap-1.0.proto`는 옛 접두사를 유지했는데, 순전히 파일명 안정성과 기존 참조를 깨지 않기 위함이다 — 이는 의도된 것이지 명명 번복이 아니다(§1.7.5 "schema 파일명은 편집 판차를 따라 개명하지 않음"과 일치).

## [Faying Protocol/1.0] — Final(2025-10-25)

이것은 1.0의 첫 번째 정식 발표 버전으로, 2025-10-25에 초안 작업 영역에서 정식 발표 디렉터리로 전체가 일괄 이전되어 확정되었다. 아래는 변경 유형별로 분류하며, 각 항목에 그것을 산출한 작업 번호를 표기한다.

### Added

본문(§1–§11 + 부록 A/B):

- §1 Overview: 프로토콜 명명, 위치, 여덟 가지 설계 목표 G1–G8, 목표와 Requirement 일대일 대응. §1.5.1이 "양방향 Faying은 모두 HP의 명시적 승인이 있어야 발효된다"는 이 핵심 단언을 확립한다.(작업 1.2)
- §2 Architecture: 네 장의 Mermaid 그림(프로토콜 스택, 엔티티 관계, 등급 계층, Bootstrap+Heartbeat+Action 시퀀스, IF 능동 발기의 Phase A0 경로 포함)과 여섯 가지 설계 원칙.(작업 1.3)
- §3 Components and Interfaces: 여섯 구성요소(MS / PC / AC / RR / LC / BBS)의 인터페이스와 불변식.(작업 1.4)
- §4 Data Models: CDDL 권위 정의, TypeScript 사람이 읽는 뷰, Disconnected 상태와 재연결 대사를 포함한 Mandate 상태 기계, endorsement 하위 구조.(작업 1.5)
- §5 Protocol Messages: 일곱 종 메시지(BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE / REVOKE / FAYING_REQUEST / DISCLOSURE), 통일 인벨로프, 14항 오류 코드 — 그중 1010 `E_HUMAN_WITNESS_REQUIRED`, 1013 `E_ENDORSEMENT_INVALID`, 1014 `E_FAYING_REQUEST_NOT_CONFIRMED`를 신규 추가.(작업 1.6)
- §6 Cryptography: 알고리즘 스위트 협상(PQC 협상 비트 포함), 키 파생, 서명 형식. endorsement 필드를 서명 입력에 편입.(작업 1.7)
- §7 Authorization Grades: G0–G4 다섯 단계 의미론, 트리거 매트릭스, 강등 단조성, 그리고 G1–G4 위에 중첩되는 §7.5 Endorsement Grades 하위 등급.(작업 1.8)
- §8 Lifecycle: 일곱 상태 생명주기(Disconnected 포함), 책임 귀속 시퀀스, §8.4 재연결 대사 트랜잭션.(작업 1.9)
- §9 Security Considerations: STRIDE, 재전송 공격 방지 / 하이재킹 방지 / 피싱 방지, 이탈 상태 식별, 실연 처리 매트릭스, 그리고 §9.10의 AI 시대 적대적 위협 목록 T1–T7.(작업 1.10)
- §10 Error Handling, §11 Open Questions, 부록 A/B: 오류 시나리오와 복구 경로, 미해결 과제 Q1–Q14, 용어표, 기본 파라미터 예산.(작업 1.11)
- 영문 규격 전문 번역.(작업 1.12)

부속 산출물:

- schema: `schemas/fap-1.0.cddl`(권위), `schemas/types.ts`(TypeScript 사람이 읽는 뷰, Not Normative), `schemas/fap-1.0.proto`(대안 gRPC 바인딩, Not Normative).(작업 2.1–2.3)
- 테스트 벡터 `vectors/`: BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE / REVOKE, 오류 코드, 인코딩 등가, Endorsement, FAYING_REQUEST, DISCLOSURE, Disconnection 총 11종 커버.(작업 3.1–3.11)
- 속성 테스트 `pbt/`: P1–P15 주 속성, 거기에 P16(Endorsed_Mandate), P17(Disconnection), P18(AI-Era) 세 족을 더해 커버.(작업 4.1–4.34)
- 상호운용 컴플라이언스 스위트 `conformance/`: 인코딩 × 서명 알고리즘 × 해시 × 채널 × 구현 언어 5차원 매트릭스, TypeScript와 Rust 두 벌의 reference 구현 첨부.(작업 5.1–5.6)
- 보안 공격 모의 `conformance/attacks/`: 재전송, 하이재킹, 피싱, 이탈 상태 식별, 그리고 T1/T3/T4/T5/T6 모의.(작업 6.1–6.10)

### Changed

- 프로토콜 명명을 초기 초안의 "Faying Auth Protocol(FAP)"에서 **Faying Protocol**로 변경, 버전 번호는 `Faying Protocol/1.0`으로 표기.(§11 Q10에 대응, 결정 완료)
- Faying 발기를 단방향(HP만 발기 가능)에서 양방향(HP 발기 + IF 발기)으로 확장하되, 발효 조건은 "HP 명확한 승인"이라는 한 가지로 통일 수렴.(작업 1.6, 3.9)
- 실연을 "실제 실연"과 "감지된 실연" 두 의미론으로 쪼개고, 프로토콜 결정은 감지된 실연만 보며, 불일치 창에 대해 비관적 추정을 한다.(작업 1.10, 3.11)
- 서명 입력을 `H(Deterministic-CBOR(Envelope_without_signature))`로 통일하여, CBOR 주 형식과 JSON 폴백이 이 기준 아래에서 등가로 상호운용된다.(작업 3.7, 5.2)

### Deprecated

- `FAP` / `FAP/1.0` / `Faying Auth Protocol` 등 옛 명명, 그리고 `application/fap+json`, `POST /fap/v1/...` 등 옛 엔드포인트 형태는 일률적으로 폐기된다. 새 표기는 `application/faying-protocol+json`과 `POST /faying-protocol/v1/{verb}`를 쓴다. schema 파일명은 옛 접두사를 유지하는 유일한 예외다(위 "버전 번호를 어떻게 정하는가" 참조).

### Removed

- 없음. 1.0은 첫 번째 베이스라인이므로 제거해야 할 기존 필드나 메시지가 없다.

### Security

- AI 시대 적대적 위협의 프로토콜 수준 제약 신규 추가: T1 사회공학, T2 블랙박스 조작, T3 핵심 회피, T4 주의력 표류, T5 고정관념 신뢰 배양, T6 감사 홍수, T7 확장 슬롯. 각 항목은 Property P18.1–P18.7과 Requirement 13.1–13.7에 대응.(작업 1.10, 4.28–4.34, 6.6–6.10)
- 배서식 인가의 변조 방지 제약: endorsement이 서명 입력에 들어가, 어느 하위 필드든 바꾸면 Mandate 검증이 실패한다(`E_ATTESTATION_INVALID` / `E_ENDORSEMENT_INVALID`).(작업 1.5, 3.8, 4.17–4.21)
- 대칭적 폐기와 폐기 불가역: 폐기 경로의 도달성은 수립 경로보다 낮지 않고, `Revoked`는 흡수 상태이며, 연쇄 폐기는 기본 활성화다.(작업 3.5, 4.5, 4.11, 4.15)

## 앞으로 어떻게 유지보수하는가

- 정식 평가에 들어가면, 각 위원회 결의를 여기에 한 줄씩 추가하고, 날짜·영향 장·트리거된 작업 번호를 명기하며, 위의 대응하는 Keep a Changelog 분류에 사람이 읽는 항목을 한 줄 보충한다.
- 버전 번호: §1.7에 따라 실행한다 — 하위 호환 증보는 MINOR로, 파괴적 변경은 MAJOR로 가며 MINOR를 0으로 되돌리고, 순수 텍스트 정오는 편집 판차(§1.7.4)로 가며 프로토콜 번호는 건드리지 않는다.
- 이후 정오와 판차 이전은 §1.7.4 / §1.7.5에 따라 처리하며, 이 이력은 본문과 함께 이전되고 판차에 맞춰 갱신된다.
- 한국어·영문 동종 변경은 같은 주기에 동기화하며, 모호하면 간체 중국어판(zh-CN)을 정본으로 한다.
