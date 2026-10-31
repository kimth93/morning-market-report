# 운영 절차 (Netlify 정적 PoC)

사이트는 정적 파일만 제공하고, 보고서 생성과 발송은 개발자가 로컬에서 직접 실행합니다. 공개 사이트에는 유료 API 호출 경로가 없습니다.

## 1. 보고서 갱신 (필요할 때만, 생성 1회 약 $0.08)

```bash
cd backend
python3 -m app.cli.export_snapshot          # frontend/public/report.json 갱신
cd .. && git add frontend/public/report.json && git commit -m "chore: refresh sample report"
git push                                     # Netlify가 자동으로 다시 배포
```

- `source_note`와 `generated_at`이 화면에 표시되므로 예시 보고서임을 항상 알 수 있습니다.
- 갱신하지 않으면 마지막 생성본이 계속 보입니다.

## 2. 신청 확인과 승인

1. Netlify 대시보드 → Forms → `subscribe`에서 신청 내역을 확인합니다.
2. 신청 내역을 CSV로 내려받아 프로젝트 루트에 둡니다 (`submissions.csv`). 이 파일은 `.gitignore`에 있어 커밋되지 않습니다.
3. 승인할 주소만 `approved.txt`에 한 줄씩 적습니다. 주소 옆에 메모를 쓰려면 `#` 주석을 씁니다.
4. dry-run으로 발송 대상을 확인합니다.

```bash
cd backend
python3 -m app.cli.approve_and_send --csv ../submissions.csv --approved ../approved.txt
```

- 기본 실행은 메일을 보내지 않습니다. 대상 목록만 출력합니다.
- 동의(`consent`)하지 않았거나 승인 목록에 없는 주소는 제외됩니다.
- 실발송(`--send`)은 시연 시점에 본인 메일로 테스트한 뒤에만 사용합니다. 실발송 구현체가 연결되기 전까지는 `--send`를 주어도 중단됩니다.

## 3. 삭제 요청 처리

1. 삭제 요청을 받으면 Netlify 대시보드 → Forms → `subscribe`에서 해당 신청을 삭제합니다.
2. `submissions.csv`와 `approved.txt`에서도 같은 주소를 지웁니다.
3. 발송 기록(`backend/outbox/sent-log.json`)이 있다면 그 주소도 지웁니다.
4. 처리 결과는 요청자에게 답장으로 알립니다. 문의 창구는 "개발자에게 문의"로 표시되어 있습니다.

## 4. 비용 확인

- Netlify 대시보드에서 대역폭과 Forms 사용량을 주기적으로 확인합니다.
- 공개 사이트는 서버 함수를 쓰지 않으므로 함수 실행 시간은 0입니다.
- 비용 알림 설정이 없다면 켜 둡니다. 한도가 가까워지면 Forms를 잠그거나 사이트를 정지합니다.

## 5. 금지 사항

- 공개 사이트에 Claude나 네이버 호출 코드를 넣지 않습니다.
- `submissions.csv`, `approved.txt`, `outbox/`를 커밋하지 않습니다.
- 승인되지 않은 주소에 발송하지 않습니다.
