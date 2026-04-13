#!/usr/bin/env bash
set -euo pipefail

# Nexus Pay customers 테이블 변경 시뮬레이터
# - NiFi QueryDatabaseTable 증분 수집 검증용
# - 지정한 간격마다 고객 3건을 업데이트한다.

INTERVAL_SECONDS="${1:-30}"
ITERATIONS="${2:-0}"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-lab-postgres}"
POSTGRES_DB="${POSTGRES_DB:-pipeline_db}"
POSTGRES_USER="${POSTGRES_USER:-pipeline}"

iteration=0

echo "============================================"
echo " Nexus Pay customer update simulator"
echo " interval=${INTERVAL_SECONDS}s iterations=${ITERATIONS}"
echo " container=${POSTGRES_CONTAINER} db=${POSTGRES_DB}"
echo "============================================"

run_update_batch() {
  local user_a user_b user_c
  user_a=$(( (RANDOM % 1000) + 1 ))
  user_b=$(( (RANDOM % 1000) + 1 ))
  user_c=$(( (RANDOM % 1000) + 1 ))

  docker exec "${POSTGRES_CONTAINER}" psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "
    UPDATE customers
       SET grade = CASE
                     WHEN grade = 'NORMAL' THEN 'VIP'
                     WHEN grade = 'VIP' THEN 'PREMIUM'
                     ELSE 'NORMAL'
                   END,
           updated_at = NOW()
     WHERE user_id = ${user_a};

    UPDATE customers
       SET email = 'user_' || user_id || '_updated_' || to_char(NOW(), 'HH24MISS') || '@nexuspay.io',
           updated_at = NOW()
     WHERE user_id = ${user_b};

    UPDATE customers
       SET is_active = NOT is_active,
           updated_at = NOW()
     WHERE user_id = ${user_c};
  " >/dev/null

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] updated users: ${user_a}, ${user_b}, ${user_c}"
}

while true; do
  iteration=$((iteration + 1))
  run_update_batch

  if [[ "${ITERATIONS}" != "0" && "${iteration}" -ge "${ITERATIONS}" ]]; then
    break
  fi

  sleep "${INTERVAL_SECONDS}"
done

echo "Simulation finished after ${iteration} iteration(s)."
