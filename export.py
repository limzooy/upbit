import pandas as pd
from db_model import SessionLocal, UpbitCandleData

# 데이터베이스 세션 생성
session = SessionLocal()

def export_to_csv(file_path="upbit_candle_data.csv"):
    """Upbit 캔들 데이터를 CSV 파일로 저장하는 함수"""
    try:
        # 데이터베이스에서 모든 데이터 조회
        data = session.query(UpbitCandleData).all()

        # 데이터가 없으면 종료
        if not data:
            print("No data found in the database.")
            return

        # 데이터 변환 (SQLAlchemy 객체 → 딕셔너리 리스트 → 데이터프레임)
        df = pd.DataFrame([{
            "market": item.market,
            "candle_date_time_utc": item.candle_date_time_utc,
            "candle_date_time_kst": item.candle_date_time_kst,
            "opening_price": item.opening_price,
            "high_price": item.high_price,
            "low_price": item.low_price,
            "trade_price": item.trade_price,
            "timestamp": item.timestamp,
            "candle_acc_trade_price": item.candle_acc_trade_price,
            "candle_acc_trade_volume": item.candle_acc_trade_volume,
            "unit": item.unit
        } for item in data])

        # CSV 파일로 저장
        df.to_csv(file_path, index=False, encoding="utf-8-sig")
        print(f"Data successfully exported to {file_path}")

    except Exception as e:
        print(f"Error exporting data: {e}")

    finally:
        session.close()  # 세션 종료

# 실행
export_to_csv()