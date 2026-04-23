# Nexus Pay Flink 운영 가이드

## 1. 잡 관리

### 잡 제출
```bash
docker exec lab-flink-jm /opt/flink/bin/flink run \
  -d -c <MainClass> /opt/flink/usrlib/flink-jobs-1.0.0.jar
```

### 잡 목록 확인
```bash
curl -s http://localhost:8081/jobs | python3 -m json.tool
```

### 잡 취소 (체크포인트 보존)
```bash
curl -X PATCH "http://localhost:8081/jobs/<JOB_ID>?mode=cancel"
```

### Savepoint 생성 (업그레이드 전)
```bash
docker exec lab-flink-jm /opt/flink/bin/flink savepoint <JOB_ID> /opt/flink/savepoints
```

### Savepoint에서 재시작
```bash
docker exec lab-flink-jm /opt/flink/bin/flink run \
  -d -s /opt/flink/savepoints/<SAVEPOINT_DIR> \
  /opt/flink/usrlib/flink-jobs-1.0.0.jar
```

## 2. 모니터링 항목

| 지표 | 임계값 | 확인 방법 |
|------|--------|----------|
| 체크포인트 소요 시간 | < 30초 | Dashboard → Checkpoints |
| 체크포인트 실패율 | 0% | `monitor_checkpoints.sh` |
| 백프레셔 | 0~LOW | Dashboard → Task → Back Pressure |
| 컨슈머 LAG | < 1000 | `kafka-consumer-groups.sh --describe` |
| TaskManager 가용 슬롯 | > 0 | Dashboard → Overview |
| 상태 크기 | < 1GB/잡 | Dashboard → Checkpoints → State Size |

## 3. 장애 대응

### TaskManager 장애
1. Flink 자동 재시작 전략에 의해 최대 3회 재시도
2. 마지막 성공 체크포인트에서 자동 복구
3. 3회 초과 실패 시 잡 FAILED → 수동 개입 필요

### 체크포인트 연속 실패
1. 상태 크기 확인 → 비정상 증가 시 상태 TTL 점검
2. 백프레셔 확인 → 병렬도 조정 또는 리소스 증설
3. Kafka 브로커 상태 확인 → 트랜잭션 타임아웃 점검

### Kafka 브로커 장애
1. Flink Kafka Source는 자동 재연결 시도
2. ISR < min.insync.replicas 시 싱크 쓰기 실패 → 체크포인트 실패
3. 브로커 복구 후 잡 자동 재시작

## 4. 성능 튜닝 가이드

| 파라미터 | 현재값 | 튜닝 방향 |
|----------|--------|----------|
| parallelism.default | 2 | Kafka 파티션 수에 맞춤 (최대 6) |
| checkpointing.interval | 60초 | 상태 크기에 따라 조정 (30~120초) |
| taskmanager.numberOfTaskSlots | 4 | 코어 수와 일치 |
| watermark.interval | 1초 | 지연 허용 범위에 따라 조정 |
| state.backend | hashmap | 상태 > 1GB 시 rocksdb 전환 |

## 5. 배포 토픽 맵

| 토픽 | 용도 | RF | 파티션 |
|------|------|-----|--------|
| nexuspay.events.ingested | NiFi 수집 데이터 (소스) | 3 | 6 |
| nexuspay.aggregation.5min | Tumbling 5분 집계 결과 | 3 | 3 |
| nexuspay.aggregation.sliding | Sliding 이동 평균 결과 | 3 | 3 |
| nexuspay.alerts.fraud | 이상거래 알림 | 3 | 3 |
| nexuspay.events.dlq | 지연·불량 데이터 | 3 | 2 |

