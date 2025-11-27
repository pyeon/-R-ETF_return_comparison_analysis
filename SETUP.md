# 설정 가이드

## 1. Repository 생성

```bash
# GitHub에서 새 repository 생성 후
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

## 2. 파일 복사

이 프로젝트의 모든 파일을 복사합니다:

```
etf_analysis_project/
├── .github/
│   └── workflows/
│       └── etf_performance_analysis.yml
├── market_data/
│   └── README.md
├── analysis_reports/
│   └── README.md
├── etf_performance_analyzer.py
├── requirements.txt
├── .gitignore
├── README.md
└── SETUP.md (이 파일)
```

## 3. GitHub Secrets 설정

### 3.1 Telegram Bot 생성

1. Telegram에서 [@BotFather](https://t.me/botfather) 검색
2. `/newbot` 명령어로 새 봇 생성
3. Bot Token 복사 (예: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 3.2 Chat ID 확인

1. Bot과 대화 시작 (아무 메시지나 전송)
2. 브라우저에서 접속: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. `chat.id` 값 확인 (예: `123456789`)

### 3.3 GitHub Secrets 등록

Repository → Settings → Secrets and variables → Actions → New repository secret

| Name | Value |
|------|-------|
| `TELEGRAM_TOKEN` | 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz |
| `CHAT_ID` | 123456789 |

## 4. 첫 실행

### 4.1 Git Push

```bash
git add .
git commit -m "Initial commit: ETF Performance Analyzer"
git push origin main
```

### 4.2 수동 실행 테스트

1. GitHub Repository → Actions 탭
2. "ETF Performance Analysis" workflow 선택
3. "Run workflow" 버튼 클릭
4. 실행 결과 확인

### 4.3 자동 실행 확인

- 매일 월~금 18:00 KST에 자동 실행
- Actions 탭에서 실행 로그 확인 가능

## 5. 결과 확인

### 5.1 GitHub에서 확인

```bash
# 최신 데이터 pull
git pull origin main

# 저장된 파일 확인
ls -l market_data/
ls -l analysis_reports/
```

### 5.2 Telegram에서 확인

- 분석 완료 시 자동으로 요약 메시지 수신
- TOP 5 수익률 정보 포함

## 6. 로컬 실행 (선택사항)

```bash
# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 환경변수 설정
export TELEGRAM_TOKEN="your_token"
export CHAT_ID="your_chat_id"

# 실행
python etf_performance_analyzer.py
```

## 7. 문제 해결

### Workflow가 실행되지 않을 때

- Repository → Settings → Actions → General
- "Workflow permissions" → "Read and write permissions" 선택
- "Allow GitHub Actions to create and approve pull requests" 체크

### Permission 에러

```yaml
# workflow 파일에 다음이 있는지 확인
permissions:
  contents: write
```

### Telegram 메시지가 안 올 때

1. Secrets 값 재확인
2. Bot이 차단되지 않았는지 확인
3. Chat ID가 정확한지 확인

### 데이터가 저장되지 않을 때

1. 월요일/일요일은 자동 스킵됨
2. Actions 로그에서 에러 확인
3. 영업일인지 확인

## 8. 커스터마이징

### 실행 시간 변경

`.github/workflows/etf_performance_analysis.yml` 파일의 cron 수정:

```yaml
schedule:
  # 한국시간 17:00 (UTC 08:00)
  - cron: '0 8 * * 1-5'
```

### 분석 대상 변경

`etf_performance_analyzer.py` 파일의 다음 부분 수정:

```python
# 상위 100개 → 200개로 변경
etf_list = etf_list.head(200).copy()
```

### Telegram 메시지 형식 변경

`generate_telegram_summary()` 메서드 수정

## 9. 유지보수

### 정기 점검 사항

- [ ] Actions 실행 로그 확인 (월 1회)
- [ ] 저장 용량 확인 (분기 1회)
- [ ] pykrx API 변경사항 확인 (반기 1회)

### 데이터 정리 (선택)

```bash
# 오래된 데이터 삭제 (예: 1년 이상)
find market_data/ -name "*.json" -mtime +365 -delete
find analysis_reports/ -name "*.xlsx" -mtime +365 -delete
```

## 10. 추가 리소스

- [pykrx 문서](https://github.com/sharebook-kr/pykrx)
- [GitHub Actions 문서](https://docs.github.com/en/actions)
- [Telegram Bot API](https://core.telegram.org/bots/api)

## 문의

이슈가 있으면 GitHub Issues에 등록해주세요!
