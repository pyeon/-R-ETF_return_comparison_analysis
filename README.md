# ETF 수익률 분석 시스템 (GitHub Actions)

운용금액 상위 100개 ETF의 수익률을 10개 기간별로 분석하여 자동으로 보고서를 생성합니다.

## 📊 주요 기능

### 분석 대상
- **선별 기준**: 운용금액 상위 100개 ETF
- **분류 기준**: 1년 수익률 기준 상위/하위 50개 + 미출시 종목

### 분석 지표
- **수익률 기간**: 1일, 3일, 1주, 2주, 1개월, 3개월, 6개월, 12개월, 3년, 5년
- **각 기간별 순위** 자동 계산

### 자동 분류
- **ETF 섹터**: 반도체, IT/테크, 2차전지, 바이오, 금융, 에너지, 부동산, 채권, 원자재, 자동차, 종합지수, 기타
- **국내외 구분**: 국내, 해외
- **레버리지**: 없음, 2배, 3배, 인버스
- **환헤지**: 해당없음(국내), 환헤지, 환노출
- **배당 유형**: 일반, 배당형, 성장형

## 🔄 자동화 워크플로우

```
1. API 데이터 수집 (pykrx)
   ↓
2. 수익률 계산 및 분류
   ↓
3. 데이터 저장
   - market_data/etf_performance_YYYYMMDD.json
   - analysis_reports/etf_performance_YYYYMMDD.xlsx
   - analysis_reports/etf_performance_YYYYMMDD.md
   ↓
4. Git Commit & Push
   ↓
5. Telegram 요약 전송 (TOP 5만)
```

## 📅 실행 일정

- **자동 실행**: 월~금 18:00 KST (장 마감 후)
- **수동 실행**: GitHub Actions 탭에서 `workflow_dispatch` 트리거

## 📁 디렉토리 구조

```
repository/
├── etf_performance_analyzer.py     # 메인 분석 스크립트
├── .github/
│   └── workflows/
│       └── etf_performance_analysis.yml
├── market_data/                    # JSON 원본 데이터
│   └── etf_performance_YYYYMMDD.json
└── analysis_reports/               # 분석 보고서
    ├── etf_performance_YYYYMMDD.xlsx
    └── etf_performance_YYYYMMDD.md
```

## ⚙️ 설정 방법

### 1. Repository Secrets 설정
GitHub Repository → Settings → Secrets and variables → Actions

```
TELEGRAM_TOKEN=your_telegram_bot_token
CHAT_ID=your_telegram_chat_id
```

### 2. Workflow 파일 배치
`.github/workflows/etf_performance_analysis.yml` 경로에 workflow 파일 배치

### 3. Permissions 확인
워크플로우 파일에 `permissions: contents: write` 포함 확인

## 📊 출력 데이터 형식

### JSON 형식
```json
{
  "analysis_date": "20241127",
  "total_etfs": 100,
  "etf_data": [
    {
      "종목명": "KODEX 200",
      "종목코드": "069500",
      "운용금액순위": 1,
      "운용금액_억": 125000.0,
      "ETF섹터": "종합지수",
      "국내외구분": "국내",
      "레버리지": "없음",
      "환헤지": "해당없음",
      "배당유형": "일반",
      "구분": "상위 50개",
      "1일_순위": 15,
      "1일_수익률": 1.25,
      "3일_순위": 20,
      "3일_수익률": 2.34,
      "1주_순위": 18,
      "1주_수익률": 3.45,
      ...
    }
  ]
}
```

### Excel 형식
- 시트명: "ETF 수익률 분석"
- 헤더 스타일: 파란색 배경, 흰색 글자
- 자동 컬럼 너비 조정

### Markdown 형식
- 1년 수익률 기준 TOP/BOTTOM 10
- 1주일 수익률 기준 TOP/BOTTOM 10
- 섹터별 통계

## 📱 Telegram 알림 예시

```
📊 ETF 수익률 분석 완료
📅 기준일: 20241127
📈 분석 대상: 100개 ETF

🔝 1년 수익률 TOP 5
1. KODEX 미국반도체MV
   💰 1년: 45.23% | 1주: 3.12%
2. TIGER 차이나전기차SOLACTIVE
   💰 1년: 38.45% | 1주: 2.89%
...

🔝 1주일 수익률 TOP 5
1. KODEX 2차전지산업
   💰 1주: 8.45% | 1년: 25.67%
...

✅ 상세 데이터: JSON, Excel, Markdown 저장됨
```

## 🔍 주요 특징

### 1. GitHub Actions 최적화
- ✅ API 데이터 수집 → 저장 → Git push 패턴
- ✅ Telegram은 요약만 전송 (파일 전송 제거)
- ✅ `permissions: contents: write` 명시

### 2. 실전 투자 활용
- ✅ 장 마감 후 자동 분석
- ✅ 다양한 기간별 수익률 비교
- ✅ ETF 특성별 자동 분류
- ✅ 운용금액 순위 정보 포함

### 3. 데이터 보존
- ✅ JSON: 원본 데이터 보존
- ✅ Excel: 상세 분석 가능
- ✅ Markdown: 빠른 요약 확인

## 📈 활용 사례

1. **수익률 비교**: 1일~5년까지 다양한 기간별 성과 비교
2. **섹터 분석**: 어떤 섹터가 강세/약세인지 파악
3. **레버리지 효과**: 레버리지 ETF vs 일반 ETF 비교
4. **환헤지 전략**: 환헤지/환노출 ETF 수익률 차이 분석
5. **트렌드 파악**: 단기(1주)/장기(1년) 수익률 괴리 확인

## 🚨 주의사항

- 월요일/일요일은 자동으로 분석 스킵
- 영업일이 아닌 경우 이전 영업일 기준으로 분석
- '미출시' 표시: 해당 기간 동안 상장되지 않은 ETF
- 운용금액은 추정치 (종가 × 거래량 기반)

## 📝 라이선스

MIT License

## 🤝 기여

이슈 및 PR 환영합니다!
