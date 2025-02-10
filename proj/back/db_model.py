from sqlalchemy import create_engine, Column, Float, Integer, String, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# MySQL 데이터베이스 설정
DATABASE_URL = "mysql+pymysql://root:root@localhost:3307/upbit"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy 테이블 정의
class UpbitCandleData(Base):
    __tablename__ = "upbit_15m_candle_data"

    id = Column(Integer, primary_key=True, index=True)
    market = Column(String(50), index=True)
    candle_date_time_utc = Column(String(50))
    candle_date_time_kst = Column(String(50))
    opening_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    trade_price = Column(Float)
    timestamp = Column(BigInteger)
    candle_acc_trade_price = Column(Float)
    candle_acc_trade_volume = Column(Float)
    unit = Column(Integer)

# 테이블 생성
Base.metadata.create_all(bind=engine)