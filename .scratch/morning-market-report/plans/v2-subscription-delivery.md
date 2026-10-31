# 구독 이메일 발송 (v2) Implementation Plan

> **For agentic workers:** 이 문서는 계획만 담는다. 구현은 아래 "결정 필요" 항목이 정해진 뒤 시작한다. 실행 시 superpowers:executing-plans를 쓴다.

**Goal:** 구독자가 매일 아침 "오늘의 시장 브리핑" 이메일을 받도록 한다. 발송 전에 이중 확인과 수신거부를 거치고, 발송 이력을 남긴다.

**Architecture:** 보고서 생성은 하루 한 번만 한다(`generate_report` 공통 함수). 생성 결과를 구독자 수만큼 복제해 보내므로 Claude 비용은 구독자 수와 무관하다. 발송은 `MailSender` 인터페이스 뒤에 두어 제공자를 바꿀 수 있게 한다. 스케줄은 APScheduler로 매일 정해진 시각에 실행한다(PRD §5의 v2 계획 유지).

**Tech Stack:** FastAPI, SQLAlchemy(SQLite), APScheduler, 메일 제공자 SDK 또는 SMTP(결정 필요), Jinja2 또는 문자열 템플릿(HTML 이메일)

**Spec:** `PRD.md` §2 Phase 2, §5 자동화 범위(v2에서 APScheduler와 이메일 실제 발송), §Out of Scope, `.scratch/morning-market-report/issues/07-email-subscription.md`

## 결정 필요 (구현 전에 정할 것)

1. **메일 제공자**
   - 추천: AWS SES (발송 단가가 낮고 API가 단순함). 대안: SendGrid, Mailgun, 네이버 클라우드 메일.
   - 필요한 것: 제공자 계정, 발신 도메인
2. **발신 도메인과 인증**: SPF, DKIM, DMARC 설정이 필요하다. 도메인이 없으면 스팸함으로 갈 가능성이 높다.
3. **발송 시각과 시간대**: 추천은 매일 07:00 KST. 이 시각에 보고서를 생성하고 발송한다.
4. **구독 확인 방식**: 추천은 이중 확인(가입 후 확인 링크 클릭). 확인되지 않은 주소에는 발송하지 않는다.
5. **실제 발송 시작 승인**: 외부 수신자에게 메일이 나가는 작업이므로, 베타 대상과 시작 시점을 직접 승인해야 한다.

## Global Constraints

- 발송 전 반드시 이중 확인을 거친 구독자에게만 보낸다.
- 모든 메일 하단에 수신거부 링크와 면책 문구("투자는 본인의 판단으로 하시기 바랍니다")를 넣는다.
- 보고서는 하루 1회만 생성하고, 같은 내용을 모든 구독자에게 보낸다.
- 개인정보(이메일, 이름)는 발송과 수신거부 처리에만 쓴다. 외부 서비스에 보내는 값은 제공자가 요구하는 최소 항목으로 한다.
- 같은 날 같은 구독자에게 두 번 발송하지 않는다 (발송 이력으로 확인).

## Review Focus

1. **같은 날 중복 발송**: 서버가 재시작되거나 스케줄이 두 번 돌면 같은 메일이 두 번 나갈 수 있다. (Task 4)
2. **수신거부 후에도 발송**: 수신거부 토큰을 처리하기 전에 발송 대상이 조회되면 안 된다. (Task 3, Task 4)
3. **확인 링크 토큰 위조**: 토큰이 예측 가능하거나 만료되지 않으면 아무 주소나 구독할 수 있다. (Task 2)
4. **제공자 오류 시 전체 중단**: 한 명의 주소가 실패해도 나머지 발송은 계속되어야 한다. (Task 4)
5. **Claude 생성 실패 시 빈 메일 발송**: 보고서가 없으면 발송하지 않고 실패를 기록한다. (Task 4)

---

### Task 1: 데이터 모델 확장

**Files:**
- Modify: `backend/app/models.py` (EmailSubscriber에 `confirmed_at`, `unsubscribe_token`, `confirm_token`, `status` 추가)
- Create: `backend/app/models.py`의 `EmailDelivery` (구독자 ID, 발송 날짜, 상태, 제공자 메시지 ID, 오류 메시지)
- Test: `backend/tests/test_delivery_models.py`

**Interfaces:**
- Consumes: 기존 `EmailSubscriber`
- Produces: `status: "pending" | "confirmed" | "unsubscribed"`. `EmailDelivery(subscriber_id, send_date: date, status: "sent" | "failed", provider_message_id: str | None, error: str | None)`. `(subscriber_id, send_date)`에 unique 제약.

- [ ] **Step 1: 실패하는 테스트**: 같은 구독자와 날짜로 `EmailDelivery`를 두 번 저장하면 `IntegrityError`가 나야 한다.
- [ ] **Step 2: 실패 확인** (`pytest tests/test_delivery_models.py`)
- [ ] **Step 3: 모델 추가 후 통과 확인**
- [ ] **Step 4: 커밋**

### Task 2: 이중 확인과 수신거부 토큰

**Files:**
- Create: `backend/app/services/tokens.py`
- Modify: `backend/app/api/subscription.py` (가입 시 확인 메일 발송 요청, `GET /api/subscription/confirm?token=`, `GET /api/subscription/unsubscribe?token=`)
- Test: `backend/tests/test_tokens.py`, `backend/tests/test_subscription_confirm.py`

**Interfaces:**
- Consumes: `EmailSubscriber` (Task 1)
- Produces:
  - `make_token(subscriber_id: int, purpose: "confirm" | "unsubscribe", secret: str) -> str`: HMAC 서명 토큰 (만료 시각 포함, 확인 토큰 7일, 수신거부 토큰은 만료 없음)
  - `verify_token(token: str, purpose: str, secret: str, now: datetime) -> int`: 서명이 틀리거나 만료되었거나 목적이 다르면 `TokenError`
  - 확인 성공 시 `status = "confirmed"`, `confirmed_at = now`. 수신거부 성공 시 `status = "unsubscribed"`.

- [ ] **Step 1: 실패하는 테스트**: 변조된 토큰, 만료된 토큰, 목적이 다른 토큰(확인 토큰으로 수신거부 시도)이 모두 거부되어야 한다.
- [ ] **Step 2: 구현 후 통과**: 서명 비밀값은 `.env`의 새 키(`SUBSCRIPTION_SECRET`)에서 읽는다. 이 키 추가는 환경 변수 변경이므로 사용자가 승인한 뒤 진행한다.
- [ ] **Step 3: 커밋**

### Task 3: 발송 대상 조회

**Files:**
- Create: `backend/app/services/recipients.py`
- Test: `backend/tests/test_recipients.py`

**Interfaces:**
- Consumes: `EmailSubscriber`, `EmailDelivery` (Task 1)
- Produces: `eligible_recipients(session, send_date: date) -> list[EmailSubscriber]`. 조건: `status == "confirmed"`이고, 같은 날짜의 `EmailDelivery`가 없는 구독자.

- [ ] **Step 1: 실패하는 테스트**: 미확인, 수신거부, 이미 발송된 구독자는 제외되어야 한다.
- [ ] **Step 2: 구현 후 통과**
- [ ] **Step 3: 커밋**

### Task 4: 발송 작업 (생성 1회, 전체 발송)

**Files:**
- Create: `backend/app/services/mail_sender.py` (`MailSender` 인터페이스, `FakeMailSender`, 제공자 구현체)
- Create: `backend/app/services/daily_delivery.py` (`run_daily_delivery(session, sender, generate_report, send_date, base_url)`)
- Create: `backend/app/services/email_template.py` (보고서 → HTML과 텍스트)
- Test: `backend/tests/test_daily_delivery.py`, `backend/tests/test_email_template.py`

**Interfaces:**
- Consumes: `eligible_recipients` (Task 3), 보고서 생성 함수(`generate_report() -> dict`, 이슈 04의 생성 파이프라인을 호출)
- Produces:
  - `MailSender.send(to: str, subject: str, html: str, text: str, unsubscribe_url: str) -> str` (제공자 메시지 ID 반환). 실패 시 `MailSendError`.
  - `run_daily_delivery(...) -> DeliveryReport(sent: int, failed: int, skipped_reason: str | None)`
  - 보고서 생성이 실패하면 발송하지 않고 `skipped_reason="report_failed"`를 기록한다 (Review Focus 5).
  - 한 구독자의 `MailSendError`는 그 구독자만 `failed`로 기록하고 다음 구독자로 넘어간다 (Review Focus 4).
- 템플릿은 시안의 이메일 미리보기 구성(시장 전망, 투자포인트, 뉴스 5개, 면책)을 따른다.

- [ ] **Step 1: 실패하는 테스트**: 보고서 생성 실패 시 발송 0건, 한 명 실패 시 나머지는 발송, 같은 날 두 번 실행해도 발송은 한 번, 메일에 수신거부 링크와 면책 문구가 있음.
- [ ] **Step 2: 구현 후 통과**
- [ ] **Step 3: 커밋**

### Task 5: 스케줄러 연결

**Files:**
- Create: `backend/app/scheduler.py` (APScheduler, 매일 07:00 KST에 `run_daily_delivery` 호출)
- Modify: `backend/app/main.py` (lifespan에서 시작·종료, 환경 변수 `DELIVERY_ENABLED`가 `1`일 때만 시작)
- Modify: `backend/requirements.txt` (`APScheduler` 버전 고정. 설치 전 2주 이상 된 버전인지 확인)
- Test: `backend/tests/test_scheduler.py` (잡 등록 여부와 실행 시각, 스케줄러가 꺼져 있으면 시작하지 않음)

**Interfaces:**
- Consumes: `run_daily_delivery` (Task 4)
- Produces: `build_scheduler(run_job: Callable[[], None]) -> BackgroundScheduler`. 잡 ID `daily_briefing`, `CronTrigger(hour=7, minute=0, timezone="Asia/Seoul")`.
- 주의: 워커를 여러 개 띄우면 같은 잡이 여러 번 돈다. Task 4의 날짜별 발송 이력이 중복을 막는다. 그래도 단일 프로세스로 운영한다.

- [ ] **Step 1: 실패하는 테스트**: 잡이 하나만 등록되고 시각이 07:00 Asia/Seoul이며, `DELIVERY_ENABLED`가 없으면 시작되지 않음.
- [ ] **Step 2: 구현 후 통과**
- [ ] **Step 3: 커밋**

### Task 6: 수신거부와 개인정보 처리

**Files:**
- Modify: `backend/app/api/subscription.py` (`DELETE /api/subscription/me?token=` 또는 수신거부 시 상태 변경만 유지할지 결정)
- Test: `backend/tests/test_privacy.py`

**Interfaces:**
- Consumes: `verify_token` (Task 2)
- Produces: 수신거부 후 이메일은 발송 대상에서 빠지고, 보관 기간(예: 수신거부 후 30일) 뒤에 삭제하는 작업을 둔다. 삭제 작업은 발송 이력 행을 함께 정리한다.

- [ ] **Step 1: 실패하는 테스트**: 수신거부 후 발송 대상에서 빠짐, 보관 기간이 지난 행은 삭제됨.
- [ ] **Step 2: 구현 후 통과**
- [ ] **Step 3: 커밋**

### Task 7: 제공자 연결과 도메인 인증 (사용자 작업 포함)

**Files:**
- Create: `backend/app/services/providers/<선택한 제공자>.py` (`MailSender` 구현)
- Test: `backend/tests/test_live_mail.py` (`RUN_LIVE=1`일 때만, 본인 주소 한 통)

**Interfaces:**
- Consumes: `MailSender` (Task 4)
- Produces: 실제 발송 구현체

- [ ] **Step 1 (사용자):** 제공자 계정 생성, 발신 도메인 DNS에 SPF, DKIM, DMARC 등록
- [ ] **Step 2:** 본인 주소로 dry-run 발송 확인. 제목, 본문, 수신거부 링크, 면책 문구 확인
- [ ] **Step 3:** 스팸함 여부와 헤더(SPF/DKIM 통과)를 확인
- [ ] **Step 4:** 커밋

### Task 8: 롤아웃

- [ ] **단계 1 (dry-run):** `DELIVERY_ENABLED=1`, 제공자 대신 `FakeMailSender`로 1주일 로그만 남김. 매일 생성 비용과 실패 건수를 확인
- [ ] **단계 2 (본인 발송):** 본인 한 명에게 실제 발송. 메일 렌더링과 수신거부 동작 확인
- [ ] **단계 3 (베타):** 승인한 소수 구독자(확인 완료자만)에게 발송. 1주일 관찰
- [ ] **단계 4 (전체):** 베타에서 문제가 없으면 확인된 전체 구독자에게 확대

각 단계에서 사용자의 승인을 받은 뒤 다음 단계로 간다. 실제 외부 발송은 되돌릴 수 없으므로 자동으로 넘어가지 않는다.

## 비용 추정

- 보고서 1회 생성 비용은 약 $0.08이다 (라이브 실측, 이슈 08 기록 참고).
- 하루 1회 생성이므로 월 약 $2.4이다. 구독자 수가 늘어도 생성 비용은 같다.
- 메일 발송 비용은 제공자 단가에 따른다 (예: SES는 1,000통당 약 $0.1 수준이며, 시연 전 가격 페이지에서 확인).

## 완료 기준 (수락 기준 초안)

| 기준 | 확인 방법 |
|---|---|
| 확인 메일을 거친 구독자에게만 발송 | Task 3 테스트 |
| 같은 날 중복 발송 없음 | Task 4 테스트 |
| 수신거부 링크가 모든 메일에 있고 동작함 | Task 2, Task 4 테스트, Task 8 단계 2 |
| 면책 문구가 모든 메일에 있음 | Task 4 테스트 |
| 제공자 실패가 다른 수신자 발송을 막지 않음 | Task 4 테스트 |
| 보고서 생성 실패 시 빈 메일을 보내지 않음 | Task 4 테스트 |
| 실제 메일이 스팸함이 아닌 받은편지함에 도착 | Task 7 Step 3 |

## Out of Scope

- 다국어 메일, 구독 주기 선택 (매일 고정)
- 구독자별 맞춤 보고서 (모든 구독자에게 같은 내용)
- 관리자 화면 (필요하면 별도 계획)
