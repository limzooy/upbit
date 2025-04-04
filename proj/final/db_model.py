from sqlalchemy import create_engine, Column, Float, Integer, String, BigInteger, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# MySQL 데이터베이스 설정
DATABASE_URL = "mysql+pymysql://root:root@localhost:3307/upbit"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    trade_type = Column(String(10))  # 'buy' or 'sell'
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    price = Column(Float)
    volume = Column(Float)

class StatusLog(Base):
    __tablename__ = "status_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    current_price = Column(Float)
    rsi = Column(Float)
    lower_band = Column(Float)
    upper_band = Column(Float)
    krw_balance = Column(Float)
    btc_balance = Column(Float)
    portfolio_value = Column(Float)
    profit_rate = Column(Float)

# 테이블 생성
Base.metadata.create_all(bind=engine)
