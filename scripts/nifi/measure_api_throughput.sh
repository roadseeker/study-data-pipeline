#!/bin/bash

set -euo pipefail

API_URL="${API_URL:-http://localhost:5050/health}"
MEASURE_SECONDS="${MEASURE_SECONDS:-300}"

read_seq() {
	curl -s "${API_URL}" | python3 -c "import sys, json; print(json.load(sys.stdin)['seq'])"
}

echo "============================================"
echo " Nexus Pay API 수집 처리량 측정"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo " 측정 대상: ${API_URL}"
echo " 측정 시간: ${MEASURE_SECONDS}초"
echo "============================================"

echo "시작 카운터를 확인합니다..."
START_COUNT="$(read_seq)"
START_TS="$(date '+%Y-%m-%d %H:%M:%S')"

echo "${MEASURE_SECONDS}초 동안 대기하며 이벤트 증가량을 추적합니다..."
sleep "${MEASURE_SECONDS}"

END_COUNT="$(read_seq)"
END_TS="$(date '+%Y-%m-%d %H:%M:%S')"
TOTAL=$((END_COUNT - START_COUNT))

if [ "${MEASURE_SECONDS}" -gt 0 ]; then
	PER_MIN=$(python3 -c "print(round(${TOTAL} / (${MEASURE_SECONDS} / 60), 2))")
	PER_SEC=$(python3 -c "print(round(${TOTAL} / ${MEASURE_SECONDS}, 2))")
else
	PER_MIN="0"
	PER_SEC="0"
fi

echo
echo "[측정 결과]"
echo " 시작 시각: ${START_TS}"
echo " 종료 시각: ${END_TS}"
echo " 시작 카운터: ${START_COUNT}"
echo " 종료 카운터: ${END_COUNT}"
echo " 총 생성 이벤트: ${TOTAL}건"
echo " 분당 평균: ${PER_MIN}건"
echo " 초당 평균: ${PER_SEC}건"
