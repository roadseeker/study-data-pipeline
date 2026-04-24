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
from datetime import datetime, timezone
import os


# 설정
# 기본 정상 거래 1만 건 생성
# 대상 일자는 2026-03-31
# 출력은 data/sample
NUM_RECORDS = 10000                 # 기본 정산 거래 1만건 생성
TARGET_DATE = datetime(2026, 3, 31, tzinfo=timezone.utc)
OUTPUT_DIR = "data/sample"

# 데이터 풀
TX_TYPES = ["PAYMENT", "REFUND", "TRANSFER"]    # 거래 유형
TX_TYPE_WEIGHTS = [0.7, 0.15, 0.15]             # 거래 유형 가중치
STATUSES = ["SUCCESS", "FAILED", "PENDING"]     # 거래 상태
STATUS_WEIGHTS = [0.92, 0.05, 0.03]             # 거래 상태 가중치
SOURCES = ["api", "csv", "db"]                  # 유입소스
SOURCE_WEIGHTS = [0.6, 0.25, 0.15]              # 유입소스 가중치
CURRENCIES = ["KRW"]                            # 통화
# 가맹점 카테고리
MERCHANT_CATEGORIES = ["F&B", "RETAIL", "ONLINE", "TRAVEL", "FINANCE", "HEALTH"]

USER_IDS = [f"USR-{i:05d}" for i in range(1, 201)]           # 사용자 아이디-200명
MERCHANT_IDS = [f"MRC-{i:04d}" for i in range(1, 51)]        # 가맹점 아이디-50개 가맹점


# 이벤트 1건 생성
def generate_event(event_time: datetime) -> dict:
    """단일 거래 이벤트를 생성한다."""

    # PAYMENT: 비교적 일반적인 결제 금액
    # REFUND: 결제보다 조금 작은 환불 분포
    # TRANSFER: 더 큰 금액 분포
    tx_type = random.choices(TX_TYPES, TX_TYPE_WEIGHTS)[0]
    # SUCCESS / FAILED / PENDING
    status = random.choices(STATUSES, STATUS_WEIGHTS)[0]

    # 금액: 거래 유형별 다른 분포
    if tx_type == "PAYMENT":
        # PAYMENT: 건수도 많고 금액대도 적당히 다양해서 일반 거래 패턴 표현에 좋음
        amount = round(random.lognormvariate(10, 1.5), 0)     # 중앙값 약 2만원
        amount = max(100, min(amount, 10_000_000))
    elif tx_type == "REFUND":
        # REFUND: 금액 분포가 상대적으로 좁아 품질 검증/집계 시 해석이 쉬움
        amount = round(random.lognormvariate(9.5, 1.2), 0)
        amount = max(100, min(amount, 5_000_000))
    else:  # TRANSFER
        # TRANSFER: 고액 거래와 극단값이 잘 나타나서 이상탐지, 분포 분석, 월별 총액 차이가 잘 드러남
        amount = round(random.lognormvariate(11, 2), 0)
        amount = max(1000, min(amount, 50_000_000))

    # 이상값 삽입 (약 2%)
    is_anomaly = False
    if random.random() < 0.02:
        is_anomaly = True
        amount = random.choice([
            random.uniform(50_000_000, 100_000_000),     # 고액 이상거래
            random.uniform(1, 50),                       # 극소액 이상거래
            -abs(amount),                                       # 음수 금액
        ])

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
        "timestamp": event_time.isoformat().replace("+00:00", "Z"),
        "source": random.choices(SOURCES, SOURCE_WEIGHTS)[0],
    }

    # null 삽입 (약 1.5%)
    if random.random() < 0.015:
        # 3개의 필드중 하나를 랜덤 선택
        null_field = random.choice(["user_id", "tx_type", "amount"])
        # 선택된 필드를 None으로 바꿈
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
