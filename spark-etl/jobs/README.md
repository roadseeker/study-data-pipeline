# spark-etl/jobs

Spark ETL 잡의 메인 실행 스크립트를 관리하는 폴더.

각 잡은 독립적으로 실행 가능하며, Bronze → Silver → Gold 레이어 순서로 데이터를 처리한다.

## 관련 주차

- Week 5: Delta Lake 기반 배치 ETL 잡 구현
  - 원본 데이터 적재 (Bronze)
  - 정제·변환 처리 (Silver)
  - 집계·분석 데이터 생성 (Gold)
