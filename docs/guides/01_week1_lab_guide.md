# Week 1: 데이터 파이프라인 실습 환경 구성

**기간**: 5일 (월~금, 풀타임 40시간)
**주제**: Docker Compose 전체 스택 기동·검증
**산출물**: 로컬 실습 환경 + 컴포넌트별 헬스체크 완료 + 통합 연동 검증

---

## 수행 시나리오

### 배경 설정

가상의 핀테크 서비스 **"Nexus Pay"** 는 안정적이고 확장 가능한 결제 플랫폼을 목표로 하는 MSA 기반 Payment Service다. 컨설턴트이자 데이터 파이프라인 담당 역할로서 PoC(Proof of Concept) 환경을 로컬에 구축하여 전체 Apache 오픈소스 스택이 정상적으로 작동하는지 검증해야 한다. 이 환경은 이후 8주간의 모든 실습의 기반이 된다.

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
NIFI_PASSWORD=1q2w3e4r5t1!

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
      - ./scripts/foundation/init-db.sql:/docker-entrypoint-initdb.d/01-init-db.sql
      - ./scripts/nifi/init-customers.sql:/docker-entrypoint-initdb.d/02-init-customers.sql
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
-- scripts/foundation/init-db.sql
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
docker exec -e REDISCLI_AUTH=redis lab-redis redis-cli ping
# 기대 결과: PONG

docker exec -e REDISCLI_AUTH=redis lab-redis redis-cli SET test:hello "pipeline-lab"
docker exec -e REDISCLI_AUTH=redis lab-redis redis-cli GET test:hello
# 기대 결과: "pipeline-lab"

docker exec -e REDISCLI_AUTH=redis lab-redis redis-cli DEL test:hello
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
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093,EXTERNAL://0.0.0.0:30092
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,EXTERNAL://localhost:30092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT,EXTERNAL:PLAINTEXT
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_LOG_RETENTION_HOURS: 168
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "false"
      CLUSTER_ID: "MkU3OEVBNTcwNTJENDM2Qk"  # KRaft 클러스터 ID (Week 2 멀티 브로커와 동일)
    ports:
      - "30092:30092"
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
    image: apache/nifi:2.9.0
    container_name: lab-nifi
    environment:
      NIFI_WEB_HTTPS_PORT: 8443
      NIFI_WEB_PROXY_HOST: localhost:8443
      SINGLE_USER_CREDENTIALS_USERNAME: ${NIFI_USERNAME}
      SINGLE_USER_CREDENTIALS_PASSWORD: ${NIFI_PASSWORD}
    ports:
      - "8443:8443"
    networks:
      - pipeline-net
    healthcheck:
      test: ["CMD-SHELL", "curl -skf https://localhost:8443/nifi/ || exit 1"]
      interval: 20s
      timeout: 10s
      retries: 15
      start_period: 60s
```

> **새 학습 환경 원칙**: NiFi 2.9.0 실습은 예전 1.x `nifi-conf` 볼륨을 재사용하지 않는다. 기존 NiFi 학습 흔적이 있으면 `pipeline-lab_nifi-conf`, `pipeline-lab_nifi-state`, `pipeline-lab_nifi-database-repo`, `pipeline-lab_nifi-flowfile-repo`, `pipeline-lab_nifi-content-repo`, `pipeline-lab_nifi-provenance-repo`, `pipeline-lab_nifi-logs`를 먼저 삭제한 뒤 새로 기동한다.

### 2-2-1. Git Bash 기준 TLS/CA 준비

NiFi 2.9.0은 기본적으로 HTTPS `8443`로 기동한다. `https://localhost:8443/nifi/` 접속 시 브라우저 경고를 줄이고, 실습 중 클라이언트 인증서 선택 창 없이 접속하려면 회사 PC에서 직접 `mkcert` 기반 로컬 CA와 `localhost` 인증서를 준비하는 편이 가장 안정적이다.

가장 빠른 방법은 저장소에 포함된 재생성 스크립트를 사용하는 것이다.

```bash
bash scripts/nifi/regenerate_local_tls.sh
```

이 스크립트는 현재 PC의 `mkcert` 로컬 CA를 기준으로 `config/nifi/tls` 아래 `localhost` 인증서와 NiFi용 `PKCS#12` 파일을 다시 만든다. 예전 클론에서 다른 PC에서 생성된 인증서가 남아 있으면 `NET::ERR_CERT_AUTHORITY_INVALID`가 발생할 수 있으므로, 이 경우에도 같은 스크립트를 다시 실행하면 된다.

**1. `mkcert` 설치 및 로컬 CA 생성**

```bash
winget install --id FiloSottile.mkcert -e
mkcert -install
```

정상 확인:

```bash
mkcert -CAROOT
```

**2. `localhost` 인증서 생성**

```bash
mkdir -p config/nifi/tls

mkcert -cert-file config/nifi/tls/localhost+2.pem \
  -key-file config/nifi/tls/localhost+2-key.pem \
  localhost 127.0.0.1 ::1
```

**3. NiFi용 PKCS#12 keystore / truststore 생성**

```bash
openssl pkcs12 -export \
  -inkey config/nifi/tls/localhost+2-key.pem \
  -in config/nifi/tls/localhost+2.pem \
  -certfile "$(mkcert -CAROOT)/rootCA.pem" \
  -out config/nifi/tls/nifi-keystore.p12 \
  -name nifi-key \
  -passout pass:changeit
```

```bash
openssl pkcs12 -export \
  -nokeys \
  -in "$(mkcert -CAROOT)/rootCA.pem" \
  -out config/nifi/tls/nifi-truststore.p12 \
  -name nifi-root-ca \
  -passout pass:changeit
```

정상 확인:

```bash
ls -l config/nifi/tls
```

**4. 왜 클라이언트 인증서 선택 창이 뜨지 않아야 하는가**

현재 저장소의 `config/nifi/start-nifi-2.9.0.sh`는 다음을 자동으로 수행한다.

- `nifi-keystore.p12`, `nifi-truststore.p12`를 NiFi `conf`로 복사
- `nifi.security.needClientAuth=false`를 `nifi.properties`에 반영
- `SINGLE_USER_CREDENTIALS_USERNAME`, `SINGLE_USER_CREDENTIALS_PASSWORD`를 적용

즉 정상 기동이라면 브라우저는 서버 인증서만 검증하고, 별도의 클라이언트 인증서를 요구하지 않아야 한다.

기동 후 확인 명령:

```bash
docker exec lab-nifi sh -lc "grep '^nifi.security.needClientAuth=' /opt/nifi/nifi-current/conf/nifi.properties"
```

정상 기대값:

```bash
nifi.security.needClientAuth=false
```

### 2-2-2. `NIFI_USERNAME`, `NIFI_PASSWORD` 적용 규칙

`.env`에 다음 값을 둔다.

```env
NIFI_USERNAME=admin
NIFI_PASSWORD=1q2w3e4r5t1!
```

`docker-compose.yml`에서는 이를 다음 환경변수로 NiFi 컨테이너에 전달한다.

```yaml
SINGLE_USER_CREDENTIALS_USERNAME: ${NIFI_USERNAME}
SINGLE_USER_CREDENTIALS_PASSWORD: ${NIFI_PASSWORD}
```

중요한 점은 Docker Compose가 `.env`보다 **현재 셸 환경변수**를 우선한다는 것이다. 따라서 Git Bash 세션에 이미 `NIFI_USERNAME` 또는 `NIFI_PASSWORD`가 잡혀 있으면 `.env` 값이 무시될 수 있다.

실습 전 권장 명령:

```bash
unset NIFI_USERNAME
unset NIFI_PASSWORD
docker compose config | grep -A3 'SINGLE_USER_CREDENTIALS'
```

기동 후 컨테이너 내부 확인:

```bash
docker exec lab-nifi sh -lc 'env | grep "^SINGLE_USER_CREDENTIALS_"'
```

정상 기대값:

```bash
SINGLE_USER_CREDENTIALS_USERNAME=admin
SINGLE_USER_CREDENTIALS_PASSWORD=1q2w3e4r5t1!
```

### 2-3. Kafka 기동 및 검증

```bash
# 기동
docker compose up -d kafka

# Git Bash 사용 시 `/opt/...` 경로가 Windows 경로로 잘못 변환될 수 있으므로
# Kafka CLI는 `docker exec ... sh -c '...'` 형태로 실행한다.

# 토픽 생성
docker exec lab-kafka sh -c '/opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --create --topic test-transactions \
  --partitions 3 \
  --replication-factor 1'

# 토픽 목록 확인
docker exec lab-kafka sh -c '/opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --list'
# 기대 결과: test-transactions

# 토픽 상세 확인
docker exec lab-kafka sh -c '/opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --describe --topic test-transactions'

# 메시지 프로듀스 테스트
echo '{"tx_id":1,"user_id":42,"amount":150000,"type":"PAYMENT"}' | \
docker exec -i lab-kafka sh -c '/opt/kafka/bin/kafka-console-producer.sh \
  --bootstrap-server localhost:9092 \
  --topic test-transactions'

# 메시지 컨슈머 테스트
docker exec lab-kafka sh -c '/opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic test-transactions \
  --from-beginning \
  --max-messages 1'
# 기대 결과: {"tx_id":1,"user_id":42,"amount":150000,"type":"PAYMENT"}
```

### 2-4. NiFi 기동 및 검증

```bash
# 기동
docker compose up -d nifi

# 로그 확인 (기동 완료까지 1~2분 소요)
docker logs -f lab-nifi 2>&1 | grep -i "started"

# 웹 UI 접속 확인
curl -skf https://localhost:8443/nifi/ > /dev/null && echo "NiFi OK" || echo "NiFi NOT READY"
```

브라우저에서 `https://localhost:8443/nifi/` 접속한다. `mkcert -install`과 `localhost` 인증서를 올바르게 준비했다면 일반적인 서버 인증서 경고 없이 접속할 수 있다. 로그인 화면이 나타나면 `.env`의 `NIFI_USERNAME / NIFI_PASSWORD` 값으로 로그인한다. 이미 `NiFi Flow` 캔버스가 바로 보이면 인증 세션이 유지된 상태이므로 추가 로그인 없이 진행하면 된다.

만약 브라우저가 `NET::ERR_CERT_AUTHORITY_INVALID`를 표시하면, 현재 PC가 신뢰하지 않는 다른 환경의 인증서가 `config/nifi/tls`에 남아 있을 가능성이 높다. 아래 순서로 복구한다.

```bash
bash scripts/nifi/regenerate_local_tls.sh
docker compose restart nifi
```

만약 브라우저가 `localhost:8443` 접속 시 `인증서 선택` 팝업을 띄우면, 이는 서버가 클라이언트 인증서를 요구하는 상태다. 아래 순서로 확인한다.

```bash
docker exec lab-nifi sh -lc "grep '^nifi.security.needClientAuth=' /opt/nifi/nifi-current/conf/nifi.properties"
docker exec lab-nifi sh -lc 'env | grep "^SINGLE_USER_CREDENTIALS_"'
docker exec lab-nifi sh -lc "grep -n 'Username' /opt/nifi/nifi-current/conf/login-identity-providers.xml"
```

문제가 있으면 NiFi 볼륨을 삭제한 뒤 재기동한다.

```bash
docker compose down
docker volume rm \
  pipeline-lab_nifi-conf \
  pipeline-lab_nifi-state \
  pipeline-lab_nifi-database-repo \
  pipeline-lab_nifi-flowfile-repo \
  pipeline-lab_nifi-content-repo \
  pipeline-lab_nifi-provenance-repo \
  pipeline-lab_nifi-logs
docker compose up -d nifi
```

**NiFi 기본 검증 플로우 생성 (UI에서 수행)**:

1. `GenerateFlowFile` 프로세서 추가 — 테스트용 FlowFile 자동 생성
2. `LogAttribute` 프로세서 추가 — FlowFile 속성 로그 기록
3. `GenerateFlowFile`의 `success` relationship을 `LogAttribute`에 Connection으로 연결
4. `LogAttribute` 설정의 `Relationships` 탭에서 `success -> terminate`를 체크하여 최종 출력 relationship을 자동 종료로 설정
5. 두 프로세서를 시작하고 Connection 큐가 `0 (0 bytes)`로 유지되는지 확인
6. `LogAttribute`의 `In` 값이 증가하는지 확인하여 FlowFile 수신을 검증

> 참고: `LogAttribute`의 `success`가 어디에도 연결되지 않았고 `terminate`도 체크되지 않으면 `Relationship success is invalid...` 경고와 함께 프로세서를 시작할 수 없다.

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
      bash -c "airflow db migrate &&
      airflow users create --username ${AIRFLOW_ADMIN_USERNAME} --password ${AIRFLOW_ADMIN_PASSWORD} --firstname Admin --lastname User --role Admin --email admin@pipeline-lab.local"
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
    restart: unless-stopped
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
    restart: unless-stopped
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

Airflow가 PostgreSQL, Redis, Kafka, Flink에 실제로 연결 가능한지 확인하는 수동 실행용 DAG를 추가한다.

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
        bash_command='python -c "from confluent_kafka.admin import AdminClient; a=AdminClient({\'bootstrap.servers\':\'kafka:9092\'}); print(\'Kafka brokers:\', len(a.list_topics(timeout=5).brokers))"',
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

파일 생성 후 Airflow가 DAG를 인식하는지 확인한다.

```bash
# Git Bash 사용 시 `/opt/...` 경로가 Windows 경로로 잘못 변환될 수 있으므로
# 컨테이너 내부 절대경로는 `sh -lc '...'` 형태로 감싸서 실행한다.

# Airflow 컨테이너에서 DAG 파일 확인
docker exec lab-airflow-web sh -lc "ls -l /opt/airflow/dags"

# DAG 목록에서 environment_healthcheck 확인
docker exec lab-airflow-web airflow dags list | grep environment_healthcheck
```

기대 결과:
- `/opt/airflow/dags/healthcheck_dag.py` 파일이 보인다
- `airflow dags list` 출력에 `environment_healthcheck`가 포함된다

수동 실행 검증은 UI 또는 CLI 중 편한 방법으로 진행한다.

```bash
# 방법 1: CLI로 DAG 수동 실행
docker exec lab-airflow-web airflow dags trigger environment_healthcheck

# 실행 상태 확인
docker exec lab-airflow-web airflow dags list-runs -d environment_healthcheck

# 태스크 인스턴스 상태 확인
docker exec lab-airflow-web airflow tasks states-for-dag-run environment_healthcheck <dag_run_id>
```

`<dag_run_id>`는 `list-runs`에서 확인한 값으로 바꿔 넣는다. 모든 태스크가 `success`이면 검증 통과다.

브라우저에서 확인하려면 아래 순서로 진행한다.

```text
1. http://localhost:8083 접속
2. admin / airflow 로그인
3. environment_healthcheck DAG 활성화
4. Trigger DAG 클릭
5. Graph 또는 Grid 화면에서 check_postgres, check_redis, check_kafka, check_flink, generate_report가 모두 success인지 확인
```

실행 로그까지 확인하려면 다음 명령을 사용한다.

```bash
# 최근 DAG 실행 로그 확인
docker exec lab-airflow-sched airflow dags list-runs -d environment_healthcheck

# 스케줄러 로그에서 task 실행 흔적 확인
docker compose logs airflow-scheduler --tail 200
```

기대 결과:
- `check_postgres`: `PostgreSQL OK`
- `check_redis`: `True`
- `check_kafka`: `Kafka brokers: 1`
- `check_flink`: Flink overview JSON 출력 후 `Flink OK`
- `generate_report`: 완료 시각 출력

검증이 끝나면 Day 3 완료 기준에 Airflow 연결성 검증까지 포함된 것으로 본다.

### 3-5. 컴포넌트별 기동 및 검증

```bash
# Flink 기동
docker compose up -d flink-jobmanager flink-taskmanager

# Flink 대시보드 확인
curl -sf http://localhost:8081/overview
# 기대: JSON 응답에 "taskmanagers":1, "slots-total":4 포함

# Spark 기동
docker compose up -d spark-master spark-worker

# Spark 마스터 UI 확인
curl -sf http://localhost:8082/ > /dev/null && echo "Spark Master OK"

# Airflow 기동 (init → webserver + scheduler 순서)
docker compose up -d airflow-init
docker compose up -d airflow-webserver airflow-scheduler

# Airflow 웹 UI 확인
curl -sf http://localhost:8083/health
# 기대: JSON 응답에 "metadatabase":{"status":"healthy"}, "scheduler":{"status":"healthy"} 포함
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
# scripts/foundation/healthcheck-all.sh
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
check "Redis" "docker exec -e REDISCLI_AUTH=redis lab-redis redis-cli ping"

echo ""
echo "[메시징·수집]"
check "Kafka" "docker exec ${KAFKA_CONTAINER} sh -c '/opt/kafka/bin/kafka-topics.sh --bootstrap-server ${KAFKA_BOOTSTRAP} --list'"
check "NiFi" "curl -skf https://localhost:8443/nifi/"

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
chmod +x scripts/foundation/healthcheck-all.sh
bash scripts/foundation/healthcheck-all.sh
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

> **참고**: 아래 `nexuspay-transactions` 토픽은 연동 검증 목적의 **임시 토픽**이다. Week 2에서 정식 명명 규칙(`<도메인>.<엔티티>.<이벤트유형>`, 점 구분자)에 따라 `nexuspay.transactions.payment` 등으로 재생성하며, 이 토픽은 삭제할 예정이다.

```bash
# 실습용 임시 토픽 생성 (Week 2에서 정식 토픽으로 교체 예정)
docker exec lab-kafka sh -c '/opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --create --topic nexuspay-transactions \
  --partitions 3 \
  --replication-factor 1'

# 샘플 거래 데이터 10건 프로듀스
for i in $(seq 1 10); do
  echo "{\"tx_id\":$i,\"user_id\":$((RANDOM % 1000)),\"amount\":$((RANDOM % 5000000 + 10000)),\"type\":\"PAYMENT\",\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" | \
  docker exec -i lab-kafka sh -c '/opt/kafka/bin/kafka-console-producer.sh \
    --bootstrap-server localhost:9092 \
    --topic nexuspay-transactions'
done

# 컨슈머로 수신 확인
docker exec lab-kafka sh -c '/opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic nexuspay-transactions \
  --from-beginning \
  --max-messages 10'
```

### 4-4. 연동 검증 실습 — PostgreSQL → Redis 피처 캐싱 시뮬레이션

```bash
# PostgreSQL에서 사용자별 거래 통계 조회
docker exec lab-postgres psql -U pipeline -d pipeline_db -t -A -F'|' \
  -c "SELECT user_id, count(*) as tx_count, round(avg(amount),0) as avg_amount
      FROM transactions GROUP BY user_id ORDER BY tx_count DESC LIMIT 5;"

# 결과를 Redis에 피처로 저장하는 시뮬레이션
docker exec -e REDISCLI_AUTH=redis lab-redis redis-cli HSET user:features:42 tx_count 15 avg_amount 3500000
docker exec -e REDISCLI_AUTH=redis lab-redis redis-cli HGETALL user:features:42
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
docker exec lab-kafka sh -c '/opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --describe --topic nexuspay-transactions'

# Kafka 컨테이너 강제 중단
docker stop lab-kafka

# 다른 서비스 영향 확인
docker compose ps

# Kafka 재기동
docker start lab-kafka

# 30초 대기 후 복구 확인
sleep 30
docker exec lab-kafka sh -c '/opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --list'

# 기존 메시지 보존 확인
docker exec lab-kafka sh -c '/opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic nexuspay-transactions \
  --from-beginning \
  --max-messages 10'
# 기대: 이전에 프로듀스한 10건 그대로 존재
```

**시나리오 B: PostgreSQL 장애 및 Airflow 영향 확인**

```bash
# PostgreSQL 중단
docker stop lab-postgres

# Airflow 상태 확인 (DB 연결 실패)
curl -s http://localhost:8083/health
# 기대: JSON 응답에 "metadatabase":{"status":"unhealthy"} 포함

# PostgreSQL 재기동
docker start lab-postgres

# 30초 대기 후 Airflow 복구 확인
# restart 정책이 있으면 scheduler/webserver가 DB 복구 후 자동 재시작될 수 있다.
sleep 30
curl -s http://localhost:8083/health
# 기대: JSON 응답에 "metadatabase":{"status":"healthy"} 포함
# 기대: scheduler.status 도 healthy 로 복구
```

**시나리오 C: Flink TaskManager 장애 및 복구**

```bash
# TaskManager 중단
docker stop lab-flink-tm

# JobManager 대시보드에서 Available Task Slots = 0 확인
curl -s http://localhost:8081/overview

# TaskManager 재기동
docker start lab-flink-tm

# 슬롯 복구 확인
sleep 15
curl -s http://localhost:8081/overview
# 기대: JSON 응답에 "taskmanagers":1, "slots-available":4 포함
```

### 5-2. 장애 테스트 결과 기록

현재 실습에서 실제로 확인한 결과는 아래와 같다.

```markdown
## 장애 테스트 결과

| 시나리오 | 중단 대상 | 영향 범위 | 복구 소요 시간 | 데이터 손실 여부 | 비고 |
|----------|----------|----------|-------------|---------------|------|
| A | Kafka | Kafka 토픽 조회 및 프로듀스/컨슈머 테스트 일시 중단, 타 서비스는 계속 실행 | 약 30초 | 없음 | `nexuspay-transactions` 토픽과 기존 메시지 10건 재조회 성공 |
| B | PostgreSQL | Airflow health endpoint 비정상 전환, metadatabase/scheduler 상태 unhealthy 확인 | 약 30초 | 없음 | PostgreSQL 재기동 후 `scheduler.status=healthy`까지 복구 확인 |
| C | Flink TaskManager | Flink 슬롯 4개 모두 소실, JobManager overview에서 `taskmanagers=0` 확인 | 약 15초 | 없음 | TaskManager 재기동 후 `taskmanagers=1`, `slots-available=4` 복구 확인 |
```

장애 테스트 해석:
- Kafka는 단일 브로커 실습 환경에서도 재기동 후 토픽과 메시지가 유지되었다.
- PostgreSQL은 Airflow의 핵심 의존성으로, 장애 시 Airflow health가 즉시 비정상으로 전환되었다.
- Flink는 TaskManager 장애 시 처리 슬롯이 사라지고, 재기동 후 슬롯이 정상 복구되었다.

### 5-3. 환경 문서화 — README.md 작성

Week 1 기준 환경 문서는 저장소 루트의 [README.md](/c:/Users/roadseeker/study/study-data-pipeline/README.md)에 정리한다. README에는 최소한 아래 내용을 포함한다.

- 아키텍처 개요: `수집(Kafka·NiFi) → 변환(Flink·Spark) → 저장(PostgreSQL·Redis) → 오케스트레이션(Airflow)`
- 서비스 구성: 컨테이너명, 포트, 역할
- 빠른 시작: `docker compose up -d`, `bash scripts/foundation/healthcheck-all.sh`
- 접속 정보: NiFi, Flink, Spark, Airflow URL 및 계정
- 프로젝트 구조: `dags/`, `docs/`, `scripts/`, `spark-etl/`, `spark-jobs/`, `flink-jobs/`, `data/`
- 종료 및 초기화: `docker compose down`, `docker compose down -v`

현재 README 반영 상태:
- 전체 스택 아키텍처 개요 정리 완료
- 서비스 구성 및 포트 문서화 완료
- 빠른 시작/접속 정보 정리 완료
- 프로젝트 구조 설명 포함
- 종료 및 정리 명령 포함

### 5-4. 최종 정리 및 Week 2 준비

```bash
# 전체 환경 최종 검증
bash scripts/foundation/healthcheck-all.sh

# Week 2 준비: Kafka 토픽 검증 상태 확인
docker exec lab-kafka sh -c '/opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --list'
```

Week 2 준비 포인트:
- `nexuspay-transactions` 토픽이 정상 동작하는지 이미 확인했다.
- Week 2에서는 이 토픽을 임시 검증용 자산으로 보고, 정식 명명 규칙 기반 토픽(`nexuspay.transactions.payment` 등)으로 재구성할 준비를 한다.
- Git Bash 사용 시 `docker exec ... sh -c '...'` 패턴을 유지한다.
- `.sh` 파일 줄바꿈 오류 재발 방지를 위해 저장소 루트에 `.gitattributes`를 추가했다.

**Day 5 완료 기준**: 장애 시나리오 3건 테스트 완료, README.md 정리 완료, Week 2 진행 준비 완료.

---

## Week 1 산출물 체크리스트

| # | 산출물 | 완료 |
|---|--------|------|
| 1 | docker-compose.yml (7개 서비스 정의) | ☑ |
| 2 | .env 환경 변수 파일 | ☑ |
| 3 | scripts/foundation/init-db.sql (PostgreSQL 초기화) | ☑ |
| 4 | scripts/foundation/healthcheck-all.sh (통합 헬스체크) | ☑ |
| 5 | dags/healthcheck_dag.py (Airflow 검증 DAG) | ☑ |
| 6 | 장애 테스트 결과 기록 | ☑ |
| 7 | README.md (환경 문서) | ☑ |
| 8 | Git 초기 커밋 | ☑ |

## 포트 맵 요약

| 포트 | 서비스 |
|------|--------|
| 5432 | PostgreSQL |
| 6379 | Redis |
| 30092 | Kafka (외부 접속) |
| 8080 | NiFi |
| 8081 | Flink Dashboard |
| 8082 | Spark Master UI |
| 8083 | Airflow |

## Week 2 예고

Week 2에서는 이 환경 위에서 Kafka 심화 실습을 진행한다. 토픽 설계 전략, 파티션 키 기반 메시지 라우팅, 컨슈머 그룹 관리, 오프셋 수동 커밋, 복제 설정 등을 다룬다. Day 4에서 만든 `nexuspay-transactions` 토픽을 확장하여 실제 금융 거래 시나리오를 구현한다.
