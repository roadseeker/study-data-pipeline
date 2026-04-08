# Nexus Pay Kafka 장애 복원력 테스트 보고서

**테스트 일자**: 2026-04-08  
**대상 환경**: Week 2 Nexus Pay Kafka 3-브로커 KRaft 클러스터  
**검증 범위**: 브로커 장애 시 leader 재선출, ISR 변화, 프로듀서 쓰기 가능 여부, 복구 후 정상화 확인

## 1. 테스트 구성

| 항목 | 값 |
|------|----|
| 브로커 수 | 3 |
| 파티션 수 | `nexuspay.transactions.payment` 기준 6 |
| 복제 팩터 | 3 |
| `min.insync.replicas` | 2 |
| 프로듀서 설정 | `acks=all`, `enable.idempotence=true` |

## 2. 장애 전 정상 상태

장애 전 `payment` 토픽은 다음과 같이 정상 상태를 보였다.

- `PartitionCount: 6`
- `ReplicationFactor: 3`
- 모든 파티션 `Isr: 1,2,3`
- leader 분산: 브로커 1, 2, 3이 각각 2개 파티션씩 담당

대표 관찰:

- Partition 0, 4 -> Leader 1
- Partition 1, 3 -> Leader 2
- Partition 2, 5 -> Leader 3

해석:

- ISR은 `3/3`으로 완전 동기화 상태였다.
- leader 역할도 3개 브로커에 균등 분산되어 쓰기/읽기 부하 분산이 정상적으로 동작했다.

## 3. 시나리오 A: 브로커 1대 장애

브로커 2 장애 후 `payment` 토픽 상태는 다음과 같았다.

- Partition 0 -> Leader 1, Isr 1,3
- Partition 1 -> Leader 3, Isr 3,1
- Partition 2 -> Leader 3, Isr 3,1
- Partition 3 -> Leader 1, Isr 1,3
- Partition 4 -> Leader 1, Isr 1,3
- Partition 5 -> Leader 3, Isr 3,1

해석:

- 브로커 2가 빠지자 원래 브로커 2가 leader였던 파티션 1, 3의 leader가 브로커 3과 1로 재선출되었다.
- 모든 파티션의 ISR은 `2/3`으로 감소했지만 `min.insync.replicas=2`는 만족했다.
- 남은 브로커 1과 3이 leader 역할을 3개씩 나눠 가지며 서비스가 계속 유지되었다.

추가 검증:

- 프로듀서 실행 결과 `connected_brokers=localhost:30092, localhost:30094`
- `delivered=50`
- `delivery_failed=0`
- `flush_failed=0`

결론:

- 브로커 1대 장애 시에도 쓰기 서비스는 정상 유지되었다.

## 4. 시나리오 B: ISR 부족 상태에서 쓰기 차단

추가 장애 상황에서 프로듀서 전송을 시도한 결과 다음 오류가 발생했다.

- `KafkaError{code=NOT_ENOUGH_REPLICAS ... "Broker: Not enough in-sync replicas"}`
- `delivered=0`
- `delivery_failed=5`

해석:

- 대상 파티션의 ISR이 `min.insync.replicas=2`보다 낮아진 상태였다.
- `acks=all` 설정으로 인해 Kafka는 안전한 복제 확인이 불가능하다고 판단해 쓰기를 거부했다.
- 이는 데이터 유실을 막기 위한 의도된 보호 동작이다.

결론:

- ISR이 1로 줄어드는 수준의 장애에서는 쓰기 가용성보다 데이터 안전성이 우선되도록 동작했다.

## 5. 시나리오 C: 브로커 복구 및 정상화

브로커 3, 브로커 2를 순차적으로 복구한 뒤 다음 상태를 확인했다.

초기 복구 직후 관찰:

- 모든 파티션 `Isr: 1,3,2`
- 모든 파티션 `Leader: 1`

해석:

- ISR은 먼저 `3/3`으로 복구되었다.
- 다만 leader는 일시적으로 브로커 1에 집중되어 완전한 분산 상태는 아니었다.

시간 경과 후 재확인 결과:

- Partition 0, 4 -> Leader 1
- Partition 1, 3 -> Leader 2
- Partition 2, 5 -> Leader 3

결론:

- 복구 직후에는 ISR 복구와 leader 재분산이 동시에 일어나지 않을 수 있다.
- 시간이 지나면서 leader가 다시 균등 분산 상태로 돌아왔고, 클러스터는 정상 운영 상태를 회복했다.

## 6. Unclean Leader Election 확인

토픽 설정 조회에서 `unclean.leader.election.enable`가 별도 토픽 설정으로 출력되지 않았다.

해석:

- 토픽 단위 override는 없으며 브로커 기본 정책을 따른다.
- 본 실습의 운영 원칙상 unclean leader election은 비활성으로 간주하고, 뒤처진 복제본 승격에 따른 데이터 유실을 허용하지 않는 방향으로 해석한다.

## 7. 종합 평가

| 항목 | 결과 |
|------|------|
| 1대 브로커 장애 허용 | 확인 |
| ISR 2 유지 시 쓰기 지속 | 확인 |
| ISR 부족 시 쓰기 차단 | 확인 |
| 컨슈머 재할당 및 계속 소비 | 확인 |
| 복구 후 ISR 3/3 회복 | 확인 |
| 복구 후 leader 재분산 | 확인 |

## 8. 컨설팅 권장 사항

- 운영 환경은 최소 3브로커, `RF=3`, `min.insync.replicas=2`를 기본값으로 유지한다.
- 프로듀서는 `acks=all`, `enable.idempotence=true`를 유지한다.
- 장애 대응 시 `Leader`, `Replicas`, `Isr`를 함께 확인한다.
- 복구 직후에는 ISR 회복뿐 아니라 leader 재분산 여부도 별도로 관찰한다.
- 알림 기준은 Under-Replicated Partitions, ISR shrink, consumer lag를 우선 적용한다.
