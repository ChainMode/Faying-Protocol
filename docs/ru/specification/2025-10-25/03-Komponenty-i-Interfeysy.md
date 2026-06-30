---
title: "Faying Protocol/1.0 — §3 Компоненты и интерфейсы"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: ru
part: "Глава 3 из 11 (текст протокола)"
---

> Навигация по тексту протокола: [Оглавление](./README.md) | предыдущая [§2 Архитектура](./02-Arhitektura.md) | следующая [§4 Модели данных](./04-Modeli-Dannyh.md)

## §3 Компоненты и интерфейсы

Эта глава даёт 6 основных компонентов уровня протокола Faying Protocol: **Mandate Service (MS) / Presence Channel (PC) / Attestation Chain (AC) / Revocation Registry (RR) / Liveness Channel (LC) / Behavior Baseline Service (BBS)**. Для каждого компонента глава предоставляет:

- **Обязанности**: положение и граница компонента в протоколе;
- **Каркас интерфейса на TypeScript**: человекочитаемое представление (**Ненормативно**); авторитетные определения находятся в §4 Модели данных и §5 Сообщения протокола;
- **Инварианты**: жёсткие ограничения уровня протокола, которые должны всегда выполняться; каждый инвариант трассируется хотя бы к одному подпункту EARS в §Requirements.

> **Примечание о трассируемости EARS**: за каждым инвариантом этой главы следует строка `Trace:`, перечисляющая соответствующие идентификаторы подпунктов EARS (из базы требований) в форме `R<requirement>.<criterion>.<clause>`.

### §3.0 Предварительные объявления общих типов (Ненормативно)

Чтобы блоки интерфейсов TypeScript этой главы могли независимо пройти `tsc --noEmit`, следующий блок кода предварительно объявляет в минимально-скелетной форме вспомогательные типы, на которые ссылается эта глава; **авторитетные определения** этих типов находятся в §4 Модели данных.

```typescript
// §3.0 — Ненормативные предварительные объявления.
// Авторитетные определения находятся в §4 Модели данных.

export type IsoTime = string;
export type MandateId = string;
export type FayID = string;
export type HumanPrimeID = string;
export type DeviceId = string;

export type AuthorizationGrade = "G0" | "G1" | "G2" | "G3" | "G4";

export interface Scope {
  readonly domains: readonly string[];
  readonly actions: readonly string[];
  readonly terminals?: readonly string[];
  readonly budget?: ResourceBudget;
}

export interface ResourceBudget {
  readonly max_calls_per_minute?: number;
  readonly max_bytes_per_call?: number;
}

export interface Grade {
  readonly value: AuthorizationGrade;
  readonly autonomy: number; // большее значение = выше автономность (G0 наименьшая, G4 наибольшая)
}

export interface PresenceRequirement {
  readonly signal_types: readonly PresenceSignalType[];
  readonly max_staleness_ms: number;
  readonly on_loss: "downgrade" | "suspend";
}

export type PresenceSignalType =
  | "webauthn-uv-fresh"
  | "face-continuous"
  | "fingerprint-tap"
  | "presence-heartbeat-only"
  | "intent-ticket";

export interface SignatureBundle {
  readonly alg: string;
  readonly hash: string;
  readonly sig: Uint8Array;
  readonly chain?: readonly SignatureBundle[];
}

export interface Endorsement {
  readonly enabled: boolean;
  readonly endorsed_scope: Scope;
  readonly endorsed_grade: Grade;
  readonly endorsed_lifetime_ms: number;
  readonly offline_revocation_policy:
    | "stop-and-audit"
    | "stop-only"
    | "graceful-stop";
  readonly start_at?: IsoTime;
}

export interface Mandate {
  readonly mandate_id: MandateId;
  readonly issuer: HumanPrimeID;
  readonly subject: FayID;
  readonly scope: Scope;
  readonly grade: Grade;
  readonly presence_req: PresenceRequirement;
  readonly device_id?: DeviceId;
  readonly not_before: IsoTime;
  readonly not_after: IsoTime;
  readonly parent?: MandateId;
  readonly endorsement?: Endorsement;
  readonly signature_bundle: SignatureBundle;
}

export interface PresenceSignal {
  readonly mandate_id: MandateId;
  readonly signal_type: PresenceSignalType;
  readonly nonce: Uint8Array;
  readonly produced_at: IsoTime;
  readonly device_attestation: Uint8Array;
  readonly challenge?: Uint8Array;
  readonly challenge_response?: Uint8Array;
  readonly signature_bundle: SignatureBundle;
}

export interface PresenceVerdict {
  readonly accepted: boolean;
  readonly verdict: "ok" | "stale" | "replay" | "attestation-invalid";
  readonly recommended_next_grade?: AuthorizationGrade;
}

export interface PresenceAck {
  readonly accepted: boolean;
  readonly mandate_id: MandateId;
  readonly observed_at: IsoTime;
}

export interface PresenceState {
  readonly mandate_id: MandateId;
  readonly last_freshness: IsoTime;
  readonly stale: boolean;
  readonly active_signal_types: readonly PresenceSignalType[];
}

export interface BootstrapRequest {
  readonly subject: FayID;
  readonly scope: Scope;
  readonly grade: Grade;
  readonly presence_req: PresenceRequirement;
  readonly not_before: IsoTime;
  readonly not_after: IsoTime;
  readonly human_witness: Uint8Array; // утверждение WebAuthn
  readonly endorsement?: Endorsement;
  readonly faying_request_ref?: string;
}

export interface GradeSwitchRequest {
  readonly mandate_id: MandateId;
  readonly target_grade: Grade;
  readonly current_grade: Grade;
  readonly human_witness?: Uint8Array;
  readonly reason: string;
}

export interface DelegateRequest {
  readonly parent_mandate_id: MandateId;
  readonly child_subject: FayID;
  readonly child_scope: Scope;
  readonly child_grade: Grade;
  readonly device_id?: DeviceId;
  readonly not_before: IsoTime;
  readonly not_after: IsoTime;
}

export type RevokeReason =
  | "human-initiated"
  | "expiry"
  | "task-completed"
  | "human-prime-unreachable"
  | "ego-deviation"
  | "fay-credential-invalid"
  | "human-prime-credential-invalid"
  | "regulatory-order"
  | "terminal-disconnected";

export interface RevokeRequest {
  readonly mandate_id: MandateId;
  readonly reason: RevokeReason;
  readonly cascade: boolean;
  readonly human_witness?: Uint8Array;
}

export interface RevokeReceipt {
  readonly mandate_id: MandateId;
  readonly reason: RevokeReason;
  readonly revoked_at: IsoTime;
  readonly cascade_targets: readonly MandateId[];
  readonly signature_bundle: SignatureBundle;
}

export interface RevocationStatus {
  readonly mandate_id: MandateId;
  readonly revoked: boolean;
  readonly revoked_at?: IsoTime;
  readonly reason?: RevokeReason;
  readonly observed_at: IsoTime;
}

export interface ScopeFilter {
  readonly subjects?: readonly FayID[];
  readonly issuers?: readonly HumanPrimeID[];
}

export interface Subscription {
  readonly subscription_id: string;
  readonly close: () => void;
}

export interface AtomicAction {
  readonly action: string;
  readonly target?: string;
  readonly sensitivity: "low" | "normal" | "high" | "critical";
}
```

### §3.1 Mandate Service (MS)

**Обязанности**: управляет полным жизненным циклом Mandate от имени Human Prime (выпуск / продление / понижение / отзыв); единственная легитимная точка входа для Faying Action.

**Интерфейс (Ненормативно)**:

```typescript
export interface MandateService {
  /** Единственная легитимная точка входа для Faying Action */
  bootstrap(req: BootstrapRequest): Promise<Mandate>;

  /** Калибровка сигнала присутствия; возвращает, остаётся ли текущий Mandate действительным / должен ли быть понижен */
  verifyPresence(
    mandateId: MandateId,
    signal: PresenceSignal
  ): Promise<PresenceVerdict>;

  /** Переключение уровня: повышения требуют свидетельства HP; понижения могут запускаться протоколом автоматически */
  switchGrade(req: GradeSwitchRequest): Promise<Mandate>;

  /** Межустройственный вывод: выводит дочерний Mandate из родительского, со scope ⊆ родительского scope, grade ≤ родительского grade */
  delegate(req: DelegateRequest): Promise<Mandate>;

  /** Симметричный отзыв: достижимость должна быть ≥ bootstrap */
  revoke(req: RevokeRequest): Promise<RevokeReceipt>;
}
```

**Ключевые инварианты**:

- **I-MS-1 (Bootstrap, заякоренный на HP)**: запрашивающий `bootstrap()` должен нести проверяемую attestation HP (форма по умолчанию: утверждение присутствия пользователя WebAuthn); нет легитимного пути для «MS самостоятельно решает bootstrap» или для IF / SA заменить HP в завершении подтверждения.
  - **Trace**: `R1.3.1` (инициированный HP должен предъявить проверяемое явное подтверждение), `R1.3.5` (не предоставляется пути для IF / MS / SA заменить HP в завершении подтверждения Faying).

- **I-MS-2 (обязательное свидетельство HP при повышениях)**: `switchGrade()` должен нести проверяемый `human_witness` тогда и только тогда, когда `target.autonomy > current.autonomy`; отсутствие или неверная подпись → отклонить с `E_HUMAN_WITNESS_REQUIRED`, и IF не должна инициировать повышения уровня автономно.
  - **Trace**: `R7.1.1` (схождение `child.scope ⊆ parent.scope` — влечёт ограничение нерасширения внутри семантики повышения/понижения уровня, согласованное с принципом монотонности понижения), `R5.1.1` (предусловие принятия на основе `presence_req`, на котором RP проверяет после записи `switchGrade` поля `presence_req`).
  - Примечание: этот инвариант также авторитетно покрыт R6.1 (повышения должны нести свидетельство HP); трассируемость EARS, приведённая в этой главе, берёт лишь релевантные подпункты в множестве Requirements, объявленных данной задачей.

- **I-MS-3 (бюджет видимости отзыва)**: как только `revoke()` публикуется RR, все последующие вызовы RP `query()` должны возвращать `revoked` в течение `RevocationVisibilityBudget` (по умолчанию 1 с, ужесточается по уровню; см. §6 / Приложение B); MS не должен предоставлять путь «оптимистичного пропуска».
  - **Trace**: `R4.2.1` (бюджет видимости отзыва ≤ `RevocationVisibilityBudget`), `R4.2.4` (нет подтверждения в течение `StaleBudget` → Default-Deny).

- **I-MS-4 (строго сходящиеся производные scope / grade)**: дочерний Mandate, выпущенный `delegate()`, должен удовлетворять `child.scope ⊆ parent.scope` ∧ `child.grade.autonomy ≤ parent.grade.autonomy`; любое расширение в любом из направлений отклоняется с `E_PROTOCOL`, а `signature_bundle.chain` дочернего Mandate должна нести контрподпись родительского Mandate.
  - **Trace**: `R7.1.1` (дочерний scope ⊆ родительского scope), `R7.1.2` (дочерняя autonomy ≤ родительской autonomy).

### §3.2 Presence Channel (PC)

**Обязанности**: безопасно, с низкой задержкой и устойчивостью к replay доставляет физические сигналы присутствия, производимые Presence Device, в MS, где MS превращает их в вердикты «непрерывной калибровки» текущего Mandate.

**Типы сигналов (согласованы с уровнями §7)**:

| Тип | Сила | Применимый уровень | Путь понижения при отказе |
| --- | --- | --- | --- |
| `webauthn-uv-fresh` | Сильный | G1 Strict | Отказ → Suspended |
| `face-continuous` | Сильный | G1 Strict | Отказ → понижение к G2 Moderate |
| `fingerprint-tap` | Средний | G2 Moderate | Отказ → понижение к G3 Loose |
| `presence-heartbeat-only` | Слабый | G3 Loose / G4 Autonomous | Отказ → Suspended |
| `intent-ticket` | Одноразовый | Межуровневое дополнение | Одноразовый; не влияет на основной уровень |

**Интерфейс (Ненормативно)**:

```typescript
export interface PresenceChannel {
  /** Инициируется PD; MS проверяет и записывает в PresenceState соответствующего Mandate */
  push(signal: PresenceSignal): Promise<PresenceAck>;

  /** RP перед каждым вызовом запрашивает, свежо ли текущее Presence */
  query(mandateId: MandateId): Promise<PresenceState>;
}
```

**Ключевые инварианты**:

- **I-PC-1 (обязательная тройка на сигнал + окно свежести со стороны Mandate)**: каждый `PresenceSignal` должен явно нести `nonce + produced_at + device_attestation`, подписанный Presence_Device; окно свежести **не переносится сигналом**, а задаётся `presence_req.max_staleness_ms` соответствующего Mandate (привязано к уровню, заякорено HP на момент BOOTSTRAP, ужесточается `LivenessDetectionBudget` по уровню). Сигналы, у которых `produced_at + presence_req.max_staleness_ms < now`, единообразно рассматриваются как устаревшие.
  - **Trace**: `R5.1.3` (поля `nonce / produced_at / device_attestation` обязательны), `R5.1.4` (PC отклоняет просроченные сигналы на фазе проверки).

- **I-PC-2 (одноразовость на nonce)**: одна и та же пара `(subject, nonce)` принимается не более одного раза в пределах окна TTL `2 × max_message_lifetime`; повторное потребление → отклонить с `E_REPLAY`.
  - **Trace**: `R5.1.1` (`last_freshness` должна удовлетворять свежести — влечёт, что семантика анти-replay на основе nonce + временной метки приземляется на уровне PC), `R5.1.3` (поле `nonce` — протокольная рукоять анти-replay).

- **I-PC-3 (свежесть присутствия автоматически ужесточается)**: `PresenceState.last_freshness` должна быть ≥ `now − presence_req.max_staleness_ms`; при провале этого PC должен заставить следующий переход состояния мигрировать в `Degraded(grade')` (`grade'.autonomy < current.autonomy`) или `Suspended`; оставаться на исходном уровне запрещено, переключаться в сторону большей автономности запрещено.
  - **Trace**: `R5.1.1` (предусловие принятия `last_freshness ≥ t − max_staleness_ms`), `R12.2.2` (использовать свежесть, а не период опроса heartbeat, как основание для пропуска вызовов).

### §3.3 Attestation Chain (AC)

**Обязанности**: организует все действия выпуска HP → MS → IF → производная IF в обратно прослеживаемую цепочку подписей, так что любой единичный Mandate может быть восстановлен независимой третьей стороной обратно к его источнику авторизации.

**Структура цепочки (иллюстративно)**:

```
Root: HP-Public-Key (self-hosted / anchored to WebAuthn credentials)
  └─ MS-Cert (HP-signed, binds MS public key with permissions)
       └─ Mandate M1 (MS-signed)
            ├─ Mandate M2 (derived from M1, MS countersign + parent Mandate countersign)
            └─ Mandate M3 (derived from M1)
```

**Интерфейс (Ненормативно)**:

```typescript
export interface AttestationChain {
  /** Проверить полную цепочку от листа до корня */
  verify(mandate: Mandate): Promise<AttestationVerifyResult>;

  /** Дописать единичное событие цепочки (Bootstrap / GradeSwitch / Delegate / Revoke) */
  append(event: AttestationEvent): Promise<void>;

  /** Разрешить конечную точку несения ответственности указанного Mandate */
  resolveAccountableParty(mandateId: MandateId): Promise<HumanPrimeID>;
}

export interface AttestationVerifyResult {
  readonly verified: boolean;
  readonly root: HumanPrimeID;
  readonly invalid_node?: string;
}

export interface AttestationEvent {
  readonly event_type: "bootstrap" | "grade-switch" | "delegate" | "revoke";
  readonly mandate_id: MandateId;
  readonly issuer: HumanPrimeID;
  readonly subject: FayID;
  readonly ts: IsoTime;
  readonly signature_bundle: SignatureBundle;
}
```

**Ключевые инварианты**:

- **I-AC-1 (двойное ограничение: подпись родителя + окно валидности)**: каждый узел цепочки должен быть подписан своим родителем, а временная метка подписи должна попадать в окно валидности родителя (`[parent.not_before, parent.not_after]`); любой провал → отклонить с `E_ATTESTATION_INVALID` и запустить Revoke соответствующего Mandate.
  - **Trace**: `R3.1.2` (проверка от листа до корня, с временными метками в пределах окна валидности родительского узла), `R3.1.3` (провал любого узла → отклонить с `E_ATTESTATION_INVALID` и запустить Revoke).

- **I-AC-2 (целостность цепочки, ни один узел не может отсутствовать)**: проверка цепочки должна проходить в каждом узле от листа до корня; любой отсутствующий узел или узел с неверной подписью рассматривается как недоверенный, и вся цепочка возвращает недоверенный результат.
  - **Trace**: `R3.1.2` (проверка от листа до корня), `R3.1.3` (любой узел с провалом → отклонить с `E_ATTESTATION_INVALID`).

- **I-AC-3 (схождение вывода необратимо нерасслабляемо в цепочке)**: при выводе `scope` и `grade.autonomy` дочернего узла должны монотонно сходиться; ни у одного производного узла, расслабляющего scope или повышающего autonomy, нет легитимного пути подписи в цепочке.
  - **Trace**: `R7.1.1` (дочерний scope ⊆ родительского scope), `R7.1.2` (дочерняя autonomy ≤ родительской autonomy).

### §3.4 Revocation Registry (RR)

**Обязанности**: сервис статуса отзыва в реальном времени. Несёт инженерную опору принципа симметрии «достижимость отзыва ≥ достижимости установления».

**Двухтрековый дизайн**:

- **Pull**: RP выполняет короткий опрос (OCSP-подобный, рекомендуется stapling) при каждом принятом вызове;
- **Push**: после отзыва MS проталкивает всем подписанным RP (WebSocket / SSE / MQTT);
- **Консервативный откат**: если RP не может подтвердить статус RR в течение `StaleBudget` (по умолчанию 5 с, ужесточается по уровню), она должна отклонить вызов по Default-Deny.

**Интерфейс (Ненормативно)**:

```typescript
export interface RevocationRegistry {
  publish(receipt: RevokeReceipt): Promise<void>;
  query(mandateId: MandateId): Promise<RevocationStatus>;
  subscribe(rpId: string, scope: ScopeFilter): Subscription;
}
```

**Ключевые инварианты**:

- **I-RR-1 (публикация отзыва немедленно видима)**: как только `publish()` завершается, все последующие вызовы `query()` должны немедленно вернуть `revoked = true` в течение `RevocationVisibilityBudget` (по умолчанию 1 с, ужесточается по уровню), демонстрируя семантику сильной согласованности.
  - **Trace**: `R4.2.1` (в течение `RevocationVisibilityBudget` `query` возвращает `revoked`).

- **I-RR-2 (недостижим → Default-Deny)**: когда RR недостижим ≥ `StaleBudget`, RP должна отклонять вызовы с `E_RR_UNAVAILABLE`; «оптимистичный пропуск» запрещён.
  - **Trace**: `R2.1.4` (недостижим в пределах `StaleBudget` → Default-Deny + `E_RR_UNAVAILABLE`), `R4.2.4` (RP рассматривает провал подтверждения статуса как Default-Deny).

> **Семантическая граница**: недостижимость RR ≠ собственный обрыв связи iFay. Недостижимость RR означает лишь «невозможно определить, был ли Mandate отозван», запуская отклонение `E_RR_UNAVAILABLE`; обрыв связи iFay (включая Actually-Disconnected / Perceived-Disconnected) отдельно характеризуется §3.5 Liveness Channel и PresenceState. Эти две категории событий обрыва не заменяют друг друга — существуют ортогональные комбинации «iFay в сети, но RR недостижим» и «RR в сети, но iFay отключена», и уровень протокола сводит обе к Default-Deny.

### §3.5 Liveness Channel (LC)

**Обязанности**: совместно судит, через низкозатратный heartbeat + свежесть присутствия, о «воспринимаемой живости» iFay_Instance с точки зрения MS / RP / HP и явно характеризует окно несогласованности между «фактической живостью» и «воспринимаемой живостью» как первоклассного гражданина уровня протокола.

**Определение двойной семантики**:

- **Actually-Disconnected**: процесс / сеть / устройство iFay_Instance прекратили работу или не могут быть достигнуты ни одной внешней стороной. Объективный физический факт, напрямую не наблюдаемый на уровне протокола.
- **Perceived-Disconnected**: с точки зрения MS / RP / HP, на основе самого последнего Presence_Signal, heartbeat и состояния push RR, iFay_Instance считается отключённой. **Единственная семантика, которую уровень протокола может использовать как основание для решения.**

**Два окна несогласованности**:

- **Окно A — Actually-Disconnected ∧ Perceived-Connected**: iFay фактически отвалилась, но самый последний Presence_Signal всё ещё в пределах `max_staleness_ms` → «слепое пятно наблюдения» внутри интервала heartbeat;
- **Окно B — Actually-Connected ∧ Perceived-Disconnected**: iFay фактически в сети, но самый последний Presence_Signal превышает `max_staleness_ms` (дрожание сети / потеря heartbeat) → уровень протокола сходится по пессимистическому допущению.

**Принцип пессимистического допущения (единое правило конвергенции)**:

> Уровень протокола использует только Perceived-Disconnected как основание для решения; любая iFay_Instance, «фактически в сети, но воспринимаемая отключённой», не может тем самым претендовать на освобождение от последствий уровня протокола. В пределах двух окон несогласованности протокол должен обрабатывать по «более строгой стороне»; нет легитимного пути для «обработки по более снисходительному состоянию».

**Интерфейс (Ненормативно; разделяет базовые сигналы с §3.2 PC)**:

```typescript
export interface LivenessChannel {
  /** Снимок текущей воспринимаемой живости */
  perceived(mandateId: MandateId): PerceivedLiveness;

  /** Явно запустить пессимистический вердикт (например, при обнаружении потери heartbeat) */
  declareStale(mandateId: MandateId, reason: string): Promise<void>;
}

export interface PerceivedLiveness {
  readonly is_perceived_connected: boolean;
  readonly last_freshness: IsoTime;
  readonly staleness_ms: number;
  readonly decided_by: "presence-signal" | "heartbeat" | "explicit-declare";
}
```

**Ключевые инварианты**:

- **I-LC-1 (вердикт на основе свежести; пропуск по периоду опроса heartbeat запрещён)**: вердикты о воспринимаемом отключении должны основываться на `last_freshness ≥ now − max_staleness_ms`; «период опроса heartbeat ещё не истёк» не должно использоваться как причина продолжать пропускать вызовы.
  - **Trace**: `R12.2.2` (использовать свежесть, а не период опроса heartbeat, как основание для пропуска вызовов).

- **I-LC-2 (переход конечного автомата в Disconnected)**: как только вынесен вердикт Perceived-Disconnected, следующий переход состояния должен следовать конечному автомату §4.3 (Active → Disconnected / Active → Suspended, в зависимости от наличия действующего Endorsed_Mandate); нет легитимного пути для пребывания в исходном состоянии или переключения к более снисходительному.
  - **Trace**: `R12.1.3` (использовать только воспринимаемое отключение как основание для решения на уровне протокола; не освобождать от последствий уровня протокола).

- **I-LC-3 (восстановление требует транзакционной сверки)**: восстановление из Perceived-Disconnected в Perceived-Connected должно проходить через транзакцию сверки §8.4; автоматическое восстановление запрещено.
  - **Trace**: `R12.1.3` (нет освобождения от последствий уровня протокола во время воспринимаемого отключения — влечёт, что «восстановление требует явного транзакционного подтверждения», согласованного с транзакциями сверки в R12.4.1 / R12.4.3; в множестве Requirements, объявленных данной задачей, это заякорено 12.1).

### §3.6 Behavior Baseline Service (BBS)

**Обязанности**: поддерживает накопительный поведенческий профиль для каждой пары (Human_Prime, iFay_Instance); используется для выявления значимых отклонений от базовой линии высокочувствительными действиями и для запуска дополнительного человеческого свидетельства при отклонении (см. защиту §9.10.6 T5).

**Интерфейс (Ненормативно)**:

```typescript
export interface BehaviorBaselineService {
  /** Накопить один новый образец действия */
  record(sample: BehaviorSample): Promise<void>;

  /** Оценить отклонение текущего действия относительно базовой линии */
  evaluate(
    hp: HumanPrimeID,
    fay: FayID,
    action: AtomicAction
  ): BaselineDeviation;

  /** Применить затухание репутации (затухание балла доверия) */
  decay(hp: HumanPrimeID, fay: FayID): Promise<void>;
}

export interface BehaviorSample {
  readonly hp: HumanPrimeID;
  readonly fay: FayID;
  readonly action: AtomicAction;
  readonly scope_used: Scope;
  readonly risk_level: "low" | "normal" | "high" | "critical";
  readonly affected_resources: readonly string[];
  readonly ts: IsoTime;
}

export interface BaselineDeviation {
  readonly exceeds_threshold: boolean;
  readonly dimensions: readonly (
    | "risk_level"
    | "scope_used"
    | "affected_resources"
  )[];
  readonly recommended_action:
    | "allow"
    | "require-extra-witness"
    | "downgrade"
    | "suspend";
}
```

**Ключевые инварианты**:

- **I-BBS-1 (балл доверия должен затухать и быть ограничен сверху)**: «балл доверия» каждой пары (HP, IF) должен затухать со временем и иметь явную верхнюю границу; неограниченное накопление запрещено, дабы не разбавлять силу человеческого свидетельства, требуемую будущими высокочувствительными действиями.
  - **Trace**: `R13.5.3` (Action Reputation Decay: балл доверия должен затухать и иметь явную верхнюю границу).

- **I-BBS-2 (события свидетельства сверх базовой линии попадают в цепочку + проталкиваются в представление HP)**: каждое событие «сверх базовой линии запускает дополнительное свидетельство» должно записываться в Attestation_Chain и проталкиваться в канал представления Human_Prime; до получения дополнительного свидетельства отклонять вызов с `E_HUMAN_WITNESS_REQUIRED`.
  - **Trace**: `R13.5.4` (событие «сверх базовой линии запускает дополнительное свидетельство» записывается в AC + проталкивается в представление HP), `R13.5.2` (отклонять с `E_HUMAN_WITNESS_REQUIRED`, пока не получено дополнительное свидетельство).

- **I-BBS-3 (изменения калибровки тоже являются событиями аудита)**: сама калибровка вычисления базовой линии после определения записывается в Attestation_Chain; изменения калибровки рассматриваются как отдельный класс событий аудита, одобряемых Protocol Committee через установленный процесс.
  - **Trace**: `R13.5.1` (MS поддерживает Behavior_Baseline), `R3.1.1` (при обработке любого события аудита AC должна содержать его подписанный узел; трассируемость EARS, приведённая в этой главе, берёт лишь релевантные подпункты в множестве Requirements, объявленных данной задачей).

---
