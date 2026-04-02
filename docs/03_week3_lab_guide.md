# Week 3: 수집 — NiFi 다중 소스 데이터 수집

**기간**: 5일 (월~금, 풀타임 40시간)
**주제**: 다중 소스 수집 파이프라인, NiFi 프로세서 그룹, Provenance 추적, Kafka 연동
**산출물**: NiFi 다중 소스 수집 플로우 + Kafka 연동 파이프라인 + Provenance 모니터링 가이드 + 데이터 흐름 아키텍처 문서
**전제 조건**: Week 1·2 환경 정상 기동 (`bash scripts/healthcheck-all.sh` 전체 통과), Kafka 3-브로커 클러스터 가동 중

---

## 수행 시나리오

### 배경 설정

페이넥스(PayNex) CTO가 Kafka 아키텍처 검증 결과에 만족했다. 이제 실질적인 데이터 수집 과제를 제시한다.

> "우리 데이터 소스가 한 곳이 아닙니다. 결제 API에서 JSON이 실시간으로 들어오고, 레거시 정산 시스템은 매시간 CSV 파일을 떨구고, 고객 마스터 데이터는 PostgreSQL에 있습니다. 이 세 가지를 **하나의 파이프라인으로 통합 수집**하되, 어떤 데이터가 언제 어디서 들어왔는지 **추적 가능**해야 합니다. 금융감독원 감사 때 데이터 출처를 증명하지 못하면 곤란합니다."

컨설턴트로서 NiFi를 활용하여 REST API·파일 시스템·데이터베이스 세 가지 이기종 소스에서 데이터를 수집하고, 스키마 표준화 후 Kafka로 라우팅하며, Provenance를 통해 전체 데이터 계보를 추적하는 파이프라인을 구축하는 것이 이번 주의 과제다.

### 목표

1. NiFi 프로세서 그룹을 활용한 체계적 플로우 설계 및 구현
2. REST API·CSV 파일·PostgreSQL 세 가지 이기종 소스 수집 파이프라인 구축
3. 수집 데이터의 스키마 표준화 및 데이터 품질 검증 로직 구현
4. NiFi → Kafka 연동을 통한 수집 데이터 실시간 라우팅
5. Provenance 추적을 활용한 데이터 계보(Lineage) 확인 및 감사 대응 역량 확보

### 일정 개요

| 일차 | 주제 | 핵심 작업 |
|------|------|----------|
| Day 1 | NiFi 핵심 개념 + 프로세서 그룹 설계 | NiFi 아키텍처 이해, 프로세서 그룹 구성, 기본 플로우 구현 |
| Day 2 | REST API 수집 파이프라인 | InvokeHTTP 기반 실시간 API 수집, JSON 파싱·변환, 오류 처리 |
| Day 3 | 파일·DB 수집 파이프라인 | CSV 파일 감시·수집, PostgreSQL 쿼리 기반 수집, 증분 추출 |
| Day 4 | Kafka 연동 + 스키마 표준화 | PublishKafka 연동, 다중 소스 스키마 통합, 데이터 품질 라우팅 |
| Day 5 | Provenance 추적 + 문서화 | 데이터 계보 추적, 모니터링 대시보드, 운영 가이드 작성 |

---

## Day 1: NiFi 핵심 개념 + 프로세서 그룹 설계

### 1-1. NiFi 아키텍처 핵심 개념 정리

NiFi를 활용한 컨설팅에서 고객에게 설명해야 하는 핵심 개념을 정리한다.

```
┌──────────────────────────────────────────────────────────┐
│                    NiFi 핵심 구성 요소                      │
│                                                            │
│  FlowFile = 데이터 단위                                     │
│    ├── Content (실제 데이터: JSON, CSV, 바이너리 등)         │
│    └── Attributes (메타데이터: filename, uuid, mime.type 등) │
│                                                            │
│  Processor = 작업 단위                                      │
│    ├── Source: 데이터 생성 (GetFile, InvokeHTTP 등)         │
│    ├── Transform: 데이터 변환 (JoltTransformJSON 등)        │
│    └── Sink: 데이터 전달 (PublishKafka, PutDatabaseRecord)  │
│                                                            │
│  Connection = 프로세서 간 큐                                 │
│    ├── FlowFile 대기열 (back-pressure 제어)                 │
│    └── Relationship 기반 라우팅 (success, failure, retry)    │
│                                                            │
│  Process Group = 논리적 플로우 묶음                           │
│    └── 소스별·기능별 그룹화 → 복잡도 관리                     │
│                                                            │
│  Provenance = 데이터 이력 추적                               │
│    └── 모든 FlowFile의 생성·변환·전달 이력 기록               │
└──────────────────────────────────────────────────────────┘
```

```bash
cat > docs/nifi-concepts.md << 'EOF'
# NiFi 핵심 개념 정리 — 컨설팅 설명 자료

## FlowFile

NiFi에서 처리되는 데이터의 최소 단위. Content(실제 데이터)와 Attributes(메타데이터)로 구성된다.
금융 데이터 관점에서 하나의 FlowFile은 거래 1건, CSV 파일 1개, API 응답 1회에 대응한다.

## Processor

FlowFile을 생성·변환·전달하는 작업 단위. NiFi는 300개 이상의 내장 프로세서를 제공한다.
PayNex에서 사용할 핵심 프로세서:
- InvokeHTTP: REST API 호출
- GetFile / ListFile + FetchFile: 파일 시스템 감시·수집
- ExecuteSQL / QueryDatabaseTable: DB 쿼리 수집
- JoltTransformJSON: JSON 스키마 변환
- PublishKafka: Kafka 토픽으로 전송
- RouteOnAttribute / RouteOnContent: 조건부 라우팅

## Connection & Back-Pressure

프로세서 간 큐 역할. Back-pressure 임계값(FlowFile 수, 데이터 크기)을 설정하면
큐가 차면 상류 프로세서가 자동 일시 정지 → 시스템 과부하 방지.

## Process Group

복수의 프로세서를 논리 단위로 묶는 컨테이너. Input/Output Port로 그룹 간 데이터 전달.
소스별(API, File, DB), 기능별(수집, 변환, 라우팅)로 그룹화하여 복잡도를 관리한다.

## Provenance

모든 FlowFile의 생명주기를 기록하는 감사 로그.
금융감독원 감사 대응에 핵심 — 데이터가 어디서 왔고 어떤 변환을 거쳤는지 증명 가능.

EOF
```

### 1-2. PayNex 수집 아키텍처 설계

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PayNex NiFi 수집 아키텍처                         │
│                                                                     │
│  ┌─────────────────┐                                                │
│  │ Source 1: API    │  InvokeHTTP → JSON 파싱 → 스키마 변환 ─────┐  │
│  │ (결제 이벤트)     │                                           │  │
│  └─────────────────┘                                             │  │
│                                                                  ▼  │
│  ┌─────────────────┐                                   ┌──────────┐ │
│  │ Source 2: File   │  ListFile → FetchFile → CSV→JSON  │ 스키마   │ │
│  │ (정산 CSV)       │  → 스키마 변환 ──────────────────→│ 표준화   │ │
│  └─────────────────┘                                   │ & 품질   │ │
│                                                        │ 검증     │ │
│  ┌─────────────────┐                                   │          │ │
│  │ Source 3: DB     │  QueryDatabaseTable → JSON 변환   │          │ │
│  │ (고객 마스터)     │  → 스키마 변환 ──────────────────→└────┬─────┘ │
│  └─────────────────┘                                        │       │
│                                                             ▼       │
│                                                   ┌─────────────┐   │
│                                                   │ PublishKafka │   │
│                                                   │ ─────────── │   │
│                                                   │ 정상 → Kafka │   │
│                                                   │ 불량 → DLQ   │   │
│                                                   └─────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 1-3. NiFi 프로세서 그룹 구조 설계

NiFi UI에서 구현할 프로세서 그룹 계층을 먼저 설계한다.

```bash
cat > config/nifi/process-group-design.md << 'EOF'
# PayNex NiFi 프로세서 그룹 설계

## 최상위 그룹: PayNex Data Ingestion

### PG-1: API Ingestion (결제 이벤트 수집)
- InvokeHTTP → EvaluateJsonPath → JoltTransformJSON → Output Port

### PG-2: File Ingestion (정산 CSV 수집)
- ListFile → FetchFile → ConvertRecord(CSV→JSON) → JoltTransformJSON → Output Port

### PG-3: DB Ingestion (고객 마스터 수집)
- QueryDatabaseTable → ConvertRecord(Avro→JSON) → JoltTransformJSON → Output Port

### PG-4: Schema Standardization (스키마 표준화)
- Input Port → ValidateRecord → RouteOnAttribute
  - valid → UpdateAttribute(source_tag 추가) → Output Port
  - invalid → Output Port (DLQ로 전달)

### PG-5: Kafka Publishing (Kafka 전달)
- Input Port → PublishKafka_2_6
  - success → LogAttribute(성공 기록)
  - failure → Retry / DLQ

## 그룹 간 연결
PG-1 Output → PG-4 Input
PG-2 Output → PG-4 Input
PG-3 Output → PG-4 Input
PG-4 Output(valid) → PG-5 Input
PG-4 Output(invalid) → PG-5 Input(DLQ 토픽)

EOF
```

### 1-4. 결제 API 시뮬레이터 구현

NiFi의 InvokeHTTP가 호출할 결제 API를 간단한 Flask 서버로 구현한다.

```python
# scripts/api_payment_simulator.py
"""
PayNex 결제 API 시뮬레이터
- GET /api/v1/payments/recent : 최근 거래 N건 반환
- GET /api/v1/payments/stream : 1건씩 실시간 반환 (polling용)
- NiFi InvokeHTTP가 주기적으로 호출하는 대상
"""

import json
import random
import time
from datetime import datetime, timezone, timedelta
from flask import Flask, jsonify, request

app = Flask(__name__)

# 시퀀스 카운터 (서버 재시작 시 리셋)
_seq_counter = 0
# 마지막 반환 시각 추적 (증분 수집용)
_last_fetched = datetime.now(timezone.utc) - timedelta(minutes=5)

MERCHANTS = [
    {"id": "MCH-101", "name": "스타벅스 강남점", "category": "CAFE"},
    {"id": "MCH-202", "name": "쿠팡 온라인", "category": "ECOMMERCE"},
    {"id": "MCH-303", "name": "GS25 역삼점", "category": "CONVENIENCE"},
    {"id": "MCH-404", "name": "현대백화점 판교", "category": "DEPARTMENT"},
    {"id": "MCH-505", "name": "배달의민족", "category": "DELIVERY"},
]

CHANNELS = ["APP", "WEB", "POS", "ATM"]
CURRENCIES = [("KRW", 70), ("USD", 20), ("JPY", 10)]
AMOUNT_RANGES = {
    "KRW": (1000, 5000000),
    "USD": (1, 5000),
    "JPY": (100, 500000),
}


def generate_payment() -> dict:
    """결제 이벤트 1건 생성"""
    global _seq_counter
    _seq_counter += 1

    currency = random.choices(
        [c[0] for c in CURRENCIES],
        weights=[c[1] for c in CURRENCIES],
        k=1
    )[0]
    lo, hi = AMOUNT_RANGES[currency]
    amount = round(random.uniform(lo, hi), 2)

    # 10% 확률 이상거래 패턴
    is_suspicious = random.random() < 0.10
    if is_suspicious:
        amount = round(amount * random.uniform(5.0, 15.0), 2)

    merchant = random.choice(MERCHANTS)

    return {
        "event_id": f"PAY-{_seq_counter:08d}",
        "event_type": "PAYMENT",
        "user_id": random.randint(1001, 2000),
        "amount": amount,
        "currency": currency,
        "merchant": merchant,
        "channel": random.choice(CHANNELS),
        "status": "COMPLETED" if random.random() < 0.92 else "FAILED",
        "is_suspicious": is_suspicious,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "payment-api",
    }


@app.route("/api/v1/payments/recent", methods=["GET"])
def get_recent_payments():
    """최근 거래 N건 반환 (배치 수집용)"""
    count = min(int(request.args.get("count", 10)), 50)
    payments = [generate_payment() for _ in range(count)]
    return jsonify({
        "status": "ok",
        "count": len(payments),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "data": payments,
    })


@app.route("/api/v1/payments/stream", methods=["GET"])
def get_stream_payment():
    """단건 거래 반환 (polling 수집용)"""
    global _last_fetched
    payment = generate_payment()
    _last_fetched = datetime.now(timezone.utc)
    return jsonify(payment)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "seq": _seq_counter})


if __name__ == "__main__":
    print("PayNex 결제 API 시뮬레이터 시작 — http://0.0.0.0:5050")
    app.run(host="0.0.0.0", port=5050, debug=False)
```

### 1-5. API 시뮬레이터를 Docker Compose에 추가

docker-compose.yml의 services 섹션에 추가:

```yaml
  # ──────────────────────────────────────
  # PayNex 결제 API 시뮬레이터
  # ──────────────────────────────────────
  payment-api:
    image: python:3.11-slim
    container_name: lab-payment-api
    working_dir: /app
    command: >
      bash -c "
        pip install flask --quiet &&
        python api_payment_simulator.py
      "
    volumes:
      - ./scripts:/app
    ports:
      - "5050:5050"
    networks:
      - pipeline-net
    healthcheck:
      test: ["CMD-SHELL", "curl -sf http://localhost:5050/health || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 15s
```

### 1-6. 정산 CSV 생성기 구현

레거시 정산 시스템이 매시간 CSV 파일을 생성하는 상황을 시뮬레이션한다.

```python
# scripts/csv_settlement_generator.py
"""
PayNex 정산 CSV 생성기
- /data/settlement/ 디렉토리에 주기적으로 CSV 파일 생성
- 레거시 시스템이 매시간 정산 파일을 떨구는 시나리오 시뮬레이션
"""

import csv
import os
import random
import time
import argparse
from datetime import datetime, timezone, timedelta

OUTPUT_DIR = "./data/settlement"  # pipeline-lab/ 디렉토리에서 실행 기준 (Docker 볼륨 마운트 경로와 일치)

SETTLEMENT_TYPES = ["DAILY_CLOSE", "MERCHANT_PAYOUT", "FEE_CALCULATION", "REFUND_BATCH"]


def generate_settlement_row(seq: int, batch_id: str) -> dict:
    """정산 레코드 1건 생성"""
    return {
        "settlement_id": f"STL-{seq:08d}",
        "batch_id": batch_id,
        "merchant_id": f"MCH-{random.randint(100, 599)}",
        "settlement_type": random.choice(SETTLEMENT_TYPES),
        "gross_amount": round(random.uniform(100000, 50000000), 2),
        "fee_amount": round(random.uniform(1000, 500000), 2),
        "net_amount": 0,  # 아래에서 계산
        "currency": random.choices(["KRW", "USD", "JPY"], weights=[80, 15, 5], k=1)[0],
        "tx_count": random.randint(10, 5000),
        "settlement_date": (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": random.choices(
            ["COMPLETED", "PENDING", "FAILED"],
            weights=[85, 10, 5],
            k=1
        )[0],
    }


def generate_csv_file(row_count: int = 50):
    """정산 CSV 파일 1개 생성"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    batch_id = f"BATCH-{timestamp}"
    filename = f"settlement_{timestamp}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    fieldnames = [
        "settlement_id", "batch_id", "merchant_id", "settlement_type",
        "gross_amount", "fee_amount", "net_amount", "currency",
        "tx_count", "settlement_date", "created_at", "status",
    ]

    rows = []
    for i in range(1, row_count + 1):
        row = generate_settlement_row(i, batch_id)
        row["net_amount"] = round(row["gross_amount"] - row["fee_amount"], 2)
        rows.append(row)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  ✅ 생성: {filepath} ({row_count}건, batch={batch_id})")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="PayNex 정산 CSV 생성기")
    parser.add_argument("-n", "--files", type=int, default=3, help="생성할 파일 수")
    parser.add_argument("-r", "--rows", type=int, default=50, help="파일당 레코드 수")
    parser.add_argument("-i", "--interval", type=int, default=30, help="파일 생성 간격(초)")
    args = parser.parse_args()

    print(f"PayNex 정산 CSV 생성기 시작")
    print(f"  출력 디렉토리: {OUTPUT_DIR}")
    print(f"  파일 수: {args.files}, 파일당 레코드: {args.rows}")
    print("=" * 60)

    for i in range(1, args.files + 1):
        generate_csv_file(args.rows)
        if i < args.files:
            print(f"  ⏳ {args.interval}초 대기...")
            time.sleep(args.interval)

    print("=" * 60)
    print(f"완료: {args.files}개 파일 생성")


if __name__ == "__main__":
    main()
```

### 1-7. 환경 기동 및 기본 검증

```bash
# API 시뮬레이터 기동
docker compose up -d payment-api

# API 정상 응답 확인
curl -s http://localhost:5050/api/v1/payments/recent?count=3 | python3 -m json.tool

# 정산 CSV 디렉토리 생성 (NiFi 컨테이너에서 접근 가능하도록 볼륨 마운트)
mkdir -p data/settlement

# CSV 파일 1개 사전 생성 (테스트용)
python scripts/csv_settlement_generator.py -n 1 -r 20

# 생성된 파일 확인
head -5 data/settlement/settlement_*.csv

# NiFi 웹 UI 접속 확인
curl -sf http://localhost:8080/nifi/ > /dev/null && echo "NiFi OK" || echo "NiFi NOT READY"
```

> **NiFi 볼륨 마운트 추가**: docker-compose.yml의 nifi 서비스에 정산 CSV 디렉토리와 API 네트워크 접근을 위한 볼륨을 추가한다.

```yaml
  nifi:
    image: apache/nifi:1.25.0
    container_name: lab-nifi
    environment:
      NIFI_WEB_HTTP_PORT: 8080
      SINGLE_USER_CREDENTIALS_USERNAME: ${NIFI_USERNAME}
      SINGLE_USER_CREDENTIALS_PASSWORD: ${NIFI_PASSWORD}
    ports:
      - "8080:8080"
    volumes:
      - ./data/settlement:/data/settlement    # 정산 CSV 디렉토리
      - ./config/nifi:/opt/nifi/custom-config  # 커스텀 설정
    networks:
      - pipeline-net
    healthcheck:
      test: ["CMD-SHELL", "curl -sf http://localhost:8080/nifi/ || exit 1"]
      interval: 20s
      timeout: 10s
      retries: 15
      start_period: 60s
```

**Day 1 완료 기준**: NiFi 핵심 개념 문서 작성, 프로세서 그룹 설계 문서 작성, 결제 API 시뮬레이터 정상 동작, 정산 CSV 생성기 정상 동작, NiFi 웹 UI 접속 확인.

---

## Day 2: REST API 수집 파이프라인

### 2-1. NiFi 프로세서 그룹 생성 (UI 작업)

NiFi 웹 UI(`http://localhost:8080/nifi`)에서 다음 프로세서 그룹을 생성한다.

1. 캔버스 상단의 **Process Group** 아이콘을 드래그하여 최상위 그룹 `PayNex Data Ingestion` 생성
2. 그룹 내부로 진입하여 하위 프로세서 그룹 생성:
   - `PG-1: API Ingestion`
   - `PG-2: File Ingestion` (Day 3에서 구성)
   - `PG-3: DB Ingestion` (Day 3에서 구성)
   - `PG-4: Schema Standardization` (Day 4에서 구성)
   - `PG-5: Kafka Publishing` (Day 4에서 구성)

### 2-2. PG-1: API Ingestion 플로우 구성

`PG-1: API Ingestion` 내부에 다음 프로세서를 배치하고 연결한다.

**프로세서 구성**:

```
InvokeHTTP
    │
    ├── (success) → SplitJson
    │                   │
    │                   └── (split) → EvaluateJsonPath
    │                                     │
    │                                     └── (matched) → JoltTransformJSON
    │                                                         │
    │                                                         ├── (success) → Output Port [api-out]
    │                                                         └── (failure) → LogAttribute [변환실패]
    │
    ├── (retry) → InvokeHTTP (자기 자신으로 루프백, 30초 후 재시도)
    └── (failure) → LogAttribute [API호출실패]
```

### 2-3. InvokeHTTP 프로세서 설정

| 속성 | 값 | 설명 |
|------|-----|------|
| HTTP Method | GET | |
| Remote URL | `http://payment-api:5050/api/v1/payments/recent?count=20` | Docker 네트워크 내 호출 |
| Scheduling — Run Schedule | `30 sec` | 30초마다 API 호출 |
| Scheduling — Execution | `Primary Node` | 중복 호출 방지 |
| Content-Type | `application/json` | |
| Connection Timeout | `10 sec` | |
| Read Timeout | `30 sec` | |

> **실무 참고**: 프로덕션에서는 API Rate Limiting을 고려하여 Run Schedule을 적절히 설정한다. PayNex 시나리오에서는 30초마다 최근 20건을 가져오는 polling 방식을 사용한다.

### 2-4. SplitJson 프로세서 설정

API 응답은 `{ "data": [ {...}, {...}, ... ] }` 형태의 배열이므로 개별 레코드로 분리해야 한다.

| 속성 | 값 | 설명 |
|------|-----|------|
| JsonPath Expression | `$.data` | data 배열의 각 요소를 개별 FlowFile로 분리 |
| Null Value Representation | `empty string` | |

### 2-5. EvaluateJsonPath 프로세서 설정

분리된 개별 JSON에서 핵심 필드를 FlowFile Attribute로 추출한다. 이후 라우팅·모니터링에 활용된다.

| 속성 | 값 |
|------|-----|
| Destination | `flowfile-attribute` |
| event_id | `$.event_id` |
| event_type | `$.event_type` |
| user_id | `$.user_id` |
| amount | `$.amount` |
| currency | `$.currency` |
| is_suspicious | `$.is_suspicious` |
| source | `$.source` |
| timestamp | `$.timestamp` |

### 2-6. JoltTransformJSON — 스키마 표준화 변환 스펙

다중 소스에서 수집한 데이터를 하나의 표준 스키마로 변환한다. 이 Jolt 스펙은 Day 3의 파일·DB 소스에도 동일하게 적용된다.

```bash
cat > config/nifi/jolt-spec-api-payment.json << 'EOF'
[
  {
    "operation": "shift",
    "spec": {
      "event_id": "event_id",
      "event_type": "event_type",
      "user_id": "user_id",
      "amount": "amount",
      "currency": "currency",
      "merchant": {
        "id": "merchant_id",
        "name": "merchant_name",
        "category": "merchant_category"
      },
      "channel": "channel",
      "status": "status",
      "is_suspicious": "is_suspicious",
      "timestamp": "event_timestamp",
      "source": "data_source"
    }
  },
  {
    "operation": "default",
    "spec": {
      "schema_version": "1.0",
      "ingested_at": "${now():format('yyyy-MM-dd\\'T\\'HH:mm:ss\\'Z\\'', 'UTC')}"
    }
  }
]
EOF
```

JoltTransformJSON 프로세서 설정:

| 속성 | 값 |
|------|-----|
| Jolt Transformation DSL | Chain |
| Jolt Specification | (위 JSON 스펙 내용 붙여넣기) |

### 2-7. 오류 처리 — LogAttribute 프로세서

API 호출 실패와 변환 실패를 별도로 기록한다.

**API 호출 실패 LogAttribute**:
| 속성 | 값 |
|------|-----|
| Log Level | `warn` |
| Log prefix | `[API-FAIL]` |
| Attributes to Log | `invokehttp.status.code, invokehttp.status.message` |

**변환 실패 LogAttribute**:
| 속성 | 값 |
|------|-----|
| Log Level | `error` |
| Log prefix | `[TRANSFORM-FAIL]` |
| Attributes to Log | `event_id, jolt.error` |

### 2-8. API 수집 플로우 동작 검증

```bash
# API 시뮬레이터 정상 동작 확인
curl -s http://localhost:5050/api/v1/payments/recent?count=3 | python3 -m json.tool

# NiFi UI에서:
# 1. PG-1: API Ingestion 그룹 내 모든 프로세서 시작
# 2. 30초 대기 후 Connection 큐에 FlowFile 확인
# 3. Output Port 직전 Connection에서 FlowFile 1개 선택 → Content 확인
```

**검증 포인트**:

```bash
# NiFi API로 프로세서 상태 확인 (선택사항 — UI에서도 확인 가능)
curl -s http://localhost:8080/nifi-api/flow/process-groups/root | python3 -m json.tool | head -30
```

Output Port 직전의 FlowFile Content가 다음 형태로 변환되어야 한다:

```json
{
  "event_id": "PAY-00000001",
  "event_type": "PAYMENT",
  "user_id": 1542,
  "amount": 325000.00,
  "currency": "KRW",
  "merchant_id": "MCH-101",
  "merchant_name": "스타벅스 강남점",
  "merchant_category": "CAFE",
  "channel": "APP",
  "status": "COMPLETED",
  "is_suspicious": false,
  "event_timestamp": "2026-04-01T09:30:00Z",
  "data_source": "payment-api",
  "schema_version": "1.0",
  "ingested_at": "2026-04-01T09:30:05Z"
}
```

### 2-9. API 수집 성능 측정

```bash
cat > scripts/measure_api_throughput.sh << 'SCRIPT'
#!/bin/bash
# NiFi API 수집 처리량 측정 스크립트

echo "============================================"
echo " API 수집 처리량 측정"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"

# 5분간 수집된 FlowFile 수 추적
echo "5분간 측정 시작..."
START_COUNT=$(curl -s http://localhost:5050/health | python3 -c "import sys,json; print(json.load(sys.stdin)['seq'])")
sleep 300
END_COUNT=$(curl -s http://localhost:5050/health | python3 -c "import sys,json; print(json.load(sys.stdin)['seq'])")

TOTAL=$((END_COUNT - START_COUNT))
echo "  5분간 API 호출로 생성된 이벤트: ${TOTAL}건"
echo "  분당 평균: $((TOTAL / 5))건"
echo "  초당 평균: $(echo "scale=1; $TOTAL / 300" | bc)건"
SCRIPT

chmod +x scripts/measure_api_throughput.sh
```

**Day 2 완료 기준**: PG-1 프로세서 그룹 내 InvokeHTTP → SplitJson → EvaluateJsonPath → JoltTransformJSON 플로우 정상 작동, 표준 스키마로 변환된 FlowFile 확인, 오류 처리 LogAttribute 동작 확인.

---

## Day 3: 파일·DB 수집 파이프라인

### 3-1. PG-2: File Ingestion — 정산 CSV 수집 플로우

`PG-2: File Ingestion` 내부에 다음 프로세서를 배치한다.

```
ListFile
    │
    └── (success) → FetchFile
                       │
                       └── (success) → ConvertRecord (CSV → JSON)
                                          │
                                          └── (success) → SplitRecord (레코드별 분리)
                                                            │
                                                            └── (success) → JoltTransformJSON
                                                                              │
                                                                              ├── (success) → Output Port [file-out]
                                                                              └── (failure) → LogAttribute [변환실패]
```

### 3-2. ListFile 프로세서 설정

| 속성 | 값 | 설명 |
|------|-----|------|
| Input Directory | `/data/settlement` | 정산 CSV 디렉토리 |
| Recurse Subdirectories | `false` | |
| File Filter | `settlement_.*\.csv` | settlement_ 접두사 CSV만 수집 |
| Minimum File Age | `5 sec` | 파일 쓰기 완료 보장 |
| Listing Strategy | `Tracking Timestamps` | 이미 수집한 파일 재수집 방지 |

> **ListFile vs GetFile**: ListFile + FetchFile 조합이 GetFile보다 권장된다. ListFile은 파일 목록만 나열하고(가벼움), FetchFile이 실제 읽기를 수행한다. GetFile은 목록 나열과 읽기를 동시에 수행하여 대용량 디렉토리에서 성능 저하가 발생할 수 있다. 또한 ListFile은 클러스터 환경에서 Primary Node 실행을 보장한다.

### 3-3. FetchFile 프로세서 설정

| 속성 | 값 | 설명 |
|------|-----|------|
| File to Fetch | `${absolute.path}/${filename}` | ListFile이 설정한 Attribute 활용 |
| Completion Strategy | `Move File` | 수집 완료 파일 이동 |
| Move Destination Directory | `/data/settlement/processed` | 처리 완료 디렉토리 |

```bash
# 처리 완료 디렉토리 생성
mkdir -p data/settlement/processed
```

### 3-4. ConvertRecord 프로세서 설정 (CSV → JSON)

NiFi의 Record 기반 처리를 위해 Reader/Writer Controller Service를 먼저 생성한다.

**Controller Service 생성 (NiFi UI → 톱니바퀴 → Controller Services)**:

**1) CSVReader**:
| 속성 | 값 |
|------|-----|
| Schema Access Strategy | `Infer Schema` |
| Date Format | `yyyy-MM-dd` |
| Timestamp Format | `yyyy-MM-dd'T'HH:mm:ssXXX` |
| Treat First Line as Header | `true` |
| CSV Parser | `Apache Commons CSV` |
| Character Set | `UTF-8` |

**2) JsonRecordSetWriter**:
| 속성 | 값 |
|------|-----|
| Schema Write Strategy | `Do Not Write Schema` |
| Output Grouping | `One Line Per Object` |
| Pretty Print JSON | `false` |

**ConvertRecord 프로세서 설정**:
| 속성 | 값 |
|------|-----|
| Record Reader | `CSVReader` |
| Record Writer | `JsonRecordSetWriter` |

### 3-5. SplitRecord 프로세서 설정

CSV 파일 하나에 50건의 레코드가 포함되어 있으므로 개별 레코드로 분리한다.

| 속성 | 값 |
|------|-----|
| Record Reader | `JsonRecordSetReader` (JsonRecordSetWriter와 동일 설정의 Reader 버전) |
| Record Writer | `JsonRecordSetWriter` |
| Records Per Split | `1` |

> **JsonRecordSetReader Controller Service 추가 생성**:
> | 속성 | 값 |
> |------|-----|
> | Schema Access Strategy | `Infer Schema` |

### 3-6. JoltTransformJSON — 정산 CSV 스키마 표준화

정산 CSV의 필드명을 표준 스키마에 맞게 변환한다.

```bash
cat > config/nifi/jolt-spec-file-settlement.json << 'EOF'
[
  {
    "operation": "shift",
    "spec": {
      "settlement_id": "event_id",
      "settlement_type": "event_type",
      "merchant_id": "merchant_id",
      "gross_amount": "amount",
      "fee_amount": "fee_amount",
      "net_amount": "net_amount",
      "currency": "currency",
      "tx_count": "tx_count",
      "settlement_date": "event_timestamp",
      "status": "status",
      "batch_id": "batch_id",
      "created_at": "created_at"
    }
  },
  {
    "operation": "default",
    "spec": {
      "data_source": "settlement-csv",
      "schema_version": "1.0",
      "channel": "BATCH",
      "is_suspicious": false,
      "user_id": null,
      "merchant_name": null,
      "merchant_category": null
    }
  }
]
EOF
```

### 3-7. 정산 CSV 수집 테스트

```bash
# CSV 파일 3개 생성 (30초 간격)
python scripts/csv_settlement_generator.py -n 3 -r 30 -i 30

# NiFi UI에서:
# 1. PG-2: File Ingestion 내 모든 프로세서 시작
# 2. ListFile이 파일 탐지 → FetchFile이 읽기 → ConvertRecord → SplitRecord → Jolt 변환
# 3. Output Port 직전 Connection에서 FlowFile 확인
# 4. /data/settlement/processed/ 디렉토리로 파일 이동 확인

ls -la data/settlement/
ls -la data/settlement/processed/
```

### 3-8. PG-3: DB Ingestion — PostgreSQL 고객 마스터 수집

PostgreSQL의 고객 데이터를 증분(Incremental) 방식으로 수집한다.

**사전 준비 — 고객 마스터 테이블 생성**:

```sql
-- scripts/init-customers.sql
-- PostgreSQL에 고객 마스터 테이블 추가

CREATE TABLE IF NOT EXISTS customers (
    customer_id   SERIAL PRIMARY KEY,
    user_id       INT UNIQUE NOT NULL,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(200),
    phone         VARCHAR(20),
    tier          VARCHAR(20) DEFAULT 'STANDARD',
    status        VARCHAR(20) DEFAULT 'ACTIVE',
    kyc_verified  BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW()
);

-- 샘플 고객 200명 생성
INSERT INTO customers (user_id, name, email, phone, tier, status, kyc_verified, created_at, updated_at)
SELECT
    1000 + gs,
    '고객_' || gs,
    'user' || gs || '@paynex.com',
    '010-' || lpad((random() * 9999)::int::text, 4, '0') || '-' || lpad((random() * 9999)::int::text, 4, '0'),
    CASE
        WHEN random() < 0.1 THEN 'VIP'
        WHEN random() < 0.3 THEN 'GOLD'
        WHEN random() < 0.6 THEN 'SILVER'
        ELSE 'STANDARD'
    END,
    CASE WHEN random() < 0.95 THEN 'ACTIVE' ELSE 'SUSPENDED' END,
    random() < 0.7,
    NOW() - (random() * INTERVAL '365 days'),
    NOW() - (random() * INTERVAL '30 days')
FROM generate_series(1, 200) AS gs
ON CONFLICT (user_id) DO NOTHING;

-- updated_at 자동 갱신 트리거
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER customers_updated
    BEFORE UPDATE ON customers
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();
```

```bash
# 고객 테이블 생성
docker exec -i lab-postgres psql -U pipeline -d pipeline_db < scripts/init-customers.sql

# 데이터 확인
docker exec lab-postgres psql -U pipeline -d pipeline_db \
  -c "SELECT tier, count(*), round(avg(CASE WHEN kyc_verified THEN 1 ELSE 0 END)::numeric * 100, 1) AS kyc_pct
      FROM customers GROUP BY tier ORDER BY count(*) DESC;"
```

### 3-9. NiFi DBCP Controller Service 설정

DB 접속을 위한 DBCP(Database Connection Pooling) 서비스를 NiFi에 등록한다.

**Controller Service 생성: DBCPConnectionPool**:

| 속성 | 값 |
|------|-----|
| Database Connection URL | `jdbc:postgresql://postgres:5432/pipeline_db` |
| Database Driver Class Name | `org.postgresql.Driver` |
| Database Driver Location(s) | `/opt/nifi/custom-config/postgresql-42.7.3.jar` |
| Database User | `pipeline` |
| Password | `pipeline` |
| Max Wait Time | `10 sec` |
| Max Total Connections | `5` |

> **PostgreSQL JDBC 드라이버 준비**:
```bash
# 드라이버 다운로드
curl -L -o config/nifi/postgresql-42.7.3.jar \
  https://jdbc.postgresql.org/download/postgresql-42.7.3.jar
```

### 3-10. QueryDatabaseTable 프로세서 설정

증분 수집(Incremental Fetch) 방식으로 변경된 레코드만 가져온다.

| 속성 | 값 | 설명 |
|------|-----|------|
| Database Connection Pooling Service | `DBCPConnectionPool` | 위에서 생성한 서비스 |
| Database Type | `PostgreSQL` | |
| Table Name | `customers` | |
| Columns to Return | `customer_id, user_id, name, email, phone, tier, status, kyc_verified, created_at, updated_at` | |
| Maximum-value Columns | `updated_at` | 증분 수집 기준 컬럼 |
| Max Rows Per Flow File | `50` | FlowFile당 최대 레코드 수 |
| Output Format | `Avro` | NiFi 기본 출력 포맷 |
| Scheduling — Run Schedule | `60 sec` | 1분마다 변경분 조회 |

> **증분 수집(Incremental Fetch) 원리**: QueryDatabaseTable은 `Maximum-value Columns`에 지정된 컬럼의 마지막 수집 값을 NiFi State에 저장한다. 다음 실행 시 `WHERE updated_at > '마지막값'` 조건이 자동 추가되어 변경분만 가져온다. 전체 테이블을 매번 스캔하지 않으므로 대용량 테이블에서도 효율적이다.

### 3-11. DB 수집 플로우 구성

`PG-3: DB Ingestion` 내부:

```
QueryDatabaseTable
    │
    └── (success) → ConvertRecord (Avro → JSON)
                       │
                       └── (success) → SplitRecord
                                          │
                                          └── (success) → JoltTransformJSON
                                                            │
                                                            └── (success) → Output Port [db-out]
```

**Avro→JSON 변환용 Controller Service 추가**:

**AvroReader**:
| 속성 | 값 |
|------|-----|
| Schema Access Strategy | `Embedded Avro Schema` |

### 3-12. JoltTransformJSON — 고객 마스터 스키마 표준화

```bash
cat > config/nifi/jolt-spec-db-customer.json << 'EOF'
[
  {
    "operation": "shift",
    "spec": {
      "customer_id": "event_id",
      "user_id": "user_id",
      "name": "customer_name",
      "email": "customer_email",
      "phone": "customer_phone",
      "tier": "customer_tier",
      "status": "status",
      "kyc_verified": "kyc_verified",
      "created_at": "created_at",
      "updated_at": "event_timestamp"
    }
  },
  {
    "operation": "default",
    "spec": {
      "event_type": "CUSTOMER_UPDATE",
      "data_source": "customer-db",
      "schema_version": "1.0",
      "channel": "DB_SYNC",
      "currency": null,
      "amount": null,
      "is_suspicious": false,
      "merchant_id": null,
      "merchant_name": null,
      "merchant_category": null
    }
  }
]
EOF
```

### 3-13. DB 수집 증분 추출 검증

```bash
# 1) NiFi에서 PG-3 프로세서 그룹 시작 → 초기 200건 수집

# 2) PostgreSQL에서 고객 데이터 변경 (3건 업데이트)
docker exec lab-postgres psql -U pipeline -d pipeline_db -c "
  UPDATE customers SET tier = 'VIP', status = 'ACTIVE' WHERE user_id = 1001;
  UPDATE customers SET email = 'vip1050@paynex.com' WHERE user_id = 1050;
  UPDATE customers SET kyc_verified = true WHERE user_id = 1100;
"

# 3) 60초 후 NiFi가 변경된 3건만 수집하는지 확인
# → PG-3 Output Port의 FlowFile 수가 3건이어야 함

# 4) 변경 확인
docker exec lab-postgres psql -U pipeline -d pipeline_db \
  -c "SELECT user_id, tier, email, kyc_verified, updated_at
      FROM customers WHERE user_id IN (1001, 1050, 1100);"
```

### 3-14. 세 소스 동시 수집 확인

```bash
# 세 소스 동시 작동 상태에서 FlowFile 흐름 확인
# NiFi UI → PayNex Data Ingestion 그룹 레벨에서:
#   PG-1 Output Port: API 이벤트 (30초마다 20건)
#   PG-2 Output Port: CSV 정산 레코드 (파일 생성 시)
#   PG-3 Output Port: DB 고객 변경분 (60초마다 증분)

# CSV 파일 추가 생성으로 PG-2 트리거
python scripts/csv_settlement_generator.py -n 2 -r 25 -i 10
```

**Day 3 완료 기준**: PG-2 파일 수집 플로우 정상 작동(CSV → JSON 변환, 처리 완료 파일 이동), PG-3 DB 수집 플로우 정상 작동(증분 추출 확인), 세 소스 동시 수집 확인.

---

## Day 4: Kafka 연동 + 스키마 표준화

### 4-1. PG-4: Schema Standardization — 스키마 표준화 + 품질 검증

세 소스에서 변환된 데이터가 표준 스키마를 충족하는지 최종 검증한다.

`PG-4: Schema Standardization` 내부:

```
Input Port [from-api]  ─┐
Input Port [from-file] ─┼──→ MergeContent (선택사항) → ValidateRecord
Input Port [from-db]   ─┘                                   │
                                                             ├── (valid) → UpdateAttribute → Output Port [valid-out]
                                                             └── (invalid) → Output Port [invalid-out]
```

> **설계 판단**: MergeContent는 소량 FlowFile을 묶어 Kafka 전송 효율을 높이는 용도로 선택 사항이다. 초기에는 개별 레코드 단위로 전송하고, 처리량이 늘어나면 배치 전송으로 전환한다.

### 4-2. 표준 스키마 정의

```bash
cat > config/nifi/paynex-standard-schema.avsc << 'EOF'
{
  "type": "record",
  "name": "PayNexStandardEvent",
  "namespace": "com.paynex.events",
  "fields": [
    {"name": "event_id", "type": "string"},
    {"name": "event_type", "type": "string"},
    {"name": "user_id", "type": ["null", "int"], "default": null},
    {"name": "amount", "type": ["null", "double"], "default": null},
    {"name": "currency", "type": ["null", "string"], "default": null},
    {"name": "merchant_id", "type": ["null", "string"], "default": null},
    {"name": "merchant_name", "type": ["null", "string"], "default": null},
    {"name": "merchant_category", "type": ["null", "string"], "default": null},
    {"name": "channel", "type": ["null", "string"], "default": null},
    {"name": "status", "type": "string"},
    {"name": "is_suspicious", "type": "boolean", "default": false},
    {"name": "event_timestamp", "type": "string"},
    {"name": "data_source", "type": "string"},
    {"name": "schema_version", "type": "string", "default": "1.0"}
  ]
}
EOF
```

### 4-3. ValidateRecord 프로세서 설정

| 속성 | 값 |
|------|-----|
| Record Reader | `JsonRecordSetReader` |
| Record Writer | `JsonRecordSetWriter` |
| Schema Access Strategy | `Use 'Schema Text' Property` |
| Schema Text | (위 Avro 스키마 내용 붙여넣기) |
| Allow Extra Fields | `true` |
| Strict Type Checking | `false` |

### 4-4. UpdateAttribute — 소스 태그 및 수집 타임스탬프 추가

| 속성 | 값 | 설명 |
|------|-----|------|
| kafka.topic | `paynex.events.ingested` | 통합 수집 토픽 |
| kafka.key | `${user_id}` | 파티션 키 (Week 2 설계 연계) |
| nifi.ingested.at | `${now():format('yyyy-MM-dd\\'T\\'HH:mm:ss\\'Z\\'', 'UTC')}` | NiFi 수집 시각 |
| nifi.source.group | `${data_source}` | 소스 구분 태그 |

### 4-5. 통합 수집 토픽 생성

> **아키텍처 전환 안내**: Week 2에서는 프로듀서가 거래 유형별로 `paynex.transactions.payment`, `paynex.transactions.transfer`, `paynex.transactions.withdrawal` 토픽에 직접 전송하는 구조였다. Week 3부터는 NiFi가 다양한 소스(API, CSV, DB)의 데이터를 **표준 스키마로 변환한 후 단일 통합 토픽으로 전송**하는 구조로 전환한다. 이후 Week 4에서 Flink가 이 통합 토픽을 소비하여 이벤트 타입별 분기 처리를 수행한다. 즉, **수집 → 표준화(NiFi) → 버퍼(Kafka) → 분기 처리(Flink)** 아키텍처로 발전시키는 것이다.

기존 거래 유형별 토픽과 별도로, NiFi에서 수집한 모든 데이터가 흘러가는 통합 토픽을 생성한다.

```bash
# 통합 수집 토픽
docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka-1:9092 \
  --create --topic paynex.events.ingested \
  --partitions 6 \
  --replication-factor 3 \
  --config min.insync.replicas=2 \
  --config retention.ms=604800000

# DLQ 토픽 (품질 검증 실패 메시지)
docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka-1:9092 \
  --create --topic paynex.events.dlq \
  --partitions 2 \
  --replication-factor 3 \
  --config min.insync.replicas=2 \
  --config retention.ms=2592000000

# 토픽 확인
docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka-1:9092 --list | grep paynex.events
```

### 4-6. PG-5: Kafka Publishing — PublishKafka 연동

`PG-5: Kafka Publishing` 내부:

```
Input Port [valid-data] ──→ PublishKafka_2_6
                                │
                                ├── (success) → LogAttribute [전송성공]
                                └── (failure) → RetryFlowFile → PublishKafka_2_6
                                                    │
                                                    └── (retries exhausted) → PublishKafka_2_6 [DLQ 토픽]

Input Port [invalid-data] ──→ PublishKafka_2_6 [DLQ 토픽]
```

### 4-7. PublishKafka_2_6 프로세서 설정 — 정상 데이터

| 속성 | 값 | 설명 |
|------|-----|------|
| Kafka Brokers | `kafka-1:9092,kafka-2:9092,kafka-3:9092` | 3-브로커 클러스터 |
| Topic Name | `${kafka.topic}` | Attribute에서 동적 결정 |
| Use Transactions | `true` | Exactly-once 보장 |
| Delivery Guarantee | `Guarantee Replicated Delivery` | acks=all 동등 |
| Message Key Field | `${kafka.key}` | user_id 기반 파티션 키 |
| Compression Type | `lz4` | |
| Max Request Size | `1 MB` | |

### 4-8. PublishKafka_2_6 프로세서 설정 — DLQ

| 속성 | 값 | 설명 |
|------|-----|------|
| Kafka Brokers | `kafka-1:9092,kafka-2:9092,kafka-3:9092` | |
| Topic Name | `paynex.events.dlq` | 고정 DLQ 토픽 |
| Delivery Guarantee | `Guarantee Replicated Delivery` | |
| Compression Type | `lz4` | |

### 4-9. 전체 연동 테스트

```bash
# 1) 모든 프로세서 그룹 시작 (NiFi UI)

# 2) 데이터 소스 활성화
# API: 자동 (30초 주기)
# CSV: 파일 생성
python scripts/csv_settlement_generator.py -n 2 -r 30 -i 15
# DB: 레코드 변경
docker exec lab-postgres psql -U pipeline -d pipeline_db -c "
  UPDATE customers SET tier = 'GOLD' WHERE user_id BETWEEN 1010 AND 1015;
"

# 3) Kafka 토픽에 메시지 도착 확인
docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka-1:9092 \
  --topic paynex.events.ingested \
  --from-beginning \
  --max-messages 5 \
  --property print.key=true \
  --property key.separator=" | "

# 4) 소스별 메시지 확인
echo "=== 소스별 메시지 수 ==="
docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka-1:9092 \
  --topic paynex.events.ingested \
  --from-beginning \
  --timeout-ms 10000 2>/dev/null | \
  python3 -c "
import sys, json
from collections import Counter
sources = Counter()
for line in sys.stdin:
    try:
        msg = json.loads(line.strip())
        sources[msg.get('data_source', 'unknown')] += 1
    except: pass
for src, cnt in sources.most_common():
    print(f'  {src}: {cnt}건')
print(f'  합계: {sum(sources.values())}건')
"

# 5) DLQ 메시지 확인 (있는 경우)
docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka-1:9092 \
  --topic paynex.events.dlq \
  --from-beginning \
  --timeout-ms 5000 2>/dev/null | wc -l
```

기대 출력 (소스별 메시지):
```
=== 소스별 메시지 수 ===
  payment-api: 40건
  settlement-csv: 60건
  customer-db: 6건
  합계: 106건
```

### 4-10. 데이터 품질 라우팅 검증

의도적으로 불량 데이터를 주입하여 DLQ 라우팅을 확인한다.

```bash
# 불량 CSV 파일 생성 (필수 필드 누락)
cat > data/settlement/settlement_bad_data.csv << 'EOF'
settlement_id,batch_id,merchant_id,settlement_type,gross_amount,fee_amount,net_amount,currency,tx_count,settlement_date,created_at,status
,,MCH-999,INVALID_TYPE,not_a_number,abc,def,,0,,2026-04-01T00:00:00Z,UNKNOWN
STL-BAD-002,,,,,,,,,,,
EOF

# NiFi가 이 파일을 수집 → ConvertRecord 또는 ValidateRecord에서 실패 → DLQ로 라우팅
# 잠시 후 DLQ 토픽 확인
sleep 30
docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka-1:9092 \
  --topic paynex.events.dlq \
  --from-beginning \
  --timeout-ms 5000
```

**Day 4 완료 기준**: 세 소스 데이터가 표준 스키마로 통합되어 Kafka 토픽(`paynex.events.ingested`)에 도착, DLQ 라우팅 정상 작동, 소스별 메시지 수 확인.

---

## Day 5: Provenance 추적 + 문서화

### 5-1. NiFi Provenance 활용 — 데이터 계보 추적

NiFi의 Provenance는 모든 FlowFile에 대해 생성·변환·전달 이력을 자동 기록한다. 금융감독원 감사 시 "이 데이터가 어디서 왔는가"에 대한 답을 제공한다.

**Provenance 이벤트 유형**:

```
CREATE      — FlowFile 최초 생성 (InvokeHTTP 응답, GetFile 등)
CONTENT_MODIFIED — 내용 변환 (JoltTransformJSON, ConvertRecord 등)
ATTRIBUTES_MODIFIED — 속성 변경 (UpdateAttribute 등)
ROUTE       — 라우팅 결정 (RouteOnAttribute 등)
SEND        — 외부 전송 (PublishKafka 등)
DROP        — FlowFile 삭제
CLONE       — FlowFile 복제
FORK        — FlowFile 분리 (SplitJson, SplitRecord 등)
```

### 5-2. Provenance 조회 실습 (NiFi UI)

**방법 1: 글로벌 Provenance 검색**

1. NiFi UI 우측 상단 **Provenance** 아이콘 (시계 모양) 클릭
2. 검색 필터 설정:
   - Component Name: `PublishKafka_2_6` (Kafka 전송 이벤트만)
   - Event Type: `SEND`
   - 시간 범위: 최근 1시간
3. 검색 결과에서 특정 이벤트 클릭 → **Lineage** 버튼

**방법 2: 개별 FlowFile Provenance 추적**

1. 임의의 Connection 큐 클릭 → **List queue**
2. FlowFile 1개 선택 → **Provenance** 아이콘
3. 해당 FlowFile의 전체 생명주기 이벤트 목록 확인
4. **Lineage** 뷰에서 시각적 데이터 흐름 추적

### 5-3. Provenance 기반 감사 추적 시나리오

```bash
cat > docs/provenance-audit-guide.md << 'EOF'
# PayNex 데이터 계보 추적 가이드 — 감사 대응용

## 감사 시나리오: "결제 이벤트 PAY-00000042의 출처를 증명하시오"

### 추적 절차

1. **Kafka에서 메시지 확인**:
   - 토픽 `paynex.events.ingested`에서 해당 event_id 검색
   - 메시지의 `data_source` 필드 확인 → "payment-api"

2. **NiFi Provenance에서 역추적**:
   - Provenance 검색: FlowFile Attribute `event_id` = "PAY-00000042"
   - SEND 이벤트 → 언제 Kafka로 전송되었는지 확인
   - CONTENT_MODIFIED 이벤트 → 어떤 변환을 거쳤는지 확인
   - CREATE 이벤트 → 원본 API 응답 시각·URL 확인

3. **증빙 자료 구성**:
   - Provenance Lineage 스크린샷 (시각적 흐름도)
   - 각 이벤트의 타임스탬프·프로세서명·입출력 내용
   - 원본 API 응답 원문 (CREATE 이벤트의 Content 확인)

### 보존 설정

| 항목 | 권장 설정 | 근거 |
|------|----------|------|
| Provenance 보존 기간 | 30일 | nifi.provenance.repository.max.storage.time |
| Provenance 저장 용량 | 10GB | nifi.provenance.repository.max.storage.size |
| 감사 로그 외부 보관 | 5년 | 금융 규정 준수 (별도 저장소 이관 필요) |

### NiFi Provenance 설정 (nifi.properties)

```properties
nifi.provenance.repository.implementation=org.apache.nifi.provenance.WriteAheadProvenanceRepository
nifi.provenance.repository.max.storage.time=30 days
nifi.provenance.repository.max.storage.size=10 GB
nifi.provenance.repository.rollover.time=10 mins
nifi.provenance.repository.rollover.size=100 MB
nifi.provenance.repository.indexed.fields=EventType,FlowFileUUID,Filename,ProcessorID,Relationship
nifi.provenance.repository.indexed.attributes=event_id,user_id,data_source,event_type
```

EOF
```

### 5-4. NiFi Bulletin 및 모니터링 설정

NiFi에서 운영 중 발생하는 경고·오류를 추적하는 모니터링 체계를 설정한다.

```bash
cat > docs/nifi-monitoring-guide.md << 'EOF'
# PayNex NiFi 모니터링 가이드

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

EOF
```

### 5-5. 전체 파이프라인 종합 검증 스크립트

```bash
cat > scripts/verify_nifi_pipeline.sh << 'SCRIPT'
#!/bin/bash
# NiFi 다중 소스 수집 파이프라인 종합 검증

echo "============================================"
echo " PayNex NiFi 파이프라인 종합 검증"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"
echo ""

PASS=0
FAIL=0

check() {
  local name=$1
  local cmd=$2
  printf "  %-35s : " "$name"
  if eval "$cmd" > /dev/null 2>&1; then
    echo "✅ OK"
    ((PASS++))
  else
    echo "❌ FAIL"
    ((FAIL++))
  fi
}

echo "[1. 인프라 서비스]"
check "NiFi 웹 UI" "curl -sf http://localhost:8080/nifi/"
check "결제 API 시뮬레이터" "curl -sf http://localhost:5050/health"
check "PostgreSQL (고객 테이블)" "docker exec lab-postgres psql -U pipeline -d pipeline_db -c 'SELECT count(*) FROM customers;'"
check "Kafka 클러스터" "docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka-1:9092 --list"

echo ""
echo "[2. Kafka 토픽]"
check "paynex.events.ingested 토픽" "docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka-1:9092 --describe --topic paynex.events.ingested"
check "paynex.events.dlq 토픽" "docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka-1:9092 --describe --topic paynex.events.dlq"

echo ""
echo "[3. 데이터 흐름 검증]"
# API → Kafka 메시지 존재 확인
check "API 소스 메시지" "docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka-1:9092 --topic paynex.events.ingested --from-beginning --timeout-ms 5000 2>/dev/null | grep payment-api"
# CSV → Kafka 메시지 존재 확인
check "CSV 소스 메시지" "docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka-1:9092 --topic paynex.events.ingested --from-beginning --timeout-ms 5000 2>/dev/null | grep settlement-csv"
# DB → Kafka 메시지 존재 확인
check "DB 소스 메시지" "docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka-1:9092 --topic paynex.events.ingested --from-beginning --timeout-ms 5000 2>/dev/null | grep customer-db"

echo ""
echo "[4. 소스별 메시지 통계]"
docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka-1:9092 \
  --topic paynex.events.ingested \
  --from-beginning \
  --timeout-ms 10000 2>/dev/null | \
python3 -c "
import sys, json
from collections import Counter
sources = Counter()
for line in sys.stdin:
    try:
        msg = json.loads(line.strip())
        sources[msg.get('data_source', 'unknown')] += 1
    except: pass
for src, cnt in sorted(sources.items()):
    print(f'  {src}: {cnt}건')
print(f'  합계: {sum(sources.values())}건')
" 2>/dev/null

echo ""
echo "============================================"
echo " 결과: ✅ ${PASS} 통과 / ❌ ${FAIL} 실패"
echo "============================================"
SCRIPT

chmod +x scripts/verify_nifi_pipeline.sh
bash scripts/verify_nifi_pipeline.sh
```

기대 출력:

```
============================================
 PayNex NiFi 파이프라인 종합 검증
 2026-04-05 17:00:00
============================================

[1. 인프라 서비스]
  NiFi 웹 UI                        : ✅ OK
  결제 API 시뮬레이터                  : ✅ OK
  PostgreSQL (고객 테이블)             : ✅ OK
  Kafka 클러스터                      : ✅ OK

[2. Kafka 토픽]
  paynex.events.ingested 토픽        : ✅ OK
  paynex.events.dlq 토픽             : ✅ OK

[3. 데이터 흐름 검증]
  API 소스 메시지                     : ✅ OK
  CSV 소스 메시지                     : ✅ OK
  DB 소스 메시지                      : ✅ OK

[4. 소스별 메시지 통계]
  customer-db: 206건
  payment-api: 120건
  settlement-csv: 90건
  합계: 416건

============================================
 결과: ✅ 9 통과 / ❌ 0 실패
============================================
```

### 5-6. 데이터 흐름 아키텍처 문서 작성

```bash
cat > docs/nifi-architecture.md << 'EOF'
# PayNex NiFi 데이터 수집 아키텍처

## 아키텍처 개요

```
  [결제 API]         [정산 CSV]         [고객 DB]
  (실시간 JSON)      (주기적 파일)       (증분 변경)
       │                  │                  │
       ▼                  ▼                  ▼
  ┌─────────┐      ┌──────────┐      ┌──────────┐
  │ PG-1    │      │ PG-2     │      │ PG-3     │
  │ API     │      │ File     │      │ DB       │
  │ Ingest  │      │ Ingest   │      │ Ingest   │
  └────┬────┘      └────┬─────┘      └────┬─────┘
       │                │                  │
       └────────────────┼──────────────────┘
                        ▼
                 ┌─────────────┐
                 │ PG-4        │
                 │ Schema      │
                 │ Standard.   │
                 └──────┬──────┘
                   ┌────┴────┐
                   ▼         ▼
              [정상]      [불량]
                   │         │
                   ▼         ▼
              ┌────────┐ ┌──────┐
              │ PG-5   │ │ DLQ  │
              │ Kafka  │ │ 토픽  │
              │ Pub    │ │      │
              └────────┘ └──────┘
                   │
                   ▼
         paynex.events.ingested
```

## 프로세서 그룹별 상세

### PG-1: API Ingestion
- **소스**: 결제 API (`http://payment-api:5050/api/v1/payments/recent`)
- **주기**: 30초
- **프로세서 체인**: InvokeHTTP → SplitJson → EvaluateJsonPath → JoltTransformJSON
- **처리량**: ~40건/분

### PG-2: File Ingestion
- **소스**: 정산 CSV 파일 (`/data/settlement/settlement_*.csv`)
- **주기**: 파일 감지 시 즉시
- **프로세서 체인**: ListFile → FetchFile → ConvertRecord(CSV→JSON) → SplitRecord → JoltTransformJSON
- **처리 완료 파일**: `/data/settlement/processed/`로 이동

### PG-3: DB Ingestion
- **소스**: PostgreSQL `customers` 테이블
- **주기**: 60초 (증분 추출)
- **프로세서 체인**: QueryDatabaseTable → ConvertRecord(Avro→JSON) → SplitRecord → JoltTransformJSON
- **증분 기준**: `updated_at` 컬럼

### PG-4: Schema Standardization
- **역할**: 세 소스 데이터의 스키마 표준 준수 검증
- **정상**: PG-5로 전달
- **불량**: DLQ 토픽으로 전달

### PG-5: Kafka Publishing
- **대상 토픽**: `paynex.events.ingested` (RF=3, min.ISR=2)
- **DLQ 토픽**: `paynex.events.dlq`
- **파티션 키**: `user_id`
- **전송 보장**: Exactly-once (트랜잭션 사용)

## 표준 스키마

| 필드 | 타입 | 필수 | API | CSV | DB |
|------|------|------|-----|-----|----|
| event_id | string | ✅ | event_id | settlement_id | customer_id |
| event_type | string | ✅ | event_type | settlement_type | "CUSTOMER_UPDATE" |
| user_id | int | - | user_id | null | user_id |
| amount | double | - | amount | gross_amount | null |
| currency | string | - | currency | currency | null |
| status | string | ✅ | status | status | status |
| data_source | string | ✅ | "payment-api" | "settlement-csv" | "customer-db" |
| event_timestamp | string | ✅ | timestamp | settlement_date | updated_at |
| schema_version | string | ✅ | "1.0" | "1.0" | "1.0" |

## 운영 포트 맵

| 포트 | 서비스 |
|------|--------|
| 8080 | NiFi 웹 UI |
| 5050 | 결제 API 시뮬레이터 |
| 5432 | PostgreSQL |
| 29092~29094 | Kafka 브로커 1~3 |

EOF
```

### 5-7. Git 커밋

```bash
git add .
git commit -m "Week 3: NiFi 다중 소스 수집 — API·CSV·DB → 스키마 표준화 → Kafka 연동"
```

**Day 5 완료 기준**: Provenance 기반 데이터 계보 추적 실습 완료, 모니터링 가이드 작성, 종합 검증 스크립트 9개 항목 전체 통과, 아키텍처 문서 작성, Git 커밋.

---

## Week 3 산출물 체크리스트

| # | 산출물 | 완료 |
|---|--------|------|
| 1 | docs/nifi-concepts.md (NiFi 핵심 개념 정리) | ☐ |
| 2 | config/nifi/process-group-design.md (프로세서 그룹 설계) | ☐ |
| 3 | scripts/api_payment_simulator.py (결제 API 시뮬레이터) | ☐ |
| 4 | scripts/csv_settlement_generator.py (정산 CSV 생성기) | ☐ |
| 5 | scripts/init-customers.sql (고객 마스터 테이블) | ☐ |
| 6 | config/nifi/jolt-spec-api-payment.json (API Jolt 스펙) | ☐ |
| 7 | config/nifi/jolt-spec-file-settlement.json (CSV Jolt 스펙) | ☐ |
| 8 | config/nifi/jolt-spec-db-customer.json (DB Jolt 스펙) | ☐ |
| 9 | config/nifi/paynex-standard-schema.avsc (표준 Avro 스키마) | ☐ |
| 10 | scripts/verify_nifi_pipeline.sh (종합 검증 스크립트) | ☐ |
| 11 | docs/provenance-audit-guide.md (Provenance 감사 추적 가이드) | ☐ |
| 12 | docs/nifi-monitoring-guide.md (NiFi 모니터링 가이드) | ☐ |
| 13 | docs/nifi-architecture.md (데이터 흐름 아키텍처 문서) | ☐ |
| 14 | docker-compose.yml 업데이트 (payment-api, NiFi 볼륨) | ☐ |
| 15 | NiFi 플로우 (5개 프로세서 그룹 구성 완료) | ☐ |
| 16 | Git 커밋 | ☐ |

## 핵심 개념 요약

| 개념 | 요약 | 실습에서 확인한 것 |
|------|------|------------------|
| FlowFile | Content + Attributes = NiFi 데이터 단위 | 모든 프로세서에서 FlowFile 흐름 관찰 |
| Process Group | 논리적 플로우 묶음으로 복잡도 관리 | 5개 그룹(API·File·DB·표준화·Kafka) 구성 |
| InvokeHTTP | REST API 주기적 polling 수집 | 30초 주기 결제 API 수집 |
| ListFile + FetchFile | 파일 시스템 감시·수집 (GetFile보다 권장) | CSV 파일 탐지·수집·완료 이동 |
| QueryDatabaseTable | 증분 추출(Incremental Fetch) | updated_at 기준 변경분만 수집 |
| JoltTransformJSON | JSON 스키마 변환 (이기종 소스 통합) | 세 소스 → 단일 표준 스키마 변환 |
| ConvertRecord | 포맷 변환 (CSV→JSON, Avro→JSON) | Record Reader/Writer 기반 변환 |
| ValidateRecord | 스키마 준수 검증 + 불량 데이터 분리 | 정상/불량 라우팅 |
| PublishKafka | NiFi → Kafka 전송 (Exactly-once) | 트랜잭션 기반 전송 |
| Provenance | 데이터 계보 추적 (감사 대응) | FlowFile 생성→변환→전송 이력 조회 |
| Back-Pressure | 큐 과부하 방지 (상류 자동 정지) | Connection 임계값 설정 |

## Week 4 예고

Week 4에서는 Flink를 활용한 실시간 스트림 처리를 구축한다. 이번 주에 NiFi가 Kafka에 전달한 `paynex.events.ingested` 토픽의 데이터를 Flink가 소비하여 윈도우 집계(Window Aggregation), Watermark 기반 이벤트 타임 처리, 실시간 이상거래 탐지 로직을 구현한다. NiFi(수집) → Kafka(버퍼) → Flink(처리)로 이어지는 실시간 파이프라인의 핵심 구간이 완성된다.
