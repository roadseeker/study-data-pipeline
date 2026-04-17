# config/flink

Flink 스트림 처리 엔진 설정 파일을 관리하는 폴더.

JobManager와 TaskManager의 동작 방식을 제어하는 설정이 위치한다.

현재 foundation 기준 런타임은 **Flink 2.2.0**을 사용한다. Flink 2.x부터 설정 파일 포맷이 `flink-conf.yaml`에서 **`config.yaml`**로 변경되었다. Docker 환경에서는 `FLINK_PROPERTIES` 환경변수 방식이 2.x에서도 지속 지원된다.

## Flink 2.x 주요 변경 사항 (1.x 대비)

- 설정 파일: `flink-conf.yaml` → `config.yaml`
- Java 버전: Java 11 → **Java 17** (2.x 권장 런타임, Java 8 지원 종료)
- Scala API 제거: 이미지 태그에서 `scala_2.12` 접미사 삭제
- Maven 아티팩트: Scala 접미사 없이 `flink-streaming-java` 사용
- Kafka 커넥터: `3.x-1.20` → `4.0.1-2.0` (Source/Sink V2 기반으로 재작성)
- DataSet API 완전 제거 → 배치는 DataStream 또는 Table API 사용

## 주요 설정 항목

- JobManager RPC 주소 (`jobmanager.rpc.address`)
- TaskManager 슬롯 수 (`taskmanager.numberOfTaskSlots`)
- 기본 병렬도 (`parallelism.default`)
- 체크포인트 및 상태 백엔드 설정 (Week 4 이후)
- 메모리 할당 설정
- Flink 2.2.0 권장 Java 런타임 (`Java 17`)

## 관련 주차

- Week 1: JobManager / TaskManager 기동 검증 (슬롯 4개 확인)
- Week 4: Kafka → Flink 실시간 스트림 처리 잡 구현
