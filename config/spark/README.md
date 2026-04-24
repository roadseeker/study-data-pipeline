# config/spark

Spark 실행 환경과 커스텀 이미지 구성을 관리하는 폴더.

Week 1 Foundation 단계부터 Spark Master / Worker를 공통 기준으로 기동할 수 있도록 Dockerfile과 관련 설명을 둔다. Week 5 이후에는 같은 이미지를 배치 ETL, Delta Lake 연동, Kafka 배치 읽기 검증에 재사용한다.

## 포함 자산

- `Dockerfile`
  - `apache/spark:3.5.8` 기반 커스텀 Spark 이미지
  - `PyYAML` 기본 포함
  - `spark` 사용자 홈 디렉터리를 `/home/spark`로 고정
  - `spark-submit --packages` 시 Ivy cache 경로가 `/nonexistent`로 깨지지 않도록 보정

## 주요 운영 포인트

- Spark Master / Worker는 `spark-class` 명령으로 직접 기동한다.
- 공통 이미지 태그는 `study-data-pipeline/spark:3.5.8`를 사용한다.
- Delta Lake와 Kafka connector jar는 실행 시점의 `--packages` 또는 SparkSession 설정으로 주입한다.
- 이벤트 로그는 `./logs/spark -> /opt/spark-events`로 마운트한다.

## 관련 주차

- Week 1: Spark Master / Worker 기동 검증
- Week 5: Delta Lake 기반 배치 ETL 파이프라인 구현
- Week 6~7: 데이터 이관 및 오케스트레이션 연동
