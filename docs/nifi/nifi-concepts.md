# NiFi 핵심 개념 정리

## 문서 목적

이 문서는 Nexus Pay Week 3 실습에서 사용할 Apache NiFi의 핵심 개념을 정리한 컨설팅 설명 자료다.
목표는 REST API, CSV 파일, PostgreSQL 데이터를 하나의 수집 파이프라인으로 통합하기 전에
NiFi의 처리 단위와 운영 개념을 명확히 이해하는 것이다.

## 적용 시나리오

Nexus Pay는 다음 세 가지 이기종 소스를 수집해야 한다.

- 결제 API: 실시간 JSON 이벤트
- 정산 CSV: 레거시 시스템이 주기적으로 생성하는 파일
- 고객 마스터 DB: PostgreSQL의 변경 데이터

NiFi는 이 세 소스를 수집하고, 표준 스키마로 정리한 뒤 Kafka로 전달하며,
각 데이터가 언제 어디서 들어왔는지 Provenance로 추적하는 역할을 맡는다.

## 1. FlowFile

FlowFile은 NiFi에서 처리되는 데이터의 최소 단위다.
하나의 FlowFile은 다음 두 부분으로 구성된다.

- Content: 실제 데이터 본문
- Attributes: 파일명, MIME 타입, 소스 식별자, 처리 시각 같은 메타데이터

Nexus Pay 기준 예시는 다음과 같다.

- API 호출 결과 JSON 한 건 또는 한 묶음
- 정산 CSV 파일 한 개
- PostgreSQL 조회 결과 레코드 집합

실무 포인트:

- Content와 Attributes를 분리해 관리하므로, 본문을 바꾸지 않고도 라우팅과 추적이 가능하다.
- 데이터 계보 추적 시 어떤 소스에서 어떤 속성으로 들어왔는지 확인하기 쉽다.

## 2. Processor

Processor는 FlowFile을 생성, 변환, 검증, 전달하는 작업 단위다.
NiFi 플로우는 여러 Processor를 연결해 구성한다.

Nexus Pay Week 3에서 사용할 대표 Processor는 다음과 같다.

- `InvokeHTTP`: 결제 API 호출
- `ListFile` / `FetchFile`: 정산 CSV 탐지 및 읽기
- `QueryDatabaseTable`: 고객 마스터 증분 조회
- `ConvertRecord`: CSV 또는 Avro를 JSON으로 변환
- `JoltTransformJSON`: 표준 스키마로 구조 변환
- `ValidateRecord`: 필수 필드와 형식 검증
- `PublishKafka_2_6`: Kafka 토픽 전송

실무 포인트:

- 각 Processor는 단일 책임으로 설계하는 것이 운영과 장애 분석에 유리하다.
- 소스 수집, 변환, 검증, 전달을 분리하면 병목 지점과 실패 구간이 명확해진다.

## 3. Connection과 Back-Pressure

Connection은 Processor와 Processor 사이를 연결하는 큐다.
FlowFile은 Connection에 잠시 저장되었다가 다음 Processor로 전달된다.

Connection의 핵심 기능은 다음과 같다.

- Relationship 기반 라우팅
- 큐 길이 시각화
- Back-Pressure 제어

Back-Pressure는 큐에 FlowFile 수나 데이터 크기가 일정 수준 이상 쌓이면
상류 Processor를 자동으로 일시 정지시켜 전체 시스템을 보호하는 기능이다.

Nexus Pay 관점에서 중요한 이유는 다음과 같다.

- Kafka 장애 또는 지연 발생 시 NiFi가 무한정 밀어 넣지 않도록 제어 가능
- DB/파일/API 소스 속도와 Kafka 전달 속도가 달라도 완충 지점을 둘 수 있음
- 운영자가 어느 구간에서 적체가 발생하는지 빠르게 파악 가능

## 4. Process Group

Process Group은 여러 Processor를 논리적으로 묶는 컨테이너다.
복잡한 플로우를 기능별, 소스별로 나눠 관리할 수 있다.

Week 3에서 설계할 Nexus Pay 그룹 구조는 다음과 같다.

- `PG-1: API Ingestion`
- `PG-2: File Ingestion`
- `PG-3: DB Ingestion`
- `PG-4: Schema Standardization`
- `PG-5: Kafka Publishing`

실무 포인트:

- 그룹 간 Input Port / Output Port를 사용하면 플로우 경계가 명확해진다.
- 장애 분석 시 어느 단계에서 실패했는지 빠르게 좁힐 수 있다.
- 추후 소스가 늘어나도 동일 패턴으로 확장하기 쉽다.

## 5. Provenance

Provenance는 FlowFile의 생성, 수정, 라우팅, 전송 이력을 기록하는 추적 기능이다.
NiFi의 감사 대응과 운영 가시성에서 가장 중요한 기능 중 하나다.

Nexus Pay에서 Provenance가 중요한 이유는 다음과 같다.

- 특정 결제 이벤트가 API, CSV, DB 중 어디서 들어왔는지 증명 가능
- 어떤 Processor를 거쳐 Kafka로 전송되었는지 확인 가능
- 장애나 데이터 품질 문제 발생 시 정확한 변환 경로를 역추적 가능
- 금융감독원 감사 대응용 계보(Lineage) 근거로 활용 가능

예시 질문:

- `PAY-00000042` 이벤트는 어느 시각에 API에서 수집되었는가?
- 이 이벤트는 어떤 Jolt 변환을 거쳐 Kafka로 전달되었는가?
- 왜 특정 레코드는 정상 토픽이 아니라 DLQ로 이동했는가?

## 6. NiFi를 사용하는 이유

Nexus Pay Week 3에서 NiFi를 사용하는 이유는 단순 수집 도구가 아니라
운영 가능한 데이터 흐름 플랫폼이기 때문이다.

핵심 장점:

- 시각적 플로우 설계
- 다중 소스 수집 지원
- 재시도 및 실패 라우팅 내장
- Back-Pressure 기반 운영 안정성
- Provenance 기반 감사 대응 가능

즉 NiFi는 "데이터를 가져오는 도구"가 아니라
"데이터 수집, 변환, 추적, 운영을 하나의 흐름으로 관리하는 플랫폼"으로 이해하는 것이 맞다.

## 7. Week 3 실습 연결 포인트

이 문서를 바탕으로 Week 3에서는 다음 순서로 진행한다.

1. API, 파일, DB 수집용 Process Group 설계
2. 각 소스별 Processor 체인 구성
3. JoltTransformJSON으로 표준 스키마 통일
4. ValidateRecord로 품질 검증
5. PublishKafka로 Kafka 전달
6. Provenance로 전체 흐름 추적

## 요약

- FlowFile: NiFi가 다루는 데이터 단위
- Processor: 데이터를 생성, 변환, 전달하는 작업 단위
- Connection: Processor 사이의 큐와 라우팅 경로
- Back-Pressure: 과부하 방지 장치
- Process Group: 복잡한 플로우를 구조화하는 논리 그룹
- Provenance: 데이터 계보와 감사 추적의 핵심 기능

Nexus Pay Week 3의 목표는 이 개념들을 바탕으로
다중 소스 데이터를 표준화하여 Kafka로 전달하고, 전체 경로를 추적 가능한 형태로 구현하는 것이다.
