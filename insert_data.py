from db_model import SessionLocal, UpbitData

# 데이터
data = [
    {
        "market": "KRW-BTC",
        "trade_date": "20250122",
        "trade_time": "051959",
        "trade_date_kst": "20250122",
        "trade_time_kst": "141959",
        "trade_timestamp": 1737523199160,
        "opening_price": 157571000.00000000,
        "high_price": 157791000.00000000,
        "low_price": 156289000.00000000,
        "trade_price": 157035000.00000000,
        "prev_closing_price": 157571000.00000000,
        "change": "FALL",
        "change_price": 536000.00000000,
        "change_rate": 0.0034016412,
        "signed_change_price": -536000.00000000,
        "signed_change_rate": -0.0034016412,
        "trade_volume": 0.00929846,
        "acc_trade_price": 76490026102.4956900000000000,
        "acc_trade_price_24h": 535117411945.26540000,
        "acc_trade_volume": 486.95100648,
        "acc_trade_volume_24h": 3428.76423651,
        "timestamp": 1737523199186
    }
]

# 데이터베이스 세션 시작
session = SessionLocal()

try:
    # 데이터 삽입
    for item in data:
        upbit_entry = UpbitData(**item)  # 데이터 모델로 변환
        session.add(upbit_entry)  # 세션에 추가

    session.commit()  # 커밋하여 데이터베이스에 저장
    print("Data inserted successfully.")
except Exception as e:
    session.rollback()  # 에러 발생 시 롤백
    print(f"Error occurred: {e}")
finally:
    session.close()  # 세션 종료

