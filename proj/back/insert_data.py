# 코드 완성 건들 ㄴㄴ
import requests
from db_model import SessionLocal, UpbitCandleData
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc
import time

URL = "https://api.upbit.com/v1/candles/minutes/15"
MARKET = "KRW-BTC"
COUNT = 200  # 한 번 요청할 때 가져올 데이터 개수

session = SessionLocal()

def get_latest_saved_candle():
    """DB에서 가장 최신에 저장된 캔들을 가져옴"""
    return session.query(UpbitCandleData).order_by(desc(UpbitCandleData.timestamp)).first()

def collect_historical_data():
    """중복되지 않게 과거 데이터를 수집하고 최신 데이터까지 따라잡을 때까지 반복"""
    latest_candle = get_latest_saved_candle()
    latest_timestamp = latest_candle.timestamp if latest_candle else None

    try:
        while True:
            params = {"market": MARKET, "count": COUNT}
            if latest_timestamp:
                params["to"] = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(latest_timestamp // 1000))
            
            response = requests.get(URL, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if not data:
                    print("No more historical data to fetch.")
                    break

                try:
                    new_entries = []
                    for item in data:
                        # 중복 데이터 체크 (timestamp 뿐만 아니라 가격도 확인)
                        exists = session.query(UpbitCandleData).filter(
                            UpbitCandleData.timestamp == item["timestamp"],
                            UpbitCandleData.trade_price == item["trade_price"]
                        ).first()
                        
                        if exists:
                            print(f"Skipping duplicate candle: {item['timestamp']}")
                            continue

                        new_entries.append(
                            UpbitCandleData(
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
                        )

                    if new_entries:
                        session.add_all(new_entries)
                        session.commit()
                        print(f"Inserted {len(new_entries)} historical candles.")
                        latest_timestamp = data[-1]["timestamp"]
                    else:
                        print("No new candles to insert.")

                    time.sleep(0.5)

                except Exception as e:
                    session.rollback()
                    print(f"Error occurred: {e}")

            else:
                print(f"API 요청 실패: {response.status_code}")
                print(response.text)
                break

    except KeyboardInterrupt:
        print("\n[INFO] 중단 요청 감지됨. 수집된 데이터 저장 후 안전하게 종료합니다.")
        session.commit()  # 지금까지 저장된 데이터 유지
        session.close()
        print("Historical data collection safely stopped.")

    except Exception as e:
        print(f"Unexpected error: {e}")
        session.rollback()

    finally:
        session.close()
        print("Historical data collection completed.")

if __name__ == "__main__":
    collect_historical_data()