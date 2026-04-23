#!/bin/bash
# =============================================================
# scripts/foundation/healthcheck-all.sh
# Pipeline Lab — 전체 환경 헬스체크 스크립트
# Foundation: 공통 인프라 기동 상태 점검
# =============================================================

set -u

echo "============================================"
echo " Pipeline Lab — 전체 환경 헬스체크"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
echo ""

PASS=0
FAIL=0
PYTHON_BIN="${PYTHON_BIN:-python}"

# Kafka 컨테이너명 자동 감지 (단일 브로커 vs 멀티 브로커)
if docker ps --format '{{.Names}}' | grep -q '^lab-kafka-1$'; then
	KAFKA_CONTAINER="lab-kafka-1"
	KAFKA_BOOTSTRAP="kafka-1:9092"
else
	KAFKA_CONTAINER="lab-kafka"
	KAFKA_BOOTSTRAP="localhost:9092"
fi

# 헬스체크 함수
check() {
	local name=$1
	local cmd=$2
	printf "  %-20s : " "$name"
	if eval "$cmd" >/dev/null 2>&1; then
		echo "✅ OK"
		((PASS++))
	else
		echo "❌ FAIL"
		((FAIL++))
	fi
}

check_retry() {
	local name=$1
	local cmd=$2
	local retries=${3:-5}
	local delay=${4:-3}
	local attempt=1

	printf "  %-20s : " "$name"
	while [ "$attempt" -le "$retries" ]; do
		if eval "$cmd" >/dev/null 2>&1; then
			echo "✅ OK"
			((PASS++))
			return 0
		fi
		if [ "$attempt" -lt "$retries" ]; then
			sleep "$delay"
		fi
		attempt=$((attempt + 1))
	done

	echo "❌ FAIL"
	((FAIL++))
	return 1
}

check_flink_taskmanager() {
	printf "  %-20s : " "Flink TaskManager"
	if curl -sf http://localhost:8081/overview | "$PYTHON_BIN" -c 'import sys, json; data = json.load(sys.stdin); raise SystemExit(0 if data.get("taskmanagers", 0) >= 1 else 1)' >/dev/null 2>&1; then
		echo "✅ OK"
		((PASS++))
	else
		echo "❌ FAIL"
		((FAIL++))
	fi
}

check_spark_worker() {
	printf "  %-20s : " "Spark Worker"
	if curl -sf http://localhost:8082/json/ | "$PYTHON_BIN" -c 'import sys, json; data = json.load(sys.stdin); workers = data.get("workers", []); alive = [w for w in workers if w.get("state") == "ALIVE"]; raise SystemExit(0 if len(alive) >= 1 else 1)' >/dev/null 2>&1; then
		echo "✅ OK"
		((PASS++))
	else
		echo "❌ FAIL"
		((FAIL++))
	fi
}

echo "[기반 서비스]"
check "PostgreSQL" "docker exec lab-postgres pg_isready -U pipeline"
check "Redis" "docker exec -e REDISCLI_AUTH=redis lab-redis redis-cli ping"

echo ""
echo "[메시징·수집]"
check "Kafka" "docker exec ${KAFKA_CONTAINER} sh -c '/opt/kafka/bin/kafka-topics.sh --bootstrap-server ${KAFKA_BOOTSTRAP} --list'"
check_retry "NiFi" "curl -skf https://localhost:8443/nifi/" 5 5

echo ""
echo "[처리·오케스트레이션]"
check "Flink JobManager" "curl -sf http://localhost:8081/overview"
check_flink_taskmanager
check "Spark Master" "curl -sf http://localhost:8082/"
check_spark_worker
check_retry "Airflow" "curl -sf http://localhost:8083/health" 5 5

echo ""
echo "============================================"
echo " 결과: ✅ ${PASS} 통과 / ❌ ${FAIL} 실패"
echo "============================================"

# 실패 항목이 있으면 종료 코드 1 반환
if [ "${FAIL}" -gt 0 ]; then
	exit 1
fi
