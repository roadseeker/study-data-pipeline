#!/bin/bash
# NiFi 다중 소스 수집 파이프라인 종합 검증

echo "============================================"
echo " Nexus Pay NiFi 파이프라인 종합 검증"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
echo ""

PASS=0
FAIL=0

check() {
  local name=$1
  local cmd=$2
  printf "  %-35s : " "$name"
  if eval "$cmd" > /dev/null 2>&1; then
    echo "✅ OK"
    ((PASS++))
  else
    echo "❌ FAIL"
    ((FAIL++))
  fi
}

echo "[1. 인프라 서비스]"
check "NiFi 웹 UI" "curl -skf https://localhost:8443/nifi/"
check "결제 API 시뮬레이터" "curl -sf http://localhost:5050/health"
check "PostgreSQL (고객 테이블)" "docker exec lab-postgres psql -U pipeline -d pipeline_db -c 'SELECT count(*) FROM customers;'"
check "Kafka 클러스터" "docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka-1:9092 --list"

echo ""
echo "[2. Kafka 토픽]"
check "nexuspay.events.ingested 토픽" "docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka-1:9092 --describe --topic nexuspay.events.ingested"
check "nexuspay.events.dlq 토픽" "docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka-1:9092 --describe --topic nexuspay.events.dlq"

echo ""
echo "[3. 데이터 흐름 검증]"
# API → Kafka 메시지 존재 확인
check "API 소스 메시지" "docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka-1:9092 --topic nexuspay.events.ingested --from-beginning --timeout-ms 5000 2>/dev/null | grep payment-api"
# CSV → Kafka 메시지 존재 확인
check "CSV 소스 메시지" "docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka-1:9092 --topic nexuspay.events.ingested --from-beginning --timeout-ms 5000 2>/dev/null | grep settlement-csv"
# DB → Kafka 메시지 존재 확인
check "DB 소스 메시지" "docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka-1:9092 --topic nexuspay.events.ingested --from-beginning --timeout-ms 5000 2>/dev/null | grep customer-db"

echo ""
echo "[4. 소스별 메시지 통계]"
docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka-1:9092 \
  --topic nexuspay.events.ingested \
  --from-beginning \
  --timeout-ms 10000 2>/dev/null | \
python3 -c "
import sys, json
from collections import Counter
sources = Counter()
for line in sys.stdin:
    try:
        msg = json.loads(line.strip())
        sources[msg.get('data_source', 'unknown')] += 1
    except: pass
for src, cnt in sorted(sources.items()):
    print(f'  {src}: {cnt}건')
print(f'  합계: {sum(sources.values())}건')
" 2>/dev/null

echo ""
echo "============================================"
echo " 결과: ✅ ${PASS} 통과 / ❌ ${FAIL} 실패"
echo "============================================"
