# 🚀 빠른 시작 가이드

## 📦 1단계: 파일 준비

### 옵션 A: ZIP 파일 사용 (추천)
```bash
# ZIP 파일 다운로드 후
unzip etf_analysis_project.zip
cd etf_analysis_project
```

### 옵션 B: 개별 파일 복사
프로젝트 폴더의 모든 파일을 새 repository에 복사

## ⚙️ 2단계: GitHub 설정

### 2-1. Repository 생성
1. GitHub에서 새 repository 생성
2. 로컬에서 초기화:
```bash
git init
git add .
git commit -m "Initial commit: ETF Performance Analyzer"
git branch -M main
git remote add origin https://github.com/your-username/your-repo.git
git push -u origin main
```

### 2-2. Secrets 설정

**Repository → Settings → Secrets and variables → Actions**

| Secret Name | Value | 설명 |
|-------------|-------|------|
| `TELEGRAM_TOKEN` | `1234567890:ABC...` | Telegram Bot Token |
| `CHAT_ID` | `123456789` | Telegram Chat ID |

#### Telegram 설정 방법:
1. [@BotFather](https://t.me/botfather)에서 `/newbot` 실행
2. Bot Token 복사
3. Bot에게 메시지 전송
4. `https://api.telegram.org/bot<TOKEN>/getUpdates` 접속
5. `chat.id` 확인

### 2-3. Workflow 권한 설정

**Repository → Settings → Actions → General**
- Workflow permissions: **"Read and write permissions"** 선택
- "Allow GitHub Actions to create and approve pull requests" 체크

## ✅ 3단계: 실행 확인

### 수동 실행 테스트
1. GitHub → Actions 탭
2. "ETF Performance Analysis" 선택
3. "Run workflow" 클릭
4. 5-10분 후 결과 확인

### 자동 실행
- 매일 월~금 18:00 KST 자동 실행
- `market_data/` 폴더에 JSON 생성
- `analysis_reports/` 폴더에 Excel, Markdown 생성
- Telegram 알림 수신

## 📊 4단계: 결과 확인

### GitHub에서
```bash
git pull origin main
ls -l market_data/
ls -l analysis_reports/
```

### Telegram에서
분석 완료 시 다음과 같은 메시지 수신:
```
📊 ETF 수익률 분석 완료
📅 기준일: 20241127
📈 분석 대상: 100개 ETF

🔝 1년 수익률 TOP 5
1. KODEX 미국반도체MV
   💰 1년: 45.23% | 1주: 3.12%
...
```

## 🔧 문제 해결

### "Permission denied" 에러
```yaml
# .github/workflows/etf_performance_analysis.yml에 추가
permissions:
  contents: write
```

### Telegram 메시지 안 옴
- Secrets 값 재확인
- Bot 차단 여부 확인
- Chat ID 정확성 확인

### 월요일/일요일에 실행 안 됨
- 정상 동작 (주말은 자동 스킵)

## 📚 더 알아보기

- 📖 [README.md](README.md) - 전체 기능 설명
- ⚙️ [SETUP.md](SETUP.md) - 상세 설정 가이드
- 🏗️ [STRUCTURE.md](STRUCTURE.md) - 폴더 구조 설명

## 🎯 체크리스트

- [ ] Repository 생성 완료
- [ ] 파일 업로드 완료
- [ ] TELEGRAM_TOKEN Secret 등록
- [ ] CHAT_ID Secret 등록
- [ ] Workflow 권한 설정
- [ ] 수동 실행 테스트 성공
- [ ] Telegram 알림 수신 확인
- [ ] 자동 실행 대기 (다음 평일 18:00)

모든 항목 체크 완료 시 설정 완료! 🎉
