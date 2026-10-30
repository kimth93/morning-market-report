# 웹 UI (이슈 06) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (Native, 인라인) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** "지금 생성" 버튼 한 번으로 `POST /api/news/generate`를 호출해, 시장 전망·투자포인트·뉴스 5개(요약, 출처, 위험도)와 면책 고지를 디자인 시안대로 보여주는 React 화면을 완성한다.

**Architecture:** 기존 `frontend/`(Vite + React 19 + TypeScript + Tailwind)를 그대로 쓴다. 상태는 `App.tsx`에서 `idle → generating → done | error` 세 단계로 관리한다. API 호출은 `src/api/news.ts` 한 곳에 모으고, 화면은 섹션별 컴포넌트(Header, HeroSection, ResultsSection, TrustPrinciples, EmailSubscription, Footer)로 나눈다. 백엔드는 CORS만 열어 준다.

**Tech Stack:** React 19, TypeScript, Vite, Tailwind CSS v4, oxlint, vitest (API 클라이언트와 상태 로직 단위 테스트), Playwright MCP (브라우저 검증)

**Spec:** `PRD.md` (§2 웹 인터페이스, §4-4 면책 고지, §Testing "웹 UI 통합 테스트"), `.scratch/morning-market-report/issues/06-web-ui.md`, 디자인 시안 `아침 시장 전망 보고서.dc.html`, API 계약 `backend/app/api/news.py`

## Global Constraints

- 면책 고지 문구는 정확히 `투자는 본인의 판단으로 하시기 바랍니다` 이며, 페이지 상단에 항상 보인다 (PRD §4-4, 이슈 06).
- 위험도 표시는 `low | medium | high` 세 값만 쓴다.
- 응답 필드는 백엔드 명세를 그대로 쓴다: `news_items[]{title, source, date, url, summary, hallucination_risk}`, `market_outlook`, `investment_points[3]`, `generated_at`.
- 이메일 구독은 시각적 폼만 제공한다 (PRD §2, v2에서 실제 발송). 제출해도 서버에 보내지 않는다.
- 백엔드 주소는 `VITE_API_BASE` 환경 변수로 바꿀 수 있고, 기본값은 `http://127.0.0.1:8000`이다.
- 디자인 시안의 CSS 토큰 파일(`styles/colors_and_type.css`)과 `support.js`는 저장소에 없다. 시안에 실제로 쓰이는 CSS 변수만 `index.css`의 `@theme`로 옮긴다 (Decision 참고).

## Decisions (이 계획에서 정한 것)

- **디자인 시안은 목표 화면이지 런타임이 아니다.** `.dc.html`은 `x-dc` 템플릿 런타임(`support.js`)에 의존하므로 실행하지 않는다. 레이아웃, 문구, 색 역할만 React + Tailwind로 옮긴다.
- **토큰 누락 처리**: `colors_and_type.css`가 없으므로 시안 인라인 스타일에서 쓰인 `--color-*`, `--font-sans`, `--ease-decel` 값을 추출해 `index.css`에 둔다. 값을 정확히 맞추지 못하면 사용자가 원본 CSS를 `frontend/styles/`에 넣어 주면 교체한다.
- **진행 표시**: 백엔드는 진행률을 주지 않으므로 생성 중에는 단계 문구("뉴스 수집 중 → 요약 중 → 전망 작성 중")를 시간 기반으로 순환해서 보여주고, 실제 완료 시점에 결과로 바꾼다.
- **에러 상태**: 502 등 실패 시 `detail` 메시지를 보여주고 "다시 시도" 버튼을 둔다.
- **테스트 도구**: vitest를 devDependency로 추가한다. 버전은 2주 이상 된 안정 버전으로 고정한다. 브라우저 검증은 Playwright MCP로 한다.
- **CORS**: FastAPI `CORSMiddleware`로 `http://localhost:5173`과 `http://127.0.0.1:5173`만 허용한다.
- **타이머 버그 수정**: 기존 `App.tsx`의 `handleGenerate`가 cleanup을 반환하는 문제는 새 상태 로직으로 대체되어 사라진다.

## Review Focus

1. **백엔드가 느리거나 실패할 때 화면이 멈춘 것처럼 보임** → 생성 중 상태와 실패 메시지가 항상 보여야 한다. (Task 2, Task 4)
2. **같은 버튼을 두 번 눌러 요청이 겹침** → 생성 중에는 버튼이 비활성화되어야 한다. (Task 4)
3. **`investment_points`가 3개가 아니거나 빈 문자열** → 화면이 깨지지 않고 있는 만큼만 보여준다. (Task 5)
4. **`date`가 ISO 형식이라 날짜가 잘못 보임** → 날짜만 `YYYY-MM-DD`로 표시한다. (Task 5)
5. **원문 링크가 `javascript:` 등 위험한 주소** → 백엔드는 http(s)만 만든다는 전제를 두고, 화면은 `http(s)` 주소만 링크로 연다. (Task 5)
6. **좁은 화면(약 400px)에서 가로 스크롤 발생** → 카드와 헤더가 세로로 쌓인다. (Task 6)

---

### Task 1: 툴체인 정리 (Tailwind v4, 빌드 복구)

**Files:**
- Modify: `frontend/src/index.css` (v3 지시문 제거, `@import "tailwindcss"`와 `@theme` 추가)
- Modify: `frontend/src/components/Header.tsx` (`bg-opacity-86` 제거)
- Delete: `frontend/tailwind.config.js` (v4는 CSS 기반 설정 사용)
- Inspect: `frontend/postcss.config.js` (v3 플러그인이면 Tailwind v4 플러그인으로 교체)

**Interfaces:**
- Consumes: 없음
- Produces: `npm run build`가 성공하는 상태. `@theme`에 `--color-primary`, `--color-primary-hover`, `--color-primary-bg`, `--color-line`, `--color-label`, `--color-bg-alt` 등 디자인 토큰이 있다. (Task 3 이후 모든 컴포넌트가 사용)

- [ ] **Step 1: 현재 빌드 실패 확인**

Run: `cd frontend && npm run build`
Expected: 누락된 컴포넌트 import 오류로 실패 (Task 2~6에서 해결)

- [ ] **Step 2: Tailwind v4 설정으로 바꾸기**

`index.css`를 `@import "tailwindcss";`로 시작하게 하고 `@tailwind` 지시문을 지운다. `tailwind.config.js`의 색과 그림자를 `@theme { --color-primary: #0066FF; ... }`로 옮긴다. `postcss.config.js`는 `@tailwindcss/postcss` 플러그인 하나만 남긴다. 패키지에 `@tailwindcss/postcss`가 없으면 `npm install -D @tailwindcss/postcss@<4.3.2와 같은 minor>`로 추가한다.

- [ ] **Step 3: 잘못된 클래스 제거**

`Header.tsx`의 `bg-opacity-86`은 `bg-white/86`으로 바꾼다. 다른 v3 전용 유틸리티가 있으면 같은 방식으로 바꾼다.

- [ ] **Step 4: 빌드 확인 (컴포넌트 누락 오류만 남아야 함)**

Run: `cd frontend && npm run build`
Expected: Tailwind 관련 오류 없음. 남은 오류는 `App.tsx`의 누락 컴포넌트 import뿐이다.

- [ ] **Step 5: 커밋**

```bash
git add frontend/src/index.css frontend/src/components/Header.tsx frontend/postcss.config.js frontend/package.json frontend/package-lock.json
git rm -q frontend/tailwind.config.js
git commit -m "chore(frontend): move styling to tailwind v4 config"
```

---

### Task 2: 백엔드 CORS와 API 클라이언트

**Files:**
- Modify: `backend/app/main.py` (CORSMiddleware 추가)
- Test: `backend/tests/test_main.py` (CORS 헤더 테스트 추가)
- Create: `frontend/src/api/news.ts`
- Create: `frontend/src/api/news.test.ts`
- Modify: `frontend/package.json` (vitest 추가, `test` 스크립트)

**Interfaces:**
- Consumes: 백엔드 `POST /api/news/generate` 응답 (Global Constraints의 필드)
- Produces:
  - `types`: `export type Risk = "low" | "medium" | "high"`, `export interface NewsItem { title: string; source: string; date: string; url: string; summary: string; hallucination_risk: Risk }`, `export interface GenerateResponse { news_items: NewsItem[]; market_outlook: string; investment_points: string[]; generated_at: string }`
  - `generateNews(fetchImpl?: typeof fetch): Promise<GenerateResponse>`: 실패 시 `ApiError(message)`를 던진다. `message`는 백엔드 `detail`을 쓴다.
  - `API_BASE`: `import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000"`

- [ ] **Step 1: CORS 테스트 작성 (실패 확인)**

`test_main.py`에 `OPTIONS /api/news/generate`를 `Origin: http://localhost:5173`으로 보내서 `access-control-allow-origin` 헤더가 같은 값인지 검증한다. 다른 출처(`http://evil.example`)는 헤더가 없어야 한다.

Run: `cd backend && python3 -m pytest tests/test_main.py -q`
Expected: FAIL (헤더 없음)

- [ ] **Step 2: CORSMiddleware 추가 후 통과 확인**

`main.py`에서 `app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["GET", "POST"], allow_headers=["*"])`를 추가한다.

Run: `cd backend && python3 -m pytest tests/test_main.py -q`
Expected: PASS

- [ ] **Step 3: vitest 설치와 API 클라이언트 테스트 작성**

Run: `cd frontend && npm install -D vitest@<2주 이상 된 버전>` 후 `package.json`에 `"test": "vitest run"`을 추가한다.

`news.test.ts`: 가짜 `fetch`로 (a) 200 응답이 타입 그대로 반환되고 URL이 `${API_BASE}/api/news/generate`이며 메서드가 POST인지, (b) 502 응답이면 `ApiError`가 나고 메시지가 `detail`과 같은지, (c) 네트워크 실패면 `ApiError`가 나는지 확인한다.

Run: `cd frontend && npm test`
Expected: FAIL (모듈 없음)

- [ ] **Step 4: 구현 후 통과 확인**

`news.ts`에 위 Interfaces 그대로 구현한다. 실패 응답 본문은 JSON의 `detail`을 읽고, 읽을 수 없으면 `HTTP <status>`를 메시지로 쓴다.

Run: `cd frontend && npm test`
Expected: PASS (3 tests)

- [ ] **Step 5: 커밋**

```bash
git add backend/app/main.py backend/tests/test_main.py frontend/src/api frontend/package.json frontend/package-lock.json
git commit -m "feat: enable cors for local frontend and add news api client"
```

---

### Task 3: 디자인 토큰 옮기기와 Header, 면책 고지

**Files:**
- Modify: `frontend/src/index.css` (`@theme` 토큰 보강)
- Modify: `frontend/src/components/Header.tsx` (시안의 Header 구조)
- Create: `frontend/src/components/Disclaimer.tsx`

**Interfaces:**
- Consumes: Task 1의 `@theme` 토큰
- Produces: `Disclaimer(): JSX.Element` (고정 문구, props 없음). `Header(): JSX.Element` (props 없음)

- [ ] **Step 1: 토큰 추출**

시안 파일에서 `var(--color-...)`, `var(--font-sans)`, `var(--ease-decel)` 사용처를 모두 찾아 실제 값을 `index.css`의 `@theme`에 넣는다. 값을 찾을 수 없으면 Decision에 따라 사용자에게 원본 CSS를 요청하고, 그 전까지는 시안 화면 색을 근사한 값을 쓴다.

Run: `grep -o 'var(--[a-z-]*)' "아침 시장 전망 보고서.dc.html" | sort -u`
Expected: 사용하는 토큰 목록이 나온다.

- [ ] **Step 2: Disclaimer 구현**

`Disclaimer.tsx`는 `role="note"`인 상자에 `투자는 본인의 판단으로 하시기 바랍니다`를 넣고, 페이지 최상단(Header 바로 아래)에 둔다.

- [ ] **Step 3: Header 구현**

시안의 Header(로고 아이콘, "아침 시장 전망", "AI 시장 요약 · Daily Market Brief", 오른쪽 알림 버튼)를 옮긴다. 알림 버튼은 동작하지 않으므로 `aria-label="알림 (준비 중)"`과 `disabled`를 준다.

- [ ] **Step 4: 빌드와 린트 확인**

Run: `cd frontend && npm run build && npm run lint`
Expected: 이 Task에서 만든 파일에서는 오류 없음 (나머지 누락 컴포넌트는 Task 4~6에서 해결)

- [ ] **Step 5: 커밋**

```bash
git add frontend/src/index.css frontend/src/components/Header.tsx frontend/src/components/Disclaimer.tsx
git commit -m "feat(frontend): add design tokens, header and disclaimer"
```

---

### Task 4: HeroSection과 생성 상태 흐름

**Files:**
- Create: `frontend/src/components/HeroSection.tsx`
- Create: `frontend/src/state/generation.ts` (상태 전이 순수 함수)
- Test: `frontend/src/state/generation.test.ts`

**Interfaces:**
- Consumes: `generateNews`, `ApiError`, `GenerateResponse` (Task 2)
- Produces:
  - `generation.ts`: `type Phase = "idle" | "generating" | "done" | "error"`, `interface GenerationState { phase: Phase; result?: GenerateResponse; error?: string; stepIndex: number }`, `reducer(state, action)` with actions `start`, `stepTick`, `succeed(result)`, `fail(message)`, `reset`. `start`는 `phase === "generating"`이면 상태를 바꾸지 않는다 (Review Focus 2).
  - `HeroSection(props: { state: GenerationState; onGenerate(): void; onRetry(): void })`. 생성 중에는 버튼을 `disabled`로 두고 단계 문구를 보여준다.

- [ ] **Step 1: 리듀서 테스트 작성 (실패 확인)**

테스트: (a) `idle → start → generating`, (b) `generating` 상태에서 `start`를 다시 보내도 상태가 같다, (c) `succeed` 후 `done`과 `result`가 채워진다, (d) `fail` 후 `error`와 `error` 메시지가 채워진다, (e) `reset`이 `idle`로 돌린다.

Run: `cd frontend && npm test -- generation`
Expected: FAIL

- [ ] **Step 2: 리듀서 구현 후 통과 확인**

Run: `cd frontend && npm test -- generation`
Expected: PASS

- [ ] **Step 3: HeroSection 구현**

단계 문구는 `["뉴스를 수집하고 있습니다", "기사를 요약하고 있습니다", "시장 전망을 작성하고 있습니다"]`를 `stepIndex`에 따라 보여준다. 약 1.5초마다 `stepTick`을 보내는 타이머는 `App.tsx`에서 `generating` 동안만 돌리고, 언마운트 시 정리한다. 실패 시 `error` 메시지와 "다시 시도" 버튼을 보여준다.

- [ ] **Step 4: 커밋**

```bash
git add frontend/src/state frontend/src/components/HeroSection.tsx
git commit -m "feat(frontend): add generation state and hero section"
```

---

### Task 5: ResultsSection (전망, 투자포인트, 뉴스 카드)

**Files:**
- Create: `frontend/src/components/ResultsSection.tsx`
- Create: `frontend/src/components/RiskBadge.tsx`
- Create: `frontend/src/lib/format.ts`
- Test: `frontend/src/lib/format.test.ts`

**Interfaces:**
- Consumes: `GenerateResponse`, `NewsItem`, `Risk` (Task 2)
- Produces:
  - `format.ts`: `formatDate(isoDate: string): string` (→ `YYYY-MM-DD`), `safeHttpUrl(url: string): string | null` (`http:`/`https:`만 통과, 아니면 `null`)
  - `ResultsSection(props: { result: GenerateResponse })`: 시장 전망 문단 1개, 투자포인트 목록(최대 3개, 빈 항목 제외), 뉴스 카드 목록.
  - `RiskBadge(props: { level: Risk })`

- [ ] **Step 1: format 테스트 작성 (실패 확인)**

테스트: `formatDate("2026-07-08")`가 `2026-07-08`, `safeHttpUrl("javascript:alert(1)")`가 `null`, `safeHttpUrl("https://www.hankyung.com/a")`가 그대로 반환.

Run: `cd frontend && npm test -- format`
Expected: FAIL

- [ ] **Step 2: 구현 후 통과 확인**

Run: `cd frontend && npm test -- format`
Expected: PASS

- [ ] **Step 3: ResultsSection 구현**

- 시장 전망: 문단 한 개. 생성 시각은 `generated_at`을 로컬 시간으로 표시한다.
- 투자포인트: `investment_points.filter(Boolean).slice(0, 3)`을 목록으로 보여준다 (Review Focus 3).
- 뉴스 카드: 제목, 요약, `언론사 · 날짜 · 원문 링크(safeHttpUrl이 null이면 링크 없이 텍스트)`, 위험도 배지. 링크는 `target="_blank" rel="noopener noreferrer"`.
- 좁은 화면에서는 카드가 한 열로 쌓인다 (Review Focus 6).

- [ ] **Step 4: 커밋**

```bash
git add frontend/src/components/ResultsSection.tsx frontend/src/components/RiskBadge.tsx frontend/src/lib/format.ts frontend/src/lib/format.test.ts
git commit -m "feat(frontend): render outlook, investment points and news cards"
```

---

### Task 6: TrustPrinciples, EmailSubscription, Footer와 App 연결

**Files:**
- Create: `frontend/src/components/TrustPrinciples.tsx`
- Create: `frontend/src/components/EmailSubscription.tsx`
- Create: `frontend/src/components/Footer.tsx`
- Modify: `frontend/src/App.tsx` (fake 타이머와 가짜 구독 ID 제거, 상태 리듀서 연결)
- Modify: `frontend/src/index.css` (필요한 경우 반응형 보정)

**Interfaces:**
- Consumes: `reducer`, `GenerationState` (Task 4), `ResultsSection` (Task 5), `generateNews` (Task 2)
- Produces:
  - `TrustPrinciples()`: 시안의 신뢰 원칙 3~4개 카드(정적 문구).
  - `EmailSubscription()`: 이메일과 이름 입력 폼. 제출 시 `e.preventDefault()`만 하고 "구독 기능은 v2에서 제공됩니다" 안내를 보여준다. 서버 호출과 임의 ID 생성은 하지 않는다.
  - `Footer()`: 면책 고지 한 줄과 출처 안내(정적).
  - `App`: `useReducer(reducer, initialState)`로 상태를 관리하고, `phase === "generating"`일 때만 1.5초 간격 `stepTick` 타이머를 돌리며 `generateNews` 결과에 따라 `succeed`/`fail`을 보낸다.

- [ ] **Step 1: 컴포넌트 구현**

시안의 TrustPrinciples, EmailSubscription, Footer 문구를 그대로 옮긴다. 시안에 가짜 구독 ID나 타이머가 있으면 가져오지 않는다.

- [ ] **Step 2: App 연결**

`App.tsx`에서 기존 `setTimeout` 4개와 `handleGenerate`의 cleanup 반환을 모두 제거한다 (Review Focus 1, 2의 원인). 타이머는 `useEffect`에서 `phase === "generating"`일 때만 설정하고 cleanup으로 정리한다.

- [ ] **Step 3: 빌드와 린트, 단위 테스트**

Run: `cd frontend && npm run build && npm run lint && npm test`
Expected: 빌드 성공, 린트 오류 없음, 테스트 전부 통과

- [ ] **Step 4: 반응형 확인 (약 400px)**

Playwright MCP로 viewport를 400×800으로 바꿔 가로 스크롤이 생기지 않는지 확인한다.

- [ ] **Step 5: 커밋**

```bash
git add frontend/src
git commit -m "feat(frontend): wire generate flow and remaining sections"
```

---

### Task 7: 실제 브라우저 검증

**Files:**
- Create: `.scratch/morning-market-report/verification/` (스크린샷 저장, 커밋하지 않음)

**Interfaces:**
- Consumes: 백엔드 `uvicorn app.main:app --port 8000`, 프론트 `npm run dev`(5173)
- Produces: 검증 결과 기록

- [ ] **Step 1: 서버 기동**

백엔드(`cd backend && python3 -m uvicorn app.main:app --port 8000`)와 프론트(`cd frontend && npm run dev`)를 띄운다.

- [ ] **Step 2: 브라우저 시나리오 (Playwright MCP)**

1. `http://localhost:5173` 열기 → 면책 고지가 상단에 보이는지 확인
2. "지금 생성" 클릭 → 버튼이 비활성화되고 단계 문구가 바뀌는지 확인
3. 완료 후 시장 전망 1문단, 투자포인트 3개, 뉴스 카드 5개(제목, 요약, 언론사, 날짜, 링크, 위험도)가 보이는지 확인
4. 링크 하나 클릭 → 새 탭으로 열리는지 확인
5. 스크린샷 저장 (데스크톱 1280px, 모바일 400px)

- [ ] **Step 3: 실패 경로 확인**

백엔드를 끈 상태에서 "지금 생성" → 오류 메시지와 "다시 시도" 버튼이 보이는지 확인한 뒤 백엔드를 다시 켜고 재시도가 성공하는지 확인한다.

- [ ] **Step 4: 결과 기록**

각 시나리오의 통과 여부와 스크린샷 경로를 `.scratch/morning-market-report/verification/RESULT.md`에 적는다. 실패가 있으면 해당 Task로 돌아가 고친다.

---

## 완료 기준 (이슈 06 수락 기준 대응)

| 수락 기준 | 확인 |
|---|---|
| React 앱 초기 설정 | Task 1 빌드 성공 |
| "지금 생성" → `/api/news/generate` | Task 2 테스트, Task 7 Step 2 |
| 뉴스 5개 요약 표시 (제목, 요약) | Task 5, Task 7 Step 2-3 |
| 출처 명시 (언론사, 발행일, 원문 링크) | Task 5, Task 7 Step 2-4 |
| 위험도 표시 | Task 5 |
| 시장 전망 1문단 | Task 5 |
| 투자포인트 3개 | Task 5 |
| 면책 고지 상단 표시 | Task 3, Task 7 Step 2-1 |
| 기본 가독성 (반응형 선택) | Task 6 Step 4 |
| 실제 브라우저에서 "지금 생성" 동작 | Task 7 |

## Out of Scope

- 이메일 실제 발송, 구독 저장 (v2)
- 알림 버튼 동작
- 백엔드 진행률 스트리밍 (단계 문구는 시간 기반)
- 디자인 시안 전체의 세밀한 애니메이션 재현
- 과거 생성 결과 이력 조회
