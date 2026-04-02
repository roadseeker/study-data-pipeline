#!/bin/bash
# =============================================================
# scripts/healthcheck-all.sh
# Pipeline Lab — 전체 환경 헬스체크 스크립트
# Week 1: 데이터 파이프라인 실습 환경 구성
# =============================================================

echo "============================================"
echo " Pipeline Lab — 전체 환경 헬스체크"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
echo ""

PASS=0
FAIL=0

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
  if eval "$cmd" > /dev/null 2>&1; then
    echo "✅ OK"
    ((PASS++))
  else
    echo "❌ FAIL"
    ((FAIL++))
  fi
}

echo "[기반 서비스]"
check "PostgreSQL" "docker exec lab-postgres pg_isready -U pipeline"
check "Redis"      "docker exec -e REDISCLI_AUTH=redis lab-redis redis-cli ping"

echo ""
echo "[메시징·수집]"
check "Kafka" "docker exec ${KAFKA_CONTAINER} sh -c '/opt/kafka/bin/kafka-topics.sh --bootstrap-server ${KAFKA_BOOTSTRAP} --list'"
check "NiFi"  "curl -sf http://localhost:8080/nifi/"

echo ""
echo "[처리·오케스트레이션]"
check "Flink JobManager" "curl -sf http://localhost:8081/overview"
check "Spark Master"     "curl -sf http://localhost:8082/"
check "Airflow"          "curl -sf http://localhost:8083/health"

echo ""
echo "============================================"
echo " 결과: ✅ ${PASS} 통과 / ❌ ${FAIL} 실패"
echo "============================================"

# 실패 항목이 있으면 종료 코드 1 반환
if [ "${FAIL}" -gt 0 ]; then
  exit 1
fi
