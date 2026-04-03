# spark-jobs

Spark 기반 데이터 이관 및 오케스트레이션 코드를 관리하는 폴더.

레거시 시스템에서 신규 파이프라인으로 데이터를 이관하거나, Airflow와 연동하여 오케스트레이션하는 Spark 잡이 위치한다.

## 하위 폴더

| 폴더 | 역할 |
|------|------|
| migration/ | 레거시 DB → Delta Lake 데이터 이관 잡 |
| orchestration/ | Airflow DAG에서 호출하는 Spark 잡 (배치 오케스트레이션) |

## 관련 주차

- Week 6: 레거시 PostgreSQL → Delta Lake 데이터 이관
- Week 7: Airflow + Spark 연동 오케스트레이션 고도화

## 실행 방법

```bash
# 이관 잡 실행 (Week 6에서 상세 명령 제공)
docker exec lab-spark-master spark-submit \
  --master spark://spark-master:7077 \
  /opt/spark-jobs/migration/<job>.py

# 오케스트레이션 잡은 Airflow DAG에서 자동 호출
```
