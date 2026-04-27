"""
Kafka 배치 읽기 연동 테스트
- Spark Structured Streaming의 배치 모드로 Kafka 토픽 데이터를 읽는다.
- 이 테스트가 성공하면 Day 2의 Bronze 적재로 넘어간다.
"""
import sys
# Python이 모듈을 찾는 경로에 현재 작업 디렉터리 . 를 맨 앞에 추가하는 것입니다.
sys.path.insert(0, ".")

from lib.spark_session_factory import create_spark_session, load_config


def main():
    config = load_config()
    spark = create_spark_session()

    kafka_conf = config["kafka"]

    print("=" * 70)
    print("[Step 1] Kafka 토픽 배치 읽기 시작")
    print(f"  브로커: {kafka_conf['bootstrap_servers']}")
    print(f"  토픽:   {kafka_conf['source_topic']}")
    print("=" * 70)

    # Kafka 배치 읽기 (startingOffsets: earliest → 전체 데이터 읽기)
    kafka_df = (
        spark.read
        # Spark는 Kafka 전용 데이터 소스 리더를 사용
        .format("kafka")
        .option("kafka.bootstrap.servers", kafka_conf["bootstrap_servers"])
        .option("subscribe", kafka_conf["source_topic"])
        .option("startingOffsets", "earliest")
        .option("endingOffsets", "latest")
        .load()
    )

    # 기본 정보 출력
    total_count = kafka_df.count()
    # f"..." : 문자열 안에 변수나 표현식을 넣을 수 있음
    print(f"\n[결과] 총 {total_count:,}건 읽기 완료")
    print(f"[스키마]")
    # DataFrame 컬럼 구조와 자료형을 출력
    kafka_df.printSchema()

    # 파티션별 건수
    print("\n[파티션별 건수]")
    # Kafka 토픽의 각 파티션에 데이터가 어떻게 분산되어 있는지 확인
    # 특정 파티션에만 데이터가 몰렸는지 점검
    # Kafka 읽기가 정상적으로 되었는지 추가 검증
    kafka_df.groupBy("partition").count().orderBy("partition").show()

    # 샘플 데이터 (value를 문자열로 변환하여 확인)
    from pyspark.sql.functions import col


    print("\n[샘플 데이터 — 상위 5건]")
    (
        kafka_df
        .select(
            col("key").cast("string").alias("key"),
            col("value").cast("string").alias("value"),
            "topic", "partition", "offset", "timestamp" // Kafka 메시지의 메타데이터도 함께 출력
        )
        .orderBy("timestamp")
        .show(5, truncate=80)
    )

    print("\n[연동 테스트 완료] Kafka 배치 읽기 정상 확인")
    spark.stop()


if __name__ == "__main__":
    main()
