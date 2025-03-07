import requests
import pandas as pd
import time

URL = "https://api.upbit.com/v1/candles/minutes/5"
MARKET = "KRW-BTC"
COUNT = 200  # 한 번 요청할 때 가져올 데이터 개수
def fetch_candle_data(start_date="2025-01-01", end_date="2025-02-28", filename="upbit_candle_data(3).csv"):
    all_data = []
    to_timestamp = time.mktime(time.strptime(end_date, "%Y-%m-%d")) * 1000  # 날짜를 타임스탬프로 변환
    
    try:
        while True:
            params = {"market": MARKET, "count": COUNT, "to": time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(to_timestamp / 1000))}
            response = requests.get(URL, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if not data or data[-1]["candle_date_time_utc"] < start_date:
                    print("데이터 수집 완료.")
                    break
                
                all_data.extend(data)
                print(f"{len(data)}개 데이터 수집 완료. 총 {len(all_data)}개 수집됨.")
                to_timestamp = data[-1]["timestamp"] - 1  # 중복 방지를 위해 마지막 데이터 이전 타임스탬프 사용
                time.sleep(0.5)
            else:
                print(f"API 요청 실패: {response.status_code}")
                break
    except Exception as e:
        print(f"데이터 수집 중 오류 발생: {e}")
    
    # 데이터프레임 변환 및 CSV 저장
    df = pd.DataFrame(all_data)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"{start_date} ~ {end_date} 기간의 데이터가 {filename} 파일로 저장되었습니다.")

if __name__ == "__main__":
    fetch_candle_data()
