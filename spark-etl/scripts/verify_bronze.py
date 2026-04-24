"""Bronze 적재 검증 스크립트"""
import sys
sys.path.insert(0, ".")

from lib.spark_session_factory import create_spark_session, load_config
from pyspark.sql import functions as F


def verify():
    config = load_config()
    spark = create_spark_session()
    bronze_path = config["paths"]["bronze"]

    df = spark.read.format("delta").load(bronze_path)

    print("=" * 70)
    print("[Bronze 검증 리포트]")
    print("=" * 70)

    print(f"\n1. 총 레코드 수: {df.count():,}")
    print(f"\n2. 스키마:")
    df.printSchema()

    print(f"\n3. 파티션별 건수:")
    df.groupBy("ingest_date").count().orderBy("ingest_date").show()

    print(f"\n4. null 값 현황:")
    for col_name in df.columns:
        null_count = df.filter(F.col(col_name).isNull()).count()
        if null_count > 0:
            print(f"  {col_name}: {null_count}건 null")

    print(f"\n5. 샘플 데이터 (kafka_value 파싱):")
    from pyspark.sql.types import StructType, StructField, StringType, DoubleType
    sample_schema = StructType([
        StructField("tx_id", StringType()),
        StructField("tx_type", StringType()),
        StructField("amount", DoubleType()),
    ])
    (
        df.select(F.from_json("kafka_value", sample_schema).alias("parsed"))
        .select("parsed.tx_id", "parsed.tx_type", "parsed.amount")
        .show(10, truncate=False)
    )

    # Delta 히스토리
    from delta.tables import DeltaTable
    delta_table = DeltaTable.forPath(spark, bronze_path)
    print(f"\n6. Delta 히스토리:")
    delta_table.history().select("version", "timestamp", "operation").show(truncate=False)

    spark.stop()
    print("\n[Bronze 검증 완료] ✓")


if __name__ == "__main__":
    verify()
