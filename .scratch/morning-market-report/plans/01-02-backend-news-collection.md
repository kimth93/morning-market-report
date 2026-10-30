# 백엔드 기초 + 네이버 뉴스 수집 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** FastAPI 백엔드 골격, SQLite 스키마, 환경 변수 설정을 세우고, 네이버 뉴스 검색 API로 경제·증권 뉴스 Top 5를 수집해 `news_items`에 저장하고 조회할 수 있게 한다.

**Architecture:** HTTP 클라이언트(`collectors/naver_news.py`)는 네이버 호출만, 정규화(`collectors/normalize.py`)는 순수 함수만 담당하고, 수집 파이프라인(`services/news_collector.py`)이 둘을 묶어 중복 제거·선정·저장을 수행한다. 라우터(`api/news.py`)는 파이프라인을 호출하는 얇은 계층이다. 외부 호출은 전부 주입 가능하게 만들어 테스트는 네트워크 없이 돈다.

**Tech Stack:** Python, FastAPI, uvicorn, SQLAlchemy (SQLite), requests, python-dotenv, pytest, httpx (TestClient)

**Spec:** `PRD.md` (§2 Phase 1, §6 API 계약, §Testing Decisions), `.scratch/morning-market-report/issues/01-backend-foundation.md`, `.scratch/morning-market-report/issues/02-news-collection.md`

## Global Constraints

- 백엔드는 Python + FastAPI, DB는 SQLite, 네이버 호출은 `requests`, 환경 변수는 `python-dotenv` (PRD §1).
- 뉴스 수집 소스는 네이버 뉴스 검색 API `https://openapi.naver.com/v1/search/news.json`만 사용한다 (이번 결정).
- 네이버 요청 파라미터 한도: `display` 최대 100, `start` 최대 1000, `sort`는 `date` 또는 `sim`.
- 네이버 인증은 헤더 `X-Naver-Client-Id`, `X-Naver-Client-Secret`. 환경 변수는 `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`.
- 키 값은 저장소에 커밋하지 않는다. `.env`는 이미 `.gitignore`에 있다.
- 기사 본문은 저장하지 않는다. 저장 대상은 제목, 언론사, 발행일, 원문 링크, 네이버 제공 요약(description)뿐이다.
- 테스트는 네트워크 호출 없이 통과해야 한다. 실제 네이버 호출 테스트는 `live` 마커로 분리하고 기본 실행에서 제외한다.

## Decisions (이 계획에서 정한 것)

- **키워드 묶음**: 아래 `KEYWORDS`를 `collectors/keywords.py`에 상수로 둔다. `코스피`, `코스닥`, `증시`, `금리`, `환율`, `연준`, `반도체`, `채권`, `나스닥`, `기업 실적`.
- **Top 5 기준**: 키워드별로 `sort=date`로 받아 합친 뒤, 원문 URL로 중복 제거하고 발행 시각 내림차순 상위 5개를 고른다.
- **언론사**: 원문 도메인을 `collectors/press_map.py`의 매핑으로 한글 언론사명으로 바꾸고, 매핑이 없으면 도메인 그대로 저장한다. 매핑 목록은 예시로 시작하고 실제 수집 결과를 보고 채운다.
- **원문 URL**: `originallink`를 쓰고, 비어 있으면 `link`(네이버 뉴스 URL)로 대체한다.
- **날짜**: 발행 시각을 `Asia/Seoul`로 바꾼 뒤 날짜 부분만 `news_items.date`(Date)에 저장한다.
- **실패 처리**: 키워드 하나라도 네이버 호출이 실패하면 수집 전체를 실패시킨다. 일부만 저장된 상태를 조용히 만들지 않는다.
- **스키마 추가**: 이슈 01 스키마에 `description`(Text, nullable)을 더한다. 이슈 03 요약 입력으로 쓰기 위해서다.
- **엔드포인트**: PRD §6의 `POST /api/news/generate`는 이슈 04·06 범위다. 이번 단계는 `POST /api/news/collect`와 `GET /api/news/latest`를 쓴다.
- **로컬 실행 경로**: 모든 명령은 `backend/` 디렉터리에서 실행한다.

## Review Focus

1. **네이버 응답 제목에 `<b>`와 HTML 엔티티(`&quot;`, `&amp;`)가 섞임** → 저장되는 제목은 태그와 엔티티가 없어야 한다. (Task 4)
2. **같은 기사가 여러 키워드에 걸림** → `news_items`에 같은 URL이 두 번 들어가지 않는다. (Task 6)
3. **`originallink`가 비어 있음** → `link`로 대체하고, 어느 쪽도 없으면 해당 항목을 건너뛴다. 예외로 죽지 않는다. (Task 6)
4. **네이버 401(키 오류)·429(한도 초과)·타임아웃** → 조용히 빈 목록을 반환하지 않고 명확한 오류로 올라간다. API 계층은 502로 응답한다. (Task 5, Task 7)
5. **결과가 5개 미만(0건 포함)** → 있는 만큼만 반환하고 빈 항목을 채워 넣지 않는다. (Task 6)
6. **pubDate의 `+0900` 오프셋** → 시간대 변환 후 날짜가 어긋나지 않는다. 예: `2026-07-08 00:30 KST`는 `2026-07-08`이다. (Task 4)

---

### Task 1: 설정 로더와 pytest 설정

**Files:**
- Modify: `backend/app/config.py` (새 파일)
- Modify: `backend/tests/test_config.py` (전부 교체)
- Create: `backend/pytest.ini`
- Create: `backend/.env.example`

**Interfaces:**
- Consumes: 없음
- Produces: `get_settings() -> Settings`. `Settings`는 `claude_api_key: str`, `naver_client_id: str`, `naver_client_secret: str`, `database_url: str` 필드를 가진다. `database_url` 기본값은 `"sqlite:///./app.db"`. 필수 값이 없으면 `ValueError`를 낸다.

- [ ] **Step 1: 기존 테스트 교체 작성**

`test_config.py`는 존재하지 않는 `app.config` 모듈 대신 `get_settings()`를 검증하도록 새로 쓴다. 각 테스트는 `monkeypatch.setenv`/`delenv`와 `tmp_path`를 쓰고, `.env` 파일 로딩은 `dotenv_path`를 인자로 주는 방식으로 검증한다. 검증할 것은 세 가지다.
- 필수 세 키가 모두 있으면 `Settings` 필드에 값이 채워진다.
- `DATABASE_URL`을 생략하면 기본값 `sqlite:///./app.db`가 된다.
- `NAVER_CLIENT_SECRET`이 없으면 `ValueError`가 난다.

- [ ] **Step 2: 실패 확인**

Run: `cd backend && pytest tests/test_config.py -v`
Expected: FAIL (`app.config` 없음 또는 `get_settings` 없음)

- [ ] **Step 3: `app/config.py` 구현**

`get_settings(dotenv_path: str | None = None) -> Settings`. 내부에서 `dotenv.load_dotenv(dotenv_path)`를 호출하고 `os.environ`을 읽는다. 필수 키 누락 시 어떤 키가 없는지 메시지에 담아 `ValueError`를 낸다. `Settings`는 `dataclass(frozen=True)`로 둔다.

- [ ] **Step 4: 통과 확인**

Run: `cd backend && pytest tests/test_config.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: `pytest.ini`와 `.env.example` 작성**

`pytest.ini`: `pythonpath = .`, 마커 `live: 실제 네이버 API 호출 (RUN_LIVE=1일 때만 실행)`을 등록한다.
`.env.example`: 키 이름만 적고 값은 비운다. 실제 값은 넣지 않는다.

- [ ] **Step 6: 커밋**

```bash
git add backend/app/config.py backend/tests/test_config.py backend/pytest.ini backend/.env.example
git commit -m "feat(backend): add settings loader and pytest config"
```

---

### Task 2: DB 스키마와 세션

**Files:**
- Create: `backend/app/db.py`
- Create: `backend/app/models.py`
- Test: `backend/tests/test_db.py`

**Interfaces:**
- Consumes: `Settings.database_url` (Task 1)
- Produces:
  - `db.py`: `Base: DeclarativeBase`, `make_engine(database_url: str) -> Engine`, `make_session_factory(engine: Engine) -> sessionmaker[Session]`, `init_db(engine: Engine) -> None`
  - `models.py`: `NewsItem`, `NewsSummary`, `EmailSubscriber` (모두 `Base` 상속)
  - `NewsItem` 컬럼: `id: int` (PK), `title: str`, `source: str`, `date: date`, `url: str` (unique), `description: str | None`, `collected_at: datetime`
  - `NewsSummary` 컬럼: `id`, `news_id` (FK → news_items.id), `summary_text: str`, `hallucination_risk: str`, `generated_at: datetime`
  - `EmailSubscriber` 컬럼: `id`, `email: str`, `name: str`, `subscribed_at: datetime`

- [ ] **Step 1: 실패하는 테스트 작성**

테스트는 임시 SQLite 파일로 엔진을 만들고 다음을 검증한다.
- `init_db` 후 `news_items`, `news_summaries`, `email_subscribers` 세 테이블이 존재한다 (`sqlalchemy.inspect(engine).get_table_names()`).
- 같은 `url`을 두 번 저장하면 `IntegrityError`가 난다.
- `description`을 주지 않고 저장해도 성공하고 값은 `None`이다.

- [ ] **Step 2: 실패 확인**

Run: `cd backend && pytest tests/test_db.py -v`
Expected: FAIL (`app.db` 없음)

- [ ] **Step 3: `db.py`, `models.py` 구현**

`make_engine`은 SQLite에서 `check_same_thread=False`를 넣는다. 모델 정의는 위 Interfaces 그대로 따른다. `hallucination_risk`는 문자열 컬럼으로 두고 허용 값 검증은 이슈 03에서 한다.

- [ ] **Step 4: 통과 확인**

Run: `cd backend && pytest tests/test_db.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: 커밋**

```bash
git add backend/app/db.py backend/app/models.py backend/tests/test_db.py
git commit -m "feat(backend): add sqlite schema for news, summaries, subscribers"
```

---

### Task 3: FastAPI 앱과 헬스 체크

**Files:**
- Create: `backend/app/main.py`
- Test: `backend/tests/test_main.py`

**Interfaces:**
- Consumes: `get_settings` (Task 1), `make_engine`, `init_db` (Task 2)
- Produces: `app: FastAPI`. `GET /health` → `{"status": "ok"}`. 앱 시작 시 `init_db`를 호출한다. 엔진과 세션 팩토리는 `app.state.session_factory`에 둔다.

- [ ] **Step 1: 실패하는 테스트 작성**

`TestClient(app)`으로 `GET /health`가 200이고 본문이 `{"status": "ok"}`인지 검증한다. 테스트에서는 `DATABASE_URL`을 `tmp_path` 기반 값으로 monkeypatch한다.

- [ ] **Step 2: 실패 확인**

Run: `cd backend && pytest tests/test_main.py -v`
Expected: FAIL (`app.main` 없음)

- [ ] **Step 3: `main.py` 구현**

`lifespan` 컨텍스트에서 `get_settings()` → `make_engine` → `init_db` → `app.state.session_factory` 설정 순서로 한다. 라우터 등록은 Task 7에서 추가하므로 여기서는 헬스 체크만 둔다.

- [ ] **Step 4: 통과 확인**

Run: `cd backend && pytest tests/test_main.py -v`
Expected: PASS

- [ ] **Step 5: 수동 기동 확인**

Run: `cd backend && uvicorn app.main:app --reload` 실행 후 `curl http://127.0.0.1:8000/health`
Expected: `{"status":"ok"}`. 필수 키 없이 기동하면 `ValueError`로 실패해야 한다. 키는 `.env`에 임시로 넣어 확인하고 커밋하지 않는다.

- [ ] **Step 6: 커밋**

```bash
git add backend/app/main.py backend/tests/test_main.py
git commit -m "feat(backend): add fastapi app with health check"
```

---

### Task 4: 정규화 순수 함수

**Files:**
- Create: `backend/app/collectors/__init__.py`
- Create: `backend/app/collectors/normalize.py`
- Create: `backend/app/collectors/press_map.py`
- Test: `backend/tests/test_normalize.py`

**Interfaces:**
- Consumes: 없음
- Produces:
  - `normalize.py`:
    - `strip_markup(text: str) -> str`: `<...>` 태그 제거 후 HTML 엔티티를 해제한다.
    - `parse_pub_date(value: str) -> datetime`: RFC 822 문자열을 시간대 포함 datetime으로 파싱한다.
    - `to_kst_date(value: datetime) -> date`: `Asia/Seoul`로 변환한 날짜를 돌려준다.
    - `press_name(url: str) -> str`: 도메인을 `press_map.PRESS_BY_DOMAIN`에서 찾고, 없으면 도메인 문자열을 돌려준다. `www.` 접두사는 무시한다.
  - `press_map.py`: `PRESS_BY_DOMAIN: dict[str, str]`. 초기 예시 항목만 둔다.

- [ ] **Step 1: 실패하는 테스트 작성**

- `strip_markup("<b>삼성</b>&quot;주가&quot; &amp; 환율")` → `'삼성"주가" & 환율'`
- `parse_pub_date("Wed, 08 Jul 2026 00:30:00 +0900")`는 tzinfo가 있고 `to_kst_date`가 `date(2026, 7, 8)`이다.
- `parse_pub_date("Tue, 07 Jul 2026 15:30:00 +0000")`(UTC 15:30 = KST 다음날 00:30)을 `to_kst_date`에 넣으면 `date(2026, 7, 8)`이다. 이 케이스가 Review Focus 6번을 막는다.
- `press_name("https://www.unknown-site.example/news/1")` → `"unknown-site.example"`
- `press_name`에 `PRESS_BY_DOMAIN`에 등록된 도메인을 넣으면 등록된 이름을 돌려준다. 테스트는 monkeypatch로 매핑 한 항목을 주입한다.

- [ ] **Step 2: 실패 확인**

Run: `cd backend && pytest tests/test_normalize.py -v`
Expected: FAIL (모듈 없음)

- [ ] **Step 3: 구현**

`strip_markup`은 `re`로 태그를 지우고 `html.unescape`를 적용한다. `parse_pub_date`는 `email.utils.parsedate_to_datetime`을 쓴다. `to_kst_date`는 `zoneinfo.ZoneInfo("Asia/Seoul")`을 쓴다. `press_name`은 `urllib.parse.urlparse(url).hostname`을 쓴다.

- [ ] **Step 4: 통과 확인**

Run: `cd backend && pytest tests/test_normalize.py -v`
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add backend/app/collectors/ backend/tests/test_normalize.py
git commit -m "feat(backend): add news normalization helpers"
```

---

### Task 5: 네이버 뉴스 검색 클라이언트

**Files:**
- Create: `backend/app/collectors/naver_news.py`
- Test: `backend/tests/test_naver_news.py`

**Interfaces:**
- Consumes: `Settings.naver_client_id`, `Settings.naver_client_secret` (Task 1)
- Produces:
  - `class NaverAPIError(Exception)`: 속성 `status_code: int | None`, `message: str`
  - `fetch_news(query: str, settings: Settings, display: int = 100, sort: str = "date", http_get: Callable | None = None) -> list[dict]`: 네이버 응답의 `items` 배열을 그대로 돌려준다. `http_get`은 테스트용 주입점이며 기본값은 `requests.get`이다.
  - 호출 URL은 `https://openapi.naver.com/v1/search/news.json`, 타임아웃은 10초다.

- [ ] **Step 1: 실패하는 테스트 작성**

`http_get`을 가짜 함수로 주입해서 검증한다.
- 200 응답이면 `items` 리스트를 돌려주고, 요청 헤더에 두 키가 들어가며, 파라미터에 `query`, `display=100`, `sort=date`가 들어간다.
- 401 응답이면 `NaverAPIError`가 나고 `status_code == 401`이다.
- 429 응답이면 `NaverAPIError`가 나고 `status_code == 429`이다.
- 가짜 함수가 `requests.Timeout`을 던지면 `NaverAPIError`가 나고 `status_code is None`이다.
- `display=101`을 넘기면 `ValueError`가 난다 (네이버 한도 방어).

- [ ] **Step 2: 실패 확인**

Run: `cd backend && pytest tests/test_naver_news.py -v`
Expected: FAIL (모듈 없음)

- [ ] **Step 3: 구현**

`http_get(url, headers=..., params=..., timeout=10)` 형태로 호출하고 `resp.status_code != 200`이면 `NaverAPIError`를 낸다. `requests.RequestException`은 잡아서 `NaverAPIError`로 감싼다. 응답 JSON의 `items`가 없으면 빈 리스트를 돌려준다.

- [ ] **Step 4: 통과 확인**

Run: `cd backend && pytest tests/test_naver_news.py -v`
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add backend/app/collectors/naver_news.py backend/tests/test_naver_news.py
git commit -m "feat(backend): add naver news search client"
```

---

### Task 6: 수집 파이프라인

**Files:**
- Create: `backend/app/collectors/keywords.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/news_collector.py`
- Test: `backend/tests/test_news_collector.py`

**Interfaces:**
- Consumes: `fetch_news`, `NaverAPIError` (Task 5), `strip_markup`, `parse_pub_date`, `to_kst_date`, `press_name` (Task 4), `NewsItem` 및 세션 팩토리 (Task 2)
- Produces:
  - `keywords.py`: `KEYWORDS: list[str]` (Decisions의 10개 키워드)
  - `news_collector.py`:
    - `collect_top_news(session: Session, settings: Settings, keywords: list[str] = KEYWORDS, limit: int = 5, fetch: Callable = fetch_news) -> list[NewsItem]`
    - 반환값은 이번 실행에서 새로 저장된 항목과, 이미 DB에 있던 같은 URL 항목을 포함하지 않는다. 단, 최종 Top 5는 DB 저장 여부와 관계없이 선정된 기사 목록이다. (아래 Step 3에서 결정을 명시)

- [ ] **Step 1: 실패하는 테스트 작성**

가짜 `fetch`(키워드별 고정 응답)와 임시 SQLite 세션으로 검증한다.
- 두 키워드가 같은 `originallink`를 가진 기사를 돌려주면 DB에는 한 번만 저장된다.
- `originallink`가 빈 문자열이면 `link`가 `url`로 저장된다. 둘 다 빈 항목은 건너뛴다.
- 결과는 `date` 내림차순이고 길이는 `limit`(5)이다. 후보가 3개뿐이면 3개를 돌려준다. 빈 항목을 채우지 않는다.
- 이미 DB에 있는 URL은 다시 저장하지 않는다 (두 번 실행해도 행 수가 같다).
- 한 키워드의 `fetch`가 `NaverAPIError`를 던지면 `collect_top_news`도 `NaverAPIError`를 던지고 DB에는 아무것도 저장되지 않는다.
- 저장되는 `title`에 `<b>`가 없다 (Review Focus 1).

- [ ] **Step 2: 실패 확인**

Run: `cd backend && pytest tests/test_news_collector.py -v`
Expected: FAIL (모듈 없음)

- [ ] **Step 3: 구현**

흐름은 다음과 같다. ① 키워드마다 `fetch(keyword, settings, sort="date")` 호출 → ② 각 항목을 `title=strip_markup(title)`, `url=originallink or link`, `source=press_name(url)`, `date=to_kst_date(parse_pub_date(pubDate))`, `description=strip_markup(description) or None`으로 정규화 → ③ `url` 기준 중복 제거 → ④ `date` 내림차순 정렬 후 `limit`개 선택 → ⑤ DB에 없는 URL만 `NewsItem`으로 저장하고 `collected_at`은 UTC now로 채운다.

결정: 선택된 기사가 이미 DB에 있으면 저장만 건너뛰고 응답에는 포함한다. 그래야 "지금 생성"을 여러 번 눌러도 같은 Top 5가 나온다. 모든 호출 전에 실패가 나면 저장하지 않는다. 저장은 ④ 이후 한 트랜잭션으로 한다.

- [ ] **Step 4: 통과 확인**

Run: `cd backend && pytest tests/test_news_collector.py -v`
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add backend/app/collectors/keywords.py backend/app/services/ backend/tests/test_news_collector.py
git commit -m "feat(backend): add news collection pipeline with dedupe and top-n selection"
```

---

### Task 7: 뉴스 API 엔드포인트

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/news.py`
- Modify: `backend/app/main.py` (라우터 등록)
- Test: `backend/tests/test_news_api.py`

**Interfaces:**
- Consumes: `collect_top_news` (Task 6), `NaverAPIError` (Task 5), `NewsItem` (Task 2), `app.state.session_factory` (Task 3)
- Produces:
  - `router: APIRouter` (prefix `/api/news`)
  - `POST /api/news/collect` → 200 `{"news_items": [...], "collected_at": "<ISO 8601>"}`. 각 항목은 `title`, `source`, `date`(YYYY-MM-DD), `url`, `description`을 가진다.
  - `GET /api/news/latest` → 200 `{"news_items": [...]}`. DB에서 `collected_at` 최신 실행분 중 `date` 내림차순 5개를 돌려준다.
  - `NaverAPIError` → 502 `{"detail": "<message>"}`

- [ ] **Step 1: 실패하는 테스트 작성**

`collect_top_news`를 monkeypatch해서 검증한다.
- `POST /api/news/collect` 성공 시 200이고 `news_items` 길이가 5 이하이며 각 항목에 다섯 필드가 있다.
- 파이프라인이 `NaverAPIError`를 던지면 502이고 `detail`에 메시지가 있다.
- `GET /api/news/latest`는 DB에 미리 넣은 행 중 최신 수집분 5개를 돌려준다.

- [ ] **Step 2: 실패 확인**

Run: `cd backend && pytest tests/test_news_api.py -v`
Expected: FAIL (라우터 없음)

- [ ] **Step 3: 구현**

라우터는 `request.app.state.session_factory()`로 세션을 얻고 `get_settings()`를 호출한다. 응답 직렬화는 함수 내부 dict 변환으로 한다. Pydantic 모델은 이번 단계에서 만들지 않는다(YAGNI). `main.py`에서 `app.include_router(news.router)`를 추가한다.

- [ ] **Step 4: 통과 확인**

Run: `cd backend && pytest tests/test_news_api.py tests/test_main.py -v`
Expected: PASS

- [ ] **Step 5: 커밋**

```bash
git add backend/app/api/ backend/app/main.py backend/tests/test_news_api.py
git commit -m "feat(backend): add news collect and latest endpoints"
```

---

### Task 8: 실제 네이버 호출 검증 (live)

**Files:**
- Create: `backend/tests/test_live_naver.py`

**Interfaces:**
- Consumes: `get_settings`, `collect_top_news` (Task 1, Task 6), `make_engine`, `init_db`, `make_session_factory` (Task 2)
- Produces: 없음 (검증 전용)

- [ ] **Step 1: 테스트 작성**

`@pytest.mark.live`를 붙이고 `RUN_LIVE=1` 환경 변수가 없으면 skip한다. 임시 DB에서 `collect_top_news`를 실행하고, 결과가 5개이며 각 항목의 `title`, `source`, `url`, `date`가 비어 있지 않은지 확인한다. `url`이 `http`로 시작하는지도 확인한다.

- [ ] **Step 2: 기본 실행에서 제외되는지 확인**

Run: `cd backend && pytest -v`
Expected: `test_live_naver`가 skip으로 나온다. 나머지는 모두 PASS.

- [ ] **Step 3: 실제 호출 실행 (사용자 키 필요)**

`backend/.env`에 `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`, `CLAUDE_API_KEY`를 넣은 뒤 실행한다.
Run: `cd backend && RUN_LIVE=1 pytest -m live -v -s`
Expected: PASS. 실패하면 상태 코드와 메시지를 그대로 보고한다. 401이면 키나 검색 API 사용 설정을, 429이면 일일 한도를 먼저 확인한다.

- [ ] **Step 4: 커밋**

```bash
git add backend/tests/test_live_naver.py
git commit -m "test(backend): add live naver news collection check"
```

---

## 완료 기준 (이슈 01·02 수락 기준 대응)

| 수락 기준 | 확인 방법 |
|---|---|
| `GET /health` 응답 (이슈 01) | Task 3 테스트, Step 5 수동 기동 |
| SQLite 스키마 3개 테이블 (이슈 01) | Task 2 테스트 |
| `.env` 로드, Claude·Naver 키 설정 (이슈 01) | Task 1 테스트 |
| 기본 폴더 구조 (이슈 01) | Task 1–7의 파일 배치 |
| 네이버 API 연동 (이슈 02) | Task 5 테스트 + Task 8 live |
| 경제·증권 Top 5 수집 (이슈 02) | Task 6 테스트 + Task 8 live |
| 제목, 언론사, 발행일, 링크 추출 (이슈 02) | Task 4, Task 6 테스트 |
| `news_items` 저장 (이슈 02) | Task 6 테스트 |
| 중복 제외 (이슈 02) | Task 6 테스트 |
| 실제 뉴스 5개 정상 동작 확인 (이슈 02) | Task 8 Step 3 |

## Out of Scope (이번 계획에서 하지 않는 것)

- Claude 요약, 시장 전망, 투자포인트 (이슈 03, 05)
- `POST /api/news/generate` 통합 엔드포인트 (이슈 04)
- 프론트엔드 연결 (이슈 06)
- 이메일 구독 (이슈 07)
- 의존성 버전 고정, `.gitignore` 수정, 추적 파일 정리 (별도 정리 작업)
- 제목 유사도 기반 중복 제거 (URL 기준으로 충분하다고 보고 보류)
