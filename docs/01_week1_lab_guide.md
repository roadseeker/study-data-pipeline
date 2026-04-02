# Week 1: 데이터 파이프라인 실습 환경 구성

**기간**: 5일 (월~금, 풀타임 40시간)
**주제**: Docker Compose 전체 스택 기동·검증
**산출물**: 로컬 실습 환경 + 컴포넌트별 헬스체크 완료 + 통합 연동 검증

---

## 수행 시나리오

### 배경 설정

가상의 중견 핀테크 기업 **"페이넥스(PayNex)"** 가 데이터 파이프라인 현대화를 검토 중이다. 컨설턴트로서 PoC(Proof of Concept) 환경을 로컬에 구축하여 전체 Apache 오픈소스 스택이 정상적으로 작동하는지 검증해야 한다. 이 환경은 이후 8주간의 모든 실습의 기반이 된다.

### 목표

1. 7개 핵심 컴포넌트를 Docker Compose로 단일 명령 기동
2. 각 컴포넌트별 독립 헬스체크로 정상 작동 확인
3. 컴포넌트 간 기본 연동 검증 (데이터가 흐르는지 확인)
4. 장애 시나리오 테스트 (컨테이너 중단 → 복구)
5. 실습 환경 문서화 (README + 아키텍처 다이어그램)

### 일정 개요

| 일차 | 주제 | 핵심 작업 |
|------|------|----------|
| Day 1 | 프로젝트 구조 설계 + 기반 서비스 기동 | 디렉토리 구성, PostgreSQL·Redis 기동·검증 |
| Day 2 | 메시징·수집 계층 구성 | Kafka(KRaft)·NiFi 기동·검증 |
| Day 3 | 처리·오케스트레이션 계층 구성 | Flink·Spark·Airflow 기동·검증 |
| Day 4 | 전체 스택 통합 기동 + 연동 검증 | 7개 컴포넌트 동시 기동, 데이터 흐름 검증 |
| Day 5 | 장애 테스트 + 문서화 | 장애 복구 시나리오, README 작성 |

---

## Day 1: 프로젝트 구조 설계 + 기반 서비스 기동

### 1-1. 프로젝트 디렉토리 구조 생성

```bash
mkdir -p pipeline-lab/{config/{kafka,nifi,flink,spark,airflow},dags,docs,scripts,spark-etl/{jobs,lib,scripts},spark-jobs/{migration,orchestration},flink-jobs,data/{sample,delta,settlement}}
cd pipeline-lab
```

최종 디렉토리 구조:

```
pipeline-lab/
├── docker-compose.yml          # 전체 스택 정의
├── .env                        # 환경 변수
├── config/
│   ├── kafka/                  # Kafka 설정
│   ├── nifi/                   # NiFi 설정
│   ├── flink/                  # Flink 설정
│   ├── spark/                  # Spark 설정
│   └── airflow/                # Airflow 설정
├── dags/                       # Airflow DAG 파일
├── docs/                       # Week 3~4 개념 문서
├── scripts/                    # 헬스체크·검증 스크립트
├── spark-etl/                  # Week 5 배치 ETL 코드
├── spark-jobs/                 # Week 6~7 이관·오케스트레이션 코드
├── flink-jobs/                 # Week 4 Flink 스트림 처리 코드
├── data/
│   ├── sample/                 # 샘플 데이터
│   ├── settlement/             # Week 3 정산 CSV 파일
│   └── delta/                  # Week 5~7 공용 Delta Lake 저장소
└── README.md
```

### 1-2. 환경 변수 파일 생성

```bash
# .env
cat > .env << 'EOF'
# === 공통 ===
COMPOSE_PROJECT_NAME=pipeline-lab

# === PostgreSQL ===
POSTGRES_USER=pipeline
POSTGRES_PASSWORD=pipeline
POSTGRES_DB=pipeline_db

# === Redis ===
REDIS_PASSWORD=redis

# === NiFi ===
NIFI_USERNAME=admin
NIFI_PASSWORD=nifi

# === Airflow ===
AIRFLOW_ADMIN_USERNAME=admin
AIRFLOW_ADMIN_PASSWORD=airflow
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://pipeline:pipeline@postgres:5432/airflow_db
AIRFLOW__CORE__FERNET_KEY=46BKJoQYlPPOexq0OhDZnIlNepKFf87WFwLbfzqDDho=
AIRFLOW__CORE__LOAD_EXAMPLES=false
AIRFLOW__WEBSERVER__SECRET_KEY=airflow-secret-key-2026
EOF
```

### 1-3. Docker Compose — 기반 서비스 (PostgreSQL + Redis)

먼저 기반 서비스만 정의하고 기동하여 안정성을 확인한다.

```yaml
# docker-compose.yml (Day 1 — 기반 서비스)
version: "3.9"

networks:
  pipeline-net:
    driver: bridge

volumes:
  postgres-data:
  redis-data:

services:
  # ──────────────────────────────────────
  # PostgreSQL — 메타데이터 저장소
  # ──────────────────────────────────────
  postgres:
    image: postgres:16-alpine
    container_name: lab-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/01-init-db.sql
      - ./scripts/init-customers.sql:/docker-entrypoint-initdb.d/02-init-customers.sql
    networks:
      - pipeline-net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ──────────────────────────────────────
  # Redis — 피처 스토어 / 캐시
  # ──────────────────────────────────────
  redis:
    image: redis:7-alpine
    container_name: lab-redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - pipeline-net
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
```

### 1-4. PostgreSQL 초기화 스크립트

```sql
-- scripts/init-db.sql
-- Airflow 메타데이터 DB
CREATE DATABASE airflow_db;

-- 실습용 샘플 테이블 (이후 데이터 이관 실습에서 활용)
CREATE TABLE transactions (
    tx_id       SERIAL PRIMARY KEY,
    user_id     INT NOT NULL,
    amount      DECIMAL(12,2) NOT NULL,
    currency    VARCHAR(3) DEFAULT 'KRW',
    tx_type     VARCHAR(20) NOT NULL,
    status      VARCHAR(20) DEFAULT 'PENDING',
    created_at  TIMESTAMP DEFAULT NOW()
);

-- 샘플 데이터 100건 삽입
INSERT INTO transactions (user_id, amount, currency, tx_type, status, created_at)
SELECT
    (random() * 999 + 1)::INT,
    (random() * 9999999 + 1000)::DECIMAL(12,2),
    CASE WHEN random() < 0.7 THEN 'KRW' WHEN random() < 0.9 THEN 'USD' ELSE 'JPY' END,
    CASE WHEN random() < 0.5 THEN 'TRANSFER' WHEN random() < 0.8 THEN 'PAYMENT' ELSE 'WITHDRAWAL' END,
    CASE WHEN random() < 0.85 THEN 'COMPLETED' WHEN random() < 0.95 THEN 'PENDING' ELSE 'FAILED' END,
    NOW() - (random() * INTERVAL '30 days')
FROM generate_series(1, 100);
```

### 1-5. 기반 서비스 기동 및 검증

```bash
# 기동
docker compose up -d postgres redis

# 상태 확인
docker compose ps

# PostgreSQL 검증
docker exec lab-postgres psql -U pipeline -d pipeline_db \
  -c "SELECT count(*) AS tx_count FROM transactions;"
# 기대 결과: tx_count = 100

docker exec lab-postgres psql -U pipeline -d pipeline_db \
  -c "SELECT tx_type, count(*), round(avg(amount),0) AS avg_amt FROM transactions GROUP BY tx_type;"

# Airflow DB 생성 확인
docker exec lab-postgres psql -U pipeline -d pipeline_db -c "\l" | grep airflow_db

# Redis 검증
docker exec lab-redis redis-cli -a redis ping
# 기대 결과: PONG

docker exec lab-redis redis-cli -a redis SET test:hello "pipeline-lab"
docker exec lab-redis redis-cli -a redis GET test:hello
# 기대 결과: "pipeline-lab"

docker exec lab-redis redis-cli -a redis DEL test:hello
```

**Day 1 완료 기준**: PostgreSQL에 transactions 테이블 100건 확인, Redis PING/PONG 정상.

---

## Day 2: 메시징·수집 계층 구성 (Kafka + NiFi)

### 2-1. Kafka (KRaft 모드) 서비스 추가

docker-compose.yml의 services 섹션에 추가:

```yaml
  # ──────────────────────────────────────
  # Kafka — KRaft 모드 (Zookeeper 불필요)
  # ──────────────────────────────────────
  kafka:
    image: apache/kafka:3.7.0
    container_name: lab-kafka
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093,EXTERNAL://0.0.0.0:29092
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,EXTERNAL://localhost:29092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT,EXTERNAL:PLAINTEXT
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_LOG_RETENTION_HOURS: 168
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "false"
      CLUSTER_ID: "MkU3OEVBNTcwNTJENDM2Qk"  # KRaft 클러스터 ID (Week 2 멀티 브로커와 동일)
    ports:
      - "29092:29092"
    networks:
      - pipeline-net
    healthcheck:
      test: ["CMD-SHELL", "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list || exit 1"]
      interval: 15s
      timeout: 10s
      retries: 10
      start_period: 30s
```

### 2-2. NiFi 서비스 추가

```yaml
  # ──────────────────────────────────────
  # NiFi — 데이터 수집·라우팅
  # ──────────────────────────────────────
  nifi:
    image: apache/nifi:1.25.0
    container_name: lab-nifi
    environment:
      NIFI_WEB_HTTP_PORT: 8080
      SINGLE_USER_CREDENTIALS_USERNAME: ${NIFI_USERNAME}
      SINGLE_USER_CREDENTIALS_PASSWORD: ${NIFI_PASSWORD}
    ports:
      - "8080:8080"
    networks:
      - pipeline-net
    healthcheck:
      test: ["CMD-SHELL", "curl -sf http://localhost:8080/nifi/ || exit 1"]
      interval: 20s
      timeout: 10s
      retries: 15
      start_period: 60s
```

### 2-3. Kafka 기동 및 검증

```bash
# 기동
docker compose up -d kafka

# 토픽 생성
docker exec lab-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --create --topic test-transactions \
  --partitions 3 \
  --replication-factor 1

# 토픽 목록 확인
docker exec lab-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --list
# 기대 결과: test-transactions

# 토픽 상세 확인
docker exec lab-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --describe --topic test-transactions

# 메시지 프로듀스 테스트
echo '{"tx_id":1,"user_id":42,"amount":150000,"type":"PAYMENT"}' | \
docker exec -i lab-kafka /opt/kafka/bin/kafka-console-producer.sh \
  --bootstrap-server localhost:9092 \
  --topic test-transactions

# 메시지 컨슈머 테스트
docker exec lab-kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic test-transactions \
  --from-beginning \
  --max-messages 1
# 기대 결과: {"tx_id":1,"user_id":42,"amount":150000,"type":"PAYMENT"}
```

### 2-4. NiFi 기동 및 검증

```bash
# 기동
docker compose up -d nifi

# 로그 확인 (기동 완료까지 1~2분 소요)
docker logs -f lab-nifi 2>&1 | grep -i "started"

# 웹 UI 접속 확인
curl -sf http://localhost:8080/nifi/ > /dev/null && echo "NiFi OK" || echo "NiFi NOT READY"
```

브라우저에서 `http://localhost:8080/nifi/` 접속하여 로그인 (admin / nifi).

**NiFi 기본 검증 플로우 생성 (UI에서 수행)**:

1. GenerateFlowFile 프로세서 추가 — 테스트 데이터 자동 생성
2. LogAttribute 프로세서 추가 — 데이터 속성 로깅
3. 두 프로세서를 Connection으로 연결
4. 시작 후 LogAttribute에서 FlowFile 수신 확인

**Day 2 완료 기준**: Kafka 토픽 생성·메시지 송수신 확인, NiFi 웹 UI 접속 및 기본 플로우 작동.

---

## Day 3: 처리·오케스트레이션 계층 (Flink + Spark + Airflow)

### 3-1. Flink 서비스 추가

```yaml
  # ──────────────────────────────────────
  # Flink — 실시간 스트림 처리
  # ──────────────────────────────────────
  flink-jobmanager:
    image: flink:1.18.1-scala_2.12-java11
    container_name: lab-flink-jm
    command: jobmanager
    environment:
      FLINK_PROPERTIES: |
        jobmanager.rpc.address: flink-jobmanager
        taskmanager.numberOfTaskSlots: 4
        parallelism.default: 2
    ports:
      - "8081:8081"
    networks:
      - pipeline-net
    healthcheck:
      test: ["CMD-SHELL", "curl -sf http://localhost:8081/overview || exit 1"]
      interval: 15s
      timeout: 10s
      retries: 10

  flink-taskmanager:
    image: flink:1.18.1-scala_2.12-java11
    container_name: lab-flink-tm
    command: taskmanager
    environment:
      FLINK_PROPERTIES: |
        jobmanager.rpc.address: flink-jobmanager
        taskmanager.numberOfTaskSlots: 4
        parallelism.default: 2
    depends_on:
      flink-jobmanager:
        condition: service_healthy
    networks:
      - pipeline-net
```

### 3-2. Spark 서비스 추가

```yaml
  # ──────────────────────────────────────
  # Spark — 배치 처리
  # ──────────────────────────────────────
  spark-master:
    image: apache/spark:3.5.1
    container_name: lab-spark-master
    command:
      - /opt/spark/bin/spark-class
      - org.apache.spark.deploy.master.Master
      - --host
      - spark-master
      - --port
      - "7077"
      - --webui-port
      - "8080"
    ports:
      - "8082:8080"
      - "7077:7077"
    volumes:
      - ./spark-etl:/opt/spark-etl
      - ./spark-jobs:/opt/spark-jobs
      - ./data:/data
    networks:
      - pipeline-net
    healthcheck:
      test: ["CMD-SHELL", "curl -sf http://localhost:8080/ || exit 1"]
      interval: 15s
      timeout: 10s
      retries: 10

  spark-worker:
    image: apache/spark:3.5.1
    container_name: lab-spark-worker
    command:
      - /opt/spark/bin/spark-class
      - org.apache.spark.deploy.worker.Worker
      - spark://spark-master:7077
      - --cores
      - "2"
      - --memory
      - 2g
      - --webui-port
      - "8081"
    depends_on:
      spark-master:
        condition: service_healthy
    volumes:
      - ./spark-etl:/opt/spark-etl
      - ./spark-jobs:/opt/spark-jobs
      - ./data:/data
    networks:
      - pipeline-net
```

> 참고: Spark는 `bitnami/spark` 대신 공식 이미지 `apache/spark:3.5.1` 기준으로 구성하며, `SPARK_MODE` 환경변수 방식이 아니라 `spark-class` 명령으로 Master/Worker를 직접 기동한다.

### 3-3. Airflow 서비스 추가

```yaml
  # ──────────────────────────────────────
  # Airflow — 오케스트레이션
  # ──────────────────────────────────────
  airflow-init:
    image: apache/airflow:2.8.4-python3.11
    container_name: lab-airflow-init
    entrypoint: >
      bash -c "
        airflow db init &&
        airflow users create \
          --username ${AIRFLOW_ADMIN_USERNAME} \
          --password ${AIRFLOW_ADMIN_PASSWORD} \
          --firstname Admin \
          --lastname User \
          --role Admin \
          --email admin@pipeline-lab.local
      "
    environment:
      AIRFLOW_ADMIN_USERNAME: ${AIRFLOW_ADMIN_USERNAME}
      AIRFLOW_ADMIN_PASSWORD: ${AIRFLOW_ADMIN_PASSWORD}
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: ${AIRFLOW__DATABASE__SQL_ALCHEMY_CONN}
      AIRFLOW__CORE__FERNET_KEY: ${AIRFLOW__CORE__FERNET_KEY}
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - pipeline-net

  airflow-webserver:
    image: apache/airflow:2.8.4-python3.11
    container_name: lab-airflow-web
    command: airflow webserver --port 8083
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: ${AIRFLOW__DATABASE__SQL_ALCHEMY_CONN}
      AIRFLOW__CORE__FERNET_KEY: ${AIRFLOW__CORE__FERNET_KEY}
      AIRFLOW__CORE__EXECUTOR: ${AIRFLOW__CORE__EXECUTOR}
      AIRFLOW__CORE__LOAD_EXAMPLES: ${AIRFLOW__CORE__LOAD_EXAMPLES}
      AIRFLOW__WEBSERVER__SECRET_KEY: ${AIRFLOW__WEBSERVER__SECRET_KEY}
      _PIP_ADDITIONAL_REQUIREMENTS: "redis confluent-kafka"
    ports:
      - "8083:8083"
    volumes:
      - ./dags:/opt/airflow/dags
    depends_on:
      airflow-init:
        condition: service_completed_successfully
    networks:
      - pipeline-net
    healthcheck:
      test: ["CMD-SHELL", "curl -sf http://localhost:8083/health || exit 1"]
      interval: 20s
      timeout: 10s
      retries: 15
      start_period: 30s

  airflow-scheduler:
    image: apache/airflow:2.8.4-python3.11
    container_name: lab-airflow-sched
    command: airflow scheduler
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: ${AIRFLOW__DATABASE__SQL_ALCHEMY_CONN}
      AIRFLOW__CORE__FERNET_KEY: ${AIRFLOW__CORE__FERNET_KEY}
      AIRFLOW__CORE__EXECUTOR: ${AIRFLOW__CORE__EXECUTOR}
      AIRFLOW__CORE__LOAD_EXAMPLES: ${AIRFLOW__CORE__LOAD_EXAMPLES}
    volumes:
      - ./dags:/opt/airflow/dags
    depends_on:
      airflow-init:
        condition: service_completed_successfully
    networks:
      - pipeline-net
```

### 3-4. 샘플 Airflow DAG — 환경 검증용

```python
# dags/healthcheck_dag.py
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
        bash_command='python -c "import psycopg2; c=psycopg2.connect(host=\'postgres\',dbname=\'pipeline_db\',user=\'pipeline\',password=\'pipeline\'); print(\'PostgreSQL OK\')"',
    )

    check_redis = BashOperator(
        task_id="check_redis",
        bash_command='python -c "import redis; r=redis.Redis(host=\'redis\',password=\'redis\'); print(r.ping())"',
    )

    check_kafka = BashOperator(
        task_id="check_kafka",
        bash_command='python3 -c "from confluent_kafka.admin import AdminClient; a=AdminClient({\'bootstrap.servers\':\'kafka:9092\'}); print(\'Kafka brokers:\', len(a.list_topics(timeout=5).brokers))"',
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
```

### 3-5. 컴포넌트별 기동 및 검증

```bash
# Flink 기동
docker compose up -d flink-jobmanager flink-taskmanager

# Flink 대시보드 확인
curl -sf http://localhost:8081/overview | python3 -m json.tool
# 기대: taskmanagers: 1, slots-total: 4

# Spark 기동
docker compose up -d spark-master spark-worker

# Spark 마스터 UI 확인
curl -sf http://localhost:8082/ > /dev/null && echo "Spark Master OK"

# Airflow 기동 (init → webserver + scheduler 순서)
docker compose up -d airflow-init
docker compose up -d airflow-webserver airflow-scheduler

# Airflow 웹 UI 확인
curl -sf http://localhost:8083/health | python3 -m json.tool
# 기대: metadatabase.status = healthy, scheduler.status = healthy
```

**웹 UI 접속 정보**:

| 서비스 | URL | 계정 |
|--------|-----|------|
| Flink Dashboard | http://localhost:8081 | (인증 없음) |
| Spark Master | http://localhost:8082 | (인증 없음) |
| Airflow | http://localhost:8083 | admin / airflow |

**Day 3 완료 기준**: Flink 대시보드에서 TaskManager 1개·슬롯 4개 확인, Spark Master에 Worker 1개 등록 확인, Airflow 웹 UI 로그인 성공.

---

## Day 4: 전체 스택 통합 기동 + 연동 검증

### 4-1. 전체 스택 한 번에 기동

```bash
# 이전 컨테이너 정리
docker compose down -v

# 전체 기동
docker compose up -d

# 전체 상태 확인 (모든 서비스 healthy/running)
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
```

### 4-2. 통합 헬스체크 스크립트

```bash
#!/bin/bash
# scripts/healthcheck-all.sh
# 전체 환경 헬스체크 스크립트

echo "============================================"
echo " Pipeline Lab — 전체 환경 헬스체크"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
echo ""

PASS=0
FAIL=0

if docker ps --format '{{.Names}}' | grep -q '^lab-kafka-1$'; then
  KAFKA_CONTAINER="lab-kafka-1"
  KAFKA_BOOTSTRAP="kafka-1:9092"
else
  KAFKA_CONTAINER="lab-kafka"
  KAFKA_BOOTSTRAP="localhost:9092"
fi

check() {
  local name=$1
  local cmd=$2
  printf "  %-20s : " "$name"
  if eval "$cmd" > /dev/null 2>&1; then
    echo "✅ OK"
    ((PASS++))
  else
    echo "❌ FAIL"
    ((FAIL++))
  fi
}

echo "[기반 서비스]"
check "PostgreSQL" "docker exec lab-postgres pg_isready -U pipeline"
check "Redis" "docker exec lab-redis redis-cli -a redis ping"

echo ""
echo "[메시징·수집]"
check "Kafka" "docker exec ${KAFKA_CONTAINER} /opt/kafka/bin/kafka-topics.sh --bootstrap-server ${KAFKA_BOOTSTRAP} --list"
check "NiFi" "curl -sf http://localhost:8080/nifi/"

echo ""
echo "[처리·오케스트레이션]"
check "Flink JobManager" "curl -sf http://localhost:8081/overview"
check "Spark Master" "curl -sf http://localhost:8082/"
check "Airflow" "curl -sf http://localhost:8083/health"

echo ""
echo "============================================"
echo " 결과: ✅ ${PASS} 통과 / ❌ ${FAIL} 실패"
echo "============================================"
```

```bash
chmod +x scripts/healthcheck-all.sh
bash scripts/healthcheck-all.sh
```

기대 출력:

```
============================================
 Pipeline Lab — 전체 환경 헬스체크
 2026-04-01 09:00:00
============================================

[기반 서비스]
  PostgreSQL           : ✅ OK
  Redis                : ✅ OK

[메시징·수집]
  Kafka                : ✅ OK
  NiFi                 : ✅ OK

[처리·오케스트레이션]
  Flink JobManager     : ✅ OK
  Spark Master         : ✅ OK
  Airflow              : ✅ OK

============================================
 결과: ✅ 7 통과 / ❌ 0 실패
============================================
```

### 4-3. 연동 검증 실습 — Kafka → 콘솔 컨슈머 데이터 흐름

파이프라인 토픽을 만들고, 샘플 거래 데이터를 프로듀싱한 뒤, 컨슈머로 확인한다.

> **참고**: 아래 `paynex-transactions` 토픽은 연동 검증 목적의 **임시 토픽**이다. Week 2에서 정식 명명 규칙(`<도메인>.<엔티티>.<이벤트유형>`, 점 구분자)에 따라 `paynex.transactions.payment` 등으로 재생성하며, 이 토픽은 삭제할 예정이다.

```bash
# 실습용 임시 토픽 생성 (Week 2에서 정식 토픽으로 교체 예정)
docker exec lab-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --create --topic paynex-transactions \
  --partitions 3 \
  --replication-factor 1

# 샘플 거래 데이터 10건 프로듀스
for i in $(seq 1 10); do
  echo "{\"tx_id\":$i,\"user_id\":$((RANDOM % 1000)),\"amount\":$((RANDOM % 5000000 + 10000)),\"type\":\"PAYMENT\",\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" | \
  docker exec -i lab-kafka /opt/kafka/bin/kafka-console-producer.sh \
    --bootstrap-server localhost:9092 \
    --topic paynex-transactions
done

# 컨슈머로 수신 확인
docker exec lab-kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic paynex-transactions \
  --from-beginning \
  --max-messages 10
```

### 4-4. 연동 검증 실습 — PostgreSQL → Redis 피처 캐싱 시뮬레이션

```bash
# PostgreSQL에서 사용자별 거래 통계 조회
docker exec lab-postgres psql -U pipeline -d pipeline_db -t -A -F'|' \
  -c "SELECT user_id, count(*) as tx_count, round(avg(amount),0) as avg_amount
      FROM transactions GROUP BY user_id ORDER BY tx_count DESC LIMIT 5;"

# 결과를 Redis에 피처로 저장하는 시뮬레이션
docker exec lab-redis redis-cli -a redis HSET user:features:42 tx_count 15 avg_amount 3500000
docker exec lab-redis redis-cli -a redis HGETALL user:features:42
# 기대: tx_count 15 avg_amount 3500000
```

### 4-5. 리소스 사용량 확인

```bash
# 컨테이너별 CPU·메모리 사용량
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

전체 스택 기동 시 최소 8GB RAM 권장. 16GB 이상이면 여유 있음.

**Day 4 완료 기준**: 7개 서비스 전체 헬스체크 통과, Kafka 메시지 10건 프로듀스→컨슈머 확인, PostgreSQL→Redis 피처 저장 확인.

---

## Day 5: 장애 테스트 + 문서화

### 5-1. 장애 시나리오 테스트

**시나리오 A: Kafka 브로커 장애 및 복구**

```bash
# 현재 토픽 상태 확인
docker exec lab-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --describe --topic paynex-transactions

# Kafka 컨테이너 강제 중단
docker stop lab-kafka

# 다른 서비스 영향 확인
docker compose ps

# Kafka 재기동
docker start lab-kafka

# 30초 대기 후 복구 확인
sleep 30
docker exec lab-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --list

# 기존 메시지 보존 확인
docker exec lab-kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic paynex-transactions \
  --from-beginning \
  --max-messages 10
# 기대: 이전에 프로듀스한 10건 그대로 존재
```

**시나리오 B: PostgreSQL 장애 및 Airflow 영향 확인**

```bash
# PostgreSQL 중단
docker stop lab-postgres

# Airflow 상태 확인 (DB 연결 실패)
curl -s http://localhost:8083/health | python3 -m json.tool
# 기대: metadatabase.status = unhealthy

# PostgreSQL 재기동
docker start lab-postgres

# 30초 대기 후 Airflow 복구 확인
sleep 30
curl -s http://localhost:8083/health | python3 -m json.tool
# 기대: metadatabase.status = healthy
```

**시나리오 C: Flink TaskManager 장애 및 복구**

```bash
# TaskManager 중단
docker stop lab-flink-tm

# JobManager 대시보드에서 Available Task Slots = 0 확인
curl -s http://localhost:8081/overview | python3 -m json.tool

# TaskManager 재기동
docker start lab-flink-tm

# 슬롯 복구 확인
sleep 15
curl -s http://localhost:8081/overview | python3 -m json.tool
# 기대: taskmanagers: 1, slots-available: 4
```

### 5-2. 장애 테스트 결과 기록 템플릿

```markdown
## 장애 테스트 결과

| 시나리오 | 중단 대상 | 영향 범위 | 복구 소요 시간 | 데이터 손실 여부 | 비고 |
|----------|----------|----------|-------------|---------------|------|
| A | Kafka | 프로듀서/컨슈머 일시 중단 | ~30초 | 없음 (로그 보존) | |
| B | PostgreSQL | Airflow 메타DB 연결 실패 | ~30초 | 없음 (볼륨 유지) | |
| C | Flink TM | 스트림 처리 중단 | ~15초 | 작업 재시작 필요 | |
```

### 5-3. 환경 문서화 — README.md 작성

```markdown
# Pipeline Lab — 데이터 파이프라인 실습 환경

## 아키텍처 개요

수집(Kafka·NiFi) → 변환(Flink·Spark) → 저장(PostgreSQL·Redis) → 오케스트레이션(Airflow)

## 서비스 구성

| 서비스 | 컨테이너 | 포트 | 용도 |
|--------|---------|------|------|
| PostgreSQL 16 | lab-postgres | 5432 | 메타데이터·샘플 DB |
| Redis 7 | lab-redis | 6379 | 피처 스토어·캐시 |
| Kafka 3.7 (KRaft) | lab-kafka | 29092 | 실시간 메시징 |
| NiFi 1.25 | lab-nifi | 8080 | 데이터 수집·라우팅 |
| Flink 1.18 | lab-flink-jm/tm | 8081 | 실시간 스트림 처리 |
| Spark 3.5 | lab-spark-master | 8082 | 배치 처리 |
| Airflow 2.8 | lab-airflow-web | 8083 | 워크플로우 오케스트레이션 |

## 빠른 시작

docker compose up -d
bash scripts/healthcheck-all.sh

## 접속 정보

- NiFi: http://localhost:8080/nifi (admin / nifi)
- Flink: http://localhost:8081
- Spark: http://localhost:8082
- Airflow: http://localhost:8083 (admin / airflow)

## 종료 및 정리

docker compose down        # 컨테이너 중단 (데이터 보존)
docker compose down -v     # 컨테이너 + 볼륨 삭제 (초기화)
```

### 5-4. 최종 정리 및 Week 2 준비

```bash
# 전체 환경 최종 검증
bash scripts/healthcheck-all.sh

# Week 2 준비: 연동 테스트용 토픽 생성 (Week 2에서 정식 명명규칙에 따라 재생성 예정)
docker exec lab-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --create --topic test.connectivity-check \
  --partitions 3 \
  --replication-factor 1

# Git 초기화 및 커밋
cd pipeline-lab
git init
echo "postgres-data/\nredis-data/" > .gitignore
git add .
git commit -m "Week 1: 전체 스택 환경 구성 완료 — 7개 컴포넌트 Docker Compose"
```

**Day 5 완료 기준**: 장애 시나리오 3건 테스트 완료, README.md 작성, Git 첫 커밋.

---

## Week 1 산출물 체크리스트

| # | 산출물 | 완료 |
|---|--------|------|
| 1 | docker-compose.yml (7개 서비스 정의) | ☐ |
| 2 | .env 환경 변수 파일 | ☐ |
| 3 | scripts/init-db.sql (PostgreSQL 초기화) | ☐ |
| 4 | scripts/healthcheck-all.sh (통합 헬스체크) | ☐ |
| 5 | dags/healthcheck_dag.py (Airflow 검증 DAG) | ☐ |
| 6 | 장애 테스트 결과 기록 | ☐ |
| 7 | README.md (환경 문서) | ☐ |
| 8 | Git 초기 커밋 | ☐ |

## 포트 맵 요약

| 포트 | 서비스 |
|------|--------|
| 5432 | PostgreSQL |
| 6379 | Redis |
| 29092 | Kafka (외부 접속) |
| 8080 | NiFi |
| 8081 | Flink Dashboard |
| 8082 | Spark Master UI |
| 8083 | Airflow |

## Week 2 예고

Week 2에서는 이 환경 위에서 Kafka 심화 실습을 진행한다. 토픽 설계 전략, 파티션 키 기반 메시지 라우팅, 컨슈머 그룹 관리, 오프셋 수동 커밋, 복제 설정 등을 다룬다. Day 4에서 만든 `paynex-transactions` 토픽을 확장하여 실제 금융 거래 시나리오를 구현한다.
