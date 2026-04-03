#!/usr/bin/env bash
set -euo pipefail

# Nexus Pay Kafka partition sizing helper
#
# Formula:
#   recommended partitions = max(throughput-based, consumer-parallelism-based)
#   final partitions       = round up(recommended * headroom factor) to an even number
#
# Defaults reflect the Week 2 lab assumptions documented in:
#   - config/kafka/partition-sizing-guide.md
#   - docs/02_week2_lab_guide.md
#
# All values can be overridden through environment variables, for example:
#   AVG_MSG_PER_SEC=80 FRAUD_CONSUMERS=4 bash scripts/partition-calculator.sh

AVG_MSG_PER_SEC="${AVG_MSG_PER_SEC:-50}"
SINGLE_PARTITION_THROUGHPUT="${SINGLE_PARTITION_THROUGHPUT:-10}"
FRAUD_CONSUMERS="${FRAUD_CONSUMERS:-3}"
SETTLEMENT_CONSUMERS="${SETTLEMENT_CONSUMERS:-2}"
HEADROOM_NUMERATOR="${HEADROOM_NUMERATOR:-3}"   # 1.5x = 3 / 2
HEADROOM_DENOMINATOR="${HEADROOM_DENOMINATOR:-2}"
DLQ_PARTITIONS="${DLQ_PARTITIONS:-2}"

if (( AVG_MSG_PER_SEC <= 0 )); then
  echo "ERROR: AVG_MSG_PER_SEC must be greater than 0." >&2
  exit 1
fi

if (( SINGLE_PARTITION_THROUGHPUT <= 0 )); then
  echo "ERROR: SINGLE_PARTITION_THROUGHPUT must be greater than 0." >&2
  exit 1
fi

if (( FRAUD_CONSUMERS <= 0 || SETTLEMENT_CONSUMERS <= 0 )); then
  echo "ERROR: FRAUD_CONSUMERS and SETTLEMENT_CONSUMERS must be greater than 0." >&2
  exit 1
fi

if (( HEADROOM_NUMERATOR <= 0 || HEADROOM_DENOMINATOR <= 0 )); then
  echo "ERROR: headroom factor values must be greater than 0." >&2
  exit 1
fi

# Ceiling division for throughput-based minimum partitions.
THROUGHPUT_PARTITIONS=$(( (AVG_MSG_PER_SEC + SINGLE_PARTITION_THROUGHPUT - 1) / SINGLE_PARTITION_THROUGHPUT ))
MAX_CONSUMERS=$(( FRAUD_CONSUMERS > SETTLEMENT_CONSUMERS ? FRAUD_CONSUMERS : SETTLEMENT_CONSUMERS ))
RECOMMENDED=$(( THROUGHPUT_PARTITIONS > MAX_CONSUMERS ? THROUGHPUT_PARTITIONS : MAX_CONSUMERS ))

# Apply headroom factor and round up.
HEADROOM_APPLIED=$(( (RECOMMENDED * HEADROOM_NUMERATOR + HEADROOM_DENOMINATOR - 1) / HEADROOM_DENOMINATOR ))

# Round up to the next even number for easier operational scaling.
FINAL=$(( (HEADROOM_APPLIED + 1) / 2 * 2 ))

# Withdrawal traffic is assumed to be lower than payment / transfer traffic.
WITHDRAWAL_RECOMMENDED=$(( (FINAL * 2 + 2) / 3 ))

# PoC lab downsizing rules from the guide.
POC_PAYMENT_PARTITIONS=$(( FINAL < 6 ? FINAL : 6 ))
POC_TRANSFER_PARTITIONS=$POC_PAYMENT_PARTITIONS
POC_WITHDRAWAL_PARTITIONS=$(( WITHDRAWAL_RECOMMENDED < 4 ? WITHDRAWAL_RECOMMENDED : 4 ))

echo "============================================"
echo " Nexus Pay 파티션 수 산정 결과"
echo "============================================"
echo " 기준 입력값"
echo "  평균 처리량 기준         : ${AVG_MSG_PER_SEC} msg/s"
echo "  단일 파티션 처리량 기준  : ${SINGLE_PARTITION_THROUGHPUT} msg/s"
echo "  이상거래 탐지 컨슈머 수  : ${FRAUD_CONSUMERS}"
echo "  정산 컨슈머 수           : ${SETTLEMENT_CONSUMERS}"
echo "  여유 계수                : ${HEADROOM_NUMERATOR}/${HEADROOM_DENOMINATOR}x"
echo ""
echo " 계산 결과"
echo "  처리량 기준 최소 파티션  : ${THROUGHPUT_PARTITIONS}"
echo "  병렬성 기준 최소 파티션  : ${MAX_CONSUMERS}"
echo "  기준 선택값              : ${RECOMMENDED}"
echo "  여유 계수 적용 후        : ${HEADROOM_APPLIED}"
echo "  최종 권장 파티션 수      : ${FINAL}"
echo ""
echo " 권장 토픽별 파티션"
echo "  nexuspay.transactions.payment     : ${FINAL}"
echo "  nexuspay.transactions.transfer    : ${FINAL}"
echo "  nexuspay.transactions.withdrawal  : ${WITHDRAWAL_RECOMMENDED}"
echo "  nexuspay.transactions.dlq         : ${DLQ_PARTITIONS}"
echo ""
echo " PoC 적용 권장값"
echo "  nexuspay.transactions.payment     : ${POC_PAYMENT_PARTITIONS}"
echo "  nexuspay.transactions.transfer    : ${POC_TRANSFER_PARTITIONS}"
echo "  nexuspay.transactions.withdrawal  : ${POC_WITHDRAWAL_PARTITIONS}"
echo "  nexuspay.transactions.dlq         : ${DLQ_PARTITIONS}"
echo "============================================"
