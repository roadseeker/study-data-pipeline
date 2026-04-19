#!/usr/bin/env bash

set -euo pipefail

echo "[INFO] Session Window 검증 시작"
echo "[INFO] 전제: SessionWindowAnalysisJob 이 RUNNING 상태여야 함"

command python - << 'PYEOF'
import json
import time
import uuid
from datetime import datetime, timezone, timedelta
from confluent_kafka import Producer

producer = Producer({"bootstrap.servers": "localhost:30092,localhost:30093,localhost:30094"})
topic = "nexuspay.events.ingested"
anchor = datetime.now(timezone.utc) - timedelta(minutes=6)

events = [
    {"user_id": 9001, "event_type": "PAYMENT", "amount": 120000, "offset": timedelta(seconds=0)},
    {"user_id": 9001, "event_type": "PAYMENT", "amount": 80000, "offset": timedelta(seconds=35)},
    {"user_id": 9001, "event_type": "TRANSFER", "amount": 150000, "offset": timedelta(minutes=3, seconds=10)},
    {"user_id": 9001, "event_type": "WITHDRAWAL", "amount": 60000, "offset": timedelta(minutes=3, seconds=40)},
    {"user_id": 9002, "event_type": "PAYMENT", "amount": 70000, "offset": timedelta(minutes=1)},
    {"user_id": 9003, "event_type": "PAYMENT", "amount": 10000, "offset": timedelta(minutes=7)},
]

for idx, event in enumerate(events, start=1):
    timestamp = (anchor + event["offset"]).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload = {
        "event_id": str(uuid.uuid4()),
        "event_type": event["event_type"],
        "user_id": event["user_id"],
        "amount": event["amount"],
        "currency": "KRW",
        "status": "COMPLETED",
        "data_source": "payment-api",
        "event_timestamp": timestamp,
        "schema_version": "1.0"
    }
    print(f"[SESSION] {idx}/6 user={payload['user_id']} amount={payload['amount']} ts={timestamp}")
    producer.produce(topic, key=str(payload["user_id"]), value=json.dumps(payload))
    producer.poll(0)
    time.sleep(0.2)

producer.flush()
PYEOF

echo "[INFO] 세션 윈도우 종료 대기"
sleep 15

SESSION_LOGS="$(docker logs lab-flink-tm --tail 1000 2>&1 | grep "SESSION" || true)"

if [[ -z "${SESSION_LOGS}" ]]; then
  echo "[ERROR] SESSION 로그를 찾지 못했습니다."
  exit 1
fi

echo "${SESSION_LOGS}"

grep -q "SESSION:.*userId=9001, count=2, total=200000" <<< "${SESSION_LOGS}"
grep -q "SESSION:.*userId=9001, count=2, total=210000" <<< "${SESSION_LOGS}"
grep -q "SESSION:.*userId=9002, count=1, total=70000" <<< "${SESSION_LOGS}"

echo "[INFO] Session Window 검증 성공"
