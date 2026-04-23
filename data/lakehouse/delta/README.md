# data/lakehouse/delta

Delta Lake 기반 Medallion 저장소의 루트 폴더이다.

Spark 배치 ETL은 이 경로 아래에 Bronze, Silver, Gold 계층을 생성한다. 각 계층은 Parquet 데이터 파일과 Delta 트랜잭션 로그(`_delta_log`)를 포함할 수 있다.

## 하위 폴더

| 폴더 | 역할 |
|------|------|
| bronze/ | 원본 이벤트를 거의 그대로 적재하는 계층 |
| silver/ | 정제, 표준화, 품질 검증을 통과한 계층 |
| gold/ | 정산·리포팅·분석용 비즈니스 집계 계층 |
| checkpoints/ | Spark 배치/스트리밍 작업의 체크포인트 저장 영역 |
| quality-reports/ | 데이터 품질 검증 결과 리포트 저장 영역 |
