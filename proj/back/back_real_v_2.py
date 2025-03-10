# real_v_2.py 백테스트

from datetime import datetime
import pandas as pd
import numpy as np

# CSV 파일 로드 및 전처리
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

# 백테스트 엔진
def backtest(df, initial_balance=10000000, fee=0.0005):
    balance = initial_balance  # 초기 자본
    btc = 0.0  # 보유 코인 수량
    web_orders = []  # 매수 거미줄 주문
    sell_web_orders = []  # 매도 거미줄 주문
    is_web_active = False  # 매수 거미줄 활성화 상태
    is_sell_web_active = False  # 매도 거미줄 활성화 상태
    trade_history = []  # 거래 기록
    avg_buy_price = 0.0  # 평균 매입가
    buy_count = 0  # 매수 횟수
    sell_count = 0  # 매도 횟수

    for i in range(len(df)):
        current_data = df.iloc[i]
        current_price = current_data['close']
        current_time = df.index[i]
        
        # 기술적 지표 값 추출
        rsi = current_data['RSI']
        lower_band = current_data['Lower']
        upper_band = current_data['Upper']
        
        # 포트폴리오 가치 계산
        portfolio_value = balance + (btc * current_price)
        
        # 평단가 수익률 계산
        profit_rate = ((current_price - avg_buy_price)/avg_buy_price)*100 if avg_buy_price > 0 else 0

        # 매수 거미줄 생성 조건
        if not is_web_active and balance > 5000:
            if current_price < lower_band and rsi < 40:
                # 기존 매도 거미줄 초기화
                sell_web_orders.clear()
                is_sell_web_active = False
                
                # 매수 거미줄 생성
                is_web_active = True
                for j in range(1, 11):
                    order_price = current_price * (1 - 0.005*j)
                    order_krw = initial_balance * 0.025  # 2.5%씩 분할 매수
                    if order_krw >= 5000:  # 최소 주문 금액 확인
                        web_orders.append({
                            'price': order_price,
                            'amount': order_krw / current_price  # KRW -> BTC 변환
                        })
                    # else:
                    #     print(f"거미줄 매수 금액이 최소 주문 금액 미만입니다. (금액: {order_krw})")
                trade_history.append((current_time, "BUY WEB 생성", current_price, 0))
                
        # 매수 체결 처리
        executed_orders = []
        for order in web_orders:
            if current_price <= order['price']:
                # 주문 가능 금액 확인
                cost = order['amount'] * current_price * (1 + fee)
                if balance >= cost and cost >= 5000:  # 최소 주문 금액 확인
                    balance -= cost
                    btc += order['amount']
                    avg_buy_price = ((avg_buy_price * (btc - order['amount'])) + 
                                    (current_price * order['amount'])) / btc
                    executed_orders.append(order)
                    trade_history.append((current_time, "BUY", current_price, order['amount']))
                    buy_count += 1  # 매수 횟수 증가
        
        # 체결된 주문 제거            
        for order in executed_orders:
            web_orders.remove(order)
            
        if not web_orders and is_web_active:
            is_web_active = False
            trade_history.append((current_time, "BUY WEB 해제", current_price, 0))

        # 매도 거미줄 생성 조건
        if not is_sell_web_active and btc > 0:
            if profit_rate >= 2:  # 평단가 2% 이상 시 활성화
                # 기존 매수 거미줄 초기화
                web_orders.clear()
                is_web_active = False
                
                # 매도 거미줄 생성
                is_sell_web_active = True
                sell_amount = btc * 0.5  # 50% 물량 매도
                for j in range(1, 6):
                    order_price = current_price * (1 + 0.01*j)  # 1% 간격
                    sell_web_orders.append({
                        'price': order_price,
                        'amount': sell_amount / 5  # 5단계 분할
                    })
                trade_history.append((current_time, "SELL WEB 생성", current_price, 0))

        # 매도 체결 처리
        executed_sell = []
        for order in sell_web_orders:
            if current_price >= order['price']:
                if btc >= order['amount'] and order['amount'] * current_price >= 5000:  # 최소 주문 금액 확인
                    balance += order['amount'] * current_price * (1 - fee)
                    btc -= order['amount']
                    executed_sell.append(order)
                    avg_buy_price = avg_buy_price if btc > 0 else 0
                    trade_history.append((current_time, "SELL", current_price, order['amount']))
                    sell_count += 1  # 매도 횟수 증가
        
        # 체결된 주문 제거
        for order in executed_sell:
            sell_web_orders.remove(order)
            
        if not sell_web_orders and is_sell_web_active:
            is_sell_web_active = False
            trade_history.append((current_time, "SELL WEB 해제", current_price, 0))

    # 최종 결과 계산
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

# 실행 예시
if __name__ == "__main__":
    # 데이터 로드
    df = load_data("backtest_data/KRW-BTC_5min_2023-2025.csv")
    df = calculate_indicators(df)
    
    # 백테스트 실행
    result = backtest(df, initial_balance=10000000)
    
    # 결과 출력
    print(f"초기 자본: {result['initial_balance']:,.0f} KRW")
    print(f"최종 자산: {result['final_balance']:,.0f} KRW")
    print(f"수익률: {result['return_rate']:.2f}%")
    print(f"잔여 BTC: {result['remaining_btc']:.8f}")
    print(f"잔여 KRW: {result['remaining_krw']:,.0f}")
    print(f"총 매수 횟수: {result['buy_count']}회")
    print(f"총 매도 횟수: {result['sell_count']}회")
    # print("\n최근 10건 거래 내역:")
    # for trade in result['trade_history'][-10:]:
    #     print(f"[{trade[0]}] {trade[1]} - 가격: {trade[2]:,.0f} 수량: {trade[3]:.8f}")

    # 결과 저장
    with open("backtest_result_v_2(2023-2025).txt", "w") as f:
        f.write("=== 백테스트 결과 ===\n")
        f.write(f"초기 자본: {result['initial_balance']:,.0f} KRW\n")
        f.write(f"최종 자산: {result['final_balance']:,.0f} KRW\n")
        f.write(f"수익률: {result['return_rate']:.2f}%\n")
        f.write(f"잔여 BTC: {result['remaining_btc']:.8f}\n")
        f.write(f"잔여 KRW: {result['remaining_krw']:,.0f}\n\n")
        f.write(f"총 매수 횟수: {result['buy_count']}회\n")
        f.write(f"총 매도 횟수: {result['sell_count']}회\n\n")
        f.write("거래 내역:\n")
        for trade in result['trade_history']:
            f.write(f"[{trade[0]}] {trade[1]} - 가격: {trade[2]:,.0f} 수량: {trade[3]:.8f}\n")
