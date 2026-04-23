# data/lakehouse/delta/checkpoints

Spark 작업의 체크포인트를 저장하는 폴더이다.

Week 5 배치 ETL에서는 주로 재실행 기준과 실습 확장을 위해 사용하며, Week 6 이후 Structured Streaming 또는 CDC 처리와 연결될 때 더 중요해진다.

## 역할

- Spark 작업 진행 상태 보존
- 장애 후 재시작 또는 증분 처리 기준 제공
- Delta Lake 데이터 경로와 분리된 운영 메타데이터 저장
