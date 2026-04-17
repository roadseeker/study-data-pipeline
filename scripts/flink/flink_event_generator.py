#!/usr/bin/env python3
"""
Flink 실습용 이벤트 생성기.
nexuspay.events.ingested 토픽에 테스트 이벤트를 주입한다.

사용법:
  python3 scripts/flink/flink_event_generator.py --mode normal    # 정상 거래 생성
  python3 scripts/flink/flink_event_generator.py --mode fraud     # 이상거래 포함 생성
  python3 scripts/flink/flink_event_generator.py --mode late      # 지연 데이터 포함 생성
  python3 scripts/flink/flink_event_generator.py --mode burst     # 대량 버스트 생성
"""

import json
import time
import random
import argparse
import uuid
from datetime import datetime, timezone, timedelta
from confluent_kafka import Producer

BOOTSTRAP_SERVERS = "localhost:30092,localhost:30093,localhost:30094"
TOPIC = "nexuspay.events.ingested"

EVENT_TYPES = ["PAYMENT", "TRANSFER", "WITHDRAWAL"]
CURRENCIES = ["KRW", "KRW", "KRW", "USD"]  # KRW 가중
STATUSES = ["COMPLETED", "COMPLETED", "COMPLETED", "PENDING", "FAILED"]

def create_event(user_id=None, event_type=None, amount=None, timestamp=None):
  """단일 Nexus Pay 이벤트 생성."""
  return {
      "event_id": str(uuid.uuid4()),
      "event_type": event_type or random.choice(EVENT_TYPES),
      "user_id": user_id or random.randint(1001, 2000),
      "amount": amount or round(random.uniform(1000, 3000000), 0),
      "currency": random.choice(CURRENCIES),
      "status": random.choice(STATUSES),
      "data_source": "payment-api",
      "event_timestamp": (timestamp or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ"),
      "schema_version": "1.0"
  }

def generate_normal(producer, count=100, interval=0.5):
  """정상 거래 이벤트 생성."""
  print(f"[NORMAL] {count}건 정상 거래 생성 시작 (간격: {interval}초)")
  for i in range(count):
    event = create_event()
    producer.produce(TOPIC, key=str(event["user_id"]), value=json.dumps(event))
    producer.poll(0)
    if (i + 1) % 10 == 0:
      print(f"  ... {i + 1}/{count}건 전송")
    time.sleep(interval)
    producer.flush()
    print(f"[NORMAL] {count}건 전송 완료")

def generate_fraud(producer, count=50):
  """이상거래 패턴 포함 이벤트 생성."""
  print(f"[FRAUD] 이상거래 패턴 포함 {count}건 생성 시작")

  fraud_user = random.randint(1001, 2000)

  for i in range(count):
    if i % 10 == 0:
      #  패턴 1: 동일 사용자 1분 내 연속 5건 (임계값 3건 초과)
      print(f"  [패턴1] user_id={fraud_user} 연속 5건 발생")
      base_time = datetime.now(timezone.utc)
      for j in range(5):
        event = create_event(
          user_id=fraud_user,
          event_type="PAYMENT",
          amount=random.uniform(100000, 500000),
          timestamp=(base_time + timedelta(seconds=j * 10)).strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        producer.produce(TOPIC, key=str(event["user_id"]), value=json.dumps(event))
        producer.poll(0)
        time.sleep(0.1)

    elif i % 15 == 0:
      # 패턴 2: 단건 고액 거래 (500만원 초과)
      high_amount = random.uniform(5_000_001, 50_000_000)
      event = create_event(amount=high_amount, event_type="TRANSFER")
      print(f"  [패턴2] 고액 거래: {high_amount:,.0f}원")
      producer.produce(TOPIC, key=str(event["user_id"]), value=json.dumps(event))
      producer.poll(0)

    else:
      event = create_event()
      producer.produce(TOPIC, key=str(event["user_id"]), value=json.dumps(event))
      producer.poll(0)

    time.sleep(0.3)
  producer.flush()
  print(f"[FRAUD] {count}건 전송 완료")

def generate_late(producer, count=50):
  """지연 데이터 포함 이벤트 생성 — Watermark 테스트용."""
  print(f"[LATE] 지연 데이터 포함 {count}건 생성 시작")
  for i in range(count):
    if i % 8 == 0:
      # 10~30초 전 타임스탬프를 가진 지연 이벤트
      delay_seconds = random.randint(10, 30)
      late_time = datetime.now(timezone.utc) - timedelta(seconds=delay_seconds)
      event = create_event(timestamp=late_time)
      print(f"  [LATE] {delay_seconds}초 지연 이벤트: {event['event_timestamp']}")
    else:
      event = create_event()
    producer.produce(TOPIC, key=str(event["user_id"]), value=json.dumps(event))
    producer.poll(0)
    time.sleep(0.3)

  producer.flush()
  print(f"[LATE] {count}건 전송 완료")

def generate_burst(producer, count=500):
  """대량 버스트 이벤트 생성 — 시스템 부하 테스트용."""
  print(f"[BURST] 대량 버스트 {count}건 생성 시작")
  for i in range(count):
    event = create_event()
    producer.produce(TOPIC, key=str(event["user_id"]), value=json.dumps(event))
    producer.poll(0)
  producer.flush()
  print(f"[BURST] {count}건 전송 완료 (무간격)")

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Flink 실습용 Nexus Pay 이벤트 생성기")
  parser.add_argument("--mode", choices=["normal", "fraud", "late", "burst"], default="normal")
  parser.add_argument("--count", type=int, default=100)
  parser.add_argument("--interval", type=float, default=0.5,
                        help="정상 이벤트 사이 간격(초). normal 모드에서만 적용.")
  args = parser.parse_args()

  producer = Producer({"bootstrap.servers": BOOTSTRAP_SERVERS})


  modes = {
        "normal": lambda: generate_normal(producer, args.count, args.interval),
        "fraud": lambda: generate_fraud(producer, args.count),
        "late": lambda: generate_late(producer, args.count),
        "burst": lambda: generate_burst(producer, args.count),
  }
  modes[args.mode]()
  producer.flush()