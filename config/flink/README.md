# config/flink

Flink 스트림 처리 엔진 설정 파일을 관리하는 폴더.

JobManager와 TaskManager의 동작 방식을 제어하는 설정이 위치한다.

현재 foundation 기준 런타임은 Flink 1.20.3 LTS를 사용한다. 이 버전에서는 `flink-conf.yaml` 설정 체계를 기준으로 JobManager·TaskManager·체크포인트·상태 백엔드 구성을 관리하며, Week 4 이후 실시간 처리 설정도 같은 기준으로 정리한다.

## 주요 설정 항목

- JobManager RPC 주소 (`jobmanager.rpc.address`)
- TaskManager 슬롯 수 (`taskmanager.numberOfTaskSlots`)
- 기본 병렬도 (`parallelism.default`)
- 체크포인트 및 상태 백엔드 설정 (Week 4 이후)
- 메모리 할당 설정
- Flink 1.20.3 LTS 권장 Java 런타임 (`Java 11`)

## 관련 주차

- Week 1: JobManager / TaskManager 기동 검증 (슬롯 4개 확인)
- Week 4: Kafka → Flink 실시간 스트림 처리 잡 구현
