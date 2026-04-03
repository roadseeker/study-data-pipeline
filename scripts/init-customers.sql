-- =============================================================
-- scripts/init-customers.sql
-- 고객 테이블 초기화 스크립트 (Week 1 — 실습 환경 구성)
-- =============================================================

-- -------------------------------------------------------------
-- 1. 고객 테이블 생성
-- -------------------------------------------------------------
CREATE TABLE customers (
    customer_id   SERIAL PRIMARY KEY,
    user_id       INT NOT NULL UNIQUE,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(200) NOT NULL UNIQUE,
    phone         VARCHAR(20),
    grade         VARCHAR(10) DEFAULT 'NORMAL',   -- NORMAL / VIP / PREMIUM
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);

-- -------------------------------------------------------------
-- 2. 샘플 고객 데이터 1000건 삽입
-- -------------------------------------------------------------
INSERT INTO customers (user_id, name, email, phone, grade, is_active, created_at)
SELECT
    gs AS user_id,
    '고객_' || gs AS name,
    'user_' || gs || '@nexuspay.io' AS email,
    '010-' || LPAD((random() * 9999)::INT::TEXT, 4, '0') || '-' || LPAD((random() * 9999)::INT::TEXT, 4, '0') AS phone,
    CASE
        WHEN random() < 0.70 THEN 'NORMAL'
        WHEN random() < 0.90 THEN 'VIP'
        ELSE 'PREMIUM'
    END AS grade,
    random() > 0.05 AS is_active,
    NOW() - (random() * INTERVAL '365 days')
FROM generate_series(1, 1000) AS gs;

-- -------------------------------------------------------------
-- 3. transactions 테이블에 외래키 관계 인덱스 추가
--    (실제 FK 제약은 이관 실습 시 부하 고려하여 생략)
-- -------------------------------------------------------------
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
CREATE INDEX idx_customers_user_id ON customers(user_id);
CREATE INDEX idx_customers_grade ON customers(grade);
