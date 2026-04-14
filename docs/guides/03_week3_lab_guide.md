# Week 3: 수집 — NiFi 다중 소스 데이터 수집

**기간**: 5일 (월~금, 풀타임 40시간)
**주제**: 다중 소스 수집 파이프라인, NiFi 프로세서 그룹, Provenance 추적, Kafka 연동
**산출물**: NiFi 다중 소스 수집 플로우 + Kafka 연동 파이프라인 + Provenance 모니터링 가이드 + 데이터 흐름 아키텍처 문서
**전제 조건**: Week 1·2 환경 정상 기동 (`bash scripts/foundation/healthcheck-all.sh` 전체 통과), Kafka 3-브로커 클러스터 가동 중

---

## 수행 시나리오

### 배경 설정

Nexus Pay CTO가 Kafka 아키텍처 검증 결과에 만족했다. 이제 실질적인 데이터 수집 과제를 제시한다.

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
cat > docs/nifi/nifi-concepts.md << 'EOF'
# NiFi 핵심 개념 정리 — 컨설팅 설명 자료

## FlowFile

NiFi에서 처리되는 데이터의 최소 단위. Content(실제 데이터)와 Attributes(메타데이터)로 구성된다.
금융 데이터 관점에서 하나의 FlowFile은 거래 1건, CSV 파일 1개, API 응답 1회에 대응한다.

## Processor

FlowFile을 생성·변환·전달하는 작업 단위. NiFi는 300개 이상의 내장 프로세서를 제공한다.
Nexus Pay에서 사용할 핵심 프로세서:
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

### 1-2. Nexus Pay 수집 아키텍처 설계

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Nexus Pay NiFi 수집 아키텍처                         │
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
# Nexus Pay NiFi 프로세서 그룹 설계

## 최상위 그룹: Nexus Pay Data Ingestion

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
- Input Port → PublishKafka
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
# scripts/nifi/api_payment_simulator.py
"""
Nexus Pay 결제 API 시뮬레이터
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
    print("Nexus Pay 결제 API 시뮬레이터 시작 — http://0.0.0.0:5050")
    app.run(host="0.0.0.0", port=5050, debug=False)
```

### 1-5. API 시뮬레이터를 Docker Compose에 추가

docker-compose.yml의 services 섹션에 추가:

```yaml
  # ──────────────────────────────────────
  # Nexus Pay 결제 API 시뮬레이터
  # ──────────────────────────────────────
  payment-api:
    image: python:3.12-slim
    container_name: lab-payment-api
    working_dir: /app
    command: >
      bash -lc "
        pip install --no-cache-dir flask &&
        python api_payment_simulator.py
      "
    volumes:
      - ./scripts/nifi:/app
    ports:
      - "5050:5050"
    networks:
      - pipeline-net
    healthcheck:
      test:
        [
          "CMD",
          "python",
          "-c",
          "import urllib.request; urllib.request.urlopen('http://localhost:5050/health', timeout=3)"
        ]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 20s
```

### 1-6. 정산 CSV 생성기 구현

레거시 정산 시스템이 매시간 CSV 파일을 생성하는 상황을 시뮬레이션한다.

이 생성기는 통화별 현실성을 반영해 `KRW`와 `JPY`는 정수 금액, `USD`는 소수 둘째 자리 금액으로 만들고, 수수료는 총액의 일정 비율(0.3%~3%)로 계산한다.
생성된 CSV를 확인할 때는 `net_amount = gross_amount - fee_amount` 관계가 유지되는지, `USD` 금액이 수만 달러 수준 이하의 현실적인 범위인지, 상태값이 `COMPLETED`·`PENDING`·`FAILED`로 다양하게 섞여 있는지를 함께 본다.

```python
# scripts/nifi/csv_settlement_generator.py
"""
Nexus Pay 정산 CSV 생성기
- /data/settlement/ 디렉토리에 주기적으로 CSV 파일 생성
- 레거시 시스템이 매시간 정산 파일을 떨구는 시나리오 시뮬레이션
"""

import csv
import os
import random
import time
import argparse
from datetime import datetime, timezone, timedelta

OUTPUT_DIR = "./data/nifi/settlement"  # pipeline-lab/ 디렉토리에서 실행 기준 (Docker 볼륨 마운트 경로와 일치)

SETTLEMENT_TYPES = ["DAILY_CLOSE", "MERCHANT_PAYOUT", "FEE_CALCULATION", "REFUND_BATCH"]
CURRENCY_WEIGHTS = [("KRW", 80), ("USD", 15), ("JPY", 5)]
GROSS_AMOUNT_RANGES = {
    "KRW": (100_000, 50_000_000),
    "USD": (100, 50_000),
    "JPY": (10_000, 5_000_000),
}
FEE_RATE_RANGE = (0.003, 0.03)


def generate_settlement_row(seq: int, batch_id: str, batch_token: str) -> dict:
    """정산 레코드 1건 생성"""
    currency = random.choices(
        [item[0] for item in CURRENCY_WEIGHTS],
        weights=[item[1] for item in CURRENCY_WEIGHTS],
        k=1,
    )[0]

    gross_lo, gross_hi = GROSS_AMOUNT_RANGES[currency]
    gross_raw = random.uniform(gross_lo, gross_hi)
    if currency in {"KRW", "JPY"}:
        gross_amount = int(round(gross_raw))
    else:
        gross_amount = round(gross_raw, 2)

    fee_rate = random.uniform(*FEE_RATE_RANGE)
    fee_raw = gross_amount * fee_rate
    if currency in {"KRW", "JPY"}:
        fee_amount = int(round(fee_raw))
        net_amount = gross_amount - fee_amount
    else:
        fee_amount = round(fee_raw, 2)
        net_amount = round(gross_amount - fee_amount, 2)

    return {
        # 파일마다 다시 1번부터 시작해도 겹치지 않도록 배치 고유 토큰을 포함한다.
        "settlement_id": f"STL-{batch_token}-{seq:06d}",
        "batch_id": batch_id,
        # 시작값과 끝값 사이의 정수 하나를 랜덤 선택
        "merchant_id": f"MCH-{random.randint(100, 599)}",
        # 목록 안의 값 중 하나를 랜덤 선택
        "settlement_type": random.choice(SETTLEMENT_TYPES),
        "gross_amount": gross_amount,
        "fee_amount": fee_amount,
        "net_amount": net_amount,
        "currency": currency,
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

    batch_token = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    batch_id = f"BATCH-{batch_token}"
    filename = f"settlement_{batch_token}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    fieldnames = [
        "settlement_id", "batch_id", "merchant_id", "settlement_type",
        "gross_amount", "fee_amount", "net_amount", "currency",
        "tx_count", "settlement_date", "created_at", "status",
    ]

    rows = []
    for i in range(1, row_count + 1):
        row = generate_settlement_row(i, batch_id, batch_token)
        rows.append(row)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  ✅ 생성: {filepath} ({row_count}건, batch={batch_id})")
    return filepath


def main():
    parser = argparse.ArgumentParser(description="Nexus Pay 정산 CSV 생성기")
    parser.add_argument("-n", "--files", type=int, default=3, help="생성할 파일 수")
    parser.add_argument("-r", "--rows", type=int, default=50, help="파일당 레코드 수")
    parser.add_argument("-i", "--interval", type=int, default=30, help="파일 생성 간격(초)")
    args = parser.parse_args()

    print(f"Nexus Pay 정산 CSV 생성기 시작")
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

### 1-7. NiFi 2.9.0 새 학습 환경 준비

Week 3 NiFi 실습은 기존 1.x 볼륨을 재사용하지 않고 `apache/nifi:2.9.0` 기준의 **새 환경**으로 시작한다. NiFi는 UI에서 만든 플로우와 state, provenance 정보를 내부 저장소에 유지하므로 Day 1 환경 기동 전에 영속 볼륨을 먼저 붙이는 것이 좋다. 다만 예전 1.x에서 만든 `conf` 볼륨을 그대로 들고 오면 `flow.json.gz`, `users.xml`, `authorizations.xml`, `nifi.properties` 형식 차이로 부팅이 실패할 수 있다.

따라서 NiFi 학습을 2.9.0에 맞춰 다시 시작할 때는 **기존 NiFi named volume을 먼저 삭제**한다.

```bash
# NiFi 컨테이너 중지
docker compose stop nifi

# NiFi 컨테이너 삭제
docker compose rm -f nifi

# 기존 NiFi named volume 삭제
docker volume rm \
  pipeline-lab_nifi-conf \
  pipeline-lab_nifi-state \
  pipeline-lab_nifi-database-repo \
  pipeline-lab_nifi-flowfile-repo \
  pipeline-lab_nifi-content-repo \
  pipeline-lab_nifi-provenance-repo \
  pipeline-lab_nifi-logs
```

> **NiFi 2.9.0 운영 메모**:
> - 기본 접속 방식은 `HTTPS:8443`
> - self-signed 인증서를 사용하므로 최초 브라우저 접속 시 예외 허용 필요
> - 로그인은 `.env`의 `NIFI_USERNAME / NIFI_PASSWORD`
> - 단일 사용자 비밀번호는 짧으면 적용되지 않을 수 있으므로 기본 예시는 `1q2w3e4r5t1!`
> - 기존 1.x 캔버스는 가져오지 않고, 2.9.0 UI 기준으로 PG-1부터 다시 구성

`docker-compose.yml` 상단 `volumes:`에 다음을 추가한다.

```yaml
volumes:
  postgres-data:
  redis-data:
  nifi-conf:
  nifi-state:
  nifi-database-repo:
  nifi-flowfile-repo:
  nifi-content-repo:
  nifi-provenance-repo:
  nifi-logs:
```

`nifi` 서비스에는 아래 마운트를 사용한다.

```yaml
  nifi:
    volumes:
      - nifi-conf:/opt/nifi/nifi-current/conf
      - nifi-state:/opt/nifi/nifi-current/state
      - nifi-database-repo:/opt/nifi/nifi-current/database_repository
      - nifi-flowfile-repo:/opt/nifi/nifi-current/flowfile_repository
      - nifi-content-repo:/opt/nifi/nifi-current/content_repository
      - nifi-provenance-repo:/opt/nifi/nifi-current/provenance_repository
      - nifi-logs:/opt/nifi/nifi-current/logs
      - ./data/nifi/settlement:/data/settlement
      - ./config/nifi:/opt/nifi/custom-config
```

적용 시점:
- Day 1의 NiFi UI 작업 시작 전
- 호스트 경로는 `data/nifi/settlement/processed`까지 미리 생성
- 기존 1.x 플로우는 백업 대상일 뿐, 새 학습 환경에는 재사용하지 않음

### 1-8. 환경 기동 및 기본 검증

```bash
# API 시뮬레이터 기동
docker compose up -d payment-api

# API 정상 응답 확인
curl -s "http://localhost:5050/api/v1/payments/recent?count=3" | jq

# 정산 CSV 디렉토리 생성 (NiFi 컨테이너에서 접근 가능하도록 볼륨 마운트)
mkdir -p data/nifi/settlement

# CSV 파일 1개 사전 생성 (테스트용)
python scripts/nifi/csv_settlement_generator.py -n 1 -r 20

# 생성된 파일 확인
head -5 data/nifi/settlement/settlement_*.csv

# NiFi 웹 UI 접속 확인
curl -skf https://localhost:8443/nifi/ > /dev/null && echo "NiFi OK" || echo "NiFi NOT READY"
```

> **Windows Git Bash에서 `jq` 설치 및 PATH 반영 방법**:
>
> 1. `winget install jqlang.jq` 로 설치한다.
> 2. PowerShell에서 실제 설치 위치를 확인한다.
>
> ```powershell
> Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet\Packages" -Recurse -Filter jq.exe -ErrorAction SilentlyContinue
> ```
>
> 예시 설치 위치:
>
> ```text
> C:\Users\<사용자명>\AppData\Local\Microsoft\WinGet\Packages\jqlang.jq_Microsoft.Winget.Source_8wekyb3d8bbwe\jq.exe
> ```
>
> 3. Git Bash 현재 세션에서만 임시 반영하려면 아래처럼 `PATH`를 추가한다.
>
> ```bash
> export PATH="$PATH:/c/Users/<사용자명>/AppData/Local/Microsoft/WinGet/Packages/jqlang.jq_Microsoft.Winget.Source_8wekyb3d8bbwe"
> jq --version
> ```
>
> 4. 이후 새 Git Bash 세션에서도 계속 사용하려면 `~/.bashrc`에 같은 경로를 추가한다.
>
> ```bash
> echo 'export PATH="$PATH:/c/Users/<사용자명>/AppData/Local/Microsoft/WinGet/Packages/jqlang.jq_Microsoft.Winget.Source_8wekyb3d8bbwe"' >> ~/.bashrc
> source ~/.bashrc
> jq --version
> ```
>
> `jq`를 바로 사용할 수 없는 환경에서는 아래 Python 대체 명령을 사용한다.
>
> ```bash
> curl -s "http://localhost:5050/api/v1/payments/recent?count=3" | python -c "import sys, json; print(json.dumps(json.load(sys.stdin), ensure_ascii=False, indent=2))"
> ```

> **NiFi 볼륨 마운트 추가**: docker-compose.yml의 nifi 서비스에 정산 CSV 디렉토리와 API 네트워크 접근을 위한 볼륨을 추가한다.

```yaml
  nifi:
    image: apache/nifi:2.9.0
    container_name: lab-nifi
    environment:
      NIFI_WEB_HTTPS_PORT: 8443
      NIFI_WEB_PROXY_HOST: localhost:8443
      SINGLE_USER_CREDENTIALS_USERNAME: ${NIFI_USERNAME}
      SINGLE_USER_CREDENTIALS_PASSWORD: ${NIFI_PASSWORD}
    ports:
      - "8443:8443"
    volumes:
      - nifi-conf:/opt/nifi/nifi-current/conf
      - nifi-state:/opt/nifi/nifi-current/state
      - nifi-database-repo:/opt/nifi/nifi-current/database_repository
      - nifi-flowfile-repo:/opt/nifi/nifi-current/flowfile_repository
      - nifi-content-repo:/opt/nifi/nifi-current/content_repository
      - nifi-provenance-repo:/opt/nifi/nifi-current/provenance_repository
      - nifi-logs:/opt/nifi/nifi-current/logs
      - ./data/nifi/settlement:/data/settlement    # 정산 CSV 디렉토리
      - ./config/nifi:/opt/nifi/custom-config  # 커스텀 설정
    networks:
      - pipeline-net
    healthcheck:
      test: ["CMD-SHELL", "curl -skf https://localhost:8443/nifi/ || exit 1"]
      interval: 20s
      timeout: 10s
      retries: 15
      start_period: 60s
```

**Day 1 완료 기준**: NiFi 핵심 개념 문서 작성, 프로세서 그룹 설계 문서 작성, 결제 API 시뮬레이터 정상 동작, 정산 CSV 생성기 정상 동작, NiFi 웹 UI 접속 확인.

**Day 1 진행 결과 정리**:
- `docs/nifi/nifi-concepts.md` 작성 완료
- `config/nifi/process-group-design.md` 작성 완료
- `scripts/nifi/api_payment_simulator.py` 정상 동작 확인
  - 검증 예시: `curl -s "http://localhost:5050/api/v1/payments/recent?count=3" | jq`
- `scripts/nifi/csv_settlement_generator.py` 정상 동작 확인
  - 검증 예시: `data/nifi/settlement/settlement_20260408135947012345.csv` 형태의 파일 생성
- NiFi 웹 UI 접근 확인
  - 검증 예시: `curl -skf https://localhost:8443/nifi/ > /dev/null && echo "NiFi OK" || echo "NiFi NOT READY"`

위 항목 기준으로 Day 1은 완료로 판단한다. 다만 실제 NiFi 캔버스에서 5개 프로세서 그룹을 모두 구성하는 작업은 Day 2 이후에 계속 진행한다.

---

## Day 2: REST API 수집 파이프라인

### 2-0. NiFi 2.9.0 참고 기준

이번 Day 2는 NiFi 2.9.0 기준으로 다음 공식 문서를 함께 본다.

- User Guide: Processor 설정, Scheduling 탭, Connection/Back Pressure, Bulletin Board, Provenance 사용법
- Administrator's Guide: HTTPS 기본 포트, 보안 로그인, 로그 파일, 리포지터리 디렉터리 운영 포인트

실습 중 바로 참고할 공식 링크:

- `https://nifi.apache.org/docs/nifi-docs/html/user-guide.html`
- `https://nifi.apache.org/nifi-docs/administration-guide.html`
- `https://nifi.apache.org/components/org.apache.nifi.processors.standard.InvokeHTTP/`
- `https://nifi.apache.org/components/org.apache.nifi.processors.standard.SplitJson/`

### 2-1. 사전 확인

NiFi 2.9.0 운영 전제는 다음과 같다.

- 접속 URL: `https://localhost:8443/nifi`
- 로그인 방식: 현재 실습 환경은 single-user credentials 기반
- Docker 이미지: `apache/nifi:2.9.0`
- 실습 API 엔드포인트: `http://payment-api:5050/api/v1/payments/recent?count=20`

관리자 매뉴얼 기준으로 NiFi는 HTTPS `8443` 포트를 기본으로 사용하며, 저장소 디렉터리(`content_repository`, `flowfile_repository`, `provenance_repository`, `logs`, `state`)의 상태를 안정적으로 유지해야 한다. 실습 환경에서는 `docker-compose.yml`과 NiFi 볼륨이 이미 이 역할을 맡고 있다.

로그인과 TLS 준비에 대해서는 다음 운영 기준을 함께 적용한다.

- 회사 PC에서 `mkcert -install`로 로컬 CA를 먼저 만든다.
- `localhost`, `127.0.0.1`, `::1`용 인증서를 `config/nifi/tls`에 직접 생성한다.
- `config/nifi/start-nifi-2.9.0.sh`는 `nifi.security.needClientAuth=false`를 강제로 반영하므로, 정상 기동 시 브라우저가 클라이언트 인증서를 요구하지 않아야 한다.
- `.env`의 `NIFI_USERNAME`, `NIFI_PASSWORD`는 Git Bash의 현재 셸 환경변수보다 우선하지 않으므로, 필요 시 `unset NIFI_USERNAME`, `unset NIFI_PASSWORD` 후 재기동한다.

실습 전 빠른 점검 명령:

```bash
docker compose config | grep -A3 'SINGLE_USER_CREDENTIALS'
docker exec lab-nifi sh -lc 'env | grep "^SINGLE_USER_CREDENTIALS_"'
docker exec lab-nifi sh -lc "grep '^nifi.security.needClientAuth=' /opt/nifi/nifi-current/conf/nifi.properties"
```

정상 기대값:

```bash
SINGLE_USER_CREDENTIALS_USERNAME=admin
SINGLE_USER_CREDENTIALS_PASSWORD=1q2w3e4r5t1!
nifi.security.needClientAuth=false
```

### 2-2. NiFi 프로세서 그룹 생성 (UI 작업)

NiFi 웹 UI에서 다음 순서로 진행한다. `mkcert` CA와 `localhost` 인증서가 올바르게 설치되어 있다면 `https://localhost:8443/nifi` 접속 시 일반적인 self-signed 경고 없이 바로 접근할 수 있고, `.env`의 `NIFI_USERNAME / NIFI_PASSWORD` 값으로 로그인한다.

1. 캔버스 상단의 **Process Group** 아이콘을 드래그하여 최상위 그룹 `Nexus Pay Data Ingestion` 생성
2. 그룹 내부로 진입하여 하위 프로세서 그룹 생성
3. 오늘은 `PG-1: API Ingestion`만 실제로 구성
4. 아래 그룹은 이름만 먼저 만들어 둔다

- `PG-2: File Ingestion` (Day 3에서 구성)
- `PG-3: DB Ingestion` (Day 3에서 구성)
- `PG-4: Schema Standardization` (Day 4에서 구성)
- `PG-5: Kafka Publishing` (Day 4에서 구성)

### 2-2A. Day 2를 시작하기 전에 캔버스 목표를 먼저 고정

오늘 Day 2에서 실제로 완성할 범위는 `PG-1: API Ingestion` 하나다. 즉, REST API에서 응답을 받아 개별 이벤트로 쪼개고, 핵심 필드를 attribute로 추출하고, 표준 JSON 형태로 정리한 뒤 `api-out`으로 넘기는 흐름까지만 만든다.

완성 목표:

1. `InvokeHTTP`가 30초마다 결제 API를 호출한다.
2. `SplitJson`이 `data` 배열을 건별 FlowFile로 분리한다.
3. `EvaluateJsonPath`가 `event_id`, `user_id`, `timestamp` 같은 필드를 attribute로 만든다.
4. `UpdateAttribute`가 `ingested_at`, `source_system`을 추가한다.
5. `JoltTransformJSON`이 Nexus Pay 표준 이벤트 형태로 바꾼다.
6. 최종 결과가 `Output Port [api-out]`까지 도달한다.

UI 작업을 시작하기 전에 머릿속에서 아래 한 줄 흐름을 고정해 두면 실습이 훨씬 덜 헷갈린다.

```text
결제 API 호출 -> 응답 수신 -> data 배열 분리 -> 필드 추출 -> 메타데이터 추가 -> 표준 JSON 변환 -> api-out 전달
```

### 2-3. PG-1: API Ingestion 플로우 구성

`PG-1: API Ingestion` 내부에 다음 프로세서를 배치하고 연결한다.

```text
InvokeHTTP
    │
    ├── (response) → SplitJson
    │                    │
    │                    └── (split) → EvaluateJsonPath
    │                                      │
    │                                      ├── (matched) → UpdateAttribute
    │                                      │                    │
    │                                      │                    └── (success) → JoltTransformJSON
    │                                      │                                          │
    │                                      │                                          ├── (success) → Output Port [api-out]
    │                                      │                                          └── (failure) → LogAttribute [변환실패]
    │                                      └── (failure) → LogAttribute [JSON경로실패]
    │
    ├── (retry / failure / no retry) → LogAttribute [API호출실패]
    └── (original) → auto-terminate
```

NiFi 2.9.0의 `InvokeHTTP`는 성공 응답 본문을 `response` relationship으로 내보내므로, 후속 `SplitJson`은 `response`에서 이어야 한다. `original`은 요청 FlowFile 경로이므로 이번 polling 시나리오에서는 종료 처리한다.

### 2-3A. 프로세서를 실제로 만드는 순서

NiFi를 처음 다루면 어떤 프로세서를 먼저 놓아야 할지부터 막히기 쉽다. 아래 순서대로 만들면 된다.

1. `PG-1: API Ingestion` 안으로 들어간다.
2. 상단 툴바에서 **Processor**를 6개 배치한다.
3. 이름을 각각 `InvokeHTTP`, `SplitJson`, `EvaluateJsonPath`, `UpdateAttribute`, `JoltTransformJSON`, `LogAttribute`로 맞춘다.
4. 오류 로깅용 `LogAttribute`는 3개가 필요하므로 이름을 아래처럼 구분한다.
5. `Output Port` 1개를 추가하고 이름을 `api-out`으로 지정한다.

권장 이름:

- `LogAttribute [API호출실패]`
- `LogAttribute [JSON경로실패]`
- `LogAttribute [변환실패]`

그 다음 연결선을 만든다.

1. `InvokeHTTP`에서 `SplitJson`으로 연결하고 relationship은 `response`만 선택한다.
2. `SplitJson`에서 `EvaluateJsonPath`로 연결하고 relationship은 `split`만 선택한다.
3. `EvaluateJsonPath`에서 `UpdateAttribute`로 연결하고 relationship은 `matched`를 선택한다.
4. `UpdateAttribute`에서 `JoltTransformJSON`으로 연결하고 relationship은 `success`를 선택한다.
5. `JoltTransformJSON`에서 `api-out`으로 연결하고 relationship은 `success`를 선택한다.
6. 실패 라인은 각각 대응하는 `LogAttribute`로 연결한다.

이 단계에서는 아직 Start 하지 않는다. 먼저 모든 프로세서 설정을 끝낸 뒤, 마지막에 한 번에 시작하는 편이 안전하다.

### 2-4. InvokeHTTP 프로세서 설정

`InvokeHTTP`를 더블클릭해 `Settings`, `Scheduling`, `Properties`, `Relationships` 탭 순서로 본다.

**Properties 탭**

| 속성 | 값 | 설명 |
|------|-----|------|
| HTTP Method | `GET` | GET polling |
| HTTP URL | `http://payment-api:5050/api/v1/payments/recent?count=20` | Docker 네트워크 내부 API 호출 |
| Connection Timeout | `10 sec` | 초기 연결 타임아웃 |
| Socket Read Timeout | `30 sec` | 응답 읽기 타임아웃 |
| Response Generation Required | `false` | 정상 응답만 `response`로 전달 |
| Response Body Ignored | `false` | 응답 본문을 후속 프로세서에서 사용 |

**Scheduling 탭**

| 속성 | 값 | 설명 |
|------|-----|------|
| Run Schedule | `30 sec` | 30초마다 polling |
| Execution | `Primary Node` | 클러스터 환경에서 중복 호출 방지 |

**Relationships 탭**

- `response`, `original`, `retry`, `failure`, `no retry`를 확인한다.
- `response`만 다음 프로세서로 연결한다.
- `original`은 auto-terminate 한다.

> `Primary Node` 설정은 User Guide의 Scheduling/Execution 개념과 연결된다. 외부 REST API를 여러 노드가 동시에 polling하면 중복 수집이 생길 수 있으므로, 현재 Nexus Pay 시나리오에서는 1회 호출만 허용하는 구성이 맞다.

> `InvokeHTTP`의 GET 호출에서는 `Request Content-Type` 설정이 필수는 아니다. 이 속성은 POST/PUT/PATCH 본문 전송 시나리오에서 더 중요하다.

설정을 저장하기 전에 마지막으로 아래 3가지만 눈으로 다시 확인한다.

- URL이 `localhost`가 아니라 `payment-api`인지 확인
- `Run Schedule`이 `30 sec`인지 확인
- `original`을 auto-terminate 했는지 확인

### 2-5. SplitJson 프로세서 설정

API 응답은 `{ "status": "ok", "count": 20, "fetched_at": "...", "data": [ ... ] }` 구조이므로 `data` 배열을 개별 거래 FlowFile로 분리한다.

| 속성 | 값 | 설명 |
|------|-----|------|
| JsonPath Expression | `$.data` | data 배열 요소를 개별 FlowFile로 분리 |
| Null Value Representation | `empty string` | null 처리 기본값 |

연결은 `InvokeHTTP response -> SplitJson`, 그리고 `SplitJson split -> EvaluateJsonPath`로 설정한다.

실무 포인트:

- `$.data[*]`가 아니라 `$.data`를 써도 배열 요소가 건별로 분리된다.
- 이 단계가 없으면 후속 프로세서는 "거래 20건이 들어 있는 한 개의 JSON 문서"를 처리하게 된다.
- Day 4에서 Kafka로 보낼 때는 보통 "거래 1건 = 메시지 1건" 형태가 운영상 유리하므로 여기서 미리 쪼개는 구조가 맞다.

### 2-6. EvaluateJsonPath 프로세서 설정

분리된 개별 JSON에서 핵심 필드를 FlowFile Attribute로 추출한다. 이후 LogAttribute, Provenance 검색, Kafka 파티션 키 설계에 재사용할 수 있다.

`EvaluateJsonPath`의 핵심 역할은 JSON 본문 자체를 바꾸는 것이 아니라, 본문 안에 들어 있는 중요한 값을 읽어 FlowFile Attribute로 꺼내 놓는 것이다. 이렇게 추출한 attribute는 NiFi가 후속 단계에서 본문을 다시 파싱하지 않고도 라우팅, 로깅, 추적, 조건 분기 작업을 수행할 수 있게 해준다. 즉 Day 2 실습에서는 `SplitJson`으로 거래 1건씩 분리한 뒤, 각 거래의 `event_id`, `user_id`, `timestamp`, `source` 같은 핵심 식별값을 NiFi가 다루기 쉬운 메타데이터 형태로 만드는 단계라고 이해하면 된다.

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

관계 연결:

- `matched -> UpdateAttribute`
- `failure -> LogAttribute [JSON경로실패]`

이 단계에서 자주 보는 실수:

- `Destination`을 `flowfile-content`로 잘못 두면 content가 덮어써진다.
- JsonPath 오타로 `matched` 대신 `failure`만 계속 쌓일 수 있다.
- 숫자 필드도 attribute에 들어가면 문자열처럼 보이므로, 이후 조건식 작성 시 이를 감안해야 한다.

### 2-7. UpdateAttribute 프로세서 설정

`JoltTransformJSON`에서 현재 시각을 직접 계산하지 않고, 먼저 attribute로 만들어 전달한다.

| 속성 | 값 |
|------|-----|
| ingested_at | `${now():format("yyyy-MM-dd'T'HH:mm:ss'Z'", "UTC")}` |
| source_system | `nexuspay-payment-api` |

관계 연결:

- `EvaluateJsonPath matched -> UpdateAttribute`
- `UpdateAttribute success -> JoltTransformJSON`

실습 의도:

- `ingested_at`은 "NiFi가 이 이벤트를 파이프라인에 올린 시각"
- `event_timestamp`는 "원본 결제 이벤트가 실제 발생한 시각"

이 둘을 분리해 두어야 나중에 지연 시간이나 수집 지연을 분석할 수 있다.

### 2-8. JoltTransformJSON 스키마 표준화

다중 소스에서 수집한 데이터를 하나의 표준 스키마로 변환한다. Day 2에서는 API 소스만 우선 적용하고, Day 3부터 CSV/DB 소스가 같은 패턴에 합류한다.

> 실습 중 `Jolt Specification`에 `${now():format(...)}`를 직접 넣으면 Expression Language 검증이 까다로울 수 있다. 그래서 이번 설계는 `UpdateAttribute`에서 시간을 만들고, Jolt에서는 `${ingested_at}`만 참조한다.

`config/nifi/jolt-spec-api-payment.json` 파일을 사용한다.

```json
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
      "ingested_at": "${ingested_at}",
      "source_system": "${source_system}"
    }
  }
]
```

`JoltTransformJSON` 설정:

| 속성 | 값 |
|------|-----|
| Jolt Transformation DSL | `Chain` |
| Jolt Specification | `config/nifi/jolt-spec-api-payment.json` 내용 붙여넣기 |

관계 연결:

- `success -> Output Port [api-out]`
- `failure -> LogAttribute [변환실패]`

여기서 꼭 확인할 점:

- `Jolt Transformation DSL`이 `Chain`인지 확인
- `default` 단계에서 `${ingested_at}`, `${source_system}` 문자열이 그대로 들어가야 하는지 테스트
- 변환 성공 후 `api-out` 앞 큐에서 최종 JSON 구조를 직접 열어본다

### 2-9. 오류 처리 프로세서 설정

Day 2에서는 오류를 "API 호출 오류", "JSON 구조 오류", "변환 오류"로 나눠 본다. 이렇게 분리해 두면 Bulletin Board와 `nifi-app.log`에서 어느 단계가 문제인지 바로 확인할 수 있다.

**API 호출 실패 LogAttribute**

| 속성 | 값 |
|------|-----|
| Log Level | `warn` |
| Log prefix | `[API-FAIL]` |
| Attributes to Log | `invokehttp.status.code, invokehttp.status.message, invokehttp.request.url, invokehttp.request.duration` |

**JSON 경로 실패 LogAttribute**

| 속성 | 값 |
|------|-----|
| Log Level | `warn` |
| Log prefix | `[JSONPATH-FAIL]` |
| Attributes to Log | `filename, uuid, mime.type` |

**변환 실패 LogAttribute**

| 속성 | 값 |
|------|-----|
| Log Level | `error` |
| Log prefix | `[TRANSFORM-FAIL]` |
| Attributes to Log | `event_id, event_type, mime.type, error.message` |

### 2-9A. Start 순서

설정이 끝나면 아래 순서로 Start 한다.

1. `LogAttribute` 3개
2. `JoltTransformJSON`
3. `UpdateAttribute`
4. `EvaluateJsonPath`
5. `SplitJson`
6. `InvokeHTTP`

이 순서를 권장하는 이유는 하류가 먼저 준비된 상태에서 상류 polling을 시작해야 최초 응답이 중간 큐에 불필요하게 적체되지 않기 때문이다.

### 2-10. API 수집 플로우 동작 검증

먼저 API 시뮬레이터를 확인한다.

```bash
curl -s "http://localhost:5050/api/v1/payments/recent?count=3" | jq
```

그다음 NiFi UI에서 아래 순서로 검증한다.

1. `PG-1: API Ingestion` 안의 프로세서를 시작한다.
2. 약 30초 대기한다.
3. `InvokeHTTP -> SplitJson` connection에 데이터가 지나가는지 본다.
4. `JoltTransformJSON -> api-out` 직전 connection에서 FlowFile 1건을 선택한다.
5. `View data`로 최종 JSON을 확인한다.
6. 우측 상단 `Bulletin Board`에서 경고/오류가 없는지 확인한다.
7. 특정 FlowFile의 `Provenance`에서 `RECEIVE/CONTENT_MODIFIED/ATTRIBUTES_MODIFIED` 흐름을 확인한다.

권장 검증 순서:

1. `InvokeHTTP`의 아웃바운드가 30초마다 실행되는지 상태 아이콘으로 본다.
2. `SplitJson` 이후 큐의 FlowFile 수가 `count=20` 기준으로 증가하는지 본다.
3. `EvaluateJsonPath` 이후 FlowFile attribute에 `event_id`, `user_id`, `timestamp`가 들어갔는지 확인한다.
4. `UpdateAttribute` 이후 `ingested_at`, `source_system`이 추가됐는지 확인한다.
5. `JoltTransformJSON` 이후 content가 표준 JSON으로 바뀌었는지 확인한다.
6. `api-out` 큐에 데이터가 쌓이면 Day 2 범위는 성공이다.

선택 검증으로 NiFi REST API를 호출해도 된다.

```bash
TOKEN=$(curl -sk \
  -X POST https://localhost:8443/nifi-api/access/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode "username=${NIFI_USERNAME}" \
  --data-urlencode "password=${NIFI_PASSWORD}")

curl -sk \
  -H "Authorization: Bearer $TOKEN" \
  https://localhost:8443/nifi-api/flow/process-groups/root | jq | head -30
```

최종 FlowFile Content 예시는 다음과 같다.

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
  "ingested_at": "2026-04-01T09:30:05Z",
  "source_system": "nexuspay-payment-api"
}
```

### 2-11. Day 2 운영 체크 포인트

User Guide와 Administrator's Guide를 Day 2 관점으로 요약하면 다음을 꼭 본다.

- Connection queue가 빠르게 쌓이면 Back Pressure 임계값과 하류 정지를 먼저 확인
- 프로세서 경고는 Bulletin Board에서, 상세 원인은 `nifi-app.log`에서 확인
- Provenance로 "API 응답 수신 -> JSON 분리 -> 속성 추가 -> Jolt 변환" 이력을 따라가며 원인 분석
- NiFi 로그/리포지터리 볼륨은 실습 중 삭제하지 않고 유지

### 2-11A. 막힐 때 바로 보는 트러블슈팅

증상별로 가장 먼저 볼 포인트를 정리하면 다음과 같다.

| 증상 | 먼저 확인할 것 | 원인 후보 |
|------|----------------|-----------|
| `InvokeHTTP`가 빨간색/노란색 | URL, 컨테이너 기동 상태, Bulletin | `payment-api` 미기동, 타임아웃 |
| `SplitJson`에서 실패 | 응답 JSON 원문 | `data` 배열 경로 불일치 |
| `EvaluateJsonPath`에서 failure 발생 | JsonPath 키 이름 | `event_id`, `timestamp` 오타 |
| `JoltTransformJSON`에서 failure 발생 | DSL 모드, 스펙 JSON | `Chain` 미설정, JSON 문법 오류 |
| `api-out`에 데이터가 안 감 | upstream queue, relationship 연결 | success 연결 누락 |

### 2-12. API 수집 성능 측정

`scripts/nifi/measure_api_throughput.sh` 스크립트로 5분 기준 API 생성 이벤트 증가량을 측정한다.

```bash
chmod +x scripts/nifi/measure_api_throughput.sh
bash scripts/nifi/measure_api_throughput.sh
```

**Day 2 완료 기준**: `PG-1: API Ingestion` 내 `InvokeHTTP(response)` → `SplitJson` → `EvaluateJsonPath` → `UpdateAttribute` → `JoltTransformJSON` 플로우가 정상 작동하고, `api-out` 직전 FlowFile에 `ingested_at`와 `source_system`이 포함되며, Bulletin Board와 Provenance에서 처리 흐름을 확인하고, `scripts/nifi/measure_api_throughput.sh` 실행 결과까지 점검한 상태.

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
                                                            └── (split) → UpdateAttribute
                                                                           │
                                                                           └── (success) → JoltTransformJSON
                                                                                             │
                                                                                             └── (success) → ExecuteScript
                                                                                                                    │
                                                                                                                    ├── (success) → Output Port [file-out]
                                                                                                                    └── (failure) → LogAttribute [변환실패-UTC정규화]
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
mkdir -p data/nifi/settlement/processed
```

### 3-4. ConvertRecord 프로세서 설정 (CSV → JSON)

NiFi의 Record 기반 처리를 위해 Reader/Writer Controller Service를 먼저 생성한다.

**Controller Service 생성 (NiFi UI 현재 버전)**:

1. `PG-2: File Ingestion` 그룹 안으로 들어간다.
2. 빈 캔버스에서 우클릭 후 `Controller Services`를 선택한다.
3. Controller Services 화면으로 이동한다.
4. `+` 버튼으로 필요한 서비스를 추가한다.

> 참고: 예전 1.x UI에서는 `Configure -> Controller Services` 경로를 사용하기도 했지만, NiFi 2.9.0에서는 우클릭 메뉴에 `Controller Services`가 바로 표시된다.

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

**3) JsonTreeReader**:
| 속성 | 값 |
|------|-----|
| Schema Access Strategy | `Infer Schema` |

**ConvertRecord 프로세서 설정**:
| 속성 | 값 |
|------|-----|
| Record Reader | `CSVReader` |
| Record Writer | `JsonRecordSetWriter` |

### 3-5. SplitRecord 프로세서 설정

CSV 파일 하나에 50건의 레코드가 포함되어 있으므로 개별 레코드로 분리한다.

| 속성 | 값 |
|------|-----|
| Record Reader | `JsonTreeReader` |
| Record Writer | `JsonRecordSetWriter` |
| Records Per Split | `1` |


### 3-6. JoltTransformJSON — 정산 CSV 스키마 표준화

정산 CSV의 필드명을 표준 스키마에 맞게 변환한다.

### 3-6A. UpdateAttribute — 정산 수집 시각 추가

정산 CSV에도 API와 동일한 `ingested_at` 필드를 넣고, 파일 수집 소스를 구분하기 위한 `source_system`을 함께 추가해 공통 계약을 맞춘다.

| 속성 | 값 |
|------|-----|
| ingested_at | `${now():format("yyyy-MM-dd'T'HH:mm:ss'Z'", "UTC")}` |
| source_system | `nexus-settlement-file` |

관계 연결:
- `SplitRecord split -> UpdateAttribute`
- `UpdateAttribute success -> JoltTransformJSON`

| 속성 | 값 |
|------|-----|
| Jolt Transformation DSL | `Chain` |
| Jolt Specification | 아래 정산 CSV용 Jolt 스펙 붙여넣기 |

관계 연결:
- `success` -> `ExecuteScript`
- `failure` -> `변환실패`

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
      "ingested_at": "${ingested_at}",
      "source_system": "${source_system}",
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

### 3-6B. ExecuteScript — event_timestamp UTC 정규화

정산 CSV의 `settlement_date`는 날짜만 제공되므로, Jolt 변환 후 생성된 `event_timestamp`를 UTC ISO-8601 형식으로 정규화한다. 이 단계는 표준 스키마가 완성된 뒤에 수행하므로, 원본 CSV 필드명 대신 최종 표준 필드인 `event_timestamp`만 다루면 된다.

여기서 목표는 "날짜만 있는 정산 기준일"을 "표준 이벤트 타임스탬프"로 바꾸는 것이다. 따라서 이 단계가 끝나면 `event_timestamp`는 더 이상 `2026-04-13` 같은 날짜 문자열이 아니라, 반드시 `2026-04-13T00:00:00Z` 형태의 UTC ISO-8601 문자열이어야 한다.

`ExecuteScript`는 `Script Body`에 직접 붙여넣는 대신 외부 파일을 읽도록 구성한다. 현재 NiFi 컨테이너는 `./config/nifi`를 `/opt/nifi/custom-config`에 마운트하므로, `config/nifi/scripts/` 아래에 스크립트를 두면 설정과 자산 구조를 더 깔끔하게 유지할 수 있다.

```bash
mkdir -p config/nifi/scripts

cat > config/nifi/scripts/normalize-settlement-event-timestamp.groovy << 'EOF'
import groovy.json.JsonSlurper
import groovy.json.JsonOutput
import org.apache.nifi.processor.io.StreamCallback
import java.nio.charset.StandardCharsets
import java.util.TimeZone

def flowFile = session.get()
if (!flowFile) return

try {
    flowFile = session.write(flowFile, { inputStream, outputStream ->
        def json = new JsonSlurper().parse(
            inputStream.newReader(StandardCharsets.UTF_8.name())
        )

        if (json.event_timestamp instanceof String &&
                json.event_timestamp ==~ /\d{4}-\d{2}-\d{2}/) {
            def date = Date.parse("yyyy-MM-dd", json.event_timestamp)
            json.event_timestamp = date.format(
                "yyyy-MM-dd'T'HH:mm:ss'Z'",
                TimeZone.getTimeZone("UTC")
            )
        }

        outputStream.write(
            JsonOutput.toJson(json).getBytes(StandardCharsets.UTF_8)
        )
    } as StreamCallback)

    flowFile = session.putAttribute(flowFile, "event_timestamp.normalized", "true")
    session.transfer(flowFile, REL_SUCCESS)
} catch (Exception e) {
    log.error("event_timestamp UTC 정규화 실패", e)
    session.transfer(flowFile, REL_FAILURE)
}
EOF
```

`ExecuteScript` 설정:

| 속성 | 값 |
|------|-----|
| Script Engine | `Groovy` |
| Script File | `/opt/nifi/custom-config/scripts/normalize-settlement-event-timestamp.groovy` |
| Script Body | 비움 |
| Module Directory | 비움 |

이 단계에서 `Script File` 방식을 선택하면 NiFi 캔버스에 긴 스크립트를 직접 붙여넣지 않아도 되고, `config/nifi/scripts/` 아래의 버전 관리 대상 파일을 그대로 재사용할 수 있다. 팀 작업이나 재현 실습 관점에서도 `Script Body`보다 추적이 쉽다.

관계 연결:
- `JoltTransformJSON success -> ExecuteScript`
- `ExecuteScript success -> file-out`
- `ExecuteScript failure -> LogAttribute [변환실패-UTC정규화]`

`LogAttribute [변환실패-UTC정규화]` 설정:

| 속성 | 값 |
|------|-----|
| Log Level | `error` |
| Log prefix | `[UTC-NORMALIZE-FAIL]` |
| Attributes to Log | `filename, uuid, mime.type, event_timestamp, source_system, data_source, event_timestamp.normalized` |

이 로그 프로세서는 `ExecuteScript`에서 UTC 정규화에 실패한 FlowFile의 핵심 식별값을 `nifi-app.log`에 남긴다. `event_timestamp.normalized=true`가 찍히지 않았거나, `event_timestamp`가 날짜형 문자열로 남아 있는 경우 이 로그를 통해 즉시 확인할 수 있다.

정상 동작 검증 순서:

1. `JoltTransformJSON -> ExecuteScript` 큐에서 FlowFile이 정상적으로 소비되는지 확인한다.
2. `ExecuteScript -> file-out` connection에서 FlowFile 1건을 선택한다.
3. `View data`에서 `event_timestamp`가 `2026-04-13T00:00:00Z`처럼 UTC 형식으로 바뀌었는지 확인한다.
4. `Attributes` 탭에서 `event_timestamp.normalized = true`가 붙었는지 확인한다.
5. 오류가 발생하면 `ExecuteScript failure -> LogAttribute [변환실패-UTC정규화]`와 `nifi-app.log`를 함께 본다.

완료 판단 기준:

- `file-out` 직전 FlowFile Content에 `event_timestamp`가 반드시 `T00:00:00Z`를 포함한 UTC 문자열로 표시된다.
- 같은 FlowFile Attribute에 `event_timestamp.normalized = true`가 기록된다.
- `source_system = nexus-settlement-file`, `data_source = settlement-csv`, `ingested_at`가 함께 유지된다.
- `failure` 경로에 FlowFile이 쌓이지 않고, `변환실패-UTC정규화` 로그가 발생하지 않는다.

정상 처리 후 `event_timestamp` 예시:

```json
"event_timestamp": "2026-04-13T00:00:00Z"
```

### 3-7. 정산 CSV 수집 테스트

```bash
# CSV 파일 3개 생성 (30초 간격)
python scripts/nifi/csv_settlement_generator.py -n 3 -r 30 -i 30

# NiFi UI에서:
# 1. PG-2: File Ingestion 내 모든 프로세서 시작
# 2. ListFile이 파일 탐지 → FetchFile이 읽기 → ConvertRecord → SplitRecord → UpdateAttribute → Jolt → ExecuteScript
# 3. Output Port 직전 Connection에서 FlowFile 확인
# 4. /data/settlement/processed/ 디렉토리로 파일 이동 확인

ls -la data/nifi/settlement/
ls -la data/nifi/settlement/processed/
```

정산 CSV 테스트가 정상 완료되면 `file-out` 직전 FlowFile은 아래 조건을 만족해야 한다.

- CSV 원본 필드가 표준 스키마로 변환되어 있다.
- `source_system = nexus-settlement-file`
- `data_source = settlement-csv`
- `ingested_at`가 포함되어 있다.
- `event_timestamp`가 `2026-04-13T00:00:00Z` 형태의 UTC 문자열이다.

### 3-8. PG-3: DB Ingestion — PostgreSQL 고객 마스터 수집

PostgreSQL의 고객 데이터를 증분(Incremental) 방식으로 수집한다.

**사전 준비 — 고객 마스터 테이블 생성**:

```sql
-- scripts/nifi/init-customers.sql
-- PostgreSQL에 고객 마스터 테이블 추가

-- 참고:
-- 이 스크립트는 Week 1 foundation 환경에서 PostgreSQL 컨테이너 최초 기동 시
-- /docker-entrypoint-initdb.d/ 경로를 통해 자동 실행된다.
-- Week 3에서는 같은 customers 테이블을 DB Ingestion 소스로 재사용한다.

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

-- 샘플 고객 1000명 생성
INSERT INTO customers (user_id, name, email, phone, grade, is_active, created_at)
SELECT
    gs AS user_id,
    '고객_' || gs,
    'user_' || gs || '@nexuspay.io',
    '010-' || lpad((random() * 9999)::int::text, 4, '0') || '-' || lpad((random() * 9999)::int::text, 4, '0'),
    CASE
        WHEN random() < 0.70 THEN 'NORMAL'
        WHEN random() < 0.90 THEN 'VIP'
        ELSE 'PREMIUM'
    END,
    random() > 0.05 AS is_active,
    NOW() - (random() * INTERVAL '365 days')
FROM generate_series(1, 1000) AS gs;
```

```bash
# customers 테이블은 foundation 환경 최초 기동 시 자동 생성된다.
# 볼륨을 초기화했거나 수동 재적재가 필요할 때만 아래 명령을 사용한다.
docker exec -i lab-postgres psql -U pipeline -d pipeline_db < scripts/nifi/init-customers.sql

# 테이블 존재 및 데이터 건수 확인
docker exec lab-postgres psql -U pipeline -d pipeline_db \
  -c "SELECT to_regclass('public.customers') AS customers_table, count(*) AS customer_count FROM customers;"

# 등급별 분포와 활성 고객 비율 확인
docker exec lab-postgres psql -U pipeline -d pipeline_db \
  -c "SELECT grade, count(*), round(avg(CASE WHEN is_active THEN 1 ELSE 0 END)::numeric * 100, 1) AS active_pct
      FROM customers GROUP BY grade ORDER BY count(*) DESC;"

# 샘플 데이터 5건 확인
docker exec lab-postgres psql -U pipeline -d pipeline_db \
  -c "SELECT customer_id, user_id, name, email, phone, grade, is_active, created_at, updated_at
      FROM customers ORDER BY customer_id LIMIT 5;"
```

이 실습에서는 Week 1 foundation 스키마를 그대로 사용한다. 즉 NiFi `PG-3: DB Ingestion`은 `customers` 테이블 구조를 다시 정의하지 않고, 이미 운영 중인 고객 마스터를 증분 수집 대상으로 읽어오는 방식으로 진행한다.

### 3-9. DB 수집 플로우 구성

`PG-3: DB Ingestion` 내부:

```
QueryDatabaseTable
    └── (success) → ConvertRecord (Avro → JSON)
                       ├── (success) → SplitRecord
                       │                  ├── (split) → UpdateAttribute
                       │                  │               └── (success) → JoltTransformJSON
                       │                  │                                ├── (success) → Output Port [db-out]
                       │                  │                                └── (failure) → LogAttribute [변환실패]
                       │                  ├── (failure) → LogAttribute [변환실패]
                       │                  └── (original) → terminate
                       └── (failure) → LogAttribute [변환실패]
```

`QueryDatabaseTable 2.9.0`은 `failure` relationship를 별도로 제공하지 않을 수 있으므로, DB 조회 오류는 Bulletin Board와 `nifi-app.log`로 확인한다.

### 3-10. PG-3 Controller Service 설정

`PG-3: DB Ingestion`에서는 아래 Controller Service를 먼저 준비한다.

1. `PG-3: DB Ingestion` 그룹 안으로 들어간다.
2. 빈 캔버스에서 우클릭 후 `Controller Services`를 선택한다.
3. `+` 버튼으로 필요한 서비스를 추가한다.
4. 속성 입력 후 `Enable`한다.

필요한 Controller Service 목록:
- `DBCPConnectionPool`
- `AvroReader`
- `JsonRecordSetWriter`
- `JsonTreeReader`

**1) DBCPConnectionPool**:

| 속성 | 값 |
|------|-----|
| Database Connection URL | `jdbc:postgresql://postgres:5432/pipeline_db` |
| Database Driver Class Name | `org.postgresql.Driver` |
| Database Driver Location(s) | `/opt/nifi/custom-config/postgresql-42.7.3.jar` |
| Database User | `pipeline` |
| Password | `pipeline` |
| Max Wait Time | `10 sec` |
| Max Total Connections | `5` |

**2) AvroReader**:

| 속성 | 값 |
|------|-----|
| Schema Access Strategy | `Use Embedded Avro Schema` |

**3) JsonRecordSetWriter**:

| 속성 | 값 |
|------|-----|
| Schema Write Strategy | `Do Not Write Schema` |
| Output Grouping | `One Line Per Object` |
| Pretty Print JSON | `false` |

**4) JsonTreeReader**:

| 속성 | 값 |
|------|-----|
| Schema Access Strategy | `Infer Schema` |

> **PostgreSQL JDBC 드라이버 준비**:
```bash
# 먼저 파일 존재 여부를 확인한다.
ls -l config/nifi/postgresql-42.7.3.jar

# 파일이 없으면 JDBC 드라이버를 다운로드한다.
curl -L -o config/nifi/postgresql-42.7.3.jar \
  https://jdbc.postgresql.org/download/postgresql-42.7.3.jar

# 다운로드 후 호스트 경로에 파일이 생겼는지 다시 확인한다.
ls -l config/nifi/postgresql-42.7.3.jar

# NiFi 컨테이너 내부에도 같은 파일이 마운트되었는지 확인한다.
docker exec -it lab-nifi sh -c 'ls -l /opt/nifi/custom-config/postgresql-42.7.3.jar'
```

`ls -l config/nifi/postgresql-42.7.3.jar` 실행 시 `No such file or directory`가 보이면 아직 JDBC 드라이버가 준비되지 않은 상태다. 이 경우 위 `curl -L -o ...` 명령으로 먼저 파일을 내려받은 뒤, `DBCPConnectionPool`의 `Database Driver Location(s)`에 `/opt/nifi/custom-config/postgresql-42.7.3.jar`를 입력해야 한다.

회사망이나 로컬 보안 정책으로 `curl` 다운로드가 막히면 브라우저에서 `https://jdbc.postgresql.org/download/postgresql-42.7.3.jar` 파일을 내려받아 `config/nifi/` 경로에 직접 저장한 뒤 같은 확인 명령을 실행한다.

> **DBCPConnectionPool invalid 메시지 처리 가이드**:
>
> `database-driver-locations validated against '/opt/nifi/custom-config/postgresql-42.7.3.jar' is invalid because The specified resource(s) do not exist or could not be accessed` 메시지가 보이면 아래 순서로 점검한다.
>
> 1. 호스트에 JDBC 드라이버 파일이 실제로 존재하는지 확인한다.
>
> ```bash
> ls -l config/nifi/postgresql-42.7.3.jar
> ```
>
> 2. NiFi 컨테이너 내부에서 동일 파일이 마운트되었는지 확인한다.
>    Git Bash에서는 `/opt/...` 경로가 Windows 경로로 잘못 변환될 수 있으므로 `sh -c`로 확인하는 것이 안전하다.
>
> ```bash
> docker exec -it lab-nifi sh -c 'ls -l /opt/nifi/custom-config/postgresql-42.7.3.jar'
> ```
>
> 3. `DBCPConnectionPool` 속성이 아래 값과 정확히 일치하는지 다시 확인한다.
>    - `Database Driver Class Name = org.postgresql.Driver`
>    - `Database Driver Location(s) = /opt/nifi/custom-config/postgresql-42.7.3.jar`
>
> 4. 설정을 다시 `Apply`한 뒤 Controller Service 화면에서 `Enable`을 재시도한다.
>
> 파일이 존재하는데도 invalid가 남으면, 원인은 더 이상 드라이버 파일 자체가 아니라 `Driver Class Name`, JDBC URL, 사용자/비밀번호 오타일 가능성이 높다.

### 3-11. QueryDatabaseTable 프로세서 설정

증분 수집(Incremental Fetch) 방식으로 변경된 레코드만 가져온다.

| 속성 | 값 | 설명 |
|------|-----|------|
| Database Connection Pooling Service | `DBCPConnectionPool` | 위에서 생성한 서비스 |
| Database Type | `PostgreSQL` | |
| Table Name | `customers` | |
| Columns to Return | `customer_id, user_id, name, email, phone, grade, is_active, created_at, updated_at` | |
| Maximum-value Columns | `updated_at` | 증분 수집 기준 컬럼 |
| Max Rows Per Flow File | `50` | FlowFile당 최대 레코드 수 |
| Scheduling — Run Schedule | `60 sec` | 1분마다 변경분 조회 |

> **증분 수집(Incremental Fetch) 원리**: QueryDatabaseTable은 `Maximum-value Columns`에 지정된 컬럼의 마지막 수집 값을 NiFi State에 저장한다. 다음 실행 시 `WHERE updated_at > '마지막값'` 조건이 자동 추가되어 변경분만 가져온다. 전체 테이블을 매번 스캔하지 않으므로 대용량 테이블에서도 효율적이다.

> **현재 UI 메모**: `QueryDatabaseTable`에서는 `Output Format = Avro` 속성이 별도로 보이지 않을 수 있다. 이 경우 표기상 출력 포맷을 설정하지 않고, 다음 단계의 `ConvertRecord`에서 `AvroReader -> JsonRecordSetWriter` 조합으로 JSON 변환을 수행하면 된다.

### 3-12. ConvertRecord 프로세서 설정 (Avro → JSON)

`QueryDatabaseTable`이 반환한 Avro 레코드를 JSON으로 변환한다.

| 속성 | 값 |
|------|-----|
| Record Reader | `AvroReader` |
| Record Writer | `JsonRecordSetWriter` |

관계 연결:
- `success` -> `SplitRecord`
- `failure` -> `변환실패`

### 3-13. SplitRecord 프로세서 설정

고객 레코드를 1건씩 개별 FlowFile로 분리한다.

| 속성 | 값 |
|------|-----|
| Record Reader | `JsonTreeReader` |
| Record Writer | `JsonRecordSetWriter` |
| Records Per Split | `1` |

관계 연결:
- `split` -> `UpdateAttribute`
- `failure` -> `변환실패`
- `original` -> `terminate`

### 3-14. UpdateAttribute — DB 수집 시각 추가

DB 변경 이벤트에도 `ingested_at`를 넣고, DB 소스 식별용 `source_system`을 함께 추가해 API/CSV와 같은 공통 메타데이터 계약을 유지한다.

| 속성 | 값 |
|------|-----|
| ingested_at | `${now():format("yyyy-MM-dd'T'HH:mm:ss'Z'", "UTC")}` |
| source_system | `nexuspay-customer-db` |

관계 연결:
- `SplitRecord split -> UpdateAttribute`
- `UpdateAttribute success -> JoltTransformJSON`

### 3-15. JoltTransformJSON — 고객 마스터 스키마 표준화

고객 마스터 필드를 표준 스키마에 맞게 변환한다.

| 속성 | 값 |
|------|-----|
| Jolt Transformation DSL | `Chain` |
| Jolt Specification | 아래 고객 마스터용 Jolt 스펙 붙여넣기 |

관계 연결:
- `success` -> `ExecuteScript`
- `failure` -> `변환실패`

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
      "grade": "customer_grade",
      "is_active": "is_active",
      "created_at": "created_at",
      "updated_at": "event_timestamp"
    }
  },
  {
    "operation": "modify-overwrite-beta",
    "spec": {
      "event_id": "=toString(@(1,event_id))"
    }
  },
  {
    "operation": "default",
    "spec": {
      "event_type": "CUSTOMER_UPDATE",
      "data_source": "customer-db",
      "source_system": "${source_system}",
      "schema_version": "1.0",
      "ingested_at": "${ingested_at}",
      "channel": "DB_SYNC",
      "status": null,
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

### 3-15A. ExecuteScript — DB event_timestamp UTC 정규화

DB 수집에서는 PostgreSQL `updated_at` 값이 Jolt 변환 후 `event_timestamp`로 전달된다. 이 값은 `2026-04-14 05:28:02.068599`처럼 timezone 정보가 없는 문자열일 수 있으므로, `ExecuteScript`를 Jolt 뒤에 두고 UTC ISO-8601 형식으로 정규화한다.

실습 기본 가정:

- PostgreSQL `updated_at` 값을 UTC 기준 timestamp로 해석한다.
- 만약 운영 환경에서 DB가 KST 로컬 시간을 저장한다면, 아래 스크립트의 `SOURCE_ZONE`을 `ZoneId.of("Asia/Seoul")`로 바꾼다.

```bash
cat > config/nifi/scripts/normalize-customer-event-timestamp.groovy << 'EOF'
import groovy.json.JsonSlurper
import groovy.json.JsonOutput
import org.apache.nifi.processor.io.StreamCallback
import java.nio.charset.StandardCharsets
import java.time.LocalDateTime
import java.time.ZoneId
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

def flowFile = session.get()
if (!flowFile) return

def SOURCE_ZONE = ZoneId.of("UTC")
def INPUT_FORMATS = [
    DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss.SSSSSS"),
    DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")
]

try {
    flowFile = session.write(flowFile, { inputStream, outputStream ->
        def json = new JsonSlurper().parse(
            inputStream.newReader(StandardCharsets.UTF_8.name())
        )

        if (json.event_timestamp instanceof String) {
            def rawTimestamp = json.event_timestamp
            LocalDateTime parsed = null

            for (formatter in INPUT_FORMATS) {
                try {
                    parsed = LocalDateTime.parse(rawTimestamp, formatter)
                    break
                } catch (Exception ignored) {
                }
            }

            if (parsed != null) {
                json.event_timestamp = parsed
                    .atZone(SOURCE_ZONE)
                    .withZoneSameInstant(ZoneOffset.UTC)
                    .format(DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss'Z'"))
            }
        }

        outputStream.write(
            JsonOutput.toJson(json).getBytes(StandardCharsets.UTF_8)
        )
    } as StreamCallback)

    flowFile = session.putAttribute(flowFile, "event_timestamp.normalized", "true")
    session.transfer(flowFile, REL_SUCCESS)
} catch (Exception e) {
    log.error("DB event_timestamp UTC 정규화 실패", e)
    session.transfer(flowFile, REL_FAILURE)
}
EOF
```

`ExecuteScript` 설정:

| 속성 | 값 |
|------|-----|
| Script Engine | `Groovy` |
| Script File | `/opt/nifi/custom-config/scripts/normalize-customer-event-timestamp.groovy` |
| Script Body | 비움 |
| Module Directory | 비움 |

관계 연결:
- `JoltTransformJSON success -> ExecuteScript`
- `ExecuteScript success -> db-out`
- `ExecuteScript failure -> LogAttribute [변환실패-UTC정규화]`

`LogAttribute [변환실패-UTC정규화]` 설정:

| 속성 | 값 |
|------|-----|
| Log Level | `error` |
| Log prefix | `[DB-UTC-NORMALIZE-FAIL]` |
| Attributes to Log | `filename, uuid, mime.type, event_timestamp, source_system, data_source, event_timestamp.normalized, tablename` |

정상 처리 후 `event_timestamp` 예시:

```json
"event_timestamp": "2026-04-14T05:28:02Z"
```

### 3-16. DB 수집 증분 추출 검증

```bash
# 1) NiFi에서 PG-3 프로세서 그룹 시작 → 초기 1000건 수집

# 2) PostgreSQL에서 고객 데이터 변경 (3건 업데이트)
docker exec lab-postgres psql -U pipeline -d pipeline_db -c "
  UPDATE customers SET grade = 'VIP', updated_at = NOW() WHERE user_id = 1;
  UPDATE customers SET email = 'vip50@nexuspay.io', updated_at = NOW() WHERE user_id = 50;
  UPDATE customers SET is_active = false, updated_at = NOW() WHERE user_id = 100;
"

# 3) 60초 후 NiFi가 변경된 3건만 수집하는지 확인
# → PG-3 Output Port의 FlowFile 수가 3건이어야 함

# 4) 변경 확인
docker exec lab-postgres psql -U pipeline -d pipeline_db \
  -c "SELECT user_id, grade, email, is_active, updated_at
      FROM customers WHERE user_id IN (1, 50, 100);"
```

고객 변경을 반복적으로 발생시켜 `QueryDatabaseTable`의 증분 수집을 더 현실적으로 검증하고 싶다면 30초 주기 시뮬레이터를 사용한다.

```bash
chmod +x scripts/nifi/simulate_customer_updates.sh

# 30초마다 3건씩 계속 변경
bash scripts/nifi/simulate_customer_updates.sh 30

# 30초 간격으로 5회만 실행
bash scripts/nifi/simulate_customer_updates.sh 30 5
```

이 스크립트는 매 실행마다 `customers` 테이블에서 임의의 고객 3명을 골라 아래 패턴으로 변경한다.

- 1명: `grade` 순환 변경 (`NORMAL -> VIP -> PREMIUM -> NORMAL`)
- 1명: `email` 변경
- 1명: `is_active` 토글

모든 업데이트는 `updated_at = NOW()`를 함께 반영하므로, `QueryDatabaseTable`의 `Maximum-value Columns = updated_at` 설정과 바로 연동된다. NiFi UI에서 `PG-3 Output Port [db-out]`와 `PG-4 db-in-check` 로그를 함께 보면 30초 간격으로 변경분이 유입되는지 확인할 수 있다.

### 3-16. 세 소스 동시 수집 확인

```bash
# 세 소스 동시 작동 상태에서 FlowFile 흐름 확인
# NiFi UI → Nexus Pay Data Ingestion 그룹 레벨에서:
#   PG-1 Output Port: API 이벤트 (30초마다 20건)
#   PG-2 Output Port: CSV 정산 레코드 (파일 생성 시)
#   PG-3 Output Port: DB 고객 변경분 (60초마다 증분)

# CSV 파일 추가 생성으로 PG-2 트리거
python scripts/nifi/csv_settlement_generator.py -n 2 -r 25 -i 10
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
cat > config/nifi/nexuspay-standard-schema.avsc << 'EOF'
{
  "type": "record",
  "name": "NexusPayStandardEvent",
  "namespace": "com.nexuspay.events",
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
    {"name": "status", "type": ["null", "string"], "default": null},
    {"name": "is_suspicious", "type": "boolean", "default": false},
    {"name": "event_timestamp", "type": "string"},
    {"name": "ingested_at", "type": ["null", "string"], "default": null},
    {"name": "data_source", "type": "string"},
    {"name": "schema_version", "type": "string", "default": "1.0"},
    {"name": "created_at", "type": ["null", "string"], "default": null},
    {"name": "fee_amount", "type": ["null", "double"], "default": null},
    {"name": "net_amount", "type": ["null", "double"], "default": null},
    {"name": "tx_count", "type": ["null", "int"], "default": null},
    {"name": "batch_id", "type": ["null", "string"], "default": null},
    {"name": "customer_name", "type": ["null", "string"], "default": null},
    {"name": "customer_email", "type": ["null", "string"], "default": null},
    {"name": "customer_phone", "type": ["null", "string"], "default": null},
    {"name": "customer_grade", "type": ["null", "string"], "default": null},
    {"name": "is_active", "type": ["null", "boolean"], "default": null}
  ]
}
EOF
```

> **표준화 원칙**: `event_id`, `event_type`, `event_timestamp`, `data_source`, `schema_version`은 공통 핵심 필드로 유지하고, `status`, `ingested_at`, `created_at` 및 소스별 확장 필드는 nullable 필드로 둔다. 이렇게 하면 API/CSV/DB 세 소스가 같은 Avro 계약을 공유하면서도, 소스 특화 정보는 손실 없이 보존할 수 있다.

### 4-3. ValidateRecord 프로세서 설정

| 속성 | 값 |
|------|-----|
| Record Reader | `JsonTreeReader` |
| Record Writer | `JsonRecordSetWriter` |
| Schema Access Strategy | `Use 'Schema Text' Property` |
| Schema Text | (위 Avro 스키마 내용 붙여넣기) |
| Allow Extra Fields | `true` |
| Strict Type Checking | `false` |

### 4-4. UpdateAttribute — 소스 태그 및 수집 타임스탬프 추가

| 속성 | 값 | 설명 |
|------|-----|------|
| kafka.topic | `nexuspay.events.ingested` | 통합 수집 토픽 |
| kafka.key | `${user_id}` | 파티션 키 (Week 2 설계 연계) |
| nifi.ingested.at | `${now():format('yyyy-MM-dd\\'T\\'HH:mm:ss\\'Z\\'', 'UTC')}` | NiFi 수집 시각 |
| nifi.source.group | `${data_source}` | 소스 구분 태그 |

### 4-5. 통합 수집 토픽 생성

> **아키텍처 전환 안내**: Week 2에서는 프로듀서가 거래 유형별로 `nexuspay.transactions.payment`, `nexuspay.transactions.transfer`, `nexuspay.transactions.withdrawal` 토픽에 직접 전송하는 구조였다. Week 3부터는 NiFi가 다양한 소스(API, CSV, DB)의 데이터를 **표준 스키마로 변환한 후 단일 통합 토픽으로 전송**하는 구조로 전환한다. 이후 Week 4에서 Flink가 이 통합 토픽을 소비하여 이벤트 타입별 분기 처리를 수행한다. 즉, **수집 → 표준화(NiFi) → 버퍼(Kafka) → 분기 처리(Flink)** 아키텍처로 발전시키는 것이다.

기존 거래 유형별 토픽과 별도로, NiFi에서 수집한 모든 데이터가 흘러가는 통합 토픽을 생성한다.

```bash
# 통합 수집 토픽
docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka-1:9092 \
  --create --topic nexuspay.events.ingested \
  --partitions 6 \
  --replication-factor 3 \
  --config min.insync.replicas=2 \
  --config retention.ms=604800000

# DLQ 토픽 (품질 검증 실패 메시지)
docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka-1:9092 \
  --create --topic nexuspay.events.dlq \
  --partitions 2 \
  --replication-factor 3 \
  --config min.insync.replicas=2 \
  --config retention.ms=2592000000

# 토픽 확인
docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka-1:9092 --list | grep nexuspay.events
```

### 4-6. PG-5: Kafka Publishing — PublishKafka 연동

> **NiFi 2.9.0 프로세서 이름 정리**: 현재 NiFi 2.9.0 UI에서는 Kafka 송신 프로세서가 `PublishKafka`, 수신 프로세서가 `ConsumeKafka`로 표시된다. 과거 문서나 예시에서 보이던 `PublishKafka_2_6`, `ConsumeKafka_2_6`는 구버전 NiFi 1.x 계열 명칭이다. 이번 Week 3 실습에서는 NiFi가 Kafka로 전송만 수행하므로 `PublishKafka`만 사용하고, `ConsumeKafka`는 사용하지 않는다.

`PG-5: Kafka Publishing` 내부:

```
Input Port [valid-data] ──→ PublishKafka
                                │
                                ├── (success) → LogAttribute [전송성공]
                                └── (failure) → RetryFlowFile → PublishKafka
                                                    │
                                                    └── (retries exhausted) → PublishKafka [DLQ 토픽]

Input Port [invalid-data] ──→ PublishKafka [DLQ 토픽]
```

### 4-7. PublishKafka 프로세서 설정 — 정상 데이터

| 속성 | 값 | 설명 |
|------|-----|------|
| Kafka Brokers | `kafka-1:9092,kafka-2:9092,kafka-3:9092` | 3-브로커 클러스터 |
| Topic Name | `${kafka.topic}` | Attribute에서 동적 결정 |
| Use Transactions | `true` | Exactly-once 보장 |
| Delivery Guarantee | `Guarantee Replicated Delivery` | acks=all 동등 |
| Message Key Field | `${kafka.key}` | user_id 기반 파티션 키 |
| Compression Type | `lz4` | |
| Max Request Size | `1 MB` | |

### 4-8. PublishKafka 프로세서 설정 — DLQ

| 속성 | 값 | 설명 |
|------|-----|------|
| Kafka Brokers | `kafka-1:9092,kafka-2:9092,kafka-3:9092` | |
| Topic Name | `nexuspay.events.dlq` | 고정 DLQ 토픽 |
| Delivery Guarantee | `Guarantee Replicated Delivery` | |
| Compression Type | `lz4` | |

### 4-9. 전체 연동 테스트

```bash
# 1) 모든 프로세서 그룹 시작 (NiFi UI)

# 2) 데이터 소스 활성화
# API: 자동 (30초 주기)
# CSV: 파일 생성
python scripts/nifi/csv_settlement_generator.py -n 2 -r 30 -i 15
# DB: 레코드 변경
docker exec lab-postgres psql -U pipeline -d pipeline_db -c "
  UPDATE customers SET tier = 'GOLD' WHERE user_id BETWEEN 1010 AND 1015;
"

# 3) Kafka 토픽에 메시지 도착 확인
docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka-1:9092 \
  --topic nexuspay.events.ingested \
  --from-beginning \
  --max-messages 5 \
  --property print.key=true \
  --property key.separator=" | "

# 4) 소스별 메시지 확인
echo "=== 소스별 메시지 수 ==="
docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka-1:9092 \
  --topic nexuspay.events.ingested \
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
  --topic nexuspay.events.dlq \
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
cat > data/nifi/settlement/settlement_bad_data.csv << 'EOF'
settlement_id,batch_id,merchant_id,settlement_type,gross_amount,fee_amount,net_amount,currency,tx_count,settlement_date,created_at,status
,,MCH-999,INVALID_TYPE,not_a_number,abc,def,,0,,2026-04-01T00:00:00Z,UNKNOWN
STL-BAD-002,,,,,,,,,,,
EOF

# NiFi가 이 파일을 수집 → ConvertRecord 또는 ValidateRecord에서 실패 → DLQ로 라우팅
# 잠시 후 DLQ 토픽 확인
sleep 30
docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka-1:9092 \
  --topic nexuspay.events.dlq \
  --from-beginning \
  --timeout-ms 5000
```

**Day 4 완료 기준**: 세 소스 데이터가 표준 스키마로 통합되어 Kafka 토픽(`nexuspay.events.ingested`)에 도착, DLQ 라우팅 정상 작동, 소스별 메시지 수 확인.

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
   - Component Name: `PublishKafka` (Kafka 전송 이벤트만)
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
# Nexus Pay 데이터 계보 추적 가이드 — 감사 대응용

## 감사 시나리오: "결제 이벤트 PAY-00000042의 출처를 증명하시오"

### 추적 절차

1. **Kafka에서 메시지 확인**:
   - 토픽 `nexuspay.events.ingested`에서 해당 event_id 검색
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

EOF
```

### 5-5. 전체 파이프라인 종합 검증 스크립트

```bash
cat > scripts/verify_nifi_pipeline.sh << 'SCRIPT'
#!/bin/bash
# NiFi 다중 소스 수집 파이프라인 종합 검증

echo "============================================"
echo " Nexus Pay NiFi 파이프라인 종합 검증"
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
check "NiFi 웹 UI" "curl -skf https://localhost:8443/nifi/"
check "결제 API 시뮬레이터" "curl -sf http://localhost:5050/health"
check "PostgreSQL (고객 테이블)" "docker exec lab-postgres psql -U pipeline -d pipeline_db -c 'SELECT count(*) FROM customers;'"
check "Kafka 클러스터" "docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka-1:9092 --list"

echo ""
echo "[2. Kafka 토픽]"
check "nexuspay.events.ingested 토픽" "docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka-1:9092 --describe --topic nexuspay.events.ingested"
check "nexuspay.events.dlq 토픽" "docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka-1:9092 --describe --topic nexuspay.events.dlq"

echo ""
echo "[3. 데이터 흐름 검증]"
# API → Kafka 메시지 존재 확인
check "API 소스 메시지" "docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka-1:9092 --topic nexuspay.events.ingested --from-beginning --timeout-ms 5000 2>/dev/null | grep payment-api"
# CSV → Kafka 메시지 존재 확인
check "CSV 소스 메시지" "docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka-1:9092 --topic nexuspay.events.ingested --from-beginning --timeout-ms 5000 2>/dev/null | grep settlement-csv"
# DB → Kafka 메시지 존재 확인
check "DB 소스 메시지" "docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka-1:9092 --topic nexuspay.events.ingested --from-beginning --timeout-ms 5000 2>/dev/null | grep customer-db"

echo ""
echo "[4. 소스별 메시지 통계]"
docker exec lab-kafka-1 /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka-1:9092 \
  --topic nexuspay.events.ingested \
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
 Nexus Pay NiFi 파이프라인 종합 검증
 2026-04-05 17:00:00
============================================

[1. 인프라 서비스]
  NiFi 웹 UI                        : ✅ OK
  결제 API 시뮬레이터                  : ✅ OK
  PostgreSQL (고객 테이블)             : ✅ OK
  Kafka 클러스터                      : ✅ OK

[2. Kafka 토픽]
  nexuspay.events.ingested 토픽        : ✅ OK
  nexuspay.events.dlq 토픽             : ✅ OK

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
# Nexus Pay NiFi 데이터 수집 아키텍처

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
         nexuspay.events.ingested
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
- **대상 토픽**: `nexuspay.events.ingested` (RF=3, min.ISR=2)
- **DLQ 토픽**: `nexuspay.events.dlq`
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
| status | string | - | status | status | null |
| ingested_at | string | - | ingested_at | ingested_at | ingested_at |
| data_source | string | ✅ | "payment-api" | "settlement-csv" | "customer-db" |
| event_timestamp | string | ✅ | timestamp | settlement_date | updated_at |
| schema_version | string | ✅ | "1.0" | "1.0" | "1.0" |
| created_at | string | - | null | created_at | created_at |
| fee_amount | double | - | null | fee_amount | null |
| net_amount | double | - | null | net_amount | null |
| tx_count | int | - | null | tx_count | null |
| batch_id | string | - | null | batch_id | null |
| customer_name | string | - | null | null | name |
| customer_email | string | - | null | null | email |
| customer_phone | string | - | null | null | phone |
| customer_grade | string | - | null | null | grade |
| is_active | boolean | - | null | null | is_active |

## 운영 포트 맵

| 포트 | 서비스 |
|------|--------|
| 8080 | NiFi 웹 UI |
| 5050 | 결제 API 시뮬레이터 |
| 5432 | PostgreSQL |
| 30092~30094 | Kafka 브로커 1~3 |

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

현재 확인 기준:
- Day 2 완료: 확인됨
- Day 3 완료: `PG-2` 파일 수집 플로우 정상 작동, `PG-3` DB 증분 수집 검증 완료, `PG-1`·`PG-2`·`PG-3` 세 소스가 `PG-4`의 `api-in-check`·`file-in-check`·`db-in-check`로 동시에 유입되는 것까지 확인됨.

| # | 산출물 | 완료 |
|---|--------|------|
| 1 | docs/nifi/nifi-concepts.md (NiFi 핵심 개념 정리) | ☑ |
| 2 | config/nifi/process-group-design.md (프로세서 그룹 설계) | ☑ |
| 3 | scripts/nifi/api_payment_simulator.py (결제 API 시뮬레이터) | ☑ |
| 4 | scripts/nifi/csv_settlement_generator.py (정산 CSV 생성기) | ☑ |
| 5 | scripts/nifi/init-customers.sql (고객 마스터 테이블) | ☑ |
| 6 | config/nifi/jolt-spec-api-payment.json (API Jolt 스펙) | ☑ |
| 7 | config/nifi/jolt-spec-file-settlement.json (CSV Jolt 스펙) | ☐ |
| 8 | config/nifi/jolt-spec-db-customer.json (DB Jolt 스펙) | ☐ |
| 9 | config/nifi/nexuspay-standard-schema.avsc (표준 Avro 스키마) | ☐ |
| 10 | scripts/nifi/measure_api_throughput.sh (API 처리량 측정 스크립트) | ☑ |
| 11 | scripts/verify_nifi_pipeline.sh (종합 검증 스크립트) | ☐ |
| 12 | docs/provenance-audit-guide.md (Provenance 감사 추적 가이드) | ☐ |
| 13 | docs/nifi-monitoring-guide.md (NiFi 모니터링 가이드) | ☐ |
| 14 | docs/nifi-architecture.md (데이터 흐름 아키텍처 문서) | ☐ |
| 15 | docker-compose.yml 업데이트 (payment-api, NiFi 볼륨) | ☑ |
| 16 | NiFi 플로우 (5개 프로세서 그룹 구성 완료) | ☑ |
| 17 | Git 커밋 | ☐ |

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

Week 4에서는 Flink를 활용한 실시간 스트림 처리를 구축한다. 이번 주에 NiFi가 Kafka에 전달한 `nexuspay.events.ingested` 토픽의 데이터를 Flink가 소비하여 윈도우 집계(Window Aggregation), Watermark 기반 이벤트 타임 처리, 실시간 이상거래 탐지 로직을 구현한다. NiFi(수집) → Kafka(버퍼) → Flink(처리)로 이어지는 실시간 파이프라인의 핵심 구간이 완성된다.
