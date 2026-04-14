# scripts/nifi/csv_settlement_generator.py
"""
Nexus Pay 정산 CSV 생성기
- /data/settlement/ 디렉토리에 주기적으로 CSV 파일 생성
- 레거시 시스템이 매시간 정산 파일을 떨구는 시나리오 시뮬레이션
"""

import csv
import os
import random
import time
import argparse
from datetime import datetime, timedelta, timezone

OUTPUT_DIR = "./data/nifi/settlement"  # CSV 파일이 저장될 디렉토리

SETTLEMENT_TYPES = ["DAILY_CLOSE", "MERCHANT_PAYOUT", "FEE_CALCULATION", "REFUND_BATCH"]
CURRENCY_WEIGHTS = [("KRW", 80), ("USD", 15), ("JPY", 5)]
GROSS_AMOUNT_RANGES = {
    "KRW": (100_000, 50_000_000),
    "USD": (100, 50_000),
    "JPY": (10_000, 5_000_000),
}
FEE_RATE_RANGE = (0.003, 0.03)
MERCHANT_CATALOG = [
    {"merchant_id": "MCH-101", "merchant_name": "스타벅스 강남점", "merchant_category": "CAFE"},
    {"merchant_id": "MCH-203", "merchant_name": "올리브영 홍대점", "merchant_category": "BEAUTY"},
    {"merchant_id": "MCH-213", "merchant_name": "이마트 성수점", "merchant_category": "MART"},
    {"merchant_id": "MCH-303", "merchant_name": "GS25 역삼점", "merchant_category": "CONVENIENCE"},
    {"merchant_id": "MCH-404", "merchant_name": "현대백화점 판교", "merchant_category": "DEPARTMENT"},
    {"merchant_id": "MCH-460", "merchant_name": "쿠팡", "merchant_category": "ECOMMERCE"},
    {"merchant_id": "MCH-505", "merchant_name": "배달의민족", "merchant_category": "DELIVERY"},
    {"merchant_id": "MCH-555", "merchant_name": "넷플릭스 코리아", "merchant_category": "SUBSCRIPTION"},
]

def generate_settlement_row(seq: int, batch_id: str, batch_token: str) -> dict:
    """정산 레코드 1건 생성"""
    merchant = random.choice(MERCHANT_CATALOG)
    currency = random.choices(
        [item[0] for item in CURRENCY_WEIGHTS],
        weights=[item[1] for item in CURRENCY_WEIGHTS],
        k=1,
    )[0]

    gross_lo, gross_hi = GROSS_AMOUNT_RANGES[currency]
    gross_raw = random.uniform(gross_lo, gross_hi)
    if currency in {"KRW", "JPY"}:
        gross_amount = int(round(gross_raw))
    else:
        gross_amount = round(gross_raw, 2)

    fee_rate = random.uniform(*FEE_RATE_RANGE)
    fee_raw = gross_amount * fee_rate
    if currency in {"KRW", "JPY"}:
        fee_amount = int(round(fee_raw))
        net_amount = gross_amount - fee_amount
    else:
        fee_amount = round(fee_raw, 2)
        net_amount = round(gross_amount - fee_amount, 2)

    return {
        # 파일마다 다시 1번부터 시작해도 겹치지 않도록 배치 고유 토큰을 포함한다.
        "settlement_id": f"STL-{batch_token}-{seq:06d}",
        "batch_id": batch_id,
        "merchant_id": merchant["merchant_id"],
        "merchant_name": merchant["merchant_name"],
        "merchant_category": merchant["merchant_category"],
        # 목록 안의 값 중 하나를 랜덤 선택
        "settlement_type": random.choice(SETTLEMENT_TYPES),
        "gross_amount": gross_amount,
        "fee_amount": fee_amount,
        "net_amount": net_amount,
        "currency": currency,
        "tx_count": random.randint(10, 5000),
        "settlement_date": (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": random.choices(
            ["COMPLETED", "PENDING", "FAILED"],
            weights=[85, 10, 5],
            k=1
        )[0],
    }

def generate_csv_file(row_count: int = 50):
    """정산 CSV 파일 1개 생성"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    batch_token = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    batch_id = f"BATCH-{batch_token}"
    filename = f"settlement_{batch_token}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    fieldnames = [
        "settlement_id", "batch_id", "merchant_id", "merchant_name", "merchant_category", "settlement_type",
        "gross_amount", "fee_amount", "net_amount", "currency",
        "tx_count", "settlement_date", "created_at", "status",
    ]

    rows = []
    for i in range(1, row_count + 1):
        row = generate_settlement_row(i, batch_id, batch_token)
        rows.append(row)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  ✅ 생성: {filepath} ({row_count}건, batch={batch_id})")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="Nexus Pay 정산 CSV 생성기")
    parser.add_argument("-n", "--files", type=int, default=3, help="생성할 파일 수")
    parser.add_argument("-r", "--rows", type=int, default=50, help="파일당 레코드 수")
    parser.add_argument("-i", "--interval", type=int, default=30, help="파일 생성 간격(초)")
    args = parser.parse_args()

    print(f"Nexus Pay 정산 CSV 생성기 시작")
    print(f"  출력 디렉토리: {OUTPUT_DIR}")
    print(f"  파일 수: {args.files}, 파일당 레코드: {args.rows}")
    print("=" * 60)

    for i in range(1, args.files + 1):
        generate_csv_file(args.rows)
        if i < args.files:
            print(f"  ⏳ {args.interval}초 대기...")
            time.sleep(args.interval)

    print("=" * 60)
    print(f"완료: {args.files}개 파일 생성")


if __name__ == "__main__":
    main()
