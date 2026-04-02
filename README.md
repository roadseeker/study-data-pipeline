# Pipeline Lab — 데이터 파이프라인 실습 환경

## 아키텍처 개요

```
수집 (Kafka · NiFi) → 변환 (Flink · Spark) → 저장 (PostgreSQL · Redis) → 오케스트레이션 (Airflow)
```

## 서비스 구성

| 서비스 | 컨테이너 | 포트 | 용도 |
|--------|---------|------|------|
| PostgreSQL 16 | lab-postgres | 5432 | 메타데이터·샘플 DB |
| Redis 7 | lab-redis | 6379 | 피처 스토어·캐시 |
| Kafka 3.7 (KRaft) | lab-kafka | 29092 | 실시간 메시징 |
| NiFi 1.25 | lab-nifi | 8080 | 데이터 수집·라우팅 |
| Flink 1.18 | lab-flink-jm / lab-flink-tm | 8081 | 실시간 스트림 처리 |
| Spark 3.5 (official Apache image) | lab-spark-master / lab-spark-worker | 8082, 7077 | 배치 처리 |
| Airflow 2.8 | lab-airflow-web / lab-airflow-sched | 8083 | 워크플로우 오케스트레이션 |

## 빠른 시작

```bash
# 전체 스택 기동
docker compose up -d

# 환경 헬스체크
bash scripts/healthcheck-all.sh
```

## 접속 정보

| 서비스 | URL | 계정 |
|--------|-----|------|
| NiFi | http://localhost:8080/nifi | admin / nifi |
| Flink Dashboard | http://localhost:8081 | (인증 없음) |
| Spark Master | http://localhost:8082 | (인증 없음) |
| Airflow | http://localhost:8083 | admin / airflow |

## 프로젝트 구조

```
pipeline-lab/
├── docker-compose.yml          # 전체 스택 정의
├── .env                        # 환경 변수 (git 제외)
├── config/
│   ├── kafka/                  # Kafka 설정
│   ├── nifi/                   # NiFi 설정
│   ├── flink/                  # Flink 설정
│   ├── spark/                  # Spark 설정
│   └── airflow/                # Airflow 설정
├── dags/                       # Airflow DAG 파일
├── docs/                       # 주차별 랩 가이드
├── scripts/                    # 헬스체크·DB 초기화 스크립트
├── spark-etl/                  # Week 5 배치 ETL 코드
├── spark-jobs/                 # Week 6~7 이관·오케스트레이션 코드
├── flink-jobs/                 # Week 4 Flink 스트림 처리 코드
└── data/
    ├── sample/                 # 샘플 데이터
    ├── settlement/             # Week 3 정산 CSV 파일
    └── delta/                  # Week 5~7 Delta Lake 저장소
```

## 종료 및 정리

```bash
# 컨테이너 중단 (데이터 볼륨 보존)
docker compose down

# 컨테이너 + 볼륨 전체 삭제 (초기화)
docker compose down -v
```
