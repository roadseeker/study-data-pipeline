# 04_Kafka MCP 서버 PoC 구현 계획서

## 1. 문서 목적

이 문서는 [03_Kafka MCP 서버 상세 설계서](/c:/Users/roadseeker/study/study-data-pipeline/docs/reports/03_Kafka%20MCP%20서버%20상세%20설계서.md)의 실행 계획 문서로, Kafka MCP 서버의 PoC를 실제로 구현하기 위한 작업 범위, 단계별 일정, 파일 구조, 테스트 시나리오, 완료 기준을 정리한다.

이 문서의 목적은 "설계"를 "즉시 착수 가능한 개발 계획"으로 전환하는 것이다.

## 2. PoC 목표

Kafka MCP PoC의 목표는 다음과 같다.

- Kafka 3-브로커 KRaft 참조 환경 상태를 읽기 전용으로 조회할 수 있다
- AI가 Kafka 상태를 해석하기 쉬운 공통 응답 포맷을 제공한다
- 현재 lab에서 검증한 운영 시나리오를 MCP 도구로 재현할 수 있다
- 이후 LibreChat, Open WebUI, OpenClaw와 연결 가능한 형태로 서버를 준비한다

PoC 범위는 `운영 가시성 확보`에 집중한다. 제어 기능은 제외한다.

## 3. PoC 범위

### 3-1. 포함 범위

다음 8개 도구를 구현한다.

1. `get_cluster_health`
2. `list_topics`
3. `describe_topic`
4. `list_consumer_groups`
5. `describe_consumer_group`
6. `get_topic_offsets`
7. `get_partition_leaders`
8. `get_under_replicated_partitions`

### 3-2. 제외 범위

다음 기능은 PoC에서 제외한다.

- 토픽 생성/삭제
- 토픽 설정 변경
- consumer offset reset
- leader rebalance 실행
- 브로커 재시작 자동화
- 승인형 제어 기능

## 4. 참조 환경

PoC는 현재 저장소의 Kafka 환경을 참조 환경으로 사용한다.

- `lab-kafka-1`
- `lab-kafka-2`
- `lab-kafka-3`
- `localhost:30092,30093,30094`

운영 기준:

- RF=3
- min.ISR=2
- acks=all

검증용 예시 토픽:

- `nexuspay.transactions.payment`
- `nexuspay.transactions.transfer`
- `nexuspay.transactions.withdrawal`

주의:

이 토픽명은 PoC 검증용 예시일 뿐이며, Kafka MCP 구현 자체는 특정 프로젝트명에 종속되지 않아야 한다.

## 5. 구현 전략

### 5-1. 기본 접근

PoC는 Python 기반으로 구현한다.

이유:

- 구조화된 응답 생성이 쉬움
- 테스트 작성이 쉬움
- MCP Python 생태계와 결합이 자연스러움

### 5-2. 데이터 조회 방식

권장 방식은 혼합형이다.

- 기본 메타데이터 조회: Python Kafka client
- consumer group / lag / 일부 운영 정보: Kafka CLI 보조

즉 PoC에서는 정확성과 개발 속도를 우선하고, 순수 Python-only 구현은 후속 단계에서 정리해도 된다.

### 5-3. 설계 원칙

- 읽기 전용만 구현
- 공통 응답 포맷 사용
- 정상/주의/위험 상태를 함께 반환
- 문자열 파싱은 최소화
- 장애 시나리오를 테스트에 포함

## 6. 제안 기술 스택

| 항목 | 제안 |
|------|------|
| 언어 | Python 3.11+ |
| 패키지 관리 | `pyproject.toml` |
| Kafka 조회 | `confluent-kafka` 또는 `kafka-python` |
| MCP 서버 구현 | Python MCP SDK 또는 경량 자체 구현 |
| 테스트 | `pytest` |
| 포맷팅 | `ruff`, `black` 또는 팀 표준 |
| 실행 환경 | 로컬 + Docker Compose Kafka 참조 클러스터 |

## 7. 제안 디렉터리 구조

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
        common.py
        health.py
        topic.py
        group.py
      utils/
        normalize.py
        parsing.py
        severity.py
    tests/
      test_cluster.py
      test_topics.py
      test_groups.py
      test_severity.py
```

## 8. 구현 작업 분해

### 8-1. 작업 1: 프로젝트 스캐폴드

산출물:

- `mcp/kafka-server/`
- `pyproject.toml`
- 기본 README
- 실행 엔트리포인트

완료 기준:

- 가상환경 설치 가능
- 테스트 프레임워크 구동 가능

### 8-2. 작업 2: 설정 계층

구현 항목:

- bootstrap server 환경변수
- timeout 설정
- 보안 프로토콜 옵션 기본값

산출물:

- `config.py`

완료 기준:

- 환경변수 기반 연결 정보 주입 가능

### 8-3. 작업 3: 공통 응답 포맷

구현 항목:

- 정상화 함수
- 상태 판정 enum
- 공통 오류 응답

산출물:

- `models/common.py`
- `utils/normalize.py`
- `utils/severity.py`

완료 기준:

- 모든 도구가 동일한 상위 포맷 반환

### 8-4. 작업 4: 클러스터/토픽 조회 도구

구현 항목:

- `get_cluster_health`
- `list_topics`
- `describe_topic`
- `get_partition_leaders`
- `get_under_replicated_partitions`

산출물:

- `tools/cluster.py`
- `tools/topics.py`

완료 기준:

- 토픽 / leader / ISR 상태를 읽을 수 있음
- 상태를 `healthy`, `degraded`, `critical`로 판정 가능

### 8-5. 작업 5: consumer group 조회 도구

구현 항목:

- `list_consumer_groups`
- `describe_consumer_group`
- `get_topic_offsets`

산출물:

- `tools/groups.py`
- `clients/cli_client.py`

완료 기준:

- 그룹 목록, lag, offset을 조회할 수 있음

### 8-6. 작업 6: MCP 도구 등록

구현 항목:

- 각 함수의 MCP tool 등록
- 입력/출력 스키마 정의

산출물:

- `server.py`

완료 기준:

- 외부 MCP 클라이언트가 도구 목록을 인식 가능

### 8-7. 작업 7: 테스트 작성

구현 항목:

- 단위 테스트
- 통합 테스트
- 장애 시나리오 테스트 문서화

산출물:

- `tests/`

완료 기준:

- 주요 응답 구조와 상태 판정 로직 검증 가능

## 9. 단계별 일정

### 9-1. Day 1

- 스캐폴드 생성
- 설정 계층 구성
- 공통 응답 모델 작성
- `list_topics` 구현

### 9-2. Day 2

- `describe_topic`
- `get_partition_leaders`
- `get_cluster_health`

### 9-3. Day 3

- `get_under_replicated_partitions`
- severity 규칙 정교화
- leader / ISR 해석 로직 추가

### 9-4. Day 4

- `list_consumer_groups`
- `describe_consumer_group`
- `get_topic_offsets`

### 9-5. Day 5

- MCP 등록 마무리
- 단위 테스트
- README 초안 작성

### 9-6. Day 6

- 통합 테스트
- 장애 시나리오 재현
- 응답 품질 보정

### 9-7. Day 7

- 데모 리허설
- 문서 정리
- 상위 인터페이스 연동 준비 메모 작성

## 10. 테스트 시나리오

### 10-1. 시나리오 A: 정상 상태

조건:

- 3브로커 모두 정상
- 예시 토픽 ISR 3/3

검증:

- `get_cluster_health` -> `healthy`
- `describe_topic(...)` -> `healthy`
- `get_partition_leaders` -> broker별 leader 분산 표시

### 10-2. 시나리오 B: 브로커 1대 장애

조건:

- 예: `lab-kafka-2` 중지

검증:

- `get_cluster_health` -> `degraded`
- `describe_topic(...)` -> ISR 감소 반영
- `get_under_replicated_partitions` -> affected partition 표시

### 10-3. 시나리오 C: ISR 부족

조건:

- 2대 장애 또는 특정 토픽 ISR 1

검증:

- 상태가 `critical`로 판정
- 요약 메시지에 "쓰기 안전성 부족" 표현 포함

### 10-4. 시나리오 D: consumer lag 조회

조건:

- 컨슈머 그룹 실행

검증:

- `list_consumer_groups` 결과 반환
- `describe_consumer_group`에 lag 필드 포함

## 11. 응답 포맷 초안

### 11-1. 정상 응답 예시

```json
{
  "system": "kafka",
  "resource_type": "cluster",
  "resource_name": "reference-kafka-lab",
  "status": "healthy",
  "summary": "3 brokers available, 0 under-replicated partitions",
  "details": {
    "broker_count": 3,
    "available_brokers": 3,
    "under_replicated_partitions": 0
  }
}
```

### 11-2. 장애 응답 예시

```json
{
  "system": "kafka",
  "resource_type": "topic",
  "resource_name": "transactions.standardized",
  "status": "degraded",
  "summary": "ISR reduced on 2 partitions after broker failure",
  "details": {
    "replication_factor": 3,
    "affected_partitions": [1, 3]
  }
}
```

## 12. README에 포함할 내용

PoC README에는 최소한 아래 내용을 포함한다.

- 목적
- 요구 패키지
- 환경변수 설정
- 로컬 실행 방법
- 테스트 실행 방법
- 도구 목록
- 예시 질의/응답
- 현재 한계

## 13. PoC 데모 시나리오

데모는 아래 순서로 구성하는 것이 좋다.

1. Kafka 클러스터 정상 상태 조회
2. 특정 토픽 상세 조회
3. consumer group lag 조회
4. 브로커 1대 중지
5. `get_cluster_health` 재호출
6. under-replicated partition 조회
7. 상태 해석 결과를 AI가 설명

이 데모가 성립하면 "Kafka MCP를 통해 AI 운영 분석이 가능하다"는 메시지를 충분히 전달할 수 있다.

## 14. 완료 기준

다음 조건을 모두 만족하면 Kafka MCP PoC 완료로 본다.

- 8개 핵심 도구 구현 완료
- 정상 / 장애 상태 판정 가능
- 단위 테스트 및 최소 통합 테스트 통과
- README 작성 완료
- 데모 시나리오 재현 가능

## 15. 예상 리스크

### 15-1. 구현 리스크

- Kafka client와 CLI 결과 차이
- consumer group lag 수집 난이도
- Windows/Git Bash/PowerShell 환경 차이

### 15-2. 대응

- CLI 의존 최소화
- 문자열 파싱을 별도 모듈로 격리
- 운영 환경용과 참조 환경용 설정 분리

## 16. PoC 이후 다음 단계

Kafka MCP PoC 완료 후 다음 단계는 다음과 같다.

1. LibreChat 또는 Open WebUI 연결 준비
2. HTTP 브리지 여부 결정
3. OpenClaw 호출 시나리오 시범 구축
4. `get_cluster_diagnostics` 같은 고수준 진단 도구 추가
5. Airflow MCP 착수

## 17. 최종 제안

Kafka MCP PoC는 1주일 내외의 집중 작업으로 충분히 데모 가능한 수준에 도달할 수 있다. 핵심은 기능 수를 넓히기보다 `상태를 잘 읽고, 의미 있게 해석하는 것`에 집중하는 것이다.

PoC의 성공 조건은 단순한 API 개수보다 다음에 있다.

- 장애 상태를 올바르게 감지하는가
- AI가 운영자에게 설명 가능한 수준의 요약을 제공하는가
- 이후 LibreChat, Open WebUI, OpenClaw로 자연스럽게 확장 가능한 구조인가

이 기준을 만족하면 Kafka MCP 서버는 범용 AI 데이터파이프라인 플랫폼의 첫 번째 실전 운영 자산이 된다.
