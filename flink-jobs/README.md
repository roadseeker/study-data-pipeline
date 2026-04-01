# flink-jobs

Flink 스트림 처리 잡 소스 코드를 관리하는 폴더.

Kafka 토픽에서 실시간으로 데이터를 소비하여 집계·변환·이상 탐지 등의 처리를 수행하는 Flink 잡이 위치한다.

## 관련 주차

- Week 4: Kafka → Flink 실시간 거래 스트림 처리 잡 구현
  - 실시간 집계 (tumbling window, sliding window)
  - 이상 거래 탐지 로직
  - 처리 결과 PostgreSQL / Redis 저장

## 빌드 및 실행

```bash
# Flink 잡 제출 (Week 4에서 상세 명령 제공)
docker exec lab-flink-jm flink run /opt/flink-jobs/<job>.jar
```
