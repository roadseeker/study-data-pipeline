"""
dags/healthcheck_dag.py
전체 실습 환경 헬스체크 DAG

Airflow가 파이프라인 내 각 컴포넌트(PostgreSQL, Redis, Kafka, Flink)에
실제로 연결 가능한지 검증한다. 수동 트리거 전용.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "pipeline-lab",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="environment_healthcheck",
    default_args=default_args,
    description="전체 실습 환경 헬스체크 DAG",
    schedule_interval=None,  # 수동 트리거 전용
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["week1", "healthcheck"],
) as dag:

    check_postgres = BashOperator(
        task_id="check_postgres",
        bash_command=(
            'python -c "'
            "import psycopg2; "
            "c = psycopg2.connect("
            "host='postgres', dbname='pipeline_db', "
            "user='pipeline', password='pipeline'"
            "); "
            "print('PostgreSQL OK')"
            '"'
        ),
    )

    check_redis = BashOperator(
        task_id="check_redis",
        bash_command=(
            'python -c "'
            "import redis; "
            "r = redis.Redis(host='redis', password='redis'); "
            "print(r.ping())"
            '"'
        ),
    )

    check_kafka = BashOperator(
        task_id="check_kafka",
        bash_command=(
            'python3 -c "'
            "from confluent_kafka.admin import AdminClient; "
            "a = AdminClient({'bootstrap.servers': 'kafka:9092'}); "
            "print('Kafka brokers:', len(a.list_topics(timeout=5).brokers))"
            '"'
        ),
    )

    check_flink = BashOperator(
        task_id="check_flink",
        bash_command="curl -sf http://flink-jobmanager:8081/overview && echo 'Flink OK'",
    )

    report = BashOperator(
        task_id="generate_report",
        bash_command='echo "=== 환경 헬스체크 완료: $(date) ==="',
    )

    [check_postgres, check_redis, check_kafka, check_flink] >> report
