# import pymysql
# import pandas as pd
# import numpy as np
# import datetime
# import json
# import time

# # MySQL 연결 정보
# DB_CONFIG = {
#     "host": "localhost",
#     "user": "root",
#     "password": "root",
#     "database": "upbit",
#     "port": 3307
# }

# # 기술적 지표 계산 함수
# def calculate_indicators(df):
#     df['ma20'] = df['trade_price'].rolling(window=20).mean()
#     df['stddev'] = df['trade_price'].rolling(window=20).std()
#     df['upper_band'] = df['ma20'] + (df['stddev'] * 2)
#     df['lower_band'] = df['ma20'] - (df['stddev'] * 2)
#     df['rsi'] = compute_rsi(df['trade_price'], 14)
#     df['macd'], df['signal_value'] = compute_macd(df['trade_price'])
#     return df

# # RSI 계산
# def compute_rsi(series, period=14):
#     delta = series.diff()
#     gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
#     loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
#     rs = gain / loss
#     return 100 - (100 / (1 + rs))

# # MACD 계산
# def compute_macd(series, short_period=12, long_period=26, signal_period=9):
#     short_ema = series.ewm(span=short_period, adjust=False).mean()
#     long_ema = series.ewm(span=long_period, adjust=False).mean()
#     macd = short_ema - long_ema
#     signal_value = macd.ewm(span=signal_period, adjust=False).mean()
#     return macd, signal_value

# # 매매 신호 생성 클래스
# class SignalGenerator:
#     def __init__(self, df):
#         self.df = calculate_indicators(df)
#         self.current_step = len(df) - 1  # 최신 데이터 사용

#     def generate_signal(self):
#         current_row = self.df.iloc[self.current_step]
#         signal_value = "HOLD"
        
#         if (current_row["trade_price"] <= current_row["lower_band"] and
#             current_row["rsi"] <= 30 and
#             current_row["macd"] > current_row["signal_value"]):
#             signal_value = "BUY"
        
#         elif (current_row["trade_price"] >= current_row["upper_band"] or
#               current_row["rsi"] >= 70 or
#               current_row["macd"] < current_row["signal_value"]):
#             signal_value = "SELL"
        
#         return signal_value, current_row

# # 데이터 불러오기 (upbit_15m_candle_data 사용)
# def fetch_data():
#     connection = pymysql.connect(**DB_CONFIG)
#     query = "SELECT timestamp, trade_price FROM upbit_15m_candle_data ORDER BY timestamp ASC"
#     df = pd.read_sql(query, connection)
#     connection.close()
#     return df

# # DB에 매매 신호 및 지표 저장
# def save_to_db(timestamp, signal_value, indicators):
#     connection = pymysql.connect(**DB_CONFIG)
#     cursor = connection.cursor()
    
#     query = """
#     INSERT INTO TechnicalIndicators (market, timestamp, moving_avg_50, rsi_14, macd, signal_value)
#     VALUES (%s, %s, %s, %s, %s, %s)
#     """
#     values = ("KRW-BTC", timestamp, indicators["ma20"], indicators["rsi"], indicators["macd"], indicators["signal_value"])
    
#     cursor.execute(query, values)
#     connection.commit()
#     connection.close()

# # 실행 함수
# if __name__ == "__main__":
#     while True:
#         df = fetch_data()
#         generator = SignalGenerator(df)
#         signal_value, indicators = generator.generate_signal()
        
#         result = {
#             "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#             "signal_value": signal_value
#         }

#         with open("trade_signal.json", "w") as f:
#             json.dump(result, f)
        
#         # DB에 저장
#         save_to_db(indicators.name, signal_value, indicators)

#         print("[매매 신호 저장 완료]", result)
        
#         # 일정 시간 대기 (예: 15분)
#         time.sleep(900)  # 900초 = 15분

import pymysql
import pandas as pd
import numpy as np
import datetime
import json
import time

# MySQL 연결 정보
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "upbit",
    "port": 3307
}

# 기술적 지표 계산 함수
def calculate_indicators(df):
    df['ma20'] = df['trade_price'].rolling(window=20).mean()
    df['stddev'] = df['trade_price'].rolling(window=20).std()
    df['upper_band'] = df['ma20'] + (df['stddev'] * 2)
    df['lower_band'] = df['ma20'] - (df['stddev'] * 2)
    df['rsi'] = compute_rsi(df['trade_price'], 14)
    df['macd'], df['signal_value'] = compute_macd(df['trade_price'])
    return df

# RSI 계산
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# MACD 계산
def compute_macd(series, short_period=12, long_period=26, signal_period=9):
    short_ema = series.ewm(span=short_period, adjust=False).mean()
    long_ema = series.ewm(span=long_period, adjust=False).mean()
    macd = short_ema - long_ema
    signal_value = macd.ewm(span=signal_period, adjust=False).mean()
    return macd, signal_value

# 매매 신호 생성 클래스
class SignalGenerator:
    def __init__(self, df):
        self.df = calculate_indicators(df)
        self.current_step = len(df) - 1  # 최신 데이터 사용

    def generate_signal(self):
        current_row = self.df.iloc[self.current_step]
        signal_value = "HOLD"
        
        if (current_row["trade_price"] <= current_row["lower_band"] and
            current_row["rsi"] <= 30 and
            current_row["macd"] > current_row["signal_value"]):
            signal_value = "BUY"
        
        elif (current_row["trade_price"] >= current_row["upper_band"] or
              current_row["rsi"] >= 70 or
              current_row["macd"] < current_row["signal_value"]):
            signal_value = "SELL"
        
        return signal_value, current_row

# 데이터 불러오기
def fetch_data():
    connection = pymysql.connect(**DB_CONFIG)
    query = "SELECT timestamp, trade_price FROM upbit_15m_candle_data ORDER BY timestamp ASC"
    df = pd.read_sql(query, connection)
    connection.close()
    return df

# DB에 매매 신호 및 지표 저장
def save_to_db(timestamp, signal_value, indicators):
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    query = """
    INSERT INTO TechnicalIndicators (market, timestamp, moving_avg_50, rsi_14, macd, signal_value)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    values = ("KRW-BTC", timestamp, indicators["ma20"], indicators["rsi"], indicators["macd"], signal_value)
    
    cursor.execute(query, values)
    connection.commit()
    connection.close()

# 실행 함수
if __name__ == "__main__":
    while True:
        df = fetch_data()
        generator = SignalGenerator(df)
        signal_value, indicators = generator.generate_signal()
        
        result = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "signal_value": signal_value
        }

        # 매매 신호를 파일로 저장
        with open("trade_signal.json", "w") as f:
            json.dump(result, f)
        
        # DB에 저장
        save_to_db(indicators.name, signal_value, indicators)

        print("[매매 신호 저장 완료]", result)
        
        time.sleep(900)  # 900초 = 15분
