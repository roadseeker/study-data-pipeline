# dags

Airflow DAG(Directed Acyclic Graph) 파일을 관리하는 폴더.

이 폴더는 Airflow 컨테이너(`lab-airflow-web`, `lab-airflow-sched`)에 볼륨 마운트되어 있어, 파일을 추가하면 Airflow가 자동으로 인식한다.

## DAG 목록

| 파일 | DAG ID | 역할 | 주차 |
|------|--------|------|------|
| healthcheck_dag.py | environment_healthcheck | 전체 컴포넌트 연결 검증 (수동 트리거) | Week 1 |

## DAG 작성 규칙

- 파일명: `{목적}_{dag}.py` (예: `settlement_dag.py`)
- 태그: 해당 주차와 도메인을 명시 (예: `tags=["week3", "settlement"]`)
- `schedule_interval=None`: 수동 트리거 전용
- `catchup=False`: 과거 실행 방지

## 관련 주차

- Week 1: environment_healthcheck DAG
- Week 3: 정산 파이프라인 DAG
- Week 5~7: Spark ETL 및 데이터 이관 오케스트레이션 DAG
