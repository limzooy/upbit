# real_v_3.py 백테스트

from datetime import datetime
import pandas as pd
import numpy as np

# CSV 파일 로드
def load_data(file_path):
    df = pd.read_csv(file_path, index_col='timestamp', parse_dates=True)
    df = df[['open', 'high', 'low', 'close', 'volume']]
    return df

# 기술적 지표 계산
def calculate_indicators(df):
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
    
    df = get_bollinger_bands(df)
    df['RSI'] = get_rsi(df['close'])
    return df

# 백테스트 실행
def backtest(df, initial_balance=10000000, fee=0.0005):
    balance = initial_balance
    btc = 0.0
    web_orders = []
    sell_web_orders = []
    is_web_active = False
    is_sell_web_active = False
    trade_history = []
    avg_buy_price = 0.0
    buy_count = 0  # 매수 횟수 카운터
    sell_count = 0  # 매도 횟수 카운터

    df = calculate_indicators(df)

    for i in range(len(df)):
        current_data = df.iloc[i]
        current_price = current_data['close']
        current_time = df.index[i]
        rsi = current_data['RSI']
        lower_band = current_data['Lower']
        upper_band = current_data['Upper']

        # 매수 거미줄 생성
        if not is_web_active and balance > 5000:
            if current_price < lower_band and rsi < 40:
                sell_web_orders.clear()
                is_sell_web_active = False
                is_web_active = True
                for j in range(1, 11):
                    order_price = current_price * (1 - 0.01 * j)
                    order_krw = initial_balance * 0.05
                    if order_krw >= 5000:  # 최소 주문 금액 확인
                        web_orders.append({
                            'price': order_price,
                            'amount': order_krw / current_price
                        })
                    # else:
                    #     print(f"거미줄 매수 금액이 최소 주문 금액 미만입니다. (금액: {order_krw})")
                trade_history.append((current_time, "BUY WEB 생성", current_price, 0))


        # 매수 체결
        executed = []
        for order in web_orders:
            if current_price <= order['price']:
                cost = order['amount'] * current_price * (1 + fee)
                if balance >= cost and cost >= 5000:  # 최소 주문 금액 확인
                    balance -= cost
                    btc += order['amount']
                    avg_buy_price = ((avg_buy_price * (btc - order['amount'])) + 
                                    (current_price * order['amount'])) / btc
                    executed.append(order)
                    trade_history.append((current_time, "BUY", current_price, order['amount']))
                    buy_count += 1  # 매수 횟수 증가
        for order in executed:
            web_orders.remove(order)
        if not web_orders and is_web_active:
            is_web_active = False
            trade_history.append((current_time, "BUY WEB 해제", current_price, 0))
        
        # 매도 조건 계산
        profit_rate = ((current_price - avg_buy_price)/avg_buy_price)*100 if avg_buy_price > 0 else 0

        # 매도 거미줄 생성
        if not is_sell_web_active and btc > 0:
            if current_price > upper_band and rsi > 65 and profit_rate >= 2:
                web_orders.clear()
                is_web_active = False
                is_sell_web_active = True
                sell_amount = btc * 0.5
                for j in range(1, 6):
                    order_price = current_price * (1 + 0.02 * j)
                    sell_web_orders.append({
                        'price': order_price,
                        'amount': sell_amount / 5
                    })
                trade_history.append((current_time, "SELL WEB 생성", current_price, 0))

        # 매도 체결
        executed_sell = []
        for order in sell_web_orders:
            if current_price >= order['price']:
                if btc >= order['amount'] and order['amount'] * current_price >= 5000:  # 최소 주문 금액 확인
                    balance += order['amount'] * current_price * (1 - fee)
                    btc -= order['amount']
                    executed_sell.append(order)
                    trade_history.append((current_time, "SELL", current_price, order['amount']))
                    sell_count += 1  # 매도 횟수 증가
        for order in executed_sell:
            sell_web_orders.remove(order)
        if not sell_web_orders and is_sell_web_active:
            is_sell_web_active = False
            trade_history.append((current_time, "SELL WEB 해제", current_price, 0))
            
    # 결과 계산
    final_value = balance + (btc * df['close'].iloc[-1])
    total_return = (final_value - initial_balance) / initial_balance * 100
    
    # 결과 리포트 생성
    result = {
        'initial_balance': initial_balance,
        'final_balance': final_value,
        'return_rate': total_return,
        'trade_history': trade_history,
        'remaining_btc': btc,
        'remaining_krw': balance,
        'buy_count': buy_count,
        'sell_count': sell_count
    }
    
    return result

# 실행 및 결과 저장
if __name__ == "__main__":
    df = load_data("backtest_data/KRW-BTC_5min_2024-2025.csv")
    result = backtest(df)

    # 콘솔 출력
    print(f"초기 자본: {result['initial_balance']:,.0f} KRW")
    print(f"최종 자산: {result['final_balance']:,.0f} KRW")
    print(f"수익률: {result['return_rate']:.2f}%")
    print(f"잔여 BTC: {result['remaining_btc']:.8f}")
    print(f"잔여 KRW: {result['remaining_krw']:,.0f}")
    print(f"총 매수 횟수: {result['buy_count']}회")
    print(f"총 매도 횟수: {result['sell_count']}회")
    
    # 파일 저장
    with open("backtest_result_v_3(2024-2025).txt", "w") as f:
        f.write("=== 개선된 백테스트 결과 ===\n")
        f.write(f"초기 자본: {result['initial_balance']:,.0f} KRW\n")
        f.write(f"최종 자산: {result['final_balance']:,.0f} KRW\n")
        f.write(f"수익률: {result['return_rate']:.2f}%\n")
        f.write(f"잔여 BTC: {result['remaining_btc']:.8f}\n")
        f.write(f"잔여 KRW: {result['remaining_krw']:,.0f}\n\n")
        f.write(f"총 매수 횟수: {result['buy_count']}회\n")
        f.write(f"총 매도 횟수: {result['sell_count']}회\n\n")
        f.write("거래 이벤트 로그:\n")
        for log in result['trade_history']:
            f.write(f"[{log[0]}] {log[1]} - 가격: {log[2]:,.0f} KRW, 수량: {log[3]:.8f} BTC\n")
