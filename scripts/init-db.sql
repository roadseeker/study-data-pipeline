-- =============================================================
-- scripts/init-db.sql
-- PostgreSQL 초기화 스크립트 (Week 1 — 실습 환경 구성)
-- =============================================================

-- -------------------------------------------------------------
-- 1. Airflow 메타데이터 DB 생성
-- -------------------------------------------------------------
CREATE DATABASE airflow_db;

-- -------------------------------------------------------------
-- 2. 실습용 거래 테이블 (이후 데이터 이관 실습에서 활용)
-- -------------------------------------------------------------
CREATE TABLE transactions (
    tx_id       SERIAL PRIMARY KEY,
    user_id     INT NOT NULL,
    amount      DECIMAL(12,2) NOT NULL,
    currency    VARCHAR(3) DEFAULT 'KRW',
    tx_type     VARCHAR(20) NOT NULL,
    status      VARCHAR(20) DEFAULT 'PENDING',
    created_at  TIMESTAMP DEFAULT NOW()
);

-- -------------------------------------------------------------
-- 3. 샘플 거래 데이터 100건 삽입
-- -------------------------------------------------------------
INSERT INTO transactions (user_id, amount, currency, tx_type, status, created_at)
SELECT
    (random() * 999 + 1)::INT,
    (random() * 9999999 + 1000)::DECIMAL(12,2),
    CASE WHEN random() < 0.7 THEN 'KRW' WHEN random() < 0.9 THEN 'USD' ELSE 'JPY' END,
    CASE WHEN random() < 0.5 THEN 'TRANSFER' WHEN random() < 0.8 THEN 'PAYMENT' ELSE 'WITHDRAWAL' END,
    CASE WHEN random() < 0.85 THEN 'COMPLETED' WHEN random() < 0.95 THEN 'PENDING' ELSE 'FAILED' END,
    NOW() - (random() * INTERVAL '30 days')
FROM generate_series(1, 100);
