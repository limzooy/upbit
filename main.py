from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
import requests
import pandas as pd
import uvicorn
from db_model import SessionLocal, UpbitCandleData
from datetime import datetime, timedelta

# FastAPI 애플리케이션 생성
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "FastAPI 서버 정상 작동 중"}

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

# 스케줄러 설정 (00분, 15분, 30분, 45분마다 실행)
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_and_store_candle_data, "cron", minute="0,15,30,45")
scheduler.start()

# MySQL 데이터 가져오기
@app.get("/candles")
def get_candle_data():
    session = SessionLocal()
    try:
        # DB에서 최신 N개 데이터 가져오기
        query = session.query(UpbitCandleData).order_by(UpbitCandleData.timestamp.desc()).limit(30).all()
        
        # UTC → KST 변환 코드 추가
        data = [
            {
                "timestamp": (datetime.utcfromtimestamp(item.timestamp / 1000) + timedelta(hours=9)).replace(microsecond=0).isoformat(),  # KST 변환
                "timestamp_unix": item.timestamp,  # 기존의 unix timestamp
                "market": item.market,
                "open": item.opening_price,
                "high": item.high_price,
                "low": item.low_price,
                "close": item.trade_price,
                "volume": item.candle_acc_trade_volume
            }
            for item in query
        ]

        # Pandas DataFrame 변환
        df = pd.DataFrame(data)
        return df.to_dict(orient="records")

    except Exception as e:
        return {"error": str(e)}
    finally:
        session.close()

# FastAPI 실행
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)