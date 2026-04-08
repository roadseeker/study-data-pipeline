"""
Nexus Pay 결제 API 시뮬레이터
- GET /api/v1/payments/recent : 최근 거래 N건 반환
- GET /api/v1/payments/stream : 1건씩 실시간 반환 (polling용)
- NiFi InvokeHTTP가 주기적으로 호출하는 대상
"""

import json
import random
import time
from datetime import datetime, timedelta, timezone

from flask import Flask, jsonify, request

# Flask 애플리케이션 객체를 생성한다.
# __name__을 넘기면 Flask가 현재 파일 기준으로 앱 경로와 실행 문맥을 식별한다.
app = Flask(__name__)

# 시퀀스 카운터 (서버 재시작 시 리셋)
_seq_counter = 0
# 마지막 반환 시각 추적 (증분 수집용)
_last_fetched = datetime.now(timezone.utc) - timedelta(minutes=5)

# 샘플 가맹점 목록: 거래 데이터에 현실감을 주기 위한 더미 마스터 데이터
MERCHANTS = [
    {"id": "MCH-101", "name": "스타벅스 강남점", "category": "CAFE"},
    {"id": "MCH-202", "name": "쿠팡 온라인", "category": "ECOMMERCE"},
    {"id": "MCH-303", "name": "GS25 역삼점", "category": "CONVENIENCE"},
    {"id": "MCH-404", "name": "현대백화점 판교", "category": "DEPARTMENT"},
    {"id": "MCH-505", "name": "배달의민족", "category": "DELIVERY"},
]

# 결제가 발생할 수 있는 채널 후보
CHANNELS = ["APP", "WEB", "POS", "ATM"]

# 통화 후보와 선택 가중치
CURRENCIES = [("KRW", 70), ("USD", 20), ("JPY", 10)]

# 통화별 금액 범위(최소값, 최대값)
AMOUNT_RANGES = {
    "KRW": (1000, 5_000_000),
    "USD": (1, 5_000),
    "JPY": (100, 500_000),
}


def generate_payment() -> dict:
    """결제 이벤트 1건 생성"""
    global _seq_counter
    _seq_counter += 1

    # "KRW", "USD", "JPY" 중에서 70:20:10 비율로 1개(k=1)를 뽑으라는 의미. 
    # 결과는 리스트로 반환되므로 [0]으로 첫 번째 요소를 가져온다.
    currency = random.choices(
        [c[0] for c in CURRENCIES],
        weights=[c[1] for c in CURRENCIES],
        k=1
    )[0]

    # 선택된 통화에 맞는 금액 범위를 가져와
    # 최소값은 lo, 최대값은 hi 변수에 각각 나눠 담는다.
    lo, hi = AMOUNT_RANGES[currency]

    # KRW와 JPY는 정수 금액으로, USD는 소수 둘째 자리까지 생성한다.
    raw_amount = random.uniform(lo, hi)
    if currency in {"KRW", "JPY"}:
        amount = int(round(raw_amount))
    else:
        amount = round(raw_amount, 2)

    # 10% 확률로 고액 이상 패턴을 섞어 NiFi 실습 시 데이터 다양성을 만든다.
    is_suspicious = random.random() < 0.10
    if is_suspicious:
        boosted_amount = amount * random.uniform(5.0, 15.0)
        if currency in {"KRW", "JPY"}:
            amount = int(round(boosted_amount))
        else:
            amount = round(boosted_amount, 2)

    merchant = random.choice(MERCHANTS)

    return {
        "event_id": f"PAY-{_seq_counter:08d}",
        "event_type": "PAYMENT",
        "user_id": random.randint(1001, 2000),
        "amount": amount,
        "currency": currency,
        "merchant": merchant,
        "channel": random.choice(CHANNELS),
        "status": "COMPLETED" if random.random() < 0.92 else "FAILED",
        "is_suspicious": is_suspicious,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "payment-api",
    }

@app.route("/api/v1/payments/recent", methods=["GET"])
# NiFi의 InvokeHTTP가 주기적으로 호출하여 N건씩 수집하는 엔드포인트
def get_recent_payments():
    """최근 거래 N건 반환 (배치 수집용)"""

    # URL 파라미터 count를 읽어 정수로 변환하고,
    # 값이 없으면 기본값 10을 쓰며, 너무 큰 요청은 최대 50건으로 제한한다.
    count = min(int(request.args.get("count", 10)), 50)
    payments = [generate_payment() for _ in range(count)]
    return jsonify({
        "status": "ok",
        "count": len(payments),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "data": payments,
    })

@app.route("/api/v1/payments/stream", methods=["GET"])
# NiFi의 InvokeHTTP가 주기적으로 호출하여 단건씩 수집하는 엔드포인트
# NiFi가 일정 주기로 계속 호출하는 polling 방식 실습용 엔드포인트입니다.
def get_stream_payment():
    """단건 거래 반환 (polling 수집용)"""
    # 함수 안에서 전역 변수 _last_fetched 값을 갱신하겠다고 선언한다.
    global _last_fetched
    # 결제 이벤트 1건을 새로 생성한다.
    payment = generate_payment()
    # 이번 요청이 처리된 현재 시각을 마지막 반환 시각으로 기록한다.
    _last_fetched = datetime.now(timezone.utc)
    # 생성한 거래 1건을 JSON 응답으로 반환한다.
    return jsonify(payment)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "seq": _seq_counter})

if __name__ == "__main__":
    print("Nexus Pay 결제 API 시뮬레이터 시작 — http://0.0.0.0:5050")
    app.run(host="0.0.0.0", port=5050, debug=False)