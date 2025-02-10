# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import FileResponse
# from apscheduler.schedulers.background import BackgroundScheduler
# from apscheduler.triggers.cron import CronTrigger
# from sqlalchemy.orm import Session
# import requests
# import pandas as pd
# import uvicorn
# import os
# from back.db_model import SessionLocal, UpbitCandleData
# from back.predict import predict_next_action
# from datetime import datetime, timedelta

# # FastAPI 애플리케이션 생성
# app = FastAPI()

# # CORS 설정 추가 (프론트엔드에서 API 요청 가능하도록)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # 모든 도메인에서 접근 가능하도록 설정
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # 정적 파일 서빙
# app.mount("/static", StaticFiles(directory="static"), name="static")

# # 기본 페이지(index.html) 제공
# @app.get("/")
# async def serve_frontend():
#     return FileResponse(os.path.join("static", "index.html"))

# # 마지막 데이터 시각을 가져오는 함수
# def get_last_candle_time():
#     session = SessionLocal()
#     try:
#         # DB에서 최신 데이터를 가져와서 가장 최근 시각 확인
#         last_entry = session.query(UpbitCandleData).order_by(UpbitCandleData.timestamp.desc()).first()
#         if last_entry:
#             last_time = datetime.utcfromtimestamp(last_entry.timestamp / 1000) + timedelta(hours=9)  # KST 변환
#             return last_time
#         else:
#             return None
#     except Exception as e:
#         print(f"Error getting last candle time: {e}")
#         return None
#     finally:
#         session.close()

# # 특정 시각에 맞춰 데이터를 수집하는 함수
# def fetch_and_store_candle_data_at_time(target_time: datetime):
#     URL = "https://api.upbit.com/v1/candles/minutes/15"
#     PARAMS = {"market": "KRW-BTC", "to": target_time.strftime('%Y-%m-%dT%H:%M:%S'), "count": 1}
#     session = SessionLocal()

#     try:
#         response = requests.get(URL, params=PARAMS)
#         if response.status_code == 200:
#             data = response.json()[0]  # 데이터 1개
#             upbit_entry = UpbitCandleData(
#                 market=data["market"],
#                 candle_date_time_utc=data["candle_date_time_utc"],
#                 candle_date_time_kst=data["candle_date_time_kst"],
#                 opening_price=data["opening_price"],
#                 high_price=data["high_price"],
#                 low_price=data["low_price"],
#                 trade_price=data["trade_price"],
#                 timestamp=data["timestamp"],
#                 candle_acc_trade_price=data["candle_acc_trade_price"],
#                 candle_acc_trade_volume=data["candle_acc_trade_volume"],
#                 unit=data["unit"],
#             )
#             session.add(upbit_entry)
#             session.commit()
#             print(f"Candle data for {target_time} inserted successfully.")
#         else:
#             print(f"API request failed for {target_time}: {response.status_code}")
#             print(response.text)
#     except Exception as e:
#         session.rollback()
#         print(f"Error occurred: {e}")
#     finally:
#         session.close()

# # 빠진 데이터를 수집하는 함수
# def fetch_missing_candle_data():
#     last_candle_time = get_last_candle_time()
#     if last_candle_time:
#         # 가장 최근의 데이터 시각부터 현재까지 빠진 시각 계산
#         now = datetime.now()
#         times_to_fetch = []
        
#         # 00, 15, 30, 45분 시각 계산
#         for minute in [0, 15, 30, 45]:
#             target_time = now.replace(minute=minute, second=0, microsecond=0)
#             if target_time > last_candle_time:  # 마지막 데이터 이후만 수집
#                 times_to_fetch.append(target_time)

#         # 각 시각에 대해 데이터를 요청하고 저장
#         for target_time in times_to_fetch:
#             fetch_and_store_candle_data_at_time(target_time)

# # FastAPI 애플리케이션 시작 시 빠진 데이터 수집
# @app.on_event("startup")
# async def startup_event():
#     fetch_missing_candle_data()

# # 스케줄러 설정 (매 시각 00, 15, 30, 45분에 실행)
# scheduler = BackgroundScheduler()
# scheduler.add_job(fetch_and_store_candle_data_at_time, CronTrigger(minute="0,15,30,45"), args=[datetime.now()])
# scheduler.start()

# # FastAPI 종료 시 스케줄러도 안전하게 종료
# @app.on_event("shutdown")
# def shutdown_event():
#     scheduler.shutdown()

# # MySQL 데이터 가져오기
# @app.get("/candles")
# def get_candle_data():
#     session = SessionLocal()
#     try:
#         # DB에서 최신 N개 데이터 가져오기
#         query = session.query(UpbitCandleData).order_by(UpbitCandleData.timestamp.desc()).limit(30).all()
        
#         # UTC → KST 변환 코드 추가
#         data = [
#             {
#                 "timestamp": (datetime.utcfromtimestamp(item.timestamp / 1000) + timedelta(hours=9)).replace(microsecond=0).isoformat(),  # KST 변환
#                 "timestamp_unix": item.timestamp,  # 기존의 unix timestamp
#                 "market": item.market,
#                 "open": item.opening_price,
#                 "high": item.high_price,
#                 "low": item.low_price,
#                 "close": item.trade_price,
#                 "volume": item.candle_acc_trade_volume
#             }
#             for item in query
#         ]

#         # Pandas DataFrame 변환
#         df = pd.DataFrame(data)
#         return df.to_dict(orient="records")

#     except Exception as e:
#         return {"error": str(e)}
#     finally:
#         session.close()
        
        
# @app.get("/predict")
# def get_prediction():
#     """예측값 반환 API"""
#     return predict_price()

# # FastAPI 실행
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8080)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
import requests
import pandas as pd
import uvicorn
import os
from back.db_model import SessionLocal, UpbitCandleData
from back.predict import predict_next_action
from datetime import datetime, timedelta

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
async def serve_frontend():
    return FileResponse(os.path.join("static", "index.html"))

# 마지막 데이터 시각을 가져오는 함수
def get_last_candle_time():
    session = SessionLocal()
    try:
        last_entry = session.query(UpbitCandleData).order_by(UpbitCandleData.timestamp.desc()).first()
        if last_entry:
            last_time = datetime.utcfromtimestamp(last_entry.timestamp / 1000) + timedelta(hours=9)  # KST 변환
            return last_time
        else:
            return None
    except Exception as e:
        print(f"Error getting last candle time: {e}")
        return None
    finally:
        session.close()

# 정확한 15분 단위 시각을 맞추기 위한 함수
def get_nearest_candle_time():
    now = datetime.utcnow() + timedelta(hours=9)  # KST 기준
    minute = now.minute

    # 가장 가까운 15분 단위로 보정
    if minute < 15:
        target_minute = 0
    elif minute < 30:
        target_minute = 15
    elif minute < 45:
        target_minute = 30
    else:
        target_minute = 45

    # 보정된 시간 반환
    return now.replace(minute=target_minute, second=0, microsecond=0)

# 특정 시각에 맞춰 데이터를 수집하는 함수
def fetch_and_store_candle_data():
    target_time = get_nearest_candle_time()  # 가장 가까운 15분 단위 시각 계산
    URL = "https://api.upbit.com/v1/candles/minutes/15"
    PARAMS = {"market": "KRW-BTC", "to": target_time.strftime('%Y-%m-%dT%H:%M:%S'), "count": 1}

    session = SessionLocal()
    try:
        response = requests.get(URL, params=PARAMS)
        if response.status_code == 200:
            data = response.json()
            if data:
                item = data[0]  # 가장 최근 데이터 1개 가져옴
                timestamp_dt = datetime.strptime(item["candle_date_time_kst"], "%Y-%m-%dT%H:%M:%S")

                # 15분 단위 데이터인지 확인 (정확한 0, 15, 30, 45분만 저장)
                if timestamp_dt.minute in [0, 15, 30, 45]:
                    exists = session.query(UpbitCandleData).filter_by(timestamp=item["timestamp"]).first()
                    if not exists:
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
                        print(f"Candle data for {target_time} inserted successfully.")
                    else:
                        print(f"Skipping duplicate timestamp: {item['timestamp']}")
                else:
                    print(f"Ignoring non-15-minute data: {timestamp_dt}")

        else:
            print(f"API request failed for {target_time}: {response.status_code}")
            print(response.text)

    except Exception as e:
        session.rollback()
        print(f"Error occurred: {e}")
    finally:
        session.close()

# 빠진 데이터를 수집하는 함수
def fetch_missing_candle_data():
    last_candle_time = get_last_candle_time()
    if last_candle_time:
        now = datetime.utcnow() + timedelta(hours=9)  # 현재 KST 기준
        times_to_fetch = []

        # 00, 15, 30, 45분 시각 계산
        for minute in [0, 15, 30, 45]:
            target_time = now.replace(minute=minute, second=0, microsecond=0)
            if target_time > last_candle_time:  # 마지막 데이터 이후만 수집
                times_to_fetch.append(target_time)

        for target_time in times_to_fetch:
            fetch_and_store_candle_data()

@app.on_event("startup")
async def startup_event():
    fetch_missing_candle_data()

# 스케줄러 설정 (매 00, 15, 30, 45분 실행)
scheduler = BackgroundScheduler()
scheduler.add_job(fetch_and_store_candle_data, CronTrigger(minute="0,15,30,45"))
scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

@app.get("/candles")
def get_candle_data():
    session = SessionLocal()
    try:
        query = session.query(UpbitCandleData).order_by(UpbitCandleData.timestamp.desc()).limit(30).all()
        data = [
            {
                "timestamp": (datetime.utcfromtimestamp(item.timestamp / 1000) + timedelta(hours=9)).isoformat(),
                "timestamp_unix": item.timestamp,
                "market": item.market,
                "open": item.opening_price,
                "high": item.high_price,
                "low": item.low_price,
                "close": item.trade_price,
                "volume": item.candle_acc_trade_volume
            }
            for item in query
        ]
        df = pd.DataFrame(data)
        return df.to_dict(orient="records")

    except Exception as e:
        return {"error": str(e)}
    finally:
        session.close()

@app.get("/predict")
def get_prediction():
    return predict_next_action()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
