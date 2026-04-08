# 02_MCP 서버 우선 구현 로드맵

## 1. 문서 목적

이 문서는 [01_AI 데이터파이프라인 구현 방안](/c:/Users/roadseeker/study/study-data-pipeline/docs/reports/01_AI%20데이터파이프라인%20구현%20방안.md)의 후속 문서로, `범용 오픈소스 AI 데이터파이프라인 플랫폼`을 구축하기 위해 어떤 MCP(Model Context Protocol) 서버를 어떤 순서로 구현해야 하는지 정리한 실행 로드맵이다.

이 문서의 전제는 다음과 같다.

- 플랫폼은 특정 고객이나 특정 도메인에 종속되지 않는다
- 현재 저장소의 Kafka/NiFi/Airflow/Flink/Spark 자산은 `참조 검증 환경`으로 활용한다
- OpenClaw는 상위 실행 콘솔
- LibreChat 또는 Open WebUI는 대화형 운영 인터페이스
- MCP 서버는 각 실행 엔진을 AI가 읽고 다루는 공통 제어 계층

## 2. 결론 요약

가장 현실적인 접근은 모든 시스템을 한 번에 MCP로 만들지 않고, `운영 가치가 높은 읽기 전용 MCP부터 단계적으로 구현`하는 것이다.

권장 우선순위는 다음과 같다.

1. Kafka MCP
2. Airflow MCP
3. NiFi MCP
4. DB MCP
5. Redis MCP
6. Flink MCP
7. Spark MCP

이 순서는 다음 기준을 함께 반영한다.

- 운영 가시성 가치
- 구현 난이도
- 범용 플랫폼 재사용성
- OpenClaw 및 대화형 UI와의 결합 효과
- 향후 승인형 제어 기능으로의 확장성

## 3. 왜 MCP 서버부터 구현해야 하는가

MCP 서버는 AI가 Kafka, NiFi, Airflow, Flink, Spark, DB, Redis 같은 시스템을 공통된 방식으로 이해하게 만드는 표준 인터페이스다.

MCP 서버를 먼저 구축하면 다음이 가능해진다.

- OpenClaw가 각 시스템을 동일한 도구 모델로 호출
- LibreChat / Open WebUI가 상태 질의와 설명에 MCP를 활용
- 향후 Admin Portal이 생겨도 같은 백엔드를 재사용
- 시스템별 API, CLI, 인증 차이를 MCP 내부에 캡슐화

즉 MCP는 부가 기능이 아니라 AI 운영 자동화의 핵심 기반 계층이다.

## 4. 우선순위 선정 기준

### 4-1. 평가 기준

| 기준 | 설명 |
|------|------|
| 운영 가치 | 장애 진단, 상태 확인, 운영 설명에 얼마나 직접 기여하는가 |
| 구현 난이도 | API 품질, 인증 복잡도, 상태 모델 난이도 |
| 범용성 | 다른 고객 환경에도 재사용 가능한가 |
| 상위 인터페이스 연계 | OpenClaw, LibreChat, Open WebUI와 자연스럽게 연결되는가 |
| 확장성 | 승인형 제어 기능으로 확장하기 쉬운가 |

### 4-2. 시스템별 평가

| 시스템 | 운영 가치 | 구현 난이도 | 범용성 | 초기 우선순위 |
|------|----------|------------|--------|--------------|
| Kafka | 매우 높음 | 중간 | 매우 높음 | 1 |
| Airflow | 높음 | 낮음~중간 | 높음 | 2 |
| NiFi | 높음 | 중간 | 높음 | 3 |
| DB | 높음 | 낮음 | 매우 높음 | 4 |
| Redis | 중간 | 낮음 | 높음 | 5 |
| Flink | 중간 | 낮음~중간 | 높음 | 6 |
| Spark | 중간 | 중간 | 높음 | 7 |

## 5. 단계별 구현 전략

### 5-1. 단계 1: 운영 가시성 PoC

목표:

- 읽기 전용 MCP 서버를 우선 구현
- AI가 각 시스템 상태를 정확히 읽고 설명할 수 있게 함
- 제어 기능은 아직 넣지 않음

대상:

- Kafka MCP
- Airflow MCP
- NiFi MCP

핵심 효과:

- "어디가 병목인가", "왜 실패했는가"를 AI가 근거와 함께 설명할 수 있게 됨

### 5-2. 단계 2: 데이터 상태 계층 확장

목표:

- DB와 Redis까지 상태 계층을 확장
- 파이프라인 입출력과 런타임 상태를 함께 볼 수 있게 함

대상:

- DB MCP
- Redis MCP

핵심 효과:

- 메시지 버스 상태뿐 아니라 실제 적재 결과와 실행 상태를 함께 검증 가능

### 5-3. 단계 3: 처리 엔진 확장

목표:

- Flink와 Spark를 포함해 실시간/배치 처리 엔진까지 MCP 범위를 확대

대상:

- Flink MCP
- Spark MCP

핵심 효과:

- 전체 데이터파이프라인을 end-to-end로 AI가 이해할 수 있게 됨

### 5-4. 단계 4: 상위 인터페이스 연결

목표:

- OpenClaw 연결
- LibreChat 또는 Open WebUI 연결
- 필요 시 HTTP/OpenAPI 브리지 추가

핵심 효과:

- 운영자는 대화형으로 상태를 묻고
- OpenClaw는 spec 생성, 도구 호출, 실행 계획 수립까지 담당할 수 있음

## 6. 시스템별 MCP 서버 설계 방향

### 6-1. Kafka MCP

목표:

- 토픽, ISR, leader, consumer lag, 클러스터 상태를 읽는 표준 계층 제공

최소 기능:

- `get_cluster_health`
- `list_topics`
- `describe_topic`
- `list_consumer_groups`
- `describe_consumer_group`
- `get_topic_offsets`
- `get_partition_leaders`
- `get_under_replicated_partitions`

우선 구현 이유:

- 이벤트 버스 중심 계층
- 장애와 성능 이상 징후가 가장 빠르게 드러남

### 6-2. Airflow MCP

목표:

- 오케스트레이션 상태, 실패 DAG, 최근 실행 상태를 읽는 계층 제공

최소 기능:

- `list_dags`
- `get_dag`
- `list_dag_runs`
- `get_dag_run`
- `list_failed_tasks`
- `get_recent_failures`

우선 구현 이유:

- REST API 품질이 높고 빠르게 가치가 나옴

### 6-3. NiFi MCP

목표:

- process group, processor, queue backlog, bulletin, provenance 요약을 읽는 계층 제공

최소 기능:

- `list_process_groups`
- `get_process_group_status`
- `list_processors`
- `get_processor_status`
- `get_queue_backlog`
- `list_bulletins`
- `get_provenance_summary`

우선 구현 이유:

- 수집 파이프라인 병목과 오류를 운영자가 가장 자주 확인해야 하는 계층

### 6-4. DB MCP

목표:

- 소스/타겟 테이블 상태와 적재 결과를 읽는 계층 제공

최소 기능:

- `list_tables`
- `describe_table`
- `get_row_count`
- `sample_rows`
- `check_primary_key`
- `compare_counts`

### 6-5. Redis MCP

목표:

- 실행 상태, 캐시, 임시 상태 정보를 읽는 계층 제공

최소 기능:

- `get_key`
- `list_keys_by_pattern`
- `get_ttl`
- `get_hash_fields`

### 6-6. Flink MCP

목표:

- job 상태, checkpoint, exception을 읽는 계층 제공

최소 기능:

- `get_cluster_overview`
- `list_jobs`
- `get_job_status`
- `get_job_exceptions`
- `get_checkpoints`
- `list_taskmanagers`

### 6-7. Spark MCP

목표:

- app, job, stage, executor 상태를 읽는 계층 제공

최소 기능:

- `list_applications`
- `get_application`
- `list_jobs`
- `list_stages`
- `get_executor_summary`
- `get_failed_jobs`

## 7. 공통 설계 원칙

### 7-1. 읽기 전용 우선

모든 MCP 서버는 읽기 전용으로 시작한다.

이유:

- 운영 리스크가 낮다
- 응답 구조를 표준화하기 쉽다
- OpenClaw나 대화형 UI 연결 전 테스트가 쉽다
- 승인형 제어를 나중에 얹기 좋다

### 7-2. 공통 응답 포맷

각 MCP 서버는 응답 포맷을 가능한 한 유사하게 맞춘다.

예시:

```json
{
  "system": "kafka",
  "resource": "topic",
  "name": "transactions.standardized",
  "status": "healthy",
  "summary": "...",
  "details": {}
}
```

### 7-3. 승인형 제어

제어 기능은 다음 조건을 만족할 때만 추가한다.

- 영향 범위 설명 가능
- 승인 단계 존재
- 감사 로그 남김
- 롤백 또는 재실행 전략 존재

### 7-4. 브리지 계층 고려

대화형 UI나 향후 외부 시스템 연계를 위해 MCP 외에 HTTP/OpenAPI 브리지를 둘 수 있다.

권장 구조:

- 내부: MCP 서버
- 외부: HTTP/OpenAPI wrapper
- 상위 UI: OpenClaw, LibreChat, Open WebUI

## 8. 상위 인터페이스 연계 시점

### 8-1. LibreChat / Open WebUI 연결 시점

최소 3개 MCP 서버가 안정화된 뒤 연결하는 것이 좋다.

권장 시점:

- Kafka MCP
- Airflow MCP
- NiFi MCP

### 8-2. OpenClaw 연결 시점

OpenClaw는 `MCP 호출 + 실행 계획 제안 + 승인 흐름`이 가능해지려면 최소 다음이 필요하다.

- Kafka MCP
- Airflow MCP
- NiFi MCP
- shell/file 실행 워커
- validation 스크립트

즉 대화형 UI보다 약간 더 뒤에 붙여도 되지만, 플랫폼의 핵심 상위 계층으로는 조기 설계가 필요하다.

## 9. 12주 기준 권장 로드맵

### Phase 1. 1~2주차: Kafka MCP PoC

산출물:

- Kafka MCP 서버 초안
- topic / group / ISR / lag 조회 도구
- 로컬 테스트 스크립트

완료 기준:

- 5개 이상 읽기 전용 도구 동작
- Kafka 장애 상황에서 상태 설명 가능

### Phase 2. 3~4주차: Airflow MCP

산출물:

- Airflow MCP 서버
- DAG / run / failure 조회 도구

완료 기준:

- 특정 DAG 실패 이력 조회 가능
- 최근 실패 task 요약 가능

### Phase 3. 5~6주차: NiFi MCP

산출물:

- NiFi MCP 서버
- process group / processor / queue / bulletin 조회 도구

완료 기준:

- backlog와 bulletin 조회 가능
- 주요 프로세서 상태 설명 가능

### Phase 4. 7주차: DB / Redis MCP

산출물:

- DB MCP 서버
- Redis MCP 서버

완료 기준:

- 적재 결과 row count 확인 가능
- 파이프라인 상태 캐시 조회 가능

### Phase 5. 8~9주차: 대화형 UI 연결

산출물:

- LibreChat 또는 Open WebUI 연동
- Kafka / Airflow / NiFi MCP 연결
- 운영 질의응답 시나리오 5개

완료 기준:

- 자연어 운영 질의에 MCP 도구 호출 성공

### Phase 6. 10~11주차: OpenClaw 실행 콘솔 연결

산출물:

- OpenClaw 연결 설계
- MCP 호출 시나리오
- spec 생성 및 실행 계획 데모

완료 기준:

- OpenClaw가 최소 3개 MCP를 호출해 실행 계획을 제안할 수 있음

### Phase 7. 12주차: Flink / Spark MCP 착수

산출물:

- Flink MCP 초안
- Spark MCP 초안
- 전체 아키텍처 회고 문서

## 10. 산출물 목록

| 단계 | 산출물 |
|------|------|
| Kafka MCP | `mcp/kafka-server/`, 테스트 스크립트, README |
| Airflow MCP | `mcp/airflow-server/`, API 매핑 문서 |
| NiFi MCP | `mcp/nifi-server/`, queue/bulletin 조회 예시 |
| DB MCP | `mcp/db-server/`, SQL 안전정책 문서 |
| Redis MCP | `mcp/redis-server/`, 상태 키 규칙 문서 |
| 대화형 UI 연계 | Compose 확장, MCP 연결 문서 |
| OpenClaw 연계 | 실행 시나리오, spec 예시, 승인 흐름 문서 |

## 11. MVP 완료 기준

다음 조건을 만족하면 MCP MVP가 성립했다고 판단할 수 있다.

- Kafka, Airflow, NiFi 상태를 AI가 조회할 수 있다
- LibreChat 또는 Open WebUI에서 자연어 질의로 MCP를 호출할 수 있다
- DB 적재 결과를 MCP로 검증할 수 있다
- OpenClaw가 최소 일부 MCP를 호출해 실행 계획을 제안할 수 있다
- 장애 상황에서 "어디가 문제인지"를 AI가 근거와 함께 설명할 수 있다

## 12. 권고 사항

- 모든 시스템을 한 번에 구현하지 말 것
- Kafka/Airflow/NiFi를 먼저 묶어 운영 가치가 큰 축부터 완성할 것
- 읽기 전용 MCP를 충분히 안정화한 뒤 제어 기능을 승인형으로 추가할 것
- OpenClaw는 상위 실행 콘솔, LibreChat/Open WebUI는 대화형 운영 인터페이스로 역할을 분리할 것
- 장기적으로는 MCP 서버를 범용 AI 데이터파이프라인 플랫폼의 공통 운영 백엔드로 발전시킬 것

## 13. 최종 제안

범용 오픈소스 AI 데이터파이프라인 플랫폼 기준의 현실적인 구현 전략은 다음과 같다.

- 1차 목표: Kafka + Airflow + NiFi MCP 구축
- 2차 목표: DB/Redis까지 확장하여 입출력과 상태 계층 통합
- 3차 목표: LibreChat 또는 Open WebUI를 붙여 대화형 운영 확보
- 4차 목표: OpenClaw를 붙여 실행 계획과 변경 제안을 수행
- 5차 목표: Flink/Spark까지 포함한 end-to-end AI 운영 체계 완성

이 로드맵을 따르면 단기간에는 운영 가시성 향상과 데모 가능한 오픈소스 AI 운영 콘솔을 만들 수 있고, 중장기적으로는 자연어 기반 데이터파이프라인 자동화 플랫폼으로 확장할 수 있다.
