from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db_model import SessionLocal, UpbitCandleData

# FastAPI 라우터 생성
router = APIRouter()

# Pydantic 모델 정의
class UpbitCandleDataRequest(BaseModel):
    market: str
    candle_date_time_utc: str
    candle_date_time_kst: str
    opening_price: float
    high_price: float
    low_price: float
    trade_price: float
    timestamp: int
    candle_acc_trade_price: float
    candle_acc_trade_volume: float
    unit: int

# 데이터 삽입 API
@router.post("/upbit/candle_data/")
def insert_upbit_candle_data(data: UpbitCandleDataRequest):
    db: Session = SessionLocal()
    try:
        db_data = UpbitCandleData(**data.dict())
        db.add(db_data)
        db.commit()
        db.refresh(db_data)
        return {"message": "Data inserted successfully", "data_id": db_data.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error inserting data: {str(e)}")
    finally:
        db.close()
