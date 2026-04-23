# Spark 배치 ETL 핵심 개념 — 컨설팅 설명 자료

## 왜 Spark인가?

Spark는 대용량 데이터셋의 배치 처리에 최적화된 분산 연산 엔진이다.
- 인메모리 연산 → MapReduce 대비 10~100배 빠른 처리 속도
- DataFrame API → SQL 친화적 인터페이스로 데이터 엔지니어·분석가 모두 사용 가능
- Catalyst 옵티마이저 → 실행 계획 자동 최적화로 수작업 튜닝 부담 감소
- Delta Lake 통합 → 데이터 레이크에 ACID 트랜잭션 부여

## 배치 처리의 정의

배치 처리란 일정 기간 동안 축적된 데이터를 한꺼번에 모아서 처리하는 방식이다.
- Nexus Pay 시나리오: 매일 새벽 3시에 전일 거래 전체를 읽어 정산 리포트 생성
- 장점: 전수 데이터 처리로 완전한 정확성 보장
- 단점: 처리 지연(레이턴시)이 존재 — 결과를 즉시 볼 수 없음

## Spark vs Flink — Nexus Pay 관점 정리

| 시나리오 | 엔진 | 이유 |
|----------|------|------|
| "1분 내 3건 이상 거래 탐지" | Flink | 밀리초 레이턴시 필요 |
| "전일 거래 유형별 매출 집계" | Spark | 전수 집계로 정합성 보장 |
| "5분 단위 실시간 대시보드" | Flink | 연속 스트림 처리 |
| "월간 수수료 정산 리포트" | Spark | 대용량 배치 집계 |
| "감사팀 과거 데이터 조회" | Spark + Delta | 타임 트래블 필요 |

## 메달리온 아키텍처 (Bronze → Silver → Gold)

데이터를 품질 단계별로 분리하여 관리하는 아키텍처 패턴이다.

```
[원본 소스] → Bronze(원본 그대로) → Silver(정제·표준화) → Gold(비즈니스 집계)
```

| 레이어 | 역할 | 데이터 상태 | Nexus Pay 예시 |
|--------|------|-----------|-------------|
| Bronze | 원본 적재 | 비정제, 스키마 그대로 | Kafka 원본 JSON 그대로 적재 |
| Silver | 정제·변환 | 스키마 표준화, 중복 제거, 타입 변환 | null 제거, 타임스탬프 파싱, 중복 거래 제거 |
| Gold | 비즈니스 집계 | 바로 리포팅 가능한 상태 | 일별 매출, 수수료 정산, 고객 누적 통계 |

## Delta Lake 핵심 기능

### 타임 트래블 (Time Travel)
```python
# 특정 버전으로 조회
df = spark.read.format("delta").option("versionAsOf", 3).load(path)

# 특정 시점으로 조회
df = spark.read.format("delta").option("timestampAsOf", "2026-03-30").load(path)
```

### MERGE (Upsert)
```python
# 조건에 따라 INSERT 또는 UPDATE
deltaTable.alias("target").merge(
    updates.alias("source"),
    "target.tx_id = source.tx_id"
).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
```

### 스키마 진화
```python
df.write.format("delta").option("mergeSchema", "true").mode("append").save(path)
```

