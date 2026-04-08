# scripts

실행 가능한 산출물과 운영 보조 스크립트를 기술 도메인별로 관리하는 폴더.

## 폴더 구조

- `foundation/`: 헬스체크, 공통 초기화 스크립트
- `kafka/`: Kafka 프로듀서, 컨슈머, 검증 스크립트
- `nifi/`: NiFi 실습용 시뮬레이터와 데이터 생성 스크립트

## 배치 원칙

- 스크립트는 주차가 아니라 역할과 기술 영역 기준으로 저장한다.
- Week 가이드에서 사용하는 스크립트라도 공통 자산이면 `foundation/`에 둔다.
- 검증 스크립트는 가능한 한 `verify_*.sh` 또는 `verify_*.py` 패턴을 유지한다.

## 실행 예시

```bash
# 전체 헬스체크
bash scripts/foundation/healthcheck-all.sh

# PostgreSQL 초기화는 docker-compose.yml 볼륨 마운트로 자동 실행됨
# (컨테이너 최초 기동 시 foundation/init-db.sql → nifi/init-customers.sql 순서로 실행)
```

