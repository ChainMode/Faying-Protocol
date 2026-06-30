---
title: "Faying Protocol/1.0 — §5 Сообщения протокола"
version: Faying Protocol/1.0
status: Final
date: 2025-10-25
editors: [Faying Protocol Committee]
language: ru
part: "Глава 5 из 11 (текст протокола)"
---

> Навигация по тексту протокола: [Оглавление](./README.md) | предыдущая [§4 Модели данных](./04-Modeli-Dannyh.md) | следующая [§6 Криптография](./06-Kriptografiya.md)

## §5 Сообщения протокола

Эта глава даёт все сообщения уровня Faying Protocol: правила кодирования, структуру конверта, перечень 7 классов бизнес-сообщений плюс 1 класс ответа-ошибки, а также таблицу соответствия между кодами ошибок и push-уведомлениями аудита / канала представления HP.

> **Примечание об авторитетности типов**: типы `Mandate / Scope / Grade / PresenceSignal / PresenceRequirement / Endorsement / SignatureBundle / Attestation / WebAuthnAssertion / AtomicAction / RevokeReason`, на которые ссылаются блоки TypeScript этой главы, имеют свои **авторитетные определения** в §4 Модели данных (CDDL); представление TypeScript — **ненормативное** человекочитаемое представление, и там, где они различаются, преимущественную силу имеет CDDL из §4.

### §5.1 Правила кодирования

- **Основной формат (CBOR)**: кодирование по умолчанию для всей передачи в проводе — CBOR ([RFC 8949](https://www.rfc-editor.org/rfc/rfc8949)); HTTP `Content-Type` должен объявляться как `application/faying-protocol+cbor`.
- **Резервный вариант для совместимости (JSON)**: JSON ([RFC 8259](https://www.rfc-editor.org/rfc/rfc8259)) используется только в сценариях отладки / браузера / человеческого обзора; HTTP `Content-Type` должен явно объявляться как `application/faying-protocol+json`; эквивалентность безопасности гарантируется идентичной семантикой полей и форматом подписи.
- **Детерминированное кодирование**: каждый подписываемый объект должен перед подписью быть сериализован в CBOR по правилу детерминированного кодирования RFC 8949 §4.2.1, избегая неоднозначности JSON-сериализации; в форме JSON вход подписи остаётся хешем байтовой строки, сериализованной в Deterministic CBOR (см. §6.3).
- **Привязка к транспорту**: по умолчанию HTTP/1.1 и HTTP/2; конечные точки Mandate Service следуют `POST /faying-protocol/v1/{verb}`; также допускается привязка к gRPC (сервис `faying-protocol.v1`) или WebSocket / SSE (потоковая передача `faying-protocol.v1`). Все привязки транспортного уровня должны сохранять подписи и nonce уровня сообщений; замена подписей уровня сообщений идентичностью канала TLS транспортного уровня запрещена.

### §5.2 Структура конверта

Все сообщения используют единый конверт `FayingProtocolEnvelope`:

```typescript
interface FayingProtocolEnvelope<TPayload> {
  header: {
    version:    "Faying Protocol/1.0";
    msg_type:   FayingProtocolMsgType;
    msg_id:     string;        // ULID
    issued_at:  IsoTime;
    expiry:     IsoTime;
    nonce:      Nonce;
    grade:      Grade;         // текущий уровень сессии (используется RP для отклонения низкоуровневых запросов)
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

**Инварианты уровня конверта**:

- Любое отсутствующее поле или поле с неверным типом → единообразно отклонить с `E_PROTOCOL` (см. §5.4).
- В пределах окна `2 × max_message_lifetime` `nonce` принимается не более одного раза для одного и того же `subject`; повтор → `E_REPLAY`.
- `expiry` должен быть конечным и `> issued_at`; просроченные конверты не входят в путь бизнес-проверки и отклоняются напрямую с `E_PROTOCOL`.
- Входом для `signature` должно быть `H( Deterministic-CBOR( Envelope_without_signature ) )` (см. §6.3).

### §5.3 Перечень сообщений

Этот протокол определяет 7 классов бизнес-сообщений: BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE / REVOKE / FAYING_REQUEST / DISCLOSURE, плюс 1 класс ответа-ошибки ERROR (см. §5.4).

#### §5.3.1 BOOTSTRAP (Faying Action)

**Назначение**: Human Prime устанавливает Mandate в MS через BOOTSTRAP, выпуская мандатную авторизацию для iFay. BOOTSTRAP — **единственная легитимная точка входа Faying Action** Faying Protocol.

```typescript
interface BootstrapClaims {
  human_prime:   HumanPrimeID;
  fay:           FayID;
  scope:         Scope;
  grade:         Grade;
  presence_req:  PresenceRequirement;
  not_after:     IsoTime;          // должен быть конечным
  human_witness: WebAuthnAssertion; // user-verification = true
  endorsement?:  Endorsement;       // опционально; если присутствует, выпустить Endorsed Mandate (см. §4 / §11)
  faying_request_ref?: string;      // на пути, инициированном IF, ссылается на соответствующий FAYING_REQUEST.msg_id
}
```

**Успешный ответ**: возвращает полный объект `Mandate` (включая `signature_bundle`).

**Жёсткие ограничения на уровне протокола**:

- `not_after` должен быть конечным и `> not_before`; `∞` и отрицательные значения запрещены; нарушение → единообразно отклонить с `E_PROTOCOL` (согласовано с §3.1 I-MS-1 / Property 7).
- Отсутствие поля `human_witness` или неверная подпись → единообразно отклонить с `E_HUMAN_WITNESS_REQUIRED`; нет легитимного пути для IF / MS / Supervisory Agent заменить HP в завершении подтверждения.
- Когда BOOTSTRAP отвечает на ранее инициированный iFay `FAYING_REQUEST`, `faying_request_ref` должен указывать на `msg_id` того запроса; MS должен в Attestation Chain связать «инициировано iFay → свидетельство HP → вступление в силу» в одну неделимую цепочку свидетельств (см. §5.3.6 и §3.3).
- Когда присутствует поле `endorsement`, MS должен перед подписью проверить `endorsed_scope ⊆ scope` ∧ `endorsed_grade.autonomy ≤ grade.autonomy` ∧ `0 < endorsed_lifetime_ms ≤ (not_after − not_before)`; любой провал → отклонить с `E_ENDORSEMENT_INVALID` (код ошибки 1013).

#### §5.3.2 PRESENCE (непрерывная калибровка)

**Назначение**: iFay_Instance периодически проталкивает сигналы присутствия, производимые Presence Device, в MS, обновляя `PresenceState.last_freshness` соответствующего Mandate.

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

**Жёсткие ограничения на уровне протокола**:

- `signal` должен нести обязательную тройку §3.2 I-PC-1 (`nonce / produced_at / device_attestation`) и быть подписан Presence Device; отсутствие любого → `E_PROTOCOL`. Окно свежести задаётся `presence_req.max_staleness_ms` соответствующего Mandate, а не переносится сигналом.
- Сигнал за пределами `presence_req.max_staleness_ms` → `E_PRESENCE_STALE`, и запускает ужесточение по §3.2 I-PC-3 (миграция к более строгому уровню или Suspended).
- Одна и та же пара `(subject, nonce)`, повторяющаяся в пределах окна `2 × max_message_lifetime` → единообразно `E_REPLAY`.

#### §5.3.3 GRADE_SWITCH (переключение уровня)

**Назначение**: корректирует уровень авторизации (повышение / понижение) в течение жизненного цикла Mandate.

```typescript
interface GradeSwitchClaims {
  mandate_id:    MandateID;
  target_grade:  Grade;
  reason:        "human-initiated" | "presence-loss" | "policy-trigger";
  human_witness?: WebAuthnAssertion;  // обязательно в направлении повышения, опционально при понижении
}
```

**Инвариант уровня протокола (обязательное свидетельство при повышении)**: когда `target_grade.autonomy > current.autonomy` (то есть строго выше автономности, чем текущий уровень), `human_witness` является **MUST**; отсутствие или неверная подпись → единообразно отклонить с `E_HUMAN_WITNESS_REQUIRED`. Направление понижения (`target_grade.autonomy ≤ current.autonomy`) может запускаться протоколом автоматически (например, `presence-loss` / `policy-trigger`); `human_witness` не требуется.

#### §5.3.4 DELEGATE (вывод для другого устройства / субагента)

**Назначение**: выводит дочерний Mandate из родительского Mandate, используется в сценариях с разными устройствами или субагентами.

```typescript
interface DelegateClaims {
  parent_mandate: MandateID;
  child_subject:  FayID;            // производный FayID
  child_scope:    Scope;            // должен ⊆ parent.scope
  child_grade:    Grade;            // child_grade.autonomy должна ≤ parent.grade.autonomy (ниже или равная автономность, т. е. строже или равно)
  device_id?:     string;           // привязать к конкретному терминалу при выводе на другое устройство
}
```

**Жёсткие ограничения на уровне протокола**:

- `child_scope ⊆ parent.scope` ∧ `child_grade.autonomy ≤ parent.grade.autonomy`; любое расширение в любом из направлений → отклонить с `E_PROTOCOL` (согласовано с §3.1 I-MS-4 / Property 6).
- `signature_bundle.chain` дочернего Mandate должна нести контрподпись родительского Mandate, образуя производный узел в Attestation Chain.
- Когда родительский Mandate несёт `endorsement`, `endorsement` дочернего Mandate (если присутствует) должен сходиться в пределах родительского endorsement; несхождение → отклонить с `E_ENDORSEMENT_INVALID`.

#### §5.3.5 REVOKE

**Назначение**: отзывает Mandate; опционально каскадно отзывает все производные дочерние Mandate.

```typescript
interface RevokeClaims {
  mandate_id:   MandateID;
  cascade:      boolean;            // каскадный отзыв всех производных дочерних Mandate (по умолчанию true)
  reason:       RevokeReason;
  effective_at: IsoTime;            // по умолчанию = now; допускается отложенный отзыв
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

`RevokeReason` соответствует один к одному девяти условиям-триггерам из главы 13.

**Жёсткие ограничения на уровне протокола**:

- Достижимость отзыва должна быть ≥ достижимости Bootstrap (согласовано с Property 4 / R4.1); не существует пути для самой iFay легитимно инициировать REVOKE.
- Когда `cascade = true`, все производные дочерние Mandate должны стать видимыми как `revoked` в течение `RevocationVisibilityBudget` (согласовано с Property 14).
- Отзыв необратим: `Revoked` — поглощающее состояние; восстановление авторизации должно проходить снова через BOOTSTRAP с новым `mandate_id`, не равным старому `mandate_id` (согласовано с Property 10).

#### §5.3.6 FAYING_REQUEST / FAYING_REQUEST_RESP (двунаправленный Faying, инициированный IF)

**Назначение**: iFay проактивно запрашивает Faying у Human Prime (запрашивая установление или корректировку мандатного отношения). Это сообщение **не порождает напрямую Mandate**; MS выступает лишь как пересыльщик, проталкивая запрос в канал представления HP; затем HP завершает подтверждение и вступление в силу через BOOTSTRAP (см. §2.4 Фаза A0).

```typescript
interface FayingRequestClaims {
  initiator:        FayID;          // сама iFay
  target_human:     HumanPrimeID;   // целевой HP
  proposed_scope:   Scope;          // предлагаемый объём мандата
  proposed_grade:   Grade;          // предлагаемый уровень
  reason:           string;         // дополнение свободным текстом
  reason_code:
    | "establish"
    | "adjust-scope"
    | "adjust-grade"
    | "renew"
    | "endorsement-request";
  expected_lifetime_ms?: number;    // ожидаемый срок жизни Mandate
  proposed_endorsement?: Endorsement; // если также запрашивается Endorsed Mandate
}

interface FayingRequestRespClaims {
  request_msg_id: string;           // ссылается на восходящий FAYING_REQUEST.msg_id
  status:         "accepted" | "rejected" | "timeout";
  bootstrap_ref?: string;           // когда status=accepted, указывает на BOOTSTRAP.msg_id, завершённый HP
  reject_reason?: string;
}
```

**Жёсткие ограничения на уровне протокола**:

- Инициированный IF FAYING_REQUEST **не** порождает напрямую никакого изменения состояния Faying; только ответ HP в течение `BootstrapTimeout` через BOOTSTRAP (несущий `faying_request_ref` и проверяемый `human_witness`) вводит запрос в силу.
- Если HP не даёт явного подтверждения в течение `BootstrapTimeout`, MS должен вернуть `FAYING_REQUEST_RESP { status="timeout" }` и записать событие в Attestation Chain, что соответствует коду ошибки `E_FAYING_REQUEST_NOT_CONFIRMED` (1014).
- Нет легитимного пути для MS / IF / Supervisory Agent заменить HP в завершении подтверждения; отсутствие `human_witness` → `E_HUMAN_WITNESS_REQUIRED` (1010).
- Частота FAYING_REQUEST для каждой пары `(HP, IF)` ограничена `ConfirmationRateLimit` (см. Приложение B); превышение лимита обрабатывается по §9.10.7 T6.

#### §5.3.7 DISCLOSURE (структурированное сообщение раскрытия)

**Назначение**: структурированное сообщение раскрытия, используемое iFay при отчёте или запросе подтверждения. Регуляторы и MS могут проводить аудит этого сообщения на уровне схемы; использование чистого свободного текста для сокрытия ключевой информации запрещено (см. §9.10.4 T3).

```typescript
interface DisclosureClaims {
  mandate_id:         MandateID;
  /** mandatory_fields (любое отсутствующее → рассматривается как ошибка протокола) */
  action:             AtomicAction;          // одно раскрытие соответствует ровно одному Atomic_Action
  scope_used:         Scope;                 // фактически использованное подмножество scope
  risk_level:         "low" | "normal" | "high" | "critical";
  reversibility:      "reversible" | "partially-reversible" | "irreversible";
  affected_resources: string[];
  uncertainty_flags:  string[];              // например ["ambiguous-target", "stale-context"]
  /** опциональные дополнения */
  free_text?:         string;
  intent?:            "report" | "request-confirmation";
  endorsement_id?:    string;                // если произошло во время Disconnected, указывает на соответствующий endorsement
}
```

**Список принуждения `mandatory_fields`** (согласован с R13.3 / §9.10.4):

`action` / `scope_used` / `risk_level` / `reversibility` / `affected_resources` / `uncertainty_flags`.

**Жёсткие ограничения на уровне протокола**:

- Любое отсутствующее или неразбираемое `mandatory_fields` → MS должен отклонить с `E_PROTOCOL` (1099) и протолкнуть в канал представления HP;
- Высокочувствительные действия (`risk_level ∈ {high, critical}`) должны **перед** выполнением измерения D сначала выпустить DISCLOSURE и дождаться явного подтверждения HP (если только текущий уровень уже не G4 Autonomous и действие не попадает в основной scope; см. §7);
- Если последующий аудит обнаружит, что `mandatory_fields` из DISCLOSURE несогласованы с фактическим действием, MS должен отозвать Mandate с `RevokeReason="ego-deviation"`;
- DISCLOSURE для действий, выполненных во время Disconnected, должно нести `endorsement_id`, чтобы действие можно было независимо проследить к одному конкретному endorsement.

### §5.4 Коды ошибок

Ответы-ошибки единообразно используют сообщение `ERROR` (конверт `msg_type = "ERROR"`); тело `claims` имеет форму `{ code, message, mandate_id?, recovery_hint? }`. В таблице ниже даны все коды ошибок и их ограничения push-уведомления аудита и канала представления HP (согласовано с §EH.3).

| Код | Имя | Смысл | Ответ | Обязан войти в аудит | Обязан войти в представление HP |
| ---: | --- | --- | --- | :---: | :---: |
| 1001 | `E_NO_MANDATE` | Запрос не несёт Mandate | Отклонить | ✗ | ✗ |
| 1002 | `E_MANDATE_EXPIRED` | Mandate истёк | Отклонить + запустить Revoke | ✓ | ✗ |
| 1003 | `E_SCOPE_VIOLATION` | Вызов превышает scope | Отклонить + записать подозрительное | ✓ | ✗ |
| 1004 | `E_GRADE_INSUFFICIENT` | Текущий уровень недостаточен для чувствительного действия | Отклонить + предложить повышение | ✓ | ✗ |
| 1005 | `E_PRESENCE_STALE` | Сигнал присутствия просрочен | Отклонить + запустить понижение | ✓ | ✗ |
| 1006 | `E_REVOKED` | Mandate отозван | Отклонить | ✓ | ✓ |
| 1007 | `E_ATTESTATION_INVALID` | Проверка attestation провалена | Отклонить + запустить Revoke | ✓ | ✓ |
| 1008 | `E_RR_UNAVAILABLE` | Реестр отзыва недостижим | Отклонить по Default-Deny | ✓ | ✗ |
| 1009 | `E_REPLAY` | nonce повторён | Отклонить + оповещение безопасности | ✓ | ✓ |
| 1010 | `E_HUMAN_WITNESS_REQUIRED` | Повышению уровня / двунаправленному Faying не хватает человеческого свидетельства | Отклонить | ✓ | ✗ |
| 1011 | `E_ROGUE_DETECTED` | Обнаружено Rogue-поведение | Отклонить + принудительный Revoke | ✓ | ✓ |
| 1012 | `E_BUDGET_EXCEEDED` | Превышен ResourceBudget | Отклонить + запустить понижение | ✓ | ✗ |
| 1013 | `E_ENDORSEMENT_INVALID` | Поле endorsement недействительно (вкл. `endorsed_scope ⊄ scope` / `endorsed_grade.autonomy > grade.autonomy` / `endorsed_lifetime` отсутствует или слишком длинный / подделано) | Отклонить + запустить Revoke этого Mandate | ✓ | ✓ |
| 1014 | `E_FAYING_REQUEST_NOT_CONFIRMED` | Инициированный IF FAYING_REQUEST не подтверждён явно HP в течение `BootstrapTimeout` | Отклонить + записать в Attestation Chain | ✓ | ✗ |
| 1099 | `E_PROTOCOL` | Ошибка уровня протокола (версия / формат / подпись / отсутствие или неразбираемость `mandatory_fields` в DISCLOSURE) | Отклонить | ✓ | ✗* |

> **Примечание `*`**: по умолчанию `E_PROTOCOL` входит только в аудит; но когда он запущен с пути отсутствия или неразбираемости `mandatory_fields` в DISCLOSURE из §5.3.7, MS должен дополнительно протолкнуть в канал представления HP (см. §5.3.7 и §9.10.4 T3).
>
> **Семантические примечания об аудите / представлении HP**:
>
> - **Обязан войти в аудит**: ошибки должны записываться в Attestation Chain / журнал аудита как пятёрка `(error_code, mandate_id, ts, RP_id, reason)`; кроме `E_NO_MANDATE` (нет контекста Mandate), все коды ошибок имеют ✓.
> - **Обязан войти в представление HP**: ошибки должны проталкиваться в канал представления HP; RP не должна тихо их проглатывать. Базовая четвёрка (`E_REVOKED` / `E_ATTESTATION_INVALID` / `E_REPLAY` / `E_ROGUE_DETECTED`) предписана §EH.3; `E_ENDORSEMENT_INVALID`, поскольку его цепочка триггеров неизбежно сопровождается `E_REVOKED`, тоже проталкивается в канал представления HP.
> - Ответам-ошибкам **запрещено** нести внутреннее состояние MS, отпечатки закрытых ключей Mandate, идентификаторы других Human Prime или иную чувствительную информацию (см. §EH.3).

---
