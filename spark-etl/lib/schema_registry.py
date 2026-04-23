"""
Nexus Pay 스키마 레지스트리
- Bronze/Silver/Gold 레이어별 스키마 정의
- Week 2~4에서 사용한 NexusPayEvent 스키마와 호환
"""
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, LongType,
    TimestampType, IntegerType, BooleanType, DateType
)


# ──────────────────────────────────────────────
# Bronze: Kafka 원본 그대로 + 메타데이터
# ──────────────────────────────────────────────
BRONZE_SCHEMA = StructType([
    StructField("kafka_key", StringType(), True),
    StructField("kafka_value", StringType(), False),        # 원본 JSON 문자열
    StructField("kafka_topic", StringType(), False),
    StructField("kafka_partition", IntegerType(), False),
    StructField("kafka_offset", LongType(), False),
    StructField("kafka_timestamp", TimestampType(), False),
    StructField("ingest_date", DateType(), False),          # 파티션 키
    StructField("ingest_timestamp", TimestampType(), False),
])

# ──────────────────────────────────────────────
# Silver: 정제·표준화된 거래 데이터
# ──────────────────────────────────────────────
SILVER_SCHEMA = StructType([
    StructField("tx_id", StringType(), False),              # 거래 고유 ID
    StructField("user_id", StringType(), False),            # 사용자 ID
    StructField("tx_type", StringType(), False),            # PAYMENT / REFUND / TRANSFER
    StructField("amount", DoubleType(), False),             # 거래 금액 (원)
    StructField("currency", StringType(), False),           # 통화 (KRW 기본)
    StructField("merchant_id", StringType(), True),         # 가맹점 ID
    StructField("merchant_category", StringType(), True),   # 가맹점 업종 코드
    StructField("status", StringType(), False),             # SUCCESS / FAILED / PENDING
    StructField("event_timestamp", TimestampType(), False), # 이벤트 발생 시점
    StructField("tx_date", DateType(), False),              # 파티션 키: 거래 일자
    StructField("tx_hour", IntegerType(), False),           # 거래 시간 (0~23)
    StructField("source_system", StringType(), True),       # 데이터 소스 (api/csv/db)
    StructField("is_anomaly", BooleanType(), False),        # 이상값 플래그
    StructField("quality_flags", StringType(), True),       # 품질 플래그 (쉼표 구분)
    StructField("processed_timestamp", TimestampType(), False),
])

# ──────────────────────────────────────────────
# Gold: 일별 거래 요약
# ──────────────────────────────────────────────
GOLD_DAILY_SUMMARY_SCHEMA = StructType([
    StructField("summary_date", DateType(), False),         # 파티션 키
    StructField("tx_type", StringType(), False),
    StructField("total_count", LongType(), False),
    StructField("success_count", LongType(), False),
    StructField("failed_count", LongType(), False),
    StructField("total_amount", DoubleType(), False),
    StructField("avg_amount", DoubleType(), False),
    StructField("min_amount", DoubleType(), False),
    StructField("max_amount", DoubleType(), False),
    StructField("unique_users", LongType(), False),
    StructField("anomaly_count", LongType(), False),
    StructField("generated_at", TimestampType(), False),
])

# ──────────────────────────────────────────────
# Gold: 고객별 누적 통계
# ──────────────────────────────────────────────
GOLD_CUSTOMER_STATS_SCHEMA = StructType([
    StructField("user_id", StringType(), False),
    StructField("stats_month", StringType(), False),        # 파티션 키: "2026-03"
    StructField("total_tx_count", LongType(), False),
    StructField("total_amount", DoubleType(), False),
    StructField("avg_amount", DoubleType(), False),
    StructField("payment_count", LongType(), False),
    StructField("refund_count", LongType(), False),
    StructField("transfer_count", LongType(), False),
    StructField("anomaly_count", LongType(), False),
    StructField("first_tx_date", DateType(), True),
    StructField("last_tx_date", DateType(), True),
    StructField("generated_at", TimestampType(), False),
])

# ──────────────────────────────────────────────
# Gold: 수수료 정산
# ──────────────────────────────────────────────
GOLD_FEE_SETTLEMENT_SCHEMA = StructType([
    StructField("settlement_date", DateType(), False),
    StructField("merchant_id", StringType(), False),
    StructField("merchant_category", StringType(), True),
    StructField("total_payment_amount", DoubleType(), False),
    StructField("total_refund_amount", DoubleType(), False),
    StructField("net_amount", DoubleType(), False),          # 결제 - 환불
    StructField("fee_rate", DoubleType(), False),             # 수수료율
    StructField("fee_amount", DoubleType(), False),           # 수수료
    StructField("settlement_amount", DoubleType(), False),    # 정산액 = net - fee
    StructField("tx_count", LongType(), False),
    StructField("generated_at", TimestampType(), False),
])
