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

from confluent_kafka import KafkaException, Producer


BROKER = "localhost:30092"
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
    """선택된 통화에 해당하는 최소값, 최대값을 가져옵니다."""
    
    amount = round(random.uniform(lower, upper), 2) 
    """최소값과 최대값 사이의 실수형 랜덤 값을 만듭니다."""

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


def verify_broker_connection(producer: Producer, timeout: int = 5) -> str:
    """Fail fast if the Week 2 Kafka broker is unreachable."""
    try:
        metadata = producer.list_topics(timeout=timeout)
    except KafkaException as exc:
        raise RuntimeError(
            "Kafka broker connection failed. "
            f"bootstrap.servers={BROKER}. "
            "Start the Week 2 broker with `docker compose up -d kafka` "
            "and verify port 30092 is exposed."
        ) from exc

    if not metadata.brokers:
        raise RuntimeError(
            "Kafka metadata lookup returned no brokers. "
            f"bootstrap.servers={BROKER}"
        )

    return ", ".join(
        f"{broker.host}:{broker.port}" for broker in metadata.brokers.values()
    )


def make_delivery_report(state: dict, verbose: bool):
    """Track delivery outcomes and print only the signals that matter."""

    def callback(err, msg) -> None:
        if err is not None:
            state["delivery_failed"] += 1
            print(f"  FAIL topic={msg.topic()} key={msg.key().decode('utf-8')} error={err}")
            return

        state["delivered"] += 1
        if verbose:
            delivery_report(err, msg)

    return callback


def flush_or_warn(producer: Producer, state: dict, sent: int, total: int) -> bool:
    """Flush pending messages and surface undelivered message counts clearly."""
    remaining = producer.flush(timeout=10)
    if remaining > 0:
        state["flush_failed"] += remaining
        print(
            "  ERROR flush timeout: "
            f"{remaining} message(s) still pending after 10s "
            f"at progress={sent}/{total}. broker={BROKER}"
        )
        return False

    print(
        f"  progress={sent}/{total} "
        f"delivered={state['delivered']} "
        f"delivery_failed={state['delivery_failed']} "
        f"flush_failed={state['flush_failed']}"
    )
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Nexus Pay transaction producer")
    parser.add_argument("-n", "--count", type=int, default=100, help="number of events")
    parser.add_argument(
        "-d", "--delay", type=float, default=0.1, help="delay between events in seconds"
    )
    parser.add_argument("--verbose", action="store_true", help="print per-message delivery")
    args = parser.parse_args()

    producer = build_producer()
    delivery_state = {"delivered": 0, "delivery_failed": 0, "flush_failed": 0}
    delivery_callback = make_delivery_report(delivery_state, args.verbose)
    stats = {"PAYMENT": 0, "TRANSFER": 0, "WITHDRAWAL": 0, "suspicious": 0}

    print(f"Nexus Pay producer start: {args.count} events")
    print(f"broker={BROKER}")
    print("=" * 60)

    try:
        connected_brokers = verify_broker_connection(producer)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1) from exc

    print(f"connected_brokers={connected_brokers}")

    failed = False

    for seq in range(1, args.count + 1):
        tx = create_transaction(seq)
        topic = TOPICS[tx["tx_type"]]
        key = str(tx["user_id"])
        value = json.dumps(tx, ensure_ascii=False)

        producer.produce(
            topic=topic,
            key=key.encode("utf-8"),
            value=value.encode("utf-8"),
            callback=delivery_callback,
        )
        producer.poll(0)

        stats[tx["tx_type"]] += 1
        if tx["is_suspicious"]:
            stats["suspicious"] += 1

        if seq % 50 == 0 or seq == args.count:
            if not flush_or_warn(producer, delivery_state, seq, args.count):
                failed = True
                break

        time.sleep(args.delay)

    print("=" * 60)
    if failed or delivery_state["delivery_failed"] or delivery_state["flush_failed"]:
        print("Transmission finished with errors")
    else:
        print("Transmission complete")
    print(f"  payment={stats['PAYMENT']}")
    print(f"  transfer={stats['TRANSFER']}")
    print(f"  withdrawal={stats['WITHDRAWAL']}")
    print(f"  suspicious={stats['suspicious']}")
    print(f"  delivered={delivery_state['delivered']}")
    print(f"  delivery_failed={delivery_state['delivery_failed']}")
    print(f"  flush_failed={delivery_state['flush_failed']}")

    if failed or delivery_state["delivery_failed"] or delivery_state["flush_failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
