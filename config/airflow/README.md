# config/airflow

Airflow 워크플로우 오케스트레이션 설정 파일을 관리하는 폴더.

Airflow 웹서버, 스케줄러, 연결 정보(Connections) 등의 설정이 위치한다.

## 주요 설정 항목

- 실행자 타입 (`AIRFLOW__CORE__EXECUTOR=LocalExecutor`)
- 메타데이터 DB 연결 (`AIRFLOW__DATABASE__SQL_ALCHEMY_CONN`)
- Fernet 암호화 키 (`AIRFLOW__CORE__FERNET_KEY`)
- 웹서버 시크릿 키 (`AIRFLOW__WEBSERVER__SECRET_KEY`)
- Connections: PostgreSQL, Redis, Kafka, Spark 연결 정보

## 관련 주차

- Week 1: Airflow 기동 및 environment_healthcheck DAG 검증
- Week 3 이후: 정산 파이프라인 DAG, Spark 잡 오케스트레이션 DAG 추가
