# NiFi 대표 프로세서와 업무 적용 예시

## 문서 목적

이 문서는 Nexus Pay Week 3 실습을 준비하면서
고객과 실무 담당자에게 Apache NiFi의 대표 프로세서가 무엇을 하는지 설명하기 위한 자료다.

목표는 다음 두 가지다.

- NiFi 프로세서가 어떤 역할을 담당하는지 이해한다.
- 실제 업무에서 어떤 형태의 데이터 수집·변환·검증·전달 작업에 적용할 수 있는지 예시로 이해한다.

이 문서는 특히 다음 질문에 답하도록 구성했다.

- "NiFi에는 어떤 프로세서들이 있습니까?"
- "그 프로세서로 실제로 무슨 업무를 자동화할 수 있습니까?"
- "우리 회사의 API, CSV, DB, Kafka 연계에 어떻게 적용됩니까?"

## 1. 프로세서란 무엇인가

NiFi에서 `Processor`는 FlowFile을 처리하는 작업 단위다.
하나의 Processor는 보통 한 가지 책임을 가진다.

예를 들면 다음과 같다.

- API를 호출한다.
- 파일을 읽는다.
- JSON에서 특정 필드를 꺼낸다.
- 스키마를 표준 형태로 바꾼다.
- 유효성 검사를 한다.
- Kafka로 전송한다.

즉 Processor는 "코드 한 덩어리"가 아니라
"데이터 흐름 안에서 특정 기능을 수행하는 조립 가능한 부품"으로 이해하면 된다.

## 2. 대표적인 프로세서 분류

NiFi 프로세서는 매우 많지만, 고객 설명 시에는 기능별로 묶어서 이해하는 것이 좋다.

### 2-1. 수집 계열

외부 시스템에서 데이터를 가져오는 프로세서다.

NiFi는 공식적으로 "수집 계열"이라는 단일 분류를 따로 두지는 않지만,
실무적으로는 다음 유형의 프로세서들을 수집 계열로 묶어 설명할 수 있다.

#### 1) API 호출형

- `InvokeHTTP`

설명:
- REST API, 내부 MSA API를 호출해 데이터를 가져오는 방식이다.

예시:
- 결제 API에서 최근 거래 JSON을 30초마다 수집

#### 2) 파일 직접 수집형 `Get*`

- `GetFile`
- `GetFTP`
- `GetHDFS`
- `GetTCP`

설명:
- 특정 파일 시스템이나 프로토콜에서 데이터를 직접 읽어오는 방식이다.

예시:
- FTP 서버에 적재된 인터페이스 파일을 읽기
- 로컬 경로의 배치 생성 파일을 직접 읽기

#### 3) 파일·오브젝트 감시형 `List* + Fetch*`

- `ListFile` + `FetchFile`
- `ListFTP` + `FetchFTP`
- `ListSFTP` + `FetchSFTP`
- `ListS3` + `FetchS3Object`
- `ListHDFS` + `FetchHDFS`
- `ListAzureBlobStorage`
- `ListAzureDataLakeStorage`
- `ListGCSBucket`

설명:
- "새 데이터가 생겼는지 탐지"하는 단계와
  "실제 내용을 읽는 단계"를 분리하는 패턴이다.
- 운영 관점에서 중복 처리 방지와 상태 관리에 유리하다.

예시:
- 매시간 떨어지는 정산 CSV를 감지 후 수집
- S3 버킷에 올라온 정산 파일을 읽기

#### 4) 데이터베이스 조회형 `Query*` / `Execute*`

- `QueryDatabaseTable`
- `QueryDatabaseTableRecord`
- `ExecuteSQL`
- `ExecuteSQLRecord`

설명:
- 관계형 데이터베이스나 일부 저장소를 조회해 데이터를 읽는 방식이다.
- 특히 증분 수집이 중요한 업무에서 자주 사용된다.

예시:
- PostgreSQL `customers` 테이블에서 변경분만 조회

#### 5) 메시징·스트리밍 소비형 `Consume*`

- `ConsumeKafka_*`
- `ConsumeKafkaRecord_*`
- `ConsumeJMS`
- `ConsumeAMQP`
- `ConsumeMQTT`
- `ConsumeKinesisStream`
- `ConsumeGCPubSub`
- `ConsumeAzureEventHub`

설명:
- 브로커나 이벤트 스트림에서 메시지를 소비하는 방식이다.

예시:
- Kafka 토픽에서 타 시스템 이벤트를 받아 후속 처리
- MQ에서 들어오는 업무 메시지를 수집

#### 6) 수신 서버형 `Listen*`

- `ListenHTTP`
- `ListenTCP`
- `ListenUDP`
- `ListenSyslog`
- `ListenSMTP`
- `ListenWebSocket`

설명:
- NiFi가 데이터를 받는 서버 역할을 하는 방식이다.
- 외부 시스템이 NiFi 쪽으로 직접 보내는 푸시형 연계에 적합하다.

예시:
- 외부 시스템이 HTTP POST로 이벤트를 보내면 NiFi가 수신
- 네트워크 장비 로그를 Syslog로 수신

#### 7) 변경 이벤트·CDC 계열

- `CaptureChangeMySQL`
- `GetHDFSEvents`

설명:
- 단순 파일 읽기나 쿼리보다 "무엇이 바뀌었는가"를 이벤트 기반으로 잡아내는 방식이다.

예시:
- MySQL 변경 이벤트를 캡처해 실시간 파이프라인에 연결

#### 8) 특정 SaaS·업무 시스템 전용 수집형

- `GetWorkdayReport`
- `GetZendesk`
- `ListBoxFile`
- `ListDropbox`

설명:
- 특정 SaaS나 업무 시스템에 맞춰 준비된 전용 프로세서다.

예시:
- Workday 보고서를 자동 수집
- Zendesk 티켓 데이터를 주기적으로 읽기

Week 3의 Nexus Pay 실습에서는 이 가운데 다음 세 가지를 핵심으로 사용한다.

- `InvokeHTTP`: 결제 API 수집
- `ListFile` / `FetchFile`: 정산 CSV 수집
- `QueryDatabaseTable`: PostgreSQL 고객 마스터 증분 수집

설명 포인트:
- "데이터가 어디서 들어오는가"를 담당한다.
- API, 파일, DB처럼 이기종 소스를 하나의 캔버스에서 통합할 수 있다.

### 2-2. 변환 계열

원천 데이터의 형식과 구조를 목적 시스템에 맞게 바꾸는 프로세서다.

- `SplitJson`: JSON 배열을 개별 레코드로 분리
- `SplitRecord`: CSV/JSON/Avro 레코드를 건별로 분리
- `EvaluateJsonPath`: JSON 필드 추출
- `ConvertRecord`: CSV, Avro, JSON 간 포맷 변환
- `JoltTransformJSON`: JSON 구조를 표준 스키마로 변환
- `UpdateAttribute`: 메타데이터 추가 또는 수정

설명 포인트:
- "데이터를 downstream이 읽기 쉬운 형태로 바꾸는 단계"다.
- 여러 소스에서 온 데이터를 하나의 공통 스키마로 맞추는 데 핵심이다.

### 2-3. 검증·품질 계열

데이터 품질과 규칙 준수를 확인하는 프로세서다.

- `ValidateRecord`: 스키마 준수 여부 확인
- `RouteOnAttribute`: 속성값에 따라 조건 분기
- `RouteOnContent`: 본문 내용에 따라 조건 분기
- `DetectDuplicate`: 중복 데이터 판별

설명 포인트:
- "정상 데이터와 예외 데이터를 분리하는 단계"다.
- 운영 안정성과 감사 대응에 매우 중요하다.

### 2-4. 전달·적재 계열

처리된 데이터를 다른 시스템으로 보내는 프로세서다.

- `PublishKafka_2_6`: Kafka 토픽 전송
- `PutDatabaseRecord`: 데이터베이스 적재
- `PutFile`: 파일 저장
- `PutSFTP`: 외부 SFTP 서버 전송

설명 포인트:
- "최종 목적지에 안전하게 전달하는 단계"다.
- 실패 경로와 재시도 설계를 함께 고려해야 한다.

### 2-5. 관찰·운영 계열

운영자가 흐름을 이해하고 장애를 대응하도록 돕는 기능과 프로세서다.

- `LogAttribute`: 속성·메타데이터 로그 확인
- `MonitorActivity`: 일정 시간 데이터 유입 없음 감지
- `HandleHttpResponse`: 요청-응답 흐름 마무리
- `Provenance`: FlowFile의 생성·변환·전송 이력 추적

설명 포인트:
- "파이프라인이 살아 있는지, 어디서 문제가 생겼는지 보는 단계"다.
- 단순 수집이 아니라 운영 가능한 데이터 파이프라인의 핵심이다.

## 3. 고객에게 설명하기 좋은 대표 프로세서

아래 프로세서들은 Nexus Pay Week 3 시나리오에서 특히 자주 설명하게 된다.

### 3-1. InvokeHTTP

REST API를 호출해 데이터를 수집한다.

- 언제 쓰는가: 외부 결제 API, 파트너 정산 API, 환율 API 수집 시
- 핵심 기능: HTTP 메서드 호출, 헤더 지정, 인증 처리, 응답 수신
- Nexus Pay 예시:
  `GET /api/v1/payments/recent`를 30초마다 호출하여 최신 결제 이벤트를 수집

### 3-2. ListFile / FetchFile

디렉터리를 감시하고 새로 들어온 파일을 읽는다.

- 언제 쓰는가: 레거시 시스템이 CSV, TXT, XML 파일을 주기적으로 생성할 때
- 핵심 기능: 신규 파일 탐지, 읽기 대상 관리, Fetch 후 후속 처리 연결
- Nexus Pay 예시:
  `/data/settlement/` 경로에 매시간 떨어지는 정산 CSV 파일을 탐지 후 수집

### 3-3. QueryDatabaseTable

데이터베이스 테이블에서 증분 방식으로 데이터를 조회한다.

- 언제 쓰는가: 고객 마스터, 거래 기준정보, 점포 정보 같은 마스터 데이터 수집 시
- 핵심 기능: Max-value 컬럼 기반 증분 조회, 상태 유지
- Nexus Pay 예시:
  PostgreSQL `customers` 테이블을 `updated_at` 기준으로 변경분만 조회

### 3-4. ConvertRecord

레코드 포맷을 다른 형식으로 변환한다.

- 언제 쓰는가: CSV를 JSON으로, Avro를 JSON으로 바꿔야 할 때
- 핵심 기능: Reader/Writer 조합으로 구조화된 데이터 변환
- Nexus Pay 예시:
  정산 CSV를 JSON 레코드로 바꿔 이후 Jolt 변환에 연결

### 3-5. EvaluateJsonPath

JSON 본문에서 특정 필드를 추출해 속성이나 값으로 만든다.

- 언제 쓰는가: `event_id`, `status`, `merchant_id` 같은 주요 필드를 꺼낼 때
- 핵심 기능: JSON 경로 기반 값 추출, 라우팅용 속성 생성
- Nexus Pay 예시:
  API 응답 JSON에서 `transaction_type`, `currency`, `amount`를 꺼내 조건 분기에 활용

### 3-6. JoltTransformJSON

JSON 구조를 원하는 표준 스키마로 바꾼다.

- 언제 쓰는가: API, CSV, DB처럼 형식이 다른 소스를 하나의 이벤트 구조로 통합할 때
- 핵심 기능: 필드명 변경, 중첩 구조 재배치, 기본값 지정
- Nexus Pay 예시:
  `settlement_id`, `customer_id`, `txn_id`처럼 제각각인 식별자 필드를
  모두 `record_id` 또는 `event_id` 체계로 맞춤

### 3-7. ValidateRecord

데이터가 정의된 스키마를 만족하는지 검사한다.

- 언제 쓰는가: 필수 필드 누락, 타입 오류, 포맷 오류를 걸러낼 때
- 핵심 기능: 정상/비정상 데이터 분기
- Nexus Pay 예시:
  `event_type`, `event_time`, `amount`, `currency`가 없는 레코드는 DLQ 경로로 분리

### 3-8. RouteOnAttribute

속성값에 따라 FlowFile을 다른 경로로 보낸다.

- 언제 쓰는가: 데이터 유형별 분기, 국가별 분기, 정상/오류 분기 시
- 핵심 기능: 표현식 언어 기반 조건 라우팅
- Nexus Pay 예시:
  `event_type=PAYMENT`는 결제 토픽으로,
  `event_type=WITHDRAWAL`은 출금 토픽으로 분기

### 3-9. PublishKafka_2_6

처리된 데이터를 Kafka로 발행한다.

- 언제 쓰는가: NiFi가 수집·표준화한 데이터를 스트리밍 플랫폼으로 전달할 때
- 핵심 기능: 토픽 지정, 키 지정, 전달 보장 설정
- Nexus Pay 예시:
  표준화된 이벤트를 `nexuspay.events.ingested` 토픽으로 전송

### 3-10. LogAttribute

FlowFile 속성값을 로그로 남겨 디버깅과 운영 점검에 활용한다.

- 언제 쓰는가: 개발 초기, 장애 분석, 속성값 확인 시
- 핵심 기능: 현재 속성과 경로 상태를 빠르게 확인
- Nexus Pay 예시:
  변환 실패 건에 대해 `source_system`, `filename`, `event_id` 속성을 로그로 출력

## 4. NiFi 프로세서로 처리할 수 있는 업무 10가지

이 절은 고객이 가장 궁금해하는 "그래서 실제로 무슨 업무를 자동화할 수 있습니까?"에 답하기 위한 예시다.

### 업무 1. 결제 API 실시간 수집

설명:
외부 결제 시스템이나 내부 MSA API를 일정 주기로 호출하여 최신 거래 데이터를 수집한다.

주요 프로세서:
- `GenerateFlowFile` 또는 스케줄링
- `InvokeHTTP`
- `SplitJson`
- `EvaluateJsonPath`

Nexus Pay 예시:
- 30초마다 `/api/v1/payments/recent` 호출
- 최신 결제 이벤트 100건 수집
- 건별 이벤트로 분리 후 후속 표준화 단계로 전달

고객 가치:
- API 기반 데이터를 수작업 없이 자동 수집
- 운영자가 수집 실패 시점을 즉시 파악 가능

### 업무 2. 레거시 정산 CSV 자동 수집

설명:
파일 서버 또는 공유 폴더에 떨어지는 CSV를 자동으로 읽어 파이프라인에 편입한다.

주요 프로세서:
- `ListFile`
- `FetchFile`
- `ConvertRecord`
- `SplitRecord`

Nexus Pay 예시:
- 매시간 생성되는 `settlement_20260408_1000.csv` 파일 탐지
- CSV를 JSON 레코드로 바꿔 건별 처리

고객 가치:
- 수동 업로드 제거
- 파일 누락·지연 감지 가능

### 업무 3. 고객 마스터 DB 증분 수집

설명:
PostgreSQL 같은 운영 DB에서 변경된 행만 주기적으로 읽어 동기화한다.

주요 프로세서:
- `QueryDatabaseTable`
- `ConvertRecord`
- `SplitRecord`

Nexus Pay 예시:
- `customers` 테이블에서 `updated_at > last_max` 조건으로 변경분만 조회
- CRM 갱신분을 Kafka나 데이터 레이크로 전달

고객 가치:
- 전체 테이블 재조회 부담 감소
- 변경분 중심 처리로 운영 효율 향상

### 업무 4. 서로 다른 소스 스키마를 공통 형식으로 표준화

설명:
API, CSV, DB가 서로 다른 필드 구조를 가지더라도 하나의 표준 이벤트 계약으로 맞춘다.

주요 프로세서:
- `JoltTransformJSON`
- `UpdateAttribute`

Nexus Pay 예시:
- API의 `txn_id`
- CSV의 `settlement_id`
- DB의 `customer_id`

이처럼 제각각인 식별자 구조를
목적에 맞게 `record_id`, `source_system`, `event_type`, `event_time` 형태로 정규화

고객 가치:
- Kafka, Flink, Spark가 동일한 구조로 데이터 소비 가능
- 후속 시스템 복잡도 감소

### 업무 5. 데이터 품질 검증과 불량 데이터 분리

설명:
필수 필드 누락, 타입 오류, 형식 오류를 검사하고
정상 데이터와 예외 데이터를 분리한다.

주요 프로세서:
- `ValidateRecord`
- `RouteOnAttribute`
- `LogAttribute`

Nexus Pay 예시:
- `amount`가 숫자가 아니거나
- `currency`가 비어 있거나
- `event_time` 포맷이 잘못된 경우

정상 토픽 대신 DLQ 토픽 또는 오류 보관 경로로 분기

고객 가치:
- 품질 문제의 조기 발견
- 잘못된 데이터가 downstream을 오염시키는 것을 방지

### 업무 6. 업무 규칙 기반 라우팅

설명:
속성값이나 본문 값을 기준으로 데이터를 여러 경로로 나눈다.

주요 프로세서:
- `EvaluateJsonPath`
- `RouteOnAttribute`
- `RouteOnContent`

Nexus Pay 예시:
- `event_type=PAYMENT`는 결제 흐름
- `event_type=TRANSFER`는 계좌이체 흐름
- `event_type=WITHDRAWAL`은 출금 흐름으로 분기

고객 가치:
- 하나의 유입 파이프라인 안에서 업무 유형별 처리 분리
- 시스템별 토픽 또는 저장소 분리 가능

### 업무 7. Kafka 실시간 발행

설명:
표준화와 검증이 끝난 이벤트를 Kafka로 전달해
실시간 분석, 이상거래 탐지, 정산 시스템으로 연계한다.

주요 프로세서:
- `PublishKafka_2_6`
- `UpdateAttribute`

Nexus Pay 예시:
- 정상 이벤트는 `nexuspay.events.ingested`
- 불량 이벤트는 `nexuspay.events.dlq`

고객 가치:
- 실시간 이벤트 허브 구성
- Flink, Spark, 후속 마이크로서비스와 손쉽게 연계

### 업무 8. 개인정보 마스킹 또는 민감정보 정제

설명:
외부 전달 전에 카드번호, 휴대폰번호, 이메일처럼 민감한 데이터를 가공한다.

주요 프로세서:
- `ReplaceText`
- `JoltTransformJSON`
- `UpdateAttribute`

Nexus Pay 예시:
- 카드번호 `1234-5678-9999-0000`를 `1234-****-****-0000` 형태로 마스킹
- 외부 파트너용 Kafka 토픽에는 주민번호·전화번호 제외

고객 가치:
- 개인정보 최소 제공 원칙 준수
- 외부 연계 시 보안 리스크 감소

### 업무 9. 수집 지연 또는 중단 감지

설명:
정상적으로 들어와야 할 데이터가 일정 시간 들어오지 않으면 운영 경고를 발생시킨다.

주요 프로세서:
- `MonitorActivity`
- `LogAttribute`
- 알림용 후속 프로세서 또는 외부 연계

Nexus Pay 예시:
- 평소 30초마다 API 응답이 오는데 10분 동안 아무 데이터가 없으면 경고
- 정산 CSV가 매시 정각 이후 15분 내 안 들어오면 운영 점검 대상 표시

고객 가치:
- 장애를 늦게 발견하는 문제 방지
- SLA 운영에 유리

### 업무 10. 데이터 출처와 처리 이력 추적

설명:
특정 데이터가 언제 들어와서 어떤 변환을 거쳐 어느 시스템으로 전송되었는지 추적한다.

주요 기능 및 프로세서:
- `Provenance`
- `UpdateAttribute`
- `LogAttribute`

Nexus Pay 예시:
- `PAY-00000042`가 10시 03분에 API에서 생성되었고
- `JoltTransformJSON`에서 표준화되었고
- `ValidateRecord`를 통과한 뒤
- `PublishKafka_2_6`를 통해 Kafka로 전송되었음을 확인

고객 가치:
- 금융감독원 감사 대응
- 장애 원인 분석과 재처리 판단 근거 확보

## 5. 고객 설명용 핵심 메시지

고객에게는 다음처럼 설명하면 이해가 쉽다.

- NiFi 프로세서는 "데이터 흐름의 조립식 부품"이다.
- API 수집, 파일 수집, DB 조회, 스키마 변환, 검증, Kafka 전송을 각 부품으로 나눠 구성한다.
- 이 부품들을 연결하면 복잡한 데이터 통합 요구사항도 화면에서 설명 가능한 파이프라인으로 만들 수 있다.
- 특히 Provenance와 큐 관찰 기능 덕분에 "무엇이 어디서 들어와 어떻게 흘렀는가"를 운영 중에도 증명할 수 있다.

## 6. Week 3 적용 포인트

Nexus Pay Week 3에서는 이 문서의 프로세서들을 다음 구조로 조합한다.

- `PG-1 API Ingestion`: `InvokeHTTP`, `SplitJson`, `EvaluateJsonPath`
- `PG-2 File Ingestion`: `ListFile`, `FetchFile`, `ConvertRecord`, `SplitRecord`
- `PG-3 DB Ingestion`: `QueryDatabaseTable`, `ConvertRecord`
- `PG-4 Schema Standardization`: `JoltTransformJSON`, `ValidateRecord`, `RouteOnAttribute`
- `PG-5 Kafka Publishing`: `PublishKafka_2_6`, `LogAttribute`

즉 이 문서는 "NiFi에 이런 프로세서가 있다"는 소개를 넘어서
"이 프로세서들을 실제 Nexus Pay 수집 파이프라인에서 어떻게 조합할 것인가"를 이해하기 위한 기준 문서다.
