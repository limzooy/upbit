import requests
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from sqlalchemy import desc
import uvicorn
from back.db_model import SessionLocal, UpbitCandleData
from back.predict import predict_next_action

# Upbit API 설정
UPBIT_API_URL = "https://api.upbit.com/v1/candles/minutes/15"
MARKET = "KRW-BTC"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")

# DB에서 마지막으로 저장된 캔들 데이터의 timestamp 가져오기
def get_last_candle_time():
    session = SessionLocal()
    try:
        last_entry = session.query(UpbitCandleData).order_by(desc(UpbitCandleData.timestamp)).first()
        if last_entry:
            return last_entry.timestamp  # Unix Timestamp(ms)
        return None
    except Exception as e:
        print(f"Error getting last candle time: {e}")
        return None
    finally:
        session.close()

# 현재 가장 가까운 15분 단위 시각을 Unix Timestamp(ms)로 반환
def get_nearest_candle_timestamp():
    now = datetime.utcnow() + timedelta(hours=9)  # 한국 시간 변환
    minute = now.minute - (now.minute % 15)
    nearest_time = now.replace(minute=minute, second=0, microsecond=0)
    return int(nearest_time.timestamp() * 1000)  # ms 단위로 변환

# Upbit API를 호출하여 최신 15분봉 데이터를 가져옴
def fetch_latest_candle_data():
    last_candle_time = get_last_candle_time()
    nearest_candle_time = get_nearest_candle_timestamp()

    if last_candle_time is None or last_candle_time < nearest_candle_time:
        print(f"[INFO] Fetching new candle data... (Last: {last_candle_time}, Nearest: {nearest_candle_time})")

        params = {"market": MARKET, "count": 5}  # 최근 데이터 5개 가져오기 (여유를 두고 수집)
        response = requests.get(UPBIT_API_URL, params=params)

        if response.status_code == 200:
            data = response.json()
            if not data:
                print("[INFO] No new candle data found.")
                return

            session = SessionLocal()
            new_entries = []

            try:
                for item in data:
                    if last_candle_time and item["timestamp"] <= last_candle_time:
                        continue  # 이미 저장된 데이터는 건너뜀

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
                    print(f"[INFO] Inserted {len(new_entries)} new candles.")

            except Exception as e:
                session.rollback()
                print(f"[ERROR] Database insert failed: {e}")

            finally:
                session.close()

        else:
            print(f"[ERROR] Upbit API request failed: {response.status_code} - {response.text}")

    else:
        print("[INFO] No new data needed.")

# FastAPI 시작 시 데이터 확인 후 부족하면 추가
@app.on_event("startup")
async def startup_event():
    fetch_latest_candle_data()

# 15분마다 자동으로 새로운 데이터를 수집
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_latest_candle_data, CronTrigger(minute="0,15,30,45"))
scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

@app.get("/candles")
def get_candle_data():
    session = SessionLocal()
    try:
        query = session.query(UpbitCandleData).order_by(desc(UpbitCandleData.timestamp)).limit(30).all()
        data = [{
            "timestamp": (datetime.utcfromtimestamp(item.timestamp / 1000) + timedelta(hours=9)).isoformat(),
            "timestamp_unix": item.timestamp,
            "market": item.market,
            "open": item.opening_price,
            "high": item.high_price,
            "low": item.low_price,
            "close": item.trade_price,
            "volume": item.candle_acc_trade_volume
        } for item in query]
        return data
    except Exception as e:
        return {"error": str(e)}
    finally:
        session.close()

@app.get("/predict")
def get_prediction():
    return predict_next_action()

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

