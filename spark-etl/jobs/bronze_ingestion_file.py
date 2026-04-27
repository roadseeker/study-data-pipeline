"""
Bronze 적재 - 파일 기반 (Kafka 미사용 테스트용)
- JSON Lines 파일을 Bronze Delta 테이블에 적재
- Kafka 메타데이터는 테스트용 값으로 보강
"""
import sys
sys.path.insert(0, ".")

from datetime import date

from pyspark.sql import functions as F

from lib.spark_session_factory import create_spark_session, load_config


def run_bronze_from_file(file_path: str, processing_date: date) -> None:
    """JSON Lines 파일을 Bronze Delta 테이블에 적재한다."""
    config = load_config()
    spark = create_spark_session()
    bronze_path = config["paths"]["bronze"]

    print("=" * 70)
    print("[Bronze 파일 적재] 시작")
    print(f"  소스 파일: {file_path}")
    print(f"  처리 일자: {processing_date}")
    print(f"  저장 경로: {bronze_path}")
    print("=" * 70)

    raw_df = spark.read.text(file_path)

    bronze_df = (
        raw_df
        .withColumnRenamed("value", "kafka_value")
        .withColumn("kafka_key", F.lit(None).cast("string"))
        .withColumn("kafka_topic", F.lit("nexuspay.events.ingested"))
        .withColumn("kafka_partition", F.lit(0).cast("int"))
        .withColumn("kafka_offset", F.monotonically_increasing_id())
        .withColumn("kafka_timestamp", F.current_timestamp())
        .withColumn("ingest_date", F.lit(processing_date).cast("date"))
        .withColumn("ingest_timestamp", F.current_timestamp())
        .select(
            "kafka_key",
            "kafka_value",
            "kafka_topic",
            "kafka_partition",
            "kafka_offset",
            "kafka_timestamp",
            "ingest_date",
            "ingest_timestamp",
        )
    )

    record_count = bronze_df.count()
    print(f"[Step 1] 파일 레코드 수: {record_count:,}건")

    if record_count == 0:
        print("[경고] 적재할 데이터가 없습니다. 종료합니다.")
        spark.stop()
        return

    (
        bronze_df.write
        .format("delta")
        .mode("append")
        .partitionBy("ingest_date")
        .save(bronze_path)
    )

    verify_df = spark.read.format("delta").load(bronze_path)
    final_count = verify_df.filter(F.col("ingest_date") == F.lit(processing_date)).count()

    print("[검증] Bronze 파일 적재 완료")
    print(f"  처리 일자 적재 건수: {final_count:,}건")
    verify_df.groupBy("ingest_date").count().orderBy("ingest_date").show(truncate=False)

    spark.stop()
    print("[Bronze 파일 적재] 완료")


if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "/data/sample/transactions_sample.jsonl"
    proc_date = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date(2026, 3, 31)
    run_bronze_from_file(input_file, proc_date)
