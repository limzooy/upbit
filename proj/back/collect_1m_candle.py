import requests
from db_model import SessionLocal, UpbitCandleData1Min
from sqlalchemy.orm import sessionmaker
from sqlalchemy import desc
import time

URL = "https://api.upbit.com/v1/candles/minutes/1"  # 1분봉 데이터 요청
MARKET = "KRW-BTC"
COUNT = 200  # 한 번 요청할 때 가져올 데이터 개수

session = SessionLocal()

def get_latest_saved_candle():
    """DB에서 가장 최신에 저장된 1분봉 캔들을 가져옴"""
    return session.query(UpbitCandleData1Min).order_by(desc(UpbitCandleData1Min.timestamp)).first()

def collect_historical_data():
    """중복되지 않게 1분봉 데이터를 수집"""
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
                        # 중복 데이터 체크
                        exists = session.query(UpbitCandleData1Min).filter(
                            UpbitCandleData1Min.timestamp == item["timestamp"],
                            UpbitCandleData1Min.trade_price == item["trade_price"]
                        ).first()
                        
                        if exists:
                            print(f"Skipping duplicate candle: {item['timestamp']}")
                            continue

                        new_entries.append(
                            UpbitCandleData1Min(
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
                        print(f"Inserted {len(new_entries)} historical 1-minute candles.")
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
        session.commit()
        session.close()
        print("1-minute candle data collection safely stopped.")

    except Exception as e:
        print(f"Unexpected error: {e}")
        session.rollback()

    finally:
        session.close()
        print("1-minute candle data collection completed.")
        
def get_latest_price():
    """가장 최신의 1분봉 거래 가격을 가져옴"""
    latest_candle = get_latest_saved_candle()
    if latest_candle:
        return latest_candle.trade_price  # 최신 1분봉의 거래 가격 반환
    else:
        print("No candles found in the database.")
        return None

if __name__ == "__main__":
    collect_historical_data()
