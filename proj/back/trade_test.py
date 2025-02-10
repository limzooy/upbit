# 테스트용 자동 매매 코드
# prediction_result.json에서 예측 결과(BUY, SELL, HOLD) 읽기
# 실제 매매 대신 가상의 잔고를 사용하여 매매 시뮬레이션
# 랜덤 거래량을 적용하여 매매가 다양하게 이루어짐
# 실행 시 10초마다 반복하여 새로운 예측 결과 반영

import json
import time
import random

# 테스트용 가상 잔고
TEST_BALANCE = 1000000  # 초기 원화 잔고 (100만원)
TEST_CRYPTO_HELD = 0.0  # 초기 보유 코인 개수
TEST_PRICE = 50000000   # 가정된 비트코인 가격 (50,000,000원)

def simulate_trade():
    global TEST_BALANCE, TEST_CRYPTO_HELD, TEST_PRICE

    # 최신 예측 결과 로드
    with open("prediction_result.json", "r") as f:
        result = json.load(f)
    
    action = result["predicted_action"]
    print(f"\n[테스트 매매] 예측된 행동: {action}")

    if action == "BUY":
        # 랜덤 매수량 (최대 잔고의 20%만 사용)
        max_buy = TEST_BALANCE * 0.2 // TEST_PRICE
        buy_volume = round(random.uniform(0.0001, max_buy), 4)

        if TEST_BALANCE >= buy_volume * TEST_PRICE:
            TEST_BALANCE -= buy_volume * TEST_PRICE
            TEST_CRYPTO_HELD += buy_volume
            print(f"[BUY] {buy_volume} BTC 매수 완료! (잔고: {TEST_BALANCE} 원, 보유량: {TEST_CRYPTO_HELD} BTC)")
        else:
            print("[BUY] 잔고 부족으로 매수 실패!")

    elif action == "SELL":
        # 랜덤 매도량 (최대 보유량의 50%)
        max_sell = TEST_CRYPTO_HELD * 0.5
        sell_volume = round(random.uniform(0.0001, max_sell), 4)

        if TEST_CRYPTO_HELD >= sell_volume:
            TEST_BALANCE += sell_volume * TEST_PRICE
            TEST_CRYPTO_HELD -= sell_volume
            print(f"[SELL] {sell_volume} BTC 매도 완료! (잔고: {TEST_BALANCE} 원, 보유량: {TEST_CRYPTO_HELD} BTC)")
        else:
            print("[SELL] 보유량 부족으로 매도 실패!")

    else:
        print("[HOLD] 현재 상태 유지.")

if __name__ == "__main__":
    while True:
        simulate_trade()
        time.sleep(30)  # 30초마다 실행
