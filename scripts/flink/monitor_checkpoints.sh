#!/bin/bash
# Flink 체크포인트 상태 모니터링

FLINK_URL="http://localhost:8081"

echo "=== Flink 잡 & 체크포인트 모니터링 ==="
echo ""

# 실행 중인 잡 목록
JOBS=$(curl -s "$FLINK_URL/jobs" | python3 -c '
import sys, json
data = json.load(sys.stdin)
for j in data.get("jobs", []):
    print("{} [{}]".format(j.get("id", ""), j.get("status", "UNKNOWN")))
')
echo "실행 중인 잡:"
echo "$JOBS"
echo ""

# 각 잡의 체크포인트 상태
for JOB_ID in $(curl -s "$FLINK_URL/jobs" | python3 -c '
import sys, json
for j in json.load(sys.stdin).get("jobs", []):
    if j.get("status") == "RUNNING":
        print(j.get("id", ""))
'); do
    echo "--- 잡: $JOB_ID ---"
    curl -s "$FLINK_URL/jobs/$JOB_ID/checkpoints" | python3 -c '
import sys, json
data = json.load(sys.stdin)
counts = data.get("counts", {})
print("  완료: {}건".format(counts.get("completed", 0)))
print("  실패: {}건".format(counts.get("failed", 0)))
print("  진행중: {}건".format(counts.get("in_progress", 0)))

latest = data.get("latest", {}).get("completed", {})
if latest:
    print("  최근 체크포인트 ID: {}".format(latest.get("id")))
    print("  소요 시간: {}ms".format(latest.get("end_to_end_duration", 0)))
    print("  상태 크기: {} bytes".format(latest.get("state_size", 0)))

restored = data.get("latest", {}).get("restored", {})
if restored:
    print("  복구된 체크포인트: {} (장애 복구)".format(restored.get("id")))
'
    echo ""
done
