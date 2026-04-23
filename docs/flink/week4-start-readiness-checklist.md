# Nexus Pay Week 4 시작 전 준비 점검 체크리스트

## 문서 목적

이 문서는 Week 3에서 구축한 NiFi 기반 수집 파이프라인을 Week 4 Flink 실시간 처리 단계로 안전하게 인계하기 전에 반드시 확인해야 할 기준선을 정리한 준비 점검 문서다.

목표는 다음 두 가지다.

- Week 4 착수 전에 인프라 상태와 데이터 인계 상태를 분리해 확인한다.
- Flink 개발 시작 후 문제가 발생했을 때 수집 계층 문제와 변환 계층 문제를 빠르게 구분할 수 있도록 기준선을 남긴다.

## 적용 범위

- 브랜치: `week4-flink`
- 인계 경로: NiFi -> Kafka -> Flink
- 대상 서비스: PostgreSQL, Redis, Kafka, NiFi, Flink, Spark, Airflow
- 시나리오: Nexus Pay 실시간 이벤트를 `nexuspay.events.ingested`에서 소비해 Flink 윈도우 집계와 이상거래 탐지를 시작하기 전 준비 상태 확인

## 현재 준비 배경

Week 3 종료 시점에 NiFi 웹 UI는 정상 접속 가능했지만 Docker healthcheck는 실패하는 문제가 있었다. 원인은 secure mode에서 `nifi.web.https.host`가 컨테이너 호스트명으로 설정되어 컨테이너 내부 `https://localhost:8443/nifi/` 헬스체크가 실패한 것이었다.

Week 4 착수 전 이 이슈는 다음 기준으로 정상화되었다.

- `nifi.web.https.host=0.0.0.0`
- 컨테이너 내부 `curl https://localhost:8443/nifi/` 결과 `HTTP:200 EXIT:0`
- `docker inspect lab-nifi --format '{{json .State.Health}}'` 결과 `healthy`

## 시작 전 점검 항목

| 구분 | 점검 항목 | 기대 상태 | 확인 방법 |
|------|-----------|-----------|-----------|
| 저장소 | 현재 브랜치 | `week4-flink` | `git branch --show-current` |
| 저장소 | 작업 트리 상태 | Week 4 준비용 의도된 변경만 존재 | `git status --short` |
| 컨테이너 | 핵심 서비스 기동 상태 | 주요 서비스가 `Up` 또는 `healthy` | `docker ps --format "table {{.Names}}\t{{.Status}}"` |
| NiFi | Web UI 접근 | `https://localhost:8443/nifi/` 접속 가능 | 브라우저 또는 `curl -skI https://localhost:8443/nifi/` |
| NiFi | Docker healthcheck | `healthy` | `docker inspect lab-nifi --format '{{.State.Health.Status}}'` |
| NiFi | HTTPS bind 설정 | `nifi.web.https.host=0.0.0.0` | `docker exec lab-nifi sh -lc 'grep -E "^nifi.web.https.host=|^nifi.web.proxy.host=" /opt/nifi/nifi-current/conf/nifi.properties'` |
| Kafka | Week 3 입력 토픽 | `nexuspay.events.ingested`, `nexuspay.events.dlq` 존재 | `kafka-topics.sh --describe` |
| Kafka | 입력 이벤트 확인 | 샘플 이벤트 1건 이상 조회 가능 | `kafka-console-consumer.sh --max-messages 5` |
| Flink | 클러스터 기준선 | `taskmanagers=1`, `slots-total=4`, `jobs-running=0` | `curl -s http://localhost:8081/overview` |
| Flink | 출력 경로 준비 | `data/flink/usrlib`, `data/flink/checkpoints`, `data/flink/savepoints` 존재 | `ls -la data/flink` |
| Flink | 배포용 JAR 준비 | `data/flink/usrlib/flink-jobs-1.0.0.jar` 확인 가능 | `ls -la data/flink/usrlib` |
| Kafka | Week 4 출력 토픽 | 집계·알림 토픽 존재 | `kafka-topics.sh --describe` |
| 운영 보조 | Spark / Airflow 상태 | 접근 가능 또는 healthy | `curl -s http://localhost:8082/`, `curl -s http://localhost:8083/health` |

## 핵심 확인 명령

```bash
git branch --show-current
git status --short
docker ps --format "table {{.Names}}\t{{.Status}}"
```

```bash
docker inspect lab-nifi --format '{{.State.Health.Status}}'
docker exec lab-nifi sh -lc 'grep -E "^nifi.web.https.host=|^nifi.web.https.port=|^nifi.web.proxy.host=" /opt/nifi/nifi-current/conf/nifi.properties'
docker exec lab-nifi sh -lc 'curl -skI -o /dev/null -w "HTTP:%{http_code} EXIT:%{exitcode}\n" https://localhost:8443/nifi/'
```

```bash
docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka-1:9092 --describe --topic nexuspay.events.ingested
docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka-1:9092 --describe --topic nexuspay.events.dlq
docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka-1:9092 \
  --topic nexuspay.events.ingested \
  --from-beginning \
  --timeout-ms 10000 \
  --max-messages 5
```

```bash
curl -s http://localhost:8081/overview
curl -s http://localhost:8082/
curl -s http://localhost:8083/health
```

## Week 4 출력 토픽 준비 확인

Week 4에서 Flink가 생성할 주요 출력 토픽은 아래와 같다.

| 토픽명 | 목적 |
|--------|------|
| `nexuspay.aggregation.5min` | 5분 Tumbling Window 집계 결과 |
| `nexuspay.aggregation.sliding` | Sliding Window 집계 결과 |
| `nexuspay.alerts.fraud` | 이상거래 탐지 알림 |

확인 명령:

```bash
docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka-1:9092 --describe --topic nexuspay.aggregation.5min
docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka-1:9092 --describe --topic nexuspay.aggregation.sliding
docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka-1:9092 --describe --topic nexuspay.alerts.fraud
```

## Go / No-Go 기준

### Go

- `lab-nifi`가 `healthy`이고 내부 HTTPS healthcheck가 성공한다.
- `nexuspay.events.ingested` 토픽에서 Week 3 표준화 이벤트를 조회할 수 있다.
- Flink overview 값이 `taskmanagers=1`, `slots-total=4`, `jobs-running=0` 기준선을 만족한다.
- Week 4 출력 토픽과 JAR·체크포인트 저장 경로가 준비되어 있다.
- 작업 트리에 의도하지 않은 변경이 없다.

### No-Go

- NiFi가 `unhealthy`이거나 내부 `localhost:8443` 헬스체크가 실패한다.
- Kafka 입력 토픽이 없거나 샘플 이벤트가 조회되지 않는다.
- Flink 클러스터가 비정상 상태이거나 이미 실행 중인 잡이 남아 있다.
- 출력 토픽 또는 JAR·체크포인트 경로가 준비되지 않았다.
- 환경 수정 이력이 있으나 반영 결과가 검증되지 않았다.

## 운영 권고

Week 4 첫 작업은 Flink 코드 작성보다 기준선 검증 결과를 먼저 남기는 것이다. 특히 NiFi healthcheck 정상화 결과와 Kafka 입력 토픽 확인 결과를 기록해 두면, 이후 Flink 잡 실행 실패 시 수집 계층과 변환 계층을 빠르게 분리해서 대응할 수 있다.
