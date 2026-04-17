# 데이터 파이프라인 · AI/ML 컨설팅 사업화 전략 보고서

**작성일**: 2026년 3월 30일
**버전**: v2.0
**형태**: 독립 컨설팅 (1인 창업)

---

## 목차

1. 사업 개요
2. 시장 현황 및 규모
3. 두 컨설팅 영역 정의
4. 기술 스택 및 핵심 역량
5. 경쟁 우위 분석
6. 사업화 로드맵
7. 1인 운영 전략 (창업 초기 2년)
8. 준비 체크리스트
9. 리스크 및 대응 전략
10. ML 역량 강화 학습 일정
11. 수익 목표 및 재무 계획
12. 결론

---

## 1. 사업 개요

### 사업 컨셉

데이터 파이프라인 구축 컨설팅과 AI·ML 도입 컨설팅을 단일 컨설턴트가 설계하는 풀스택 데이터·AI 컨설팅 사업이다. 두 영역은 분리되지 않는다. AI는 데이터 파이프라인 없이 작동하지 않으며, 파이프라인만으로는 비즈니스 가치가 제한된다. 이 연결을 이해하고 설계할 수 있는 컨설턴트가 한국 시장에서 절대적으로 드물다는 점이 핵심 차별점이다.

### 사업 정의

- **영역 A**: Apache 오픈소스 기반 데이터 파이프라인 컨설팅
- **영역 B**: ML 모델 설계·구축·배포 및 LLM/RAG 도입 컨설팅
- **타겟 고객**: 금융·핀테크·제조 중견기업 (레거시 시스템 보유, 자체 AI 역량 부재)
- **차별점**: 오픈소스 기반 비용 절감 + 데이터 파이프라인부터 AI까지 단일 설계 역량
- **운영 형태**: 창업 초기 2년 1인 체제 → 이후 팀 확장

### 사업 배경

2026년은 AI 도입이 실험 단계를 넘어 전사 인프라로 자리잡는 전환점이다. 동시에 AI 프로젝트의 상당수가 성과를 내지 못하는 현실이 확인되고 있으며, 그 주요 원인은 데이터 인프라 미비다. 기업들이 AI 실패를 경험한 뒤 "왜 안 됐나"를 분석하면 결국 데이터 파이프라인 문제로 귀결된다. 이 구조적 수요가 본 사업의 시장 진입 근거다.

---

## 2. 시장 현황 및 규모

### 국내 데이터 산업 시장

| 구분 | 규모 | 비고 |
|------|------|------|
| 데이터 산업 전체 (2024E) | 30조 7,462억원 | 전년 대비 5.8% 성장 |
| **데이터 구축·컨설팅 서비스업** | **10조 5,676억원** | **전체 34.4% — 직접 타겟 시장** |
| 데이터 판매·제공 서비스업 | 14조 6,443억원 | 전체 47.6% |
| 데이터 처리·관리 솔루션 | 5조 5,343억원 | 전체 18.0% |
| 데이터 파이프라인 특화 SAM | 약 2.1조원 | 순수 컨설팅 중 파이프라인 관련 추산 |
| 초기 현실 목표 SOM | 100~300억원 | Apache 오픈소스 특화, 초기 3~5년 |

출처: 과학기술정보통신부·한국데이터산업진흥원 「2024 데이터산업현황조사」

### 시장 성장성

- 국내 데이터 산업 연평균 성장률 (2019~2023): **21.2%**
- 2028년 국내 데이터 산업 전망 규모: **49조원** (연평균 12.7% 성장 가정)
- 글로벌 데이터 파이프라인 시장 (2024→2032): 100억 달러 → CAGR **19.9%** 성장

### 수요 신호 — 2026년 국내 기업 IT 우선순위 조사

| 항목 | 응답률 | 의미 |
|------|--------|------|
| 생성형 AI를 최우선 과제로 지목 | 63% (1위) | 수요 확실 |
| AI/ML 및 자동화를 우선과제로 지목 | 40% (3위) | 수요 지속 |
| AI·데이터 인재 부족을 도전 과제로 지목 | 40% (2위) | **외부 의존 필요** |
| AI 과제 수행 역량 보유 기업 | **7%** | **93%가 역량 공백** |
| 역량 격차 해소에 외부 전문가 활용 계획 | 65% | **직접적 컨설팅 수요** |

출처: CIO Korea 「2026 IT 전망 조사」 (2025년 10~11월, 884명 응답)

### 시장 구조 판단

딜로이트 2026 TMT 전망에 따르면 AI 도입 초점이 "무엇을 만들 수 있는가"에서 "어떻게 실제 비즈니스에 적용하고 운영할 것인가"로 이동하고 있다. 구축 역량보다 설계·운영 역량이 더 중요해지는 시점으로, 독립 컨설턴트에게 유리한 환경이 형성되고 있다.

---

## 3. 두 컨설팅 영역 정의

### 영역 A: 데이터 파이프라인 컨설팅

**핵심 가치 제안**: 레거시 RDBMS에 갇힌 데이터를 실시간 처리 가능한 현대 아키텍처로 전환. 오픈소스 기반으로 상용 툴 대비 라이선스 비용 없이 동등한 성능 구현.

**주요 서비스**:

- 데이터 파이프라인 아키텍처 설계 및 컨설팅
- 실시간 데이터 수집·변환·저장 체계 구축
- 레거시 RDBMS → 현대 데이터 플랫폼 이관 프로젝트
- 데이터 오케스트레이션 및 모니터링 체계 수립
- 데이터 거버넌스 및 품질 관리 체계 구축

**고객이 이관을 원하는 주요 이유**:

- Oracle·SQL Server 등 고비용 라이선스 절감 필요
- 기존 RDBMS의 TB 규모 한계 → PB 이상 처리 구조 필요
- AI 도입을 위한 데이터 인프라 현대화 필요
- 비정형 데이터(로그, JSON, 이미지)를 포함한 통합 플랫폼 구성 필요

**예상 단가**:

| 서비스 유형 | 단가 범위 | 기간 |
|------------|----------|------|
| 아키텍처 설계 컨설팅 | 500~3,000만원 | 1~2개월 |
| 파이프라인 구축 프로젝트 | 3,000만~1억원 | 2~4개월 |
| 운영 유지보수 계약 | 월 200~500만원 | 계속 |

### 영역 B: AI·ML 컨설팅

**핵심 가치 제안**: 데이터 파이프라인 위에 AI를 얹는 풀스택 설계. "AI 도입하고 싶은데 어디서부터 시작해야 하는지 모르는" 기업의 실질적 진입점 역할.

**주요 서비스**:

- AI 도입 전략 수립 및 로드맵 설계
- ML 모델 선정·학습·평가·배포 컨설팅
- 실험 추적 및 모델 버전 관리 체계 구축
- LLM/RAG 기반 사내 문서 Q&A 시스템 구축
- 모델 재학습 자동화 파이프라인 설계
- AI 성과 측정 지표(KPI) 수립

**ML 모델 유형별 주요 적용 시나리오**:

| 모델 유형 | 대표 시나리오 | 기대 효과 |
|-----------|-------------|----------|
| 분류 | 이상거래 탐지, 고객 이탈 예측 | 손실 감소, 선제 대응 |
| 회귀 | 매출·수요 예측, 가격 산정 | 의사결정 정확도 향상 |
| 군집화 | 고객 세분화, 이상 패턴 탐지 | 타겟 마케팅, 리스크 관리 |
| 딥러닝 | 이미지 품질 검사, 문서 분류 | 검사 자동화, 비용 절감 |
| LLM/RAG | 사내 문서 Q&A, 보고서 자동화 | 업무 효율화 |
| 강화학습 | 공정 최적화, 추천 시스템 | 운영 효율 개선 |

**예상 단가**:

| 서비스 유형 | 단가 범위 | 기간 |
|------------|----------|------|
| AI 도입 전략 컨설팅 | 1,000~5,000만원 | 1~3개월 |
| 모델 구축 프로젝트 | 5,000만~3억원 | 3~6개월 |
| 재학습·운영 계약 | 월 300~800만원 | 계속 |

### 두 영역의 연결 구조

데이터 파이프라인 컨설팅이 AI 컨설팅의 선행 조건이다. 파이프라인 프로젝트를 통해 고객의 데이터 인프라를 구축하고, 자연스럽게 그 위에 AI 모델 도입으로 확장하는 흐름이 가장 이상적인 고객 생애가치(LTV) 구조다.

```
파이프라인 설계 컨설팅
        ↓
파이프라인 구축 프로젝트
        ↓
데이터 품질·거버넌스 수립
        ↓
AI·ML 도입 전략 수립
        ↓
모델 구축 및 배포
        ↓
운영·재학습 유지보수 (반복 수익)
```

---

## 4. 기술 스택 및 핵심 역량

### 데이터 파이프라인 영역

| 계층 | 도구 | 역할 |
|------|------|------|
| 수집(Ingest) | Apache Kafka, Apache NiFi, Kafka Connect | 실시간·배치 데이터 수집 |
| 변환(Transform) | Apache Flink, Apache Spark, dbt | 실시간 처리·피처 계산·ETL |
| 저장(Store) | HDFS, Amazon S3, Apache Iceberg | 데이터 레이크·웨어하우스 |
| 오케스트레이션 | Apache Airflow | 스케줄·모니터링·재시도 |
| 이관 특화 | Spark JDBC, Debezium(CDC) | RDBMS 데이터 이관 |
| 피처 스토어 | Redis, PostgreSQL | 실시간·배치 피처 관리 |

### 기술 상태 점검 (`2026-04-01` 기준)

| 기술 | 사용 맥락 | 상태 점검 | 비고 |
|------|-----------|-----------|------|
| Apache Kafka | 이벤트 수집·전달 | 활성 오픈소스 | Apache 프로젝트, 지속 릴리스 진행 |
| Apache NiFi | 다중 소스 수집 | 활성 오픈소스 | Apache 프로젝트, 2.x 계열 운영 가능 |
| Kafka Connect | CDC·커넥터 실행 | 활성 오픈소스 | Kafka 생태계 핵심 구성 요소 |
| Apache Flink | 실시간 변환 | 활성 오픈소스 | 스트림 처리 엔진으로 지속 개발 중 |
| Apache Spark | 배치 ETL·JDBC 이관 | 활성 오픈소스 | 4.x 계열 기준 지속 릴리스 진행 |
| Apache Airflow | 오케스트레이션 | 활성 오픈소스 | 3.x 계열 기준 지속 개발 중 |
| Debezium | CDC | 활성 오픈소스 | Kafka Connect 기반 CDC 프로젝트 |
| Delta Lake | 레이크하우스 저장 | 활성 오픈소스 | Spark 기반 Delta 테이블 관리에 적합 |
| Apache Iceberg | 테이블 포맷 | 활성 오픈소스 | 데이터 레이크 테이블 포맷으로 활발히 사용 |
| HDFS | 레이크 저장소 | 활성 오픈소스 | Apache Hadoop 생태계 구성 요소 |
| PostgreSQL | 운영·결과 저장 | 활성 오픈소스 | 커뮤니티 주도 RDBMS, 지속 릴리스 진행 |
| MySQL Community | 레거시 소스 DB 실습 | 활성 오픈소스 | 실습용 원천 시스템으로 사용 |
| dbt Core | 변환 계층 보조 | 활성 오픈소스 | SQL 기반 변환 도구, 선택적 도입 가능 |
| Docker Compose | 로컬 통합 환경 | 활성 오픈소스 도구 | Docker Compose Spec 기반 실습 환경 구성 |
| Amazon S3 | 클라우드 저장소 | 오픈소스 아님 | AWS 관리형 서비스, 레이크 저장소로 활용 가능 |
| Redis | 캐시·피처 스토어 | 활성이나 라이선스 주의 | `2025-05-01` 이후 Redis 8에 AGPLv3 옵션 추가, 버전별 라이선스 확인 필요 |

> 점검 결과 요약: 현재 프로젝트 핵심 스택에는 `Apache Attic` 이관 또는 공식 종료 상태의 기술이 포함되어 있지 않다. 다만 `Amazon S3`는 오픈소스가 아닌 관리형 서비스이며, `Redis`는 버전별 라이선스 정책을 확인해 사용하는 것이 바람직하다.

### AI·ML 영역

| 계층 | 도구 | 역할 |
|------|------|------|
| ML 프레임워크 | scikit-learn, XGBoost, LightGBM | 분류·회귀·군집화 모델 |
| 실험 추적 | MLflow | 모델 버전 관리·배포 |
| 추론 서버 | FastAPI, uvicorn | 실시간 모델 서빙 |
| LLM (로컬) | Ollama (llama3.2, mistral) | 비용 없는 로컬 LLM |
| LLM (클라우드) | OpenAI GPT-4o-mini | 고품질 자연어 생성 |
| 벡터 DB | Qdrant | RAG 문서 검색 |
| 임베딩 | sentence-transformers | 텍스트 벡터화 |
| 대시보드 | Streamlit | 결과 시각화 |

### 인프라

- **컨테이너**: Docker, Docker Compose
- **클라우드**: AWS (MSK, S3, RDS), 카카오클라우드
- **OS**: Ubuntu Linux, macOS

---

## 5. 경쟁 우위 분석

### 시장 내 포지셔닝

| 경쟁자 | 강점 | 약점 | 대응 전략 |
|--------|------|------|----------|
| 대형 SI (삼성SDS, LG CNS, SK C&C) | 브랜드, 대형 프로젝트 수주 역량 | 중소·중견 대상 비용 과다, 속도 느림 | 중견 이하 빠른 납기·저비용 공략 |
| AI 전문 스타트업 | 최신 AI 기술 | 데이터 파이프라인 인프라 약함 | 파이프라인~AI 통합 설계 강조 |
| 클라우드 MSP | 관리형 서비스 편의성 | 오픈소스 깊이 부족 | 오픈소스 기반 비용 절감 가치 제안 |
| 퓨처젠 씨플래닛 등 국내 전문사 | Confluent 파트너십 | 상용 라이선스 의존적 | Apache 순수 오픈소스 스택 포지셔닝 |

### 핵심 차별점 3가지

**1. 풀스택 연결 역량**

데이터 수집부터 AI 추론까지 단일 컨설턴트가 전체를 설계한다. 대형 SI는 파이프라인팀과 AI팀이 분리되어 연결 설계에 실패하는 경우가 많으며, AI 스타트업은 데이터 인프라를 다루지 못한다. 두 영역을 모두 이해하는 컨설턴트가 한국 시장에서 매우 드물다.

**2. 오픈소스 기반 비용 절감 포지셔닝**

Confluent·Informatica·Talend 등 상용 툴의 라이선스 없이 Apache 오픈소스만으로 동등한 성능을 구현한다. 중견기업 IT 예산 제약에 직접 소구하는 가치 제안으로, "라이선스 비용 절감"이 제안서의 첫 페이지가 된다.

**3. 파이프라인을 AI 도입의 선행 조건으로 포지셔닝**

AI 프로젝트 실패의 주요 원인이 데이터 인프라 미비임을 설득 포인트로 활용한다. "파이프라인 먼저, AI 나중"이라는 접근으로 파이프라인 컨설팅을 선행 판매하고 자연스럽게 AI 컨설팅으로 확장한다. AI ROI 회의론이 오히려 진입점이 된다.

---

## 6. 사업화 로드맵

### 전체 일정 개요

| 단계 | 기간 | 핵심 목표 | 운영 형태 |
|------|------|----------|----------|
| Phase 1 | 현재~3개월 (풀타임) | 파이프라인 실습 + ML 실습 + 포트폴리오 구성 | 1인 (준비) |
| Phase 2 | 3~9개월 | 레퍼런스 1~2건 확보 | 1인 (초기 매출) |
| Phase 3 | 9~15개월 | 월 매출 1,500만원 안정화 | 1인 (성장) |
| Phase 4 | 15~21개월 | 월 매출 3,000만원 + 확장 준비 | 1인 → 팀 검토 |
| Phase 5 | 21개월~ | 팀 구성 + 도메인 특화 | 팀 체제 전환 |

### Phase 1: 역량 완성 (현재~3개월, 풀타임)

**목표**: 데이터 파이프라인 실습 완주 + ML 6종 모델 실습 완료 + 포트폴리오 구성 + 사업 기반 마련

**데이터 파이프라인 실습 완주 (8주 · Month 1~2)**:
- Kafka 브로커 구성 및 토픽 설계·운영 실습
- NiFi 기반 다중 소스 데이터 수집 파이프라인 구축
- Flink 실시간 스트림 처리 및 피처 계산 실습
- Spark 배치 ETL 파이프라인 설계 및 구현
- RDBMS → Delta Lake 데이터 이관 실습 (Spark JDBC, Debezium CDC)
- Airflow DAG 오케스트레이션 및 장애 복구 시나리오 실습
- Redis 피처 스토어 + PostgreSQL 결과 저장 연동
- Docker Compose 기반 전체 스택 통합 구동 및 검증

**ML 6종 모델 실습 완주 (8주 · Month 3~4)**:
- 16주 ML 실습 일정 완주 (분류→회귀→군집화→딥러닝→LLM→강화학습)
- 각 모델별 실제 데이터셋 활용 및 포트폴리오 산출물 구성

**사업 기반 마련**:
- 구현 완료된 파이프라인 + ML 프로젝트 GitHub 공개 포트폴리오 정리
- 사업자 등록 (IT 컨설팅업)
- ROI 중심 제안서 템플릿 1벌 작성
- 컨설팅 계약서 템플릿 준비 (NDA, 지식재산권 조항 포함)
- 기술 블로그 개설 (잠자는 영업사원 역할)

산출물: 파이프라인 실습 코드 저장소, ML 포트폴리오 3건, 제안서 템플릿, 사업자 등록증, 기술 블로그

### Phase 2: 레퍼런스 확보 (6~12개월)

**목표**: 유료 프로젝트 1~2건 수주 + 사례 문서화

주요 활동:
- 금융·핀테크 도메인 네트워크를 통한 첫 프로젝트 수주 (저가 또는 성과 기반)
- 데이터 파이프라인 아키텍처 설계 → 납품 → 사례 문서화
- 기술 블로그 정기 발행 (데이터 파이프라인, ML 실전 경험)
- 컨퍼런스·밋업 발표 1회 이상 (데이터 파이프라인 + AI 통합 주제)
- 첫 유지보수 계약 확보 시도

산출물: 레퍼런스 사례 1~2건, 발표 이력, 유지보수 계약 1건

### Phase 3: 사업화 안정 (12~18개월)

**목표**: 월 매출 1,000~1,500만원 안정화

주요 활동:
- 레퍼런스 기반 금융·제조 중견기업 영업 확대
- 운영 유지보수 계약 누적으로 반복 수익 구조 강화
- 파이프라인 + AI 패키지 서비스 상품화 (정형화된 메뉴 구성)
- 단가 점진적 상향 조정
- 파트너 네트워크 구성 시작 (인프라, 보안, 법무 전문가 1인씩)

산출물: 반복 수익 계약 2~3건, 패키지 서비스 메뉴, 파트너 네트워크

### Phase 4: 확장 준비 (18~24개월)

**목표**: 월 매출 2,500~3,500만원 + 팀 구성 검토

주요 활동:
- 금융 데이터 파이프라인 또는 제조 AI 도메인 특화 포지셔닝
- 정부 지원 사업 참여 (과기부, 중소기업진흥공단 AI 도입 지원)
- 교육·워크숍 서비스 추가 (내부 역량 이전 패키지)
- 팀 구성 또는 법인 전환 검토 시점

산출물: 도메인 특화 레퍼런스, 교육 서비스 패키지, 법인 전환 검토 보고서

### Phase 5: 팀 체제 (24개월~)

**목표**: 파트너 또는 주니어 컨설턴트 추가 + 수주 규모 확대

주요 활동:
- 주니어 컨설턴트 1인 채용 또는 프리랜서 파트너십
- 동시 프로젝트 3건 이상 수주 가능한 체제 구성
- 특정 산업 버티컬 전문 컨설팅펌 포지셔닝

---

## 7. 1인 운영 전략 (창업 초기 2년)

### 1인 체제를 유지해야 하는 이유

초기 2년은 1인 체제가 팀 운영보다 전략적으로 유리하다.

**비용 구조의 가벼움**: 직원 고용 시 월 400~600만원의 고정 인건비가 발생한다. 초기에는 프로젝트가 불규칙하기 때문에 고정비가 적을수록 생존 가능성이 높다. 1인 구조는 매출이 없는 달에도 버틸 수 있다.

**의사결정의 신속성**: 고객과 미팅 당일 제안서 수정이 가능하다. 팀이 생기면 내부 조율 비용과 시간이 발생한다.

**고단가 정당화**: "전문가 1인"이라는 포지셔닝은 오히려 고단가를 정당화한다. 팀을 꾸려야 한다는 부담이 없기 때문에 컨설팅 일당 기준으로 대형 SI보다 높은 단가를 받을 수 있다.

### 월별 수입 현실 예측

| 시기 | 예상 월 수입 | 주요 수입원 |
|------|------------|-----------|
| 1~3개월 | 0원 | 풀타임 실습 기간 (수입 없음) |
| 4~6개월 | 100~500만원 | 첫 프로젝트 착수금 |
| 7~12개월 | 300~1,000만원 | 프로젝트 + 유지보수 시작 |
| 13~18개월 | 1,000~2,000만원 | 복수 프로젝트 + 유지보수 누적 |
| 19~24개월 | 2,000~3,500만원 | 안정적 파이프라인 구축 |

**핵심**: 첫 번째 유지보수 계약(월 200~300만원)이 생기는 순간 심리적 안정과 영업 여유가 동시에 생긴다. 이것을 최대한 빨리 확보하는 것이 초기 생존의 핵심이다.

### 1인 운영의 현실적 한계와 대응

**한계 1: 동시 프로젝트 수 제한**

대응: 동시 진행 프로젝트를 최대 2건으로 제한한다. 파이프라인 구축 후 운영 단계에서 고객 내부 인력에게 역량을 이전하는 구조를 설계해 관여도를 점진적으로 낮춘다. 납기 일정을 여유 있게 제안한다.

**한계 2: 전문 영역 외 요구 발생**

대응: 파트너 네트워크를 미리 구성한다. 클라우드 인프라, 보안, 법무 분야 전문가 각 1인과 협력 관계를 유지한다. 직원이 아닌 프리랜서 협력 방식이므로 고정비가 발생하지 않는다.

**한계 3: 영업과 실행의 동시 부담**

대응: 기술 블로그와 GitHub 포트폴리오가 잠자는 영업사원 역할을 한다. 콘텐츠가 쌓이면 인바운드 문의가 발생하기 시작한다. 이 구조를 2년간 꾸준히 구축하는 것이 가장 중요한 병행 투자다.

**한계 4: 장기 프로젝트 중 공백 발생**

대응: 프로젝트 계약 시 마일스톤 기반 단계별 정산을 적용한다. 한 프로젝트가 끝나기 2개월 전부터 다음 프로젝트 영업을 시작하는 리듬을 유지한다.

### 생존을 위한 재무 조건

사업 시작 전 최소 **6개월치 생활비 준비금**을 확보해야 한다. 월 생활비를 300만원으로 가정하면 1,800만원의 준비금이 필요하다. 이 완충재가 없으면 조급함이 생겨 저가 수주나 잘못된 계약으로 이어질 위험이 있다.

---

## 8. 준비 체크리스트

### 이미 보유한 역량 (강점)

- [x] 데이터 파이프라인 전체 아키텍처 이해 (수집·변환·저장·오케스트레이션)
- [x] ML 모델 학습~배포 전체 흐름 파악
- [x] RAG + 벡터 DB + LLM 연동 설계 경험
- [x] Docker 기반 전체 스택 로컬 구동 경험
- [x] 금융·ETF 데이터 도메인 이해
- [x] 파이프라인~AI 통합 풀스택 예제 프로젝트 완성
- [x] Airflow DAG 오케스트레이션 설계 경험

### 6개월 내 추가 필요 항목

- [ ] **데이터 파이프라인 실습 완주 (8주)** — Kafka·NiFi·Flink·Spark·Spark JDBC·Airflow 전 계층 실습
- [ ] ML 6종 모델 실습 완료 (16주 학습 일정 이행)
- [ ] 실제 데이터셋으로 포트폴리오 3건 구성
- [ ] GitHub 포트폴리오 공개 정리
- [ ] 사업자 등록 (IT 컨설팅업)
- [ ] ROI 중심 컨설팅 제안서 템플릿 작성
- [ ] 컨설팅 계약서 템플릿 준비
- [ ] 기술 블로그 개설
- [ ] 첫 레퍼런스 고객 1건 확보

### 12개월 내 추가 준비 항목

- [ ] 금융 도메인 특화 레퍼런스 아키텍처 문서
- [ ] 파이프라인 도입 ROI 계산 템플릿
- [ ] 서비스 패키지 상품화 (단계별 메뉴)
- [ ] 파트너 네트워크 구성 (인프라·보안·법무)
- [ ] 기술 발표 이력 1건 이상

---

## 9. 리스크 및 대응 전략

### 리스크 1: 대형 SI와의 경쟁

**내용**: 삼성SDS, LG CNS, SK C&C 등이 동일 시장을 공략 중.

**대응**: 대형 SI가 접근하기 어려운 연 매출 100~500억 규모 중견기업에 집중한다. 납기 속도(대형 SI 6개월 vs 독립 컨설턴트 2개월)와 비용(대형 SI 3억 vs 독립 5천만원) 우위로 차별화한다.

### 리스크 2: 클라우드 관리형 서비스 대체

**내용**: AWS MSK, Azure Event Hub 등 관리형 서비스가 구축 수요 일부 대체.

**대응**: 관리형 서비스가 해결하지 못하는 레거시 시스템 연동, 온프레미스 요건, 복잡한 변환 로직 설계를 집중 공략한다. 관리형 서비스 위에 올라가는 아키텍처 설계 컨설팅으로 포지셔닝한다.

### 리스크 3: AI ROI 회의론 확산

**내용**: AI 프로젝트 상당수가 의미 있는 성과를 내지 못한다는 분석이 확산 중.

**대응**: AI 실패의 주원인이 데이터 인프라 미비임을 설득 포인트로 활용한다. "파이프라인 먼저, AI 나중" 접근으로 파이프라인 컨설팅을 선행 판매하고 AI 컨설팅으로 자연스럽게 확장한다.

### 리스크 4: 데이터 품질 문제로 인한 성과 미달

**내용**: 고객사 데이터 품질이 낮아 ML 모델 성능이 기대에 미치지 못할 수 있음.

**대응**: 계약 전 데이터 현황 진단을 필수 선행 단계로 설정한다. 데이터 거버넌스 수립을 패키지에 포함하고, 초기에는 규칙 기반 방식으로 시작해 데이터가 쌓이면 ML 모델로 전환하는 단계적 접근을 제안한다.

### 리스크 5: 1인 운영 한계로 인한 납기 지연

**내용**: 예상보다 복잡한 프로젝트에서 납기를 맞추지 못할 위험.

**대응**: 계약 시 충분한 버퍼 일정을 확보한다. 복잡도에 따라 프리랜서 협력자를 투입할 수 있는 파트너 풀을 사전에 구성한다. 동시 프로젝트 2건 이상은 수주하지 않는 원칙을 유지한다.

---

## 10. 역량 강화 학습 일정

총 16주(4개월) 과정. **풀타임 기준** (주 40~50시간). 데이터 파이프라인 실습(8주)과 ML 실습(8주)을 순서대로 이행한다.

> **전제 조건**: 이미 fraud_pipeline 풀스택 예제(Kafka·Flink·Redis·MLflow·FastAPI·Qdrant)를 직접 구현한 경험이 있으므로 각 과정의 기초는 빠르게 통과 가능하다. 심화·응용에 집중한다.

### 영역 A: 데이터 파이프라인 실습 (8주 · Month 1~2)

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

### 영역 B: ML 모델 실습 (8주 · Month 3~4)

주당 풀타임 투자로 기존 16주 과정을 압축한다. 이미 분류(RandomForest)·LLM/RAG 기반이 있으므로 해당 주제는 빠르게 통과하고 신규 영역에 시간을 집중 배분한다.

| 주차 | 주제 | 데이터셋 | 산출물 | 비고 |
|------|------|---------|--------|------|
| Week 9 | 분류 심화 | Kaggle Credit Card Fraud | 모델 3종 비교 리포트 (RF·XGBoost·LightGBM) | 기반 있음 → 빠르게 통과 |
| Week 10 | 회귀 | 국토부 실거래가 or Kaggle House Prices | 매매가 예측 API | 신규 |
| Week 11 | 군집화 | Kaggle Mall Customer | 고객 세분화 보고서 + 시각화 | 신규 |
| Week 12 | LLM/RAG 심화 | 자체 PDF 문서 | 로컬 완전 동작 챗봇 | 기반 있음 → 빠르게 통과 |
| Week 13~14 | 딥러닝 | Kaggle Chest X-Ray | 이미지 진단 웹앱 (Streamlit) | 2주 배정 — 신규 개념 |
| Week 15 | 강화학습 기초 | Gymnasium CartPole → FinRL | 개념 이해 + CartPole 실습 | 기초 수준 (심화는 추후) |
| Week 16 | 통합 포트폴리오 | 전체 | GitHub 정리 + 제안서 템플릿 작성 | 사업 기반 완성 |

> **강화학습 참고**: 컨설팅 초기 수주 가능성이 낮은 영역이므로 Week 15는 개념 이해와 기초 실습 수준으로 정리한다. 실제 수요 발생 시 별도 심화 학습한다.

### 월별 집중 목표 요약

| 월 | 기간 | 집중 영역 | 완료 기준 |
|----|------|---------|----------|
| Month 1 | Week 1~4 | 파이프라인 수집·변환 | Kafka·NiFi·Flink·Spark 실습 코드 완성 |
| Month 2 | Week 5~8 | 파이프라인 이관·오케스트레이션·통합 | 전체 파이프라인 통합 레포 완성 |
| Month 3 | Week 9~12 | ML 분류·회귀·군집화·LLM | 포트폴리오 3건 + 챗봇 완성 |
| Month 4 | Week 13~16 | 딥러닝·강화학습·포트폴리오 정리 | GitHub 공개 + 제안서 템플릿 완성 |

### 추천 데이터셋 및 환경

**데이터 파이프라인**:
- 실습 환경: Docker Compose (Kafka·NiFi·Flink·Spark·Airflow·Redis·PostgreSQL)
- 이관 실습용 샘플 DB: MySQL World Database, Northwind

**ML 모델**:
- 분류: https://kaggle.com/datasets/mlg-ulb/creditcardfraud
- 회귀: https://kaggle.com/competitions/house-prices-advanced
- 군집화: https://kaggle.com/datasets/vjchoudhary7/customer-segmentation
- 딥러닝: https://kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia (Google Colab T4 GPU 활용)
- 강화학습: `pip install gymnasium finrl`

---

## 11. 수익 목표 및 재무 계획

### 월별 수익 목표

| 시점 | 목표 월 매출 | 수입 구성 |
|------|------------|----------|
| 3개월 (역량 완성) | — | 준비 기간 |
| 6개월 | 300~500만원 | 소규모 프로젝트 1건 |
| 12개월 | 800~1,200만원 | 프로젝트 1건 + 유지보수 1건 |
| 18개월 | 1,500~2,000만원 | 프로젝트 1건 + 유지보수 2~3건 |
| 24개월 | 2,500~3,500만원 | 프로젝트 2건 + 유지보수 3건 |
| 36개월 | 5,000만원+ | 팀 구성 + 패키지 서비스 |

### 반복 수익 구조 (핵심)

단발 프로젝트보다 운영 유지보수 계약 누적이 사업 안정성의 핵심이다.

| 유지보수 계약 수 | 월 고정 수입 | 안정성 |
|----------------|------------|--------|
| 0건 | 0원 | 불안정 |
| 1건 (월 250만원) | 250만원 | 기본 생활 가능 |
| 2건 (월 500만원) | 500만원 | 영업 여유 생김 |
| 3건 (월 750만원) | 750만원 | 안정적 성장 기반 |

### 초기 투자 및 운영비

| 항목 | 초기 비용 | 월 비용 |
|------|----------|--------|
| 사업자 등록 | 0원 | — |
| 개발 장비 (보유 시 불필요) | 0~200만원 | — |
| 클라우드 서버 (실습·데모용) | — | 3~10만원 |
| 기술 블로그 운영 | 0원 | 0원 (무료 플랫폼) |
| 생활비 준비금 (6개월) | 1,500~2,000만원 | — |
| **합계** | **1,500~2,200만원** | **3~10만원** |

---

## 12. 결론

### 시장 타이밍 판단

2026년은 세 가지 흐름이 동시에 발생하는 특수한 시점이다. AI 도입 수요가 폭발적으로 증가하고 있고, 동시에 AI 프로젝트 실패 경험이 누적되면서 "제대로 된 데이터 인프라"에 대한 인식이 높아지고 있으며, 이를 설계할 수 있는 전문가는 여전히 부족하다. 이 세 조건이 겹치는 지금이 진입 최적 시점이다.

### 이 사업의 본질적 강점

대형 SI는 파이프라인팀과 AI팀이 분리되어 있다. AI 스타트업은 모델은 알지만 데이터 인프라를 모른다. 클라우드 MSP는 자사 서비스 판매에 집중한다. 오픈소스 기반으로 수집~변환~저장~학습~추론~운영까지 단일 관점에서 설계할 수 있는 독립 컨설턴트는 한국 시장에서 찾기 어렵다. 이것이 이 사업의 가장 현실적인 진입 장벽이자 경쟁 우위다.

### 1인 체제 2년의 의미

초기 2년은 레퍼런스를 쌓고 반복 수익 구조를 만드는 기간이다. 화려한 성장보다 안정적 생존이 우선이다. 유지보수 계약 3건이 쌓이는 순간 사업의 기반이 완성되며, 그때부터 팀 구성과 서비스 확장을 논의할 수 있다.

### 지금 당장 실행할 것

16주 ML 학습 일정을 이행하면서 완성된 파이프라인 프로젝트를 GitHub 공개 포트폴리오로 정리하는 것이 오늘 시작할 수 있는 가장 직접적인 준비다. 이 두 가지가 완료되면 첫 번째 제안서를 쓸 수 있는 준비가 된다. 포트폴리오 하나가 제안서 100장보다 강력하다.

---

*본 보고서는 2026년 3월 기준 시장 데이터와 기술 역량 분석을 바탕으로 작성되었습니다.*

*주요 출처: 과기정통부·KDATA 「2024 데이터산업현황조사」 / CIO Korea 「2026 IT 전망 조사」 / Deloitte 「2026 TMT 전망 보고서」 / 한국지능정보사회진흥원 「2026년 AI 전망 분석」 / Fortune Business Insights 「AI 컨설팅 서비스 시장 분석」*
