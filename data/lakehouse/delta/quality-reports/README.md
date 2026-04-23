# data/lakehouse/delta/quality-reports

Spark 데이터 품질 검증 결과를 저장하는 폴더이다.

Silver 계층으로 승격되지 못한 데이터의 건수, 원인, 검증 시각 등을 리포트 형태로 남겨 운영자가 품질 이슈를 추적할 수 있게 한다.

## 역할

- null, 중복, 이상 금액, 상태값 오류 등 품질 검증 결과 보관
- Bronze to Silver 감소율 분석
- 배치 운영 가이드와 통합 검증 스크립트의 근거 데이터 제공
