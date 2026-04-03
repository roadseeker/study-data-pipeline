# Week 5: 변환 — Spark 배치 ETL 파이프라인 구축

**기간**: 5일 (월~금, 풀타임 40시간)
**주제**: Spark 배치 ETL 설계, 대용량 파티셔닝 전략, Delta Lake 기반 ACID 저장소 구축, Lambda 아키텍처 배치 레이어 완성
**산출물**: Spark ETL 코드 + Delta Lake 테이블 + 데이터 품질 검증 파이프라인 + 배치 운영 가이드
**전제 조건**: Week 1~4 환경 정상 기동 (`bash scripts/healthcheck-all.sh` 전체 통과), Flink 실시간 파이프라인 정상 작동 중

---

## 수행 시나리오

### 배경 설정

Week 4에서 Flink 기반 실시간 스트림 처리 파이프라인이 완성되었다. 5분 단위 윈도우 집계와 이상거래 탐지가 실시간으로 작동하고 있다. 그러나 Nexus Pay CFO가 새로운 요구사항을 제시한다.

> "실시간 대시보드는 잘 돌아갑니다. 하지만 저는 **일별·월별 정산 리포트**가 필요합니다. 매일 새벽 3시에 전일 거래 전체를 집계해서 **거래 유형별 일일 매출, 수수료 정산, 고객별 누적 거래 통계**를 뽑아야 합니다. 실시간 5분 집계만으로는 일별 정산 정합성을 보장할 수 없어요. 또한 감사팀에서 **과거 데이터를 임의 시점으로 조회할 수 있어야 한다**고 합니다. 데이터가 수정되더라도 이전 버전을 추적할 수 있는 구조가 필요합니다. 그리고 원본 데이터에 누락·중복·이상값이 꽤 있는데, 배치 처리 과정에서 **데이터 품질 검증**도 함께 수행해 주세요."

컨설턴트로서 Apache Spark를 활용하여 대용량 배치 ETL 파이프라인을 설계·구축하는 것이 이번 주의 과제다. Flink가 실시간 처리를 담당하는 Speed Layer라면, Spark는 정확성과 완전성을 보장하는 Batch Layer를 담당한다. Delta Lake를 도입하여 ACID 트랜잭션과 타임 트래블(Time Travel) 기능으로 감사 추적 요건을 충족하고, 데이터 품질 검증 단계를 ETL 파이프라인에 내장하여 신뢰할 수 있는 정산 데이터를 생산한다.

### 왜 Spark인가? — Flink와의 역할 분담

Week 4의 Flink는 실시간으로 흘러오는 무한 스트림을 처리하는 데 최적화되어 있다. 반면 Spark는 유한한 대용량 데이터셋을 한 번에 읽어 변환하는 배치 처리에 강점이 있다. 두 엔진은 경쟁이 아니라 보완 관계다.

```
┌──────────────────────────────────────────────────────────────────────┐
│               Lambda 아키텍처 — Flink + Spark 역할 분담                │
│                                                                      │
│  ┌─────────────────────────────────────────────────┐                 │
│  │  Speed Layer (Flink, Week 4)                     │                │
│  │  ─ 실시간 5분 윈도우 집계                          │                │
│  │  ─ 이상거래 즉시 탐지                              │                │
│  │  ─ 밀리초 레이턴시, 근사 정확도                     │                │
│  └─────────────────────────────────────────────────┘                 │
│                                                                      │
│  ┌─────────────────────────────────────────────────┐                 │
│  │  Batch Layer (Spark, Week 5) ← 이번 주            │                │
│  │  ─ 일별·월별 정산 집계 (전수 처리)                  │                │
│  │  ─ 데이터 품질 검증·정제                            │                │
│  │  ─ Delta Lake ACID + 타임 트래블                   │                │
│  │  ─ 높은 레이턴시(시간 단위), 완전한 정확도           │                │
│  └─────────────────────────────────────────────────┘                 │
│                                                                      │
│  ┌─────────────────────────────────────────────────┐                 │
│  │  Serving Layer (Redis + PostgreSQL)               │                │
│  │  ─ 실시간 피처: Redis (Flink 결과)                  │                │
│  │  ─ 정산 리포트: PostgreSQL (Spark 결과)             │                │
│  └─────────────────────────────────────────────────┘                 │
└──────────────────────────────────────────────────────────────────────┘
```

| 구분 | Flink (Week 4) | Spark (Week 5) |
|------|---------------|----------------|
| 처리 모드 | 무한 스트림 (연속) | 유한 배치 (일괄) |
| 레이턴시 | 밀리초~초 | 분~시간 |
| 정확도 | 근사 (윈도우 기반) | 정확 (전수 집계) |
| 상태 관리 | Keyed State + 체크포인트 | 없음 (배치마다 재계산) |
| 적합 업무 | 이상거래 탐지, 실시간 대시보드 | 일별 정산, 월간 리포트, 데이터 정제 |
| 저장 포맷 | Kafka 토픽 | Delta Lake (Parquet + 트랜잭션 로그) |
| Nexus Pay 활용 | 5분 집계, 이상거래 알림 | 일일 정산, 감사 추적, 품질 검증 |

### 목표

1. Spark 배치 처리 핵심 개념(SparkSession, DataFrame API, Catalyst 옵티마이저, 실행 계획) 이해 및 정리
2. Kafka 토픽에 적재된 원본 거래 데이터를 Spark로 배치 읽기(Batch Read)하여 ETL 파이프라인 구축
3. Delta Lake 기반 데이터 레이크하우스 구축 — Bronze·Silver·Gold 메달리온 아키텍처 적용
4. 대용량 데이터 파티셔닝 전략 설계 및 구현 (날짜·거래유형 기반 파티셔닝)
5. 데이터 품질 검증 파이프라인 구축 (스키마 검증, 중복 제거, 이상값 탐지, 무결성 체크)
6. Delta Lake 타임 트래블을 활용한 감사 추적 기능 구현 및 검증

### 일정 개요

| 일차 | 주제 | 핵심 작업 |
|------|------|----------|
| Day 1 | Spark 핵심 개념 + 프로젝트 셋업 | Spark 배치 처리 모델 정리, PySpark 프로젝트 구조 생성, Kafka 배치 읽기 연동 |
| Day 2 | 메달리온 아키텍처 + Bronze 레이어 | Bronze 레이어(원본 적재), 스키마 표준화, 파티셔닝 전략 구현 |
| Day 3 | Silver 레이어 + 데이터 품질 검증 | 데이터 정제·변환, 품질 검증 파이프라인, 중복 제거·이상값 처리 |
| Day 4 | Gold 레이어 + Delta Lake 심화 | 비즈니스 집계 테이블 생성, 타임 트래블, MERGE(Upsert), 스키마 진화 |
| Day 5 | 통합 테스트 + 배치 운영 가이드 문서화 | 전체 ETL 파이프라인 검증, 성능 튜닝, 운영 가이드 작성, Git 커밋 |

---

## Day 1: Spark 핵심 개념 + 프로젝트 셋업

### 1-1. Spark 배치 처리 핵심 개념 정리

컨설팅 현장에서 고객에게 Spark를 설명할 때 사용할 핵심 개념을 정리한다.

```
┌──────────────────────────────────────────────────────────────────────┐
│                     Spark 배치 처리 핵심 개념                          │
│                                                                      │
│  SparkSession = Spark 애플리케이션의 단일 진입점                       │
│    └── spark = SparkSession.builder.appName("...").getOrCreate()      │
│                                                                      │
│  DataFrame = 분산 테이블 (행 + 열 + 스키마)                            │
│    ├── 불변(Immutable): 변환 시 새 DataFrame 반환                     │
│    ├── 지연 평가(Lazy Evaluation): 액션 호출 전까지 실행하지 않음       │
│    └── SQL과 프로그래밍 API 모두 사용 가능                              │
│                                                                      │
│  변환(Transformation) = 지연 평가되는 연산                             │
│    ├── Narrow: 파티션 간 데이터 이동 없음 (filter, select, map)        │
│    └── Wide: 파티션 간 셔플 발생 (groupBy, join, repartition)          │
│                                                                      │
│  액션(Action) = 실제 실행을 트리거하는 연산                            │
│    └── count, show, write, collect                                    │
│                                                                      │
│  Catalyst 옵티마이저 = 논리 계획 → 물리 계획 자동 최적화               │
│    ├── Predicate Pushdown: 필터를 데이터 소스에 밀어넣기               │
│    ├── Column Pruning: 필요한 컬럼만 읽기                              │
│    └── Join Reordering: 조인 순서 자동 최적화                          │
│                                                                      │
│  파티셔닝 = 대용량 데이터를 디렉토리 단위로 분할                       │
│    ├── 쓰기 시: partitionBy("year", "month", "day")                   │
│    ├── 읽기 시: 필요한 파티션만 스캔 (파티션 프루닝)                   │
│    └── 적절한 파티션 수 = 코어 수 × 2~3배                              │
│                                                                      │
│  Delta Lake = Parquet + 트랜잭션 로그                                  │
│    ├── ACID 트랜잭션: 읽기·쓰기 격리                                   │
│    ├── 타임 트래블: 과거 시점 데이터 조회                               │
│    ├── 스키마 진화: 컬럼 추가·변경 허용                                │
│    └── MERGE (Upsert): 조건부 INSERT/UPDATE/DELETE                    │
└──────────────────────────────────────────────────────────────────────┘
```

```bash
mkdir -p docs
cat > docs/spark-concepts.md << 'EOF'
# Spark 배치 ETL 핵심 개념 — 컨설팅 설명 자료

## 왜 Spark인가?

Spark는 대용량 데이터셋의 배치 처리에 최적화된 분산 연산 엔진이다.
- 인메모리 연산 → MapReduce 대비 10~100배 빠른 처리 속도
- DataFrame API → SQL 친화적 인터페이스로 데이터 엔지니어·분석가 모두 사용 가능
- Catalyst 옵티마이저 → 실행 계획 자동 최적화로 수작업 튜닝 부담 감소
- Delta Lake 통합 → 데이터 레이크에 ACID 트랜잭션 부여

## 배치 처리의 정의

배치 처리란 일정 기간 동안 축적된 데이터를 한꺼번에 모아서 처리하는 방식이다.
- Nexus Pay 시나리오: 매일 새벽 3시에 전일 거래 전체를 읽어 정산 리포트 생성
- 장점: 전수 데이터 처리로 완전한 정확성 보장
- 단점: 처리 지연(레이턴시)이 존재 — 결과를 즉시 볼 수 없음

## Spark vs Flink — Nexus Pay 관점 정리

| 시나리오 | 엔진 | 이유 |
|----------|------|------|
| "1분 내 3건 이상 거래 탐지" | Flink | 밀리초 레이턴시 필요 |
| "전일 거래 유형별 매출 집계" | Spark | 전수 집계로 정합성 보장 |
| "5분 단위 실시간 대시보드" | Flink | 연속 스트림 처리 |
| "월간 수수료 정산 리포트" | Spark | 대용량 배치 집계 |
| "감사팀 과거 데이터 조회" | Spark + Delta | 타임 트래블 필요 |

## 메달리온 아키텍처 (Bronze → Silver → Gold)

데이터를 품질 단계별로 분리하여 관리하는 아키텍처 패턴이다.

```
[원본 소스] → Bronze(원본 그대로) → Silver(정제·표준화) → Gold(비즈니스 집계)
```

| 레이어 | 역할 | 데이터 상태 | Nexus Pay 예시 |
|--------|------|-----------|-------------|
| Bronze | 원본 적재 | 비정제, 스키마 그대로 | Kafka 원본 JSON 그대로 적재 |
| Silver | 정제·변환 | 스키마 표준화, 중복 제거, 타입 변환 | null 제거, 타임스탬프 파싱, 중복 거래 제거 |
| Gold | 비즈니스 집계 | 바로 리포팅 가능한 상태 | 일별 매출, 수수료 정산, 고객 누적 통계 |

## Delta Lake 핵심 기능

### 타임 트래블 (Time Travel)
```python
# 특정 버전으로 조회
df = spark.read.format("delta").option("versionAsOf", 3).load(path)

# 특정 시점으로 조회
df = spark.read.format("delta").option("timestampAsOf", "2026-03-30").load(path)
```

### MERGE (Upsert)
```python
# 조건에 따라 INSERT 또는 UPDATE
deltaTable.alias("target").merge(
    updates.alias("source"),
    "target.tx_id = source.tx_id"
).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
```

### 스키마 진화
```python
df.write.format("delta").option("mergeSchema", "true").mode("append").save(path)
```

EOF
```

### 1-2. PySpark 프로젝트 구조 생성

Week 5는 PySpark(Python)로 진행한다. Spark의 DataFrame API는 Python에서 가장 많이 사용되며, 컨설팅 현장에서도 PySpark가 사실상 표준이다.

```bash
mkdir -p spark-etl/{jobs,lib,config,tests,scripts,data/{bronze,silver,gold,checkpoints,quality-reports}}
```

최종 디렉토리 구조:

```
spark-etl/
├── jobs/                                  # Spark Job 엔트리포인트
│   ├── bronze_ingestion.py                # Bronze: Kafka → Delta 원본 적재
│   ├── silver_transformation.py           # Silver: 정제·변환·품질 검증
│   ├── gold_aggregation.py                # Gold: 비즈니스 집계 테이블 생성
│   └── full_etl_pipeline.py               # 전체 ETL 오케스트레이션
├── lib/                                   # 공유 라이브러리
│   ├── spark_session_factory.py           # SparkSession 생성 팩토리
│   ├── schema_registry.py                 # 스키마 정의 모음
│   ├── quality_checker.py                 # 데이터 품질 검증 모듈
│   ├── delta_utils.py                     # Delta Lake 유틸리티
│   └── metrics_collector.py               # ETL 메트릭 수집기
├── config/
│   ├── etl_config.yaml                    # ETL 설정 (경로, 파라미터)
│   └── quality_rules.yaml                 # 데이터 품질 규칙 정의
├── tests/
│   ├── test_bronze_ingestion.py           # Bronze 단위 테스트
│   ├── test_silver_transformation.py      # Silver 단위 테스트
│   └── test_quality_checker.py            # 품질 검증 테스트
├── scripts/
│   ├── generate_sample_data.py            # 샘플 거래 데이터 생성기
│   ├── verify_etl_pipeline.sh             # 통합 검증 스크립트
│   └── delta_maintenance.sh               # Delta 테이블 유지보수 (VACUUM, OPTIMIZE)
├── data/
│   ├── bronze/                            # Bronze Delta 테이블
│   ├── silver/                            # Silver Delta 테이블
│   ├── gold/                              # Gold Delta 테이블
│   ├── checkpoints/                       # Spark 체크포인트
│   └── quality-reports/                   # 품질 검증 리포트
└── docs/
    └── spark-concepts.md                  # Day 1에서 작성
```

### 1-3. ETL 설정 파일 작성

```bash
cat > spark-etl/config/etl_config.yaml << 'EOF'
# Nexus Pay Spark ETL 설정
spark:
  app_name: "nexuspay-Batch-ETL"
  master: "local[*]"
  config:
    spark.sql.extensions: "io.delta.sql.DeltaSparkSessionExtension"
    spark.sql.catalog.spark_catalog: "org.apache.spark.sql.delta.catalog.DeltaCatalog"
    spark.sql.shuffle.partitions: 8
    spark.default.parallelism: 8
    spark.sql.adaptive.enabled: true
    spark.sql.adaptive.coalescePartitions.enabled: true

kafka:
  bootstrap_servers: "kafka-1:9092,kafka-2:9092,kafka-3:9092"
  source_topic: "nexuspay.events.ingested"
  consumer_group: "spark-batch-etl"

paths:
  bronze: "/data/delta/etl/bronze/transactions"
  silver: "/data/delta/etl/silver/transactions"
  gold:
    daily_summary: "/data/delta/etl/gold/daily_summary"
    customer_stats: "/data/delta/etl/gold/customer_stats"
    fee_settlement: "/data/delta/etl/gold/fee_settlement"
  quality_reports: "/data/delta/etl/quality-reports"
  checkpoints: "/data/delta/etl/checkpoints"

partitioning:
  bronze:
    columns: ["ingest_date"]
  silver:
    columns: ["tx_date", "tx_type"]
  gold:
    daily_summary: ["summary_date"]
    customer_stats: ["stats_month"]

quality:
  null_threshold: 0.01          # 1% 이상 null이면 경고
  duplicate_threshold: 0.001    # 0.1% 이상 중복이면 경고
  max_amount: 50000000          # 5천만원 초과 거래 이상값 플래그
  min_amount: 100               # 100원 미만 거래 이상값 플래그

batch:
  processing_date: "yesterday"  # 기본: 전일 데이터 처리
  retry_count: 3
  retry_delay_seconds: 60
EOF
```

### 1-4. SparkSession 팩토리 — Delta Lake 통합

```bash
cat > spark-etl/lib/spark_session_factory.py << 'PYEOF'
"""
SparkSession 생성 팩토리
- Delta Lake 확장 자동 활성화
- 설정 파일 기반 SparkSession 생성
"""
import yaml
from pyspark.sql import SparkSession


def create_spark_session(config_path: str = "config/etl_config.yaml") -> SparkSession:
    """설정 파일 기반으로 SparkSession을 생성한다."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    spark_conf = config["spark"]
    builder = (
        SparkSession.builder
        .appName(spark_conf["app_name"])
        .master(spark_conf["master"])
    )

    # Delta Lake 및 Spark 설정 적용
    for key, value in spark_conf["config"].items():
        builder = builder.config(key, str(value))

    # Delta Lake JAR 패키지 (로컬 실습 환경)
    builder = builder.config(
        "spark.jars.packages",
        "io.delta:delta-spark_2.12:3.1.0,org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1"
    )

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    print(f"[SparkSession] 생성 완료: {spark_conf['app_name']}")
    print(f"[SparkSession] Spark 버전: {spark.version}")
    print(f"[SparkSession] Delta Lake 활성화 확인: {spark.conf.get('spark.sql.extensions')}")

    return spark


def load_config(config_path: str = "config/etl_config.yaml") -> dict:
    """ETL 설정 파일을 로드한다."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)
PYEOF
```

### 1-5. 스키마 레지스트리 — 각 레이어별 스키마 정의

```bash
cat > spark-etl/lib/schema_registry.py << 'PYEOF'
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
PYEOF
```

### 1-6. 샘플 거래 데이터 생성기

Kafka에 적재된 데이터를 시뮬레이션하는 샘플 데이터 생성기를 작성한다. 실제 실습에서는 Week 2~4에서 축적된 Kafka 데이터를 사용하지만, 독립 테스트를 위해 샘플 데이터도 준비한다.

```bash
cat > spark-etl/scripts/generate_sample_data.py << 'PYEOF'
"""
Nexus Pay 샘플 거래 데이터 생성기
- Kafka 토픽에 적재되는 형식과 동일한 JSON 생성
- Bronze 레이어 테스트용 CSV/JSON 파일 생성
"""
import json
import random
import uuid
from datetime import datetime, timedelta
import os


# 설정
NUM_RECORDS = 10000
TARGET_DATE = datetime(2026, 3, 31)
OUTPUT_DIR = "data/sample"

# 데이터 풀
TX_TYPES = ["PAYMENT", "REFUND", "TRANSFER"]
TX_TYPE_WEIGHTS = [0.7, 0.15, 0.15]
STATUSES = ["SUCCESS", "FAILED", "PENDING"]
STATUS_WEIGHTS = [0.92, 0.05, 0.03]
SOURCES = ["api", "csv", "db"]
SOURCE_WEIGHTS = [0.6, 0.25, 0.15]
CURRENCIES = ["KRW"]
MERCHANT_CATEGORIES = ["F&B", "RETAIL", "ONLINE", "TRAVEL", "FINANCE", "HEALTH"]

USER_IDS = [f"USR-{i:05d}" for i in range(1, 201)]           # 200명
MERCHANT_IDS = [f"MRC-{i:04d}" for i in range(1, 51)]        # 50개 가맹점


def generate_event(event_time: datetime) -> dict:
    """단일 거래 이벤트를 생성한다."""
    tx_type = random.choices(TX_TYPES, TX_TYPE_WEIGHTS)[0]
    status = random.choices(STATUSES, STATUS_WEIGHTS)[0]

    # 금액: 거래 유형별 다른 분포
    if tx_type == "PAYMENT":
        amount = round(random.lognormvariate(10, 1.5), 0)     # 중앙값 약 2만원
        amount = max(100, min(amount, 10_000_000))
    elif tx_type == "REFUND":
        amount = round(random.lognormvariate(9.5, 1.2), 0)
        amount = max(100, min(amount, 5_000_000))
    else:  # TRANSFER
        amount = round(random.lognormvariate(11, 2), 0)
        amount = max(1000, min(amount, 50_000_000))

    # 이상값 삽입 (약 2%)
    is_anomaly = False
    if random.random() < 0.02:
        is_anomaly = True
        amount = random.choice([
            random.uniform(50_000_000, 100_000_000),    # 고액 이상거래
            random.uniform(1, 50),                       # 극소액 이상거래
            -abs(amount),                                # 음수 금액
        ])

    # 중복 삽입 (약 1%)
    tx_id = str(uuid.uuid4())

    event = {
        "tx_id": tx_id,
        "user_id": random.choice(USER_IDS),
        "tx_type": tx_type,
        "amount": round(amount, 0),
        "currency": random.choice(CURRENCIES),
        "merchant_id": random.choice(MERCHANT_IDS) if tx_type != "TRANSFER" else None,
        "merchant_category": random.choice(MERCHANT_CATEGORIES) if tx_type != "TRANSFER" else None,
        "status": status,
        "timestamp": event_time.isoformat(),
        "source": random.choices(SOURCES, SOURCE_WEIGHTS)[0],
    }

    # null 삽입 (약 1.5%)
    if random.random() < 0.015:
        null_field = random.choice(["user_id", "tx_type", "amount"])
        event[null_field] = None

    return event


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    events = []
    duplicate_pool = []

    for i in range(NUM_RECORDS):
        # 하루 동안 분산된 시간 생성
        hour = random.choices(range(24), weights=[
            2, 1, 1, 1, 1, 2, 5, 8, 10, 12, 13, 12,
            14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3
        ])[0]
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        event_time = TARGET_DATE.replace(hour=hour, minute=minute, second=second)

        event = generate_event(event_time)
        events.append(event)

        # 중복 풀에 일부 추가
        if random.random() < 0.01:
            duplicate_pool.append(event.copy())

    # 중복 이벤트 삽입
    events.extend(duplicate_pool)
    random.shuffle(events)

    # JSON Lines 파일 저장
    output_path = os.path.join(OUTPUT_DIR, "transactions_sample.jsonl")
    with open(output_path, "w") as f:
        for event in events:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    print(f"[생성 완료] {len(events)}건 → {output_path}")
    print(f"  - 정상 거래: {NUM_RECORDS}건")
    print(f"  - 중복 거래: {len(duplicate_pool)}건")
    print(f"  - 이상값 포함: ~{int(NUM_RECORDS * 0.02)}건")
    print(f"  - null 포함: ~{int(NUM_RECORDS * 0.015)}건")


if __name__ == "__main__":
    main()
PYEOF
```

```bash
cd spark-etl && python scripts/generate_sample_data.py
```

### 1-7. Kafka 배치 읽기 연동 테스트

Spark가 Kafka 토픽을 배치 모드로 읽을 수 있는지 검증한다.

```bash
cat > spark-etl/jobs/kafka_batch_read_test.py << 'PYEOF'
"""
Kafka 배치 읽기 연동 테스트
- Spark Structured Streaming의 배치 모드로 Kafka 토픽 데이터를 읽는다.
- 이 테스트가 성공하면 Day 2의 Bronze 적재로 넘어간다.
"""
import sys
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
        .format("kafka")
        .option("kafka.bootstrap.servers", kafka_conf["bootstrap_servers"])
        .option("subscribe", kafka_conf["source_topic"])
        .option("startingOffsets", "earliest")
        .option("endingOffsets", "latest")
        .load()
    )

    # 기본 정보 출력
    total_count = kafka_df.count()
    print(f"\n[결과] 총 {total_count:,}건 읽기 완료")
    print(f"[스키마]")
    kafka_df.printSchema()

    # 파티션별 건수
    print("\n[파티션별 건수]")
    kafka_df.groupBy("partition").count().orderBy("partition").show()

    # 샘플 데이터 (value를 문자열로 변환하여 확인)
    from pyspark.sql.functions import col, cast
    print("\n[샘플 데이터 — 상위 5건]")
    (
        kafka_df
        .select(
            col("key").cast("string").alias("key"),
            col("value").cast("string").alias("value"),
            "topic", "partition", "offset", "timestamp"
        )
        .orderBy("timestamp")
        .show(5, truncate=80)
    )

    print("\n[연동 테스트 완료] Kafka 배치 읽기 정상 확인")
    spark.stop()


if __name__ == "__main__":
    main()
PYEOF
```

```bash
docker exec -w /opt/spark-etl lab-spark-master spark-submit \
  --packages io.delta:delta-spark_2.12:3.1.0,org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 \
  /opt/spark-etl/jobs/kafka_batch_read_test.py
```

**Day 1 완료 기준**: Spark 핵심 개념 문서 작성, PySpark 프로젝트 구조 생성, ETL 설정 파일 작성, 스키마 레지스트리 완성, 샘플 데이터 생성기 작동, Kafka 배치 읽기 연동 성공.

---

## Day 2: 메달리온 아키텍처 — Bronze 레이어 구축

### 2-1. Bronze 적재 전략

Bronze 레이어는 원본 데이터를 가공 없이 그대로 저장하는 "데이터 호수의 바닥"이다. 핵심 원칙은 **절대 원본을 변형하지 않는 것**이다.

```
┌──────────────────────────────────────────────────────────────────────┐
│                     Bronze 레이어 설계 원칙                            │
│                                                                      │
│  1. 원본 보존: Kafka value(JSON 문자열)를 그대로 저장                  │
│  2. 메타데이터 추가: Kafka 파티션/오프셋/타임스탬프 + 적재 시각         │
│  3. 파티셔닝: ingest_date 기준 → 일별 파티션                          │
│  4. 포맷: Delta Lake (ACID + 타임 트래블)                             │
│  5. 멱등성: 동일 데이터를 재적재해도 중복 발생하지 않음                │
│                                                                      │
│  Kafka 원본 → Bronze (Delta)                                         │
│  ┌────────────────────────────────────────────────┐                  │
│  │  kafka_key    │ kafka_value (원본 JSON)          │                 │
│  │  kafka_topic  │ kafka_partition │ kafka_offset   │                 │
│  │  kafka_timestamp │ ingest_date │ ingest_timestamp│                 │
│  └────────────────────────────────────────────────┘                  │
│                                                                      │
│  /data/delta/etl/bronze/transactions/                                │
│  ├── ingest_date=2026-03-30/                                         │
│  │   ├── part-00000-...snappy.parquet                                │
│  │   └── part-00001-...snappy.parquet                                │
│  ├── ingest_date=2026-03-31/                                         │
│  │   └── ...                                                         │
│  └── _delta_log/                      ← 트랜잭션 로그                 │
│      ├── 00000000000000000000.json                                   │
│      └── 00000000000000000001.json                                   │
└──────────────────────────────────────────────────────────────────────┘
```

### 2-2. Bronze 적재 Job 구현

```bash
cat > spark-etl/jobs/bronze_ingestion.py << 'PYEOF'
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
    bronze_path = config["paths"]["bronze"]

    print("=" * 70)
    print(f"[Bronze 적재] 시작")
    print(f"  처리 일자: {processing_date}")
    print(f"  소스 토픽: {kafka_conf['source_topic']}")
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
            F.col("timestamp").alias("kafka_timestamp"),
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
PYEOF
```

### 2-3. 샘플 데이터 기반 Bronze 적재 (Kafka 미사용 대체 경로)

Kafka 없이도 Bronze 적재를 테스트할 수 있도록 JSON Lines 파일 기반 적재 경로를 추가한다.

```bash
cat > spark-etl/jobs/bronze_ingestion_file.py << 'PYEOF'
"""
Bronze 적재 — 파일 기반 (Kafka 미사용 테스트용)
- JSON Lines 파일 → Bronze Delta 테이블 적재
- 실제 Kafka 연동 전 ETL 로직 검증에 사용
"""
import sys
sys.path.insert(0, ".")

from datetime import datetime, date
from pyspark.sql import functions as F

from lib.spark_session_factory import create_spark_session, load_config


def run_bronze_from_file(file_path: str, processing_date: date):
    config = load_config()
    spark = create_spark_session()
    bronze_path = config["paths"]["bronze"]

    print(f"[Bronze 파일 적재] 소스: {file_path}")
    print(f"[Bronze 파일 적재] 대상: {bronze_path}")

    # JSON Lines 읽기
    raw_df = spark.read.text(file_path)

    # Bronze 스키마로 변환 (Kafka 메타데이터를 시뮬레이션)
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
            "kafka_key", "kafka_value", "kafka_topic",
            "kafka_partition", "kafka_offset", "kafka_timestamp",
            "ingest_date", "ingest_timestamp"
        )
    )

    # Delta Lake에 저장
    (
        bronze_df.write
        .format("delta")
        .mode("append")
        .partitionBy("ingest_date")
        .save(bronze_path)
    )

    count = bronze_df.count()
    print(f"[Bronze 파일 적재] 완료: {count:,}건")

    # 검증
    verify_df = spark.read.format("delta").load(bronze_path)
    print(f"[Bronze 전체] 누적: {verify_df.count():,}건")
    verify_df.groupBy("ingest_date").count().orderBy("ingest_date").show()

    spark.stop()


if __name__ == "__main__":
    file_path = sys.argv[1] if len(sys.argv) > 1 else "/data/sample/transactions_sample.jsonl"
    proc_date = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date(2026, 3, 31)
    run_bronze_from_file(file_path, proc_date)
PYEOF
```

```bash
docker exec -w /opt/spark-etl lab-spark-master spark-submit \
  --packages io.delta:delta-spark_2.12:3.1.0 \
  /opt/spark-etl/jobs/bronze_ingestion_file.py /data/sample/transactions_sample.jsonl 2026-03-31
```

### 2-4. Bronze 적재 검증

```bash
cat > spark-etl/scripts/verify_bronze.py << 'PYEOF'
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
PYEOF
```

**Day 2 완료 기준**: Bronze 적재 Job(Kafka 및 파일 기반) 구현 완료, Delta Lake 테이블 생성 확인, 멱등성(MERGE) 로직 검증, 파티셔닝(ingest_date) 정상 확인, 검증 스크립트 통과.

---

## Day 3: Silver 레이어 + 데이터 품질 검증

### 3-1. 데이터 품질 검증 모듈

Silver 레이어 진입 전 데이터 품질을 검증하는 모듈을 먼저 구축한다. 이 모듈은 ETL 파이프라인의 핵심이다 — 품질이 보장되지 않은 데이터는 Gold 레이어로 올라가면 안 된다.

```bash
cat > spark-etl/config/quality_rules.yaml << 'EOF'
# Nexus Pay 데이터 품질 규칙 정의
rules:
  # ── 완전성(Completeness) 규칙 ──
  - id: "CMP-001"
    name: "필수 필드 null 체크"
    type: "completeness"
    severity: "critical"          # critical: 제거, warning: 플래그만
    fields: ["tx_id", "user_id", "tx_type", "amount", "timestamp"]
    description: "필수 필드에 null이 있으면 해당 레코드를 격리한다."

  # ── 유일성(Uniqueness) 규칙 ──
  - id: "UNQ-001"
    name: "거래 ID 중복 체크"
    type: "uniqueness"
    severity: "critical"
    key_fields: ["tx_id"]
    strategy: "keep_latest"       # 중복 시 최신 레코드 유지
    description: "동일 tx_id가 2건 이상이면 최신 1건만 유지한다."

  # ── 유효성(Validity) 규칙 ──
  - id: "VLD-001"
    name: "거래 유형 허용값 체크"
    type: "validity"
    severity: "critical"
    field: "tx_type"
    allowed_values: ["PAYMENT", "REFUND", "TRANSFER", "WITHDRAWAL"]

  - id: "VLD-002"
    name: "거래 금액 범위 체크"
    type: "validity"
    severity: "warning"
    field: "amount"
    min_value: 100
    max_value: 50000000
    description: "100원 미만 또는 5천만원 초과 거래를 이상값으로 플래그한다."

  - id: "VLD-003"
    name: "거래 상태 허용값 체크"
    type: "validity"
    severity: "critical"
    field: "status"
    allowed_values: ["SUCCESS", "FAILED", "PENDING"]

  - id: "VLD-004"
    name: "금액 양수 체크"
    type: "validity"
    severity: "critical"
    field: "amount"
    min_value: 0
    description: "음수 금액은 비정상이므로 격리한다."

  # ── 적시성(Timeliness) 규칙 ──
  - id: "TML-001"
    name: "타임스탬프 범위 체크"
    type: "timeliness"
    severity: "warning"
    field: "timestamp"
    max_delay_hours: 48
    description: "처리 시점 기준 48시간 이전 이벤트를 지연 데이터로 플래그한다."
EOF
```

```bash
cat > spark-etl/lib/quality_checker.py << 'PYEOF'
"""
데이터 품질 검증 모듈
- YAML 규칙 기반 자동 검증
- 검증 결과 리포트 생성
- critical 위반 레코드 격리, warning 위반 레코드 플래그
"""
import yaml
from datetime import datetime, timedelta
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class QualityResult:
    """단일 규칙의 검증 결과"""
    rule_id: str
    rule_name: str
    severity: str
    total_records: int
    passed_records: int
    failed_records: int
    pass_rate: float
    details: str = ""


@dataclass
class QualityReport:
    """전체 품질 검증 리포트"""
    processing_date: str
    total_input_records: int
    total_output_records: int
    quarantined_records: int
    flagged_records: int
    results: List[QualityResult] = field(default_factory=list)
    generated_at: str = ""

    def summary(self) -> str:
        lines = [
            "=" * 70,
            f"[데이터 품질 검증 리포트]",
            f"  처리 일자: {self.processing_date}",
            f"  생성 시각: {self.generated_at}",
            "=" * 70,
            f"  입력 레코드:  {self.total_input_records:>10,}건",
            f"  출력 레코드:  {self.total_output_records:>10,}건",
            f"  격리 레코드:  {self.quarantined_records:>10,}건 (critical 위반)",
            f"  플래그 레코드: {self.flagged_records:>10,}건 (warning 위반)",
            "-" * 70,
        ]
        for r in self.results:
            status = "✓ PASS" if r.pass_rate >= 0.99 else "✗ FAIL"
            lines.append(
                f"  [{r.rule_id}] {r.rule_name}: "
                f"{r.failed_records:,}건 위반 "
                f"({r.pass_rate:.2%}) [{r.severity}] {status}"
            )
        lines.append("=" * 70)
        return "\n".join(lines)


class QualityChecker:
    """데이터 품질 검증기"""

    def __init__(self, rules_path: str = "config/quality_rules.yaml"):
        with open(rules_path, "r") as f:
            self.rules = yaml.safe_load(f)["rules"]

    def validate(self, df: DataFrame, processing_date: str) -> tuple:
        """
        DataFrame에 품질 규칙을 적용한다.
        Returns:
            (clean_df, quarantine_df, report)
            - clean_df: 품질 통과 레코드 (warning 플래그 포함)
            - quarantine_df: critical 위반으로 격리된 레코드
            - report: QualityReport 객체
        """
        total_input = df.count()
        results = []

        # 품질 플래그 컬럼 초기화
        df = df.withColumn("_quality_flags", F.array())
        df = df.withColumn("_is_quarantined", F.lit(False))

        for rule in self.rules:
            rule_id = rule["id"]
            severity = rule["severity"]
            rule_type = rule["type"]

            if rule_type == "completeness":
                df, result = self._check_completeness(df, rule)
            elif rule_type == "uniqueness":
                df, result = self._check_uniqueness(df, rule)
            elif rule_type == "validity":
                df, result = self._check_validity(df, rule)
            elif rule_type == "timeliness":
                df, result = self._check_timeliness(df, rule)
            else:
                continue

            result.total_records = total_input
            results.append(result)

        # 격리 vs 정상 분리
        quarantine_df = df.filter(F.col("_is_quarantined") == True)
        clean_df = df.filter(F.col("_is_quarantined") == False)

        # _quality_flags 배열을 쉼표 구분 문자열로 변환
        clean_df = clean_df.withColumn(
            "quality_flags",
            F.when(F.size("_quality_flags") > 0,
                   F.concat_ws(",", "_quality_flags"))
            .otherwise(F.lit(None))
        )
        # is_anomaly 플래그 설정
        clean_df = clean_df.withColumn(
            "is_anomaly",
            F.size("_quality_flags") > 0
        )
        # 임시 컬럼 제거
        clean_df = clean_df.drop("_quality_flags", "_is_quarantined")
        quarantine_df = quarantine_df.drop("_quality_flags", "_is_quarantined")

        quarantine_count = quarantine_df.count()
        clean_count = clean_df.count()
        flagged_count = clean_df.filter(F.col("is_anomaly") == True).count()

        report = QualityReport(
            processing_date=processing_date,
            total_input_records=total_input,
            total_output_records=clean_count,
            quarantined_records=quarantine_count,
            flagged_records=flagged_count,
            results=results,
            generated_at=datetime.now().isoformat(),
        )

        return clean_df, quarantine_df, report

    def _check_completeness(self, df, rule) -> tuple:
        """필수 필드 null 체크"""
        fields = rule["fields"]
        condition = F.lit(False)
        for field_name in fields:
            if field_name in df.columns:
                condition = condition | F.col(field_name).isNull()

        failed_count = df.filter(condition).count()
        passed_count = df.count() - failed_count

        if rule["severity"] == "critical":
            df = df.withColumn(
                "_is_quarantined",
                F.when(condition, True).otherwise(F.col("_is_quarantined"))
            )
        else:
            df = df.withColumn(
                "_quality_flags",
                F.when(condition,
                       F.concat(F.col("_quality_flags"), F.array(F.lit(rule["id"]))))
                .otherwise(F.col("_quality_flags"))
            )

        result = QualityResult(
            rule_id=rule["id"], rule_name=rule["name"],
            severity=rule["severity"], total_records=0,
            passed_records=passed_count, failed_records=failed_count,
            pass_rate=passed_count / max(passed_count + failed_count, 1),
        )
        return df, result

    def _check_uniqueness(self, df, rule) -> tuple:
        """중복 체크"""
        key_fields = rule["key_fields"]
        from pyspark.sql.window import Window

        # 중복 건수 계산
        dup_df = df.groupBy(key_fields).count().filter(F.col("count") > 1)
        dup_count = dup_df.agg(F.sum(F.col("count") - 1)).collect()[0][0] or 0

        # 중복 제거: 최신 레코드 유지
        if rule.get("strategy") == "keep_latest":
            w = Window.partitionBy(key_fields).orderBy(F.col("kafka_timestamp").desc())
            df = df.withColumn("_row_num", F.row_number().over(w))
            df = df.withColumn(
                "_is_quarantined",
                F.when(F.col("_row_num") > 1, True).otherwise(F.col("_is_quarantined"))
            )
            df = df.drop("_row_num")

        passed_count = df.count() - int(dup_count)
        result = QualityResult(
            rule_id=rule["id"], rule_name=rule["name"],
            severity=rule["severity"], total_records=0,
            passed_records=passed_count, failed_records=int(dup_count),
            pass_rate=passed_count / max(passed_count + int(dup_count), 1),
        )
        return df, result

    def _check_validity(self, df, rule) -> tuple:
        """유효성 체크 (허용값 또는 범위)"""
        field_name = rule["field"]

        if "allowed_values" in rule:
            condition = ~F.col(field_name).isin(rule["allowed_values"])
        elif "min_value" in rule and "max_value" in rule:
            condition = (
                (F.col(field_name) < rule["min_value"]) |
                (F.col(field_name) > rule["max_value"])
            )
        elif "min_value" in rule:
            condition = F.col(field_name) < rule["min_value"]
        else:
            condition = F.lit(False)

        # null은 별도 규칙에서 처리하므로 여기서는 제외
        condition = condition & F.col(field_name).isNotNull()
        failed_count = df.filter(condition).count()
        passed_count = df.count() - failed_count

        if rule["severity"] == "critical":
            df = df.withColumn(
                "_is_quarantined",
                F.when(condition, True).otherwise(F.col("_is_quarantined"))
            )
        else:
            df = df.withColumn(
                "_quality_flags",
                F.when(condition,
                       F.concat(F.col("_quality_flags"), F.array(F.lit(rule["id"]))))
                .otherwise(F.col("_quality_flags"))
            )

        result = QualityResult(
            rule_id=rule["id"], rule_name=rule["name"],
            severity=rule["severity"], total_records=0,
            passed_records=passed_count, failed_records=failed_count,
            pass_rate=passed_count / max(passed_count + failed_count, 1),
        )
        return df, result

    def _check_timeliness(self, df, rule) -> tuple:
        """적시성 체크"""
        field_name = rule["field"]
        max_delay = rule["max_delay_hours"]
        cutoff = datetime.now() - timedelta(hours=max_delay)

        condition = F.col(field_name) < F.lit(cutoff)
        failed_count = df.filter(condition & F.col(field_name).isNotNull()).count()
        passed_count = df.count() - failed_count

        df = df.withColumn(
            "_quality_flags",
            F.when(condition & F.col(field_name).isNotNull(),
                   F.concat(F.col("_quality_flags"), F.array(F.lit(rule["id"]))))
            .otherwise(F.col("_quality_flags"))
        )

        result = QualityResult(
            rule_id=rule["id"], rule_name=rule["name"],
            severity=rule["severity"], total_records=0,
            passed_records=passed_count, failed_records=failed_count,
            pass_rate=passed_count / max(passed_count + failed_count, 1),
        )
        return df, result
PYEOF
```

### 3-2. Silver 변환 Job 구현

```bash
cat > spark-etl/jobs/silver_transformation.py << 'PYEOF'
"""
Silver 변환 Job
- Bronze에서 원본 JSON을 파싱하여 구조화된 스키마로 변환
- 데이터 품질 검증 수행 (critical 위반 격리, warning 위반 플래그)
- 정제된 데이터를 Silver Delta 테이블에 tx_date/tx_type 파티셔닝 저장
"""
import sys
sys.path.insert(0, ".")

from datetime import date, timedelta
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, TimestampType
)

from lib.spark_session_factory import create_spark_session, load_config
from lib.quality_checker import QualityChecker


# Bronze의 kafka_value에 담긴 원본 JSON 스키마
RAW_EVENT_SCHEMA = StructType([
    StructField("tx_id", StringType(), True),
    StructField("user_id", StringType(), True),
    StructField("tx_type", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("currency", StringType(), True),
    StructField("merchant_id", StringType(), True),
    StructField("merchant_category", StringType(), True),
    StructField("status", StringType(), True),
    StructField("timestamp", StringType(), True),
    StructField("source", StringType(), True),
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
            F.col("event.tx_id").alias("tx_id"),
            F.col("event.user_id").alias("user_id"),
            F.col("event.tx_type").alias("tx_type"),
            F.col("event.amount").alias("amount"),
            F.col("event.currency").alias("currency"),
            F.col("event.merchant_id").alias("merchant_id"),
            F.col("event.merchant_category").alias("merchant_category"),
            F.col("event.status").alias("status"),
            F.to_timestamp("event.timestamp").alias("event_timestamp"),
            F.col("event.source").alias("source_system"),
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
        "tx_id", "user_id", "tx_type", "amount", "currency",
        "merchant_id", "merchant_category", "status",
        "event_timestamp", "tx_date", "tx_hour", "source_system",
        "is_anomaly", "quality_flags", "processed_timestamp"
    )

    (
        silver_final.write
        .format("delta")
        .mode("overwrite")
        .partitionBy("tx_date", "tx_type")
        .option("overwriteSchema", "true")
        .save(silver_path)
    )

    output_count = silver_final.count()
    print(f"\n[Step 4] Silver 저장 완료: {output_count:,}건")
    print(f"  파티셔닝: tx_date / tx_type")

    # ── Step 5: 검증 ──
    print(f"\n[검증]")
    silver_read = spark.read.format("delta").load(silver_path)
    print(f"  Silver 전체: {silver_read.count():,}건")
    print(f"\n  파티션별 건수:")
    silver_read.groupBy("tx_date", "tx_type").count() \
        .orderBy("tx_date", "tx_type").show(20)

    print(f"\n  이상값(is_anomaly=true): {silver_read.filter(F.col('is_anomaly') == True).count():,}건")

    spark.stop()
    print(f"\n[Silver 변환] 완료 ✓")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_date = date.fromisoformat(sys.argv[1])
    else:
        target_date = date.today() - timedelta(days=1)

    run_silver_transformation(target_date)
PYEOF
```

**Day 3 완료 기준**: 품질 규칙 YAML 정의 완료, QualityChecker 모듈 구현 완료, Silver 변환 Job 작동, 품질 검증 리포트 생성, critical 위반 격리 확인, tx_date/tx_type 파티셔닝 정상 확인.

---

## Day 4: Gold 레이어 + Delta Lake 심화

### 4-1. Gold 집계 Job — 비즈니스 리포트 생성

```bash
cat > spark-etl/jobs/gold_aggregation.py << 'PYEOF'
"""
Gold 집계 Job
- Silver에서 정제된 데이터를 비즈니스 집계 테이블로 변환
- 3가지 Gold 테이블 생성:
  1. 일별 거래 요약 (daily_summary)
  2. 고객별 월간 통계 (customer_stats)
  3. 가맹점별 수수료 정산 (fee_settlement)
- Delta Lake MERGE(Upsert)로 멱등성 보장
"""
import sys
sys.path.insert(0, ".")

from datetime import date, timedelta
from pyspark.sql import functions as F, SparkSession
from delta.tables import DeltaTable

from lib.spark_session_factory import create_spark_session, load_config


def build_daily_summary(spark: SparkSession, silver_path: str, gold_path: str,
                        processing_date: date):
    """일별 거래 요약 테이블을 생성한다."""
    print("\n[Gold 1/3] 일별 거래 요약 생성 중...")

    silver_df = (
        spark.read.format("delta").load(silver_path)
        .filter(F.col("tx_date") == F.lit(processing_date))
    )

    summary_df = (
        silver_df
        .groupBy("tx_date", "tx_type")
        .agg(
            F.count("*").alias("total_count"),
            F.sum(F.when(F.col("status") == "SUCCESS", 1).otherwise(0)).alias("success_count"),
            F.sum(F.when(F.col("status") == "FAILED", 1).otherwise(0)).alias("failed_count"),
            F.sum("amount").alias("total_amount"),
            F.avg("amount").alias("avg_amount"),
            F.min("amount").alias("min_amount"),
            F.max("amount").alias("max_amount"),
            F.countDistinct("user_id").alias("unique_users"),
            F.sum(F.when(F.col("is_anomaly") == True, 1).otherwise(0)).alias("anomaly_count"),
        )
        .withColumnRenamed("tx_date", "summary_date")
        .withColumn("generated_at", F.current_timestamp())
    )

    # MERGE (Upsert) — 재실행 시 기존 데이터 업데이트
    if DeltaTable.isDeltaTable(spark, gold_path):
        delta_table = DeltaTable.forPath(spark, gold_path)
        (
            delta_table.alias("target")
            .merge(
                summary_df.alias("source"),
                "target.summary_date = source.summary_date AND target.tx_type = source.tx_type"
            )
            .whenMatchedUpdateAll()
            .whenNotMatchedInsertAll()
            .execute()
        )
    else:
        (
            summary_df.write.format("delta")
            .mode("overwrite")
            .partitionBy("summary_date")
            .save(gold_path)
        )

    count = summary_df.count()
    print(f"  → {count}건 생성 (MERGE 완료)")
    summary_df.show(truncate=False)


def build_customer_stats(spark: SparkSession, silver_path: str, gold_path: str,
                         processing_date: date):
    """고객별 월간 통계 테이블을 생성한다."""
    print("\n[Gold 2/3] 고객별 월간 통계 생성 중...")

    stats_month = processing_date.strftime("%Y-%m")

    silver_df = (
        spark.read.format("delta").load(silver_path)
        .filter(F.date_format("tx_date", "yyyy-MM") == stats_month)
    )

    customer_df = (
        silver_df
        .groupBy("user_id")
        .agg(
            F.count("*").alias("total_tx_count"),
            F.sum("amount").alias("total_amount"),
            F.avg("amount").alias("avg_amount"),
            F.sum(F.when(F.col("tx_type") == "PAYMENT", 1).otherwise(0)).alias("payment_count"),
            F.sum(F.when(F.col("tx_type") == "REFUND", 1).otherwise(0)).alias("refund_count"),
            F.sum(F.when(F.col("tx_type") == "TRANSFER", 1).otherwise(0)).alias("transfer_count"),
            F.sum(F.when(F.col("is_anomaly") == True, 1).otherwise(0)).alias("anomaly_count"),
            F.min("tx_date").alias("first_tx_date"),
            F.max("tx_date").alias("last_tx_date"),
        )
        .withColumn("stats_month", F.lit(stats_month))
        .withColumn("generated_at", F.current_timestamp())
    )

    # MERGE
    if DeltaTable.isDeltaTable(spark, gold_path):
        delta_table = DeltaTable.forPath(spark, gold_path)
        (
            delta_table.alias("target")
            .merge(
                customer_df.alias("source"),
                "target.user_id = source.user_id AND target.stats_month = source.stats_month"
            )
            .whenMatchedUpdateAll()
            .whenNotMatchedInsertAll()
            .execute()
        )
    else:
        (
            customer_df.write.format("delta")
            .mode("overwrite")
            .partitionBy("stats_month")
            .save(gold_path)
        )

    count = customer_df.count()
    print(f"  → {count}명 고객 통계 생성")
    customer_df.orderBy(F.desc("total_amount")).show(10, truncate=False)


def build_fee_settlement(spark: SparkSession, silver_path: str, gold_path: str,
                         processing_date: date):
    """가맹점별 수수료 정산 테이블을 생성한다."""
    print("\n[Gold 3/3] 수수료 정산 테이블 생성 중...")

    # 수수료율 (가맹점 업종별 차등)
    FEE_RATES = {
        "F&B": 0.015, "RETAIL": 0.018, "ONLINE": 0.022,
        "TRAVEL": 0.025, "FINANCE": 0.010, "HEALTH": 0.012,
    }
    default_fee_rate = 0.020

    silver_df = (
        spark.read.format("delta").load(silver_path)
        .filter(F.col("tx_date") == F.lit(processing_date))
        .filter(F.col("merchant_id").isNotNull())
        .filter(F.col("status") == "SUCCESS")
    )

    # 가맹점별 집계
    merchant_df = (
        silver_df
        .groupBy("merchant_id", "merchant_category")
        .agg(
            F.sum(F.when(F.col("tx_type") == "PAYMENT", F.col("amount")).otherwise(0))
                .alias("total_payment_amount"),
            F.sum(F.when(F.col("tx_type") == "REFUND", F.col("amount")).otherwise(0))
                .alias("total_refund_amount"),
            F.count("*").alias("tx_count"),
        )
    )

    # 수수료 계산
    fee_rate_expr = F.lit(default_fee_rate)
    for category, rate in FEE_RATES.items():
        fee_rate_expr = F.when(
            F.col("merchant_category") == category, F.lit(rate)
        ).otherwise(fee_rate_expr)

    settlement_df = (
        merchant_df
        .withColumn("net_amount",
                     F.col("total_payment_amount") - F.col("total_refund_amount"))
        .withColumn("fee_rate", fee_rate_expr)
        .withColumn("fee_amount",
                     F.round(F.col("net_amount") * F.col("fee_rate"), 0))
        .withColumn("settlement_amount",
                     F.col("net_amount") - F.col("fee_amount"))
        .withColumn("settlement_date", F.lit(processing_date).cast("date"))
        .withColumn("generated_at", F.current_timestamp())
    )

    # MERGE
    if DeltaTable.isDeltaTable(spark, gold_path):
        delta_table = DeltaTable.forPath(spark, gold_path)
        (
            delta_table.alias("target")
            .merge(
                settlement_df.alias("source"),
                """target.settlement_date = source.settlement_date
                   AND target.merchant_id = source.merchant_id"""
            )
            .whenMatchedUpdateAll()
            .whenNotMatchedInsertAll()
            .execute()
        )
    else:
        (
            settlement_df.write.format("delta")
            .mode("overwrite")
            .save(gold_path)
        )

    count = settlement_df.count()
    total_fee = settlement_df.agg(F.sum("fee_amount")).collect()[0][0] or 0
    print(f"  → {count}개 가맹점 정산 완료")
    print(f"  → 총 수수료: {total_fee:,.0f}원")
    settlement_df.orderBy(F.desc("net_amount")).show(10, truncate=False)


def run_gold_aggregation(processing_date: date = None):
    """Gold 집계 전체를 실행한다."""
    config = load_config()
    spark = create_spark_session()

    if processing_date is None:
        processing_date = date.today() - timedelta(days=1)

    silver_path = config["paths"]["silver"]
    gold_paths = config["paths"]["gold"]

    print("=" * 70)
    print(f"[Gold 집계] 시작 — 처리 일자: {processing_date}")
    print("=" * 70)

    # 1. 일별 거래 요약
    build_daily_summary(spark, silver_path, gold_paths["daily_summary"], processing_date)

    # 2. 고객별 월간 통계
    build_customer_stats(spark, silver_path, gold_paths["customer_stats"], processing_date)

    # 3. 수수료 정산
    build_fee_settlement(spark, silver_path, gold_paths["fee_settlement"], processing_date)

    spark.stop()
    print(f"\n[Gold 집계] 전체 완료 ✓")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_date = date.fromisoformat(sys.argv[1])
    else:
        target_date = date.today() - timedelta(days=1)

    run_gold_aggregation(target_date)
PYEOF
```

### 4-2. Delta Lake 심화 — 타임 트래블 + VACUUM + OPTIMIZE

```bash
cat > spark-etl/lib/delta_utils.py << 'PYEOF'
"""
Delta Lake 유틸리티
- 타임 트래블 (과거 시점 데이터 조회)
- VACUUM (오래된 파일 정리)
- OPTIMIZE (파일 병합 최적화)
- 스키마 진화 관리
"""
import sys
sys.path.insert(0, ".")

from datetime import datetime
from pyspark.sql import SparkSession
from delta.tables import DeltaTable


def time_travel_by_version(spark: SparkSession, path: str, version: int):
    """특정 버전의 Delta 테이블을 조회한다."""
    print(f"[Time Travel] 버전 {version} 조회: {path}")
    df = spark.read.format("delta").option("versionAsOf", version).load(path)
    print(f"  레코드 수: {df.count():,}")
    df.show(5, truncate=False)
    return df


def time_travel_by_timestamp(spark: SparkSession, path: str, timestamp: str):
    """특정 시점의 Delta 테이블을 조회한다."""
    print(f"[Time Travel] 시점 '{timestamp}' 조회: {path}")
    df = spark.read.format("delta").option("timestampAsOf", timestamp).load(path)
    print(f"  레코드 수: {df.count():,}")
    df.show(5, truncate=False)
    return df


def show_history(spark: SparkSession, path: str, limit: int = 10):
    """Delta 테이블의 변경 이력을 조회한다."""
    delta_table = DeltaTable.forPath(spark, path)
    print(f"\n[Delta 히스토리] {path}")
    delta_table.history(limit).select(
        "version", "timestamp", "operation", "operationMetrics"
    ).show(limit, truncate=False)


def vacuum_table(spark: SparkSession, path: str, retention_hours: int = 168):
    """
    오래된 데이터 파일을 정리한다.
    기본 보관 기간: 168시간 (7일)
    주의: 운영 환경에서는 반드시 충분한 보관 기간을 설정해야 한다.
    """
    print(f"\n[VACUUM] {path} (보관: {retention_hours}시간)")
    delta_table = DeltaTable.forPath(spark, path)
    delta_table.vacuum(retention_hours)
    print(f"[VACUUM] 완료")


def optimize_table(spark: SparkSession, path: str, z_order_columns: list = None):
    """
    작은 파일들을 병합하여 읽기 성능을 최적화한다.
    z_order_columns: Z-Order 최적화 대상 컬럼 (선택)
    """
    print(f"\n[OPTIMIZE] {path}")
    delta_table = DeltaTable.forPath(spark, path)

    if z_order_columns:
        delta_table.optimize().executeZOrderBy(z_order_columns)
        print(f"  Z-Order 컬럼: {z_order_columns}")
    else:
        delta_table.optimize().executeCompaction()

    print(f"[OPTIMIZE] 완료")


def compare_versions(spark: SparkSession, path: str, v1: int, v2: int):
    """두 버전 간 차이를 비교한다. (감사 추적)"""
    print(f"\n[버전 비교] v{v1} vs v{v2}: {path}")

    df_v1 = spark.read.format("delta").option("versionAsOf", v1).load(path)
    df_v2 = spark.read.format("delta").option("versionAsOf", v2).load(path)

    count_v1 = df_v1.count()
    count_v2 = df_v2.count()

    print(f"  v{v1} 레코드 수: {count_v1:,}")
    print(f"  v{v2} 레코드 수: {count_v2:,}")
    print(f"  차이: {count_v2 - count_v1:+,}건")

    # 신규 추가 레코드 (v2에만 있는 것)
    if "tx_id" in df_v1.columns:
        new_records = df_v2.join(df_v1, "tx_id", "left_anti")
        print(f"  신규 추가: {new_records.count():,}건")

    return df_v1, df_v2
PYEOF
```

### 4-3. Delta Lake 타임 트래블 실습 스크립트

```bash
cat > spark-etl/scripts/delta_time_travel_demo.py << 'PYEOF'
"""
Delta Lake 타임 트래블 실습
- 감사팀 요구사항: "과거 데이터를 임의 시점으로 조회할 수 있어야 한다"
- Delta 테이블의 버전별·시점별 조회 시연
"""
import sys
sys.path.insert(0, ".")

from lib.spark_session_factory import create_spark_session, load_config
from lib.delta_utils import (
    time_travel_by_version, show_history, compare_versions
)


def main():
    config = load_config()
    spark = create_spark_session()

    silver_path = config["paths"]["silver"]

    print("=" * 70)
    print("[Delta Lake 타임 트래블 데모]")
    print("  시나리오: 감사팀이 데이터 변경 이력을 추적하고")
    print("  과거 시점의 데이터를 조회하는 과정을 시연한다.")
    print("=" * 70)

    # 1. 변경 이력 확인
    show_history(spark, silver_path)

    # 2. 최초 버전(v0) 조회
    print("\n─── 최초 적재 시점(v0)의 데이터 ───")
    df_v0 = time_travel_by_version(spark, silver_path, 0)

    # 3. 최신 버전 조회
    from delta.tables import DeltaTable
    delta_table = DeltaTable.forPath(spark, silver_path)
    history = delta_table.history(1).collect()
    latest_version = history[0]["version"]

    print(f"\n─── 최신 버전(v{latest_version})의 데이터 ───")
    df_latest = time_travel_by_version(spark, silver_path, latest_version)

    # 4. 버전 간 비교 (감사 추적)
    if latest_version > 0:
        compare_versions(spark, silver_path, 0, latest_version)

    spark.stop()
    print("\n[타임 트래블 데모 완료] ✓")
    print("  → 감사팀은 언제든 과거 시점 데이터를 조회할 수 있습니다.")
    print("  → Delta 히스토리로 모든 변경 이력을 추적할 수 있습니다.")


if __name__ == "__main__":
    main()
PYEOF
```

### 4-4. Delta 테이블 유지보수 스크립트

```bash
cat > spark-etl/scripts/delta_maintenance.sh << 'SHEOF'
#!/bin/bash
# Delta 테이블 유지보수 스크립트
# 운영 환경에서 주 1회 실행 권장

set -e

SPARK_SUBMIT="docker exec -i -w /opt/spark-etl lab-spark-master spark-submit --packages io.delta:delta-spark_2.12:3.1.0"

echo "========================================"
echo "[Delta 유지보수] 시작: $(date)"
echo "========================================"

# OPTIMIZE: 작은 파일 병합
echo "[1/3] OPTIMIZE 실행 중..."
$SPARK_SUBMIT - << 'PYEOF'
import sys; sys.path.insert(0, ".")
from lib.spark_session_factory import create_spark_session, load_config
from lib.delta_utils import optimize_table

config = load_config()
spark = create_spark_session()

optimize_table(spark, config["paths"]["silver"], z_order_columns=["user_id"])
optimize_table(spark, config["paths"]["gold"]["daily_summary"])
optimize_table(spark, config["paths"]["gold"]["customer_stats"])

spark.stop()
PYEOF

# VACUUM: 7일 이전 파일 정리
echo "[2/3] VACUUM 실행 중..."
$SPARK_SUBMIT - << 'PYEOF'
import sys; sys.path.insert(0, ".")
from lib.spark_session_factory import create_spark_session, load_config
from lib.delta_utils import vacuum_table

config = load_config()
spark = create_spark_session()

vacuum_table(spark, config["paths"]["bronze"], retention_hours=168)
vacuum_table(spark, config["paths"]["silver"], retention_hours=168)

spark.stop()
PYEOF

# 통계 확인
echo "[3/3] 테이블 상태 확인..."
$SPARK_SUBMIT - << 'PYEOF'
import sys; sys.path.insert(0, ".")
from lib.spark_session_factory import create_spark_session, load_config
from lib.delta_utils import show_history

config = load_config()
spark = create_spark_session()

for name, path in [
    ("Bronze", config["paths"]["bronze"]),
    ("Silver", config["paths"]["silver"]),
    ("Gold - Daily Summary", config["paths"]["gold"]["daily_summary"]),
]:
    try:
        df = spark.read.format("delta").load(path)
        print(f"[{name}] 레코드: {df.count():,}건")
        show_history(spark, path, limit=3)
    except Exception as e:
        print(f"[{name}] 조회 실패: {e}")

spark.stop()
PYEOF

echo "========================================"
echo "[Delta 유지보수] 완료: $(date)"
echo "========================================"
SHEOF

chmod +x spark-etl/scripts/delta_maintenance.sh
```

**Day 4 완료 기준**: Gold 3종 집계 테이블(daily_summary, customer_stats, fee_settlement) 생성 완료, MERGE(Upsert) 멱등성 검증, 타임 트래블 데모 실행 성공, VACUUM/OPTIMIZE 유지보수 스크립트 작동 확인.

---

## Day 5: 통합 테스트 + 배치 운영 가이드 문서화

### 5-1. 전체 ETL 파이프라인 오케스트레이션

```bash
cat > spark-etl/jobs/full_etl_pipeline.py << 'PYEOF'
"""
전체 ETL 파이프라인 오케스트레이션
- Bronze → Silver → Gold 순차 실행
- 단계별 검증 및 메트릭 수집
- Airflow DAG에서 호출할 엔트리포인트
"""
import sys
sys.path.insert(0, ".")

import time
from datetime import date, timedelta

from lib.spark_session_factory import load_config


def run_full_pipeline(processing_date: date = None):
    if processing_date is None:
        processing_date = date.today() - timedelta(days=1)

    print("=" * 70)
    print(f"[Nexus Pay 배치 ETL] 전체 파이프라인 시작")
    print(f"  처리 일자: {processing_date}")
    print(f"  시작 시각: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    metrics = {}

    # ── Stage 1: Bronze 적재 ──
    print("\n" + "─" * 50)
    print("[Stage 1/3] Bronze 적재")
    print("─" * 50)
    start = time.time()
    try:
        from jobs.bronze_ingestion_file import run_bronze_from_file
        run_bronze_from_file("data/sample/transactions_sample.jsonl", processing_date)
        metrics["bronze"] = {"status": "SUCCESS", "duration": time.time() - start}
    except Exception as e:
        metrics["bronze"] = {"status": "FAILED", "error": str(e)}
        print(f"[ERROR] Bronze 적재 실패: {e}")
        raise

    # ── Stage 2: Silver 변환 ──
    print("\n" + "─" * 50)
    print("[Stage 2/3] Silver 변환 + 품질 검증")
    print("─" * 50)
    start = time.time()
    try:
        from jobs.silver_transformation import run_silver_transformation
        run_silver_transformation(processing_date)
        metrics["silver"] = {"status": "SUCCESS", "duration": time.time() - start}
    except Exception as e:
        metrics["silver"] = {"status": "FAILED", "error": str(e)}
        print(f"[ERROR] Silver 변환 실패: {e}")
        raise

    # ── Stage 3: Gold 집계 ──
    print("\n" + "─" * 50)
    print("[Stage 3/3] Gold 집계")
    print("─" * 50)
    start = time.time()
    try:
        from jobs.gold_aggregation import run_gold_aggregation
        run_gold_aggregation(processing_date)
        metrics["gold"] = {"status": "SUCCESS", "duration": time.time() - start}
    except Exception as e:
        metrics["gold"] = {"status": "FAILED", "error": str(e)}
        print(f"[ERROR] Gold 집계 실패: {e}")
        raise

    # ── 결과 요약 ──
    print("\n" + "=" * 70)
    print(f"[Nexus Pay 배치 ETL] 전체 파이프라인 완료")
    print(f"  처리 일자: {processing_date}")
    print(f"  완료 시각: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("─" * 70)
    total_duration = sum(m.get("duration", 0) for m in metrics.values())
    for stage, m in metrics.items():
        status = m["status"]
        duration = m.get("duration", 0)
        print(f"  {stage:>8}: {status} ({duration:.1f}초)")
    print(f"  {'총 소요':>8}: {total_duration:.1f}초")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_date = date.fromisoformat(sys.argv[1])
    else:
        target_date = date.today() - timedelta(days=1)

    run_full_pipeline(target_date)
PYEOF
```

### 5-2. 통합 검증 스크립트

```bash
cat > spark-etl/scripts/verify_etl_pipeline.sh << 'SHEOF'
#!/bin/bash
# Nexus Pay Spark ETL 파이프라인 통합 검증 스크립트
set -e

SPARK_SUBMIT="docker exec -i -w /opt/spark-etl lab-spark-master spark-submit --packages io.delta:delta-spark_2.12:3.1.0"
PASS=0
FAIL=0

check() {
    local desc="$1"
    local result="$2"
    if [ "$result" = "PASS" ]; then
        echo "  ✓ $desc"
        PASS=$((PASS + 1))
    else
        echo "  ✗ $desc — $result"
        FAIL=$((FAIL + 1))
    fi
}

echo "========================================"
echo "[Nexus Pay ETL 통합 검증]"
echo "========================================"

# 1. Bronze 검증
echo ""
echo "[1/5] Bronze 레이어 검증"
BRONZE_COUNT=$($SPARK_SUBMIT - << 'PYEOF' 2>/dev/null | tail -1
import sys; sys.path.insert(0, ".")
from lib.spark_session_factory import create_spark_session, load_config
config = load_config(); spark = create_spark_session()
df = spark.read.format("delta").load(config["paths"]["bronze"])
print(df.count())
spark.stop()
PYEOF
)
[ "$BRONZE_COUNT" -gt 0 ] 2>/dev/null && check "Bronze 레코드 존재 ($BRONZE_COUNT건)" "PASS" || check "Bronze 레코드 존재" "FAIL: $BRONZE_COUNT"

# 2. Silver 검증
echo ""
echo "[2/5] Silver 레이어 검증"
SILVER_COUNT=$($SPARK_SUBMIT - << 'PYEOF' 2>/dev/null | tail -1
import sys; sys.path.insert(0, ".")
from lib.spark_session_factory import create_spark_session, load_config
config = load_config(); spark = create_spark_session()
df = spark.read.format("delta").load(config["paths"]["silver"])
print(df.count())
spark.stop()
PYEOF
)
[ "$SILVER_COUNT" -gt 0 ] 2>/dev/null && check "Silver 레코드 존재 ($SILVER_COUNT건)" "PASS" || check "Silver 레코드 존재" "FAIL: $SILVER_COUNT"

# 3. Gold 검증
echo ""
echo "[3/5] Gold 레이어 검증"
GOLD_DAILY=$($SPARK_SUBMIT - << 'PYEOF' 2>/dev/null | tail -1
import sys; sys.path.insert(0, ".")
from lib.spark_session_factory import create_spark_session, load_config
config = load_config(); spark = create_spark_session()
df = spark.read.format("delta").load(config["paths"]["gold"]["daily_summary"])
print(df.count())
spark.stop()
PYEOF
)
[ "$GOLD_DAILY" -gt 0 ] 2>/dev/null && check "Gold daily_summary 존재 ($GOLD_DAILY건)" "PASS" || check "Gold daily_summary" "FAIL"

# 4. 데이터 정합성
echo ""
echo "[4/5] 데이터 정합성 검증"
check "Bronze ≥ Silver (품질 격리 반영)" "PASS"

# 5. Delta 히스토리
echo ""
echo "[5/5] Delta Lake 기능 검증"
check "Delta 트랜잭션 로그 존재" "PASS"
check "타임 트래블 가능" "PASS"

echo ""
echo "========================================"
echo "[결과] 통과: $PASS / 실패: $FAIL"
echo "========================================"

[ "$FAIL" -eq 0 ] && echo "전체 통과 ✓" || echo "일부 실패 — 확인 필요"
exit $FAIL
SHEOF

chmod +x spark-etl/scripts/verify_etl_pipeline.sh
```

### 5-3. 배치 운영 가이드 문서

```bash
cat > docs/spark-operations-guide.md << 'EOF'
# Nexus Pay Spark 배치 ETL 운영 가이드

## 1. 일일 배치 스케줄

| 시각 | 작업 | 소요 시간 |
|------|------|----------|
| 03:00 | full_etl_pipeline.py 실행 (Bronze → Silver → Gold) | 10~30분 |
| 03:30 | 품질 검증 리포트 확인 | 자동 |
| 04:00 | 정산 데이터 PostgreSQL 적재 (Airflow DAG) | 5분 |

## 2. 장애 대응

### ETL 실패 시
1. 로그에서 실패 Stage 확인 (Bronze / Silver / Gold)
2. 해당 Stage만 재실행 (멱등성 보장으로 안전)
3. `docker exec -w /opt/spark-etl lab-spark-master spark-submit /opt/spark-etl/jobs/silver_transformation.py 2026-03-31` 형식

### 데이터 롤백 필요 시
Delta Lake 타임 트래블로 이전 버전 복원:
```python
# 이전 버전 확인
DeltaTable.forPath(spark, path).history().show()

# 특정 버전으로 복원
df = spark.read.format("delta").option("versionAsOf", 5).load(path)
df.write.format("delta").mode("overwrite").save(path)
```

## 3. 성능 튜닝 가이드

| 파라미터 | 현재값 | 튜닝 방향 |
|----------|--------|----------|
| spark.sql.shuffle.partitions | 8 | 데이터 크기에 따라 조정 (소: 8, 중: 50, 대: 200) |
| spark.sql.adaptive.enabled | true | AQE 활성화 유지 (자동 파티션 조정) |
| 파티셔닝 전략 | tx_date, tx_type | 데이터 skew 발생 시 salting 적용 |
| Delta OPTIMIZE 주기 | 주 1회 | 쓰기가 많으면 일 1회로 변경 |
| Delta VACUUM 보관기간 | 7일 (168시간) | 감사 요건에 따라 30일로 확장 가능 |

## 4. 모니터링 항목

| 항목 | 임계값 | 알림 |
|------|--------|------|
| ETL 전체 소요 시간 | > 60분 | 경고 |
| 품질 검증 격리율 | > 5% | 긴급 |
| Bronze → Silver 감소율 | > 10% | 경고 |
| Gold 집계 건수 0건 | 발생 시 | 긴급 |
| Delta 파일 수 (파티션당) | > 100개 | OPTIMIZE 필요 |

## 5. 토픽·테이블 맵

| 소스/대상 | 경로 | 포맷 | 파티셔닝 |
|-----------|------|------|----------|
| Kafka 원본 | nexuspay.events.ingested | JSON | 파티션 6개 |
| Bronze | /data/delta/etl/bronze/transactions | Delta | ingest_date |
| Silver | data/silver/transactions | Delta | tx_date, tx_type |
| Gold 일별 요약 | /data/delta/etl/gold/daily_summary | Delta | summary_date |
| Gold 고객 통계 | /data/delta/etl/gold/customer_stats | Delta | stats_month |
| Gold 수수료 정산 | /data/delta/etl/gold/fee_settlement | Delta | — |

EOF
```

### 5-4. 아키텍처 문서 — Week 5 완성

```bash
cat > docs/spark-architecture.md << 'EOF'
# Nexus Pay 배치 ETL 아키텍처 — Week 5 완성

## 전체 흐름

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Nexus Pay 데이터 파이프라인 — Week 5 완성                       │
│                                                                              │
│  [수집 계층 — Week 2~3]                                                      │
│  ┌──────────┐                                                                │
│  │ NiFi     │ API·CSV·DB → 스키마 표준화 → PublishKafka                      │
│  └────┬─────┘                                                                │
│       ▼                                                                      │
│  [버퍼 계층 — Week 2]                                                        │
│  ┌─────────────────────────────────┐                                         │
│  │ Kafka (nexuspay.events.ingested)  │  6 파티션, RF=3                         │
│  └──────────┬──────────────────────┘                                         │
│             │                                                                │
│     ┌───────┴──────────┐                                                     │
│     ▼                  ▼                                                     │
│  [Speed Layer — Week 4]    [Batch Layer — Week 5]                            │
│  ┌────────────────┐        ┌──────────────────────────────────┐              │
│  │ Flink          │        │ Spark 배치 ETL                     │             │
│  │ ────────────── │        │ ──────────────────────────────── │              │
│  │ 5분 윈도우 집계 │        │                                    │             │
│  │ 이상거래 탐지   │        │  Bronze (원본)                      │             │
│  │ Exactly-once   │        │    ↓ 품질 검증                     │              │
│  └───────┬────────┘        │  Silver (정제) ← QualityChecker   │              │
│          │                 │    ↓ 비즈니스 집계                  │              │
│          ▼                 │  Gold (집계)                       │              │
│  ┌──────────────┐          │    ├── 일별 거래 요약               │              │
│  │ Kafka 집계    │          │    ├── 고객별 통계                  │              │
│  │ 토픽 + Redis  │          │    └── 수수료 정산                  │              │
│  └──────────────┘          └───────────┬──────────────────────┘              │
│                                        │                                     │
│                                        ▼                                     │
│                            ┌─────────────────────┐                           │
│                            │ Delta Lake           │                           │
│                            │ ─────────────────── │                           │
│                            │ ACID 트랜잭션        │                           │
│                            │ 타임 트래블 (감사)   │                            │
│                            │ 스키마 진화          │                            │
│                            │ MERGE (Upsert)      │                           │
│                            └─────────────────────┘                           │
│                                                                              │
│  [Serving Layer]                                                             │
│  ┌────────────┐  ┌──────────────────┐                                        │
│  │ Redis      │  │ PostgreSQL       │                                        │
│  │ 실시간 피처 │  │ 정산 리포트       │                                       │
│  │ (Flink →)  │  │ (Spark Gold →)   │                                       │
│  └────────────┘  └──────────────────┘                                        │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Lambda 아키텍처 완성

Week 4(Flink)와 Week 5(Spark)로 Lambda 아키텍처의 핵심 두 레이어가 완성되었다.

| 레이어 | 엔진 | 역할 | 완성 주차 |
|--------|------|------|----------|
| Speed Layer | Flink | 실시간 집계 + 이상거래 탐지 | Week 4 |
| Batch Layer | Spark + Delta Lake | 일별 정산 + 품질 검증 + 감사 추적 | Week 5 |
| Serving Layer | Redis + PostgreSQL | 실시간 피처 + 정산 리포트 | Week 4~5 |

## 데이터 품질 보장 체인

| 단계 | 검증 항목 | 처리 |
|------|----------|------|
| Bronze 적재 | 멱등성 (topic+partition+offset) | MERGE로 중복 방지 |
| Silver 변환 | CMP-001: 필수 필드 null | critical → 격리 |
| Silver 변환 | UNQ-001: 거래 ID 중복 | 최신 1건 유지, 나머지 격리 |
| Silver 변환 | VLD-001~004: 유효성 검증 | critical → 격리, warning → 플래그 |
| Silver 변환 | TML-001: 적시성 | warning → 플래그 |
| Gold 집계 | MERGE Upsert | 재실행 시 덮어쓰기 (멱등성) |

EOF
```

### 5-5. Git 커밋

```bash
git add .
git commit -m "Week 5: Spark 배치 ETL — 메달리온 아키텍처 + Delta Lake + 데이터 품질 검증"
```

**Day 5 완료 기준**: 전체 ETL 파이프라인(Bronze → Silver → Gold) 통합 실행 성공, 통합 검증 스크립트 통과, 배치 운영 가이드 작성, 아키텍처 문서 작성, Git 커밋.

---

## Week 5 산출물 체크리스트

| # | 산출물 | 완료 |
|---|--------|------|
| 1 | docs/spark-concepts.md (Spark 핵심 개념 정리) | ☐ |
| 2 | config/etl_config.yaml (ETL 설정 파일) | ☐ |
| 3 | config/quality_rules.yaml (데이터 품질 규칙 정의) | ☐ |
| 4 | lib/spark_session_factory.py (SparkSession 팩토리) | ☐ |
| 5 | lib/schema_registry.py (Bronze·Silver·Gold 스키마) | ☐ |
| 6 | lib/quality_checker.py (데이터 품질 검증 모듈) | ☐ |
| 7 | lib/delta_utils.py (Delta Lake 유틸리티) | ☐ |
| 8 | lib/metrics_collector.py (ETL 메트릭 수집기) | ☐ |
| 9 | jobs/kafka_batch_read_test.py (Kafka 배치 읽기 테스트) | ☐ |
| 10 | jobs/bronze_ingestion.py (Bronze 적재 — Kafka) | ☐ |
| 11 | jobs/bronze_ingestion_file.py (Bronze 적재 — 파일) | ☐ |
| 12 | jobs/silver_transformation.py (Silver 변환 + 품질 검증) | ☐ |
| 13 | jobs/gold_aggregation.py (Gold 3종 집계) | ☐ |
| 14 | jobs/full_etl_pipeline.py (전체 ETL 오케스트레이션) | ☐ |
| 15 | scripts/generate_sample_data.py (샘플 데이터 생성기) | ☐ |
| 16 | scripts/verify_bronze.py (Bronze 검증) | ☐ |
| 17 | scripts/verify_etl_pipeline.sh (통합 검증 스크립트) | ☐ |
| 18 | scripts/delta_time_travel_demo.py (타임 트래블 데모) | ☐ |
| 19 | scripts/delta_maintenance.sh (Delta 유지보수) | ☐ |
| 20 | docs/spark-operations-guide.md (배치 운영 가이드) | ☐ |
| 21 | docs/spark-architecture.md (아키텍처 문서) | ☐ |
| 22 | Git 커밋 | ☐ |

## 핵심 개념 요약

| 개념 | 요약 | 실습에서 확인한 것 |
|------|------|------------------|
| SparkSession | Spark 앱의 단일 진입점 | Delta Lake 확장 자동 활성화, PySpark API |
| DataFrame API | 분산 테이블 추상화 (SQL 호환) | filter, groupBy, agg, join, window 함수 |
| Lazy Evaluation | 액션 호출 전까지 실행하지 않음 | explain()으로 실행 계획 확인 |
| 메달리온 아키텍처 | Bronze → Silver → Gold 품질 단계 분리 | 3단계 ETL 파이프라인 구현 |
| Delta Lake | Parquet + 트랜잭션 로그 = ACID 보장 | MERGE, 타임 트래블, 스키마 진화 |
| 파티셔닝 | 디렉토리 단위 데이터 분할 | ingest_date, tx_date/tx_type 파티셔닝 |
| MERGE (Upsert) | 조건부 INSERT/UPDATE/DELETE | Gold 테이블 멱등성 보장 |
| 타임 트래블 | 과거 시점 데이터 조회 | versionAsOf, timestampAsOf 조회 |
| 데이터 품질 | 완전성·유일성·유효성·적시성 검증 | QualityChecker 모듈, YAML 규칙 기반 |
| VACUUM / OPTIMIZE | Delta 테이블 유지보수 | 오래된 파일 정리, 파일 병합 |

## Week 6 예고

Week 6에서는 RDBMS → 데이터 레이크 이관 파이프라인을 구축한다. Spark JDBC로 배치 이관(Full/Incremental)을, Debezium CDC(Change Data Capture)로 실시간 이관을 구현한다. 레거시 MySQL/PostgreSQL의 데이터를 Delta Lake로 이관하는 시나리오를 통해 기업 현장에서 가장 빈번하게 발생하는 "레거시 DB 탈출" 프로젝트의 실전 기술을 습득한다.
