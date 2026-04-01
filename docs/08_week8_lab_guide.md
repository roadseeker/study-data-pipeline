# Week 8: 통합 실습 — End-to-End 데이터 파이프라인 검증 + 최종 포트폴리오 정리

**기간**: 5일 (월~금, 풀타임 40시간)  
**주제**: 수집(NiFi·Kafka) → 실시간 처리(Flink) → 배치 ETL(Spark) → 이관(Spark JDBC·Debezium CDC) → 오케스트레이션(Airflow) 전 구간 통합 검증  
**산출물**: 통합 리허설 DAG + End-to-End 검증 스크립트 + 장애 주입/복구 리허설 보고서 + 최종 아키텍처 문서 + 포트폴리오 데모 가이드  
**전제 조건**: Week 1~7 환경 정상 기동 (`bash scripts/healthcheck-all.sh` 전체 통과), Week 7 Airflow DAG 정상 실행, Delta Lake Bronze/Silver/Gold 및 CDC 파이프라인 동작 확인

---

## 수행 시나리오

### 배경 설정

Week 7까지 페이넥스(PayNex)의 데이터 파이프라인은 계층별로 완성되었다.

- Week 1: Kafka·NiFi·Flink·Spark·Airflow·Redis·PostgreSQL 실습 환경 구성
- Week 2: Kafka 토픽 설계, 파티션 전략, 컨슈머 그룹, 복제 설정
- Week 3: NiFi 기반 API·CSV·DB 다중 소스 수집 파이프라인
- Week 4: Flink 기반 실시간 집계, 이상거래 탐지, Exactly-once 처리
- Week 5: Spark + Delta Lake 기반 Bronze·Silver·Gold 배치 ETL
- Week 6: Spark JDBC 배치 이관 + Debezium CDC 실시간 이관
- Week 7: Airflow 기반 DAG 오케스트레이션, SLA, 백필, 장애 복구

이제 페이넥스 CTO와 COO가 마지막 요구사항을 제시한다.

> "각 기술이 따로 동작하는 건 확인했습니다. 하지만 고객에게 제안하려면 **하나의 운영 시나리오로 끝까지 연결된다는 증거**가 필요합니다. 결제 API와 정산 CSV, 레거시 MySQL 변경 데이터가 들어오면, Kafka와 NiFi를 거쳐 Flink·Spark·Delta Lake·Airflow가 **운영 환경처럼 유기적으로 연결**되어야 합니다."
>
> "그리고 단순 성공 데모만으로는 부족합니다. **장애가 났을 때 어떻게 복구되는지**, **특정 날짜만 다시 돌릴 수 있는지**, **최종 리포트가 언제 만들어지는지**, **고객에게 어떤 문서로 설명할지**까지 포함해야 진짜 컨설팅 산출물입니다."

이번 주의 과제는 Week 1~7의 결과물을 하나의 End-to-End 데이터 파이프라인으로 통합하고, 고객 수용 테스트(Acceptance Test) 관점에서 성공 기준, 장애 복구, 운영 리허설, 최종 포트폴리오 정리까지 마무리하는 것이다.

### 왜 통합 실습인가? — 고객 수용 테스트의 관점

실무에서는 Kafka, NiFi, Flink, Spark, Airflow를 각각 잘 다루는 것만으로 충분하지 않다. 고객은 다음 질문에 대한 답을 원한다.

```
┌──────────────────────────────────────────────────────────────────────┐
│                고객이 실제로 확인하고 싶은 통합 질문 6가지              │
│                                                                      │
│  1. 여러 소스(API, CSV, DB, MySQL 변경 데이터)가 동시에 들어와도        │
│     파이프라인이 안정적으로 처리되는가?                                │
│                                                                      │
│  2. 실시간 탐지(Flink)와 배치 리포트(Spark)가 같은 원천 데이터를        │
│     일관성 있게 해석하는가?                                            │
│                                                                      │
│  3. 레거시 DB 변경분이 Debezium CDC를 통해 Delta Lake에                │
│     지연 없이 반영되는가?                                              │
│                                                                      │
│  4. Airflow가 이관 → ETL → 검증 → 리포트 게시 순서를                   │
│     운영 가능한 수준으로 자동화하는가?                                 │
│                                                                      │
│  5. 장애가 나면 어떤 기준으로 탐지·복구·재실행하는가?                   │
│                                                                      │
│  6. 최종적으로 고객 제안서와 포트폴리오에 넣을 수 있는                  │
│     구조도, 운영 가이드, 결과 보고서가 준비되는가?                     │
└──────────────────────────────────────────────────────────────────────┘
```

Week 8은 위 질문에 대한 "예"를 증명하는 주차다.

### 목표

1. Week 1~7 자산을 하나의 통합 운영 시나리오로 연결하고 성공 기준을 문서화한다.
2. 비즈니스 데이 리허설용 데이터 시나리오(API·CSV·Kafka·CDC)를 구성한다.
3. Airflow 기반 통합 리허설 DAG를 구현하고 End-to-End 실행 경로를 자동화한다.
4. Kafka·NiFi·Flink·Spark·Delta Lake·CDC·Airflow 전 구간의 정합성 검증 스크립트를 작성한다.
5. 장애 주입(Flink, Kafka Connect, Airflow 태스크 실패)과 복구·백필 시나리오를 검증한다.
6. 최종 아키텍처 문서, 수용 테스트 보고서, 포트폴리오 데모 가이드를 작성한다.

### 일정 개요

| 일차 | 주제 | 핵심 작업 |
|------|------|----------|
| Day 1 | 통합 요구사항 정리 + 성공 기준 수립 | 수용 테스트 범위 정의, 성공 기준 문서, 비즈니스 데이 시나리오 설계 |
| Day 2 | 통합 리허설 자동화 | 통합 리허설 스크립트, CDC 변경 시나리오, Acceptance DAG 구현 |
| Day 3 | End-to-End 실행 + 품질 검증 | 전체 파이프라인 실행, 계약 검증, KPI 요약 데이터 생성 |
| Day 4 | 장애 주입 + 복구 리허설 | Flink·CDC·Airflow 장애 주입, 복구 검증, 백필 테스트 |
| Day 5 | 최종 포트폴리오 정리 + 고객 보고서 | 최종 아키텍처 문서, 수용 테스트 보고서, 데모 시나리오, Git 커밋 |

---

## Day 1: 통합 요구사항 정리 + 성공 기준 수립

### 1-1. 통합 파이프라인 성공 기준 정의

Week 8에서는 "잘 돌아가는 것 같다" 수준이 아니라, 무엇이 성공인지 명확히 정의해야 한다.

| 구간 | 입력 | 처리 | 성공 기준 |
|------|------|------|----------|
| 수집 | API JSON / CSV / PostgreSQL / MySQL 변경분 | NiFi, Kafka Connect | 모든 소스가 Kafka 또는 Delta Lake로 유입 |
| 실시간 처리 | `paynex.events.ingested` | Flink | 5분 집계 생성, 이상거래 알림 생성, 체크포인트 정상 |
| 배치 처리 | Bronze / CDC Delta | Spark | Silver·Gold 테이블 생성, 데이터 품질 규칙 통과 |
| 이관 | MySQL 마스터/거래/정산 | Spark JDBC, Debezium | Full/Incremental/CDC 경로별 정합성 확보 |
| 오케스트레이션 | Airflow DAG | Acceptance DAG + Master DAG 순차 실행 | `paynex_acceptance_rehearsal_dag` 성공 및 `master -> migration -> etl` 완료 |
| 운영 | 장애·백필 | Airflow, Runbook | 장애 탐지, 복구, 특정 날짜 재처리 가능 |

### 1-2. 통합 프로젝트 구조

Week 8 전용 자산을 보관할 디렉토리를 만든다.

```bash
mkdir -p config/e2e
mkdir -p scripts/e2e
mkdir -p docs/final
mkdir -p dags
mkdir -p spark-etl/jobs
```

최종 구조 예시:

```text
.
├── config/
│   └── e2e/
│       └── business_day_scenario.yaml
├── scripts/
│   └── e2e/
│       ├── run_business_day_rehearsal.sh
│       ├── verify_end_to_end.sh
│       ├── run_failure_drills.sh
│       └── collect_pipeline_snapshot.sh
├── dags/
│   └── paynex_acceptance_rehearsal_dag.py
├── spark-etl/
│   └── jobs/
│       └── build_pipeline_kpis.py
└── docs/
    └── final/
        ├── acceptance-criteria.md
        ├── failure-drill-report.md
        ├── paynex-final-architecture.md
        ├── acceptance-test-report.md
        └── portfolio-demo-script.md
```

### 1-3. 비즈니스 데이 시나리오 파일 작성

통합 실습을 위해 하루치 운영 시나리오를 정의한다.

```yaml
# config/e2e/business_day_scenario.yaml
run_id: week8_acceptance_2026_04_01
business_date: 2026-04-01

sources:
  api_payments:
    event_count: 120
    interval_seconds: 0.2
  settlement_csv:
    file_count: 2
    rows_per_file: 40
  kafka_transactions:
    event_count: 200
    delay_seconds: 0.02
  mysql_cdc_changes:
    inserts: 10
    updates: 8
    deletes: 2

expectations:
  kafka_topics:
    paynex.events.ingested_min: 120
    paynex.alerts.fraud_min: 1
  delta_tables:
    bronze_transactions_min: 120
    silver_transactions_min: 120
    gold_daily_summary_min: 1
  airflow:
    required_dags:
      - paynex_daily_master
      - paynex_daily_etl
      - paynex_daily_migration
      - paynex_acceptance_rehearsal_dag
```

### 1-4. 성공 기준 문서 작성

고객과 내부 팀이 같은 기준으로 평가할 수 있도록 문서화한다.

```markdown
# docs/final/acceptance-criteria.md

## 1. 범위
- API JSON, CSV, PostgreSQL, MySQL CDC 입력 포함
- NiFi → Kafka → Flink → Delta Lake → Airflow 경로 포함
- Spark JDBC Full/Incremental 및 Debezium CDC 포함

## 2. 성공 기준
- 실시간 이벤트가 Kafka 토픽에 정상 적재
- Flink 집계 결과 및 이상거래 알림 생성
- Spark ETL이 Bronze → Silver → Gold를 완료
- Airflow DAG 전체 성공
- CDC 변경이 Delta Lake에 반영
- 특정 장애 발생 후 복구 가능

## 3. 산출물
- 최종 아키텍처 문서
- 수용 테스트 보고서
- 장애 복구 리허설 결과
- 포트폴리오 데모 스크립트
```

### 1-5. Airflow 스크립트 마운트 보강

Week 8에서는 Acceptance DAG가 `scripts/e2e` 아래의 셸 스크립트를 직접 호출하므로, Airflow 서비스에도 `scripts` 디렉토리를 마운트한다.

```yaml
  airflow-init:
    volumes:
      - ./scripts:/opt/airflow/scripts

  airflow-webserver:
    volumes:
      - ./scripts:/opt/airflow/scripts

  airflow-scheduler:
    volumes:
      - ./scripts:/opt/airflow/scripts
```

### 1-6. 사전 점검

```bash
# 전체 환경 상태 확인
bash scripts/healthcheck-all.sh

# Airflow DAG 목록 확인
docker exec lab-airflow-web airflow dags list | grep paynex

# Kafka 토픽 목록 확인
docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka-1:9092 --list

# Flink 잡 상태 확인
curl -s http://localhost:8081/jobs/overview
```

---

## Day 2: 통합 리허설 자동화

### 2-1. 비즈니스 데이 리허설 스크립트 작성

기존 주차에서 만든 스크립트를 하나의 운영 시나리오로 묶는다.

```bash
# scripts/e2e/run_business_day_rehearsal.sh
#!/usr/bin/env bash
set -euo pipefail

TARGET_DATE="${1:-2026-04-01}"

echo "[1/5] API 결제 이벤트 생성 (Docker payment-api 서비스가 이미 기동 중인지 확인)"
# payment-api 컨테이너가 Week 3에서 이미 Docker 서비스로 실행 중이므로 별도 기동 불필요.
# NiFi가 payment-api:5050 으로부터 자동 수집 중.
docker exec lab-payment-api curl -sf http://localhost:5050/health || \
  echo "⚠ payment-api 컨테이너가 실행 중이 아닙니다. docker compose up -d payment-api 를 먼저 실행하세요."

echo "[2/5] 정산 CSV 파일 생성"
python3 scripts/csv_settlement_generator.py -n 2 -r 40 -i 5

echo "[3/5] Kafka 거래 이벤트 생성"
python3 scripts/producer_paynex.py -n 200 --delay 0.02

echo "[4/5] MySQL CDC 변경 반영"
docker exec -i lab-mysql mysql -u paynex -ppaynex1234 paynex_legacy < scripts/e2e/mysql_cdc_changes.sql

echo "[5/5] Airflow 통합 DAG 실행"
docker exec lab-airflow-web airflow dags trigger paynex_acceptance_rehearsal_dag \
  --logical-date "${TARGET_DATE}T00:00:00" \
  --conf "{\"target_date\":\"${TARGET_DATE}\"}"

echo "[done] business day rehearsal finished"
```

### 2-2. CDC 변경 시나리오 SQL 작성

정산 상태 변경, 신규 입력, 삭제를 한 번에 검증한다.

```sql
-- scripts/e2e/mysql_cdc_changes.sql

-- INSERT
INSERT INTO settlements (merchant_id, settlement_date, total_amount, fee_amount, net_amount, tx_count, status)
VALUES (12, CURDATE(), 120000, 2400, 117600, 5, 'PENDING');

-- UPDATE
UPDATE settlements
SET status = 'PROCESSING', updated_at = NOW()
WHERE settlement_id = 1001;

UPDATE settlements
SET status = 'COMPLETED', updated_at = NOW()
WHERE settlement_id = 1002;

-- DELETE
DELETE FROM settlements
WHERE settlement_id = 1003;
```

### 2-3. 통합 리허설 DAG 작성

Week 7의 마스터 DAG를 재사용하되, Week 8에서는 최종 검증 태스크를 추가한다. Acceptance DAG는 수동 실행만 허용하고, 내부에서 `paynex_daily_master`를 호출해 `migration -> etl` 순서를 그대로 재사용한다.

```python
# dags/paynex_acceptance_rehearsal_dag.py
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.bash import BashOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

default_args = {
    "owner": "paynex",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="paynex_acceptance_rehearsal_dag",
    start_date=datetime(2026, 4, 1),
    schedule=None,
    catchup=False,
    default_args=default_args,
    tags=["week8", "acceptance", "integration"],
) as dag:
    start = EmptyOperator(task_id="start")

    trigger_master = TriggerDagRunOperator(
        task_id="trigger_master_dag",
        trigger_dag_id="paynex_daily_master",
        logical_date="{{ dag_run.conf.get('target_date') if dag_run and dag_run.conf else ds }}",
        conf={"target_date": "{{ dag_run.conf.get('target_date') if dag_run and dag_run.conf else ds }}"},
        wait_for_completion=True,
        poke_interval=60,
        allowed_states=["success"],
        failed_states=["failed"],
        execution_timeout=timedelta(hours=3),
    )

    verify_e2e = BashOperator(
        task_id="verify_end_to_end",
        bash_command="bash /opt/airflow/scripts/e2e/verify_end_to_end.sh {{ dag_run.conf.get('target_date') if dag_run and dag_run.conf else ds }}",
    )

    build_kpis = SparkSubmitOperator(
        task_id="build_pipeline_kpis",
        application="/opt/airflow/spark-etl/jobs/build_pipeline_kpis.py",
        packages="io.delta:delta-spark_2.12:3.1.0",
        application_args=["{{ dag_run.conf.get('target_date') if dag_run and dag_run.conf else ds }}"],
        conn_id="spark_default",
    )

    snapshot = BashOperator(
        task_id="collect_pipeline_snapshot",
        bash_command="bash /opt/airflow/scripts/e2e/collect_pipeline_snapshot.sh {{ dag_run.conf.get('target_date') if dag_run and dag_run.conf else ds }}",
    )

    end = EmptyOperator(task_id="end")

    start >> trigger_master >> verify_e2e >> build_kpis >> snapshot >> end
```

### 2-4. DAG 등록 확인

```bash
docker exec lab-airflow-web airflow dags list | grep acceptance
docker exec lab-airflow-web airflow dags show paynex_acceptance_rehearsal_dag
```

---

## Day 3: End-to-End 실행 + 품질 검증

### 3-1. End-to-End 검증 스크립트 작성

Week 8의 핵심은 "각 계층이 최종적으로 같은 결과를 보고하는가"를 확인하는 것이다.

```bash
# scripts/e2e/verify_end_to_end.sh
#!/usr/bin/env bash
set -euo pipefail

TARGET_DATE="${1:-2026-04-01}"

echo "=== 1. Kafka 토픽 데이터 확인 ==="
docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka-1:9092 --describe --topic paynex.events.ingested
docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka-1:9092 --describe --topic paynex.alerts.fraud

echo "=== 2. Airflow DAG 실행 상태 확인 ==="
docker exec lab-airflow-web airflow dags state paynex_daily_master "${TARGET_DATE}"
docker exec lab-airflow-web airflow dags state paynex_daily_migration "${TARGET_DATE}"
docker exec lab-airflow-web airflow dags state paynex_daily_etl "${TARGET_DATE}"

echo "=== 3. Delta Lake 결과 검증 ==="
docker exec -w /opt/spark-etl lab-spark-master spark-submit \
  --packages io.delta:delta-spark_2.12:3.1.0 \
  /opt/spark-etl/jobs/verify_gold_outputs.py "${TARGET_DATE}"

echo "=== 4. Flink 잡 상태 확인 ==="
curl -s http://localhost:8081/jobs/overview

echo "=== 5. CDC 커넥터 상태 확인 ==="
curl -s http://localhost:8084/connectors/paynex-mysql-cdc/status
```

### 3-2. KPI 요약 잡 작성

최종 고객 보고서에 넣을 수 있는 요약 데이터를 만든다.

```python
# spark-etl/jobs/build_pipeline_kpis.py
import sys
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, sum as spark_sum, lit

target_date = sys.argv[1]
target_month = datetime.strptime(target_date, "%Y-%m-%d").strftime("%Y-%m")

spark = (
    SparkSession.builder
    .appName("build_pipeline_kpis")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    .getOrCreate()
)

daily_summary = spark.read.format("delta").load("/data/delta/etl/gold/daily_summary")
customer_stats = spark.read.format("delta").load("/data/delta/etl/gold/customer_stats")

kpi_df = (
    daily_summary.filter(col("summary_date") == lit(target_date))
    .agg(
        count("*").alias("summary_rows"),
        spark_sum("total_amount").alias("total_amount"),
        spark_sum("anomaly_count").alias("anomaly_count")
    )
    .withColumn("summary_date", lit(target_date))
    .withColumn("stats_month", lit(target_month))
)

customer_cnt = customer_stats.filter(col("stats_month") == lit(target_month)).count()
print(f"[kpi] summary_date={target_date}, stats_month={target_month}, customer_stats_rows={customer_cnt}")
kpi_df.show(truncate=False)
```

### 3-3. 운영 상태 스냅샷 수집 스크립트

통합 리허설 직후의 핵심 상태를 한 번에 저장해 두면, 보고서 작성과 회고가 쉬워진다.

```bash
# scripts/e2e/collect_pipeline_snapshot.sh
#!/usr/bin/env bash
set -euo pipefail

TARGET_DATE="${1:-2026-04-01}"
OUT_DIR="logs/week8/${TARGET_DATE}"
mkdir -p "${OUT_DIR}"

docker compose ps > "${OUT_DIR}/docker-compose-ps.txt"
curl -s http://localhost:8081/jobs/overview > "${OUT_DIR}/flink-jobs.json"
curl -s http://localhost:8084/connectors/paynex-mysql-cdc/status > "${OUT_DIR}/cdc-status.json"
docker exec lab-airflow-web airflow dags list-runs -d paynex_acceptance_rehearsal_dag > "${OUT_DIR}/airflow-acceptance.txt"

echo "[done] pipeline snapshot saved to ${OUT_DIR}"
```

### 3-4. 통합 실행 절차

```bash
# 1. 비즈니스 데이 시나리오 실행
bash scripts/e2e/run_business_day_rehearsal.sh 2026-04-01

# 2. Acceptance DAG 상태 확인
docker exec lab-airflow-web airflow dags list-runs -d paynex_acceptance_rehearsal_dag

# 3. End-to-End 검증
bash scripts/e2e/verify_end_to_end.sh 2026-04-01
```

### 3-5. 핵심 검증 포인트

| 검증 항목 | 확인 방법 | 기대 결과 |
|-----------|----------|----------|
| API/CSV/DB 입력 유입 | NiFi 큐, Kafka 토픽 확인 | 다중 소스 이벤트가 Kafka로 유입 |
| Flink 집계 | 결과 토픽 / 로그 | 5분 집계 정상 생성 |
| 이상거래 탐지 | `paynex.alerts.fraud` | 최소 1건 이상 탐지 |
| Spark ETL | Gold 테이블 | 일별 정산 요약 생성 |
| CDC 반영 | Delta `settlements` | INSERT/UPDATE/DELETE 반영 |
| Airflow 오케스트레이션 | DAG run 상태 | 통합 DAG success |

---

## Day 4: 장애 주입 + 복구 리허설

### 4-1. 장애 주입 매트릭스

Week 8에서는 기술 데모보다 운영 복구 능력이 더 중요하다.

| 시나리오 | 장애 유형 | 기대 동작 | 검증 포인트 |
|----------|----------|----------|------------|
| A | Flink TaskManager 재기동 | 체크포인트 기반 복구 | 중복/유실 없이 집계 재개 |
| B | Debezium 커넥터 중지 | CDC 모니터링 DAG 감지 | 알림 후 재기동 가능 |
| C | Airflow ETL 태스크 실패 | 재시도 또는 수동 clear 후 재실행 | DAG 상태 정상 복구 |
| D | 특정 날짜 데이터 오류 | 백필 DAG로 재처리 | 대상 날짜만 재적재 |

### 4-2. 장애 주입 스크립트 작성

```bash
# scripts/e2e/run_failure_drills.sh
#!/usr/bin/env bash
set -euo pipefail

echo "[A] Flink TaskManager 재기동"
docker stop lab-flink-taskmanager
sleep 10
docker start lab-flink-taskmanager

echo "[B] Debezium 커넥터 일시 중지"
curl -X PUT http://localhost:8084/connectors/paynex-mysql-cdc/pause
sleep 5
curl -X PUT http://localhost:8084/connectors/paynex-mysql-cdc/resume

echo "[C] Airflow ETL 백필 DAG 실행"
docker exec lab-airflow-web airflow dags trigger paynex_backfill_recovery_dag \
  --conf '{"target_date":"2026-04-01","reason":"week8_failure_drill"}'

echo "[done] failure drills completed"
```

### 4-3. 백필 및 재처리 검증

Week 7에서 만든 `paynex_backfill_recovery_dag.py`를 실제 운영 복구 관점으로 검증한다.

```bash
# 특정 날짜 재처리
docker exec lab-airflow-web airflow dags trigger paynex_backfill_recovery_dag \
  --conf '{"target_date":"2026-04-01","mode":"reprocess"}'

# DAG 실행 결과 확인
docker exec lab-airflow-web airflow dags list-runs -d paynex_backfill_recovery_dag
```

### 4-4. 장애 복구 결과 문서화

```markdown
# docs/final/failure-drill-report.md

## 1. Flink 장애 복구
- TaskManager 재기동 후 체크포인트에서 복구 확인
- 집계 결과 중복 없음

## 2. CDC 커넥터 중단/복구
- 모니터링 DAG에서 pause 상태 감지
- resume 후 CDC 이벤트 반영 재개

## 3. Airflow 재처리
- Backfill DAG로 특정 날짜 재실행
- Gold 결과 재생성 확인

## 4. 결론
- 운영 환경 기준 최소 복구 시나리오 검증 완료
```

---

## Day 5: 최종 포트폴리오 레포 정리 + 고객 보고서

### 5-1. 최종 아키텍처 문서 작성

```markdown
# docs/final/paynex-final-architecture.md

## 1. 전체 아키텍처
API / CSV / PostgreSQL / MySQL
  -> NiFi / Spark JDBC / Debezium CDC
  -> Kafka
  -> Flink (실시간 집계, 이상거래 탐지)
  -> Delta Lake Bronze / Silver / Gold
  -> Airflow DAG 오케스트레이션
  -> 리포트 / 운영 검증 / 백필

## 2. 계층별 역할
- Kafka: 이벤트 버스
- NiFi: 다중 소스 수집
- Flink: 실시간 계산
- Spark: 배치 ETL
- Debezium: CDC
- Airflow: 운영 자동화

## 3. 운영 포인트
- SLA: 06:00 이전 Gold 리포트 완료
- 장애 복구: Backfill DAG, CDC 모니터링 DAG
- 데이터 정합성: 소스↔타겟 검증 스크립트
```

### 5-2. 수용 테스트 보고서 작성

```markdown
# docs/final/acceptance-test-report.md

## 1. 테스트 범위
- 수집, 실시간 처리, 배치 ETL, CDC, 오케스트레이션

## 2. 실행 시나리오
- business_date: 2026-04-01
- API 120건, CSV 2개 파일, Kafka 200건, CDC 변경 20건

## 3. 결과 요약
- NiFi -> Kafka 적재 성공
- Flink 집계 및 이상거래 탐지 성공
- Spark Bronze/Silver/Gold 생성 성공
- Airflow DAG 성공
- 백필 및 장애 복구 검증 성공

## 4. 남은 리스크
- 운영 환경에서는 메트릭 수집 및 알림 채널 고도화 필요
- 대용량 부하 테스트는 별도 성능 실습으로 확장 가능
```

### 5-3. 포트폴리오 데모 스크립트 작성

```markdown
# docs/final/portfolio-demo-script.md

## 데모 순서
1. 전체 아키텍처 설명 (3분)
2. API/CSV/MySQL 변경 데이터 투입 (3분)
3. Kafka / NiFi / Flink 동작 확인 (3분)
4. Airflow DAG 실행 및 Gold 리포트 생성 확인 (3분)
5. 장애 주입 후 복구 시연 (3분)
6. 최종 보고서 및 포트폴리오 구조 설명 (3분)
```

### 5-4. 최종 리허설

```bash
# 최종 통합 리허설
bash scripts/e2e/run_business_day_rehearsal.sh 2026-04-01

# 검증 스크립트
bash scripts/e2e/verify_end_to_end.sh 2026-04-01

# 장애 주입 리허설
bash scripts/e2e/run_failure_drills.sh
```

### 5-5. Git 커밋

```bash
git add .
git commit -m "feat: add week8 end-to-end integration rehearsal guide"
```

---

## Week 8 산출물 체크리스트

| # | 산출물 | 완료 |
|---|--------|------|
| 1 | `config/e2e/business_day_scenario.yaml` (통합 비즈니스 데이 시나리오) | ☐ |
| 2 | `docs/final/acceptance-criteria.md` (성공 기준 문서) | ☐ |
| 3 | `scripts/e2e/run_business_day_rehearsal.sh` (통합 리허설 실행 스크립트) | ☐ |
| 4 | `scripts/e2e/mysql_cdc_changes.sql` (CDC 변경 시나리오 SQL) | ☐ |
| 5 | `dags/paynex_acceptance_rehearsal_dag.py` (최종 수용 테스트 DAG) | ☐ |
| 6 | `scripts/e2e/verify_end_to_end.sh` (End-to-End 계약 검증 스크립트) | ☐ |
| 7 | `spark-etl/jobs/build_pipeline_kpis.py` (최종 KPI 요약 잡) | ☐ |
| 8 | `scripts/e2e/run_failure_drills.sh` (장애 주입 리허설 스크립트) | ☐ |
| 9 | `scripts/e2e/collect_pipeline_snapshot.sh` (운영 상태 스냅샷 수집) | ☐ |
| 10 | `docs/final/failure-drill-report.md` (장애 복구 리허설 보고서) | ☐ |
| 11 | `docs/final/paynex-final-architecture.md` (최종 아키텍처 문서) | ☐ |
| 12 | `docs/final/acceptance-test-report.md` (수용 테스트 결과 보고서) | ☐ |
| 13 | `docs/final/portfolio-demo-script.md` (포트폴리오 데모 스크립트) | ☐ |
| 14 | 통합 리허설 실행 로그 및 화면 캡처 | ☐ |
| 15 | Git 커밋 | ☐ |

## 핵심 개념 요약

| 개념 | 요약 | 실습에서 확인한 것 |
|------|------|------------------|
| Acceptance Test | 고객 수용 기준 기반의 최종 검증 | 수집·처리·저장·오케스트레이션 전 구간 성공 기준 정의 |
| End-to-End Validation | 입력부터 최종 산출물까지 전체 경로 검증 | API/CSV/DB/MySQL 변경분이 Gold 리포트까지 연결 |
| Contract Check | 계층 간 기대 결과 확인 | Kafka 토픽, Delta 테이블, DAG 상태 점검 |
| Reconciliation | 소스↔타겟 정합성 비교 | MySQL ↔ Delta Lake 건수 및 상태 반영 검증 |
| Failure Drill | 의도적 장애 주입 후 복구 검증 | Flink, CDC, Airflow 장애 시나리오 테스트 |
| Backfill | 과거 날짜 재처리 | `paynex_backfill_recovery_dag.py` 실제 재실행 검증 |
| Operational Readiness | 운영 준비 상태 | SLA, 알림, 복구 절차, Runbook 정리 |
| Portfolio Packaging | 고객/면접/제안용 산출물 정리 | 최종 구조도, 보고서, 데모 스크립트 작성 |

## Week 9 예고

Week 9부터는 영역 B인 ML 모델 실습으로 넘어간다. Week 8에서 완성한 데이터 파이프라인을 기반으로, 사기 거래 탐지 분류 모델을 학습하고 배포하는 흐름으로 확장할 수 있다.
