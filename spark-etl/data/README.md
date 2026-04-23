# spark-etl/data

Spark ETL 코드 개발 중 사용하는 소규모 로컬 테스트 데이터 영역이다.

운영성 산출물은 `data/lakehouse` 아래에 저장하고, 이 폴더는 단위 테스트나 개발 편의를 위한 작은 fixture 데이터만 둔다.

## 하위 폴더

| 폴더 | 역할 |
|------|------|
| bronze/ | Bronze 변환 테스트용 fixture |
| silver/ | Silver 변환 테스트용 fixture |
| gold/ | Gold 집계 테스트용 fixture |
| checkpoints/ | 개발용 체크포인트 fixture |
| quality-reports/ | 품질 리포트 테스트 fixture |
