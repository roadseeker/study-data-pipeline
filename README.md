# Pipeline Lab — 데이터 파이프라인 실습 환경

## 아키텍처 개요

```
수집 (Kafka · NiFi) → 변환 (Flink · Spark) → 저장 (PostgreSQL · Redis) → 오케스트레이션 (Airflow)
```

이 저장소는 **Nexus Pay** 시나리오를 기반으로 Apache 오픈소스 중심 데이터 파이프라인 랩을 단계적으로 구축하는 프로젝트다. Nexus Pay는 안정적이고 확장 가능한 결제 플랫폼을 목표로 하는 MSA 기반 Payment Service이며, 이 저장소에서는 해당 서비스의 데이터 파이프라인을 설계·구축·검증하는 역할을 수행한다. Week 1 범위에서는 7개 핵심 서비스를 Docker Compose로 통합 기동하고, 헬스체크·연동 검증·장애 복구 시나리오를 수행할 수 있는 실습 환경을 완성했다.

## 서비스 구성

| 서비스 | 컨테이너 | 포트 | 용도 |
|--------|---------|------|------|
| PostgreSQL 16 | lab-postgres | 5432 | 메타데이터·샘플 DB |
| Redis 7 | lab-redis | 6379 | 피처 스토어·캐시 |
| Kafka 3.7 (KRaft) | lab-kafka-1 / lab-kafka-2 / lab-kafka-3 | 30092, 30093, 30094 | 실시간 메시징 |
| NiFi 1.25 | lab-nifi | 8080 | 데이터 수집·라우팅 |
| Flink 1.18 | lab-flink-jm / lab-flink-tm | 8081 | 실시간 스트림 처리 |
| Spark 3.5 (official Apache image) | lab-spark-master / lab-spark-worker | 8082, 7077 | 배치 처리 |
| Airflow 2.8 | lab-airflow-web / lab-airflow-sched | 8083 | 워크플로우 오케스트레이션 |

## 빠른 시작

```bash
# 전체 스택 기동
docker compose up -d

# 환경 헬스체크
bash scripts/foundation/healthcheck-all.sh
```

## Week 1 검증 완료 범위

- 전체 스택 통합 헬스체크 `7/7` 통과
- Airflow `environment_healthcheck` DAG 등록 및 수동 실행 성공
- Kafka `nexuspay-transactions` 토픽 생성, 프로듀스/컨슈머 흐름 검증 성공
- PostgreSQL 집계 결과를 Redis 해시에 저장하는 피처 캐싱 시뮬레이션 성공
- 장애 테스트 3종 완료

장애 테스트 요약:
- Kafka 중단 후 재기동 시 토픽 및 기존 메시지 보존 확인
- PostgreSQL 중단 시 Airflow health 비정상 전환, 복구 후 정상화 확인
- Flink TaskManager 중단 시 슬롯 0 확인, 재기동 후 슬롯 4 복구 확인

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
├── docs/
│   ├── guides/                 # Week 1~8 랩 가이드
│   ├── foundation/             # 기반 환경 관련 문서
│   ├── kafka/                  # Kafka 운영·검증 문서
│   ├── nifi/                   # NiFi 개념·수집 문서
│   ├── flink/                  # Flink 문서
│   ├── spark/                  # Spark 및 이관 문서
│   ├── airflow/                # Airflow 문서
│   └── reports/                # 컨설팅 보고서 및 교차 주차 리포트
├── scripts/
│   ├── foundation/             # 헬스체크·기반 초기화 스크립트
│   ├── kafka/                  # Kafka producer/consumer/verify 스크립트
│   └── nifi/                   # NiFi 시뮬레이터·수집 보조 스크립트
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

## Week 2 준비 메모

- 현재 `nexuspay-transactions` 토픽은 Week 1 연동 검증용 임시 토픽이다.
- Week 2에서는 정식 Kafka 명명 규칙에 따라 `nexuspay.transactions.payment` 등으로 재구성할 예정이다.
- 브랜드 명칭은 `Nexus Pay`로 통일하고, 기술 식별자는 `nexuspay` / `NexusPay` 규칙을 사용한다.
- Git Bash 환경에서는 컨테이너 내부 절대경로 명령 실행 시 `docker exec ... sh -c '...'` 형태를 권장한다.
- Week 가이드는 `docs/guides/`에, 실제 산출물 문서와 스크립트는 기술 도메인 폴더에 저장한다.


