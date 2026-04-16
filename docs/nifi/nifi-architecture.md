# Nexus Pay NiFi 데이터 수집 아키텍처

## 아키텍처 개요

```
  [결제 API]         [정산 CSV]         [고객 DB]
  (실시간 JSON)      (주기적 파일)       (증분 변경)
       │                  │                  │
       ▼                  ▼                  ▼
  ┌─────────┐      ┌──────────┐      ┌──────────┐
  │ PG-1    │      │ PG-2     │      │ PG-3     │
  │ API     │      │ File     │      │ DB       │
  │ Ingest  │      │ Ingest   │      │ Ingest   │
  └────┬────┘      └────┬─────┘      └────┬─────┘
       │                │                  │
       └────────────────┼──────────────────┘
                        ▼
                 ┌─────────────┐
                 │ PG-4        │
                 │ Schema      │
                 │ Standard.   │
                 └──────┬──────┘
                   ┌────┴────┐
                   ▼         ▼
              [정상]      [불량]
                   │         │
                   ▼         ▼
              ┌────────┐ ┌──────┐
              │ PG-5   │ │ DLQ  │
              │ Kafka  │ │ 토픽  │
              │ Pub    │ │      │
              └────────┘ └──────┘
                   │
                   ▼
         nexuspay.events.ingested
```

## 프로세서 그룹별 상세

### PG-1: API Ingestion
- **소스**: 결제 API (`http://payment-api:5050/api/v1/payments/recent`)
- **주기**: 30초
- **프로세서 체인**: InvokeHTTP → SplitJson → UpdateAttribute → ExecuteScript → JoltTransformJSON → EvaluateJsonPath
- **처리량**: ~40건/분

### PG-2: File Ingestion
- **소스**: 정산 CSV 파일 (`/data/settlement/settlement_*.csv`)
- **주기**: 파일 감지 시 즉시
- **프로세서 체인**: ListFile → FetchFile → ConvertRecord(CSV→JSON) → SplitRecord → UpdateAttribute → ExecuteScript → JoltTransformJSON → EvaluateJsonPath
- **처리 완료 파일**: `/data/settlement/processed/`로 이동

### PG-3: DB Ingestion
- **소스**: PostgreSQL `customers` 테이블
- **주기**: 60초 (증분 추출)
- **프로세서 체인**: QueryDatabaseTable → ConvertRecord(Avro→JSON) → SplitRecord → UpdateAttribute → ExecuteScript → JoltTransformJSON → EvaluateJsonPath
- **증분 기준**: `updated_at` 컬럼

### PG-4: Schema Standardization
- **역할**: 세 소스 데이터의 스키마 표준 준수 검증
- **정상**: PG-5로 전달
- **불량**: DLQ 토픽으로 전달

### PG-5: Kafka Publishing
- **대상 토픽**: `nexuspay.events.ingested` (RF=3, min.ISR=2)
- **DLQ 토픽**: `nexuspay.events.dlq`
- **파티션 키**: `event_id`
- **전송 보장**: Exactly-once (트랜잭션 사용)

## 표준 스키마

| 필드 | 타입 | 필수 | API | CSV | DB |
|------|------|------|-----|-----|----|
| event_id | string | ✅ | event_id | settlement_id | customer_id |
| event_type | string | ✅ | event_type | settlement_type | "CUSTOMER_UPDATE" |
| user_id | int | - | user_id | null | user_id |
| amount | double | - | amount | gross_amount | null |
| currency | string | - | currency | currency | null |
| status | string | - | status | status | null |
| ingested_at | string | - | ingested_at | ingested_at | ingested_at |
| data_source | string | ✅ | "payment-api" | "settlement-csv" | "customer-db" |
| event_timestamp | string | ✅ | timestamp | settlement_date | updated_at |
| schema_version | string | ✅ | "1.0" | "1.0" | "1.0" |
| created_at | string | - | null | created_at | created_at |
| fee_amount | double | - | null | fee_amount | null |
| net_amount | double | - | null | net_amount | null |
| tx_count | int | - | null | tx_count | null |
| batch_id | string | - | null | batch_id | null |
| customer_name | string | - | null | null | name |
| customer_email | string | - | null | null | email |
| customer_phone | string | - | null | null | phone |
| customer_grade | string | - | null | null | grade |
| is_active | boolean | - | null | null | is_active |

## 운영 포트 맵

| 포트 | 서비스 |
|------|--------|
| 8080 | NiFi 웹 UI |
| 5050 | 결제 API 시뮬레이터 |
| 5432 | PostgreSQL |
| 30092~30094 | Kafka 브로커 1~3 |

