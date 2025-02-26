import pymysql
import pandas as pd
import numpy as np
import datetime
import json
import pyupbit

# MySQL 연결 정보
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "upbit",
    "port": 3307
}

# 초기 자본 및 매매 설정
INITIAL_BALANCE = 1000000  # 100만원 초기 자본
BUY_UNIT = INITIAL_BALANCE / 50  # 자본의 1/50씩 매수
MIN_ORDER_AMOUNT = 5000  # 최소 주문 금액
TAKE_PROFIT_RATIO = 1.05  # 5% 이상 상승 시 매도

# 거래 기록
class SpiderTrading:
    def __init__(self, df):
        self.df = df
        self.current_step = 0
        self.balance = INITIAL_BALANCE
        self.holdings = []  # 매수 가격을 개별 저장
        
    def reset(self):
        self.current_step = 0
        self.balance = INITIAL_BALANCE
        self.holdings = []
    
    def _next_price(self):
        return self.df.iloc[self.current_step]["close"]
    
    def buy(self):
        current_price = self._next_price()
        buy_amount = min(BUY_UNIT, self.balance)
        
        if buy_amount >= MIN_ORDER_AMOUNT:
            self.holdings.append((current_price, buy_amount / current_price))
            self.balance -= buy_amount
            print(f"BUY: {buy_amount} KRW at {current_price} KRW")
    
    def sell(self):
        current_price = self._next_price()
        new_holdings = []
        
        for buy_price, amount in self.holdings:
            if current_price >= buy_price * TAKE_PROFIT_RATIO:
                self.balance += current_price * amount
                print(f"SELL: {amount * current_price} KRW at {current_price} KRW (Bought at {buy_price})")
            else:
                new_holdings.append((buy_price, amount))
        
        self.holdings = new_holdings
    
    def step(self):
        self.buy()
        self.sell()
        self.current_step += 1
        return self.current_step >= len(self.df) - 1

# 데이터 불러오기
def fetch_data():
    connection = pymysql.connect(**DB_CONFIG)
    query = "SELECT timestamp, close FROM market_data ORDER BY timestamp ASC"
    df = pd.read_sql(query, connection)
    connection.close()
    return df

# 실행 함수
if __name__ == "__main__":
    df = fetch_data()
    trader = SpiderTrading(df)
    
    while not trader.step():
        pass
    
    print(f"Final Balance: {trader.balance} KRW")
