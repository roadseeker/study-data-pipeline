# scripts

환경 초기화 및 운영 보조 스크립트를 관리하는 폴더.

## 파일 목록

| 파일 | 역할 |
|------|------|
| init-db.sql | PostgreSQL 초기화: airflow_db 생성, transactions 테이블 및 샘플 100건 삽입 |
| init-customers.sql | PostgreSQL 초기화: customers 테이블 및 샘플 1,000건 삽입, 인덱스 생성 |
| healthcheck-all.sh | 전체 7개 서비스 헬스체크 (터미널에서 직접 실행) |

## 실행 방법

```bash
# 전체 헬스체크
bash scripts/healthcheck-all.sh

# PostgreSQL 초기화는 docker-compose.yml 볼륨 마운트로 자동 실행됨
# (컨테이너 최초 기동 시 init-db.sql → init-customers.sql 순서로 실행)
```

## 주의사항

- `init-*.sql`은 PostgreSQL 컨테이너 최초 기동 시에만 자동 실행된다.
- 재초기화가 필요할 경우 `docker compose down -v` 후 재기동한다.
