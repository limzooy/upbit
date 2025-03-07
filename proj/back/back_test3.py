# test_3 매도 조건: 평단가 수익률 2%이상 매도 and 볼린저 상단 and rsi 65이상
# 매수: 자산의 2.5%, 매도: 보유 금액의 50%
# 매수 거미줄 간격: 0.5%, 매도 거미줄 간격: 1%
# 매수/매도 전략에 거미줄 전략이 적용 O

import pandas as pd
import numpy as np

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

def backtest(df, initial_balance=10000000):
    balance = initial_balance
    btc = 0
    fee = 0.0005
    buy_web_interval = 0.005  # 매수 거미줄 간격 (0.5%)
    sell_web_interval = 0.01  # 매도 거미줄 간격 (1%)
    buy_orders = []
    sell_orders = []
    is_buy_web_active = False
    is_sell_web_active = False
    trade_history = []
    total_buy_cost = 0
    average_buy_price = 0

    for i in range(len(df)):
        current_price = df['close'].iloc[i]
        rsi = df['RSI'].iloc[i]
        lower_band = df['Lower'].iloc[i]
        upper_band = df['Upper'].iloc[i]

        portfolio_value = balance + (btc * current_price)
        order_amount = portfolio_value * 0.025  # 자산의 2.5%

        # 거미줄 매수 주문 실행
        if is_buy_web_active:
            for order in buy_orders[:]:
                if current_price <= order['price']:
                    if balance >= order['amount']:
                        btc_to_buy = (order['amount'] / current_price) * (1 - fee)
                        balance -= order['amount']
                        btc += btc_to_buy
                        total_buy_cost += order['amount']
                        average_buy_price = total_buy_cost / btc if btc > 0 else 0
                        trade_history.append(('Buy', current_price, btc_to_buy, balance, btc))
                        buy_orders.remove(order)
                    else:
                        is_buy_web_active = False
                        buy_orders.clear()
                        break

            if not buy_orders:
                is_buy_web_active = False

        # 거미줄 매도 주문 실행
        if is_sell_web_active:
            for order in sell_orders[:]:
                if current_price >= order['price']:
                    if btc >= order['amount']:
                        sell_value = order['amount'] * current_price
                        balance += sell_value * (1 - fee)
                        btc -= order['amount']
                        total_buy_cost -= order['amount'] * average_buy_price
                        average_buy_price = total_buy_cost / btc if btc > 0 else 0
                        trade_history.append(('Sell', current_price, order['amount'], balance, btc))
                        sell_orders.remove(order)
                    else:
                        is_sell_web_active = False
                        sell_orders.clear()
                        break

            if not sell_orders:
                is_sell_web_active = False

        # 새로운 거미줄 매수 주문 생성
        if not is_buy_web_active and not is_sell_web_active and balance > order_amount and current_price < lower_band and rsi < 40:
            is_buy_web_active = True
            sell_orders.clear()  # 매도 주문 초기화
            for j in range(1, 6):  # 5개의 거미줄 주문 생성
                order_price = current_price * (1 - buy_web_interval * j)
                buy_orders.append({'price': order_price, 'amount': order_amount})

        # 새로운 거미줄 매도 주문 생성 (평단가 수익률 2% 이상 AND 볼린저 상단 AND RSI 65 이상일 때)
        if not is_sell_web_active and not is_buy_web_active and btc > 0:
            profit_rate = (current_price - average_buy_price) / average_buy_price
            if profit_rate >= 0.02 and current_price > upper_band and rsi > 65:  # 수정된 조건
                is_sell_web_active = True
                buy_orders.clear()  # 매수 주문 초기화
                total_sell_amount = btc * 0.5  # 보유 코인의 50%
                for j in range(1, 6):  # 5개의 거미줄 주문 생성
                    order_price = current_price * (1 + 0.02 + sell_web_interval * j)  # 기본 수익률 2% + 거미줄 간격 1%씩
                    sell_amount = total_sell_amount / 5  # 각 주문당 총 매도량의 1/5
                    sell_orders.append({'price': order_price, 'amount': sell_amount})

    # 최종 자산 평가
    final_balance = balance + btc * df['close'].iloc[-1]
    return final_balance, trade_history


def main():
    # CSV 파일 로드
    df = pd.read_csv('C:\\Users\\limjy\\upbit\\proj\\btc_5m_2023-2025.csv')
    df['datetime'] = pd.to_datetime(df['timestamp'])
    df.set_index('datetime', inplace=True)

    # 기술적 지표 계산
    df = get_bollinger_bands(df)
    df['RSI'] = get_rsi(df['close'])

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
    
    profit_rate = ((final_balance / initial_balance) - 1) * 100
    print(f"Final profit rate: {profit_rate:.2f}%")

    # 거래 기록을 DataFrame으로 변환하여 CSV로 저장
    trade_df = pd.DataFrame(trade_history, columns=['Type', 'Price', 'Amount', 'Balance', 'BTC'])
    trade_df.to_csv('trade_backtest_v3.csv', index=False)
    print("Trade history saved to 'trade_backtest_v3.csv'")

if __name__ == '__main__':
    main()
