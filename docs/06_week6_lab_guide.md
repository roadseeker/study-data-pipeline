# Week 6: 이관 — Spark JDBC 배치 이관 + Debezium CDC 실시간 이관

**기간**: 5일 (월~금, 풀타임 40시간)
**주제**: RDBMS → 데이터 레이크 배치 이관(Spark JDBC), 실시간 변경 데이터 캡처(Debezium CDC), 레거시 DB 탈출 전략 수립
**산출물**: Spark JDBC 배치 이관 파이프라인 + Debezium CDC 실시간 이관 파이프라인 + 이관 전략 가이드 + 데이터 정합성 검증 도구
**전제 조건**: Week 1~5 환경 정상 기동 (`bash scripts/healthcheck-all.sh` 전체 통과), Delta Lake 메달리온 아키텍처 구축 완료

---

## 수행 시나리오

### 배경 설정

Week 5에서 Spark 기반 Delta Lake 메달리온 아키텍처가 완성되었다. Bronze·Silver·Gold 3단계 ETL 파이프라인이 정상 작동하고, 타임 트래블로 감사 추적도 가능해졌다. 그런데 Nexus Pay CIO가 근본적인 문제를 제기한다.

> "파이프라인과 데이터 레이크는 훌륭합니다. 그런데 정작 **우리 핵심 데이터가 아직 레거시 MySQL에 갇혀 있습니다**. 10년간 운영해 온 정산 시스템의 MySQL에 고객 마스터, 가맹점 정보, 정산 이력 3억 건이 있어요. 이걸 Delta Lake로 옮기지 않으면 아무리 파이프라인이 좋아도 **분석할 데이터 자체가 없습니다**."
>
> "이관 방식도 고민이 필요합니다. **고객 마스터처럼 자주 변하지 않는 테이블**은 야간에 한 번 전체 복사해도 됩니다. 하지만 **거래 이력 테이블은 하루에도 수십만 건이 새로 쌓이는데**, 매번 전체를 복사할 수는 없으니 **증분 이관**이 필요합니다. 가장 까다로운 건 **정산 테이블**입니다. 실시간으로 정산 상태가 변경되는데(대기→처리중→완료→취소), 이 **변경 사항을 즉시 반영**해야 실시간 대시보드에서 최신 정산 현황을 보여줄 수 있습니다."
>
> "그리고 가장 중요한 건 **이관 중에 서비스가 멈추면 안 됩니다**. MySQL은 현재도 실서비스 중이에요. 이관 때문에 정산이 밀리면 가맹점들한테 돈이 안 나가요."

컨설턴트로서 이번 주에는 레거시 RDBMS에서 데이터 레이크로의 이관 파이프라인을 설계·구축한다. 배치 이관에는 Spark JDBC를, 실시간 이관에는 Debezium CDC(Change Data Capture)를 활용한다. 기업 현장에서 가장 빈번하게 발생하는 "레거시 DB 탈출" 프로젝트의 실전 기술을 습득하는 것이 목표다. 이때 Week 5의 ETL 영역(`/data/delta/etl`)과 충돌하지 않도록, Week 6 이관 산출물은 `/data/delta/migration` 루트 아래에 별도로 적재한다.

### 왜 이관(Migration)인가? — 컨설팅 현장의 현실

데이터 파이프라인 컨설팅 프로젝트의 70% 이상은 "기존 RDBMS 데이터를 어떻게 데이터 레이크로 옮기느냐"에서 시작한다. 아무리 Kafka·Flink·Spark·Delta Lake가 훌륭해도 레거시 DB에 갇힌 데이터를 꺼내지 못하면 파이프라인은 빈 껍데기다.

```
┌──────────────────────────────────────────────────────────────────────┐
│              레거시 DB → 데이터 레이크 이관 전략 3단계                    │
│                                                                      │
│  ┌─────────────────────────────────────────────────┐                 │
│  │  전략 1: Full Export (전체 이관)                   │                │
│  │  ─ Spark JDBC                                    │                │
│  │  ─ 테이블 전체를 한 번에 복사                       │                │
│  │  ─ 마스터 데이터, 코드 테이블에 적합                │                │
│  │  ─ 데이터량 적을 때 가장 단순                       │                │
│  └─────────────────────────────────────────────────┘                 │
│                                                                      │
│  ┌─────────────────────────────────────────────────┐                 │
│  │  전략 2: Incremental Import (증분 이관)            │                │
│  │  ─ Spark JDBC + WHERE / watermark                │                │
│  │  ─ 최종 수정 시각 이후 데이터만 추출                │                │
│  │  ─ 거래 이력, 로그 테이블에 적합                    │                │
│  │  ─ append(신규만) vs lastmodified(변경 포함)       │                │
│  └─────────────────────────────────────────────────┘                 │
│                                                                      │
│  ┌─────────────────────────────────────────────────┐                 │
│  │  전략 3: CDC (실시간 변경 캡처)                     │                │
│  │  ─ Debezium + Kafka Connect                      │                │
│  │  ─ DB 트랜잭션 로그(binlog) 기반 실시간 캡처        │                │
│  │  ─ INSERT·UPDATE·DELETE 모두 감지                  │                │
│  │  ─ 정산 테이블 등 상태 변경이 빈번한 테이블에 적합    │                │
│  │  ─ 소스 DB 부하 최소화 (쿼리 X, 로그 읽기 O)       │                │
│  └─────────────────────────────────────────────────┘                 │
└──────────────────────────────────────────────────────────────────────┘
```

| 전략 | 도구 | 방식 | 적합 대상 | 지연 | 소스 DB 부하 |
|------|------|------|----------|------|-------------|
| Full Export | Spark JDBC | 테이블 전체 SELECT | 마스터·코드 테이블 | 시간 단위 | 높음 (풀스캔) |
| Incremental | Spark JDBC + WHERE / watermark | PK 또는 updated_at 조건 추출 | 거래 이력·로그 | 분~시간 | 중간 |
| CDC | Debezium + Kafka Connect | binlog 스트림 캡처 | 정산·상태 변경 | 초~밀리초 | 낮음 (로그 읽기) |

### 목표

1. 레거시 MySQL 환경 구성 및 샘플 데이터 적재 (고객·가맹점·거래·정산 테이블)
2. Spark JDBC 배치 이관 파이프라인 구축 — Full Export + Incremental Import
3. Spark JDBC 병렬 읽기·분할 전략과 Delta Lake 적재 패턴 학습
4. Debezium CDC 실시간 이관 파이프라인 구축 — MySQL binlog → Kafka → Delta Lake
5. 이관 데이터 정합성 검증 도구 개발 (소스 DB ↔ Delta Lake 건수·PK 비교)
6. 이관 전략 가이드 문서화 (고객 제안서에 활용 가능한 수준)

### 일정 개요

| 일차 | 주제 | 핵심 작업 |
|------|------|----------|
| Day 1 | 이관 핵심 개념 + 레거시 MySQL 환경 구성 | 이관 전략 정리, MySQL 컨테이너 추가, 레거시 샘플 DB 설계·적재 |
| Day 2 | Spark JDBC 배치 이관 — Full Export | Spark JDBC Full Export, Delta Lake Bronze 적재, 병렬 읽기 튜닝 |
| Day 3 | Spark JDBC 증분 이관 + 정합성 검증 | Spark JDBC Incremental Append, Lastmodified 패턴, 정합성 검증 |
| Day 4 | Debezium CDC 실시간 이관 | Kafka Connect + Debezium 구성, MySQL binlog 캡처, Kafka 토픽 확인, 실시간 Delta Lake 반영 |
| Day 5 | 정합성 검증 + 이관 전략 가이드 문서화 | 소스↔타겟 정합성 검증 도구, 이관 전략 가이드, 통합 테스트, Git 커밋 |

---

## Day 1: 이관 핵심 개념 + 레거시 MySQL 환경 구성

### 1-1. 데이터 이관 핵심 개념 정리

컨설팅 현장에서 고객에게 데이터 이관 전략을 설명할 때 사용할 핵심 개념을 정리한다.

```
┌──────────────────────────────────────────────────────────────────────┐
│                     데이터 이관 핵심 개념                                │
│                                                                      │
│  ETL vs ELT                                                          │
│    ├── ETL: 추출 → 변환 → 적재 (전통 DW/배치 적재 방식)                │
│    └── ELT: 추출 → 적재 → 변환 (현대 방식, Delta Lake에서 변환)         │
│                                                                      │
│  배치 이관 (Batch Migration)                                          │
│    ├── Full Export: 테이블 전체 복사 (SELECT *)                        │
│    ├── Incremental Append: 신규 행만 추출 (WHERE id > last_id)        │
│    └── Incremental Lastmodified: 변경 행 추출 (WHERE updated > last)  │
│                                                                      │
│  실시간 이관 (Real-time Migration)                                    │
│    ├── CDC (Change Data Capture): DB 로그 기반 변경 감지               │
│    ├── Binlog: MySQL 트랜잭션 로그 (모든 변경 기록)                    │
│    └── WAL: PostgreSQL Write-Ahead Log (동일 개념)                     │
│                                                                      │
│  이관 도구 비교                                                        │
│    ├── Spark JDBC: Spark DataFrame으로 직접 읽는 배치 이관 방식         │
│    ├── Debezium: 오픈소스 CDC 플랫폼 (Kafka Connect 기반)              │
│    ├── Kafka Connect JDBC: JDBC 폴링 기반 수집 (간단하지만 한계 존재)   │
│    └── Delta Lake: 적재 대상이자 검증 가능한 Lakehouse 저장소           │
│                                                                      │
│  정합성 검증 (Data Reconciliation)                                    │
│    ├── 건수 비교: 소스 COUNT(*) = 타겟 COUNT(*)                        │
│    ├── 체크섬 비교: 소스 SUM(hash) = 타겟 SUM(hash)                   │
│    └── 샘플 검증: 무작위 N건 행 단위 비교                               │
└──────────────────────────────────────────────────────────────────────┘
```

```bash
cat > docs/migration-concepts.md << 'EOF'
# 데이터 이관 핵심 개념 — 컨설팅 설명 자료

## 왜 이관이 필요한가?

대부분의 기업은 핵심 데이터가 레거시 RDBMS(MySQL, Oracle, SQL Server)에 저장되어 있다.
데이터 레이크(Delta Lake, HDFS, S3)로 이관해야 하는 이유:
- 분석·ML 워크로드를 OLTP DB에서 분리 (운영 DB 부하 제거)
- 대용량 분석에 부적합한 RDBMS 대신 분산 처리 활용
- 다양한 소스 데이터를 하나의 레이크에 통합
- 히스토리 보존 + 타임 트래블 (RDBMS는 현재 상태만 유지)

## Spark JDBC vs Debezium vs Kafka Connect JDBC

| 비교 항목 | Spark JDBC | Debezium CDC | Kafka Connect JDBC |
|-----------|------------|-------------|--------------------|
| 처리 방식 | Spark DataFrame 배치 | binlog 스트림 | JDBC 폴링 |
| 지연 | 분~시간 | 초~밀리초 | 분 단위 |
| 증분 지원 | WHERE / watermark 직접 구현 | 자동 (모든 변경 캡처) | incrementing / timestamp 모드 |
| DELETE 감지 | 불가 | 가능 (tombstone 이벤트) | 불가 |
| 소스 DB 부하 | 높음 (SELECT 쿼리) | 낮음 (로그 읽기) | 중간~높음 (주기적 조회) |
| 스키마 진화 | 수동 대응 | Avro + Schema Registry | 제한적 |
| 생태계 | Spark + Delta Lake | Kafka Connect + Kafka | Kafka Connect |
| 적합한 용도 | 배치 이관 + 변환 + 검증 | 실시간 변경 추적 | 단순 폴링 수집 |

## 이관 전략 선택 기준

1. 데이터 변경 빈도가 낮고 테이블이 작다 → Full Export (Spark JDBC)
2. 신규 데이터만 추가되고 변경이 없다 → Incremental Append
3. 기존 행이 수정되지만 실시간 필요 없다 → Incremental Lastmodified
4. 실시간 변경 반영이 필요하다 → Debezium CDC
5. DELETE도 감지해야 한다 → Debezium CDC (유일한 선택지)

EOF
```

### 1-2. 레거시 MySQL 환경 구성

Nexus Pay 레거시 정산 시스템의 MySQL을 Docker Compose에 추가한다.

docker-compose.yml의 services 섹션에 추가:

```yaml
  # ──────────────────────────────────────
  # MySQL — 레거시 정산 시스템 (이관 소스)
  # ──────────────────────────────────────
  mysql:
    image: mysql:8.0
    container_name: lab-mysql
    environment:
      MYSQL_ROOT_PASSWORD: root1234
      MYSQL_DATABASE: nexuspay_legacy
      MYSQL_USER: Nexus Pay
      MYSQL_PASSWORD: nexuspay1234
    command:
      - --server-id=1
      - --log-bin=mysql-bin
      - --binlog-format=ROW
      - --binlog-row-image=FULL
      - --gtid-mode=ON
      - --enforce-gtid-consistency=ON
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
    ports:
      - "3306:3306"
    volumes:
      - mysql-data:/var/lib/mysql
      - ./scripts/init-mysql.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - pipeline-net
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-proot1234"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 30s
```

volumes 섹션에 추가:

```yaml
volumes:
  # ... 기존 볼륨 ...
  mysql-data:
```

> **핵심 설정 해설**:
> - `--log-bin=mysql-bin`: 바이너리 로그 활성화 (Debezium CDC의 전제 조건)
> - `--binlog-format=ROW`: 행 단위 로그 기록 (CDC가 각 행의 변경 전후 값을 캡처하려면 필수)
> - `--binlog-row-image=FULL`: 변경 전후 모든 컬럼 기록 (MINIMAL이면 변경된 컬럼만 기록)
> - `--gtid-mode=ON`: Global Transaction ID 활성화 (복제·CDC 안정성 향상)

### 1-3. 레거시 DB 스키마 설계 및 샘플 데이터 적재

Nexus Pay 정산 시스템의 4개 핵심 테이블을 설계한다.

```bash
cat > scripts/init-mysql.sql << 'SQLEOF'
-- ============================================
-- Nexus Pay 레거시 정산 시스템 — 초기 데이터
-- Week 6: 이관 실습용
-- ============================================

-- Debezium CDC용 권한 설정
CREATE USER IF NOT EXISTS 'debezium'@'%' IDENTIFIED BY 'debezium1234';
GRANT SELECT, RELOAD, SHOW DATABASES, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'debezium'@'%';
FLUSH PRIVILEGES;

USE nexuspay_legacy;

-- ──────────────────────────────────────
-- 1. 고객 마스터 테이블 (변경 빈도: 낮음 → Full Export 대상)
-- ──────────────────────────────────────
CREATE TABLE customers (
    customer_id     BIGINT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(200) NOT NULL UNIQUE,
    phone           VARCHAR(20),
    grade           ENUM('BASIC','SILVER','GOLD','VIP') DEFAULT 'BASIC',
    status          ENUM('ACTIVE','DORMANT','WITHDRAWN') DEFAULT 'ACTIVE',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_grade (grade),
    INDEX idx_status (status),
    INDEX idx_updated (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ──────────────────────────────────────
-- 2. 가맹점 정보 테이블 (변경 빈도: 낮음 → Full Export 대상)
-- ──────────────────────────────────────
CREATE TABLE merchants (
    merchant_id     BIGINT AUTO_INCREMENT PRIMARY KEY,
    business_name   VARCHAR(200) NOT NULL,
    business_number VARCHAR(20) NOT NULL UNIQUE COMMENT '사업자등록번호',
    category        ENUM('RESTAURANT','RETAIL','ONLINE','TRAVEL','OTHER') NOT NULL,
    fee_rate        DECIMAL(5,4) NOT NULL DEFAULT 0.0200 COMMENT '수수료율',
    bank_code       VARCHAR(10) NOT NULL,
    account_number  VARCHAR(30) NOT NULL,
    status          ENUM('ACTIVE','SUSPENDED','TERMINATED') DEFAULT 'ACTIVE',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ──────────────────────────────────────
-- 3. 거래 이력 테이블 (변경 빈도: 높음, INSERT only → Incremental Append 대상)
-- ──────────────────────────────────────
CREATE TABLE transactions (
    tx_id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    customer_id     BIGINT NOT NULL,
    merchant_id     BIGINT NOT NULL,
    amount          BIGINT NOT NULL COMMENT '거래 금액 (원)',
    currency        VARCHAR(3) DEFAULT 'KRW',
    tx_type         ENUM('PAYMENT','REFUND','CANCEL') NOT NULL,
    channel         ENUM('ONLINE','OFFLINE','MOBILE','ATM') NOT NULL,
    status          ENUM('SUCCESS','FAILED','PENDING') NOT NULL DEFAULT 'SUCCESS',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_customer (customer_id),
    INDEX idx_merchant (merchant_id),
    INDEX idx_created (created_at),
    INDEX idx_type_status (tx_type, status),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ──────────────────────────────────────
-- 4. 정산 테이블 (변경 빈도: 매우 높음, UPDATE 빈번 → CDC 대상)
-- ──────────────────────────────────────
CREATE TABLE settlements (
    settlement_id   BIGINT AUTO_INCREMENT PRIMARY KEY,
    merchant_id     BIGINT NOT NULL,
    settlement_date DATE NOT NULL,
    total_amount    BIGINT NOT NULL DEFAULT 0 COMMENT '총 거래 금액',
    fee_amount      BIGINT NOT NULL DEFAULT 0 COMMENT '수수료',
    net_amount      BIGINT NOT NULL DEFAULT 0 COMMENT '정산 금액 (total - fee)',
    tx_count        INT NOT NULL DEFAULT 0,
    status          ENUM('PENDING','PROCESSING','COMPLETED','FAILED','CANCELLED') DEFAULT 'PENDING',
    processed_at    DATETIME NULL,
    completed_at    DATETIME NULL,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_merchant_date (merchant_id, settlement_date),
    INDEX idx_status (status),
    INDEX idx_updated (updated_at),
    FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ──────────────────────────────────────
-- 샘플 데이터 적재 — 고객 500명
-- ──────────────────────────────────────
DELIMITER //
CREATE PROCEDURE generate_customers()
BEGIN
    DECLARE i INT DEFAULT 1;
    DECLARE grades VARCHAR(20);
    WHILE i <= 500 DO
        SET grades = ELT(1 + FLOOR(RAND() * 4), 'BASIC','SILVER','GOLD','VIP');
        INSERT INTO customers (name, email, phone, grade, status, created_at)
        VALUES (
            CONCAT('고객_', LPAD(i, 4, '0')),
            CONCAT('user', i, '@nexuspay.co.kr'),
            CONCAT('010-', LPAD(FLOOR(RAND()*10000), 4, '0'), '-', LPAD(FLOOR(RAND()*10000), 4, '0')),
            grades,
            IF(RAND() < 0.9, 'ACTIVE', IF(RAND() < 0.5, 'DORMANT', 'WITHDRAWN')),
            DATE_SUB(NOW(), INTERVAL FLOOR(RAND()*730) DAY)
        );
        SET i = i + 1;
    END WHILE;
END //
DELIMITER ;
CALL generate_customers();
DROP PROCEDURE generate_customers;

-- ──────────────────────────────────────
-- 샘플 데이터 적재 — 가맹점 100개
-- ──────────────────────────────────────
DELIMITER //
CREATE PROCEDURE generate_merchants()
BEGIN
    DECLARE i INT DEFAULT 1;
    DECLARE cat VARCHAR(20);
    WHILE i <= 100 DO
        SET cat = ELT(1 + FLOOR(RAND() * 5), 'RESTAURANT','RETAIL','ONLINE','TRAVEL','OTHER');
        INSERT INTO merchants (business_name, business_number, category, fee_rate, bank_code, account_number, status, created_at)
        VALUES (
            CONCAT(ELT(1+FLOOR(RAND()*5), '스마트','글로벌','베스트','프리미엄','이지'), ELT(1+FLOOR(RAND()*5), '마트','카페','샵','스토어','몰'), '_', LPAD(i, 3, '0')),
            CONCAT(LPAD(FLOOR(RAND()*1000), 3, '0'), '-', LPAD(FLOOR(RAND()*100), 2, '0'), '-', LPAD(FLOOR(RAND()*100000), 5, '0')),
            cat,
            ROUND(0.015 + RAND() * 0.020, 4),
            LPAD(FLOOR(RAND()*100), 3, '0'),
            CONCAT(LPAD(FLOOR(RAND()*10000000000), 10, '0'), LPAD(FLOOR(RAND()*100), 2, '0')),
            IF(RAND() < 0.95, 'ACTIVE', 'SUSPENDED'),
            DATE_SUB(NOW(), INTERVAL FLOOR(RAND()*365) DAY)
        );
        SET i = i + 1;
    END WHILE;
END //
DELIMITER ;
CALL generate_merchants();
DROP PROCEDURE generate_merchants;

-- ──────────────────────────────────────
-- 샘플 데이터 적재 — 거래 이력 100,000건
-- ──────────────────────────────────────
DELIMITER //
CREATE PROCEDURE generate_transactions()
BEGIN
    DECLARE i INT DEFAULT 1;
    DECLARE tx_type VARCHAR(10);
    DECLARE ch VARCHAR(10);
    WHILE i <= 100000 DO
        SET tx_type = ELT(1 + FLOOR(RAND() * 3), 'PAYMENT','REFUND','CANCEL');
        SET ch = ELT(1 + FLOOR(RAND() * 4), 'ONLINE','OFFLINE','MOBILE','ATM');
        INSERT INTO transactions (customer_id, merchant_id, amount, tx_type, channel, status, created_at)
        VALUES (
            1 + FLOOR(RAND() * 500),
            1 + FLOOR(RAND() * 100),
            1000 + FLOOR(RAND() * 4999000),
            tx_type,
            ch,
            IF(RAND() < 0.95, 'SUCCESS', IF(RAND() < 0.5, 'FAILED', 'PENDING')),
            DATE_SUB(NOW(), INTERVAL FLOOR(RAND()*90) DAY)
        );
        SET i = i + 1;
    END WHILE;
END //
DELIMITER ;
CALL generate_transactions();
DROP PROCEDURE generate_transactions;

-- ──────────────────────────────────────
-- 샘플 데이터 적재 — 정산 5,000건
-- ──────────────────────────────────────
DELIMITER //
CREATE PROCEDURE generate_settlements()
BEGIN
    DECLARE i INT DEFAULT 1;
    DECLARE m_id BIGINT;
    DECLARE s_date DATE;
    DECLARE total BIGINT;
    DECLARE fee BIGINT;
    DECLARE st VARCHAR(20);
    WHILE i <= 5000 DO
        SET m_id = 1 + FLOOR(RAND() * 100);
        SET s_date = DATE_SUB(CURDATE(), INTERVAL FLOOR(RAND()*90) DAY);
        SET total = 100000 + FLOOR(RAND() * 49900000);
        SET fee = FLOOR(total * (0.015 + RAND() * 0.020));
        SET st = ELT(1 + FLOOR(RAND() * 5), 'PENDING','PROCESSING','COMPLETED','COMPLETED','COMPLETED');
        INSERT INTO settlements (merchant_id, settlement_date, total_amount, fee_amount, net_amount, tx_count, status, processed_at, completed_at, created_at)
        VALUES (
            m_id, s_date, total, fee, total - fee,
            FLOOR(RAND() * 500) + 1,
            st,
            IF(st IN ('PROCESSING','COMPLETED','FAILED'), DATE_ADD(s_date, INTERVAL 1 DAY), NULL),
            IF(st = 'COMPLETED', DATE_ADD(s_date, INTERVAL 2 DAY), NULL),
            s_date
        );
        SET i = i + 1;
    END WHILE;
END //
DELIMITER ;
CALL generate_settlements();
DROP PROCEDURE generate_settlements;

-- 데이터 건수 확인
SELECT 'customers' AS tbl, COUNT(*) AS cnt FROM customers
UNION ALL SELECT 'merchants', COUNT(*) FROM merchants
UNION ALL SELECT 'transactions', COUNT(*) FROM transactions
UNION ALL SELECT 'settlements', COUNT(*) FROM settlements;
SQLEOF
```

### 1-4. MySQL 기동 및 검증

```bash
# MySQL 기동
docker compose up -d mysql

# 헬스체크 대기
docker compose ps mysql

# 데이터 적재 확인
docker exec lab-mysql mysql -u nexuspay -pnexuspay1234 nexuspay_legacy \
  -e "SELECT 'customers' AS tbl, COUNT(*) AS cnt FROM customers
      UNION ALL SELECT 'merchants', COUNT(*) FROM merchants
      UNION ALL SELECT 'transactions', COUNT(*) FROM transactions
      UNION ALL SELECT 'settlements', COUNT(*) FROM settlements;"
```

기대 출력:

```
+--------------+--------+
| tbl          | cnt    |
+--------------+--------+
| customers    |    500 |
| merchants    |    100 |
| transactions | 100000 |
| settlements  |   5000 |
+--------------+--------+
```

### 1-5. binlog 활성화 확인

```bash
# binlog 상태 확인 (CDC 전제 조건)
docker exec lab-mysql mysql -u root -proot1234 \
  -e "SHOW VARIABLES LIKE 'log_bin%';
      SHOW VARIABLES LIKE 'binlog_format';
      SHOW VARIABLES LIKE 'binlog_row_image';
      SHOW VARIABLES LIKE 'gtid_mode';
      SHOW MASTER STATUS;"
```

기대 결과:

```
+------------------+-------+
| Variable_name    | Value |
+------------------+-------+
| log_bin          | ON    |
| binlog_format    | ROW   |
| binlog_row_image | FULL  |
| gtid_mode        | ON    |
+------------------+-------+
```

### 1-6. 이관 대상 테이블 분류 문서

```bash
cat > docs/migration-target-tables.md << 'EOF'
# Nexus Pay 레거시 DB — 이관 대상 테이블 분류

## 이관 전략 매핑

| 테이블 | 건수 | 변경 빈도 | 변경 유형 | 이관 전략 | 이관 도구 | 주기 |
|--------|------|----------|----------|----------|----------|------|
| customers | 500 | 낮음 | 간헐적 UPDATE | Full Export | Spark JDBC | 일 1회 (야간) |
| merchants | 100 | 낮음 | 간헐적 UPDATE | Full Export | Spark JDBC | 일 1회 (야간) |
| transactions | 100,000+ | 높음 | INSERT only | Incremental Append | Spark JDBC | 시간 1회 |
| settlements | 5,000+ | 매우 높음 | INSERT + UPDATE | CDC (실시간) | Debezium | 실시간 |

## 이관 우선순위

1. **customers + merchants** (Day 2): Full Export로 단순 복사 → Delta Lake Bronze
2. **transactions** (Day 2~3): Incremental Append → 신규 건만 추가 → Delta Lake Bronze
3. **settlements** (Day 4): Debezium CDC → 실시간 변경 반영 → Delta Lake Bronze

EOF
```

**Day 1 완료 기준**: MySQL 컨테이너 정상 기동, 4개 테이블 데이터 적재 확인 (500 + 100 + 100,000 + 5,000), binlog ROW 포맷 활성화 확인, 이관 전략 문서 작성.

---

## Day 2: Spark JDBC 배치 이관 — Full Export + Delta Lake Bronze 적재

### 2-1. Spark JDBC Full Export 설계

별도 전용 이관 도구를 추가하지 않고, 기존 Spark 클러스터에서 JDBC로 직접 읽어 Delta Lake Bronze에 적재한다. Full Export는 변경 빈도가 낮은 마스터 테이블과 초기 기준 적재가 필요한 거래 이력에 적용한다.

> **핵심 원칙**:
> - `customers`, `merchants`: 매일 야간 overwrite 가능한 마스터 테이블
> - `transactions`: 최초 1회 전체 적재 후 Day 3부터 증분 append
> - 숫자형 PK를 `partitionColumn`으로 사용해 병렬 읽기
> - 적재 즉시 Delta Lake 메타컬럼 추가 (`_ingested_at`, `_source`, `_migration_type`, `_batch_id`)

### 2-2. Spark JDBC Full Export 스크립트 작성

```bash
cat > spark-jobs/migration/jdbc_full_export.py << 'PYEOF'
"""
Spark JDBC Full Export — 고객·가맹점·거래 테이블 → Delta Lake Bronze
Week 6 Day 2: Spark JDBC 기반 초기 배치 이관
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, lit
from datetime import datetime

def create_spark():
    return SparkSession.builder \
        .appName("nexuspay-JDBC-FullExport") \
        .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.1.0,mysql:mysql-connector-java:8.0.33") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()

JDBC_URL = "jdbc:mysql://mysql:3306/nexuspay_legacy"
JDBC_PROPS = {
    "user": "nexuspay",
    "password": "nexuspay1234",
    "driver": "com.mysql.cj.jdbc.Driver"
}

MIGRATION_ROOT = "/data/delta/migration"

def full_export_table(spark, table_name, partition_column=None, num_partitions=4):
    """테이블 전체를 Spark JDBC로 읽어 Delta Lake Bronze에 적재"""
    print(f"\n{'='*60}")
    print(f" Full Export: {table_name}")
    print(f"{'='*60}")

    reader = spark.read.jdbc(
        url=JDBC_URL,
        table=table_name,
        properties=JDBC_PROPS
    )

    if partition_column:
        bounds = spark.read.jdbc(
            url=JDBC_URL,
            table=f"(SELECT MIN({partition_column}) AS min_val, MAX({partition_column}) AS max_val FROM {table_name}) t",
            properties=JDBC_PROPS
        ).first()

        reader = spark.read.jdbc(
            url=JDBC_URL,
            table=table_name,
            column=partition_column,
            lowerBound=int(bounds["min_val"]),
            upperBound=int(bounds["max_val"]),
            numPartitions=num_partitions,
            properties=JDBC_PROPS
        )

    df = reader.withColumn("_ingested_at", current_timestamp()) \
               .withColumn("_source", lit("mysql.nexuspay_legacy")) \
               .withColumn("_migration_type", lit("jdbc_full_export")) \
               .withColumn("_batch_id", lit(datetime.now().strftime("%Y%m%d_%H%M%S")))

    target_path = f"{MIGRATION_ROOT}/{table_name}"
    df.write \
      .format("delta") \
      .mode("overwrite") \
      .option("overwriteSchema", "true") \
      .save(target_path)

    count = spark.read.format("delta").load(target_path).count()
    print(f"  적재 완료: {count} 건 → {target_path}")
    return count

def main():
    spark = create_spark()

    print("\n" + "="*60)
    print(" Nexus Pay 레거시 DB → Delta Lake Bronze 초기 적재")
    print(" 방식: Spark JDBC Full Export")
    print(f" 시작: {datetime.now()}")
    print("="*60)

    results = {}
    results["customers"] = full_export_table(spark, "customers", "customer_id", 2)
    results["merchants"] = full_export_table(spark, "merchants", "merchant_id", 1)
    results["transactions"] = full_export_table(spark, "transactions", "tx_id", 4)

    print("\n" + "="*60)
    print(" 이관 결과 요약")
    print("="*60)
    for table, count in results.items():
        print(f"  {table:20s} : {count:>10,} 건")
    print(f"\n  총 이관 건수: {sum(results.values()):>10,} 건")
    print(f"  완료 시각: {datetime.now()}")

    spark.stop()

if __name__ == "__main__":
    main()
PYEOF
```

### 2-3. Spark JDBC Full Export 실행

```bash
docker exec lab-spark-master spark-submit \
  --master spark://spark-master:7077 \
  --packages io.delta:delta-spark_2.12:3.1.0,mysql:mysql-connector-java:8.0.33 \
  /opt/spark-jobs/migration/jdbc_full_export.py
```

### 2-4. 적재 결과 확인

```bash
docker exec lab-spark-master ls -la /data/delta/migration/customers
docker exec lab-spark-master ls -la /data/delta/migration/transactions
```

> **Spark JDBC 병렬 읽기 핵심 옵션**:
> - `column`: 병렬 분할 기준 컬럼 (보통 숫자형 PK)
> - `lowerBound` / `upperBound`: 파티션 범위 계산 값
> - `numPartitions`: JDBC 병렬 연결 수, 소스 DB 부하와 함께 조정
> - `mode("overwrite")`: Full Export를 멱등하게 재실행하기 위한 기본 전략

**Day 2 완료 기준**: Spark JDBC Full Export 3건 (`customers`, `merchants`, `transactions`) 완료, Delta Lake Bronze 디렉터리 생성 확인, 병렬 읽기 설정 검토 완료.

---

## Day 3: Spark JDBC 증분 이관 + 정합성 검증

### 3-1. Spark JDBC Incremental Append 설계

`INSERT only` 성격의 `transactions`는 마지막 `tx_id` 이후 데이터만 읽는 append 패턴을 적용한다. 마지막 워터마크는 Delta Lake Bronze에서 직접 계산해 별도 상태 저장소 없이 재실행 가능하게 만든다.

### 3-2. Spark JDBC Incremental Import 스크립트 작성

```bash
cat > spark-jobs/migration/jdbc_incremental.py << 'PYEOF'
"""
Spark JDBC Incremental Import — 거래 이력 증분 이관
Week 6 Day 3: 마지막 tx_id 이후 신규 건만 추출하여 Delta Lake에 추가
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, lit, max as spark_max
from datetime import datetime

def create_spark():
    return SparkSession.builder \
        .appName("nexuspay-JDBC-Incremental") \
        .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.1.0,mysql:mysql-connector-java:8.0.33") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()

JDBC_URL = "jdbc:mysql://mysql:3306/nexuspay_legacy"
JDBC_PROPS = {
    "user": "nexuspay",
    "password": "nexuspay1234",
    "driver": "com.mysql.cj.jdbc.Driver"
}

MIGRATION_PATH = "/data/delta/migration/transactions"

def get_last_value(spark, path, column):
    """Delta Lake에서 마지막 증분 값 조회"""
    try:
        df = spark.read.format("delta").load(path)
        result = df.agg(spark_max(column)).first()[0]
        print(f"  마지막 {column}: {result}")
        return result
    except Exception:
        print("  기존 데이터 없음 — 전체 이관 필요")
        return 0

def incremental_import(spark, table, check_column, last_value, target_path):
    """증분 이관: last_value 이후 데이터만 추출"""
    print(f"\n{'='*60}")
    print(f" Incremental Import: {table} ({check_column} > {last_value})")
    print(f"{'='*60}")

    query = f"(SELECT * FROM {table} WHERE {check_column} > {last_value}) AS incremental"

    df = spark.read.jdbc(
        url=JDBC_URL,
        table=query,
        properties=JDBC_PROPS
    )

    new_count = df.count()
    print(f"  신규 건수: {new_count}")

    if new_count == 0:
        print("  신규 데이터 없음 — 스킵")
        return 0

    df = df.withColumn("_ingested_at", current_timestamp()) \
           .withColumn("_source", lit("mysql.nexuspay_legacy")) \
           .withColumn("_migration_type", lit("incremental_append")) \
           .withColumn("_batch_id", lit(datetime.now().strftime("%Y%m%d_%H%M%S")))

    df.write \
      .format("delta") \
      .mode("append") \
      .save(target_path)

    total = spark.read.format("delta").load(target_path).count()
    print(f"  적재 완료: +{new_count} 건 (총 {total} 건)")
    return new_count

def main():
    spark = create_spark()
    last_tx_id = get_last_value(spark, MIGRATION_PATH, "tx_id")
    imported = incremental_import(spark, "transactions", "tx_id", last_tx_id, MIGRATION_PATH)
    print(f"\n  증분 이관 완료: {imported} 건 추가")
    spark.stop()

if __name__ == "__main__":
    main()
PYEOF
```

### 3-3. 신규 데이터 추가 후 증분 이관 실행

```bash
# MySQL에 신규 거래 1,000건 추가 (실시간 유입 시뮬레이션)
docker exec lab-mysql mysql -u nexuspay -pnexuspay1234 nexuspay_legacy << 'SQL'
DELIMITER //
CREATE PROCEDURE generate_new_tx()
BEGIN
    DECLARE i INT DEFAULT 1;
    WHILE i <= 1000 DO
        INSERT INTO transactions (customer_id, merchant_id, amount, tx_type, channel, status, created_at)
        VALUES (
            1 + FLOOR(RAND() * 500),
            1 + FLOOR(RAND() * 100),
            1000 + FLOOR(RAND() * 4999000),
            ELT(1 + FLOOR(RAND()*3), 'PAYMENT','REFUND','CANCEL'),
            ELT(1 + FLOOR(RAND()*4), 'ONLINE','OFFLINE','MOBILE','ATM'),
            'SUCCESS',
            NOW()
        );
        SET i = i + 1;
    END WHILE;
END //
DELIMITER ;
CALL generate_new_tx();
DROP PROCEDURE generate_new_tx;
SQL

docker exec lab-spark-master spark-submit \
  --master spark://spark-master:7077 \
  --packages io.delta:delta-spark_2.12:3.1.0,mysql:mysql-connector-java:8.0.33 \
  /opt/spark-jobs/migration/jdbc_incremental.py

NEW_TOTAL=$(docker exec lab-mysql mysql -u nexuspay -pnexuspay1234 -N \
  -e "SELECT COUNT(*) FROM nexuspay_legacy.transactions")
echo "MySQL 총 건수: ${NEW_TOTAL} (초기 100,000 + 신규 1,000)"
```

> **Incremental Append 핵심**:
> - `tx_id > last_tx_id` 방식은 INSERT only 테이블에 가장 단순하고 빠르다.
> - 마지막 워터마크를 Delta Lake에서 읽기 때문에 재실행에 강하다.
> - UPDATE·DELETE를 반영해야 하는 테이블에는 그대로 적용하면 안 된다.

### 3-4. Incremental Lastmodified 패턴 (참고)

정산처럼 UPDATE가 발생하지만 실시간성이 절대적이지 않은 테이블은 `updated_at` 워터마크와 `Delta MERGE`를 조합할 수 있다. 다만 DELETE 처리와 낮은 지연 요구사항까지 고려하면 Day 4의 Debezium CDC가 더 적합하다.

```python
from delta.tables import DeltaTable

watermark = "2026-04-01 00:00:00"
query = f"(SELECT * FROM settlements WHERE updated_at > '{watermark}') t"

changes_df = spark.read.jdbc(url=JDBC_URL, table=query, properties=JDBC_PROPS)

DeltaTable.forPath(spark, "/data/delta/migration/settlements") \
    .alias("t") \
    .merge(changes_df.alias("s"), "t.settlement_id = s.settlement_id") \
    .whenMatchedUpdateAll() \
    .whenNotMatchedInsertAll() \
    .execute()
```

### 3-5. 정합성 검증 — 소스 DB ↔ Delta Lake 건수 비교

```bash
cat > spark-jobs/migration/verify_migration.py << 'PYEOF'
"""
이관 정합성 검증 — MySQL 소스 ↔ Delta Lake 타겟 건수·PK 비교
Week 6 Day 3: 배치 이관 후 데이터 일치 여부 검증
"""
from pyspark.sql import SparkSession

def create_spark():
    return SparkSession.builder \
        .appName("nexuspay-Migration-Verify") \
        .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.1.0,mysql:mysql-connector-java:8.0.33") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()

JDBC_URL = "jdbc:mysql://mysql:3306/nexuspay_legacy"
JDBC_PROPS = {"user": "nexuspay", "password": "nexuspay1234", "driver": "com.mysql.cj.jdbc.Driver"}
MIGRATION_ROOT = "/data/delta/migration"

def verify_table(spark, table_name, pk_column):
    print(f"\n{'-'*50}")
    print(f"  검증: {table_name}")
    print(f"{'-'*50}")

    src_df = spark.read.jdbc(url=JDBC_URL, table=table_name, properties=JDBC_PROPS)
    tgt_df = spark.read.format("delta").load(f"{MIGRATION_ROOT}/{table_name}")

    src_count = src_df.count()
    tgt_count = tgt_df.count()
    count_match = "PASS" if src_count == tgt_count else "FAIL"
    print(f"  건수 비교: MySQL={src_count:,} / Delta={tgt_count:,} -> {count_match}")

    src_pks = set(src_df.select(pk_column).rdd.flatMap(lambda x: x).collect())
    tgt_pks = set(tgt_df.select(pk_column).rdd.flatMap(lambda x: x).collect())

    missing = src_pks - tgt_pks
    extra = tgt_pks - src_pks
    print(f"  누락 건수: {len(missing)}")
    print(f"  추가 건수: {len(extra)}")

    return src_count == tgt_count and len(missing) == 0 and len(extra) == 0

def main():
    spark = create_spark()
    tables = [
        ("customers", "customer_id"),
        ("merchants", "merchant_id"),
        ("transactions", "tx_id"),
    ]

    results = []
    for table, pk in tables:
        results.append(verify_table(spark, table, pk))

    print("\n전체 결과:", "ALL PASS" if all(results) else "FAIL")
    spark.stop()

if __name__ == "__main__":
    main()
PYEOF

docker exec lab-spark-master spark-submit \
  --master spark://spark-master:7077 \
  --packages io.delta:delta-spark_2.12:3.1.0,mysql:mysql-connector-java:8.0.33 \
  /opt/spark-jobs/migration/verify_migration.py
```

### 3-6. Spark JDBC vs Debezium 선택 기준 정리

```bash
cat > docs/spark-jdbc-vs-debezium.md << 'EOF'
# Spark JDBC vs Debezium 선택 가이드

## 기술 비교

| 항목 | Spark JDBC | Debezium CDC |
|------|------------|--------------|
| 데이터 획득 방식 | JDBC SELECT | MySQL binlog 읽기 |
| 지연 | 분~시간 | 초~밀리초 |
| DELETE 감지 | 불가 | 가능 |
| 변환 유연성 | 매우 높음 (DataFrame API) | 중간 (SMT + 후처리) |
| 소스 DB 부하 | 높음 | 낮음 |
| 적합한 패턴 | Full Export, Incremental Append | 상태 변경, 실시간 동기화 |

## 권장 시나리오

| 상황 | 권장 방식 | 이유 |
|------|-----------|------|
| 고객·가맹점 마스터 | Spark JDBC Full Export | 야간 배치로 단순하게 재적재 가능 |
| 거래 이력 누적 테이블 | Spark JDBC Incremental Append | PK 워터마크 기반 증분 추출이 단순 |
| 정산 상태 변경 테이블 | Debezium CDC | UPDATE·DELETE와 낮은 지연을 함께 처리 |
| 이관 중 변환·품질 검증 필요 | Spark JDBC | Spark 코드에서 적재와 검증을 함께 수행 가능 |

## 결론

배치 이관의 기본값은 Spark JDBC다.
실시간성, DELETE 추적, 상태 변경 반영이 중요해지는 지점부터 Debezium CDC로 전환한다.
EOF
```

**Day 3 완료 기준**: `transactions` 1,000건 증분 이관 완료, 소스↔타겟 정합성 검증 통과, `Spark JDBC vs Debezium` 선택 가이드 작성 완료.

---

## Day 4: Debezium CDC 실시간 이관

### 4-1. Debezium + Kafka Connect 환경 구성

```yaml
  # ──────────────────────────────────────
  # Kafka Connect + Debezium — CDC 실시간 이관
  # ──────────────────────────────────────
  kafka-connect:
    image: debezium/connect:2.5
    container_name: lab-kafka-connect
    environment:
      BOOTSTRAP_SERVERS: kafka-1:9092,kafka-2:9092,kafka-3:9092
      GROUP_ID: nexuspay-connect
      CONFIG_STORAGE_TOPIC: _connect-configs
      OFFSET_STORAGE_TOPIC: _connect-offsets
      STATUS_STORAGE_TOPIC: _connect-status
      CONFIG_STORAGE_REPLICATION_FACTOR: 3
      OFFSET_STORAGE_REPLICATION_FACTOR: 3
      STATUS_STORAGE_REPLICATION_FACTOR: 3
      KEY_CONVERTER: org.apache.kafka.connect.json.JsonConverter
      VALUE_CONVERTER: org.apache.kafka.connect.json.JsonConverter
      KEY_CONVERTER_SCHEMAS_ENABLE: "true"
      VALUE_CONVERTER_SCHEMAS_ENABLE: "true"
    ports:
      - "8084:8083"
    depends_on:
      kafka-1:
        condition: service_healthy
      kafka-2:
        condition: service_healthy
      kafka-3:
        condition: service_healthy
      mysql:
        condition: service_healthy
    networks:
      - pipeline-net
    healthcheck:
      test: ["CMD-SHELL", "curl -sf http://localhost:8083/ || exit 1"]
      interval: 15s
      timeout: 10s
      retries: 10
      start_period: 30s
```

```bash
# Kafka Connect 기동
docker compose up -d kafka-connect

# 상태 확인
curl -s http://localhost:8084/ | python3 -m json.tool

# 사용 가능한 커넥터 플러그인 확인
curl -s http://localhost:8084/connector-plugins | python3 -m json.tool | grep class
```

### 4-2. Debezium MySQL 커넥터 등록

```bash
cat > config/debezium-mysql-connector.json << 'JSON'
{
  "name": "nexuspay-mysql-cdc",
  "config": {
    "connector.class": "io.debezium.connector.mysql.MySqlConnector",
    "tasks.max": "1",
    "database.hostname": "mysql",
    "database.port": "3306",
    "database.user": "debezium",
    "database.password": "debezium1234",
    "database.server.id": "100",
    "topic.prefix": "nexuspay.cdc",
    "database.include.list": "nexuspay_legacy",
    "table.include.list": "nexuspay_legacy.settlements,nexuspay_legacy.transactions",
    "schema.history.internal.kafka.bootstrap.servers": "kafka-1:9092,kafka-2:9092,kafka-3:9092",
    "schema.history.internal.kafka.topic": "_schema-history.nexuspay",
    "include.schema.changes": "true",
    "snapshot.mode": "initial",
    "decimal.handling.mode": "double",
    "time.precision.mode": "connect",
    "tombstones.on.delete": "true",
    "transforms": "unwrap",
    "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState",
    "transforms.unwrap.drop.tombstones": "false",
    "transforms.unwrap.delete.handling.mode": "rewrite",
    "transforms.unwrap.add.fields": "op,source.ts_ms,db,table"
  }
}
JSON

# 커넥터 등록
curl -X POST http://localhost:8084/connectors \
  -H "Content-Type: application/json" \
  -d @config/debezium-mysql-connector.json | python3 -m json.tool

# 커넥터 상태 확인
curl -s http://localhost:8084/connectors/nexuspay-mysql-cdc/status | python3 -m json.tool
```

> **Debezium 핵심 설정 해설**:
> - `topic.prefix`: CDC 이벤트가 발행될 Kafka 토픽의 접두사 (예: `nexuspay.cdc.nexuspay_legacy.settlements`)
> - `snapshot.mode: initial`: 최초 실행 시 기존 데이터 전체를 스냅샷으로 캡처
> - `tombstones.on.delete`: DELETE 발생 시 tombstone 이벤트 생성 (다운스트림에서 삭제 감지 가능)
> - `transforms.unwrap`: Debezium의 복잡한 이벤트 구조를 단순화 (before/after 엔벨로프 제거)
> - `delete.handling.mode: rewrite`: DELETE 이벤트에 `__deleted=true` 필드 추가

### 4-3. CDC 이벤트 확인 — 스냅샷 단계

```bash
# CDC 토픽 목록 확인
docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka-1:9092 --list | grep nexuspay.cdc

# settlements 테이블 CDC 이벤트 확인 (스냅샷)
docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka-1:9092 \
  --topic nexuspay.cdc.nexuspay_legacy.settlements \
  --from-beginning \
  --max-messages 3 | python3 -m json.tool
```

### 4-4. 실시간 변경 테스트 — INSERT, UPDATE, DELETE

```bash
# 터미널 1: CDC 이벤트 실시간 모니터링
docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka-1:9092 \
  --topic nexuspay.cdc.nexuspay_legacy.settlements \
  --property print.key=true \
  --property print.timestamp=true

# 터미널 2: MySQL에서 실시간 변경 실행
docker exec -it lab-mysql mysql -u nexuspay -pnexuspay1234 nexuspay_legacy

# === INSERT: 새 정산 건 추가 ===
INSERT INTO settlements (merchant_id, settlement_date, total_amount, fee_amount, net_amount, tx_count, status)
VALUES (1, CURDATE(), 5000000, 100000, 4900000, 50, 'PENDING');
-- → CDC 이벤트: op=c (create)

# === UPDATE: 정산 상태 변경 (PENDING → PROCESSING) ===
UPDATE settlements SET status = 'PROCESSING', processed_at = NOW()
WHERE settlement_id = (SELECT MAX(settlement_id) FROM (SELECT settlement_id FROM settlements) t);
-- → CDC 이벤트: op=u (update), before/after 값 포함

# === UPDATE: 정산 완료 (PROCESSING → COMPLETED) ===
UPDATE settlements SET status = 'COMPLETED', completed_at = NOW()
WHERE settlement_id = (SELECT MAX(settlement_id) FROM (SELECT settlement_id FROM settlements) t);
-- → CDC 이벤트: op=u (update)

# === DELETE: 정산 취소 ===
DELETE FROM settlements
WHERE settlement_id = (SELECT MAX(settlement_id) FROM (SELECT settlement_id FROM settlements) t);
-- → CDC 이벤트: op=d (delete) + tombstone
```

### 4-5. CDC 이벤트 → Delta Lake 실시간 적재

```bash
cat > spark-jobs/migration/cdc_to_delta.py << 'PYEOF'
"""
Debezium CDC → Delta Lake 실시간 적재
Week 6 Day 4: Kafka CDC 토픽을 Spark Structured Streaming으로 읽어
Delta Lake에 MERGE (Upsert + Delete) 수행
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp, lit, when
from pyspark.sql.types import StructType, StructField, StringType, LongType, IntegerType, DoubleType, TimestampType

def create_spark():
    return SparkSession.builder \
        .appName("nexuspay-CDC-to-Delta") \
        .config("spark.jars.packages",
                "io.delta:delta-spark_2.12:3.1.0,"
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()

# Debezium unwrap 후 스키마 (settlements 테이블)
SETTLEMENT_SCHEMA = StructType([
    StructField("settlement_id", LongType()),
    StructField("merchant_id", LongType()),
    StructField("settlement_date", StringType()),
    StructField("total_amount", LongType()),
    StructField("fee_amount", LongType()),
    StructField("net_amount", LongType()),
    StructField("tx_count", IntegerType()),
    StructField("status", StringType()),
    StructField("processed_at", StringType()),
    StructField("completed_at", StringType()),
    StructField("created_at", StringType()),
    StructField("updated_at", StringType()),
    StructField("__op", StringType()),          # Debezium operation (c/u/d/r)
    StructField("__source_ts_ms", LongType()),  # 소스 DB 변경 시각
    StructField("__deleted", StringType()),     # 삭제 여부
    StructField("__db", StringType()),
    StructField("__table", StringType()),
])

CDC_TOPIC = "nexuspay.cdc.nexuspay_legacy.settlements"
DELTA_PATH = "/data/delta/migration/settlements_cdc"

def process_batch(batch_df, batch_id):
    """마이크로 배치 단위로 Delta Lake MERGE 수행"""
    if batch_df.isEmpty():
        return

    spark = batch_df.sparkSession
    print(f"\n--- Batch {batch_id}: {batch_df.count()} 건 처리 ---")

    # JSON 파싱
    parsed = batch_df.select(
        from_json(col("value").cast("string"), SETTLEMENT_SCHEMA).alias("data")
    ).select("data.*")

    parsed = parsed.withColumn("_cdc_ingested_at", current_timestamp())

    # Delta 테이블 존재 확인
    from delta.tables import DeltaTable
    if DeltaTable.isDeltaTable(spark, DELTA_PATH):
        delta_table = DeltaTable.forPath(spark, DELTA_PATH)

        # 삭제 건 분리
        deletes = parsed.filter(col("__deleted") == "true")
        upserts = parsed.filter((col("__deleted").isNull()) | (col("__deleted") != "true"))

        # UPSERT (INSERT or UPDATE)
        if upserts.count() > 0:
            delta_table.alias("target").merge(
                upserts.alias("source"),
                "target.settlement_id = source.settlement_id"
            ).whenMatchedUpdateAll() \
             .whenNotMatchedInsertAll() \
             .execute()
            print(f"  UPSERT: {upserts.count()} 건")

        # SOFT DELETE (__deleted 플래그 설정)
        if deletes.count() > 0:
            delta_table.alias("target").merge(
                deletes.alias("source"),
                "target.settlement_id = source.settlement_id"
            ).whenMatchedUpdate(set={
                "__deleted": lit("true"),
                "_cdc_ingested_at": current_timestamp()
            }).execute()
            print(f"  DELETE: {deletes.count()} 건 (소프트 삭제)")
    else:
        # 최초 적재
        parsed.write.format("delta").mode("overwrite").save(DELTA_PATH)
        print(f"  초기 적재: {parsed.count()} 건")

def main():
    spark = create_spark()

    print("="*60)
    print(" Debezium CDC → Delta Lake 실시간 적재 시작")
    print(f" 토픽: {CDC_TOPIC}")
    print(f" 타겟: {DELTA_PATH}")
    print("="*60)

    # Kafka Structured Streaming 읽기
    stream = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka-1:9092,kafka-2:9092,kafka-3:9092") \
        .option("subscribe", CDC_TOPIC) \
        .option("startingOffsets", "earliest") \
        .option("failOnDataLoss", "false") \
        .load()

    # 마이크로 배치 처리
    query = stream.writeStream \
        .foreachBatch(process_batch) \
        .option("checkpointLocation", "/data/checkpoints/cdc_settlements") \
        .trigger(processingTime="10 seconds") \
        .start()

    print("\n스트리밍 시작됨. Ctrl+C로 종료.")
    query.awaitTermination()

if __name__ == "__main__":
    main()
PYEOF
```

### 4-6. CDC 파이프라인 통합 테스트

```bash
# 터미널 1: CDC → Delta Lake 스트리밍 시작
docker exec lab-spark-master spark-submit \
  --master spark://spark-master:7077 \
  --packages io.delta:delta-spark_2.12:3.1.0,org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1 \
  /opt/spark-jobs/migration/cdc_to_delta.py

# 터미널 2: MySQL에서 변경 발생 → Delta Lake 반영 확인
docker exec lab-mysql mysql -u nexuspay -pnexuspay1234 nexuspay_legacy << 'SQL'
-- 정산 상태 대량 변경 (100건)
UPDATE settlements
SET status = 'COMPLETED', completed_at = NOW()
WHERE status = 'PENDING'
LIMIT 100;
SQL

# 터미널 3: Delta Lake 반영 확인
docker exec lab-spark-master spark-submit --packages io.delta:delta-spark_2.12:3.1.0 \
  -c "
from pyspark.sql import SparkSession
spark = SparkSession.builder.config('spark.jars.packages','io.delta:delta-spark_2.12:3.1.0').getOrCreate()
df = spark.read.format('delta').load('/data/delta/migration/settlements_cdc')
print(f'Total: {df.count()}')
df.groupBy('status').count().show()
df.groupBy('__deleted').count().show()
"
```

### 4-7. CDC 이벤트 구조 분석 문서

```bash
cat > docs/cdc-event-structure.md << 'EOF'
# Debezium CDC 이벤트 구조 — 컨설팅 참고 자료

## 이벤트 유형 (op 필드)

| op | 의미 | 발생 시점 |
|----|------|----------|
| r | read (snapshot) | 최초 스냅샷 시 기존 데이터 읽기 |
| c | create | INSERT |
| u | update | UPDATE |
| d | delete | DELETE |

## Unwrap 전후 비교

### Unwrap 전 (원본 Debezium 이벤트)
```json
{
  "before": { "settlement_id": 1, "status": "PENDING", ... },
  "after":  { "settlement_id": 1, "status": "COMPLETED", ... },
  "source": { "db": "nexuspay_legacy", "table": "settlements", "ts_ms": 1711900000000 },
  "op": "u",
  "ts_ms": 1711900000100
}
```

### Unwrap 후 (ExtractNewRecordState 적용)
```json
{
  "settlement_id": 1,
  "status": "COMPLETED",
  ...
  "__op": "u",
  "__source_ts_ms": 1711900000000,
  "__db": "nexuspay_legacy",
  "__table": "settlements"
}
```

## DELETE 처리 전략

Debezium은 DELETE 시 두 가지 이벤트를 발생시킨다:
1. 삭제된 행의 마지막 상태 (op=d) + `__deleted=true`
2. Tombstone (key=PK, value=null) — 로그 컴팩션 시 삭제

Delta Lake에서의 처리:
- Hard Delete: 행 자체를 삭제 (규정 준수 필요 시)
- Soft Delete: `__deleted=true` 플래그만 설정 (감사 추적용, 권장)

EOF
```

**Day 4 완료 기준**: Debezium MySQL 커넥터 정상 작동, INSERT/UPDATE/DELETE CDC 이벤트 Kafka 토픽에서 확인, CDC → Delta Lake 실시간 MERGE 파이프라인 작동, CDC 이벤트 구조 문서 작성.

---

## Day 5: 정합성 검증 + 이관 전략 가이드 문서화

### 5-1. 통합 정합성 검증 스크립트

```bash
cat > scripts/verify_migration_all.sh << 'BASH'
#!/bin/bash
echo "============================================"
echo " Week 6 — 전체 이관 정합성 검증"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"

PASS=0
FAIL=0

verify_count() {
    local table=$1
    local src_count=$(docker exec lab-mysql mysql -u nexuspay -pnexuspay1234 -N \
      -e "SELECT COUNT(*) FROM nexuspay_legacy.${table}")
    echo ""
    echo "[${table}]"
    echo "  MySQL (소스) : ${src_count} 건"
    echo "  ※ Delta Lake 건수는 Spark 검증 스크립트로 확인"
}

echo ""
echo "=== 소스 DB (MySQL) 현재 상태 ==="
verify_count "customers"
verify_count "merchants"
verify_count "transactions"
verify_count "settlements"

echo ""
echo "=== Debezium CDC 커넥터 상태 ==="
CDC_STATUS=$(curl -s http://localhost:8084/connectors/nexuspay-mysql-cdc/status | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(f\"  커넥터: {d['connector']['state']}\")
for t in d.get('tasks',[]):
    print(f\"  태스크 {t['id']}: {t['state']}\")
" 2>/dev/null || echo "  ❌ 커넥터 응답 없음")
echo "${CDC_STATUS}"

echo ""
echo "=== Kafka CDC 토픽 오프셋 ==="
docker exec lab-kafka-1 /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server kafka-1:9092 \
  --describe --group nexuspay-connect 2>/dev/null | head -20

echo ""
echo "============================================"
echo " ※ Spark 기반 상세 검증: docker exec lab-spark-master spark-submit /opt/spark-jobs/migration/verify_migration.py"
echo "============================================"
BASH
chmod +x scripts/verify_migration_all.sh
bash scripts/verify_migration_all.sh
```

### 5-2. 이관 전략 가이드 — 고객 제안서용 문서

```bash
cat > docs/migration-strategy-guide.md << 'EOF'
# 데이터 이관 전략 가이드
## Nexus Pay 레거시 DB → 데이터 레이크 이관 프로젝트 결과 보고서

---

### 1. 프로젝트 개요

레거시 MySQL 정산 시스템의 핵심 데이터 4종을 Delta Lake 기반 데이터 레이크로
이관하는 파이프라인을 설계·구축하였다.

### 2. 이관 아키텍처

```
┌───────────────────────────────────────────────────────────────────┐
│                  Nexus Pay 데이터 이관 아키텍처                         │
│                                                                   │
│  ┌─────────────┐     배치 이관 (야간)     ┌──────────────────┐    │
│  │             │  ─── Spark JDBC ────→   │                  │    │
│  │   MySQL     │                          │  Delta Lake      │    │
│  │  (레거시)   │  ─── Debezium CDC ──→   │  (Bronze 레이어)  │    │
│  │             │     Kafka Connect        │                  │    │
│  └─────────────┘     실시간 이관           └──────────────────┘    │
│                                                                   │
│  이관 전략:                                                        │
│  ├── Full Export    : customers, merchants (일 1회)               │
│  ├── Incremental    : transactions (시간 1회)                     │
│  └── CDC (실시간)   : settlements (밀리초 단위)                    │
└───────────────────────────────────────────────────────────────────┘
```

### 3. 테이블별 이관 결과

| 테이블 | 건수 | 이관 전략 | 이관 도구 | 소요 시간 | 정합성 |
|--------|------|----------|----------|----------|--------|
| customers | 500 | Full Export | Spark JDBC | ~10초 | ✅ PASS |
| merchants | 100 | Full Export | Spark JDBC | ~5초 | ✅ PASS |
| transactions | 101,000 | Incremental Append | Spark JDBC | ~30초 | ✅ PASS |
| settlements | 5,000+ | CDC (실시간) | Debezium | 밀리초 | ✅ PASS |

### 4. 핵심 의사결정 및 근거

**Q: 왜 배치 이관에 Spark JDBC를 선택했는가?**
A: 기존 Spark 클러스터와 Delta Lake를 그대로 활용하면서, 이관 중 변환·품질 검증을 DataFrame API로 함께 수행할 수 있기 때문이다.
또한 병렬 분할 읽기와 Delta 직접 적재를 한 코드 경로에서 처리할 수 있다.

**Q: 왜 settlements만 CDC인가?**
A: 정산 테이블은 상태 변경(PENDING→PROCESSING→COMPLETED)이 빈번하고,
UPDATE·DELETE를 감지해야 한다. 배치 이관은 DELETE를 감지하지 못한다.

**Q: CDC의 스냅샷 모드는?**
A: `initial` — 최초 실행 시 기존 데이터를 전체 스냅샷으로 읽은 후
이후부터 binlog 기반 실시간 캡처로 전환한다. CDC로 관리할 테이블은 별도 초기 적재 없이 시작할 수 있다.

### 5. 운영 권장 사항

1. **배치 이관 스케줄**: Airflow DAG으로 매일 03:00 실행 (Week 7에서 구현)
2. **CDC 모니터링**: Kafka Connect REST API로 커넥터 상태 주기적 확인
3. **정합성 검증**: 매일 배치 이관 후 자동 검증 스크립트 실행
4. **장애 복구**: Debezium 스냅샷 재실행 (`snapshot.mode=when_needed`)
5. **스키마 변경**: Debezium의 `include.schema.changes=true` 설정으로 자동 감지

### 6. 위험 요소 및 대응

| 위험 | 영향 | 대응 |
|------|------|------|
| MySQL 부하 증가 | 서비스 성능 저하 | CDC는 binlog 읽기라 부하 최소, 배치는 야간 실행 |
| CDC 지연 | 실시간 대시보드 정확도 저하 | Consumer Lag 모니터링 + 알림 |
| 스키마 변경 | 이관 실패 | Debezium 스키마 히스토리 + Delta Lake 스키마 진화 |
| 네트워크 단절 | CDC 이벤트 유실 | Kafka 토픽 보존 + Debezium 오프셋 복구 |

EOF
```

### 5-3. 아키텍처 문서 — Week 1~6 누적 파이프라인

```bash
cat > docs/migration-architecture.md << 'EOF'
# Nexus Pay 데이터 파이프라인 아키텍처 — Week 6 완성

## 전체 흐름

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                       Nexus Pay 데이터 파이프라인 전체 아키텍처                     │
│                                                                              │
│  [레거시 시스템 — Week 6]                                                     │
│  ┌─────────────┐                                                             │
│  │ MySQL       │                                                             │
│  │ (정산 시스템) │ ──── Spark JDBC (배치) ──── → Delta Lake Bronze             │
│  │             │ ──── Debezium CDC (실시간) → Kafka → Delta Lake Bronze        │
│  └─────────────┘                                                             │
│                                                                              │
│  [수집 계층 — Week 2·3]                                                       │
│  ┌─────────────┐                                                             │
│  │ NiFi        │ API·CSV·DB → 스키마 표준화 → PublishKafka                    │
│  └─────┬───────┘                                                             │
│        ▼                                                                     │
│  [버퍼 계층 — Week 2]                                                         │
│  ┌─────────────────────────────────────┐                                     │
│  │ Kafka (3-브로커 클러스터)              │                                    │
│  │ ├── nexuspay.events.ingested (수집)    │                                    │
│  │ ├── nexuspay.cdc.* (CDC 이벤트)        │                                    │
│  │ ├── nexuspay.aggregation.* (집계 결과)  │                                    │
│  │ └── nexuspay.alerts.fraud (이상거래)    │                                    │
│  └─────────────┬───────────────────────┘                                     │
│                │                                                             │
│        ┌───────┴───────┐                                                     │
│        ▼               ▼                                                     │
│  [변환 계층 — Week 4·5]                                                       │
│  ┌────────────────┐  ┌────────────────┐                                      │
│  │ Flink (실시간)  │  │ Spark (배치)    │                                      │
│  │ ─ 윈도우 집계   │  │ ─ 일별 정산     │                                      │
│  │ ─ 이상거래 탐지  │  │ ─ 품질 검증     │                                      │
│  │ ─ Exactly-once  │  │ ─ Delta Lake    │                                     │
│  └───────┬────────┘  └────────┬───────┘                                      │
│          ▼                    ▼                                               │
│  [저장 계층]                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────────┐                       │
│  │ Redis    │  │ PostgreSQL│  │ Delta Lake             │                      │
│  │ 실시간    │  │ 정산 리포트│  │ Bronze·Silver·Gold     │                      │
│  │ 피처 캐시 │  │ 메타데이터 │  │ + 이관 데이터 (Week 6) │                       │
│  └──────────┘  └──────────┘  └───────────────────────┘                       │
│                                                                              │
│  [오케스트레이션 — Week 7]                                                     │
│  ┌────────────┐                                                              │
│  │ Airflow    │ DAG 스케줄링 · SLA 모니터링 · 장애 알림                        │
│  └────────────┘                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

EOF
```

### 5-4. Git 커밋

```bash
git add .
git commit -m "Week 6: 이관 파이프라인 — Spark JDBC 배치 + Debezium CDC 실시간"
```

**Day 5 완료 기준**: 통합 정합성 검증 스크립트 실행 완료, 이관 전략 가이드 작성, 아키텍처 문서 작성, Git 커밋.

---

## Week 6 산출물 체크리스트

| # | 산출물 | 완료 |
|---|--------|------|
| 1 | docs/migration-concepts.md (이관 핵심 개념 정리) | ☐ |
| 2 | docs/migration-target-tables.md (이관 대상 테이블 분류) | ☐ |
| 3 | scripts/init-mysql.sql (MySQL 레거시 DB 초기화) | ☐ |
| 4 | docker-compose.yml 업데이트 (MySQL + Kafka Connect 추가) | ☐ |
| 5 | spark-jobs/migration/jdbc_full_export.py (Spark JDBC 전체 이관) | ☐ |
| 6 | spark-jobs/migration/jdbc_incremental.py (Spark JDBC 증분 이관) | ☐ |
| 7 | spark-jobs/migration/verify_migration.py (이관 정합성 검증) | ☐ |
| 8 | docs/spark-jdbc-vs-debezium.md (배치/실시간 선택 가이드) | ☐ |
| 9 | config/debezium-mysql-connector.json (Debezium 커넥터 설정) | ☐ |
| 10 | spark-jobs/migration/cdc_to_delta.py (CDC → Delta Lake 스트리밍) | ☐ |
| 11 | docs/cdc-event-structure.md (CDC 이벤트 구조 문서) | ☐ |
| 12 | scripts/verify_migration_all.sh (통합 정합성 검증) | ☐ |
| 13 | docs/migration-strategy-guide.md (이관 전략 가이드) | ☐ |
| 14 | docs/migration-architecture.md (아키텍처 문서) | ☐ |
| 15 | Git 커밋 | ☐ |

## 핵심 개념 요약

| 개념 | 요약 | 실습에서 확인한 것 |
|------|------|------------------|
| Full Export | 테이블 전체를 한 번에 복사 | customers·merchants Spark JDBC 이관 |
| Incremental Append | 신규 행만 추출 (PK > last_value) | transactions 1,000건 증분 이관 |
| Incremental Lastmodified | 변경 행 추출 (updated_at > last) | settlements lastmodified 패턴 검토 (참고) |
| CDC (Change Data Capture) | DB 트랜잭션 로그 기반 실시간 변경 캡처 | Debezium MySQL binlog 캡처 |
| Debezium | 오픈소스 CDC 플랫폼 (Kafka Connect 기반) | MySQL → Kafka → Delta Lake 파이프라인 |
| binlog (ROW format) | MySQL 행 단위 변경 로그 | INSERT/UPDATE/DELETE 이벤트 확인 |
| Snapshot Mode | 최초 실행 시 기존 데이터 전체 캡처 | `initial` 모드 → 이후 실시간 전환 |
| ExtractNewRecordState | Debezium 이벤트 단순화 변환 | before/after 엔벨로프 → 단순 레코드 |
| Tombstone | DELETE 시 key만 남는 null 이벤트 | Kafka 로그 컴팩션에서 삭제 마커 역할 |
| Soft Delete | `__deleted=true` 플래그로 논리적 삭제 | Delta Lake에서 감사 추적 가능 |
| Data Reconciliation | 소스↔타겟 정합성 검증 | 건수·PK 비교 검증 도구 |
| Delta MERGE | 변경분 upsert 처리 구문 | settlements 변경 반영 패턴 검토 |
| Spark JDBC | Spark 기반 배치 이관 방식 (Delta Lake 직접 연동) | DataFrame API 기반 이관 + 검증 |

## Week 7 예고

Week 7에서는 Apache Airflow를 활용한 오케스트레이션 심화 실습을 진행한다. Week 1~6에서 구축한 모든 파이프라인(배치 이관, CDC 모니터링, Spark ETL, 정합성 검증)을 Airflow DAG으로 스케줄링하고, SLA 모니터링·장애 복구·알림 설정을 통해 운영 수준의 파이프라인 오케스트레이션을 완성한다. Day 2에서 만든 배치 이관이 매일 자동으로 실행되고, Day 3의 정합성 검증이 이관 후 자동으로 수행되며, Day 4의 CDC 커넥터 상태가 주기적으로 점검되는 통합 워크플로우를 구현한다.
