# Netlify PoC 배포 계획

**목적:** 포트폴리오용 PoC를 일부 사람에게 정상 동작으로 보여준다.
**절대 조건:** 비용이 발생하지 않는다. 외부 유료 API를 공개 사이트에서 호출하지 않는다.

## 1. 전제와 조사 결과

| 항목 | 확인 결과 | 출처 |
|---|---|---|
| Netlify Functions 동기 실행 제한 | 최대 10초 → 생성(약 50초)을 서버에서 돌릴 수 없음 | [Functions 소개](https://main--www.netlify.com/products/functions) |
| 백그라운드 함수 무료 여부 | 미확인 (2020년 발표는 Pro 이상) | [백그라운드 함수 문서](https://docs.netlify.com/build/functions/background-functions/) |
| Python 함수 지원 | 공식 근거 없음, 커뮤니티 답변은 미지원 | [커뮤니티 답변](https://answers.netlify.com/t/python-lambda-functions/3423) |
| Netlify Forms 한도 | 자료마다 다름 (월 100건 vs 무제한). 공식 가격표 확인 필요 | [Forms 한도](https://splitforms.com/blog/netlify-forms-limits), [2026 플랜](https://netli.fyi/blog/netlify-pricing-and-limits) |

**결론:** 공개 사이트는 **정적 사이트**로만 만든다. 백엔드(FastAPI)는 배포하지 않는다. 보고서는 개발자가 로컬에서 만들어 정적 파일로 올리고, 구독 신청은 Netlify Forms로 받는다.

## 2. 구조

```
[로컬 개발자 PC]                       [Netlify (정적)]
 FastAPI + Claude + Naver               Vite 빌드 결과(dist)
   │  export_snapshot (수동 실행)          ├ report.json (마지막 생성본)
   └─► frontend/public/report.json ──────►├ 화면 (생성 버튼 없음, 보고서 보기)
                                          └ 구독 폼 → Netlify Forms
                                                 │
                                   [관리자: Netlify 대시보드에서 신청 확인]
                                                 │ 승인 목록 export (CSV)
                                   [로컬 CLI] approve_and_send
                                     기본 dry-run, 승인된 주소만 대상
```

- **생성은 로컬에서만**: 공개 사이트에 Claude 호출 경로가 없으므로 비용이 생기지 않는다.
- **Netlify Functions 미사용**: 서버 코드가 없으므로 함수 실행 비용도 없다.
- **발송은 승인 후 수동 실행**: 자동 스케줄러 없음. 승인된 주소에만 보낸다.

## 3. 결정 필요

1. **Netlify 무료 플랜 확인**: 계정 생성 후 Forms 한도와 크레딧 정책을 가격 페이지에서 확인. 한도가 낮으면 신청을 사이트 밖(예: 이메일 링크)으로 받는 방법을 검토.
2. **보고서 갱신 주기**: 공개 전 한 번 생성할지, 주 1회 수동 갱신할지. 생성 1회 약 $0.08 (라이브 실측 기준). 갱신할 때마다 비용이 생긴다.
3. **발송 범위**: PoC에서는 **dry-run 로그까지만**(실제 메일은 보내지 않음) 할지, 본인 주소 한 통 등 제한된 실발송까지 할지. 실발송은 발신 도메인과 제공자가 필요하고, 제공자 무료 한도 확인 후 결정.
4. **개인정보 처리**: 신청 내역(이메일, 이름)은 Netlify에 저장된다. 아래 5번의 안내 문구와 삭제 절차를 적용.

## 4. 작업 목록

### Task 1: 보고서 스냅샷 내보내기 (백엔드, 로컬 전용)

- Create: `backend/app/cli/export_snapshot.py`
- 기능: `generate_report()`(기존 생성 파이프라인) 결과를 `frontend/public/report.json`으로 저장. `generated_at`, `source_note`("개발자가 생성한 예시 보고서") 포함.
- 테스트: 가짜 생성 결과로 JSON 구조와 필드 확인, 파일이 `public/`에 쓰이는지 확인.
- 실행은 개발자가 수동으로만 한다.

### Task 2: 정적 모드 화면 (프론트)

- Modify: `frontend/src/App.tsx`
  - 시작 시 `/report.json`을 읽어 결과 화면을 바로 보여준다.
  - "지금 생성하기" 버튼은 제거하고, 대신 "생성 시각: …, 예시 보고서입니다" 문구를 보여준다.
- Modify: `frontend/src/api/news.ts`: `loadSnapshot(fetchImpl)` 추가. 실패하면 "보고서를 불러오지 못했습니다" 표시.
- 테스트: 단위 테스트(스냅샷 로드, 실패 처리), E2E(페이지 로드 시 뉴스 5개 표시, 생성 버튼 없음).

### Task 3: 구독 신청 (Netlify Forms)

- Modify: `frontend/src/components/EmailSubscription.tsx`
  - 제출 대상을 백엔드에서 Netlify Forms로 바꾼다. 필드: `name`, `email`, `consent`(체크박스, 필수).
  - 성공 문구: "신청이 접수되었습니다. 관리자 승인 후 발송됩니다. (현재는 PoC입니다)"
  - 백엔드 구독 엔드포인트는 로컬 개발용으로만 유지.
- Modify: `frontend/index.html`: Netlify가 폼을 감지하도록 숨은 정적 폼 정의 (빌드 시 SPA 폼과 필드명이 같아야 함).
- 테스트: E2E에서 폼 필드와 동의 체크 필수 여부 확인. 실제 제출은 배포 후 Netlify 대시보드에서 확인.

### Task 4: 개인정보 처리 방침과 안내

- Create: `frontend/src/components/PrivacyNotice.tsx` (또는 정적 페이지 `privacy.html`)
  - 수집 항목(이메일, 이름), 목적(PoC 신청 확인과 승인 후 발송), 보관 기간, 삭제 요청 방법(이메일 주소로 요청)
  - 신청 전 동의 체크박스에 링크
- 문구는 실제 연락처가 생기면 채운다. 연락처가 없으면 "개발자에게 문의" 형태로 둔다.

### Task 5: 승인과 발송 도구 (로컬 CLI)

- Create: `backend/app/cli/approve_and_send.py`
  - 입력: Netlify 대시보드에서 내려받은 신청 CSV, 승인 목록 파일(`approved.txt`)
  - 동작: 승인 목록에 있는 주소만 대상으로 한다. 기본값은 dry-run이며 로그만 남긴다.
  - `--send` 플래그를 줘야만 실제 발송 함수(`MailSender`)를 호출한다. 실발송 구현체는 결정 3번 이후에 추가.
  - 같은 날 같은 주소에 두 번 보내지 않도록 `EmailDelivery` 이력을 쓴다(v2 계획과 같은 규칙).
- 테스트: 승인되지 않은 주소는 제외, dry-run은 발송 호출 0회, 중복 발송 방지, 동의하지 않은 신청 제외.

### Task 6: Netlify 설정 (배포 구성)

- Create: `netlify.toml`
  - `base = "frontend"`, `command = "npm run build"`, `publish = "dist"`
  - 함수 디렉터리 없음 (Functions 미사용)
- 환경 변수: 없음 (백엔드 주소를 쓰지 않음). `VITE_API_BASE`는 정적 모드에서 사용하지 않는다.
- 검증: 빌드 로그에서 Functions 빌드 단계가 없는지 확인.

### Task 7: 배포와 비용 확인 (사용자 계정 필요)

- 사용자가 Netlify 계정을 만들고 GitHub 저장소를 연결한다. (무료 플랜 선택)
- 가격 페이지에서 Forms 한도와 크레딧 정책 확인, 사용량 알림 설정 확인.
- 배포 후 Playwright로 배포 주소를 열어 확인: 보고서 표시, 신청 제출, 모바일 레이아웃.
- Netlify 대시보드에서 Functions, Forms, 대역폭 사용량이 기대한 수준인지 확인.

### Task 8: 운영 절차 문서

- `.scratch/morning-market-report/ops-runbook.md`
  - 보고서 갱신 절차 (로컬 생성 → export → 커밋 → 배포)
  - 신청 확인과 승인 절차 (대시보드 → CSV → 승인 목록 → dry-run → 실발송)
  - 삭제 요청 처리 절차

## 5. 비용 안전장치

- 공개 사이트에는 외부 유료 API 호출 코드가 없다. 빌드 결과에 Claude나 네이버 호출이 들어가지 않는지 `grep`으로 확인한다.
- 생성은 로컬에서만 한다. 갱신 횟수는 결정 2번에 따른다.
- Netlify에서 Functions를 쓰지 않으므로 함수 실행 시간은 0이다.
- 사용량 알림을 켜고, 한도에 가까워지면 Forms를 잠그거나 대시보드에서 확인한다.

## 6. 완료 기준

| 기준 | 확인 |
|---|---|
| 공개 URL에서 보고서가 정상 표시 | Task 7 Playwright |
| "지금 생성" 같은 유료 호출 경로가 없음 | Task 2 테스트 + 빌드 결과 grep |
| 신청이 Netlify에 접수됨 | Task 3, 대시보드에서 확인 |
| 동의하지 않으면 신청이 안 됨 | Task 3 E2E |
| 승인된 주소에만 발송 대상 포함 | Task 5 테스트 |
| 기본값은 실발송 없음 (dry-run) | Task 5 테스트 |
| 신청 내역 삭제 절차가 문서화됨 | Task 8 |
| 배포 후 비용 발생 없음 | Task 7 대시보드 확인 |
