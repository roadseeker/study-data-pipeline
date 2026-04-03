"""
Nexus Pay transaction producer for Week 2 Kafka lab.

- Uses user_id as the partition key to preserve per-user ordering
- Generates weighted payment/transfer/withdrawal events
- Adds suspicious transactions for later fraud-detection exercises
"""

import argparse
import json
import random
import time
from datetime import datetime, timezone

from confluent_kafka import Producer


BROKER = "localhost:29092"
TOPICS = {
    "PAYMENT": "nexuspay.transactions.payment",
    "TRANSFER": "nexuspay.transactions.transfer",
    "WITHDRAWAL": "nexuspay.transactions.withdrawal",
}
TX_WEIGHTS = [("PAYMENT", 50), ("TRANSFER", 30), ("WITHDRAWAL", 20)]
USER_IDS = list(range(1001, 2001))
AMOUNT_RANGES = {
    "KRW": (1_000, 10_000_000),
    "USD": (1, 10_000),
    "JPY": (100, 1_000_000),
}


def create_transaction(seq: int) -> dict:
    """Create one synthetic transaction event.

    This function takes an integer seq and returns a dict containing
    transaction information.
    """
    tx_type = random.choices(
        [item[0] for item in TX_WEIGHTS],
        weights=[item[1] for item in TX_WEIGHTS],
        k=1,
    )[0]

    user_id = random.choice(USER_IDS)
    currency = random.choices(["KRW", "USD", "JPY"], weights=[70, 20, 10], k=1)[0]
    lower, upper = AMOUNT_RANGES[currency]
    amount = round(random.uniform(lower, upper), 2)

    is_suspicious = random.random() < 0.10
    if is_suspicious:
        amount = round(amount * random.uniform(5.0, 20.0), 2)

    return {
        "tx_id": f"TX-{seq:08d}",
        "user_id": user_id,
        "amount": amount,
        "currency": currency,
        "tx_type": tx_type,
        "status": "PENDING",
        "is_suspicious": is_suspicious,
        "merchant_id": f"MCH-{random.randint(100, 999)}",
        "channel": random.choice(["APP", "WEB", "ATM", "POS"]),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def delivery_report(err, msg) -> None:
    """Message delivery callback for verbose mode."""
    if err is not None:
        print(f"  FAIL topic={msg.topic()} error={err}")
        return

    key = msg.key().decode("utf-8") if msg.key() else ""
    print(
        f"  OK topic={msg.topic()} partition={msg.partition()} "
        f"offset={msg.offset()} key={key}"
    )


def build_producer() -> Producer:
    """Create a producer with Week 2 recommended settings."""
    return Producer(
        {
            "bootstrap.servers": BROKER,
            "client.id": "nexuspay-producer",
            "acks": "all",
            "retries": 3,
            "linger.ms": 5,
            "compression.type": "lz4",
            "enable.idempotence": True,
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Nexus Pay transaction producer")
    parser.add_argument("-n", "--count", type=int, default=100, help="number of events")
    parser.add_argument(
        "-d", "--delay", type=float, default=0.1, help="delay between events in seconds"
    )
    parser.add_argument("--verbose", action="store_true", help="print per-message delivery")
    args = parser.parse_args()

    producer = build_producer()
    stats = {"PAYMENT": 0, "TRANSFER": 0, "WITHDRAWAL": 0, "suspicious": 0}

    print(f"Nexus Pay producer start: {args.count} events")
    print(f"broker={BROKER}")
    print("=" * 60)

    for seq in range(1, args.count + 1):
        tx = create_transaction(seq)
        topic = TOPICS[tx["tx_type"]]
        key = str(tx["user_id"])
        value = json.dumps(tx, ensure_ascii=False)

        producer.produce(
            topic=topic,
            key=key.encode("utf-8"),
            value=value.encode("utf-8"),
            callback=delivery_report if args.verbose else None,
        )
        producer.poll(0)

        stats[tx["tx_type"]] += 1
        if tx["is_suspicious"]:
            stats["suspicious"] += 1

        if seq % 50 == 0 or seq == args.count:
            producer.flush()
            print(f"  progress={seq}/{args.count}")

        time.sleep(args.delay)

    print("=" * 60)
    print("Transmission complete")
    print(f"  payment={stats['PAYMENT']}")
    print(f"  transfer={stats['TRANSFER']}")
    print(f"  withdrawal={stats['WITHDRAWAL']}")
    print(f"  suspicious={stats['suspicious']}")


if __name__ == "__main__":
    main()
