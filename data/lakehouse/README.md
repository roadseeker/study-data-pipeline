# data/lakehouse

Week 5 이후 Spark 기반 레이크하우스 산출물을 저장하는 루트 폴더이다.

이 폴더는 Spark 컨테이너에 `/data/lakehouse`로 마운트되며, Delta Lake 테이블과 배치 처리 보조 산출물을 호스트에 보존한다.

## 하위 폴더

| 폴더 | 역할 |
|------|------|
| delta/ | Delta Lake 기반 Bronze, Silver, Gold 테이블 저장소 |

## 운영 기준

- 실제 Delta 테이블 파일은 로컬 런타임 산출물이므로 Git에 포함하지 않는다.
- 레이크하우스 경로는 Week 5 Spark ETL, Week 7 Airflow 연계, Week 8 통합 검증에서 공통 기준으로 사용한다.
