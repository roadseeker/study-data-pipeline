# spark-jobs/orchestration

Airflow DAG에서 호출하는 Spark 오케스트레이션 잡을 관리하는 폴더.

## 용도

- Airflow `SparkSubmitOperator` 또는 `BashOperator`를 통해 트리거되는 잡
- 배치 파이프라인 전체 흐름 제어 (수집 → 변환 → 적재 → 검증)
- 잡 간 의존성 및 실행 순서 관리

## 관련 주차

- Week 7: Airflow + Spark 연동 오케스트레이션 고도화
