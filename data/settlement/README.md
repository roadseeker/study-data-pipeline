# data/settlement

Spark 배치 ETL에서 읽는 Nexus Pay 정산 입력 파일을 두는 폴더이다.

Week 5에서는 Spark 컨테이너에 `/data/settlement:ro`로 마운트하여, 배치 잡이 입력 파일을 읽되 원본 파일을 수정하지 않는 구조를 권장한다.

## 용도

- 정산 CSV 또는 정산 검증용 입력 파일 보관
- 일별·월별 정산 리포트 배치 처리의 입력 경로
- NiFi 런타임용 `data/nifi/settlement`와 구분되는 Spark 입력 경로

## 주의사항

- 실제 고객 데이터나 민감 정보는 포함하지 않는다.
- 대용량 생성 파일은 Git에 포함하지 않는다.
