# 03_Kafka MCP 서버 상세 설계서

## 1. 문서 목적

이 문서는 [02_MCP 서버 우선 구현 로드맵](/c:/Users/roadseeker/study/study-data-pipeline/docs/reports/02_MCP%20서버%20우선%20구현%20로드맵.md)의 후속 상세 설계 문서로, `범용 오픈소스 AI 데이터파이프라인 플랫폼`에서 가장 먼저 구현할 `Kafka MCP 서버`의 목표, 기능 범위, 내부 구조, 안전 정책, 검증 기준을 구체화한다.

Kafka MCP 서버의 목적은 단순 상태 조회가 아니라, AI가 Kafka 클러스터를 표준화된 방식으로 이해하고 운영 질의에 답할 수 있는 공통 인터페이스를 제공하는 것이다.

## 2. 대상 환경과 범용성 전제

이 문서는 현재 저장소의 Kafka 3-브로커 KRaft 구성을 참조 환경으로 사용한다.

참조 환경:

- `lab-kafka-1`
- `lab-kafka-2`
- `lab-kafka-3`
- 외부 포트:
  - `localhost:30092`
  - `localhost:30093`
  - `localhost:30094`
- 운영 원칙:
  - `replication.factor=3`
  - `min.insync.replicas=2`
  - `acks=all`
  - `auto.create.topics.enable=false`

하지만 Kafka MCP 설계 자체는 특정 프로젝트명이나 특정 토픽명에 종속되지 않아야 한다.

즉, 현재 lab의 `nexuspay.*` 토픽은 검증 예시일 뿐이며, Kafka MCP는 어떤 고객 환경의 어떤 토픽명에도 적용 가능한 구조로 설계해야 한다.

## 3. Kafka MCP 서버의 목표

### 3-1. 1차 목표

- Kafka 운영 상태의 읽기 전용 표준 인터페이스 제공
- AI가 클러스터 상태, 토픽 상태, 리더 분산, ISR, consumer lag를 설명할 수 있게 함
- OpenClaw, LibreChat, Open WebUI가 공통 방식으로 Kafka 상태를 조회할 수 있게 함

### 3-2. 2차 목표

- 장애 상황에서 운영자가 묻는 질문에 근거 기반 답변 제공

예:

- "왜 producer 전송이 실패했는가"
- "현재 under-replicated partition이 있는가"
- "consumer lag가 큰 그룹은 무엇인가"
- "어떤 브로커가 leader를 과도하게 맡고 있는가"

### 3-3. 3차 목표

- 추후 승인형 제어 기능을 넣을 수 있도록 내부 구조를 분리
- 단, 초기 버전은 읽기 전용으로 제한

## 4. 설계 원칙

### 4-1. 읽기 전용 우선

초기 Kafka MCP는 읽기 전용으로 구현한다.

이유:

- 잘못된 제어가 클러스터 안정성을 해칠 수 있음
- 운영 상태 가시성만으로도 높은 가치가 있음
- 상위 UI 연결 전 테스트가 쉬움

### 4-2. 두 계층 접근

Kafka MCP는 내부적으로 두 가지 접근 방식을 함께 고려한다.

- Python Kafka Admin Client 기반 조회
- Kafka CLI 기반 보조 조회

권장 방안:

- 기본 조회는 Python 기반
- 필요한 일부 정보는 CLI 보조 사용

### 4-3. 표준 응답 포맷

모든 도구는 가능한 한 공통 구조를 따른다.

예시:

```json
{
  "system": "kafka",
  "resource_type": "topic",
  "resource_name": "transactions.standardized",
  "status": "healthy",
  "summary": "6 partitions, RF=3, ISR normal",
  "details": {}
}
```

### 4-4. 진단 우선

Kafka MCP는 원시 데이터를 단순 출력하는 수준을 넘어서 운영 해석을 함께 제공해야 한다.

예:

- ISR이 RF와 같으면 `healthy`
- ISR이 감소했지만 leader가 존재하면 `degraded`
- leader 없는 partition이 있으면 `critical`
- leader가 한 브로커에 과도하게 몰리면 `imbalanced`

## 5. 기능 범위

### 5-1. PoC 범위

Kafka MCP PoC는 다음 8개 도구를 최소 범위로 한다.

1. `get_cluster_health`
2. `list_topics`
3. `describe_topic`
4. `list_consumer_groups`
5. `describe_consumer_group`
6. `get_topic_offsets`
7. `get_partition_leaders`
8. `get_under_replicated_partitions`

### 5-2. MVP 확장 범위

PoC 이후 아래 도구를 추가한다.

9. `get_broker_overview`
10. `get_leader_distribution`
11. `get_isr_summary`
12. `find_unavailable_partitions`
13. `get_topic_config`
14. `get_cluster_diagnostics`

### 5-3. 후기 제어형 범위

승인형으로만 도입 가능한 기능:

- `create_topic`
- `alter_topic_config`
- `reset_consumer_offsets`
- `rebalance_recommendation`

초기에는 구현하지 않는다.

## 6. 도구별 상세 설계

### 6-1. `get_cluster_health`

목적:

- 클러스터 전체 상태를 한 번에 요약

출력:

- 브로커 수
- 사용 가능한 브로커 수
- 토픽 수
- under-replicated partition 수
- leader 없는 partition 수
- 상태 등급

### 6-2. `list_topics`

목적:

- 전체 토픽 목록과 기본 메타데이터 조회

출력:

- 토픽명
- 파티션 수
- replication factor
- 내부 토픽 여부

### 6-3. `describe_topic`

목적:

- 특정 토픽의 파티션, leader, replicas, ISR 상태 확인

출력:

- 토픽명
- 파티션 수
- replication factor
- partition별 leader
- replicas
- ISR
- `min.insync.replicas`
- 상태 해석

### 6-4. `list_consumer_groups`

목적:

- 현재 클러스터의 consumer group 목록 조회

출력:

- 그룹명
- 상태
- 프로토콜
- member 수

### 6-5. `describe_consumer_group`

목적:

- 특정 컨슈머 그룹의 lag와 파티션 할당 상태 분석

출력:

- group id
- topic/partition
- current offset
- log end offset
- lag
- consumer id
- host
- client id
- 상태 요약

### 6-6. `get_topic_offsets`

목적:

- 토픽별 파티션 offset 상태 조회

출력:

- partition별 latest offset
- partition 간 편차
- 요약 정보

### 6-7. `get_partition_leaders`

목적:

- leader broker 분포 확인

출력:

- partition별 leader
- broker별 leader 수
- leader 편중 여부

### 6-8. `get_under_replicated_partitions`

목적:

- ISR이 RF보다 작은 파티션 집중 조회

출력:

- topic
- partition
- leader
- replicas
- ISR
- 심각도

## 7. 내부 구현 구조

### 7-1. 권장 디렉터리 구조

```text
mcp/
  kafka-server/
    README.md
    pyproject.toml
    src/
      server.py
      config.py
      clients/
        admin_client.py
        cli_client.py
      tools/
        cluster.py
        topics.py
        groups.py
        diagnostics.py
      models/
        health.py
        topic.py
        group.py
      utils/
        normalize.py
        severity.py
        parsing.py
    tests/
      test_cluster.py
      test_topics.py
      test_groups.py
```

### 7-2. 모듈 역할

| 모듈 | 역할 |
|------|------|
| `config.py` | bootstrap server, timeout, 인증 옵션 |
| `admin_client.py` | Python Kafka Admin Client 호출 |
| `cli_client.py` | CLI 보조 호출 |
| `cluster.py` | 클러스터 상태 관련 도구 |
| `topics.py` | topic/partition/ISR 관련 도구 |
| `groups.py` | consumer group/lag 관련 도구 |
| `diagnostics.py` | 고수준 진단 도구 |
| `normalize.py` | 공통 응답 구조 생성 |
| `severity.py` | healthy/degraded/critical 규칙 |

## 8. 구현 방식 비교

### 8-1. Python Admin Client 기반

장점:

- 구조화된 데이터 접근이 쉬움
- 문자열 파싱 의존도가 낮음
- 테스트 작성이 쉬움

단점:

- consumer group lag 등 일부 정보는 별도 처리 필요
- Kafka 버전 차이에 따라 제한 있을 수 있음

### 8-2. CLI 래핑 기반

장점:

- Kafka CLI가 제공하는 운영 정보가 풍부함
- 현재 참조 환경의 운영 가이드와 일치

단점:

- 문자열 파싱이 취약함
- 출력 형식 변경 리스크가 있음

### 8-3. 권장 결론

- 기본 구현은 Python Admin Client 기반
- 일부 운영 정보는 CLI 보조 사용
- `diagnostics` 계층에서 두 결과를 통합

## 9. 인증 및 연결 정책

현재 참조 환경은 PLAINTEXT 기반이다.

초기 설정:

- `bootstrap.servers=localhost:30092,localhost:30093,localhost:30094`
- 인증 없음

향후 확장:

- SASL/SSL 설정 옵션 구조화
- 환경변수 기반 secret 주입

예시 환경변수:

```text
KAFKA_BOOTSTRAP_SERVERS=localhost:30092,localhost:30093,localhost:30094
KAFKA_SECURITY_PROTOCOL=PLAINTEXT
KAFKA_REQUEST_TIMEOUT_MS=5000
```

## 10. 상태 해석 규칙

### 10-1. 클러스터 상태

| 조건 | 상태 |
|------|------|
| 모든 브로커 정상, URP=0 | healthy |
| 브로커 일부 장애, ISR 감소 | degraded |
| leader 없는 partition 존재 | critical |

### 10-2. 토픽 상태

| 조건 | 상태 |
|------|------|
| 모든 파티션 ISR=RF | healthy |
| 일부 ISR<RF, leader 있음 | degraded |
| leader 없음 | critical |

### 10-3. consumer group 상태

| 조건 | 상태 |
|------|------|
| lag 낮음, partition 정상 할당 | healthy |
| lag 높음 | degraded |
| member 없음 또는 partition 매핑 이상 | critical |

## 11. 운영 질문 예시

Kafka MCP가 답할 수 있어야 하는 대표 질문은 다음과 같다.

- 현재 Kafka 클러스터는 정상인가
- 어떤 토픽의 ISR이 줄었는가
- 리더가 한 브로커에 몰려 있는가
- consumer lag가 가장 큰 그룹은 무엇인가
- 특정 토픽의 replication factor와 min.insync.replicas는 얼마인가
- 현재 producer 실패 원인이 ISR 부족 때문인가

## 12. 상위 인터페이스 연계 시나리오

### 12-1. LibreChat / Open WebUI

대화형 UI에서 Kafka MCP를 붙이면 다음과 같은 질의가 가능하다.

- "현재 Kafka 클러스터 상태를 요약해줘"
- "특정 토픽의 leader 분산이 고른가"
- "최근 consumer lag가 가장 큰 그룹은 무엇인가"
- "브로커 1대 장애 시 현재 쓰기가 가능한 상태인가"

### 12-2. OpenClaw

OpenClaw에서 Kafka MCP를 붙이면 다음과 같은 실행 보조가 가능하다.

- 상태를 요약해 다음 점검 순서 제안
- producer 실패 원인을 해석하고 검증 명령 제시
- 다른 MCP와 함께 end-to-end 진단 계획 생성

## 13. 테스트 전략

### 13-1. 단위 테스트

- 응답 정규화 함수
- 상태 판정 함수
- leader 분산 계산 함수
- lag 임계치 판정 함수

### 13-2. 통합 테스트

- 토픽 생성 후 `describe_topic`
- consumer group 생성 후 `describe_consumer_group`
- 브로커 1대 중지 후 `get_cluster_health`
- ISR 감소 시 `get_under_replicated_partitions`

### 13-3. 시나리오 테스트

- 정상 상태: `healthy`
- 1대 장애: `degraded`
- 2대 장애 또는 leader 손실: `critical`

## 14. PoC 일정

### 14-1. 1주차

- 서버 스캐폴드 구성
- config, normalize, severity 모듈 작성
- `get_cluster_health`
- `list_topics`
- `describe_topic`

### 14-2. 2주차

- `list_consumer_groups`
- `describe_consumer_group`
- `get_partition_leaders`
- `get_under_replicated_partitions`
- 통합 테스트 작성

### 14-3. PoC 완료 기준

- 8개 핵심 도구 동작
- 정상/장애 상태를 healthy/degraded/critical로 구분
- LibreChat, Open WebUI, 또는 OpenClaw에서 호출 가능한 구조 확보
- 운영자가 결과를 읽고 다음 행동을 판단할 수 있을 수준의 요약 제공

## 15. 리스크와 대응

### 리스크

- CLI 출력 형식 변경에 따른 파싱 불안정
- consumer group lag 계산 복잡도
- 브로커 일시 장애 시 false positive 발생
- KRaft 환경 메타데이터 차이에 따른 해석 차이

### 대응

- 문자열 파싱 최소화
- Python client 우선 사용
- timeout, retry, health rule 분리
- 참조 환경 기반 회귀 테스트 확보

## 16. 최종 권고

Kafka MCP 서버는 범용 오픈소스 AI 데이터파이프라인 플랫폼의 첫 번째 MCP 구현 대상으로 적합하다. 운영 가치가 매우 높고, 현재 참조 환경에서 이미 검증된 leader / ISR / lag / 장애 복구 시나리오를 그대로 AI 운영 계층으로 승격시킬 수 있기 때문이다.

권장 순서는 다음과 같다.

1. 읽기 전용 Kafka MCP PoC 구현
2. 대화형 UI 연결 전 로컬 시나리오 테스트
3. LibreChat 또는 Open WebUI 연동
4. OpenClaw 실행 보조 연동
5. 이후 승인형 제어 기능 검토

즉 Kafka MCP는 단순 상태 조회 도구가 아니라, 범용 AI 데이터파이프라인 플랫폼의 첫 번째 실전 운영 자산으로 설계해야 한다.
