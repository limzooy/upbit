from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db_model import SessionLocal, UpbitData

# FastAPI 라우터 생성
router = APIRouter()

# Pydantic 모델 정의
class UpbitDataRequest(BaseModel):
    market: str
    trade_date: str
    trade_time: str
    trade_date_kst: str
    trade_time_kst: str
    trade_timestamp: int
    opening_price: float
    high_price: float
    low_price: float
    trade_price: float
    prev_closing_price: float
    change: str
    change_price: float
    change_rate: float
    signed_change_price: float
    signed_change_rate: float
    trade_volume: float
    acc_trade_price: float
    acc_trade_price_24h: float
    acc_trade_volume: float
    acc_trade_volume_24h: float
    timestamp: int

# 데이터 삽입 API
@router.post("/upbit/data/")
def insert_upbit_data(data: UpbitDataRequest):
    db: Session = SessionLocal()
    try:
        db_data = UpbitData(**data.dict())
        db.add(db_data)
        db.commit()
        db.refresh(db_data)
        return {"message": "Data inserted successfully", "data_id": db_data.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error inserting data: {str(e)}")
    finally:
        db.close()

