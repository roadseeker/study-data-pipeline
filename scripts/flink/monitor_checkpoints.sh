#!/bin/bash
# Flink 체크포인트 상태 모니터링

FLINK_URL="${FLINK_URL:-http://localhost:8081}"

echo "=== Flink 잡 & 체크포인트 모니터링 ==="
echo ""

fetch_json() {
  curl -sf "$1"
}

json_number() {
  local json="$1"
  local key="$2"
  echo "$json" | grep -o "\"$key\":[0-9]*" | head -1 | sed "s/\"$key\"://"
}

jobs_json="$(fetch_json "$FLINK_URL/jobs")"
if [ -z "$jobs_json" ]; then
  echo "ERROR: Flink REST API에 연결할 수 없습니다: $FLINK_URL" >&2
  exit 1
fi

job_rows="$(echo "$jobs_json" | grep -o '{"id":"[^"]*","status":"[^"]*"}')"

echo "실행 중인 잡:"
if [ -z "$job_rows" ]; then
  echo "  없음"
else
  echo "$job_rows" | while IFS= read -r row; do
    job_id="$(echo "$row" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p')"
    status="$(echo "$row" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')"
    echo "$job_id [$status]"
  done
fi
echo ""

echo "$job_rows" | while IFS= read -r row; do
  status="$(echo "$row" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')"
  [ "$status" = "RUNNING" ] || continue

  job_id="$(echo "$row" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p')"
  echo "--- 잡: $job_id ---"

  cp_json="$(fetch_json "$FLINK_URL/jobs/$job_id/checkpoints")"
  if [ -z "$cp_json" ]; then
    echo "  ERROR: 체크포인트 정보를 가져올 수 없습니다."
    echo ""
    continue
  fi

  completed="$(json_number "$cp_json" "completed")"
  failed="$(json_number "$cp_json" "failed")"
  in_progress="$(json_number "$cp_json" "in_progress")"

  echo "  완료: ${completed:-0}건"
  echo "  실패: ${failed:-0}건"
  echo "  진행중: ${in_progress:-0}건"

  latest_completed="$(echo "$cp_json" | sed -n 's/.*"latest":{"completed":{\([^}]*\)}.*/\1/p')"
  if [ -n "$latest_completed" ]; then
    cp_id="$(json_number "$latest_completed" "id")"
    duration="$(json_number "$latest_completed" "end_to_end_duration")"
    state_size="$(json_number "$latest_completed" "state_size")"
    echo "  최근 체크포인트 ID: ${cp_id:-N/A}"
    echo "  소요 시간: ${duration:-0}ms"
    echo "  상태 크기: ${state_size:-0} bytes"
  fi

  restored="$(echo "$cp_json" | sed -n 's/.*"restored":{"id":\([0-9]*\).*/\1/p')"
  if [ -n "$restored" ]; then
    echo "  복구된 체크포인트: $restored (장애 복구)"
  fi
  echo ""
done
