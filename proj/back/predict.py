import pymysql
import pandas as pd
import numpy as np
import gym
from gym import spaces
from stable_baselines3 import PPO
import datetime
import json

# MySQL 연결 정보
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "upbit",
    "port": 3307
}

# 강화학습 환경 정의
class TradingEnv(gym.Env):
    def __init__(self, df):
        super(TradingEnv, self).__init__()
        
        self.df = df
        self.current_step = 0
        self.initial_balance = 1000  # 초기 자본
        self.balance = self.initial_balance
        self.crypto_held = 0
        self.total_profit = 0
        
        # 상태 공간 (종가, 이동 평균, 거래량)
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(3,), dtype=np.float32
        )
        
        # 행동 공간 (0: 매도, 1: 유지, 2: 매수)
        self.action_space = spaces.Discrete(3)
    
    def reset(self):
        self.current_step = 0
        self.balance = self.initial_balance
        self.crypto_held = 0
        self.total_profit = 0
        return self._next_observation()
    
    def _next_observation(self):
        obs = np.array([
            self.df.iloc[self.current_step]["close"],
            self.df.iloc[self.current_step]["ma10"],
            self.df.iloc[self.current_step]["volume"]
        ])
        return obs
    
    def step(self, action):
        current_price = self.df.iloc[self.current_step]["close"]
        reward = 0
        
        if action == 2:  # 매수
            if self.balance >= current_price:
                self.crypto_held += 1
                self.balance -= current_price
        elif action == 0:  # 매도
            if self.crypto_held > 0:
                self.crypto_held -= 1
                self.balance += current_price
                self.total_profit += current_price
        
        self.current_step += 1
        done = self.current_step >= len(self.df) - 1
        reward = self.total_profit  # 총 수익을 보상으로 사용
        
        return self._next_observation(), reward, done, {}

def fetch_data():
    connection = pymysql.connect(**DB_CONFIG)
    query = """
        SELECT timestamp, close, volume FROM market_data 
        ORDER BY timestamp ASC
    """
    df = pd.read_sql(query, connection)
    df["ma10"] = df["close"].rolling(window=10).mean().fillna(method='bfill')
    connection.close()
    return df

def train_model(df):
    env = TradingEnv(df)
    model = PPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=10000)
    model.save("ppo_trading")
    return model

def predict_next_action(df):
    model = PPO.load("ppo_trading")
    env = TradingEnv(df)
    obs = env.reset()
    
    action, _ = model.predict(obs)
    return action

if __name__ == "__main__":
    df = fetch_data()
    train_model(df)
    
    latest_data = df.iloc[-1:].copy()
    action = predict_next_action(latest_data)
    
    action_map = {0: "SELL", 1: "HOLD", 2: "BUY"}
    predicted_action = action_map[action]
    
    result = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "predicted_action": predicted_action
    }
    
    with open("prediction_result.json", "w") as f:
        json.dump(result, f)
    
    print("Predicted Action:", predicted_action)
