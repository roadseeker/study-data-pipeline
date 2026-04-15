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
declare -a UNIQUE_USER_POOL=()
pool_index=0
CURRENT_USER_A=""
CURRENT_USER_B=""
CURRENT_USER_C=""

echo "============================================"
echo " Nexus Pay customer update simulator"
echo " interval=${INTERVAL_SECONDS}s iterations=${ITERATIONS}"
echo " container=${POSTGRES_CONTAINER} db=${POSTGRES_DB}"
echo "============================================"

prepare_unique_pool() {
  local required_count="$1"

  if [[ "${required_count}" -gt 1000 ]]; then
    echo "ERROR: requested ${required_count} unique users, but only 1000 users are available." >&2
    exit 1
  fi

  mapfile -t UNIQUE_USER_POOL < <(seq 1 1000 | shuf -n "${required_count}")
}

draw_three_unique_users() {
  if [[ "${ITERATIONS}" != "0" ]]; then
    CURRENT_USER_A="${UNIQUE_USER_POOL[pool_index]}"
    CURRENT_USER_B="${UNIQUE_USER_POOL[pool_index + 1]}"
    CURRENT_USER_C="${UNIQUE_USER_POOL[pool_index + 2]}"
    pool_index=$((pool_index + 3))
    return
  fi

  local user_a user_b user_c
  user_a=$(( (RANDOM % 1000) + 1 ))
  while true; do
    user_b=$(( (RANDOM % 1000) + 1 ))
    [[ "${user_b}" != "${user_a}" ]] && break
  done
  while true; do
    user_c=$(( (RANDOM % 1000) + 1 ))
    [[ "${user_c}" != "${user_a}" && "${user_c}" != "${user_b}" ]] && break
  done

  CURRENT_USER_A="${user_a}"
  CURRENT_USER_B="${user_b}"
  CURRENT_USER_C="${user_c}"
}

run_update_batch() {
  draw_three_unique_users

  docker exec "${POSTGRES_CONTAINER}" psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "
    UPDATE customers
       SET grade = CASE
                     WHEN grade = 'NORMAL' THEN 'VIP'
                     WHEN grade = 'VIP' THEN 'PREMIUM'
                     ELSE 'NORMAL'
                   END,
           updated_at = NOW()
     WHERE user_id = ${CURRENT_USER_A};

    UPDATE customers
       SET email = 'user_' || user_id || '_updated_' || to_char(NOW(), 'HH24MISS') || '@nexuspay.io',
           updated_at = NOW()
     WHERE user_id = ${CURRENT_USER_B};

    UPDATE customers
       SET is_active = NOT is_active,
           updated_at = NOW()
     WHERE user_id = ${CURRENT_USER_C};
  " >/dev/null

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] updated users: ${CURRENT_USER_A}, ${CURRENT_USER_B}, ${CURRENT_USER_C}"
}

if [[ "${ITERATIONS}" != "0" ]]; then
  prepare_unique_pool "$((ITERATIONS * 3))"
fi

while true; do
  iteration=$((iteration + 1))
  run_update_batch

  if [[ "${ITERATIONS}" != "0" && "${iteration}" -ge "${ITERATIONS}" ]]; then
    break
  fi

  sleep "${INTERVAL_SECONDS}"
done

echo "Simulation finished after ${iteration} iteration(s)."
