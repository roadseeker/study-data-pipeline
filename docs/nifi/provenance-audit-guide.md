# Nexus Pay 데이터 계보 추적 가이드 — 감사 대응용

## 감사 시나리오: "결제 이벤트 PAY-00000042의 출처를 증명하시오"

### 추적 절차

1. **Kafka에서 메시지 확인**:
   - 토픽 `nexuspay.events.ingested`에서 해당 event_id 검색
   - 메시지의 `data_source` 필드 확인 → "payment-api"

2. **NiFi Provenance에서 역추적**:
   - `Search Events`에서 `Event Type = SEND`로 1차 조회
   - 메인 목록 `Filter By = component name`, `Filter = PublishKafka [ingested-topic]`
   - 각 후보 행의 `View Details -> Content`에서 `event_id = PAY-00000042` 확인
   - 찾은 이벤트의 `FlowFile UUID`를 복사해 다시 `FlowFile UUID` 기준으로 재검색
   - 같은 이벤트의 `Show Lineage` 실행
   - Lineage 그래프에서 `FORK` 또는 `CLONE` 노드 우클릭 → `Find parents` 반복
   - 최종적으로 `SplitJson`, `UpdateAttribute`, `ExecuteScript`, `JoltTransformJSON`, `EvaluateJsonPath`, `ValidateRecord`, `PublishKafka` 흐름과 상위 `InvokeHTTP` 수신 흔적까지 확인
   - `Attributes`에서 `data_source = payment-api`, `source_system = nexuspay-payment-api` 확인

3. **증빙 자료 구성**:
   - Provenance Lineage 스크린샷 (시각적 흐름도)
   - 각 이벤트의 타임스탬프·프로세서명·입출력 내용
   - 원본 API 응답 원문 (CREATE 이벤트의 Content 확인)

## 실습 예시: 정산 레코드 `STL-20260416014714873026-000030`의 출처를 증명하시오

### 추적 절차

1. **원본 파일 기준 조회**:
   - `Search Events`에서 `Filename = settlement_20260416014714873026.csv`
   - 메인 목록에서 `Filter By = component name`, `Filter = PublishKafka`

2. **표준 이벤트 확인**:
   - 후보 `SEND` 이벤트의 `View Details -> Attributes` 또는 `Content`에서 `event_id = STL-20260416014714873026-000030` 확인
   - `data_source = settlement-csv`, `source_system = nexuspay-settlement-file` 확인

3. **Lineage 확장**:
   - 같은 행에서 `Show Lineage`
   - 그래프의 `FORK / SplitRecord` 또는 상위 분기 이벤트에서 `Find parents` 반복
   - 최종적으로 `ListFile -> FetchFile -> ConvertRecord -> SplitRecord -> UpdateAttribute -> ExecuteScript -> JoltTransformJSON -> EvaluateJsonPath -> ValidateRecord -> PublishKafka` 흐름 확인

4. **필드 매핑 해석**:
   - 원본 CSV의 `settlement_id = STL-20260416014714873026-000030`
   - `JoltTransformJSON` 이후 표준 스키마에서 같은 값이 `event_id`로 매핑됨
   - 따라서 Kafka와 Provenance 후반부에서는 `settlement_id` 대신 `event_id` 기준으로 추적하면 된다.

### 보존 설정

| 항목 | 권장 설정 | 근거 |
|------|----------|------|
| Provenance 보존 기간 | 30일 | nifi.provenance.repository.max.storage.time |
| Provenance 저장 용량 | 10GB | nifi.provenance.repository.max.storage.size |
| 감사 로그 외부 보관 | 5년 | 금융 규정 준수 (별도 저장소 이관 필요) |

### NiFi Provenance 설정 (nifi.properties)

```properties
nifi.provenance.repository.implementation=org.apache.nifi.provenance.WriteAheadProvenanceRepository
nifi.provenance.repository.max.storage.time=30 days
nifi.provenance.repository.max.storage.size=10 GB
nifi.provenance.repository.rollover.time=10 mins
nifi.provenance.repository.rollover.size=100 MB
nifi.provenance.repository.indexed.fields=EventType,FlowFileUUID,Filename,ProcessorID,Relationship
nifi.provenance.repository.indexed.attributes=event_id,user_id,data_source,event_type
```

> **설정 메모**: `nifi.provenance.repository.indexed.attributes`는 Provenance 저장소의 인덱싱 대상 attribute를 정의한다. 다만 NiFi 2.9.0 기본 `Search Events` 팝업이 모든 custom attribute 입력칸을 자동으로 노출하는 것은 아니므로, UI에서는 여전히 `Filename` 또는 `FlowFile UUID`로 먼저 찾고 `Attributes`/`Content`에서 `event_id`를 확인하는 절차가 필요할 수 있다.

