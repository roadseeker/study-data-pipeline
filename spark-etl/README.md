# spark-etl

Spark 배치 ETL 코드를 관리하는 폴더.

Delta Lake 기반의 배치 파이프라인 구현 코드가 위치한다.

## 하위 폴더

| 폴더 | 역할 |
|------|------|
| jobs/ | Spark ETL 잡 메인 스크립트 |
| lib/ | 공통 유틸리티 및 헬퍼 모듈 |
| scripts/ | 잡 실행·테스트 보조 쉘 스크립트 |

## 관련 주차

- Week 5: Delta Lake 기반 배치 ETL 파이프라인 구현
  - Bronze / Silver / Gold 레이어 설계
  - 증분 적재 (incremental load)
  - 데이터 품질 검증

## 실행 방법

```bash
# Spark Master 컨테이너에서 잡 실행 (Week 5에서 상세 명령 제공)
docker exec lab-spark-master spark-submit \
  --master spark://spark-master:7077 \
  /opt/spark-etl/jobs/<job>.py
```
