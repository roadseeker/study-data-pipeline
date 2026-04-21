#!/usr/bin/env python3
"""
Kafka nexuspay.alerts.fraud 토픽을 소비하여 Redis에 캐싱.
실시간 대시보드에서 조회할 수 있도록 사용자별 최근 알림을 저장한다.

Redis 키 구조:
  fraud:alert:latest:{user_id}  — 사용자별 최신 알림 (Hash)
  fraud:alert:count:{user_id}   — 사용자별 누적 알림 수 (Counter)
  fraud:alerts:recent            — 최근 100건 알림 (Sorted Set, score=timestamp)
"""

import json
import redis
import time
from confluent_kafka import Consumer, KafkaError

KAFKA_SERVERS = 'localhost:30092,localhost:30093,localhost:30094'
TOPIC = 'nexuspay.alerts.fraud'
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_PASSWORD = 'redis'

def main():
    consumer = Consumer({
        'bootstrap.servers': KAFKA_SERVERS,
        'group.id': 'fraud-alert-redis-sink',
        'auto.offset.reset': 'latest'
    })

    consumer.subscribe([TOPIC])
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, decode_responses=True
                    )
    print("[Redis Sink] 시작 - {TOPIC} -> Redis 캐싱")

    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue
        alert = json.loads(msg.value().decode('utf-8'))
        user_id = alert['user_id']

        # 1. 사용자별 최신 알림
        r.hset(f"fraud:alert:latest:{user_id}", mapping=alert)
        r.expire(f"fraud:alert:latest:{user_id}", 86400)  # 1시간 후 만료

        # 2. 사용자별 알림 카운터
        r.incr(f"fraud:alert:count:{user_id}")

        # 3. 최근 100건 알림 저장 (score=timestamp)
        score = time.time()
        r.zadd("fraud:alerts:recent", {json.dumps(alert): score})
        r.zremrangebyrank("fraud:alerts:recent", 0, -101)  # 100건 초과 시 오래된 알림 제거

        print(f" [{alert['rule_id']}] user={user_id}, alert_id={alert['alert_id']} -> Redis 캐싱 완료")

if __name__ == "__main__":
    main()
