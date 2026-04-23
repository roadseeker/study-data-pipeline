# data/lakehouse/delta/gold

Gold 계층은 비즈니스 사용자가 바로 조회할 수 있는 집계·리포팅용 Delta Lake 영역이다.

Week 5에서는 일별 매출 요약, 고객별 누적 거래 통계, 수수료 정산 결과 같은 Nexus Pay 정산·분석 산출물을 이 계층에 저장한다.

## 역할

- CFO·운영팀 대상 정산 리포트 데이터 제공
- BI, 대시보드, AI/ML Feature Dataset의 후보 입력 제공
- 감사 추적을 위한 Delta Lake Time Travel 검증 대상
