import json
import time

# 테스트용 잔고 및 보유량 설정
TEST_BALANCE = 1000000  # 100만원
TEST_CRYPTO_HELD = 0.0
TRADE_UNIT = 100000  # 한 번 거래할 금액
MIN_ORDER_KRW = 5000  # 최소 주문 금액

# 현재 가격을 가져오는 함수(test)
def get_latest_price():
    return 65000000  # ex: 6500만 원 (BTC)

# 매매 시뮬레이션 함수
def simulate_trade():
    global TEST_BALANCE, TEST_CRYPTO_HELD
    
    TEST_PRICE = get_latest_price()
    if not TEST_PRICE:
        print("[ERROR] 현재 가격을 가져올 수 없음.")
        return
    
    # 최신 매매 신호 로드
    try:
        with open("trade_signal.json", "r") as f:
            result = json.load(f)
        action = result["signal_value"]
        print(f"\n[테스트 매매] 예측된 행동: {action}")
    except FileNotFoundError:
        print("[ERROR] trade_signal.json 파일을 찾을 수 없음.")
        return
    
    if action == "BUY":
        if TEST_BALANCE >= MIN_ORDER_KRW:
            buy_krw = min(TRADE_UNIT, TEST_BALANCE)
            buy_volume = buy_krw / TEST_PRICE
            TEST_BALANCE -= buy_krw
            TEST_CRYPTO_HELD += buy_volume
            print(f"[BUY] {buy_volume:.6f} BTC 매수 완료! (잔고: {TEST_BALANCE} 원, 보유량: {TEST_CRYPTO_HELD} BTC)")

    elif action == "SELL":
        if TEST_CRYPTO_HELD > 0:
            sell_volume = min(TEST_CRYPTO_HELD, TRADE_UNIT / TEST_PRICE)
            sell_krw = sell_volume * TEST_PRICE
            TEST_BALANCE += sell_krw
            TEST_CRYPTO_HELD -= sell_volume
            print(f"[SELL] {sell_volume:.6f} BTC 매도 완료! (잔고: {TEST_BALANCE} 원, 보유량: {TEST_CRYPTO_HELD} BTC)")

    else:
        print("[HOLD] 현재 상태 유지.")

# 실행 함수
if __name__ == "__main__":
    while True:
        simulate_trade()
        time.sleep(900)  # 15분마다 실행
