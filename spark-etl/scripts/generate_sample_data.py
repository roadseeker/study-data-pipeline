"""
Nexus Pay 샘플 거래 데이터 생성기
- Kafka 토픽에 적재되는 형식과 동일한 JSON 생성
- Bronze 레이어 테스트용 CSV/JSON 파일 생성
- 의도적으로 중복, null, 이상값을 섞어서 Silver 품질 검증 테스트 가능하게 만들기
- data/sample/transactions_sample.jsonl에 JSON Lines 형식으로 저장
"""
import json
import random
import uuid
from datetime import datetime, timedelta
import os


# 설정
# 기본 정상 거래 1만 건 생성
# 대상 일자는 2026-03-31
# 출력은 data/sample
NUM_RECORDS = 10000
TARGET_DATE = datetime(2026, 3, 31)
OUTPUT_DIR = "data/sample"

# 데이터 풀
# 거래 유형: PAYMENT, REFUND, TRANSFER
# 상태값: SUCCESS, FAILED, PENDING
# 유입 소스: api, csv, db
# 사용자 200명, 가맹점 50개를 미리 만들어 둠
TX_TYPES = ["PAYMENT", "REFUND", "TRANSFER"]
TX_TYPE_WEIGHTS = [0.7, 0.15, 0.15]
STATUSES = ["SUCCESS", "FAILED", "PENDING"]
STATUS_WEIGHTS = [0.92, 0.05, 0.03]
SOURCES = ["api", "csv", "db"]
SOURCE_WEIGHTS = [0.6, 0.25, 0.15]
CURRENCIES = ["KRW"]
MERCHANT_CATEGORIES = ["F&B", "RETAIL", "ONLINE", "TRAVEL", "FINANCE", "HEALTH"]

USER_IDS = [f"USR-{i:05d}" for i in range(1, 201)]           # 200명
MERCHANT_IDS = [f"MRC-{i:04d}" for i in range(1, 51)]        # 50개 가맹점


# 이벤트 1건 생성
# 여기서 중요한 건 거래 유형별 금액 분포가 다르다는 점입니다.
#
# PAYMENT: 비교적 일반적인 결제 금액
# REFUND: 결제보다 조금 작은 환불 분포
# TRANSFER: 더 큰 금액 분포
# 또 실습용 품질 문제도 일부러 넣습니다.
#
# 이상값 약 2%
# 5천만~1억 초고액
# 1~50원 극소액
# 음수 금액
# null 약 1.5%
# user_id, tx_type, amount 중 하나를 None
# TRANSFER는 가맹점 개념이 없어서 merchant_id, merchant_category를 None
# 이 부분이 Silver 레이어에서 품질 검증 규칙을 시험하는 핵심입니다.
def generate_event(event_time: datetime) -> dict:
    """단일 거래 이벤트를 생성한다."""
    tx_type = random.choices(TX_TYPES, TX_TYPE_WEIGHTS)[0]
    status = random.choices(STATUSES, STATUS_WEIGHTS)[0]

    # 금액: 거래 유형별 다른 분포
    if tx_type == "PAYMENT":
        amount = round(random.lognormvariate(10, 1.5), 0)     # 중앙값 약 2만원
        amount = max(100, min(amount, 10_000_000))
    elif tx_type == "REFUND":
        amount = round(random.lognormvariate(9.5, 1.2), 0)
        amount = max(100, min(amount, 5_000_000))
    else:  # TRANSFER
        amount = round(random.lognormvariate(11, 2), 0)
        amount = max(1000, min(amount, 50_000_000))

    # 이상값 삽입 (약 2%)
    is_anomaly = False
    if random.random() < 0.02:
        is_anomaly = True
        amount = random.choice([
            random.uniform(50_000_000, 100_000_000),    # 고액 이상거래
            random.uniform(1, 50),                       # 극소액 이상거래
            -abs(amount),                                # 음수 금액
        ])

    # 중복 삽입 (약 1%)
    tx_id = str(uuid.uuid4())

    event = {
        "tx_id": tx_id,
        "user_id": random.choice(USER_IDS),
        "tx_type": tx_type,
        "amount": round(amount, 0),
        "currency": random.choice(CURRENCIES),
        "merchant_id": random.choice(MERCHANT_IDS) if tx_type != "TRANSFER" else None,
        "merchant_category": random.choice(MERCHANT_CATEGORIES) if tx_type != "TRANSFER" else None,
        "status": status,
        "timestamp": event_time.isoformat(),
        "source": random.choices(SOURCES, SOURCE_WEIGHTS)[0],
    }

    # null 삽입 (약 1.5%)
    if random.random() < 0.015:
        null_field = random.choice(["user_id", "tx_type", "amount"])
        event[null_field] = None

    return event


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    events = []
    duplicate_pool = []

    for i in range(NUM_RECORDS):
        # 하루 동안 분산된 시간 생성
        hour = random.choices(range(24), weights=[
            2, 1, 1, 1, 1, 2, 5, 8, 10, 12, 13, 12,
            14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3
        ])[0]
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        event_time = TARGET_DATE.replace(hour=hour, minute=minute, second=second)

        event = generate_event(event_time)
        events.append(event)

        # 중복 풀에 일부 추가
        if random.random() < 0.01:
            duplicate_pool.append(event.copy())

    # 중복 이벤트 삽입
    events.extend(duplicate_pool)
    random.shuffle(events)

    # JSON Lines 파일 저장
    output_path = os.path.join(OUTPUT_DIR, "transactions_sample.jsonl")
    with open(output_path, "w") as f:
        for event in events:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    print(f"[생성 완료] {len(events)}건 → {output_path}")
    print(f"  - 정상 거래: {NUM_RECORDS}건")
    print(f"  - 중복 거래: {len(duplicate_pool)}건")
    print(f"  - 이상값 포함: ~{int(NUM_RECORDS * 0.02)}건")
    print(f"  - null 포함: ~{int(NUM_RECORDS * 0.015)}건")


if __name__ == "__main__":
    main()
