"""
Bronze 적재 Job
- Kafka 토픽에서 지정된 날짜의 거래 데이터를 배치 읽기
- 원본 JSON을 그대로 보존하며 Kafka 메타데이터 추가
- Delta Lake 포맷으로 ingest_date 파티셔닝 저장
- 멱등성 보장: topic+partition+offset 기준 중복 제거
"""
import sys
sys.path.insert(0, ".")

from datetime import datetime, date, timedelta
from pyspark.sql import functions as F
from pyspark.sql.types import DateType

from lib.spark_session_factory import create_spark_session, load_config


def run_bronze_ingestion(processing_date: date = None):
    """Bronze 레이어에 Kafka 원본 데이터를 적재한다."""
    config = load_config()
    spark = create_spark_session()

    if processing_date is None:
        processing_date = date.today() - timedelta(days=1)

    kafka_conf = config["kafka"]
    # bronze: "/data/lakehouse/delta/bronze/transactions"
    bronze_path = config["paths"]["bronze"]

    print("=" * 70)
    print(f"[Bronze 적재] 시작")
    print(f"  처리 일자: {processing_date}")
    print(f"  소스 토픽: {kafka_conf['source_topic']}") # source_topic: "nexuspay.events.ingested"
    print(f"  저장 경로: {bronze_path}")
    print("=" * 70)

    # ── Step 1: Kafka 배치 읽기 ──
    raw_df = (
        spark.read
        .format("kafka")
        .option("kafka.bootstrap.servers", kafka_conf["bootstrap_servers"])
        .option("subscribe", kafka_conf["source_topic"])
        .option("startingOffsets", "earliest")
        .option("endingOffsets", "latest")
        .load()
    )

    # ── Step 2: 컬럼 변환 + 메타데이터 추가 ──
    bronze_df = (
        raw_df
        .select(
            F.col("key").cast("string").alias("kafka_key"),
            F.col("value").cast("string").alias("kafka_value"),
            F.col("topic").alias("kafka_topic"),
            F.col("partition").alias("kafka_partition"),
            F.col("offset").alias("kafka_offset"),
            F.col("timestamp").alias("kafka_timestamp"), # timestamp: Kafka 메시지 생성 시간 -> kafka_timestamp
        )
        # 처리 대상 날짜 필터링
        .filter(F.to_date("kafka_timestamp") == F.lit(processing_date))
        # 메타데이터 추가
        .withColumn("ingest_date", F.to_date("kafka_timestamp"))
        .withColumn("ingest_timestamp", F.current_timestamp())
    )

    record_count = bronze_df.count()
    print(f"\n[Step 2] 처리 대상: {record_count:,}건")

    if record_count == 0:
        print("[경고] 처리할 데이터가 없습니다. 종료.")
        spark.stop()
        return

    # ── Step 3: 멱등성 보장 — 기존 데이터와 중복 제거 ──
    from delta.tables import DeltaTable

    if DeltaTable.isDeltaTable(spark, bronze_path):
        print("[Step 3] 기존 Bronze 테이블 발견 → MERGE (멱등성)")
        existing_table = DeltaTable.forPath(spark, bronze_path)

        (
            existing_table.alias("target")
            .merge(
                bronze_df.alias("source"),
                """
                target.kafka_topic = source.kafka_topic
                AND target.kafka_partition = source.kafka_partition
                AND target.kafka_offset = source.kafka_offset
                """
            )
            .whenNotMatchedInsertAll()
            .execute()
        )
        final_count = spark.read.format("delta").load(bronze_path) \
            .filter(F.col("ingest_date") == F.lit(processing_date)).count()
    else:
        print("[Step 3] Bronze 테이블 최초 생성 → 신규 쓰기")
        (
            bronze_df.write
            .format("delta")
            .mode("overwrite")
            .partitionBy("ingest_date")
            .save(bronze_path)
        )
        final_count = record_count

    # ── Step 4: 적재 검증 ──
    print(f"\n[검증] Bronze 적재 완료")
    print(f"  처리 일자: {processing_date}")
    print(f"  적재 건수: {final_count:,}")

    # Delta 히스토리 확인
    delta_table = DeltaTable.forPath(spark, bronze_path)
    print("\n[Delta 히스토리 — 최근 3건]")
    delta_table.history(3).select(
        "version", "timestamp", "operation", "operationMetrics"
    ).show(truncate=False)

    spark.stop()
    print(f"\n[Bronze 적재] 완료 ✓")


if __name__ == "__main__":
    # 인자로 날짜를 받거나 기본값(전일) 사용
    if len(sys.argv) > 1:
        target_date = date.fromisoformat(sys.argv[1])
    else:
        target_date = date.today() - timedelta(days=1)

    run_bronze_ingestion(target_date)
