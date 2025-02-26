import pyupbit
import pandas as pd
import time
from datetime import datetime, timezone, timedelta

# RSI 계산 함수
def get_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# 볼린저 밴드 계산 함수(단기는 14~18이 적당 / 장기 20)
def get_bollinger_bands(df, n=18, k=2):
    df['MA'] = df['close'].rolling(window=n).mean()
    df['STD'] = df['close'].rolling(window=n).std()
    df['Upper'] = df['MA'] + k * df['STD']
    df['Lower'] = df['MA'] - k * df['STD']
    return df

# 이동평균선 계산 함수 (단기는 MA3, MA10 / 장기는 MA5, MA20)
def get_moving_averages(df):
    df['MA3'] = df['close'].rolling(window=3).mean()
    df['MA10'] = df['close'].rolling(window=10).mean()
    return df

# 거래 로그 저장 함수
def log_trade(action, price, amount, balance, timestamp, reason="", log_file="trade_log.txt"):
    with open(log_file, "a", encoding="utf-8") as log:
        log.write(f"{timestamp}, {action}, {price}, {amount:.4f}, {balance:.0f}, {reason}\n")

def real_time_trading(symbol="KRW-BTC", initial_balance=10000000, fee_rate=0.00139):
    # KST 시간대 설정
    KST = timezone(timedelta(hours=9))

    balance = initial_balance
    coin = 0
    trades = []
    web_orders = []  # 거미줄 주문 목록
    web_interval = 0.01  # 거미줄 간격 (1%)

    while True:
        try:
            # 최근 200개의 15분봉 데이터 가져오기 (실시간 데이터 사용)
            df = pyupbit.get_ohlcv(symbol, interval="minute5", count=100)

            # 기술적 지표 계산
            df = get_bollinger_bands(df)
            df['RSI'] = get_rsi(df['close'])
            df = get_moving_averages(df)

            current_price = df['close'].iloc[-1]
            rsi = df['RSI'].iloc[-1]
            lower_band = df['Lower'].iloc[-1]
            upper_band = df['Upper'].iloc[-1]

            current_time = datetime.now(KST)
            print(f"현재 시간: {current_time}, 가격: {current_price}, RSI: {rsi:.2f}")

            executed_trade = False

            # 거미줄 매수 주문 실행
            for order in web_orders[:]:
                if current_price <= order['price']:
                    buy_amount = order['amount']
                    coin_bought = buy_amount / current_price * (1 - fee_rate)
                    balance -= buy_amount
                    coin += coin_bought
                    trades.append(('buy', current_price, coin_bought, current_time))
                    web_orders.remove(order)
                    log_trade("매수", current_price, coin_bought, balance, current_time)
                    print(f"매수 실행: 가격 {current_price}, 수량 {coin_bought:.4f}")
                    executed_trade = True

            # 새로운 거미줄 매수 주문 생성
            buy_conditions = []
            if current_price < lower_band:
                buy_conditions.append(f"Lower Band({lower_band:.2f}) 충족")
            else:
                buy_conditions.append(f"Lower Band({lower_band:.2f}) 미충족")

            if rsi < 40:
                buy_conditions.append(f"RSI({rsi:.2f}) 충족")
            else:
                buy_conditions.append(f"RSI({rsi:.2f}) 미충족")

            if balance > 0 and current_price < lower_band and rsi < 40:
                for j in range(1, 21):  # 20개의 거미줄 주문 생성
                    order_price = current_price * (1 - web_interval * j)
                    order_amount = balance * 0.025  # 잔고의 5%씩 매수
                    web_orders.append({'price': order_price, 'amount': order_amount})
                print("새로운 거미줄 매수 주문 생성")
                executed_trade = True
            else:
                print(f"거래 보류: {', '.join(buy_conditions)}")
                log_trade("HOLD", current_price, 0, balance, current_time, reason=', '.join(buy_conditions))

            # 매도 신호
            if coin > 0 and current_price > upper_band and rsi > 60:
                sell_amount = coin * 0.5  # 보유 코인의 50% 매도
                balance += sell_amount * current_price * (1 - fee_rate)
                coin -= sell_amount
                trades.append(('sell', current_price, sell_amount, current_time))
                log_trade("매도", current_price, sell_amount, balance, current_time)
                print(f"매도 실행: 가격 {current_price}, 수량 {sell_amount:.4f}")
                executed_trade = True

            print(f"현재 잔고: {balance:.0f} 원, 코인 보유량: {coin:.4f}")
            print("------------------------")

            time.sleep(300)  # 15분 대기

        except Exception as e:
            print(f"에러 발생: {e}")
            time.sleep(300)  # 에러 발생 시 15분 대기 후 재시도

# 실시간 거래 시작
real_time_trading()

