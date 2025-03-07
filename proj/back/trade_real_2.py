# 퍼플렉시티
from dotenv import load_dotenv
import os
import pyupbit
import time
import datetime
import numpy as np
import pandas as pd
import logging
from logging.handlers import TimedRotatingFileHandler

# .env 파일 로드
load_dotenv()

access_key = os.getenv("ACCESS_KEY")
secret_key = os.getenv("SECRET_KEY")

# Upbit 객체 생성
upbit = pyupbit.Upbit(access_key, secret_key)

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    file_handler = TimedRotatingFileHandler(
        'trading_log.txt', when='midnight', interval=1, backupCount=7, encoding='utf-8'
    )
    file_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(file_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

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
            return float(b['balance']) if b.get('balance') else 0
    return 0

def buy_crypto_currency(ticker, krw):
    try:
        krw_balance = get_balance("KRW")
        if krw_balance < krw:
            print(f"잔고 부족: 필요 금액 {krw}원, 현재 잔고 {krw_balance}원")
            return None
        return upbit.buy_market_order(ticker, krw)
    except Exception as e:
        print(f"매수 오류: {e}")
        return None

def sell_crypto_currency(ticker, volume):
    try:
        return upbit.sell_market_order(ticker, volume)
    except Exception as e:
        print(e)
        return None

def cancel_all_orders(ticker):
    try:
        orders = upbit.get_order(ticker)
        for order in orders:
            upbit.cancel_order(order['uuid'])
        print(f"모든 {ticker} 주문 취소 완료")
    except Exception as e:
        print(f"주문 취소 오류: {e}")

def main():
    logger = setup_logger()
    ticker = "KRW-BTC"
    
    try:
        logger.info("======= 자동 매매 시작 =======")
        
        # 초기 파라미터 설정
        buy_interval = 0.005
        sell_interval = 0.01
        buy_orders = []
        sell_orders = []
        initial_krw = get_balance("KRW")
        is_buy_active = False
        is_sell_active = False
        avg_price = 0

        while True:
            try:
                # 데이터 수집
                now = datetime.datetime.now()
                df = pyupbit.get_ohlcv(ticker, "minute5", count=100)
                df = get_bollinger_bands(df)
                df['RSI'] = get_rsi(df['close'])
                df = get_moving_averages(df)
                current_price = get_current_price(ticker)
                rsi = df['RSI'].iloc[-1]
                lower_band = df['Lower'].iloc[-1]
                upper_band = df['Upper'].iloc[-1]
                btc_balance = get_balance("BTC")
                krw_balance = get_balance("KRW")
                portfolio_value = krw_balance + (btc_balance * current_price)
                profit_rate = ((portfolio_value - initial_krw) / initial_krw * 100) if initial_krw > 0 else 0

                # 매수 로직
                if is_buy_active:
                    for order in buy_orders[:]:
                        if current_price <= order['price']:
                            # 동적 주문 금액 사용 (order['amount'] 사용)
                            result = buy_crypto_currency(ticker, order['amount'])
                            if result:
                                logger.info(f"매수 체결: {order['price']:.0f}원 ({order['amount']:,.0f}원)")
                                new_btc = order['amount'] / current_price
                                avg_price = ((avg_price * btc_balance) + (current_price * new_btc)) / (btc_balance + new_btc)
                                buy_orders.remove(order)
                            else:
                                buy_orders.clear()
                                is_buy_active = False
                                break

                # 매도 로직 (변경 없음)
                if is_sell_active and btc_balance > 0:
                    for order in sell_orders[:]:
                        if current_price >= order['price']:
                            sell_volume = btc_balance * 0.5
                            result = sell_crypto_currency(ticker, sell_volume)
                            if result:
                                logger.info(f"매도 체결: {order['price']:.0f}원")
                                avg_price = avg_price * (btc_balance / (btc_balance - sell_volume))
                                sell_orders.remove(order)
                            else:
                                sell_orders.clear()
                                is_sell_active = False
                                break

                # 거미줄 생성 조건 (변경 부분)
                if not is_buy_active:
                    dynamic_order_amount = max(krw_balance * 0.025, 5000)  # 2.5%, 최소 5,000원
                    if krw_balance >= dynamic_order_amount:
                        if current_price < lower_band and rsi < 40:
                            cancel_all_orders(ticker)
                            max_orders = min(int(krw_balance // dynamic_order_amount), 5)  # 최대 5주문
                            buy_orders = [{
                                'price': current_price * (1 - buy_interval * j),
                                'amount': dynamic_order_amount
                            } for j in range(1, max_orders+1)]
                            is_buy_active = True
                            logger.info(f"매수 거미줄 생성 ({max_orders}개 x {dynamic_order_amount:,.0f}원)")

                if not is_sell_active and btc_balance > 0 and avg_price > 0:
                    profit = ((current_price - avg_price)/avg_price)*100
                    if profit >= 2:
                        cancel_all_orders(ticker)
                        base_price = avg_price * 1.02
                        sell_orders = [{
                            'price': base_price * (1 + sell_interval * j)
                        } for j in range(10) if (base_price * (1 + sell_interval * j)) <= current_price * 1.5]
                        is_sell_active = True
                        logger.info(f"매도 거미줄 생성: {len(sell_orders)}개")

                # 로깅
                logger.info(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 현재가: {current_price:,.0f}원")
                logger.info(f"[시장 현황] RSI: {rsi:.2f} | 밴드: {lower_band:.0f}~{upper_band:.0f}")
                logger.info(f"[조건 판단] 볼린저: {'충족' if current_price < lower_band else '미충족'} | RSI: {'충족' if rsi < 40 else '미충족'}")
                logger.info(f"[잔고] KRW: {krw_balance:,.0f}원 | BTC: {btc_balance:.8f}")
                logger.info(f"[포트폴리오] 총액: {portfolio_value:,.0f}원 | 수익률: {profit_rate:.2f}%")
                logger.info("-" * 60)
                time.sleep(10)

            except Exception as e:
                logger.error(f"오류 발생: {str(e)}", exc_info=True)
                time.sleep(30)

    except KeyboardInterrupt:
        logger.info("사용자 종료")
    finally:
        logger.info("======= 시스템 종료 =======")

if __name__ == "__main__":
    main()
