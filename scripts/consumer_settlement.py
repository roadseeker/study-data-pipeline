"""
정산 컨슈머
- settlement 그룹으로 모든 거래 토픽 소비
- 통화별·유형별 일일 정산 집계
- 수동 오프셋 커밋
"""


import json
import signal
import sys
import argparse
from collections import defaultdict
from confluent_kafka import Consumer, KafkaError

BROKER = "localhost:30092"
TOPICS = [
    "nexuspay.transactions.payment",
    "nexuspay.transactions.transfer",
    "nexuspay.transactions.withdrawal",
]

running = True

def signal_handler(sig, frame):
    global running
    print("\n종료 신호 수신 — 정리 중...")
    running = False

signal.signal(signal.SIGINT, signal_handler)

def main():
    consumer = Consumer({
        "bootstrap.servers": BROKER,
        "group.id": "settlement",
        "client.id": "settlement-consumer-1",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    })

    consumer.subscribe(TOPICS)

    print("[정산 집계] 컨슈머 시작")
    print(f"  그룹: settlement")
    print("=" * 60)

    # lambda는 이름 없는 짧은 함수를 만드는 파이썬 문법
    # 통화별(currency) -> 거래유형별(tx_type) -> 집계값(count, total) 구조를 저장하는 중첩 defaultdict.
    # 존재하지 않는 키에 접근하면 자동으로 {"count": 0, "total": 0.0} 형태의 기본 집계 구조를 만든다.
    ledger = defaultdict(lambda: defaultdict(lambda: {"count": 0, "total": 0.0}))

    processed = 0

    while running:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                print(f"오류: {msg.error()}")
                continue
        
        tx = json.loads(msg.value().decode("utf-8"))
        processed += 1

        # 통화(currency)를 1차 키로, 거래유형(tx_type)을 2차 키로 사용해
        # 해당 분류의 거래 건수(count)를 1 증가시키고 금액 합계(total)에 현재 거래 금액을 누적한다.
        ledger[tx["currency"]][tx["tx_type"]]["count"] += 1
        ledger[tx["currency"]][tx["tx_type"]]["total"] += tx["amount"]

        if processed % 10 == 0:
            consumer.commit(asynchronous=False)

        if processed % 50 == 0:
            print_summary(ledger, processed)

    # 종료 전 최종 집계 출력
    consumer.commit(asynchronous=False)
    consumer.close()
    print("\n" + "=" * 60)
    print("최종 정산 집계")
    print_summary(ledger, processed)



def print_summary(ledger, processed):
    """정산 집계 출력"""

    print(f"\n  📊 정산 중간 집계 ({processed}건 처리)")
    # 정산 집계 표의 헤더 행을 출력한다.
    # 각 컬럼(통화, 유형, 건수, 합계)을 지정한 폭에 맞춰 정렬해 보기 좋게 표시한다.
    print(f"  {'통화':<6} {'유형':<12} {'건수':>8} {'합계':>18}")
    print(f"  {'-'*48}")

    for currency in sorted(ledger.keys()):
        for tx_type in sorted(ledger[currency].keys()):
            entry = ledger[currency][tx_type]
            print(
                f"  {currency:<6} {tx_type:<12} {entry['count']:>8,} "
                f"{entry['total']:>18,.0f}"
            )

            
if __name__ == "__main__":
    main()
