# config/flink

Flink 스트림 처리 엔진 설정 파일을 관리하는 폴더.

JobManager와 TaskManager의 동작 방식을 제어하는 설정이 위치한다.

## 주요 설정 항목

- JobManager RPC 주소 (`jobmanager.rpc.address`)
- TaskManager 슬롯 수 (`taskmanager.numberOfTaskSlots`)
- 기본 병렬도 (`parallelism.default`)
- 체크포인트 및 상태 백엔드 설정 (Week 4 이후)
- 메모리 할당 설정

## 관련 주차

- Week 1: JobManager / TaskManager 기동 검증 (슬롯 4개 확인)
- Week 4: Kafka → Flink 실시간 스트림 처리 잡 구현
