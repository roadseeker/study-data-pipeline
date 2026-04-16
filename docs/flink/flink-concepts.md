# Flink 실시간 스트림 처리 핵심 개념 — 컨설팅 설명 자료

## 왜 Flink인가?

Spark Streaming(마이크로 배치)과 달리 Flink는 진정한 이벤트 단위 스트림 처리 엔진이다.
- 이벤트 발생 즉시 처리 → 밀리초 단위 레이턴시
- 이벤트 타임 기반 처리 → 지연 도착 데이터도 정확한 윈도우에 배치
- Exactly-once 상태 일관성 → 금융 데이터 정합성 보장
- 대규모 상태 관리 → TB 단위 상태도 안정적 처리
지
## 배치 vs 스트림 — Nexus Pay 관점

| 구분 | 배치 (Spark) | 스트림 (Flink) |
|------|-------------|---------------|
| 처리 단위 | 시간/일 단위 묶음 | 이벤트 단위 |
| 레이턴시 | 분~시간 | 밀리초~초 |
| 적합 업무 | 일별 정산, 월간 리포트 | 이상거래 탐지, 실시간 대시보드 |
| Nexus Pay 활용 | Week 5 (Spark 배치 ETL) | Week 4 (실시간 분석) |

## Event Time vs Processing Time

금융 거래에서는 반드시 Event Time을 사용해야 한다.
예: 23:59:58에 발생한 결제가 네트워크 지연으로 00:00:02에 Flink에 도착.
- Processing Time 기준: 다음 날 거래로 집계 (오류)
- Event Time 기준: 당일 거래로 정확하게 집계 (정확)

## Watermark 메커니즘

Watermark(t)의 의미: "타임스탬프 t 이전의 모든 이벤트는 도착 완료되었다."
- BoundedOutOfOrderness(5초): 최대 5초까지 늦게 도착하는 이벤트 허용
- Watermark 이후 도착 = Late Data → Side Output으로 별도 처리

## Checkpoint와 Exactly-once

Flink의 체크포인트는 분산 스냅샷이다.
1. JobManager가 체크포인트 배리어를 소스에 주입
2. 배리어가 연산자를 통과하면서 각 연산자가 상태를 스냅샷
3. 모든 연산자 스냅샷 완료 → 체크포인트 성공
4. 장애 발생 시 마지막 성공 체크포인트에서 복구
5. Kafka 소스 오프셋도 체크포인트에 포함 → 중복/유실 방지

