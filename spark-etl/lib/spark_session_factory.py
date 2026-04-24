"""
SparkSession 생성 팩토리
- Delta Lake 확장 자동 활성화
- 설정 파일 기반 SparkSession 생성
"""
import yaml
from pyspark.sql import SparkSession

def create_spark_session(config_file_path: str = "config/etl_config.yaml") -> SparkSession:
    """설정 파일 기반으로 SparkSession을 생성한다

    Args:
        config_file_path (str, optional): 설정 파일 경로. 기본값은 'config/etl_config.yaml'.

    Returns:
        SparkSession: 생성된 SparkSession 객체
    """
    with open(config_file_path, 'r') as file:
        config = yaml.safe_load(file)

        spark_conf = config["spark"]
        builder = (
            SparkSession.builder
            .appName(spark_conf["app_name"])
            .master(spark_conf["master"])
        )

        # Delta Lake 및 Spart 설정 적용
        builder = builder.enableHiveSupport()

        for key, value in spark_conf["config"].items():
            builder = builder.config(key, str(value))

        # Week 3 NiFi 이벤트 시간과 같은 기준으로 UTC를 고정한다.
        builder = builder.config("spark.sql.session.timeZone", "UTC")
        #Delta Lake JAR 패키지(로컬 실습 환경)
        builder = builder.config(
            "spark.jars.packages",
            "io.delta:delta-spark_2.12:3.1.0,org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.8"
        )
        spark = builder.getOrCreate()
        spark.sparkContext.setLogLevel("WARN")

        print(f"[SparkSession] 생성 완료: {spark_conf['app_name']}")
        print(f"[SparkSession] Spark 버전: {spark.version}")
        print(f"[SparkSession] Delta Lake 활성화 확인: {spark.conf.get('spark.sql.extensions')}")

        return spark
def load_config(config_path: str = "config/etl_config.yaml") -> dict:
    """ETL 설정 파일을 로드한다."""
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

