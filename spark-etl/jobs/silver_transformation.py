"""
Silver 변환 Job
- Bronze에서 원본 JSON을 파싱하여 구조화된 스키마로 변환
- 데이터 품질 검증 수행 (critical 위반 격리, warning 위반 플래그)
- 정제된 데이터를 Silver Delta 테이블에 tx_date/event_type 파티셔닝 저장
"""
import sys
sys.path.insert(0, ".")

from datetime import date, timedelta
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, IntegerType, BooleanType
)

from lib.spark_session_factory import create_spark_session, load_config
from lib.quality_checker import QualityChecker


# Bronze의 kafka_value에 담긴 원본 JSON 스키마
RAW_EVENT_SCHEMA = StructType([
    StructField("event_id", StringType(), True),
    StructField("event_type", StringType(), True),
    StructField("user_id", IntegerType(), True),
    StructField("amount", DoubleType(), True),
    StructField("currency", StringType(), True),
    StructField("merchant_id", StringType(), True),
    StructField("merchant_name", StringType(), True),
    StructField("merchant_category", StringType(), True),
    StructField("channel", StringType(), True),
    StructField("status", StringType(), True),
    StructField("is_suspicious", BooleanType(), True),
    StructField("event_timestamp", StringType(), True),
    StructField("ingested_at", StringType(), True),
    StructField("data_source", StringType(), True),
    StructField("schema_version", StringType(), True),
    StructField("created_at", StringType(), True),
    StructField("fee_amount", DoubleType(), True),
    StructField("net_amount", DoubleType(), True),
    StructField("tx_count", IntegerType(), True),
    StructField("batch_id", StringType(), True),
    StructField("customer_name", StringType(), True),
    StructField("customer_email", StringType(), True),
    StructField("customer_phone", StringType(), True),
    StructField("customer_grade", StringType(), True),
    StructField("is_active", BooleanType(), True),
])


def run_silver_transformation(processing_date: date = None):
    """Silver 레이어 변환을 수행한다."""
    config = load_config()
    spark = create_spark_session()
    checker = QualityChecker()

    if processing_date is None:
        processing_date = date.today() - timedelta(days=1)

    bronze_path = config["paths"]["bronze"]
    silver_path = config["paths"]["silver"]
    quality_report_path = config["paths"]["quality_reports"]

    print("=" * 70)
    print(f"[Silver 변환] 시작")
    print(f"  처리 일자: {processing_date}")
    print(f"  Bronze 소스: {bronze_path}")
    print(f"  Silver 대상: {silver_path}")
    print("=" * 70)

    # ── Step 1: Bronze에서 해당 날짜 데이터 읽기 ──
    bronze_df = (
        spark.read.format("delta").load(bronze_path)
        .filter(F.col("ingest_date") == F.lit(processing_date))
    )

    input_count = bronze_df.count()
    print(f"\n[Step 1] Bronze 입력: {input_count:,}건")

    if input_count == 0:
        print("[경고] 처리할 데이터가 없습니다. 종료.")
        spark.stop()
        return

    # ── Step 2: JSON 파싱 + 스키마 변환 ──
    parsed_df = (
        bronze_df
        .select(
            F.from_json("kafka_value", RAW_EVENT_SCHEMA).alias("event"),
            "kafka_timestamp",
        )
        .select(
            F.col("event.event_id").alias("event_id"),
            F.col("event.user_id").alias("user_id"),
            F.col("event.event_type").alias("event_type"),
            F.col("event.amount").alias("amount"),
            F.col("event.currency").alias("currency"),
            F.col("event.merchant_id").alias("merchant_id"),
            F.col("event.merchant_category").alias("merchant_category"),
            F.col("event.status").alias("status"),
            F.to_timestamp("event.event_timestamp").alias("event_timestamp"),
            F.col("event.data_source").alias("data_source"),
            "kafka_timestamp",
        )
        # 파생 컬럼
        .withColumn("tx_date", F.to_date("event_timestamp"))
        .withColumn("tx_hour", F.hour("event_timestamp"))
        # currency 기본값
        .withColumn("currency",
                     F.when(F.col("currency").isNull(), F.lit("KRW"))
                     .otherwise(F.col("currency")))
    )

    print(f"[Step 2] JSON 파싱 완료: {parsed_df.count():,}건")

    # ── Step 3: 데이터 품질 검증 ──
    print("\n[Step 3] 데이터 품질 검증 수행 중...")
    clean_df, quarantine_df, report = checker.validate(
        parsed_df, str(processing_date)
    )

    print(report.summary())

    # 품질 리포트 저장
    report_path = f"{quality_report_path}/{processing_date}_report.json"
    import json
    report_dict = {
        "processing_date": report.processing_date,
        "total_input_records": report.total_input_records,
        "total_output_records": report.total_output_records,
        "quarantined_records": report.quarantined_records,
        "flagged_records": report.flagged_records,
        "generated_at": report.generated_at,
        "rules": [
            {
                "rule_id": r.rule_id, "rule_name": r.rule_name,
                "severity": r.severity, "failed_records": r.failed_records,
                "pass_rate": r.pass_rate,
            }
            for r in report.results
        ]
    }
    spark.sparkContext.parallelize([json.dumps(report_dict, ensure_ascii=False)]) \
        .saveAsTextFile(report_path)

    # ── Step 4: Silver Delta 테이블에 저장 ──
    silver_df = clean_df.withColumn("processed_timestamp", F.current_timestamp())

    # Silver 스키마에 맞게 컬럼 선택
    silver_final = silver_df.select(
        "event_id", "user_id", "event_type", "amount", "currency",
        "merchant_id", "merchant_category", "status",
        "event_timestamp", "tx_date", "tx_hour", "data_source",
        "is_anomaly", "quality_flags", "processed_timestamp"
    )

    (
        silver_final.write
        .format("delta")
        .mode("overwrite")
        .partitionBy("tx_date", "event_type")
        .option("overwriteSchema", "true")
        .save(silver_path)
    )

    output_count = silver_final.count()
    print(f"\n[Step 4] Silver 저장 완료: {output_count:,}건")
    print(f"  파티셔닝: tx_date / event_type")

    # ── Step 5: 검증 ──
    print(f"\n[검증]")
    silver_read = spark.read.format("delta").load(silver_path)
    print(f"  Silver 전체: {silver_read.count():,}건")
    print(f"\n  파티션별 건수:")
    silver_read.groupBy("tx_date", "event_type").count() \
        .orderBy("tx_date", "event_type").show(20)

    print(f"\n  이상값(is_anomaly=true): {silver_read.filter(F.col('is_anomaly') == True).count():,}건")

    spark.stop()
    print(f"\n[Silver 변환] 완료 ✓")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_date = date.fromisoformat(sys.argv[1])
    else:
        target_date = date.today() - timedelta(days=1)

    run_silver_transformation(target_date)
