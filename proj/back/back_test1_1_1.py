# # test1_1_1 매도 조건: 볼린저 상단 and rsi 65이상
# # 매수: 자산의 2.5%, 매도: 보유 금액의 50%
# # 기술적 지표 조건 + 거미줄 매수 전략
# # 매도 전략에는 거미줄 전략이 적용 O
# # 매수 거미줄 간격: 0.5%, 매도 거미줄 간격: 1%

# import pandas as pd
# import numpy as np

# def get_rsi(data, period=14):
#     delta = data.diff()
#     gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
#     loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
#     rs = gain / loss
#     return 100 - (100 / (1 + rs))

# def get_bollinger_bands(df, n=20, k=2):
#     df['MA'] = df['trade_price'].rolling(window=n).mean()
#     df['STD'] = df['trade_price'].rolling(window=n).std()
#     df['Upper'] = df['MA'] + k * df['STD']
#     df['Lower'] = df['MA'] - k * df['STD']
#     return df

# def backtest(df, initial_balance=10000000):
#     balance = initial_balance
#     btc = 0
#     fee = 0.0005
#     buy_interval = 0.005  # 매수 거미줄 간격 (0.5%)
#     sell_interval = 0.01  # 매도 거미줄 간격 (1%)
#     buy_orders = []  # 매수 거미줄 주문 목록
#     sell_orders = []  # 매도 거미줄 주문 목록
#     is_buy_web_active = False  # 매수 거미줄 활성화 상태
#     is_sell_web_active = False  # 매도 거미줄 활성화 상태
#     trade_history = []

#     for i in range(len(df)):
#         current_price = df['trade_price'].iloc[i]
#         rsi = df['RSI'].iloc[i]
#         lower_band = df['Lower'].iloc[i]
#         upper_band = df['Upper'].iloc[i]

#         portfolio_value = balance + (btc * current_price)
#         order_amount = portfolio_value * 0.025  # 자산의 2.5%

#         # 거미줄 매수 주문 실행
#         if is_buy_web_active:
#             for order in buy_orders[:]:
#                 if current_price <= order['price']:
#                     if balance >= order['amount']:
#                         btc_to_buy = (order['amount'] / current_price) * (1 - fee)
#                         balance -= order['amount']
#                         btc += btc_to_buy
#                         trade_history.append(('Buy', current_price, btc_to_buy, balance, btc))
#                         buy_orders.remove(order)
#             if not buy_orders:
#                 is_buy_web_active = False

#         # 거미줄 매도 주문 실행
#         if is_sell_web_active:
#             for order in sell_orders[:]:
#                 if current_price >= order['price']:
#                     if btc >= order['amount']:
#                         sell_value = order['amount'] * current_price
#                         balance += sell_value * (1 - fee)
#                         btc -= order['amount']
#                         trade_history.append(('Sell', current_price, order['amount'], balance, btc))
#                         sell_orders.remove(order)
#                     else:
#                         is_sell_web_active = False
#                         sell_orders.clear()
#                         break

#         # 새로운 거미줄 매수 주문 생성
#         if not is_buy_web_active and not is_sell_web_active and balance > order_amount and current_price < lower_band and rsi < 40:
#             for j in range(1, 11):  # 매수 거미줄 개수 유지
#                 buy_price = current_price * (1 - 0.005 * j)  # 0.5% 간격 매수 거미줄
#                 place_limit_order('buy', buy_price, order_amount)

#         # 새로운 거미줄 매도 주문 생성
#         if not is_sell_web_active and not is_buy_web_active and btc > 0 and current_price > upper_band and rsi > 65:
#             for j in range(1, 11):  # 매도 거미줄 개수 유지
#                 sell_price = current_price * (1 + 0.01 * j)  # 1% 간격 매도 거미줄
#                 place_limit_order('sell', sell_price, order_amount)

#     final_balance = balance + btc * df['trade_price'].iloc[-1]
#     return final_balance, trade_history

# def main():
#     df = pd.read_csv('upbit_candle_data(1).csv')
#     df['datetime'] = pd.to_datetime(df['timestamp'])
#     df.set_index('datetime', inplace=True)

#     df = get_bollinger_bands(df)
#     df['RSI'] = get_rsi(df['trade_price'])

#     initial_balance = 10000000
#     final_balance, trade_history = backtest(df, initial_balance)

#     print(f"Initial Balance: {initial_balance:,.0f} KRW")
#     print(f"Final Balance: {final_balance:,.0f} KRW")
#     print(f"Profit: {final_balance - initial_balance:,.0f} KRW")
#     print(f"Return: {((final_balance / initial_balance) - 1) * 100:.2f}%")
#     print(f"Number of trades: {len(trade_history)}")

#     buy_count = sum(1 for trade in trade_history if trade[0] == 'Buy')
#     sell_count = sum(1 for trade in trade_history if trade[0] == 'Sell')
#     print(f"Number of buy trades: {buy_count}")
#     print(f"Number of sell trades: {sell_count}")

#     trade_df = pd.DataFrame(trade_history, columns=['Type', 'Price', 'Amount', 'Balance', 'BTC'])
#     trade_df.to_csv('trade_backtest_result.csv', index=False)
#     print("Trade history saved to 'trade_backtest_1_1(1).csv'")

# if __name__ == '__main__':
#     main()
