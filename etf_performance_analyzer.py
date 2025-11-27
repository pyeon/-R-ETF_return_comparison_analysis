"""
ETF 수익률 비교 분석 시스템 (GitHub Actions 최적화)
- 운용금액 상위 100개 ETF 중 1년 수익률 기준 상위/하위 50개 분석
- 10개 기간별 수익률 및 순위 계산
- 자동 분류: 섹터, 국내외, 레버리지, 환헤지, 배당유형
- 데이터 저장: JSON, Excel, Markdown → Git push → Telegram 요약 전송
"""

import pandas as pd
import numpy as np
from pykrx import stock
from datetime import datetime, timedelta
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import requests
from typing import Dict, Tuple, List
import warnings
import os
import json
warnings.filterwarnings('ignore')


class ETFPerformanceAnalyzer:
    """ETF 수익률 분석기 (GitHub Actions 호환)"""
    
    def __init__(self, telegram_token: str = None, chat_id: str = None):
        """
        초기화
        
        Args:
            telegram_token: 텔레그램 봇 토큰 (환경변수에서 자동 로드 가능)
            chat_id: 텔레그램 채팅방 ID (환경변수에서 자동 로드 가능)
        """
        self.telegram_token = telegram_token or os.getenv('TELEGRAM_TOKEN')
        self.chat_id = chat_id or os.getenv('CHAT_ID')
        self.base_date = None
        
        # 디렉토리 생성
        os.makedirs('market_data', exist_ok=True)
        os.makedirs('analysis_reports', exist_ok=True)
    
    def get_last_trading_day(self) -> str:
        """마지막 영업일 가져오기 (전일 마감 기준)"""
        today = datetime.now()
        
        # 월요일/일요일은 작업 안함
        if today.weekday() in [0, 6]:
            return None
        
        if today.weekday() == 0:  # 월요일
            last_day = today - timedelta(days=3)
        elif today.weekday() == 6:  # 일요일
            last_day = today - timedelta(days=2)
        else:
            last_day = today - timedelta(days=1)
        
        date_str = last_day.strftime('%Y%m%d')
        try:
            test = stock.get_index_ohlcv(date_str, date_str, "1001")
            if len(test) == 0:
                return self.get_previous_trading_day(last_day)
            return date_str
        except:
            return self.get_previous_trading_day(last_day)
    
    def get_previous_trading_day(self, from_date: datetime) -> str:
        """이전 영업일 찾기"""
        for i in range(1, 10):
            test_date = from_date - timedelta(days=i)
            date_str = test_date.strftime('%Y%m%d')
            try:
                test = stock.get_index_ohlcv(date_str, date_str, "1001")
                if len(test) > 0:
                    return date_str
            except:
                continue
        return (datetime.now() - timedelta(days=5)).strftime('%Y%m%d')
    
    def get_date_before_period(self, base_date: str, days: int) -> str:
        """특정 기간 전 날짜 계산"""
        base = datetime.strptime(base_date, '%Y%m%d')
        target = base - timedelta(days=days)
        return target.strftime('%Y%m%d')
    
    def classify_etf(self, name: str, code: str) -> Dict[str, str]:
        """
        ETF 특성 자동 분류
        
        분류 항목:
        - ETF섹터: 반도체, IT/테크, 2차전지, 바이오, 금융, 에너지, 부동산, 채권, 원자재, 자동차, 종합지수, 기타
        - 국내외구분: 국내, 해외
        - 레버리지: 없음, 2배, 3배, 인버스
        - 환헤지: 해당없음(국내), 환헤지, 환노출
        - 배당유형: 일반, 배당형, 성장형
        """
        classification = {
            '국내외구분': '국내',
            '레버리지': '없음',
            '환헤지': '해당없음',
            '배당유형': '일반',
            'ETF섹터': '기타'
        }
        
        # 국내/해외 구분
        overseas_keywords = ['미국', 'S&P', 'NASDAQ', 'SPY', '나스닥', '중국', '일본', 
                            '유럽', '글로벌', 'MSCI', '선진국', '이머징', '베트남', 
                            '인도', 'USA', 'China', 'Japan', 'Europe']
        if any(keyword in name for keyword in overseas_keywords):
            classification['국내외구분'] = '해외'
        
        # 레버리지 구분
        if 'LEVERAGE' in name or '레버리지' in name:
            if '2X' in name or '2배' in name:
                classification['레버리지'] = '2배'
            elif '3X' in name or '3배' in name:
                classification['레버리지'] = '3배'
            else:
                classification['레버리지'] = '2배'
        elif 'INVERSE' in name or '인버스' in name or '곱버스' in name or 'Short' in name:
            classification['레버리지'] = '인버스'
        
        # 환헤지 구분 (해외 ETF만)
        if classification['국내외구분'] == '해외':
            if '환헤지' in name or '(H)' in name or 'Hedged' in name:
                classification['환헤지'] = '환헤지'
            else:
                classification['환헤지'] = '환노출'
        
        # 배당 유형
        if '배당' in name or 'DIV' in name or 'Dividend' in name or '고배당' in name:
            classification['배당유형'] = '배당형'
        elif '성장' in name or 'Growth' in name:
            classification['배당유형'] = '성장형'
        
        # ETF 섹터 분류
        sector_keywords = {
            '반도체': ['반도체', '칩', 'Chip', 'Semi', '필라델피아', 'SOX'],
            'IT/테크': ['IT', '인터넷', '테크', 'Tech', 'Technology', 'Internet', 
                      '소프트웨어', 'Cloud', 'Cyber', 'Software'],
            '2차전지': ['2차전지', '배터리', 'Battery', '전기차'],
            '바이오': ['바이오', 'Bio', '제약', 'Pharma', '헬스케어', 'Healthcare', 'Health'],
            '금융': ['금융', '은행', 'Bank', 'Finance', 'Financial'],
            '에너지': ['에너지', 'Energy', '원유', 'Oil', 'Gas'],
            '부동산': ['리츠', 'REIT', '부동산', 'Real Estate'],
            '채권': ['채권', 'Bond', '국채', '회사채', 'Treasury', 'TLT'],
            '원자재': ['금', 'Gold', '은', 'Silver', '원자재', 'Commodity'],
            '자동차': ['자동차', 'Auto', 'Car', 'Mobility', 'Vehicle'],
            '종합지수': ['KOSPI', 'KOSDAQ', 'KRX', 'S&P500', 'NASDAQ100', 'Russell', 'Dow', 'QQQ']
        }
        
        for sector, keywords in sector_keywords.items():
            if any(keyword in name for keyword in keywords):
                classification['ETF섹터'] = sector
                break
        
        return classification
    
    def get_all_etf_list(self) -> pd.DataFrame:
        """전체 ETF 목록 가져오기"""
        try:
            date_str = self.base_date
            etf_list = stock.get_etf_ticker_list(date_str)
            
            etf_data = []
            for ticker in etf_list:
                try:
                    name = stock.get_etf_ticker_name(ticker)
                    ohlcv = stock.get_etf_ohlcv_by_date(date_str, date_str, ticker)
                    
                    if len(ohlcv) > 0:
                        etf_data.append({
                            '종목코드': ticker,
                            '종목명': name,
                            '현재가': ohlcv['종가'].values[0]
                        })
                except:
                    continue
            
            return pd.DataFrame(etf_data)
            
        except Exception as e:
            print(f"Error in get_all_etf_list: {e}")
            return pd.DataFrame()
    
    def calculate_returns(self, ticker: str, base_date: str) -> Dict[str, float]:
        """
        기간별 수익률 계산
        
        계산 기간: 1일, 3일, 1주, 2주, 1개월, 3개월, 6개월, 12개월, 3년, 5년
        수익률 = (현재가 - 과거가) / 과거가 * 100
        """
        returns = {}
        periods = {
            '1일': 1, '3일': 3, '1주': 7, '2주': 14, '1개월': 30,
            '3개월': 90, '6개월': 180, '12개월': 365, '3년': 365*3, '5년': 365*5
        }
        
        try:
            start_date = self.get_date_before_period(base_date, 365 * 6)
            df = stock.get_etf_ohlcv_by_date(start_date, base_date, ticker)
            
            if len(df) == 0:
                return {period: '미출시' for period in periods.keys()}
            
            listing_date = df.index[0]
            base_dt = pd.to_datetime(base_date)
            
            for period_name, days in periods.items():
                try:
                    target_date = base_dt - pd.Timedelta(days=days)
                    
                    if target_date < listing_date:
                        returns[period_name] = '미출시'
                        continue
                    
                    base_price = df.loc[base_date, '종가']
                    available_dates = df.index[df.index <= target_date]
                    
                    if len(available_dates) == 0:
                        returns[period_name] = '미출시'
                        continue
                    
                    target_actual_date = available_dates[-1]
                    target_price = df.loc[target_actual_date, '종가']
                    
                    ret = ((base_price - target_price) / target_price) * 100
                    returns[period_name] = round(ret, 2)
                    
                except:
                    returns[period_name] = '미출시'
                    
        except:
            returns = {period: '미출시' for period in periods.keys()}
        
        return returns
    
    def get_etf_nav(self, ticker: str, date: str) -> float:
        """
        ETF 운용금액 추정
        
        계산 방식: 종가 × 거래량 / 100,000 (억원 단위)
        실제 순자산은 아니지만 거래규모의 proxy로 사용
        """
        try:
            ohlcv = stock.get_etf_ohlcv_by_date(date, date, ticker)
            if len(ohlcv) > 0:
                price = ohlcv['종가'].values[0]
                volume = ohlcv['거래량'].values[0]
                market_cap = price * volume / 100000
                return market_cap
            return 0
        except:
            return 0
    
    def analyze_etfs(self) -> pd.DataFrame:
        """
        전체 ETF 분석 수행
        
        프로세스:
        1. 마지막 영업일 확인
        2. 전체 ETF 목록 가져오기
        3. 운용금액 기준 상위 100개 선별
        4. 각 ETF별 10개 기간 수익률 계산
        5. 각 기간별 순위 계산
        6. 1년 수익률 기준 상위/하위 50개 구분
        """
        print("=" * 60)
        print("ETF 수익률 분석 시작")
        print("=" * 60)
        
        self.base_date = self.get_last_trading_day()
        
        if self.base_date is None:
            print("⚠️  오늘은 분석 작업일이 아닙니다 (월요일/일요일)")
            return None
        
        print(f"\n📅 기준일: {self.base_date}")
        
        print("\n1단계: ETF 목록 가져오는 중...")
        etf_list = self.get_all_etf_list()
        print(f"   ✓ 총 {len(etf_list)}개 ETF 발견")
        
        print("\n2단계: 운용금액 계산 및 정렬 중...")
        etf_list['운용금액_억'] = etf_list['종목코드'].apply(
            lambda x: self.get_etf_nav(x, self.base_date)
        )
        etf_list = etf_list.sort_values('운용금액_억', ascending=False)
        etf_list['운용금액순위'] = range(1, len(etf_list) + 1)
        etf_list = etf_list.head(100).copy()
        print(f"   ✓ 상위 100개 ETF 선별 완료")
        
        print("\n3단계: 수익률 계산 중 (5-10분 소요)...")
        all_results = []
        
        for idx, (i, row) in enumerate(etf_list.iterrows(), 1):
            ticker = row['종목코드']
            name = row['종목명']
            
            if idx % 10 == 0:
                print(f"   진행률: {idx}/100 ({idx}%)")
            
            returns = self.calculate_returns(ticker, self.base_date)
            classification = self.classify_etf(name, ticker)
            
            result = {
                '종목명': name,
                '종목코드': ticker,
                '운용금액순위': row['운용금액순위'],
                '운용금액_억': round(row['운용금액_억'], 0),
                **classification,
            }
            
            for period in ['1일', '3일', '1주', '2주', '1개월', '3개월', 
                          '6개월', '12개월', '3년', '5년']:
                result[f'{period}_수익률'] = returns[period]
            
            all_results.append(result)
        
        df = pd.DataFrame(all_results)
        
        print("\n4단계: 순위 계산 중...")
        for period in ['1일', '3일', '1주', '2주', '1개월', '3개월', 
                      '6개월', '12개월', '3년', '5년']:
            col = f'{period}_수익률'
            rank_col = f'{period}_순위'
            
            valid_mask = df[col] != '미출시'
            df.loc[valid_mask, rank_col] = df.loc[valid_mask, col].rank(
                ascending=False, method='min').astype(int)
            df.loc[~valid_mask, rank_col] = '미출시'
        
        print("\n5단계: 상위/하위 50개 구분 중...")
        valid_12month = df['12개월_수익률'] != '미출시'
        df_valid = df[valid_12month].copy()
        df_invalid = df[~valid_12month].copy()
        
        df_valid = df_valid.sort_values('12개월_수익률', ascending=False)
        
        top_50 = df_valid.head(50).copy()
        top_50['구분'] = '상위 50개'
        
        bottom_50 = df_valid.tail(50).copy()
        bottom_50['구분'] = '하위 50개'
        
        df_invalid['구분'] = '미출시(1년)'
        
        final_df = pd.concat([top_50, bottom_50, df_invalid], ignore_index=True)
        
        # 컬럼 순서 정리
        column_order = ['종목명', '종목코드', '운용금액순위', '운용금액_억',
                       'ETF섹터', '국내외구분', '레버리지', '환헤지', '배당유형', '구분']
        
        for period in ['1일', '3일', '1주', '2주', '1개월', '3개월', 
                      '6개월', '12개월', '3년', '5년']:
            column_order.extend([f'{period}_순위', f'{period}_수익률'])
        
        final_df = final_df[column_order]
        
        print("   ✓ 분석 완료!")
        return final_df
    
    def save_to_json(self, df: pd.DataFrame) -> str:
        """JSON 파일로 저장"""
        filename = f"market_data/etf_performance_{self.base_date}.json"
        
        # DataFrame을 딕셔너리로 변환 (NaN 처리)
        data = {
            'analysis_date': self.base_date,
            'total_etfs': len(df),
            'etf_data': df.to_dict('records')
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"   ✓ JSON 저장: {filename}")
        return filename
    
    def save_to_excel(self, df: pd.DataFrame) -> str:
        """
        엑셀 파일 생성
        
        스타일:
        - 헤더: 파란색 배경, 흰색 글자, 가운데 정렬
        - 데이터: 테두리, 자동 컬럼 너비
        """
        filename = f"analysis_reports/etf_performance_{self.base_date}.xlsx"
        
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='ETF 수익률 분석', index=False)
            
            workbook = writer.book
            worksheet = writer.sheets['ETF 수익률 분석']
            
            # 헤더 스타일
            header_fill = PatternFill(start_color='366092', end_color='366092', 
                                     fill_type='solid')
            header_font = Font(bold=True, color='FFFFFF', size=11)
            
            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # 컬럼 너비
            worksheet.column_dimensions['A'].width = 35  # 종목명
            worksheet.column_dimensions['B'].width = 12  # 종목코드
            worksheet.column_dimensions['C'].width = 15  # 운용금액순위
            worksheet.column_dimensions['D'].width = 15  # 운용금액
            worksheet.column_dimensions['E'].width = 15  # ETF섹터
            worksheet.column_dimensions['F'].width = 12  # 국내외구분
            worksheet.column_dimensions['G'].width = 12  # 레버리지
            worksheet.column_dimensions['H'].width = 12  # 환헤지
            worksheet.column_dimensions['I'].width = 12  # 배당유형
            worksheet.column_dimensions['J'].width = 15  # 구분
            
            for col in list(worksheet.columns)[10:]:
                worksheet.column_dimensions[col[0].column_letter].width = 12
        
        print(f"   ✓ Excel 저장: {filename}")
        return filename
    
    def save_to_markdown(self, df: pd.DataFrame) -> str:
        """마크다운 요약 보고서 생성"""
        filename = f"analysis_reports/etf_performance_{self.base_date}.md"
        
        # 1년 기준 정렬
        df_1y = df[df['12개월_수익률'] != '미출시'].copy()
        df_1y = df_1y.sort_values('12개월_수익률', ascending=False)
        
        # 1주일 기준 정렬
        df_1w = df[df['1주_수익률'] != '미출시'].copy()
        df_1w = df_1w.sort_values('1주_수익률', ascending=False)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# ETF 수익률 분석 보고서\n\n")
            f.write(f"**분석 기준일**: {self.base_date}\n\n")
            f.write(f"**분석 대상**: {len(df)}개 ETF (운용금액 상위 100개)\n\n")
            f.write("---\n\n")
            
            # 1년 기준 TOP 10
            f.write("## 📈 1년 수익률 기준\n\n")
            f.write("### 🔝 상위 10개\n\n")
            f.write("| 순위 | 종목명 | 종목코드 | 1년 수익률 | 1주 수익률 | ETF섹터 | 국내외 |\n")
            f.write("|------|--------|----------|-----------|-----------|---------|--------|\n")
            
            for idx, row in df_1y.head(10).iterrows():
                f.write(f"| {int(row['12개월_순위'])} | {row['종목명']} | {row['종목코드']} | "
                       f"{row['12개월_수익률']}% | {row['1주_수익률']}% | "
                       f"{row['ETF섹터']} | {row['국내외구분']} |\n")
            
            f.write("\n### 🔻 하위 10개\n\n")
            f.write("| 순위 | 종목명 | 종목코드 | 1년 수익률 | 1주 수익률 | ETF섹터 | 국내외 |\n")
            f.write("|------|--------|----------|-----------|-----------|---------|--------|\n")
            
            for idx, row in df_1y.tail(10).iterrows():
                f.write(f"| {int(row['12개월_순위'])} | {row['종목명']} | {row['종목코드']} | "
                       f"{row['12개월_수익률']}% | {row['1주_수익률']}% | "
                       f"{row['ETF섹터']} | {row['국내외구분']} |\n")
            
            # 1주일 기준 TOP 10
            f.write("\n---\n\n")
            f.write("## 📊 1주일 수익률 기준\n\n")
            f.write("### 🔝 상위 10개\n\n")
            f.write("| 순위 | 종목명 | 종목코드 | 1주 수익률 | 1년 수익률 | ETF섹터 | 국내외 |\n")
            f.write("|------|--------|----------|-----------|-----------|---------|--------|\n")
            
            for idx, row in df_1w.head(10).iterrows():
                f.write(f"| {int(row['1주_순위'])} | {row['종목명']} | {row['종목코드']} | "
                       f"{row['1주_수익률']}% | {row['12개월_수익률']}% | "
                       f"{row['ETF섹터']} | {row['국내외구분']} |\n")
            
            f.write("\n### 🔻 하위 10개\n\n")
            f.write("| 순위 | 종목명 | 종목코드 | 1주 수익률 | 1년 수익률 | ETF섹터 | 국내외 |\n")
            f.write("|------|--------|----------|-----------|-----------|---------|--------|\n")
            
            for idx, row in df_1w.tail(10).iterrows():
                f.write(f"| {int(row['1주_순위'])} | {row['종목명']} | {row['종목코드']} | "
                       f"{row['1주_수익률']}% | {row['12개월_수익률']}% | "
                       f"{row['ETF섹터']} | {row['국내외구분']} |\n")
            
            # 섹터별 통계
            f.write("\n---\n\n")
            f.write("## 📊 섹터별 통계\n\n")
            
            sector_stats = df.groupby('ETF섹터').agg({
                '종목코드': 'count'
            }).reset_index()
            sector_stats.columns = ['섹터', '종목 수']
            sector_stats = sector_stats.sort_values('종목 수', ascending=False)
            
            f.write("| 섹터 | 종목 수 |\n")
            f.write("|------|--------|\n")
            for _, row in sector_stats.iterrows():
                f.write(f"| {row['섹터']} | {row['종목 수']} |\n")
        
        print(f"   ✓ Markdown 저장: {filename}")
        return filename
    
    def generate_telegram_summary(self, df: pd.DataFrame) -> str:
        """
        텔레그램 요약 메시지 생성 (TOP 5만)
        """
        # 1년 기준 정렬
        df_1y = df[df['12개월_수익률'] != '미출시'].copy()
        df_1y = df_1y.sort_values('12개월_수익률', ascending=False)
        
        # 1주일 기준 정렬
        df_1w = df[df['1주_수익률'] != '미출시'].copy()
        df_1w = df_1w.sort_values('1주_수익률', ascending=False)
        
        msg = f"<b>📊 ETF 수익률 분석 완료</b>\n"
        msg += f"📅 기준일: {self.base_date}\n"
        msg += f"📈 분석 대상: {len(df)}개 ETF\n\n"
        
        msg += "<b>🔝 1년 수익률 TOP 5</b>\n"
        for idx, row in df_1y.head(5).iterrows():
            msg += f"{int(row['12개월_순위'])}. {row['종목명']}\n"
            msg += f"   💰 1년: {row['12개월_수익률']}% | 1주: {row['1주_수익률']}%\n"
        
        msg += f"\n<b>🔝 1주일 수익률 TOP 5</b>\n"
        for idx, row in df_1w.head(5).iterrows():
            msg += f"{int(row['1주_순위'])}. {row['종목명']}\n"
            msg += f"   💰 1주: {row['1주_수익률']}% | 1년: {row['12개월_수익률']}%\n"
        
        msg += f"\n✅ 상세 데이터: JSON, Excel, Markdown 저장됨"
        
        return msg
    
    def send_telegram_message(self, message: str):
        """텔레그램 메시지 전송 (파일 전송 제거)"""
        if not self.telegram_token or not self.chat_id:
            print("   ⚠️  텔레그램 설정 없음 - 전송 스킵")
            return
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                print("   ✓ 텔레그램 전송 완료")
            else:
                print(f"   ✗ 텔레그램 전송 실패: {response.status_code}")
            
        except Exception as e:
            print(f"   ✗ 텔레그램 전송 실패: {e}")
    
    def run(self):
        """전체 분석 실행 (GitHub Actions 패턴)"""
        # 1. API로 데이터 수집
        df = self.analyze_etfs()
        
        if df is None:
            return None
        
        # 2. 데이터 저장 (JSON, Excel, Markdown)
        print("\n📁 데이터 저장 중...")
        json_file = self.save_to_json(df)
        excel_file = self.save_to_excel(df)
        md_file = self.save_to_markdown(df)
        
        # 3. Git commit은 workflow에서 수행
        print("\n📤 텔레그램 요약 전송 중...")
        summary = self.generate_telegram_summary(df)
        self.send_telegram_message(summary)
        
        print("\n" + "=" * 60)
        print("✅ 전체 분석 완료!")
        print(f"📁 저장된 파일:")
        print(f"   - {json_file}")
        print(f"   - {excel_file}")
        print(f"   - {md_file}")
        print("=" * 60)
        
        return df


if __name__ == "__main__":
    analyzer = ETFPerformanceAnalyzer()
    result_df = analyzer.run()
    
    if result_df is not None:
        print("\n📋 결과 샘플:")
        print(result_df.head(10))
