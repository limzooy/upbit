import json
import time
import requests

# Upbit API 키
ACCESS_KEY = "h3AUxrBG5eb7YmDogbp8Z16m3NTNBvnoxRLTRped"
SECRET_KEY = "ExvWPUcScHsGjRtQgDrbhPmibIyCS0WUIxI5vsK9"

UPBIT_API_URL = "https://api.upbit.com/v1"

# Upbit 주문 함수
def place_order(side, market="KRW-BTC", volume=0.001, price=None):
    order_data = {
        "market": market,
        "side": side,
        "volume": str(volume),
        "ord_type": "price" if price else "market"
    }
    headers = {"Authorization": f"Bearer {ACCESS_KEY}"}
    
    response = requests.post(UPBIT_API_URL + "/orders", json=order_data, headers=headers)
    return response.json()

def execute_trade():
    with open("prediction_result.json", "r") as f:
        result = json.load(f)
    
    action = result["predicted_action"]
    
    if action == "BUY":
        response = place_order("bid")
        print("BUY ORDER PLACED:", response)
    
    elif action == "SELL":
        response = place_order("ask")
        print("SELL ORDER PLACED:", response)
    
    else:
        print("HOLD: No action taken")

if __name__ == "__main__":
    while True:
        execute_trade()
        time.sleep(900)  # 15분마다 실행
