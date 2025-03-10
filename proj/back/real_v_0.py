# test0_매도 조건: 볼린저 상단 and rsi 65이상
# 매수: 자산의 2.5%, 매도: 보유 금액의 50%
# 기술적 지표 조건 + 거미줄 매수 전략
# 매도 전략에는 거미줄 전략이 적용 X !!!!

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

def get_moving_averages(df):
    df['MA5'] = df['close'].rolling(window=5).mean()
    df['MA20'] = df['close'].rolling(window=20).mean()
    return df

def get_current_price(ticker):
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def get_balance(ticker):
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
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

def cancel_all_orders(ticker):
    """모든 미체결 주문을 취소합니다."""
    try:
        orders = upbit.get_order(ticker)
        for order in orders:
            upbit.cancel_order(order['uuid'])
        print(f"모든 {ticker} 주문이 취소되었습니다.")
    except Exception as e:
        print(f"주문 취소 중 오류 발생: {e}")

def main():
    ticker = "KRW-BTC"
    fee = 0.0005
    web_interval = 0.005  # 거미줄 간격 (0.5%)
    web_orders = []  # 거미줄 주문 목록
    initial_balance = get_balance("KRW")  # 초기 잔고 저장
    is_web_active = False  # 거미줄 활성화 상태

    while True:
        try:
            now = datetime.datetime.now()
            df = pyupbit.get_ohlcv(ticker, interval="minute5", count=100)

            df = get_bollinger_bands(df)
            df['RSI'] = get_rsi(df['close'])
            df = get_moving_averages(df)

            current_price = get_current_price(ticker)
            rsi = df['RSI'].iloc[-1]
            lower_band = df['Lower'].iloc[-1]
            upper_band = df['Upper'].iloc[-1]

            krw = get_balance("KRW")
            btc = get_balance("BTC")

            # 포트폴리오 가치 계산
            portfolio_value = krw + (btc * current_price)
            profit_rate = ((portfolio_value - initial_balance) / initial_balance) * 100

            # 거미줄 매수 주문 실행
            if is_web_active:
                for order in web_orders[:]:
                    if current_price <= order['price'] and order['amount'] >= 5000::
                        buy_result = buy_crypto_currency(ticker, order['amount'])
                        if buy_result:
                            print(f"매수 주문 체결: 가격 {current_price}원, 금액 {order['amount']}원")
                            web_orders.remove(order)

                # 모든 거미줄 주문이 체결되면 거미줄 비활성화
                if not web_orders:
                    is_web_active = False
                    print("모든 거미줄 주문이 체결되었습니다. 거미줄 비활성화.")

            # 새로운 거미줄 매수 주문 생성
            if not is_web_active and krw > 5000 and current_price < lower_band and rsi < 40:
                is_web_active = True
                for j in range(1, 11):  # 10개의 거미줄 주문 생성
                    order_price = current_price * (1 - web_interval * j)
                    order_amount = initial_balance * 0.025  # 초기 잔고의 2.5%씩 매수
                    if order_amount >= 5000:  # 최소 주문 금액 확인
                        web_orders.append({'price': order_price, 'amount': order_amount})
                        print(f"거미줄 매수 주문 생성: 가격 {order_price}원, 금액 {order_amount}원")
                    else:
                        print("거미줄 매수 금액이 최소 주문 금액 미만입니다.")

            # 매도 신호
            if btc > 0 and current_price > upper_band and rsi > 65:
                sell_amount = btc * 0.5  # 보유 코인의 50% 매도
                sell_result = sell_crypto_currency(ticker, sell_amount)
                if sell_krw >= 5000:  # 최소 주문 금액 확인
                    sell_result = sell_crypto_currency(ticker, sell_amount)
                    if sell_result:
                        print(f"매도 주문 체결: 가격 {current_price}원, 수량 {sell_amount}")
                        cancel_all_orders(ticker)
                        web_orders.clear()
                        is_web_active = False
                        print("매도 후 거미줄 초기화 완료")
                else:
                    print("매도 금액이 최소 주문 금액 미만입니다.")

            # 출력 형식 수정
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