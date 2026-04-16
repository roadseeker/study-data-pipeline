# Nexus Pay NiFi 모니터링 가이드

## 핵심 모니터링 지표

| 지표 | 정상 범위 | 알림 기준 | 확인 방법 |
|------|----------|----------|----------|
| 큐 대기 FlowFile 수 | < 1,000 | > 5,000 | Connection 큐 크기 |
| Back-pressure 활성 여부 | OFF | ON | Connection 색상 변화 (노란색) |
| 프로세서 오류 | 0/분 | > 10/분 | Bulletin Board |
| Provenance 이벤트/분 | 가변 | 급감 시 확인 | Provenance 검색 |
| FlowFile 처리 시간 | < 5초/건 | > 30초/건 | 프로세서 상태 탭 |
| DLQ 토픽 메시지 | 0 | > 0 | Kafka 컨슈머 그룹 lag |

## Back-Pressure 설정 (Connection별)

| 유형 | 임계값 | 설명 |
|------|--------|------|
| FlowFile 수 기준 | 10,000개 | 큐에 쌓인 FlowFile 수 |
| 데이터 크기 기준 | 1 GB | 큐에 쌓인 데이터 총 크기 |

임계값 도달 시 상류 프로세서가 자동 일시 정지되어 시스템 과부하를 방지한다.

## Bulletin Board 활용

NiFi UI 우측 상단 **Bulletin Board** → 최근 경고·오류 메시지 확인.
프로세서별 Bulletin Level 설정으로 중요도에 따른 필터링 가능.

## 운영 일상 점검 체크리스트

- [ ] 모든 프로세서 Running 상태 확인
- [ ] Connection 큐 Back-pressure 발생 여부 확인
- [ ] Bulletin Board 오류 메시지 확인
- [ ] DLQ 토픽 메시지 유무 확인
- [ ] Provenance 저장 용량 확인

