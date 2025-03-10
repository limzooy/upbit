# real_v_0.py 백테스트

import pandas as pd
import numpy as np
import datetime

# CSV 데이터 로드
df = pd.read_csv("backtest_data/KRW-BTC_5min_2020-01-01_2020-12-31.csv")
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp', inplace=True)

# RSI 계산 함수
def get_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# 볼린저 밴드 계산 함수
def get_bollinger_bands(df, n=20, k=2):
    df['MA'] = df['close'].rolling(window=n).mean()
    df['STD'] = df['close'].rolling(window=n).std()
    df['Upper'] = df['MA'] + k * df['STD']
    df['Lower'] = df['MA'] - k * df['STD']
    return df

# 이동 평균선 계산 함수
def get_moving_averages(df):
    df['MA5'] = df['close'].rolling(window=5).mean()
    df['MA20'] = df['close'].rolling(window=20).mean()
    return df

# 데이터 처리 및 지표 계산
df = get_bollinger_bands(df)
df['RSI'] = get_rsi(df['close'])
df = get_moving_averages(df)

# 백테스트 변수 설정
initial_balance = 1000000  # 초기 자본 (100만원)
krw_balance = initial_balance
btc_balance = 0
fee = 0.0005
web_interval = 0.005  # 거미줄 매매 간격
web_orders = []  # 거미줄 주문 리스트
is_web_active = False
trade_log = []

# 거래 횟수 카운터 추가
buy_count = 0
sell_count = 0

# 백테스트 실행
for i in range(len(df)):
    current_price = df.iloc[i]['close']
    rsi = df.iloc[i]['RSI']
    lower_band = df.iloc[i]['Lower']
    upper_band = df.iloc[i]['Upper']
    timestamp = df.index[i]

    # 거미줄 매수 주문 처리
    if is_web_active:
        for order in web_orders[:]:
            if current_price <= order['price'] and order['amount'] >= 5000:
                buy_count += 1
                btc_balance += order['amount'] / current_price
                krw_balance -= order['amount']
                trade_log.append((timestamp, "매수", current_price, order['amount'] / current_price))
                web_orders.remove(order)
        if not web_orders:
            is_web_active = False

    # 거미줄 매수 주문 생성
    if not is_web_active and krw_balance > 5000 and current_price < lower_band and rsi < 40:
        is_web_active = True
        for j in range(1, 11):
            order_price = current_price * (1 - web_interval * j)
            order_amount = initial_balance * 0.025
            if order_amount >= 5000:  # 최소 주문 금액 확인
                web_orders.append({'price': order_price, 'amount': order_amount})
            # else:
            #     print(f"거미줄 매수 금액이 최소 주문 금액 미만입니다. (금액: {order_amount})")
    
    # 매도 조건
    if btc_balance > 0 and current_price > upper_band and rsi > 65:
        sell_amount = btc_balance * 0.5
        sell_krw = sell_amount * current_price
        if sell_krw >= 5000:  # 최소 주문 금액 확인
            sell_count += 1
            krw_balance += sell_amount * current_price * (1 - fee)
            btc_balance -= sell_amount
            trade_log.append((timestamp, "매도", current_price, sell_amount))
            web_orders.clear()
            is_web_active = False
        # else:
        #     print(f"매도 금액이 최소 주문 금액 미만입니다. (금액: {sell_krw})")

# 최종 결과 출력
final_value = krw_balance + (btc_balance * df.iloc[-1]['close'])
profit_rate = ((final_value - initial_balance) / initial_balance) * 100
print(f"최종 포트폴리오 가치: {final_value:.0f} KRW")
print(f"총 수익률: {profit_rate:.2f}%")
print(f"총 매수 횟수: {buy_count}회")  # 매수 횟수 출력
print(f"총 매도 횟수: {sell_count}회")  # 매도 횟수 출력

# 거래 기록을 파일로 저장
with open("backtest_result_v_3.txt", "w") as file:
    file.write(f"최종 자산 가치: {final_value:.0f} KRW\n")
    file.write(f"총 수익률: {profit_rate:.2f}%\n")
    file.write(f"총 매수 횟수: {buy_count}회\n")  # 파일에 매수 횟수 기록
    file.write(f"총 매도 횟수: {sell_count}회\n")  # 파일에 매도 횟수 기록
    # file.write("거래 기록:\n")
    # for log in trade_log:
    #     file.write(f"{log[0]} {log[1]} 가격: {log[2]:.0f} 수량: {log[3]:.8f}\n")
