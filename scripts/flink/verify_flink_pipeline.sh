#!/bin/bash
# Week 4 Flink 파이프라인 통합 검증 스크립트

PASS=0
FAIL=0

if [ -z "$PYTHON_BIN" ]; then
    if [ -x ".venv/Scripts/python.exe" ]; then
        PYTHON_BIN=".venv/Scripts/python.exe"
    else
        PYTHON_BIN="python"
    fi
fi

check() {
    if [ $1 -eq 0 ]; then
        echo "  ✅ $2"
        PASS=$((PASS + 1))
    else
        echo "  ❌ $2"
        FAIL=$((FAIL + 1))
    fi
}

echo "=========================================="
echo " Week 4: Flink 파이프라인 통합 검증"
echo "=========================================="
echo ""

# 1. Flink 클러스터 상태
echo "[1] Flink 클러스터 상태"
FLINK_STATUS=$(curl -sf http://localhost:8081/overview 2>/dev/null)
echo "$FLINK_STATUS" | "$PYTHON_BIN" -c "import sys,json; d=json.load(sys.stdin); exit(0 if d.get('taskmanagers',0)>0 else 1)" 2>/dev/null
check $? "Flink TaskManager 활성"

SLOTS=$(echo "$FLINK_STATUS" | "$PYTHON_BIN" -c "import sys,json; print(json.load(sys.stdin).get('slots-available',0))" 2>/dev/null | tr -d '\r')
echo "     사용 가능 슬롯: $SLOTS"

# 2. Flink 잡 실행 상태
echo ""
echo "[2] Flink 잡 상태"
RUNNING_JOBS=$(curl -sf http://localhost:8081/jobs 2>/dev/null | "$PYTHON_BIN" -c "
import sys,json
jobs = [j for j in json.load(sys.stdin).get('jobs',[]) if j['status']=='RUNNING']
print(len(jobs))
" 2>/dev/null | tr -d '\r')
[ "$RUNNING_JOBS" -ge 1 ] 2>/dev/null
check $? "실행 중인 잡 존재 ($RUNNING_JOBS건)"

# 3. 소스 토픽 데이터 존재
echo ""
echo "[3] Kafka 토픽 검증"
docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka-1:9092 --list 2>/dev/null | grep -q "nexuspay.events.ingested"
check $? "소스 토픽 nexuspay.events.ingested 존재"

docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka-1:9092 --list 2>/dev/null | grep -q "nexuspay.aggregation.5min"
check $? "집계 토픽 nexuspay.aggregation.5min 존재"

docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka-1:9092 --list 2>/dev/null | grep -q "nexuspay.alerts.fraud"
check $? "알림 토픽 nexuspay.alerts.fraud 존재"

# 4. 이벤트 주입 및 결과 확인
# 주: 이벤트 생성기의 stderr는 의도적으로 출력한다. 스크립트 실패 시
#     Python 문법 오류/트레이스백을 즉시 확인할 수 있어야 원인 파악이 쉽다.
echo ""
echo "[4] 이벤트 주입 테스트"
"$PYTHON_BIN" scripts/flink/flink_event_generator.py --mode fraud --count 30
check $? "이벤트 생성기 실행 성공"

sleep 10

# 알림 토픽에 메시지 도착 확인
ALERT_COUNT=$(docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka-1:9092 \
  --topic nexuspay.alerts.fraud \
  --from-beginning --timeout-ms 5000 2>/dev/null | wc -l)
[ "$ALERT_COUNT" -ge 1 ] 2>/dev/null
check $? "이상거래 알림 생성 확인 ($ALERT_COUNT건)"

# 5. 체크포인트 상태
echo ""
echo "[5] 체크포인트 상태"
for JOB_ID in $(curl -sf http://localhost:8081/jobs 2>/dev/null | "$PYTHON_BIN" -c "
import sys,json
for j in json.load(sys.stdin).get('jobs',[]):
    if j['status']=='RUNNING': print(j['id'])
" 2>/dev/null | tr -d '\r'); do
    CP_COMPLETED=$(curl -sf "http://localhost:8081/jobs/$JOB_ID/checkpoints" 2>/dev/null | \
      "$PYTHON_BIN" -c "import sys,json; print(json.load(sys.stdin).get('counts',{}).get('completed',0))" 2>/dev/null | tr -d '\r')
    [ "$CP_COMPLETED" -ge 1 ] 2>/dev/null
    check $? "잡 $JOB_ID 체크포인트 완료 ($CP_COMPLETED건)"
done

# 6. Redis 알림 캐시
echo ""
echo "[6] Redis 캐시 상태"
REDIS_KEYS=$(docker exec -e REDISCLI_AUTH=redis lab-redis redis-cli KEYS "fraud:*" 2>/dev/null | wc -l)
[ "$REDIS_KEYS" -ge 1 ] 2>/dev/null
check $? "Redis 알림 캐시 존재 ($REDIS_KEYS 키)"

echo ""
echo "=========================================="
echo " 결과: ✅ $PASS건 통과 / ❌ $FAIL건 실패"
echo "=========================================="
