from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from db_model import SessionLocal, UpbitCandleData

# FastAPI 애플리케이션 생성
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "FastAPI 서버 정상 작동 중"}

# 초기 데이터 수집 함수
def initial_data_collection():
    URL = "https://api.upbit.com/v1/candles/minutes/15"
    PARAMS = {"market": "KRW-BTC", "count": 200}  # 과거 데이터 최대 요청
    session = SessionLocal()

    try:
        response = requests.get(URL, params=PARAMS)
        if response.status_code == 200:
            data = response.json()
            for item in data:
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
            print("Initial data collection completed.")
        else:
            print(f"API 요청 실패: {response.status_code}")
            print(response.text)
    except Exception as e:
        session.rollback()
        print(f"Error occurred during initial data collection: {e}")
    finally:
        session.close()

# 실시간 데이터 수집 함수
def fetch_and_store_candle_data():
    URL = "https://api.upbit.com/v1/candles/minutes/15"
    PARAMS = {"market": "KRW-BTC", "count": 1}  # 최신 데이터 1개만 요청
    session = SessionLocal()

    try:
        response = requests.get(URL, params=PARAMS)
        if response.status_code == 200:
            data = response.json()[0]  # 최신 데이터 1개
            upbit_entry = UpbitCandleData(
                market=data["market"],
                candle_date_time_utc=data["candle_date_time_utc"],
                candle_date_time_kst=data["candle_date_time_kst"],
                opening_price=data["opening_price"],
                high_price=data["high_price"],
                low_price=data["low_price"],
                trade_price=data["trade_price"],
                timestamp=data["timestamp"],
                candle_acc_trade_price=data["candle_acc_trade_price"],
                candle_acc_trade_volume=data["candle_acc_trade_volume"],
                unit=data["unit"],
            )
            session.add(upbit_entry)
            session.commit()
            print("Latest candle data inserted successfully.")
        else:
            print(f"API 요청 실패: {response.status_code}")
            print(response.text)
    except Exception as e:
        session.rollback()
        print(f"Error occurred: {e}")
    finally:
        session.close()

# 스케줄러 설정
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_and_store_candle_data, "interval", minutes=15)  # 15분마다 실행
scheduler.start()

# 초기 데이터 수집 실행
if __name__ == "__main__":
    initial_data_collection()
