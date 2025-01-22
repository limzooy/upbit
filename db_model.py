from sqlalchemy import create_engine, Column, Float, Integer, String, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# MySQL 데이터베이스 설정
DATABASE_URL = "mysql+pymysql://root:test@127.0.0.1/upbit"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy 테이블 정의
class UpbitData(Base):
    __tablename__ = "upbit_data"
    
    id = Column(Integer, primary_key=True, index=True)
    market = Column(String(50), index=True)  # VARCHAR 길이 지정
    trade_date = Column(String(10))          # VARCHAR 길이 지정
    trade_time = Column(String(8))           # VARCHAR 길이 지정
    trade_date_kst = Column(String(10))      # VARCHAR 길이 지정
    trade_time_kst = Column(String(8))       # VARCHAR 길이 지정
    trade_timestamp = Column(BigInteger)
    opening_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    trade_price = Column(Float)
    prev_closing_price = Column(Float)
    change = Column(String(20))              # VARCHAR 길이 지정
    change_price = Column(Float)
    change_rate = Column(Float)
    signed_change_price = Column(Float)
    signed_change_rate = Column(Float)
    trade_volume = Column(Float)
    acc_trade_price = Column(Float)
    acc_trade_price_24h = Column(Float)
    acc_trade_volume = Column(Float)
    acc_trade_volume_24h = Column(Float)
    timestamp = Column(BigInteger)

# 테이블 생성
Base.metadata.create_all(bind=engine)