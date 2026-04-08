# Nexus Pay Kafka 운영 가이드

## 1. 목적

이 문서는 Nexus Pay Week 2 Kafka 실습 환경의 운영 기준을 정리한다. 목적은 멀티 브로커 KRaft 클러스터의 기본 구성, 프로듀서·컨슈머 운영 원칙, 장애 대응 절차, 모니터링 기준을 일관되게 관리하는 것이다.

적용 범위는 `docker-compose.yml` 기반 3-브로커 Kafka 클러스터와 아래 거래 토픽이다.

- `nexuspay.transactions.payment`
- `nexuspay.transactions.transfer`
- `nexuspay.transactions.withdrawal`

## 2. 표준 클러스터 구성

| 항목 | 표준값 | 운영 의미 |
|------|--------|----------|
| 브로커 수 | 3 | 브로커 1대 장애 허용 |
| 복제 팩터 | 3 | 각 파티션을 3개 브로커에 복제 |
| min.insync.replicas | 2 | `acks=all` 기준 최소 2개 ISR 유지 시에만 안전한 쓰기 허용 |
| unclean leader election | 비활성 권장 | 뒤처진 복제본의 리더 승격 방지 |
| 거래 토픽 보존 기간 | 7일 | 운영 점검 및 재처리 여유 확보 |

## 3. 토픽 설계 원칙

- 명명 규칙은 `<도메인>.<엔티티>.<이벤트유형>` 형식을 사용한다.
- `user_id`를 파티션 키로 사용해 동일 사용자 거래 순서를 보장한다.
- 결제·이체 토픽은 6개 파티션, 출금 토픽은 4개 파티션을 기본값으로 사용한다.
- Dead Letter Queue는 별도 토픽으로 관리한다.

## 4. 프로듀서 운영 기준

| 설정 | 권장값 | 설명 |
|------|--------|------|
| `bootstrap.servers` | `localhost:30092,localhost:30093,localhost:30094` | 멀티 브로커 메타데이터 조회 |
| `acks` | `all` | ISR 확인 후 성공 반환 |
| `enable.idempotence` | `true` | 중복 전송 방지 |
| `retries` | `3` | 일시적 오류 재시도 |
| `compression.type` | `lz4` | 네트워크 사용량 절감 |
| `linger.ms` | `5` | 소규모 배치 효율 향상 |

운영 해석 기준:

- 브로커 1대 장애 시 `ISR=2`가 유지되면 쓰기 지속이 가능하다.
- `NOT_ENOUGH_REPLICAS` 또는 `NOT_ENOUGH_REPLICAS_AFTER_APPEND`가 발생하면 ISR이 `min.insync.replicas` 기준을 만족하지 못한 상태로 본다.
- 프로듀서 성공 기준은 `delivered > 0`, `delivery_failed = 0`, `flush_failed = 0`이다.

## 5. 컨슈머 운영 기준

| 설정 | 권장값 | 설명 |
|------|--------|------|
| `enable.auto.commit` | `false` | 처리 완료 후 수동 커밋 |
| `auto.offset.reset` | `earliest` | 신규 그룹 초기 검증에 유리 |
| `max.poll.interval.ms` | `300000` | 처리 여유 시간 확보 |
| `session.timeout.ms` | `30000` | 장애 탐지 시간 |

운영 해석 기준:

- 리밸런싱 직후 모든 파티션이 재할당되면 그룹 복구는 정상으로 본다.
- 브로커 장애 후에도 컨슈머가 계속 처리 로그를 출력하면 리더 재선출이 정상 동작한 것이다.
- `earliest` 설정에서는 기존 누적 메시지까지 재처리될 수 있으므로 처리 건수 해석 시 주의한다.

## 6. 모니터링 핵심 지표

| 지표 | 정상 범위 | 알림 기준 |
|------|----------|----------|
| Under-Replicated Partitions | 0 | 5분 이상 0 초과 |
| ISR Shrink | 0 | 즉시 점검 |
| Consumer Lag | 1000 미만 | 10000 초과 |
| Request Latency p99 | 100ms 미만 | 500ms 초과 |
| Disk Usage | 70% 미만 | 85% 초과 |

## 7. 운영 확인 명령어

```bash
# 토픽 목록
docker exec lab-kafka-1 sh -c '/opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka-1:9092 --list'

# 토픽 상세 확인
docker exec lab-kafka-1 sh -c '/opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka-1:9092 \
  --describe --topic nexuspay.transactions.payment'

# 리더 분산 확인
docker exec lab-kafka-1 sh -c '/opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka-1:9092 \
  --describe --topic nexuspay.transactions.payment' \
  | grep "Leader:" | awk '{print $6}' | sort | uniq -c

# 컨슈머 그룹 상태 확인
docker exec lab-kafka-1 sh -c '/opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server kafka-1:9092 \
  --describe --group fraud-detection'
```

## 8. 장애 대응 절차

1. `kafka-topics.sh --describe`로 `Leader`, `Replicas`, `Isr` 상태를 확인한다.
2. 장애 브로커를 식별하고 컨테이너 상태를 점검한다.
3. 프로듀서 오류가 `NOT_ENOUGH_REPLICAS`인지 확인한다.
4. 장애 브로커를 재기동하고 ISR 복구를 기다린다.
5. ISR이 `3/3`으로 복구된 뒤 리더 분산이 정상화되는지 재확인한다.
6. 컨슈머 재할당과 프로듀서 전송 성공 여부를 함께 검증한다.

## 9. 실습에서 확인한 운영 관찰

- 정상 상태에서는 6개 파티션의 leader가 브로커 1, 2, 3에 각각 2개씩 분산되었다.
- 브로커 1대 장애 시 ISR이 `2/3`으로 줄어도 `min.insync.replicas=2`를 만족하면 프로듀서 전송이 계속 성공했다.
- ISR이 `1`까지 감소한 상태에서는 프로듀서가 `NOT_ENOUGH_REPLICAS`로 쓰기를 거부했다.
- 브로커 복구 직후에는 ISR이 먼저 복구되고, leader 분산은 잠시 뒤에 균형 상태로 돌아올 수 있었다.

## 10. 운영 결론

Nexus Pay Week 2 Kafka 구성은 `RF=3`, `min.insync.replicas=2`, `acks=all` 조합을 통해 금융성 거래 이벤트에 필요한 기본 내구성과 장애 허용성을 제공한다. 운영상 핵심은 브로커 수 자체보다 ISR 유지 여부와 leader 분산 상태를 함께 보는 것이다.
