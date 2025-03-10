import pyupbit
import pandas as pd
import time

def get_ohlcv_by_range(ticker, start_date, end_date, interval="minute5"):
    all_data = []
    to = end_date  # 최신 데이터부터 거꾸로 수집

    while True:
        df = pyupbit.get_ohlcv(ticker, interval=interval, to=to, count=200)
        
        if df is None or df.empty:
            print("데이터 수집 종료 (더 이상 데이터 없음)")
            break  # 더 이상 데이터가 없으면 종료
        
        all_data.append(df)
        to = df.index[0].strftime('%Y-%m-%d %H:%M:%S')  # 가장 오래된 날짜를 기준으로 업데이트

        # 현재까지 수집된 데이터 개수 출력
        total_rows = sum(len(d) for d in all_data)
        print(f"현재까지 수집된 데이터 개수: {total_rows}개")
        
        # 시작 날짜보다 이전 데이터라면 종료
        if df.index[0] < pd.to_datetime(start_date):
            print("시작 날짜보다 이전 데이터 도달, 종료")
            break

        time.sleep(0.5)  # API 요청 제한을 피하기 위해 잠시 대기
    
    # 데이터프레임 합치기
    final_df = pd.concat(all_data).sort_index()  # 시간 순서대로 정렬

    # 시작 날짜 이후의 데이터만 필터링
    final_df = final_df[final_df.index >= pd.to_datetime(start_date)]
    
    return final_df

# 원하는 기간 설정
start_date = "2023-01-01"
end_date = "2025-03-06"
ticker = "KRW-BTC"

# 데이터 수집
df = get_ohlcv_by_range(ticker, start_date, end_date)

# CSV 저장
csv_filename = f"{ticker}_5min_{start_date}_{end_date}.csv"
df.to_csv(csv_filename, encoding='utf-8-sig')

print(f"데이터 저장 완료: {csv_filename}")
print(f"최종 데이터 개수: {len(df)}개")
print(df.head())  # 데이터 확인
