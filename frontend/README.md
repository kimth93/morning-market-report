# 아침 시장 전망 프론트엔드

React 19 + TypeScript + Vite + Tailwind CSS v4 기반 화면입니다.

## 실행

```bash
npm install
npm run dev        # http://localhost:5173 (백엔드는 http://127.0.0.1:8000 가정)
npm test           # 단위 테스트 (vitest)
npm run e2e        # 브라우저 E2E (Playwright, API 모킹)
npm run build      # 타입 검사 + 빌드
npm run lint       # oxlint
```

백엔드 주소를 바꾸려면 `VITE_API_BASE` 환경 변수를 설정하세요.
