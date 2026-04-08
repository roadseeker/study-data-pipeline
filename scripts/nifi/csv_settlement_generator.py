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

OUTPUT_DIR = "./data/settlement" # CSV 파일이 저장될 디렉토리

SETTLEMENT_TYPES = ["DAILY_CLOSE", "MERCHANT_PAYOUT", "FEE_CALCULATION", "REFUND_BATCH"]

def generate_settlement_row(seq: int, batch_id: str) -> dict:
    """정산 레코드 1건 생성"""
    return {
        # 정산번호를 STL-00000001 같은 형식의 고정 길이 문자열로 만든다.
        "settlement_id": f"STL-{seq:08d}",
        "batch_id": batch_id,
        # 시작값과 끝값 사이의 정수 하나를 랜덤 선택
        "merchant_id": f"MCH-{random.randint(100, 599)}",
        # 목록 안의 값 중 하나를 랜덤 선택
        "settlement_type": random.choice(SETTLEMENT_TYPES),
        # 시작값과 끝값 사이의 실수 하나를 랜덤 선택
        "gross_amount": round(random.uniform(100000, 50000000), 2),
        "fee_amount": round(random.uniform(1000, 500000), 2),
        "net_amount": 0,  # 아래에서 계산
        "currency": random.choices(["KRW", "USD", "JPY"], weights=[80, 15, 5], k=1)[0],
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

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    batch_id = f"BATCH-{timestamp}"
    filename = f"settlement_{timestamp}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    fieldnames = [
        "settlement_id", "batch_id", "merchant_id", "settlement_type",
        "gross_amount", "fee_amount", "net_amount", "currency",
        "tx_count", "settlement_date", "created_at", "status",
    ]

    rows = []
    for i in range(1, row_count + 1):
        row = generate_settlement_row(i, batch_id)
        # 고객이 결제한 총액: gross_amount
        # Nexus Pay가 서비스 대가로 가져가는 금액: fee_amount
        # 가맹점에 최종 지급할 금액: net_amount
        row["net_amount"] = round(row["gross_amount"] - row["fee_amount"], 2)
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
