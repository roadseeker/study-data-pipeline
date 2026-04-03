# config/spark

Spark 배치 처리 엔진 설정 파일을 관리하는 폴더.

Spark Master / Worker의 동작 방식과 Delta Lake 연동 설정이 위치한다.

## 주요 설정 항목

- Spark Master 주소 및 포트 (`spark.master`)
- Worker 코어 수 및 메모리 (`SPARK_WORKER_CORES`, `SPARK_WORKER_MEMORY`)
- Delta Lake 관련 패키지 설정
- Spark History Server 설정 (선택)

## 관련 주차

- Week 1: Spark Master / Worker 기동 검증
- Week 5: Delta Lake 기반 배치 ETL 파이프라인 구현
- Week 6~7: 데이터 이관 및 오케스트레이션 연동
