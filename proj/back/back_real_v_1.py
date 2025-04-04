# real_v_1.py 백테스트
# 기술적 지표 만족 시 거미줄 전략 활성화

import pandas as pd
import numpy as np

# CSV 파일 로드
def load_data(file_path):
    df = pd.read_csv(file_path, index_col='timestamp', parse_dates=True)
    df = df[['open', 'high', 'low', 'close', 'volume']]
    return df

# RSI 계산
def get_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# 볼린저 밴드 계산
def get_bollinger_bands(df, n=20, k=2):
    df['MA'] = df['close'].rolling(window=n).mean()
    df['STD'] = df['close'].rolling(window=n).std()
    df['Upper'] = df['MA'] + k * df['STD']
    df['Lower'] = df['MA'] - k * df['STD']
    return df

# 백테스트 실행
def backtest(df, initial_balance=1000000, web_interval=0.005, sell_web_interval=0.02):
    balance = initial_balance
    btc = 0
    web_orders = []
    sell_web_orders = []
    is_web_active = False
    is_sell_web_active = False
    trade_log = []
    
    # 거래 횟수 카운터 추가
    buy_count = 0
    sell_count = 0

    df = get_bollinger_bands(df)
    df['RSI'] = get_rsi(df['close'])
    
    for i in range(len(df)):
        current_price = df['close'].iloc[i]
        rsi = df['RSI'].iloc[i]
        lower_band = df['Lower'].iloc[i]
        upper_band = df['Upper'].iloc[i]
        
        # 매수 거미줄 생성 조건
        if not is_web_active and balance > 5000 and current_price < lower_band and rsi < 40:
            sell_web_orders.clear()
            is_sell_web_active = False
            is_web_active = True
            for j in range(1, 11):
                order_price = current_price * (1 - web_interval * j)
                order_amount = initial_balance * 0.05 / current_price
                if order_amount * order_price >= 5000:  # 최소 주문 금액 확인
                    web_orders.append({'price': order_price, 'amount': order_amount})
        
        # 매수 체결
        for order in web_orders[:]:
            if current_price <= order['price'] and balance >= order['amount'] * current_price:
                if order['amount'] * current_price >= 5000:  # 최소 주문 금액 확인
                    buy_count += 1
                    balance -= order['amount'] * current_price
                    btc += order['amount']
                    web_orders.remove(order)
                    trade_log.append((df.index[i], 'BUY', current_price, order['amount']))
                
        if not web_orders:
            is_web_active = False
        
        # 매도 거미줄 생성 조건
        avg_price = (initial_balance - balance) / btc if btc > 0 else 0
        profit_rate = (current_price - avg_price) / avg_price * 100 if avg_price > 0 else 0
        if not is_sell_web_active and btc > 0 and current_price > upper_band and rsi > 65 and profit_rate >= 2:
            web_orders.clear()
            is_web_active = False
            is_sell_web_active = True
            sell_amount = btc * 0.5
            for j in range(1, 6):
                sell_price = current_price * (1 + sell_web_interval * j)
                sell_web_orders.append({'price': sell_price, 'amount': sell_amount / 5})
        
        # 매도 체결
        for order in sell_web_orders[:]:
            if current_price >= order['price'] and btc >= order['amount']:
                if order['amount'] * current_price >= 5000:  # 최소 주문 금액 확인
                    sell_count += 1
                    balance += order['amount'] * current_price
                    btc -= order['amount']
                    sell_web_orders.remove(order)
                    trade_log.append((df.index[i], 'SELL', current_price, order['amount']))
        if not sell_web_orders:
            is_sell_web_active = False
    
    final_value = balance + (btc * df['close'].iloc[-1])
    profit = (final_value - initial_balance) / initial_balance * 100
    
    # 거래 기록을 파일로 저장
    with open("backtest_result_v_1(2024-2025).txt", "w") as file:
        file.write(f"최종 자산 가치: {final_value:.0f} KRW\n")
        file.write(f"총 수익률: {profit:.2f}%\n")
        file.write(f"총 매수 횟수: {buy_count}회\n")  # 파일에 매수 횟수 기록
        file.write(f"총 매도 횟수: {sell_count}회\n")  # 파일에 매도 횟수 기록

        file.write("거래 기록:\n")
        for log in trade_log:
            file.write(f"{log[0]} {log[1]} 가격: {log[2]:.0f} 수량: {log[3]:.8f}\n")
    
    return trade_log, final_value, profit, buy_count, sell_count

# 실행
data_path = "backtest_data/KRW-BTC_5min_2024-2025.csv"
df = load_data(data_path)
trade_log, final_value, profit, buy_count, sell_count = backtest(df)

# 결과 출력
print(f"최종 자산 가치: {final_value:.0f} KRW")
print(f"총 수익률: {profit:.2f}%")
print(f"총 매수 횟수: {buy_count}회")  # 매수 횟수 출력
print(f"총 매도 횟수: {sell_count}회")  # 매도 횟수 출력