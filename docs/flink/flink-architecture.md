# Nexus Pay 실시간 파이프라인 아키텍처 — Week 4 완성

## 전체 흐름

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    Nexus Pay 실시간 데이터 파이프라인                          │
│                                                                          │
│  [수집 계층 — Week 3]                                                     │
│  ┌─────────┐                                                             │
│  │ NiFi    │ API·CSV·DB → 스키마 표준화 → PublishKafka                    │
│  └────┬────┘                                                             │
│       ▼                                                                  │
│  [버퍼 계층 — Week 2]                                                     │
│  ┌────────────────────────────────┐                                      │
│  │ Kafka (nexuspay.events.ingested) │  6 파티션, RF=3, min.ISR=2           │
│  └────────────┬───────────────────┘                                      │
│               │                                                          │
│       ┌───────┴───────┐                                                  │
│       ▼               ▼                                                  │
│  [변환 계층 — Week 4]                                                     │
│  ┌────────────────┐  ┌───────────────────┐                               │
│  │ Aggregation Job │  │ Fraud Detection   │                               │
│  │ ─────────────── │  │ Job               │                               │
│  │ Tumbling 5min   │  │ ───────────────── │                               │
│  │ Sliding 5min/1m │  │ RULE-001: 빈도    │                               │
│  │ Session 2min    │  │ RULE-002: 고액    │                               │
│  │                 │  │ RULE-003: 합계    │                               │
│  └───────┬─────┬──┘  └──────┬────────────┘                               │
│          │     │             │                                            │
│          ▼     ▼             ▼                                            │
│  ┌──────────┐ ┌──────┐ ┌──────────────┐  ┌──────┐                        │
│  │ 집계 토픽 │ │ DLQ  │ │ 알림 토픽      │  │ Redis │                       │
│  │ .5min    │ │ .dlq │ │ .alerts.fraud │  │ 캐시  │                        │
│  │ .sliding │ │      │ │              │  │      │                          │
│  └──────────┘ └──────┘ └──────────────┘  └──────┘                        │
│                                                                          │
│  [보장 수준]  End-to-End Exactly-once (체크포인트 + 트랜잭션)              │
└──────────────────────────────────────────────────────────────────────────┘
```

## Exactly-once 보장 체인

| 구간 | 메커니즘 | 설정 |
|------|----------|------|
| NiFi → Kafka | PublishKafka 트랜잭션 (Week 3) | Use Transactions=true |
| Kafka → Flink | 체크포인트에 오프셋 포함 | CheckpointingMode.EXACTLY_ONCE |
| Flink 내부 | 분산 스냅샷 (Chandy-Lamport) | 60초 주기 체크포인트 |
| Flink → Kafka | 2-Phase Commit | DeliveryGuarantee.EXACTLY_ONCE |

## 잡별 리소스

| 잡 | 슬롯 | 병렬도 | 체크포인트 주기 | 상태 백엔드 |
|-----|------|--------|---------------|-----------|
| TransactionAggregationJob | 2 | 2 | 60초 | HashMap |
| FraudDetectionJob | 2 | 2 | 30초 | HashMap |
| SessionWindowAnalysisJob | 1 | 1 | 60초 | HashMap |

