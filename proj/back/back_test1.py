# (기존)test1_매도 조건: 볼린저 상단 and rsi 65이상
# 매수: 자산의 2.5%, 매도: 보유 금액의 50%
# 기술적 지표 조건 + 거미줄 매수 전략
# 매도 전략에는 거미줄 전략이 적용 X

import pandas as pd
import numpy as np

def get_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_bollinger_bands(df, n=20, k=2):
    df['MA'] = df['trade_price'].rolling(window=n).mean()
    df['STD'] = df['trade_price'].rolling(window=n).std()
    df['Upper'] = df['MA'] + k * df['STD']
    df['Lower'] = df['MA'] - k * df['STD']
    return df

def backtest(df, initial_balance=10000000):
    balance = initial_balance
    btc = 0
    fee = 0.0005
    web_interval = 0.005  # 거미줄 간격 (0.5%)
    web_orders = []  # 거미줄 주문 목록
    is_web_active = False  # 거미줄 활성화 상태
    trade_history = []

    for i in range(len(df)):
        current_price = df['trade_price'].iloc[i]
        rsi = df['RSI'].iloc[i]
        lower_band = df['Lower'].iloc[i]
        upper_band = df['Upper'].iloc[i]

        # 포트폴리오 가치 계산
        portfolio_value = balance + (btc * current_price)
        order_amount = portfolio_value * 0.025  # 자산의 2.5%

        # 거미줄 매수 주문 실행
        if is_web_active:
            for order in web_orders[:]:
                if current_price <= order['price']:
                    if balance >= order['amount']:
                        btc_to_buy = (order['amount'] / current_price) * (1 - fee)
                        balance -= order['amount']
                        btc += btc_to_buy
                        trade_history.append(('Buy', current_price, btc_to_buy, balance, btc))
                        web_orders.remove(order)

            # 모든 거미줄 주문이 체결되면 거미줄 비활성화
            if not web_orders:
                is_web_active = False

        # 새로운 거미줄 매수 주문 생성
        if not is_web_active and balance > order_amount and current_price < lower_band and rsi < 40:
            if not web_orders:  # 기존 거미줄이 남아 있는 경우 중복 생성 방지
                is_web_active = True
                for j in range(1, 11):  # 10개의 거미줄 주문 생성
                    order_price = current_price * (1 - web_interval * j)
                    web_orders.append({'price': order_price, 'amount': order_amount})

        # 매도 조건
        if btc > 0 and current_price > upper_band and rsi > 65:
            sell_amount = btc * 0.5  # 보유 코인의 50% 매도
            sell_value = sell_amount * current_price
            balance += sell_value * (1 - fee)
            btc -= sell_amount
            trade_history.append(('Sell', current_price, sell_amount, balance, btc))
            web_orders.clear()
            is_web_active = False

    # 최종 자산 평가
    final_balance = balance + btc * df['trade_price'].iloc[-1]
    return final_balance, trade_history

def main():
    # CSV 파일 로드
    df = pd.read_csv('upbit_candle_data(3).csv')
    df['datetime'] = pd.to_datetime(df['timestamp'])
    df.set_index('datetime', inplace=True)

    # 기술적 지표 계산
    df = get_bollinger_bands(df)
    df['RSI'] = get_rsi(df['trade_price'])

    # 백테스트 실행
    initial_balance = 10000000  # 1천만원
    final_balance, trade_history = backtest(df, initial_balance)

    # 결과 출력
    print(f"Initial Balance: {initial_balance:,.0f} KRW")
    print(f"Final Balance: {final_balance:,.0f} KRW")
    print(f"Profit: {final_balance - initial_balance:,.0f} KRW")
    print(f"Return: {((final_balance / initial_balance) - 1) * 100:.2f}%")
    print(f"Number of trades: {len(trade_history)}")
    
    buy_count = sum(1 for trade in trade_history if trade[0] == 'Buy')
    sell_count = sum(1 for trade in trade_history if trade[0] == 'Sell')
    print(f"Number of buy trades: {buy_count}")
    print(f"Number of sell trades: {sell_count}")

    # 거래 기록을 DataFrame으로 변환하여 CSV로 저장
    trade_df = pd.DataFrame(trade_history, columns=['Type', 'Price', 'Amount', 'Balance', 'BTC'])
    trade_df.to_csv('trade_backtest_result.csv', index=False)
    print("Trade history saved to 'trade_backtest_(3).csv'")

if __name__ == '__main__':
    main()
