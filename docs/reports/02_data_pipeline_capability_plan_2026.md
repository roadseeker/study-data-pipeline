# 2026년 Data Pipeline 역량 강화 실행계획

이 문서는 3개월 역량 강화 계획 중 **data-pipeline** 영역의 상세 실행계획이다. 총괄 일정은 `01_capability_building_plan_2026.md`를 참조한다.

## 영역 A: 데이터파이프라인 잔여 실습 (3주 · 2026-05-04~2026-05-24)

Spark/Delta Lake는 4월 말까지 Week 5 산출물로 마무리한다. 5월의 영역 A는 Week 1~5에서 진행 완료했거나 마무리 중인 Kafka·NiFi·Flink·Spark 기반을 다시 길게 반복하지 않고, Spark JDBC·CDC·Airflow·E2E 통합을 3주 안에 압축 완주하는 일정으로 운영한다.

| 기간 | 집중 주제 | 데이터파이프라인 구축 수준 학습 내용 | 완료 기준 |
|------|----------|------------------------------------|----------|
| 2026-05-04~2026-05-10 | Spark JDBC + Full/Incremental Load | PostgreSQL/MySQL 원천 테이블을 Delta Lake로 full load, 증분 기준 컬럼 설계, 중복 방지 merge/upsert, 적재 이력 테이블 구성 | RDBMS → Delta 이관 실행, full/incremental 차이 설명, 재실행 시 중복 없는 적재 검증 |
| 2026-05-11~2026-05-17 | Debezium CDC + Airflow 오케스트레이션 | CDC 이벤트 구조 이해, Kafka Connect/Debezium 변경 이벤트 흐름 정리, Spark ETL을 Airflow DAG로 실행, 의존성·재시도·알림·백필 설계 | CDC 흐름 문서화, Airflow DAG 실행, 실패 재처리와 백필 시나리오 정리 |
| 2026-05-18~2026-05-24 | E2E 통합 + 장애/운영 리포트 | 수집→저장→변환→오케스트레이션→KPI 리포트 연결, 장애 주입, 특정 기간 재처리, 품질 지표와 비즈니스 KPI 산출 | End-to-End 리허설, 장애/복구 보고서, CTO/COO용 운영 리포트 작성 |

#### 기존 8주 상세 커리큘럼 참조

아래 Week 1~8 내용은 전체 데이터파이프라인 학습의 원래 상세 커리큘럼이다. 2026년 5월 실행계획에서는 진행 완료했거나 마무리 중인 Week 1~5를 기반으로 Week 6~8의 핵심을 3주 압축 일정으로 수행한다.

| 주차 | 주제 | 실습 내용 | 산출물 |
|------|------|---------|--------|
| Week 1 | 환경 구성 | Docker Compose 전체 스택 기동·검증 (Kafka·NiFi·Flink·Spark·Airflow·Redis·PostgreSQL) | 로컬 실습 환경 |
| Week 2 | 수집: Kafka 심화 | 토픽 설계, 파티션 전략, 컨슈머 그룹, 오프셋 관리, 복제 설정 | Kafka 운영 가이드 |
| Week 3 | 수집: NiFi | 다중 소스 수집 파이프라인, Provenance 추적, 데이터 흐름 시각화 | NiFi 플로우 구성 |
| Week 4 | 변환: Flink 심화 | 윈도우 집계, Watermark, 정확히 한 번(Exactly-once) 처리 | Flink 실시간 파이프라인 |
| Week 5 | 변환: Spark 배치 | 배치 ETL, 대용량 파티셔닝, Delta Lake 연동 | Spark ETL 코드 |
| Week 6 | 이관: Spark JDBC·CDC | RDBMS → Delta Lake 배치 이관, Debezium CDC 실시간 이관 시나리오 | 이관 파이프라인 |
| Week 7 | 오케스트레이션: Airflow 심화 | DAG 의존성 관리, SLA 모니터링, 장애 복구·알림 설정 | Airflow DAG 모음 |
| Week 8 | 통합 실습 | 전체 파이프라인 연동·검증 (수집→변환→저장→오케스트레이션) | 통합 파이프라인 레포 |

#### 1주차
>수행 시나리오: Nexus Pay의 데이터 파이프라인 현대화 PoC를 위해 Kafka·NiFi·Flink·Spark·Airflow·Redis·PostgreSQL 전체 스택이 로컬에서 정상 동작하는 실습 환경을 구성합니다. 이후 8주 실습의 기반이 되는 공통 환경을 검증하는 것이 목표입니다.
5일 일정 구성:

* Day 1: 프로젝트 구조 설계 + 기반 서비스 기동 — 디렉토리 구성, PostgreSQL·Redis 기동·검증
* Day 2: 메시징·수집 계층 구성 — Kafka(KRaft)·NiFi 기동·검증
* Day 3: 처리·오케스트레이션 계층 구성 — Flink·Spark·Airflow 기동·검증
* Day 4: 전체 스택 통합 기동 + 연동 검증 — 7개 컴포넌트 동시 기동, 데이터 흐름 확인
* Day 5: 장애 테스트 + 문서화 — 컨테이너 중단·복구 시나리오, README 및 환경 문서 정리

실습 예제 구성:

* `docker-compose.yml` + `.env`: Kafka·NiFi·Flink·Spark·Airflow·Redis·PostgreSQL 전체 실습 환경 정의
* `scripts/foundation/init-db.sql`: PostgreSQL 초기 스키마와 샘플 데이터 적재
* `scripts/foundation/healthcheck-all.sh` + `dags/healthcheck_dag.py`: 통합 헬스체크와 Airflow 기반 환경 검증 자동화
* `README.md`: 로컬 기동 절차, 포트, 장애 대응 기본 가이드 정리

#### 2주차
>수행 시나리오: Nexus Pay CTO가 일 평균 50만 건, 향후 200만 건까지 증가할 거래 이벤트를 Kafka로 수집하되 이상거래 탐지 팀과 정산 팀이 서로 간섭 없이 같은 데이터를 소비할 수 있도록 설계하라고 요구합니다. Kafka 토픽 아키텍처와 장애 복원력을 검증하는 것이 이번 주 과제입니다.
5일 일정 구성:

* Day 1: 토픽 설계 전략 — 비즈니스 이벤트 모델링, 토픽 명명 규칙, 파티션 수 산정
* Day 2: 파티션 키 설계 + 프로듀서 구현 — 키 기반 라우팅, 거래 데이터 생성기 구현
* Day 3: 컨슈머 그룹 + 오프셋 관리 — 다중 컨슈머 그룹, 수동 커밋, 리밸런싱 관찰
* Day 4: 멀티 브로커 + 복제 — 3-브로커 클러스터 구성, 복제 팩터, ISR 관리
* Day 5: 장애 시나리오 + 운영 가이드 문서화 — 브로커 장애 복구, 리더 선출, 운영 가이드 작성

실습 예제 구성:

* `config/kafka/topic-naming-convention.md` + `config/kafka/topic-configs.md`: 토픽 설계 기준과 운영 설정 초안
* `scripts/kafka/partition-calculator.sh` + `scripts/kafka/producer_nexuspay.py`: 파티션 수 산정과 거래 이벤트 프로듀서 구현
* `scripts/kafka/verify_partition_key.py` + `scripts/kafka/consumer_fraud_detection.py` + `scripts/kafka/consumer_settlement.py`: 파티션 키 검증과 다중 컨슈머 그룹 실습
* `docker-compose.yml` 업데이트 + `docs/kafka/fault-tolerance-report.md` + `docs/kafka/kafka-operations-guide.md`: 3-브로커 클러스터와 장애 복원력 운영 문서 정리

#### 3주차
>수행 시나리오: Nexus Pay CTO가 결제 API JSON, 레거시 정산 CSV, 고객 마스터 DB 데이터를 하나의 파이프라인으로 통합 수집하고, 감사 대응을 위해 데이터 출처와 흐름이 추적 가능해야 한다고 요구합니다. NiFi 기반 다중 소스 수집과 Provenance 추적 체계를 구축합니다.
5일 일정 구성:

* Day 1: NiFi 핵심 개념 + 프로세서 그룹 설계 — NiFi 아키텍처 이해, 기본 플로우 설계
* Day 2: REST API 수집 파이프라인 — InvokeHTTP 기반 실시간 API 수집, JSON 파싱·변환, 오류 처리
* Day 3: 파일·DB 수집 파이프라인 — CSV 감시·수집, PostgreSQL 기반 증분 추출
* Day 4: Kafka 연동 + 스키마 표준화 — PublishKafka 연동, 다중 소스 스키마 통합, 품질 라우팅
* Day 5: Provenance 추적 + 문서화 — 데이터 계보 추적, 모니터링 대시보드, 운영 가이드 작성

실습 예제 구성:

* `scripts/nifi/api_payment_simulator.py` + `scripts/nifi/csv_settlement_generator.py` + `scripts/nifi/init-customers.sql`: API·파일·DB 3개 소스 데이터 생성 및 초기화
* `config/nifi/process-group-design.md` + `config/nifi/jolt-spec-*.json`: NiFi 프로세서 그룹 설계와 소스별 표준화 변환 규칙
* `config/nifi/nexuspay-standard-schema.avsc` + `scripts/verify_nifi_pipeline.sh`: 공통 이벤트 스키마와 종합 검증 스크립트
* `docs/provenance-audit-guide.md` + `docs/nifi-monitoring-guide.md` + `docs/nifi-architecture.md`: 계보 추적, 운영, 아키텍처 문서화

#### 4주차
>수행 시나리오: NiFi를 통해 `nexuspay.events.ingested` 토픽으로 실시간 이벤트가 유입되자, Nexus Pay CTO가 5분 단위 집계, 실시간 이상거래 탐지, Exactly-once 보장을 요구합니다. Apache Flink로 실시간 변환 계층의 핵심 구간을 완성합니다.
5일 일정 구성:

* Day 1: Flink 핵심 개념 + 프로젝트 셋업 — 스트림 처리 모델 정리, Kafka 소스 연동
* Day 2: Watermark + 윈도우 집계 — 이벤트 타임 처리, Tumbling·Sliding·Session 윈도우 구현
* Day 3: 실시간 이상거래 탐지 — CEP 패턴 매칭, 룰 기반 탐지, Kafka·Redis 알림 싱크 연동
* Day 4: Exactly-once + 체크포인트 — 체크포인트 설정, Kafka 트랜잭션 싱크, 장애 복구 정합성 검증
* Day 5: 통합 테스트 + 운영 가이드 문서화 — 전체 실시간 파이프라인 검증, 성능 튜닝, 운영 가이드 작성

실습 예제 구성:

* `docs/flink-concepts.md` + `flink-jobs/pom.xml`: Flink 핵심 개념 정리와 Maven 기반 프로젝트 셋업
* `flink-jobs/src/main/java/com/nexuspay/flink/job/TransactionAggregationJob.java` + `FraudDetectionJob.java`: 윈도우 집계와 이상거래 탐지 핵심 잡 구현
* `scripts/flink_event_generator.py` + `scripts/fraud_alert_redis_sink.py`: 실시간 테스트 이벤트 생성과 Redis 알림 적재 실습
* `scripts/verify_flink_pipeline.sh` + `scripts/monitor_checkpoints.sh` + `docs/flink-operations-guide.md`: Exactly-once 검증, 체크포인트 모니터링, 운영 가이드 정리

#### 5주차 : 
>수행 시나리오: Nexus Pay CFO가 일별·월별 정산 리포트, 감사 추적(타임 트래블), 데이터 품질 검증을 요구하는 상황에서 Apache Spark 배치 ETL로 대응합니다.
5일 일정 구성:

* Day 1 — Spark 핵심 개념 정리 + PySpark 프로젝트 구조 + Kafka 배치 읽기 연동
* Day 2 — 메달리온 아키텍처 설계 + Bronze 레이어(원본 적재, Delta Lake, 멱등성 MERGE)
* Day 3 — Silver 레이어 + 데이터 품질 검증(YAML 규칙 기반 QualityChecker 모듈, critical 격리 / warning 플래그)
* Day 4 — Gold 3종 집계(일별 매출·고객 통계·수수료 정산) + Delta Lake 심화(타임 트래블, VACUUM, OPTIMIZE)
* Day 5 — 전체 ETL 통합 실행 + 검증 스크립트 + 배치 운영 가이드 + 아키텍처 문서

실습 예제 구성:

* `config/etl_config.yaml` + `config/quality_rules.yaml` + `lib/quality_checker.py`: ETL 설정과 데이터 품질 검증 규칙 모듈
* `spark-etl/jobs/bronze_ingestion.py` + `silver_transformation.py` + `gold_aggregation.py`: Bronze·Silver·Gold 메달리온 ETL 구현
* `spark-etl/jobs/full_etl_pipeline.py` + `spark-etl/scripts/verify_etl_pipeline.sh`: 전체 배치 파이프라인 오케스트레이션과 통합 검증
* `spark-etl/scripts/delta_time_travel_demo.py` + `spark-etl/scripts/delta_maintenance.sh` + `docs/spark-operations-guide.md`: Delta Lake 심화 기능과 배치 운영 가이드 정리


#### 6주차
>수행 시나리오: Nexus Pay CIO가 레거시 MySQL 정산 시스템의 3억 건 데이터를 Delta Lake로 이관해야 하는 과제를 제시합니다. 서비스 중단 없이 이관해야 하며, 테이블 특성에 따라 다른 전략이 필요합니다.
5일 일정 구성:

* Day 1: 이관 핵심 개념 정리 + MySQL 레거시 환경 구성 (4개 테이블: customers 500건, merchants 100건, transactions 10만건, settlements 5,000건), binlog ROW 포맷 활성화
* Day 2: Spark JDBC 배치 이관 — Full Export(고객·가맹점·거래 이력 초기 적재), Delta Lake Bronze 직접 적재, 병렬 분할 읽기 실습
* Day 3: Spark JDBC Incremental Append(거래 이력) + Lastmodified 패턴(정산 참고) + 소스↔타겟 정합성 검증 도구 개발
* Day 4: Debezium CDC + Kafka Connect 구성, MySQL binlog → Kafka → Spark Structured Streaming → Delta Lake MERGE(Upsert+Soft Delete) 실시간 파이프라인
* Day 5: 통합 정합성 검증, 이관 전략 가이드 문서화(고객 제안서 수준), Week 1~6 누적 아키텍처 문서, Git 커밋

실습 예제 구성:

* `docs/migration-concepts.md` + `docs/migration-target-tables.md` + `scripts/init-mysql.sql`: 이관 전략 정리와 MySQL 레거시 소스 환경 준비
* `spark-jobs/migration/jdbc_full_export.py` + `jdbc_incremental.py` + `verify_migration.py`: Spark JDBC 전체·증분 이관과 정합성 검증
* `config/debezium-mysql-connector.json` + `spark-jobs/migration/cdc_to_delta.py` + `docs/cdc-event-structure.md`: Debezium CDC와 Delta Lake 실시간 반영 실습
* `scripts/verify_migration_all.sh` + `docs/spark-jdbc-vs-debezium.md` + `docs/migration-strategy-guide.md`: 통합 검증과 배치/실시간 이관 선택 기준 문서화

산출물 15건, Week 7(Airflow 오케스트레이션)과의 연계를 위한 예고까지 포함했습니다.

#### 7주차
>수행 시나리오: Nexus Pay COO가 Week 1~6에서 구축한 배치 이관(Spark JDBC), 배치 ETL(Spark), CDC(Debezium) 파이프라인을 Apache Airflow로 운영 자동화하라고 요구합니다. 매일 03:00 이관, 06:00 이전 정산 리포트 완료, CDC 장애·SLA 지연 즉시 알림, 특정 날짜 백필·재처리가 가능해야 합니다.
5일 일정 구성:

* Day 1: Airflow 심화 개념 정리 + 운영 요구사항 모델링 + DAG 구조 설계 (Connections, Variables, TaskGroup, Trigger Rule)
* Day 2: 배치 이관 child DAG 구현 — Spark JDBC Full/Incremental + 정합성 검증 태스크 연결, master DAG 호출 기준의 수동 실행형 구조 설계
* Day 3: Spark ETL child DAG 연계 — Week 5 `full_etl_pipeline.py` 호출, `TriggerDagRunOperator(wait_for_completion=True)` 기반 순차 실행 구조 정리
* Day 4: CDC 모니터링 + 백필/복구 DAG 구현 — Kafka Connect 상태 점검, SLA miss 감지, 재시도·알림 콜백, 특정 날짜 재처리
* Day 5: 통합 마스터 DAG + 운영 가이드 문서화 — 일일 오케스트레이션 리허설, Runbook·장애 대응 절차 정리, Git 커밋

실습 예제 구성:

* `Dockerfile.airflow` + `plugins/alerting.py`: Airflow 커스텀 이미지와 실패 알림·SLA miss 플러그인 구성
* `dags/nexuspay_daily_migration_dag.py` + `spark-jobs/orchestration/master_refresh.py`: Spark JDBC 이관과 마스터 리프레시 DAG
* `dags/nexuspay_daily_etl_dag.py` + `spark-etl/jobs/publish_gold_report.py` + `spark-etl/jobs/verify_gold_outputs.py`: Week 5 배치 ETL 연계와 Gold 결과 검증 자동화
* `dags/nexuspay_cdc_monitoring_dag.py` + `dags/nexuspay_backfill_recovery_dag.py` + `dags/nexuspay_daily_master_dag.py` + `docs/airflow-operations-guide.md`: CDC 상태 점검, 백필·복구, 단일 스케줄 기반 통합 마스터 DAG, 운영 Runbook

#### 8주차
>수행 시나리오: Nexus Pay CTO와 COO가 Week 1~7에서 구축한 Kafka·NiFi·Flink·Spark·Spark JDBC·Debezium·Airflow 자산을 하나의 운영 시나리오로 끝까지 연결해 고객 수용 테스트 수준으로 검증하라고 요구합니다. API JSON, 정산 CSV, PostgreSQL, MySQL 변경 데이터가 동시에 유입되더라도 실시간 탐지와 배치 리포트가 일관되게 생성되어야 하며, 장애 주입·복구·백필까지 재현 가능해야 합니다.
5일 일정 구성:

* Day 1: 통합 요구사항 정리 + 성공 기준 수립 — 수용 테스트 범위 정의, 비즈니스 데이 시나리오 설계, 성공 기준 문서화
* Day 2: 통합 리허설 자동화 — API·CSV·Kafka·CDC 입력 시나리오 연결, Acceptance DAG 구현, master DAG 재사용 기반 운영 리허설 스크립트 작성
* Day 3: End-to-End 실행 + 품질 검증 — Kafka·NiFi·Flink·Spark·Delta Lake·Airflow 전 구간 실행, KPI 요약 및 계약 검증
* Day 4: 장애 주입 + 복구 리허설 — Flink·Kafka Connect·Airflow 장애 시나리오 테스트, 백필·재처리 검증
* Day 5: 최종 포트폴리오 정리 + 고객 보고서 — 최종 아키텍처 문서, 수용 테스트 보고서, 데모 스크립트, Git 커밋

실습 예제 구성:

* `config/e2e/business_day_scenario.yaml` + `docs/final/acceptance-criteria.md`: 통합 비즈니스 데이 시나리오와 고객 수용 기준 정의
* `scripts/e2e/run_business_day_rehearsal.sh` + `scripts/e2e/mysql_cdc_changes.sql`: API·CSV·Kafka·CDC를 묶은 운영 리허설 스크립트와 변경 시나리오
* `dags/nexuspay_acceptance_rehearsal_dag.py` + `scripts/e2e/verify_end_to_end.sh` + `spark-etl/jobs/build_pipeline_kpis.py`: 통합 수용 테스트 DAG, End-to-End 검증, 최종 KPI 요약
* `scripts/e2e/run_failure_drills.sh` + `scripts/e2e/collect_pipeline_snapshot.sh`: 장애 주입·복구 리허설과 운영 상태 스냅샷 수집
* `docs/final/failure-drill-report.md` + `docs/final/acceptance-test-report.md` + `docs/final/nexuspay-final-architecture.md` + `docs/final/portfolio-demo-script.md`: 최종 복구 보고서, 수용 테스트 결과, 아키텍처 문서, 포트폴리오 데모 자료

#### 최종 Git 저장소 디렉토리·파일 구조

8주 실습 완료 후 `pipeline-lab/` 저장소의 전체 구조다. 각 파일 우측의 `(Wn)`은 해당 파일이 처음 생성되는 주차를 나타낸다.

```
pipeline-lab/
│
├── .env                                        (W1) 환경 변수 (DB 접속, Airflow, Redis 등)
├── .gitignore                                  (W1) postgres-data/, redis-data/ 등 제외
├── docker-compose.yml                          (W1) 전체 스택 정의 — W2·W3·W6·W7에서 점진 확장
├── Dockerfile.airflow                          (W7) Airflow 커스텀 이미지 (SparkSubmit·Slack 포함)
├── README.md                                   (W1) 기동 절차, 포트 안내, 장애 대응 가이드
│
├── config/
│   ├── kafka/
│   │   ├── topic-naming-convention.md          (W2) 토픽 명명 규칙 (<도메인>.<엔티티>.<이벤트>)
│   │   └── topic-configs.md                    (W2) 토픽별 파티션·보존·복제 설정 기준
│   ├── nifi/
│   │   ├── process-group-design.md             (W3) 5개 프로세서 그룹 설계 문서
│   │   ├── jolt-spec-api-payment.json          (W3) REST API JSON → 표준 스키마 변환
│   │   ├── jolt-spec-file-settlement.json      (W3) 정산 CSV → 표준 스키마 변환
│   │   ├── jolt-spec-db-customer.json          (W3) 고객 DB → 표준 스키마 변환
│   │   └── nexuspay-standard-schema.avsc         (W3) 14필드 통합 Avro 스키마
│   ├── flink/                                  (W1) Flink 설정 예비 디렉토리
│   ├── spark/                                  (W1) Spark 설정 예비 디렉토리
│   ├── airflow/                                (W1) Airflow 설정 예비 디렉토리
│   ├── debezium-mysql-connector.json           (W6) Debezium MySQL CDC 커넥터 설정
│   └── e2e/
│       └── business_day_scenario.yaml          (W8) 통합 비즈니스 데이 시나리오 정의
│
├── dags/
│   ├── healthcheck_dag.py                      (W1) 7개 컴포넌트 헬스체크 DAG
│   ├── nexuspay_daily_migration_dag.py           (W7) Spark JDBC 배치 이관 DAG
│   ├── nexuspay_daily_etl_dag.py                 (W7) Spark ETL (Bronze→Silver→Gold) DAG
│   ├── nexuspay_cdc_monitoring_dag.py            (W7) Kafka Connect CDC 상태 감시 DAG
│   ├── nexuspay_backfill_recovery_dag.py         (W7) 특정 날짜 백필·재처리 DAG
│   ├── nexuspay_daily_master_dag.py              (W7) 일일 통합 오케스트레이션 마스터 DAG
│   └── nexuspay_acceptance_rehearsal_dag.py      (W8) 고객 수용 테스트 리허설 DAG
│
├── plugins/
│   └── alerting.py                             (W7) Slack·이메일 실패/SLA miss 알림 콜백
│
├── docs/
│   ├── kafka-operations-guide.md               (W2) Kafka 운영 가이드 (브로커·토픽·복제)
│   ├── fault-tolerance-report.md               (W2) 브로커 장애 복구 테스트 보고서
│   ├── nifi-concepts.md                        (W3) NiFi 핵심 개념 정리
│   ├── nifi-architecture.md                    (W3) NiFi 프로세서 그룹 아키텍처 문서
│   ├── nifi-monitoring-guide.md                (W3) NiFi 모니터링·백프레셔 가이드
│   ├── provenance-audit-guide.md               (W3) 데이터 계보(Provenance) 추적 가이드
│   ├── flink-concepts.md                       (W4) Flink 스트림 처리 핵심 개념
│   ├── flink-architecture.md                   (W4) Flink 잡 아키텍처 문서
│   ├── flink-operations-guide.md               (W4) Flink 체크포인트·장애 복구 가이드
│   ├── spark-concepts.md                       (W5) Spark 배치 처리 핵심 개념
│   ├── spark-architecture.md                   (W5) 메달리온 아키텍처 설계 문서
│   ├── spark-operations-guide.md               (W5) Spark ETL 배치 운영 가이드
│   ├── migration-concepts.md                   (W6) 이관 전략 3단계 (Full→Incremental→CDC)
│   ├── migration-target-tables.md              (W6) 이관 대상 4개 테이블 분석
│   ├── migration-architecture.md               (W6) 이관 파이프라인 아키텍처 문서
│   ├── migration-strategy-guide.md             (W6) 고객 제안서 수준 이관 전략 가이드
│   ├── spark-jdbc-vs-debezium.md               (W6) 배치 vs 실시간 이관 선택 기준
│   ├── cdc-event-structure.md                  (W6) Debezium CDC 이벤트 구조 정리
│   ├── airflow-operations-guide.md             (W7) Airflow DAG 운영 Runbook
│   └── final/
│       ├── acceptance-criteria.md              (W8) 수용 테스트 범위·성공 기준
│       ├── acceptance-test-report.md           (W8) 최종 수용 테스트 결과 보고서
│       ├── failure-drill-report.md             (W8) 장애 주입·복구 리허설 보고서
│       ├── nexuspay-final-architecture.md        (W8) 최종 전체 아키텍처 문서
│       └── portfolio-demo-script.md            (W8) 포트폴리오 데모 시나리오
│
├── scripts/
│   ├── init-db.sql                             (W1) PostgreSQL 초기 스키마·샘플 데이터
│   ├── init-customers.sql                      (W3) 고객 마스터 테이블 초기 데이터
│   ├── init-mysql.sql                          (W6) MySQL 레거시 4테이블 스키마·샘플 데이터
│   ├── healthcheck-all.sh                      (W1) 전체 컴포넌트 통합 헬스체크
│   ├── partition-calculator.sh                 (W2) 파티션 수 산정 스크립트
│   ├── producer_nexuspay.py                      (W2) Kafka 거래 이벤트 프로듀서 (confluent-kafka)
│   ├── verify_partition_key.py                 (W2) 파티션 키 라우팅 검증
│   ├── consumer_fraud_detection.py             (W2) 이상거래 탐지 컨슈머 그룹
│   ├── consumer_settlement.py                  (W2) 정산 처리 컨슈머 그룹
│   ├── api_payment_simulator.py                (W3) Flask 기반 결제 API 시뮬레이터
│   ├── csv_settlement_generator.py             (W3) 정산 CSV 파일 생성기
│   ├── measure_api_throughput.sh               (W3) API 처리량 측정
│   ├── verify_nifi_pipeline.sh                 (W3) NiFi 파이프라인 종합 검증
│   ├── flink_event_generator.py                (W4) Flink 실습용 이벤트 생성기 (confluent-kafka)
│   ├── fraud_alert_redis_sink.py               (W4) 이상거래 알림 → Redis 캐싱 싱크
│   ├── monitor_checkpoints.sh                  (W4) Flink 체크포인트 모니터링
│   ├── verify_flink_pipeline.sh                (W4) Flink 파이프라인 통합 검증
│   └── e2e/
│       ├── run_business_day_rehearsal.sh        (W8) 비즈니스 데이 통합 리허설
│       ├── mysql_cdc_changes.sql                (W8) CDC 변경 시나리오 (INSERT·UPDATE·DELETE)
│       ├── verify_end_to_end.sh                 (W8) 전 구간 End-to-End 검증
│       ├── run_failure_drills.sh                (W8) 장애 주입·복구 리허설
│       └── collect_pipeline_snapshot.sh         (W8) 운영 상태 스냅샷 수집
│
├── spark-etl/                                  ── Week 5 배치 ETL ──
│   ├── config/
│   │   ├── etl_config.yaml                     (W5) ETL 설정 (소스·싱크·배치 크기)
│   │   └── quality_rules.yaml                  (W5) 데이터 품질 규칙 (유효성·범위·정합성)
│   ├── lib/
│   │   ├── spark_session_factory.py            (W5) SparkSession 팩토리 (Delta Lake 설정 포함)
│   │   ├── schema_registry.py                  (W5) Bronze·Silver·Gold 스키마 정의
│   │   ├── quality_checker.py                  (W5) YAML 기반 품질 검증 엔진
│   │   └── delta_utils.py                      (W5) Delta Lake MERGE·VACUUM 유틸리티
│   ├── jobs/
│   │   ├── kafka_batch_read_test.py            (W5) Kafka 배치 읽기 연동 테스트
│   │   ├── bronze_ingestion.py                 (W5) Kafka → Bronze 원본 적재 (멱등성 MERGE)
│   │   ├── bronze_ingestion_file.py            (W5) 파일 기반 Bronze 적재
│   │   ├── silver_transformation.py            (W5) 정제·중복제거·품질검증 (Silver)
│   │   ├── gold_aggregation.py                 (W5) 일별매출·고객통계·수수료정산 (Gold 3종)
│   │   ├── full_etl_pipeline.py                (W5) Bronze→Silver→Gold 전체 오케스트레이션
│   │   ├── publish_gold_report.py              (W7) Gold 리포트 발행 (Airflow 연계)
│   │   ├── verify_gold_outputs.py              (W7) Gold 산출물 검증 (Airflow 연계)
│   │   └── build_pipeline_kpis.py              (W8) 최종 KPI 요약 (수용 테스트용)
│   └── scripts/
│       ├── generate_sample_data.py             (W5) 샘플 데이터 생성
│       ├── verify_bronze.py                    (W5) Bronze 레이어 검증
│       ├── delta_time_travel_demo.py           (W5) Delta Lake 타임 트래블 데모
│       ├── delta_maintenance.sh                (W5) VACUUM·OPTIMIZE 유지보수
│       └── verify_etl_pipeline.sh              (W5) 전체 ETL 파이프라인 통합 검증
│
├── spark-jobs/                                 ── Week 6~7 이관·오케스트레이션 ──
│   ├── migration/
│   │   ├── jdbc_full_export.py                 (W6) Spark JDBC Full Export (customers·merchants)
│   │   ├── jdbc_incremental.py                 (W6) Spark JDBC Incremental Append (transactions)
│   │   ├── cdc_to_delta.py                     (W6) CDC → Structured Streaming → Delta MERGE
│   │   └── verify_migration.py                 (W6) 소스↔타겟 정합성 검증
│   └── orchestration/
│       └── master_refresh.py                   (W7) 마스터 테이블 Full Refresh (Airflow 연계)
│
├── flink-jobs/                                 ── Week 4 실시간 스트림 처리 ──
│   ├── pom.xml                                 (W4) Maven 빌드 설정 (Flink 2.2.0, Java 17, Kafka 커넥터 4.0.1-2.0)
│   └── src/main/java/com/nexuspay/flink/
│       ├── job/
│       │   ├── TransactionAggregationJob.java  (W4) 5분 윈도우 거래 집계
│       │   ├── SessionWindowAnalysisJob.java   (W4) 세션 윈도우 사용자 행동 분석
│       │   └── FraudDetectionJob.java          (W4) 실시간 이상거래 탐지 (CEP)
│       ├── function/
│       │   ├── TransactionAggregateFunction.java   (W4) 집계 함수
│       │   ├── TransactionWindowFunction.java      (W4) 윈도우 결과 포매팅
│       │   ├── LateDataSideOutputFunction.java     (W4) 지연 데이터 Side Output 처리
│       │   └── FraudDetectionFunction.java         (W4) KeyedProcess 기반 탐지 로직
│       ├── model/
│       │   ├── NexusPayEvent.java                (W4) 14필드 이벤트 POJO
│       │   ├── AggregatedResult.java           (W4) 윈도우 집계 결과 모델
│       │   └── FraudAlert.java                 (W4) 이상거래 알림 모델
│       └── util/
│           ├── NexusPayEventDeserializer.java    (W4) JSON→POJO 역직렬화 (SNAKE_CASE 매핑)
│           ├── FlinkConfigUtil.java            (W4) Flink 설정 유틸리티
│           └── ExactlyOnceKafkaSinkBuilder.java (W4) Exactly-once Kafka 싱크 빌더
│
└── data/
    ├── sample/                                 (W1) 샘플 데이터
    ├── settlement/                             (W3) NiFi가 수집하는 정산 CSV 파일
    │   └── processed/                          (W3) 처리 완료 CSV 보관
    └── delta/                                  (W5~) Delta Lake 저장소
        ├── etl/                                (W5) Spark 배치 ETL 산출물
        │   ├── bronze/                         (W5) 원본 적재 (Kafka·파일 소스)
        │   ├── silver/                         (W5) 정제·품질검증 완료 데이터
        │   ├── gold/                           (W5) 비즈니스 집계 리포트
        │   │   ├── daily_summary/              (W5) 일별 매출 요약
        │   │   ├── customer_stats/             (W5) 고객 통계
        │   │   └── fee_settlement/             (W5) 수수료 정산
        │   └── checkpoints/                    (W5) Spark Structured Streaming 체크포인트
        ├── migration/                          (W6) RDBMS 이관 산출물
        │   ├── customers/                      (W6) 고객 마스터 (Full Export)
        │   ├── merchants/                      (W6) 가맹점 마스터 (Full Export)
        │   ├── transactions/                   (W6) 거래 이력 (Incremental Append)
        │   ├── settlements/                    (W6) 정산 (Lastmodified 패턴)
        │   └── settlements_cdc/                (W6) 정산 실시간 변경 (Debezium CDC)
        └── quality-reports/                    (W5) 품질 검증 결과 리포트
```

**산출물 통계**:

| 구분 | 수량 | 주요 내용 |
|------|------|----------|
| Python 스크립트 | 40+ | 프로듀서·컨슈머, ETL 잡, 이관, 시뮬레이터, 검증 |
| Java 클래스 | 13 | Flink 잡·함수·모델·유틸리티 |
| Shell 스크립트 | 10+ | 헬스체크, 파티션 산정, 파이프라인 검증, 장애 리허설 |
| Airflow DAG | 7 | 헬스체크, 이관, ETL, CDC, 백필, 마스터, 수용테스트 |
| 설정 파일 | 10+ | .yaml, .json, .avsc, .env, Dockerfile |
| SQL 파일 | 4 | PostgreSQL·MySQL 초기화, CDC 변경 시나리오 |
| 운영 문서 | 20+ | 아키텍처, 운영 가이드, 전략 문서, 수용 테스트 보고서 |
| Delta Lake 테이블 | 10 | Bronze·Silver·Gold 3계층 + 이관 5테이블 + 품질 리포트 |

**Docker 서비스 구성** (최종 `docker-compose.yml`):

| 서비스 | 컨테이너 | 호스트 포트 | 도입 주차 |
|--------|---------|-----------|----------|
| PostgreSQL | lab-postgres | 5432 | W1 |
| Redis | lab-redis | 6379 | W1 |
| Kafka (3-브로커) | lab-kafka-1/2/3 | 30092/30093/30094 | W1→W2 확장 |
| Apache NiFi | lab-nifi | 8080 | W1 |
| Flink JobManager | lab-flink-jm | 8081 | W1 |
| Flink TaskManager | lab-flink-tm | — | W1 |
| Spark Master | lab-spark-master | 8082, 7077 | W1 |
| Spark Worker | lab-spark-worker | — | W1 |
| Airflow Webserver | lab-airflow-web | 8083 | W1→W7 커스텀 이미지 |
| Airflow Scheduler | lab-airflow-sched | — | W1→W7 커스텀 이미지 |
| MySQL (레거시) | lab-mysql | 3306 | W6 |
| Kafka Connect | lab-kafka-connect | 8084 | W6 |
| Payment API | lab-payment-api | 5050 | W3 |
