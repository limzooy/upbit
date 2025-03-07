# 매도 조건에 문제있음!!!!

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
        if isinstance(b, dict) and b.get('currency') == ticker:
            if b.get('balance') is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def buy_crypto_currency(ticker, krw):
    try:
        krw_balance = get_balance("KRW")
        if krw_balance < krw:
            print(f"잔고 부족: 필요 금액 {krw}원, 현재 잔고 {krw_balance}원")
            return None
        return upbit.buy_market_order(ticker, krw)
    except Exception as e:
        print(f"매수 중 오류 발생: {e}")
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
    if initial_balance == 0:
        print("경고: 초기 KRW 잔고가 0입니다. 거래를 시작하기 전에 잔고를 확인하세요.")
    is_web_active = False  # 거미줄 활성화 상태
    fixed_order_amount = 10000  # 고정 주문 금액 (원)

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
                    if current_price <= order['price']:
                        buy_result = buy_crypto_currency(ticker, fixed_order_amount)
                        if buy_result:
                            print(f"매수 주문 체결: 가격 {current_price}원, 금액 {fixed_order_amount}원")
                            web_orders.remove(order)
                        else:
                            print("매수 주문 실패: 잔고 부족 또는 기타 오류")
                            is_web_active = False
                            web_orders.clear()
                            print("거미줄 매수 중단: 잔고 부족")
                            break

                # 모든 거미줄 주문이 체결되면 거미줄 비활성화
                if not web_orders:
                    is_web_active = False
                    print("모든 거미줄 주문이 체결되었습니다. 거미줄 비활성화.")

            # 새로운 거미줄 매수 주문 생성
            if not is_web_active and krw > fixed_order_amount and current_price < lower_band and rsi < 40:
                is_web_active = True
                for j in range(1, 6):  # 5개의 거미줄 주문 생성
                    order_price = current_price * (1 - web_interval * j)
                    web_orders.append({'price': order_price, 'amount': fixed_order_amount})
                    print(f"거미줄 매수 주문 생성: 가격 {order_price}원, 금액 {fixed_order_amount}원")
            
            # 매도 신호
            if btc > 0 and current_price > upper_band and rsi > 60:
                sell_amount = btc * 0.5  # 보유 코인의 50% 매도
                sell_result = sell_crypto_currency(ticker, sell_amount)
                if sell_result:
                    print(f"매도 주문 체결: 가격 {current_price}원, 수량 {sell_amount}")
                    # 매도 후 거미줄 초기화
                    cancel_all_orders(ticker)
                    web_orders.clear()
                    is_web_active = False
                    print("매도 후 거미줄 초기화 완료")

            # 출력 형식 수정
            print(f"현재시간: {now} 현재가: {current_price:.0f}")
            print(f"RSI: {rsi:.2f} 하한: {lower_band:.0f} 상한: {upper_band:.0f}")
            print(f"볼린저 밴드 조건: {'충족' if current_price < lower_band else '미충족'}")
            print(f"RSI 조건: {'충족' if rsi < 40 else '미충족'}")
            print(f"KRW 잔고: {krw:.0f} BTC 잔고: {btc:.8f}")
            print(f"포트폴리오 가치: {portfolio_value:.0f} 수익률: {profit_rate:.2f}%")
            print("-" * 50)

            time.sleep(10)

        except Exception as e:
            print(f"예외 발생: {e}")
            time.sleep(10)

if __name__ == '__main__':
    main()
