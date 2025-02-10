# Exchange API
# 주문은 초당 8회, 분당 200회 / 주문 외 요청은 초당 30회, 분당 900회 사용 가능
# https://github.com/sharebook-kr/pyupbit

#로그인(Access Key와 Sercret Key를 사용해서 Upbit 객체를 생성)
import pyupbit

access = "h3AUxrBG5eb7YmDogbp8Z16m3NTNBvnoxRLTRped"  
secret = "ExvWPUcScHsGjRtQgDrbhPmibIyCS0WUIxI5vsK9"
upbit = pyupbit.Upbit(access, secret)

# KRW-BTC 잔고 조회
print(upbit.get_balance("KRW-BTC"))     # KRW-BTC조회
print(upbit.get_balance("KRW"))         # 보유 현금 조회

# 모든 암호화폐 잔고 및 단가 정보 조회
print(upbit.get_balances())

# 지정가 매수/매도 주문 (원화 시장에 N원에 N개)
# 매도
print(upbit.sell_limit_order("KRW-BTC", 600, 20))
# 매수
print(upbit.buy_limit_order("KRW-BTC", 613, 10))

# 시장가 매수/매도 주문
# 시장가 매수
print(upbit.buy_market_order("KRW-BTC", 10000))
# 시장가 매수는 최우선 매도호가에 즉시 매수함.
# buy_market_order 매서드로 티커와 매수 금액만을 입력
# 위 숫자는 수수료가 제외된 금액
# 수수료가 0.0N%라면 수수료를 포함한 N+수수료의 현금을 보유하고 있어야함.

#시장가 매도
print(upbit.sell_market_order("KRW-BTC", 30))

#미체결 주문 조회
upbit.get_order("KRW-BTC")

# state 파라미터를 사용하면 완료된 주문들을 조회할 수 있음
print(upbit.get_order("KRW-BTC", state="done"))

#특정 주문 상세 조회 = uuid
order = upbit.get_order('50e184b3-9b4f-4bb0-9c03-30318e3ff10a')
print(order)

#매수/매도 주문 취소
#uuid값을 사용해서 주문 취소 가능
print(upbit.cancel_order('50e184b3-9b4f-4bb0-9c03-30318e3ff10a'))
