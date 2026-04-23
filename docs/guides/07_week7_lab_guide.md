# Week 7: 오케스트레이션 — Airflow 심화

**기간**: 5일 (월~금, 풀타임 40시간)  
**주제**: Airflow DAG 의존성 관리, 배치/스트리밍 파이프라인 오케스트레이션, SLA 모니터링, 장애 복구·알림 체계 구축  
**산출물**: Airflow DAG 모음 + 운영 알림 콜백 + 백필/복구 워크플로우 + Airflow 운영 가이드  
**전제 조건**: Week 1~6 환경 정상 기동 (`bash scripts/foundation/healthcheck-all.sh` 전체 통과), Week 5 Spark ETL 및 Week 6 Spark JDBC/CDC 파이프라인 정상 작동

---

## 수행 시나리오

### 배경 설정

Week 6까지 Nexus Pay의 배치 이관(Spark JDBC), 실시간 CDC(Debezium), 배치 ETL(Spark), 실시간 처리(Flink)가 각각 동작하게 되었다. 그러나 지금은 운영자가 Spark 작업, 정합성 검증 스크립트, CDC 상태 점검을 수동으로 실행하고 있어 장애 대응이 늦고 재실행 기준도 일관되지 않다. Nexus Pay COO가 다음 요구사항을 제시한다.

> "매일 새벽 3시 배치 이관이 자동으로 실행되고, 6시 전에 정산 리포트가 준비되어야 합니다. CDC 커넥터가 멈추거나 배치 작업이 SLA를 넘기면 운영팀이 바로 알아야 해요. 특정 날짜 데이터가 잘못 들어간 경우에는 해당 날짜만 다시 돌릴 수 있어야 합니다."
>
> "지금처럼 누가 수동으로 `spark-submit`을 치는 방식으로는 운영이 안 됩니다. DAG 의존성, 재시도, 실패 알림, 백필까지 갖춘 오케스트레이션 체계가 필요합니다."

컨설턴트로서 Apache Airflow를 활용해 Week 1~6에서 구축한 전체 파이프라인을 운영 가능한 DAG으로 연결하고, 의존성 관리·재시도·백필(backfill)·장애 알림까지 포함한 오케스트레이션 체계를 완성하는 것이 이번 주의 과제다.

### 목표

1. Airflow 핵심 개념(DAG, TaskGroup, Sensor, Trigger Rule, SLA, Backfill) 이해 및 운영 관점으로 정리
2. Week 6의 Spark JDBC 배치 이관을 일일 Airflow DAG으로 자동화
3. Week 5의 Spark ETL 파이프라인을 Airflow에서 의존성 기반으로 연결
4. Debezium/Kafka Connect 상태를 점검하는 CDC 모니터링 DAG 구축
5. 특정 날짜 재처리를 위한 백필·복구 DAG 구현
6. 실패 알림, SLA miss 감지, 운영 가이드 문서화까지 포함한 운영 체계 완성

### 일정 개요

| 일차 | 주제 | 핵심 작업 |
|------|------|----------|
| Day 1 | Airflow 심화 개념 + 환경 확장 | Airflow 운영 개념 정리, 커스텀 이미지 준비, Connections/Variables 설계 |
| Day 2 | 배치 이관 DAG 구현 | Spark JDBC Full/Incremental/정합성 검증 DAG 구성, TaskGroup·재시도·알림 적용 |
| Day 3 | Spark ETL DAG 연계 | Week 5 ETL 파이프라인 DAG화, 마스터 DAG 기반 순차 실행 구조 정리 |
| Day 4 | CDC 모니터링 + 장애 복구 | Kafka Connect 상태 점검 DAG, SLA miss 대응, 백필/복구 DAG 구현 |
| Day 5 | 통합 운영 리허설 + 문서화 | 마스터 DAG 구성, 운영 가이드/Runbook 문서화, 통합 검증, Git 커밋 |

---

## Day 1: Airflow 심화 개념 + 환경 확장

### 1-1. Airflow 운영 핵심 개념 정리

Week 1에서는 Airflow를 "기동 확인용 오케스트레이터"로만 사용했다. Week 7에서는 운영 관점에서 Airflow를 다시 정리한다.

| 개념 | 의미 | Nexus Pay 적용 예시 |
|------|------|------------------|
| DAG | 워크플로우 정의 단위 | 일일 이관 DAG, ETL DAG, CDC 모니터링 DAG |
| TaskGroup | 논리적 작업 묶음 | 마스터 테이블 Full Export 묶음 |
| Sensor | 외부 상태 대기 | 이관 DAG 완료 대기 후 ETL DAG 실행 |
| Trigger Rule | 업스트림 상태별 실행 조건 | 일부 작업 skip 시에도 알림 태스크 실행 |
| Retry | 일시 오류 자동 재시도 | Spark 일시 실패 시 2회 재시도 |
| SLA | 목표 완료 시간 | 06:00 이전 정산 리포트 완료 |
| Backfill | 과거 날짜 재실행 | 2026-03-31 데이터만 재처리 |
| Callback | 실패/성공/지연 이벤트 처리 | Slack/이메일 알림 |

### 1-2. 운영 요구사항 → Airflow 기능 매핑

| 운영 요구사항 | Airflow 기능 | 구현 방식 |
|--------------|-------------|----------|
| 매일 03:00 통합 배치 자동 실행 | Cron Schedule | `nexuspay_daily_master`를 `0 3 * * *`로 스케줄 |
| 마스터 DAG 내부에서 이관 후 ETL 순차 실행 | `TriggerDagRunOperator` | `wait_for_completion=True`로 하위 DAG를 동기 실행 |
| CDC 커넥터 이상 즉시 감지 | 주기성 모니터링 DAG | 5분 주기 상태 점검 |
| 실패 시 운영팀 알림 | Callback | `on_failure_callback` |
| 06:00 이전 리포트 완료 보장 | SLA | `sla=timedelta(hours=3)` |
| 특정 날짜 재처리 | 수동 DAG + `dag_run.conf` | Backfill DAG |

### 1-3. 오케스트레이션 프로젝트 구조

```bash
mkdir -p dags/utils plugins logs/airflow docs
mkdir -p spark-jobs/orchestration
mkdir -p scripts/airflow
```

최종 구조:

```text
.
├── dags/
│   ├── nexuspay_daily_migration_dag.py
│   ├── nexuspay_daily_etl_dag.py
│   ├── nexuspay_cdc_monitoring_dag.py
│   ├── nexuspay_backfill_recovery_dag.py
│   ├── nexuspay_daily_master_dag.py
│   └── utils/
├── plugins/
│   └── alerting.py
├── spark-etl/
│   └── jobs/
├── spark-jobs/
│   ├── migration/
│   └── orchestration/
├── scripts/
│   └── airflow/
└── docs/
    └── airflow-operations-guide.md
```

### 1-4. Airflow 커스텀 이미지 준비

Week 7부터는 SparkSubmitOperator, HTTP Provider, Slack 알림을 사용하므로 Airflow 이미지를 커스터마이징한다.

```dockerfile
cat > Dockerfile.airflow << 'DOCKERFILE'
FROM apache/airflow:2.8.4-python3.11

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-17-jre-headless curl wget procps && \
    rm -rf /var/lib/apt/lists/*

ENV SPARK_VERSION=3.5.8
RUN wget -q https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz && \
    tar -xzf spark-${SPARK_VERSION}-bin-hadoop3.tgz -C /opt && \
    ln -s /opt/spark-${SPARK_VERSION}-bin-hadoop3 /opt/spark && \
    rm spark-${SPARK_VERSION}-bin-hadoop3.tgz

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV SPARK_HOME=/opt/spark
ENV PATH=$SPARK_HOME/bin:$PATH

USER airflow
RUN pip install --no-cache-dir \
    apache-airflow-providers-apache-spark==4.8.1 \
    apache-airflow-providers-http==4.12.0 \
    apache-airflow-providers-slack==8.5.0 \
    requests==2.31.0 \
    pendulum==3.0.0
DOCKERFILE
```

### 1-5. Airflow 볼륨 생성 가이드

Week 7부터는 DAG, 플러그인, 운영 로그를 장기간 유지해야 하므로 Airflow 서비스 보강 전에 관련 경로를 먼저 준비한다. Airflow 자체 컨테이너는 bind mount 중심으로 운영하고, 메타데이터는 PostgreSQL이 영속 저장을 담당한다고 가정한다.

먼저 호스트 디렉터리를 생성한다.

```bash
mkdir -p dags/utils plugins logs/airflow docs
mkdir -p scripts/airflow
```

Airflow 서비스에는 최소 아래 볼륨을 유지한다.

```yaml
  airflow-webserver:
    volumes:
      - ./dags:/opt/airflow/dags
      - ./plugins:/opt/airflow/plugins
      - ./spark-etl:/opt/airflow/spark-etl
      - ./spark-jobs:/opt/airflow/spark-jobs
      - ./data:/data
      - ./logs/airflow:/opt/airflow/logs
```

적용 시점:
- Day 1 Airflow 환경 확장 전에 반영
- 운영 로그는 `logs/airflow`에서 누적 관리
- 별도 Airflow 전용 메타DB를 도입할 때만 추가 named volume을 검토

### 1-6. docker-compose.yml의 Airflow 서비스 보강

기존 Week 1 Airflow 서비스를 아래와 같이 보강한다.

```yaml
  airflow-init:
    build:
      context: .
      dockerfile: Dockerfile.airflow
    image: nexuspay-airflow:week7
    container_name: lab-airflow-init
    entrypoint: >
      bash -c "
        airflow db init &&
        airflow users create
          --username ${AIRFLOW_ADMIN_USERNAME}
          --password ${AIRFLOW_ADMIN_PASSWORD}
          --firstname Admin
          --lastname User
          --role Admin
          --email admin@pipeline-lab.local &&
        airflow connections add spark_default
          --conn-type spark
          --conn-host spark://spark-master
          --conn-port 7077 &&
        airflow connections add kafka_connect_api
          --conn-type http
          --conn-host kafka-connect
          --conn-port 8083
          --conn-schema http &&
        airflow variables set nexuspay_alert_email ops@nexuspay.local &&
        airflow variables set nexuspay_slack_webhook http://mock-webhook.local/slack
      "
    volumes:
      - ./dags:/opt/airflow/dags
      - ./plugins:/opt/airflow/plugins
      - ./spark-etl:/opt/airflow/spark-etl
      - ./spark-jobs:/opt/airflow/spark-jobs
      - ./data:/data
      - ./logs/airflow:/opt/airflow/logs

  airflow-webserver:
    build:
      context: .
      dockerfile: Dockerfile.airflow
    image: nexuspay-airflow:week7
    container_name: lab-airflow-web
    command: airflow webserver --port 8083
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: ${AIRFLOW__DATABASE__SQL_ALCHEMY_CONN}
      AIRFLOW__CORE__FERNET_KEY: ${AIRFLOW__CORE__FERNET_KEY}
      AIRFLOW__CORE__EXECUTOR: ${AIRFLOW__CORE__EXECUTOR}
      AIRFLOW__CORE__LOAD_EXAMPLES: ${AIRFLOW__CORE__LOAD_EXAMPLES}
      AIRFLOW__WEBSERVER__SECRET_KEY: ${AIRFLOW__WEBSERVER__SECRET_KEY}
    ports:
      - "8083:8083"
    volumes:
      - ./dags:/opt/airflow/dags
      - ./plugins:/opt/airflow/plugins
      - ./spark-etl:/opt/airflow/spark-etl
      - ./spark-jobs:/opt/airflow/spark-jobs
      - ./data:/data
      - ./logs/airflow:/opt/airflow/logs
    depends_on:
      airflow-init:
        condition: service_completed_successfully
    healthcheck:
      test: ["CMD", "curl", "-sf", "http://localhost:8083/health"]
      interval: 30s
      timeout: 10s
      retries: 15
      start_period: 30s

  airflow-scheduler:
    build:
      context: .
      dockerfile: Dockerfile.airflow
    image: nexuspay-airflow:week7
    container_name: lab-airflow-sched
    command: airflow scheduler
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: ${AIRFLOW__DATABASE__SQL_ALCHEMY_CONN}
      AIRFLOW__CORE__FERNET_KEY: ${AIRFLOW__CORE__FERNET_KEY}
      AIRFLOW__CORE__EXECUTOR: ${AIRFLOW__CORE__EXECUTOR}
      AIRFLOW__CORE__LOAD_EXAMPLES: ${AIRFLOW__CORE__LOAD_EXAMPLES}
    volumes:
      - ./dags:/opt/airflow/dags
      - ./plugins:/opt/airflow/plugins
      - ./spark-etl:/opt/airflow/spark-etl
      - ./spark-jobs:/opt/airflow/spark-jobs
      - ./data:/data
      - ./logs/airflow:/opt/airflow/logs
    depends_on:
      airflow-init:
        condition: service_completed_successfully
```

### 1-6. Airflow 기동 및 연결 확인

```bash
docker compose build airflow-init airflow-webserver airflow-scheduler
docker compose up -d airflow-init
docker compose up -d airflow-webserver airflow-scheduler

curl -sf http://localhost:8083/health | python3 -m json.tool
docker exec lab-airflow-web airflow connections get spark_default
docker exec lab-airflow-web airflow connections get kafka_connect_api
docker exec lab-airflow-web airflow variables get nexuspay_alert_email
```

**Day 1 완료 기준**: Airflow 커스텀 이미지 빌드 완료, Web UI 접속 성공, `spark_default`/`kafka_connect_api` 연결 확인, 운영 요구사항과 Airflow 기능 매핑 정리 완료.

---

## Day 2: 배치 이관 DAG 구현

### 2-1. 일일 이관 DAG 설계

Day 2의 목표는 Week 6 수동 명령을 DAG으로 바꾸는 것이다.

```text
start
  └─ precheck
      └─ master_full_refresh
           ├─ customers full export
           └─ merchants full export
      └─ transactions_incremental
      └─ verify_migration
      └─ notify_success
end
```

### 2-2. 공통 알림 콜백 플러그인

```python
cat > plugins/alerting.py << 'PYEOF'
import json
import requests
from airflow.models import Variable


def _post_webhook(payload):
    webhook = Variable.get("nexuspay_slack_webhook", default_var="")
    if not webhook:
        print("[alert] webhook not configured")
        print(json.dumps(payload, ensure_ascii=False))
        return
    try:
        requests.post(webhook, json=payload, timeout=5)
    except Exception as exc:
        print(f"[alert] webhook send failed: {exc}")


def task_failure_alert(context):
    ti = context["task_instance"]
    payload = {
        "text": f"[Nexus Pay Airflow] FAILED - {ti.dag_id}.{ti.task_id} ({context['ds']})"
    }
    _post_webhook(payload)


def task_success_alert(context):
    ti = context["task_instance"]
    payload = {
        "text": f"[Nexus Pay Airflow] SUCCESS - {ti.dag_id}.{ti.task_id} ({context['ds']})"
    }
    _post_webhook(payload)


def sla_miss_alert(dag, task_list, blocking_task_list, slas, blocking_tis):
    payload = {
        "text": f"[Nexus Pay Airflow] SLA MISS - {dag.dag_id} / tasks={task_list}"
    }
    _post_webhook(payload)
PYEOF
```

### 2-3. 마스터 테이블 Full Export 래퍼 스크립트

Week 6의 `jdbc_full_export.py`는 여러 테이블을 한 번에 적재하므로, Airflow에서는 테이블별 태스크로 쪼개기 위해 래퍼 스크립트를 둔다.

```python
cat > spark-jobs/orchestration/master_refresh.py << 'PYEOF'
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, lit
from datetime import datetime
import argparse

JDBC_URL = "jdbc:mysql://mysql:3306/nexuspay_legacy"
JDBC_PROPS = {
    "user": "nexuspay",
    "password": "nexuspay1234",
    "driver": "com.mysql.cj.jdbc.Driver",
}
MIGRATION_ROOT = "/data/delta/migration"


def create_spark():
    return SparkSession.builder \
        .appName("nexuspay-Master-Refresh") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()


def run(table_name, partition_column, num_partitions):
    spark = create_spark()
    bounds = spark.read.jdbc(
        url=JDBC_URL,
        table=f"(SELECT MIN({partition_column}) AS min_val, MAX({partition_column}) AS max_val FROM {table_name}) t",
        properties=JDBC_PROPS,
    ).first()

    df = spark.read.jdbc(
        url=JDBC_URL,
        table=table_name,
        column=partition_column,
        lowerBound=int(bounds["min_val"]),
        upperBound=int(bounds["max_val"]),
        numPartitions=num_partitions,
        properties=JDBC_PROPS,
    )

    df = df.withColumn("_ingested_at", current_timestamp()) \
           .withColumn("_source", lit("mysql.nexuspay_legacy")) \
           .withColumn("_migration_type", lit("airflow_master_refresh")) \
           .withColumn("_batch_id", lit(datetime.now().strftime("%Y%m%d_%H%M%S")))

    df.write.format("delta").mode("overwrite").option("overwriteSchema", "true") \
        .save(f"{MIGRATION_ROOT}/{table_name}")
    spark.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", required=True)
    parser.add_argument("--partition-column", required=True)
    parser.add_argument("--num-partitions", type=int, default=1)
    args = parser.parse_args()
    run(args.table, args.partition_column, args.num_partitions)
PYEOF
```

### 2-4. `nexuspay_daily_migration_dag.py`

```python
cat > dags/nexuspay_daily_migration_dag.py << 'PYEOF'
from datetime import timedelta
from pendulum import datetime

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

from alerting import task_failure_alert, task_success_alert, sla_miss_alert

SPARK_PACKAGES = (
    "io.delta:delta-spark_2.12:3.1.0,"
    "mysql:mysql-connector-java:8.0.33"
)

default_args = {
    "owner": "nexuspay-data-platform",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": task_failure_alert,
}

with DAG(
    dag_id="nexuspay_daily_migration",
    start_date=datetime(2026, 4, 1, tz="Asia/Seoul"),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    dagrun_timeout=timedelta(hours=2),
    sla_miss_callback=sla_miss_alert,
    tags=["nexuspay", "week7", "migration"],
) as dag:
    start = EmptyOperator(task_id="start")

    precheck = BashOperator(
        task_id="precheck_airflow_runtime",
        bash_command="echo 'Airflow migration DAG started for {{ ds }}'",
    )

    with TaskGroup(group_id="master_full_refresh") as master_full_refresh:
        refresh_customers = SparkSubmitOperator(
            task_id="refresh_customers",
            conn_id="spark_default",
            application="/opt/airflow/spark-jobs/orchestration/master_refresh.py",
            packages=SPARK_PACKAGES,
            application_args=[
                "--table", "customers",
                "--partition-column", "customer_id",
                "--num-partitions", "2",
            ],
        )

        refresh_merchants = SparkSubmitOperator(
            task_id="refresh_merchants",
            conn_id="spark_default",
            application="/opt/airflow/spark-jobs/orchestration/master_refresh.py",
            packages=SPARK_PACKAGES,
            application_args=[
                "--table", "merchants",
                "--partition-column", "merchant_id",
                "--num-partitions", "1",
            ],
        )

    incremental_transactions = SparkSubmitOperator(
        task_id="incremental_transactions",
        conn_id="spark_default",
        application="/opt/airflow/spark-jobs/migration/jdbc_incremental.py",
        packages=SPARK_PACKAGES,
        sla=timedelta(hours=1),
    )

    verify_migration = SparkSubmitOperator(
        task_id="verify_migration",
        conn_id="spark_default",
        application="/opt/airflow/spark-jobs/migration/verify_migration.py",
        packages=SPARK_PACKAGES,
    )

    notify_success = BashOperator(
        task_id="notify_success",
        bash_command="echo '[Nexus Pay] daily migration finished for {{ ds }}'",
        on_success_callback=task_success_alert,
        trigger_rule="all_success",
    )

    end = EmptyOperator(task_id="end")

    start >> precheck >> master_full_refresh >> incremental_transactions >> verify_migration >> notify_success >> end
PYEOF
```

### 2-5. DAG 등록 확인 및 실행

```bash
docker exec lab-airflow-web airflow dags list
docker exec lab-airflow-web airflow dags test nexuspay_daily_migration 2026-04-01
```

**Day 2 완료 기준**: `nexuspay_daily_migration` DAG 등록 성공, TaskGroup 시각화 확인, `SparkSubmitOperator` 기반 Full/Incremental/검증 흐름 실행 확인.

---

## Day 3: Spark ETL DAG 연계

### 3-1. ETL DAG 설계

Week 5의 Spark ETL은 `/data/delta/etl` 루트의 Delta Lake를 기준으로 동작하고, Week 6의 이관 DAG는 `/data/delta/migration` 아래의 마스터·CDC 데이터를 갱신한다. 운영 흐름에서는 마스터 DAG가 "migration 완료 → ETL 실행" 순서를 보장하므로, `nexuspay_daily_etl`은 독립 실행 가능한 수동 DAG로 두고 일일 스케줄은 마스터 DAG 한 곳에만 둔다.

```text
nexuspay_daily_master
         ↓
trigger nexuspay_daily_migration (wait_for_completion=True)
         ↓
trigger nexuspay_daily_etl (wait_for_completion=True)
         ↓
run_full_etl_pipeline
         ↓
publish_gold_report
         ↓
verify_gold_outputs
```

### 3-2. Gold 결과 적재 래퍼 스크립트

```python
cat > spark-etl/jobs/publish_gold_report.py << 'PYEOF'
from pyspark.sql import SparkSession
import pyspark.sql.functions as F
from datetime import date, timedelta
import sys


def create_spark():
    return SparkSession.builder \
        .appName("nexuspay-Publish-Gold-Report") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()


if __name__ == "__main__":
    target_date = sys.argv[1] if len(sys.argv) > 1 else str(date.today() - timedelta(days=1))
    spark = create_spark()
    df = spark.read.format("delta").load("/data/delta/etl/gold/daily_summary")
    report_df = df.filter(F.col("summary_date") == F.lit(target_date))
    print(f"[publish_gold_report] target_date={target_date}, rows={report_df.count()}")
    report_df.show(20, truncate=False)
    spark.stop()
PYEOF
```

```python
cat > spark-etl/jobs/verify_gold_outputs.py << 'PYEOF'
from pyspark.sql import SparkSession


def create_spark():
    return SparkSession.builder \
        .appName("nexuspay-Verify-Gold-Outputs") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()


if __name__ == "__main__":
    spark = create_spark()
    daily = spark.read.format("delta").load("/data/delta/etl/gold/daily_summary").count()
    customer = spark.read.format("delta").load("/data/delta/etl/gold/customer_stats").count()
    print(f"[verify_gold_outputs] daily_summary={daily}, customer_stats={customer}")
    if daily == 0 or customer == 0:
        raise ValueError("Gold outputs are empty")
    spark.stop()
PYEOF
```

### 3-3. `nexuspay_daily_etl_dag.py`

```python
cat > dags/nexuspay_daily_etl_dag.py << 'PYEOF'
from datetime import timedelta
from pendulum import datetime

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

from alerting import task_failure_alert, sla_miss_alert

SPARK_PACKAGES = "io.delta:delta-spark_2.12:3.1.0,mysql:mysql-connector-java:8.0.33"

with DAG(
    dag_id="nexuspay_daily_etl",
    start_date=datetime(2026, 4, 1, tz="Asia/Seoul"),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "nexuspay-data-platform",
        "retries": 1,
        "retry_delay": timedelta(minutes=10),
        "on_failure_callback": task_failure_alert,
    },
    sla_miss_callback=sla_miss_alert,
    tags=["nexuspay", "week7", "etl"],
) as dag:
    start = EmptyOperator(task_id="start")

    run_full_etl = SparkSubmitOperator(
        task_id="run_full_etl_pipeline",
        conn_id="spark_default",
        application="/opt/airflow/spark-etl/jobs/full_etl_pipeline.py",
        packages=SPARK_PACKAGES,
        py_files="/opt/airflow/spark-etl/lib/spark_session_factory.py,/opt/airflow/spark-etl/lib/quality_engine.py",
        application_args=["{{ dag_run.conf.get('target_date') if dag_run and dag_run.conf else ds }}"],
        sla=timedelta(hours=2),
    )

    publish_gold_report = SparkSubmitOperator(
        task_id="publish_gold_report",
        conn_id="spark_default",
        application="/opt/airflow/spark-etl/jobs/publish_gold_report.py",
        packages=SPARK_PACKAGES,
        py_files="/opt/airflow/spark-etl/lib/spark_session_factory.py,/opt/airflow/spark-etl/lib/quality_engine.py",
        application_args=["{{ dag_run.conf.get('target_date') if dag_run and dag_run.conf else ds }}"],
    )

    verify_gold_outputs = SparkSubmitOperator(
        task_id="verify_gold_outputs",
        conn_id="spark_default",
        application="/opt/airflow/spark-etl/jobs/verify_gold_outputs.py",
        packages=SPARK_PACKAGES,
        py_files="/opt/airflow/spark-etl/lib/spark_session_factory.py,/opt/airflow/spark-etl/lib/quality_engine.py",
    )

    end = EmptyOperator(task_id="end")

    start >> run_full_etl >> publish_gold_report >> verify_gold_outputs >> end
PYEOF
```

### 3-4. DAG 실행 확인

```bash
docker exec lab-airflow-web airflow dags list
docker exec lab-airflow-web airflow dags test nexuspay_daily_etl 2026-04-01
```

**Day 3 완료 기준**: `nexuspay_daily_etl` DAG 등록 성공, `/data/delta/etl` 경로 기준 Gold 산출물 읽기 확인, Week 5 ETL 파이프라인이 Airflow 태스크로 호출되는 것 확인.

---

## Day 4: CDC 모니터링 + 장애 복구

### 4-1. `nexuspay_cdc_monitoring_dag.py`

CDC는 배치와 다르게 "작업 실행"보다 "상태 감시"가 핵심이다. Kafka Connect REST API를 조회해 Debezium 커넥터 상태를 점검한다.

```python
cat > dags/nexuspay_cdc_monitoring_dag.py << 'PYEOF'
from datetime import timedelta
from pendulum import datetime

from airflow import DAG
from airflow.decorators import task
from airflow.providers.http.operators.http import HttpOperator

from alerting import task_failure_alert, task_success_alert

with DAG(
    dag_id="nexuspay_cdc_monitoring",
    start_date=datetime(2026, 4, 1, tz="Asia/Seoul"),
    schedule="*/5 * * * *",
    catchup=False,
    default_args={
        "owner": "nexuspay-ops",
        "retries": 1,
        "retry_delay": timedelta(minutes=2),
        "on_failure_callback": task_failure_alert,
    },
    tags=["nexuspay", "week7", "cdc", "monitoring"],
) as dag:
    fetch_connector_status = HttpOperator(
        task_id="fetch_connector_status",
        http_conn_id="kafka_connect_api",
        endpoint="/connectors/nexuspay-mysql-cdc/status",
        method="GET",
        log_response=True,
    )

    @task(on_success_callback=task_success_alert)
    def evaluate_status(response_text: str):
        import json
        payload = json.loads(response_text)
        connector_state = payload["connector"]["state"]
        task_states = [task["state"] for task in payload["tasks"]]
        print(f"connector_state={connector_state}, task_states={task_states}")
        if connector_state != "RUNNING" or any(state != "RUNNING" for state in task_states):
            raise ValueError(f"CDC connector unhealthy: {payload}")
        return payload

    evaluate_status(fetch_connector_status.output)
PYEOF
```

### 4-2. 백필/복구 DAG

```python
cat > dags/nexuspay_backfill_recovery_dag.py << 'PYEOF'
from datetime import timedelta
from pendulum import datetime

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

from alerting import task_failure_alert

SPARK_PACKAGES = "io.delta:delta-spark_2.12:3.1.0,mysql:mysql-connector-java:8.0.33"

with DAG(
    dag_id="nexuspay_backfill_recovery",
    start_date=datetime(2026, 4, 1, tz="Asia/Seoul"),
    schedule=None,
    catchup=False,
    default_args={
        "owner": "nexuspay-ops",
        "retries": 0,
        "on_failure_callback": task_failure_alert,
    },
    params={"target_date": "2026-04-01"},
    tags=["nexuspay", "week7", "backfill"],
) as dag:
    start = EmptyOperator(task_id="start")

    rerun_incremental = SparkSubmitOperator(
        task_id="rerun_incremental",
        conn_id="spark_default",
        application="/opt/airflow/spark-jobs/migration/jdbc_incremental.py",
        packages=SPARK_PACKAGES,
    )

    rerun_etl = SparkSubmitOperator(
        task_id="rerun_etl",
        conn_id="spark_default",
        application="/opt/airflow/spark-etl/jobs/full_etl_pipeline.py",
        packages=SPARK_PACKAGES,
        py_files="/opt/airflow/spark-etl/lib/spark_session_factory.py,/opt/airflow/spark-etl/lib/quality_engine.py",
        application_args=["{{ dag_run.conf.get('target_date') if dag_run and dag_run.conf else ds }}"],
    )

    rerun_verification = SparkSubmitOperator(
        task_id="rerun_verification",
        conn_id="spark_default",
        application="/opt/airflow/spark-jobs/migration/verify_migration.py",
        packages=SPARK_PACKAGES,
    )

    end = EmptyOperator(task_id="end")

    start >> rerun_incremental >> rerun_etl >> rerun_verification >> end
PYEOF
```

### 4-3. 장애 복구 실습

```bash
# 1. CDC 상태 점검 DAG 테스트
docker exec lab-airflow-web airflow dags test nexuspay_cdc_monitoring 2026-04-01

# 2. 특정 날짜 백필
docker exec lab-airflow-web airflow dags trigger nexuspay_backfill_recovery \
  --conf '{"target_date":"2026-03-31"}'
```

> **운영 포인트**:
> - CDC 모니터링 DAG는 `catchup=False`로 두고 "현재 상태"만 감시한다.
> - 백필 DAG는 `schedule=None`으로 두고 운영자가 필요 시에만 수동 실행한다.
> - Backfill은 "원인 분석 → 대상 날짜 지정 → 재처리 → 검증" 순서를 따라야 한다.

**Day 4 완료 기준**: CDC 모니터링 DAG 등록 및 상태 판별 성공, 백필 DAG 수동 실행 성공, 특정 날짜 재처리 흐름 확인.

---

## Day 5: 통합 운영 리허설 + 운영 가이드 문서화

### 5-1. 마스터 오케스트레이션 DAG

Day 2~4에 만든 DAG를 "운영 진입점" 하나로 연결한다.

```python
cat > dags/nexuspay_daily_master_dag.py << 'PYEOF'
from datetime import timedelta
from pendulum import datetime

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

with DAG(
    dag_id="nexuspay_daily_master",
    start_date=datetime(2026, 4, 1, tz="Asia/Seoul"),
    schedule="0 3 * * *",
    catchup=False,
    max_active_runs=1,
    default_args={"owner": "nexuspay-ops", "retries": 0},
    tags=["nexuspay", "week7", "master"],
) as dag:
    start = EmptyOperator(task_id="start")

    trigger_migration = TriggerDagRunOperator(
        task_id="trigger_migration",
        trigger_dag_id="nexuspay_daily_migration",
        wait_for_completion=True,
        logical_date="{{ ds }}",
        conf={"target_date": "{{ ds }}"},
        poke_interval=60,
        allowed_states=["success"],
        failed_states=["failed"],
        execution_timeout=timedelta(hours=2),
    )

    trigger_etl = TriggerDagRunOperator(
        task_id="trigger_etl",
        trigger_dag_id="nexuspay_daily_etl",
        wait_for_completion=True,
        logical_date="{{ ds }}",
        conf={"target_date": "{{ ds }}"},
        poke_interval=60,
        allowed_states=["success"],
        failed_states=["failed"],
        execution_timeout=timedelta(hours=3),
    )

    end = EmptyOperator(task_id="end")

    start >> trigger_migration >> trigger_etl >> end
PYEOF
```

### 5-2. Airflow 운영 가이드 문서

```bash
cat > docs/airflow-operations-guide.md << 'EOF'
# Nexus Pay Airflow 운영 가이드

## 1. DAG 구성

| DAG | 스케줄 | 역할 |
|-----|--------|------|
| nexuspay_daily_master | 03:00 | 일일 통합 오케스트레이션 진입점 |
| nexuspay_daily_migration | 수동 / master 트리거 | Spark JDBC 배치 이관 + 검증 |
| nexuspay_daily_etl | 수동 / master 트리거 | Spark ETL + Gold 리포트 생성 |
| nexuspay_cdc_monitoring | 5분 주기 | Debezium/Kafka Connect 상태 감시 |
| nexuspay_backfill_recovery | 수동 | 특정 날짜 재처리 |

## 2. 일일 운영 체크리스트

1. 03:10 이전 `nexuspay_daily_master` 실행 여부 확인
2. 04:00 이전 `nexuspay_daily_migration` 성공 여부 확인
3. 06:00 이전 `nexuspay_daily_etl` 완료 여부 확인
4. `nexuspay_cdc_monitoring` 최근 1시간 실패 횟수 확인
5. Slack/이메일 알림 수신 여부 확인

## 3. 장애 대응

### Spark 작업 실패
1. 실패 태스크의 로그에서 Spark 예외 확인
2. 소스 DB/Delta 경로/패키지 의존성 확인
3. 실패 태스크만 Clear 후 재실행

### CDC 커넥터 실패
1. Kafka Connect REST API에서 상태 확인
2. Debezium 오프셋/스냅샷 모드 점검
3. 필요 시 커넥터 재시작 후 모니터링 DAG 재확인

### 특정 날짜 재처리
1. `nexuspay_backfill_recovery` DAG 실행
2. `target_date` 지정
3. 재처리 후 검증 로그 확인

## 4. SLA 기준

| 업무 | SLA |
|------|-----|
| 일일 배치 이관 완료 | 04:00 |
| ETL + 리포트 완료 | 06:00 |
| CDC 장애 감지 | 5분 이내 |

EOF
```

### 5-3. 통합 운영 리허설

```bash
# DAG 등록 확인
docker exec lab-airflow-web airflow dags list

# 통합 DAG 테스트
docker exec lab-airflow-web airflow dags test nexuspay_daily_master 2026-04-01

# 헬스체크
curl -sf http://localhost:8083/health | python3 -m json.tool
```

### 5-4. Git 커밋

```bash
git add .
git commit -m "Week 7: Airflow orchestration, monitoring, and recovery workflows"
```

**Day 5 완료 기준**: 마스터 DAG 등록 성공, 일일 배치/ETL/CDC 모니터링 DAG 연결 확인, 운영 가이드 문서 작성, Git 커밋 준비 완료.

---

## Week 7 산출물 체크리스트

| # | 산출물 | 완료 |
|---|--------|------|
| 1 | Dockerfile.airflow (Airflow 커스텀 이미지) | ☐ |
| 2 | docker-compose.yml Airflow 보강 | ☐ |
| 3 | plugins/alerting.py (실패·SLA 알림 콜백) | ☐ |
| 4 | spark-jobs/orchestration/master_refresh.py (마스터 Full Export 래퍼) | ☐ |
| 5 | dags/nexuspay_daily_migration_dag.py (일일 배치 이관 DAG) | ☐ |
| 6 | dags/nexuspay_daily_etl_dag.py (배치 ETL DAG) | ☐ |
| 7 | spark-etl/jobs/publish_gold_report.py (Gold 리포트 게시) | ☐ |
| 8 | spark-etl/jobs/verify_gold_outputs.py (Gold 출력 검증) | ☐ |
| 9 | dags/nexuspay_cdc_monitoring_dag.py (CDC 상태 점검 DAG) | ☐ |
| 10 | dags/nexuspay_backfill_recovery_dag.py (백필/복구 DAG) | ☐ |
| 11 | dags/nexuspay_daily_master_dag.py (통합 마스터 DAG) | ☐ |
| 12 | docs/airflow-operations-guide.md (운영 가이드) | ☐ |
| 13 | 통합 DAG 실행 로그 및 캡처 | ☐ |
| 14 | Git 커밋 | ☐ |

## 핵심 개념 요약

| 개념 | 요약 | 실습에서 확인한 것 |
|------|------|------------------|
| DAG | 작업 흐름 정의 단위 | migration / etl / monitoring / master DAG 구성 |
| TaskGroup | 관련 태스크 논리 그룹 | customers·merchants Full Export 묶음 |
| SparkSubmitOperator | Spark 작업 제출용 연산자 | JDBC 이관·ETL·검증 작업 실행 |
| TriggerDagRunOperator | 다른 DAG 실행 및 완료 대기 | master DAG에서 migration / etl 순차 실행 |
| Callback | 실패/성공/SLA 이벤트 후처리 | Slack/이메일 알림 템플릿 |
| SLA | 작업 완료 목표 시간 | ETL 06:00 이전 완료 요구 |
| Backfill | 과거 날짜 재처리 | 특정 `target_date` 수동 재실행 |
| 단일 스케줄 구조 | 마스터 DAG만 정기 실행 | child DAG 중복 실행 방지 |
| CDC Monitoring | 커넥터 상태 감시 | Kafka Connect REST API 점검 |

## Week 8 예고

Week 8에서는 Week 1~7에서 구축한 모든 계층을 통합 검증한다. Kafka·NiFi·Flink·Spark·Spark JDBC·Debezium·Airflow를 하나의 시나리오로 연결하여, 수집 → 변환 → 저장 → 이관 → 오케스트레이션의 전체 데이터 파이프라인을 실제 운영 관점에서 리허설하고 최종 포트폴리오 레포 형태로 정리한다.
