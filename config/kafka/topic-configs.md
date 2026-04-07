# Nexus Pay Kafka 토픽 설정 가이드

## 목적

이 문서는 Nexus Pay 데이터 파이프라인의 Kafka 토픽 설정 기준을 정리한다.  
Week 2 단일 브로커 PoC 환경과, 이후 멀티 브로커 운영 확장 시 적용할 기본값을 함께 설명한다.

## 핵심 설정 항목

| 설정 | Kafka 기본값 | Nexus Pay 기준 | 설명 |
|------|--------------|----------------|------|
| `retention.ms` | `604800000` (7일) | 거래 토픽 7일, DLQ 30일 | 메시지 보존 기간 |
| `cleanup.policy` | `delete` | `delete` | 만료 메시지 처리 방식 |
| `min.insync.replicas` | `1` | PoC 1, 멀티 브로커 2 | 동기화 복제본 최소 개수 |
| `max.message.bytes` | `1048576` (1MB) | 1MB 유지 | 단일 메시지 최대 크기 |
| `compression.type` | `producer` | `producer` 유지 | 프로듀서 압축 정책 존중 |
| `segment.bytes` | `1073741824` (1GB) | 기본값 유지 | 로그 세그먼트 크기 |

## Week 2 적용 토픽

| 토픽명 | 파티션 수 | 복제 팩터 | `retention.ms` | 비고 |
|--------|-----------|-----------|----------------|------|
| `nexuspay.transactions.payment` | 6 | 1 | `604800000` | 결제 거래 이벤트 |
| `nexuspay.transactions.transfer` | 6 | 1 | `604800000` | 이체 거래 이벤트 |
| `nexuspay.transactions.withdrawal` | 4 | 1 | `604800000` | 출금 거래 이벤트 |
| `nexuspay.transactions.dlq` | 2 | 1 | `2592000000` | 처리 실패 메시지 보관 |

## 설정 결정 기준

### `retention.ms`

- 거래 토픽은 재처리, 장애 분석, 지연 복구를 고려해 7일 유지한다.
- DLQ는 운영자 수동 검토 시간이 더 필요하므로 30일 유지한다.
- 금융 감사·장기 보관 요구는 Kafka가 아니라 별도 저장소로 이관하는 것을 전제로 한다.

### `cleanup.policy=delete`

- Week 2 실습의 목적은 실시간 거래 이벤트 스트리밍과 장애 복구 검증이다.
- 최신 상태만 필요한 compact 토픽이 아니라 이벤트 이력을 일정 기간 유지하는 delete 정책이 적합하다.

### `min.insync.replicas`

- 단일 브로커 PoC에서는 `1`이 맞다.
- Day 4 이후 3-브로커 구성으로 확장하면 `replication.factor=3`, `min.insync.replicas=2`를 적용한다.
- 이는 `acks=all`과 함께 최소 2개 복제본 확인 후 쓰기를 성공시키기 위한 운영 기준이다.

### `compression.type`

- 현재 실습은 프로듀서가 압축 여부를 제어하는 `producer` 기본값이면 충분하다.
- 트래픽 증가 시 `lz4` 또는 `snappy`를 별도 검토할 수 있다.

## 운영 권장사항

- 토픽 생성 시 설정값은 문서와 스크립트에 동시에 반영한다.
- DLQ 토픽은 업무 토픽과 분리하고 보존 기간을 더 길게 잡는다.
- `min.insync.replicas`는 브로커 수와 함께 조정하며, 단일 브로커 환경에 운영값을 그대로 적용하지 않는다.
- 토픽 설정 변경 전에는 컨슈머 지연, 메시지 크기, 재처리 요구사항을 먼저 검토한다.

## Day 4 확장 시 변경점

멀티 브로커 확장 이후에는 아래 기준으로 조정한다.

| 항목 | PoC (Day 1~3) | 멀티 브로커 (Day 4~) |
|------|---------------|----------------------|
| 복제 팩터 | 1 | 3 |
| `min.insync.replicas` | 1 | 2 |
| 장애 허용성 | 낮음 | 브로커 1대 장애 허용 |

## 검증 포인트

- `kafka-topics.sh --describe`로 파티션 수와 복제 팩터 확인
- `kafka-configs.sh --describe`로 토픽별 설정 확인
- DLQ의 보존 기간이 거래 토픽보다 길게 설정되었는지 확인
