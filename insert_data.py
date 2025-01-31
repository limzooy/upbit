import requests
from db_model import SessionLocal, UpbitCandleData
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc
import time

URL = "https://api.upbit.com/v1/candles/minutes/15"
MARKET = "KRW-BTC"
COUNT = 200  # 한 번 요청할 때 가져올 데이터 개수

session = SessionLocal()

def get_latest_saved_timestamp():
    """DB에서 가장 최신에 저장된 캔들의 timestamp를 가져옴"""
    latest_candle = session.query(UpbitCandleData).order_by(desc(UpbitCandleData.timestamp)).first()
    return latest_candle.timestamp if latest_candle else None

def collect_historical_data():
    """중복되지 않게 과거 데이터를 수집하고 최신 데이터까지 따라잡을 때까지 반복"""
    latest_timestamp = get_latest_saved_timestamp()

    try:
        while True:
            # 최신 데이터가 없으면 (최초 실행 시), 가장 최근 데이터부터 200개 가져옴
            params = {"market": MARKET, "count": COUNT}
            
            if latest_timestamp:
                params["to"] = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(latest_timestamp // 1000))

            response = requests.get(URL, params=params)

            if response.status_code == 200:
                data = response.json()

                # 데이터가 없으면 더 이상 수집할 필요 없음
                if not data:
                    print("No more historical data to fetch.")
                    break

                try:
                    for item in data:
                        # 중복 방지: timestamp가 이미 존재하는지 확인 후 저장
                        exists = session.query(UpbitCandleData).filter_by(timestamp=item["timestamp"]).first()
                        if exists:
                            print(f"Skipping duplicate timestamp: {item['timestamp']}")
                            continue

                        upbit_entry = UpbitCandleData(
                            market=item["market"],
                            candle_date_time_utc=item["candle_date_time_utc"],
                            candle_date_time_kst=item["candle_date_time_kst"],
                            opening_price=item["opening_price"],
                            high_price=item["high_price"],
                            low_price=item["low_price"],
                            trade_price=item["trade_price"],
                            timestamp=item["timestamp"],
                            candle_acc_trade_price=item["candle_acc_trade_price"],
                            candle_acc_trade_volume=item["candle_acc_trade_volume"],
                            unit=item["unit"],
                        )
                        session.add(upbit_entry)

                    session.commit()
                    print(f"Inserted {len(data)} historical candles.")

                    # 다음 요청을 위해 가장 오래된 데이터의 timestamp 갱신
                    latest_timestamp = data[-1]["timestamp"]

                    # API 요청 제한 방지를 위해 약간의 지연
                    time.sleep(1.0)

                except Exception as e:
                    session.rollback()
                    print(f"Error occurred: {e}")

            else:
                print(f"API 요청 실패: {response.status_code}")
                print(response.text)
                break

    except KeyboardInterrupt:
        print("\n[INFO] 중단 요청 감지됨. 변경 사항을 저장")
        session.commit()  # 현재까지의 데이터를 저장
        print("[INFO] 데이터 저장 완료. 안전하게 종료.")

    finally:
        session.close()  # 세션 정리
        print("Historical data collection completed.")

if __name__ == "__main__":
    collect_historical_data()
