# 📈 Upbit 비트코인 자동매매 봇 (기술적 지표 + 거미줄 전략)

이 프로젝트는 **Upbit API**를 활용한 **비트코인 자동 매매 프로그램램**입니다.  
**RSI, 볼린저 밴드** 기반의 기술적 분석 + **거미줄 매수/매도 전략**을 조합하여, 안정적인 수익 실현을 목표로 합니다.

---

## 전략 요약

### 🔹 매수 조건
- 현재가 < 볼린저밴드 하단
- RSI < 40
- 조건 만족 시, **거미줄 매수** 실행:
  - 간격: 0.5%씩 10단계
  - 금액: 초기 자산의 2.5%씩

### 🔹 매도 조건
- 현재가 > 볼린저밴드 상단
- RSI > 65
- 조건 만족 시, **보유 BTC의 50% 매도**를 5단계로 분할:
  - 간격: 2%씩 상승
  - 금액: 1/5씩 분할 매도

---

## 📊 주요 기능

- 실시간 가격 데이터 및 기술 지표 계산 (5분봉 기준)
- RSI / Bollinger Bands 분석
- 매수 / 매도 조건 자동 감지
- 거미줄 방식의 자동 분할 매수 및 매도
- 수익률 실시간 추적 및 출력

---

## 🧩 기술 스택

- Python 3.9+
- [PyUpbit](https://github.com/sharebook-kr/pyupbit)
- Pandas / Numpy
- dotenv

---

## ⚙️ 설치 및 실행

1. 이 저장소를 클론하세요:

```bash
git clone https://github.com/limzooy/upbit.git
cd upbit-bot
