"""
Verify that the same NexusPay user_id is always routed to the same partition.
"""

import json

from confluent_kafka import Consumer, OFFSET_BEGINNING, TopicPartition


BROKER = "localhost:29092"
TOPIC = "nexuspay.transactions.payment"


def main() -> None:
    consumer = Consumer(
        {
            "bootstrap.servers": BROKER,
            "group.id": "partition-key-verifier",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )

    metadata = consumer.list_topics(TOPIC, timeout=10)
    if TOPIC not in metadata.topics:
        consumer.close()
        raise RuntimeError(f"토픽을 찾을 수 없습니다: {TOPIC}")

    partitions = sorted(metadata.topics[TOPIC].partitions.keys())
    consumer.assign([TopicPartition(TOPIC, partition, OFFSET_BEGINNING) for partition in partitions])

    user_partitions = {}
    count = 0
    empty_polls = 0

    print(f"토픽 '{TOPIC}'에서 메시지 읽는 중...")

    try:
        while count < 200:
            msg = consumer.poll(timeout=2.0)
            if msg is None:
                empty_polls += 1
                if empty_polls >= 3:
                    break
                continue
            if msg.error():
                continue

            empty_polls = 0
            tx = json.loads(msg.value().decode("utf-8"))
            uid = tx["user_id"]
            partition = msg.partition()

            user_partitions.setdefault(uid, set()).add(partition)
            count += 1
    finally:
        consumer.close()

    violations = {uid: parts for uid, parts in user_partitions.items() if len(parts) > 1}

    print("\n검증 결과:")
    print(f"  수집 메시지: {count}건")
    print(f"  고유 사용자: {len(user_partitions)}명")
    print(f"  파티션 키 위반 사용자: {len(violations)}명")

    if violations:
        print("\n위반 사례:")
        for uid, parts in list(violations.items())[:5]:
            print(f"  user_id={uid} -> 파티션 {sorted(parts)}")
    else:
        print("\n모든 사용자가 단일 파티션에 일관되게 배치됨 - 순서 보장 확인")

    partition_user_counts = {}
    for parts in user_partitions.values():
        for partition in parts:
            partition_user_counts[partition] = partition_user_counts.get(partition, 0) + 1

    print("\n파티션별 사용자 분포:")
    for partition in sorted(partition_user_counts):
        user_count = partition_user_counts[partition]
        bar = "#" * max(1, user_count // 2)
        print(f"  파티션 {partition}: {user_count:>4}명  {bar}")


if __name__ == "__main__":
    main()
