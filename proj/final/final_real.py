# test1_매도 조건: 볼린저 상단 and rsi 65이상
# 매수: 자산의 5%, 매도: 보유 금액의 50%
# 기술적 지표 조건 + 거미줄 매수 전략
# 매수 거미줄 간격: 0.5%에 10개, 매도 거미줄 간격: 2%에 5개

from dotenv import load_dotenv
import os
import pyupbit
import time
import datetime
import numpy as np
import pandas as pd

# .env 파일 로드
load_dotenv()

# 환경 변수에서 API 키 불러오기
access_key = os.getenv("ACCESS_KEY")
secret_key = os.getenv("SECRET_KEY")

# Upbit 객체 생성
upbit = pyupbit.Upbit(access_key, secret_key)

def get_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_bollinger_bands(df, n=20, k=2):
    df['MA'] = df['close'].rolling(window=n).mean()
    df['STD'] = df['close'].rolling(window=n).std()
    df['Upper'] = df['MA'] + k * df['STD']
    df['Lower'] = df['MA'] - k * df['STD']
    return df

def get_current_price(ticker):
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def get_balance(ticker):
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            return float(b['balance']) if b['balance'] is not None else 0
    return 0

def buy_crypto_currency(ticker, krw):
    try:
        return upbit.buy_market_order(ticker, krw)
    except Exception as e:
        print(e)
        return None

def sell_crypto_currency(ticker, volume):
    try:
        return upbit.sell_market_order(ticker, volume)
    except Exception as e:
        print(e)
        return None

def main():
    ticker = "KRW-BTC"
    fee = 0.0005
    web_interval = 0.005  # 매수 거미줄 간격 (0.5%)
    sell_web_interval = 0.02  # 매도 거미줄 간격 (2%)
    web_orders = []  # 매수 거미줄 주문 리스트
    sell_web_orders = []  # 매도 거미줄 주문 리스트
    # initial_balance = get_balance("KRW")
    # 아래 while 루프 안에서 실시간 기준으로 업데이트
    initial_balance = get_balance("KRW") + get_balance("BTC") * get_current_price(ticker)
    is_web_active = False  # 매수 거미줄 활성화 여부
    is_sell_web_active = False  # 매도 거미줄 활성화 여부

    while True:
        try:
            now = datetime.datetime.now()
            df = pyupbit.get_ohlcv(ticker, interval="minute5", count=100)
            df = get_bollinger_bands(df)
            df['RSI'] = get_rsi(df['close'])
            current_price = get_current_price(ticker)
            rsi = df['RSI'].iloc[-1]
            lower_band = df['Lower'].iloc[-1]
            upper_band = df['Upper'].iloc[-1]
            krw = get_balance("KRW")
            btc = get_balance("BTC")
            portfolio_value = krw + (btc * current_price)
            profit_rate = ((portfolio_value - initial_balance) / initial_balance) * 100

            if not is_web_active and krw > 5000 and current_price < lower_band and rsi < 40:
                if is_sell_web_active:
                    sell_web_orders.clear()
                    is_sell_web_active = False
                    print("매도 거미줄이 삭제되었습니다.")
                is_web_active = True
                for j in range(1, 11):
                    order_price = current_price * (1 - web_interval * j)
                    order_amount = initial_balance * 0.025
                    if order_amount >= 5000:  # 최소 주문 금액 확인
                        web_orders.append({'price': order_price, 'amount': order_amount})
                    else:
                        print(f"거미줄 매수 금액이 최소 주문 금액 미만입니다. (금액: {order_amount})")
                        
            if is_web_active:
                for order in web_orders[:]:
                    if current_price <= order['price'] and order['amount'] >= 5000:
                        buy_result = buy_crypto_currency(ticker, order['amount'])
                        if buy_result:
                            web_orders.remove(order)
                            print(f"[매수 체결] {order['amount']:.0f} KRW @ {order['price']:.0f}원")
                if not web_orders:
                    is_web_active = False

            if not is_sell_web_active and btc > 0 and current_price > upper_band and rsi > 65:
                if is_web_active:
                    web_orders.clear()
                    is_web_active = False
                    print("매수 거미줄이 삭제되었습니다.")
                is_sell_web_active = True
                sell_amount = btc * 0.5
                sell_krw = sell_amount * current_price
                if sell_krw >= 5000:  # 최소 주문 금액 확인
                    for j in range(1, 6):
                        sell_price = current_price * (1 + sell_web_interval * j)
                        sell_web_orders.append({'price': sell_price, 'amount': sell_amount / 5})
                else:
                    print(f"매도 금액이 최소 주문 금액 미만입니다. (금액: {sell_krw})")


            if is_sell_web_active:
                for order in sell_web_orders[:]:
                    if current_price >= order['price'] and order['amount'] * current_price >= 5000:
                        sell_result = sell_crypto_currency(ticker, order['amount'])
                        if sell_result:
                            sell_web_orders.remove(order)
                            print(f"[매도 체결] {order['amount']:.6f} BTC @ {order['price']:.0f}원")
                if not sell_web_orders:
                    is_sell_web_active = False

            print(f"현재시간: {now} 현재가: {current_price:.0f} RSI: {rsi:.2f} 하한: {lower_band:.0f} 상한: {upper_band:.0f}")
            print(f"KRW 잔고: {krw:.0f} BTC 잔고: {btc:.8f}")
            print(f"포트폴리오 가치: {portfolio_value:.0f} 수익률: {profit_rate:.2f}%")
            print("-" * 50)

            time.sleep(10)

        except Exception as e:
            print(e)
            time.sleep(10)

if __name__ == '__main__':
    main()
