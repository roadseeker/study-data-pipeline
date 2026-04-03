# Nexus Pay Kafka 토픽 명명 규칙

## 목적

이 문서는 Nexus Pay 데이터 파이프라인에서 사용하는 Kafka 토픽 명명 규칙을 정의한다.  
목표는 다음 세 가지다.

- 비즈니스 도메인과 이벤트 목적이 토픽명만으로 이해되도록 한다.
- 운영·모니터링·장애 대응 시 검색 가능성과 일관성을 높인다.
- Week 2 이후 NiFi, Flink, Spark, Airflow 자산이 동일한 규칙을 공유하도록 한다.

## 기본 형식

`<domain>.<entity>.<event>`

예시:

- `nexuspay.transactions.payment`
- `nexuspay.transactions.transfer`
- `nexuspay.transactions.withdrawal`
- `nexuspay.events.ingested`
- `nexuspay.alerts.fraud`

## 명명 원칙

1. 모든 토픽명은 소문자만 사용한다.
2. 계층 구분은 점(`.`)으로 표현한다.
3. 점(`.`)과 밑줄(`_`)을 혼용하지 않는다. Nexus Pay 토픽은 점(`.`)만 사용한다.
4. 복수형 엔티티를 기본으로 사용한다.
5. 약어보다 의미가 분명한 단어를 우선한다.
6. 토픽명에는 환경명, 날짜, 버전을 직접 넣지 않는다.
7. 파이프라인 단계가 중요한 경우에만 `events`, `alerts`, `aggregation`, `cdc`, `dlq` 같은 목적형 엔티티를 사용한다.

## Kafka 경고 해설

Kafka 토픽 생성 시 아래와 같은 경고가 출력될 수 있다.

`WARNING: Due to limitations in metric names, topics with a period ('.') or underscore ('_') could collide.`

이 경고의 의미는 Kafka의 JMX/메트릭 이름 처리 과정에서 점(`.`)과 밑줄(`_`)이 충돌할 수 있다는 것이다. 예를 들어 다음 두 토픽은 메트릭 이름 관점에서 충돌 후보가 된다.

- `nexuspay.transactions.payment`
- `nexuspay_transactions_payment`

Nexus Pay 실습에서는 토픽명에 밑줄(`_`)을 사용하지 않고 점(`.`)만 사용하므로, 현재와 같이 점만 포함된 토픽을 생성할 때 출력되는 이 경고는 일반 안내 메시지로 보면 된다. 즉, 현재 생성한 `nexuspay.transactions.payment`, `nexuspay.transactions.transfer` 자체가 잘못된 것은 아니다.

## 세부 규칙

### domain

- 서비스 또는 비즈니스 경계를 나타낸다.
- Nexus Pay 실습 환경에서는 기본적으로 `nexuspay`를 사용한다.

### entity

- 데이터의 핵심 업무 대상을 나타낸다.
- 예: `transactions`, `users`, `events`, `alerts`, `aggregation`, `cdc`

### event

- 해당 토픽의 처리 목적 또는 이벤트 유형을 나타낸다.
- 예: `payment`, `transfer`, `withdrawal`, `ingested`, `fraud`, `dlq`

## 권장 토픽 목록

| 토픽명 | 용도 | 비고 |
|--------|------|------|
| `nexuspay.transactions.payment` | 결제 이벤트 | 사용자별 순서 보장 필요 |
| `nexuspay.transactions.transfer` | 이체 이벤트 | 결제와 분리 운영 |
| `nexuspay.transactions.withdrawal` | 출금 이벤트 | 상대적 저빈도 트래픽 |
| `nexuspay.transactions.dlq` | Week 2 처리 실패 메시지 | 프로듀서·컨슈머 오류 분리 |
| `nexuspay.events.ingested` | Week 3 통합 수집 표준 이벤트 | NiFi 표준화 결과 수집 |
| `nexuspay.events.dlq` | Week 3 수집 품질 실패 메시지 | 수집 단계 DLQ |
| `nexuspay.alerts.fraud` | 이상거래 탐지 결과 | Flink 탐지 알림 |
| `nexuspay.aggregation.5min` | 5분 집계 결과 | 실시간 집계 산출물 |

## 금지 예시

다음과 같은 토픽명은 사용하지 않는다.

- `payment-topic`
- `transaction`
- `nexuspay_payment`
- `NexusPay.Transactions.Payment`
- `nexuspay.transactions.v1.payment`
- `dev.nexuspay.payment`

이유:

- 의미 계층이 불명확하거나
- 대소문자/구분자 규칙이 일관되지 않거나
- 환경/버전 정보가 토픽명에 섞여 운영 복잡도를 높이기 때문이다.

## DLQ 규칙

- DLQ는 원본 업무 흐름과 목적을 유지하면서 `.dlq`로 마무리한다.
- Week 2의 처리 실패 DLQ는 `nexuspay.transactions.dlq`를 사용한다.
- Week 3의 수집 품질 실패 DLQ는 `nexuspay.events.dlq`를 사용한다.
- 서로 다른 실패 성격을 하나의 DLQ 토픽으로 합치지 않는다.

## 운영 관점 가이드

- 토픽명만 보고도 “어느 계층의 어떤 데이터인가”를 판단할 수 있어야 한다.
- 대시보드, 알림, 검증 스크립트, DAG, 아키텍처 문서에서 동일한 토픽명을 그대로 사용한다.
- 신규 토픽 추가 시 이 문서에 먼저 등록하고, 이후 코드와 문서를 함께 갱신한다.

## Week 2 적용 결론

Week 2 Kafka 심화 실습에서는 아래 4개 토픽을 우선 표준 토픽으로 사용한다.

- `nexuspay.transactions.payment`
- `nexuspay.transactions.transfer`
- `nexuspay.transactions.withdrawal`
- `nexuspay.transactions.dlq`
