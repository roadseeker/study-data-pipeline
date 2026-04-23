# data/lakehouse/delta/bronze

Bronze 계층은 원천 데이터를 감사와 재처리를 위해 보존하는 Delta Lake 영역이다.

Week 5 Spark ETL에서는 Kafka 원본 이벤트 또는 샘플 입력 파일을 표준 스키마와 적재 메타데이터를 붙여 이 계층에 저장한다.

## 역할

- 원본 이벤트 보존
- 재처리 가능한 배치 입력 기준 제공
- 적재 일자 기준 파티셔닝 실습
- Silver 계층으로 넘어가기 전 원천 품질 상태 보존
