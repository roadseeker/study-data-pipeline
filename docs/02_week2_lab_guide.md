# Week 2: 수집 — Kafka 심화

**기간**: 5일 (월~금, 풀타임 40시간)
**주제**: 토픽 설계, 파티션 전략, 컨슈머 그룹, 오프셋 관리, 복제 설정
**산출물**: Kafka 운영 가이드 + Nexus Pay 거래 파이프라인 + 장애 복원력 검증 보고서
**전제 조건**: Week 1 환경 정상 기동 (`bash scripts/healthcheck-all.sh` 전체 통과)

---

## 수행 시나리오

### 배경 설정

Nexus Pay PoC 환경 구축이 완료되었다. Nexus Pay는 안정적이고 확장 가능한 결제 플랫폼을 목표로 하는 MSA 기반 Payment Service이며, 이제 CTO가 구체적인 질문을 던진다.

> "현재 일 평균 거래 50만 건인데, 1년 내 200만 건까지 늘어날 겁니다. 결제·이체·출금 이벤트를 실시간으로 수집하되, 이상거래 탐지 팀과 정산 팀이 **서로 간섭 없이** 같은 데이터를 소비해야 합니다. Kafka로 이걸 어떻게 설계해야 합니까?"

컨설턴트이자 데이터 파이프라인 담당 역할로서 이 요구사항을 충족하는 Kafka 토픽 아키텍처를 설계하고, 파티션 전략·컨슈머 그룹 분리·오프셋 관리·장애 복원력까지 검증하는 것이 이번 주의 과제다.

### 목표

1. 비즈니스 요구사항 기반 토픽 설계 전략 수립 및 구현
2. 파티션 키 설계로 메시지 순서 보장과 부하 분산 달성
3. 컨슈머 그룹 분리를 통한 독립적 데이터 소비 구조 구현
4. 수동 오프셋 커밋으로 최소 한 번(at-least-once) 처리 보장
5. 멀티 브로커 환경에서 복제 설정 및 장애 복원력 검증

### 일정 개요

| 일차 | 주제 | 핵심 작업 |
|------|------|----------|
| Day 1 | 토픽 설계 전략 | 비즈니스 이벤트 모델링, 토픽 명명 규칙, 파티션 수 산정 |
| Day 2 | 파티션 키 설계 + 프로듀서 구현 | 키 기반 라우팅, 거래 데이터 생성기 구현 |
| Day 3 | 컨슈머 그룹 + 오프셋 관리 | 다중 컨슈머 그룹, 수동 커밋, 리밸런싱 관찰 |
| Day 4 | 멀티 브로커 + 복제 | 3-브로커 클러스터 구성, 복제 팩터, ISR 관리 |
| Day 5 | 장애 시나리오 + 운영 가이드 문서화 | 브로커 장애 복구, 파티션 리더 선출, 운영 가이드 작성 |

---

## Day 1: 토픽 설계 전략

### 1-1. Nexus Pay 이벤트 모델 정의

Nexus Pay 거래 시스템에서 발생하는 핵심 이벤트를 정의한다.

```
┌─────────────────────────────────────────────────────┐
│                 Nexus Pay 이벤트 흐름                  │
│                                                       │
│  [결제 서비스] ──→ nexuspay.transactions.payment        │
│  [이체 서비스] ──→ nexuspay.transactions.transfer       │
│  [출금 서비스] ──→ nexuspay.transactions.withdrawal     │
│                        │                              │
│                        ▼                              │
│         ┌──────────────┴──────────────┐               │
│         │                             │               │
│  [이상거래 탐지팀]              [정산팀]               │
│  consumer-group:                consumer-group:        │
│   fraud-detection                settlement            │
│         │                             │               │
│         ▼                             ▼               │
│  실시간 알림·차단              일별 정산 집계           │
└─────────────────────────────────────────────────────┘
```

### 1-2. 토픽 명명 규칙 수립

컨설팅 현장에서 통용되는 토픽 명명 규칙을 정의한다. 이 규칙은 이후 모든 실습과 포트폴리오에 일관되게 적용한다.

```
규칙: <도메인>.<엔티티>.<이벤트유형>

예시:
  nexuspay.transactions.payment      — 결제 이벤트
  nexuspay.transactions.transfer     — 이체 이벤트
  nexuspay.transactions.withdrawal   — 출금 이벤트
  nexuspay.transactions.dlq          — 처리 실패 메시지 (Dead Letter Queue)
  nexuspay.users.signup              — 회원가입 이벤트
  nexuspay.users.profile-update      — 프로필 변경 이벤트
```

명명 규칙 문서를 작성한다:

```bash
cat > config/kafka/topic-naming-convention.md << 'EOF'
# Nexus Pay Kafka 토픽 명명 규칙

## 형식
`<도메인>.<엔티티>.<이벤트유형>`

## 규칙
- 소문자 + 점(.) 구분자 사용
- 단어 내 구분자는 하이픈(-) 사용
- 약어 금지 (transaction → transactions, ✗ tx)
- DLQ(Dead Letter Queue)는 원본 토픽명 + `.dlq` 접미사

## 등록 토픽 목록

| 토픽명 | 파티션 | 보존 기간 | 용도 |
|--------|--------|----------|------|
| nexuspay.transactions.payment | 6 | 7일 | 결제 이벤트 |
| nexuspay.transactions.transfer | 6 | 7일 | 이체 이벤트 |
| nexuspay.transactions.withdrawal | 4 | 7일 | 출금 이벤트 |
| nexuspay.transactions.dlq | 2 | 30일 | 처리 실패 메시지 |
| nexuspay.users.signup | 2 | 7일 | 회원가입 이벤트 |

EOF
```

### 1-3. 파티션 수 산정 기준

파티션 수는 목표 처리량과 컨슈머 병렬성에 의해 결정된다. Nexus Pay 시나리오 기준으로 산정 로직을 수립한다.

```bash
cat > scripts/partition-calculator.sh << 'SCRIPT'
#!/bin/bash
# Nexus Pay 파티션 수 산정 스크립트
#
# 공식: 파티션 수 = max(목표처리량 / 단일파티션처리량, 컨슈머수)
#
# Nexus Pay 기준:
#   - 피크 시간대 초당 메시지: 약 50 msg/s (일 200만 건 / 11시간 영업 기준)
#   - 단일 파티션 처리 가능량: ~10 msg/s (보수적 추정, 직렬화·네트워크 포함)
#   - 이상거래 탐지 컨슈머: 3대
#   - 정산 컨슈머: 2대

PEAK_MSG_PER_SEC=50
SINGLE_PARTITION_THROUGHPUT=10
FRAUD_CONSUMERS=3
SETTLEMENT_CONSUMERS=2

THROUGHPUT_PARTITIONS=$((PEAK_MSG_PER_SEC / SINGLE_PARTITION_THROUGHPUT))
MAX_CONSUMERS=$((FRAUD_CONSUMERS > SETTLEMENT_CONSUMERS ? FRAUD_CONSUMERS : SETTLEMENT_CONSUMERS))

RECOMMENDED=$((THROUGHPUT_PARTITIONS > MAX_CONSUMERS ? THROUGHPUT_PARTITIONS : MAX_CONSUMERS))
# 여유 계수 1.5배 적용 후 짝수로 올림
FINAL=$(( (RECOMMENDED * 3 / 2 + 1) / 2 * 2 ))

echo "============================================"
echo " Nexus Pay 파티션 수 산정 결과"
echo "============================================"
echo "  피크 처리량 기준 : ${THROUGHPUT_PARTITIONS} 파티션"
echo "  컨슈머 병렬성 기준 : ${MAX_CONSUMERS} 파티션"
echo "  여유 계수(1.5x) 적용 : ${FINAL} 파티션"
echo "============================================"
echo "  → 권장 파티션 수: ${FINAL}"
echo ""
echo "  참고: 결제·이체는 트래픽 많음 → ${FINAL} 파티션"
echo "        출금은 상대적 저빈도 → $((FINAL * 2 / 3)) 파티션"
echo "        DLQ·이벤트 보조 → 2 파티션"
SCRIPT

chmod +x scripts/partition-calculator.sh
bash scripts/partition-calculator.sh
```

기대 출력:
```
============================================
 Nexus Pay 파티션 수 산정 결과
============================================
  피크 처리량 기준 : 5 파티션
  컨슈머 병렬성 기준 : 3 파티션
  여유 계수(1.5x) 적용 : 8 파티션
============================================
  → 권장 파티션 수: 8
  
  참고: 결제·이체는 트래픽 많음 → 8 파티션
        출금은 상대적 저빈도 → 5 파티션
        DLQ·이벤트 보조 → 2 파티션
```

> **실무 참고**: 실제 컨설팅에서는 정확한 벤치마크 없이 피크 처리량을 보수적으로 추정한 뒤 여유 계수를 곱하는 방식이 일반적이다. 파티션 수는 늘리기는 쉽지만 줄이기는 불가능하므로 보수적 시작이 원칙이다.

> **PoC 환경 조정**: 산정 스크립트의 권장값은 8 파티션이지만, PoC 환경에서는 리소스를 고려하여 결제·이체 토픽은 **6 파티션**, 출금 토픽은 **4 파티션**으로 축소 적용한다. 운영 환경에서는 산정 결과에 따라 조정할 것.

### 1-4. 토픽 생성

Week 1에서 만든 단일 브로커 환경에서 토픽을 생성한다 (Day 4에서 멀티 브로커로 확장 시 재생성).

```bash
# 기존 테스트 토픽 정리
docker exec lab-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --delete --topic test-transactions 2>/dev/null

docker exec lab-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --delete --topic nexuspay-transactions 2>/dev/null

# 거래 토픽 생성
for TOPIC in nexuspay.transactions.payment nexuspay.transactions.transfer; do
  docker exec lab-kafka /opt/kafka/bin/kafka-topics.sh \
    --bootstrap-server localhost:9092 \
    --create --topic "$TOPIC" \
    --partitions 6 \
    --replication-factor 1 \
    --config retention.ms=604800000 \
    --config cleanup.policy=delete
  echo "Created: $TOPIC"
done

docker exec lab-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --create --topic nexuspay.transactions.withdrawal \
  --partitions 4 \
  --replication-factor 1 \
  --config retention.ms=604800000

# DLQ 전략:
#   - nexuspay.transactions.dlq : 프로듀서/컨슈머 처리 실패 메시지 (Week 2 프로듀서·컨슈머 단계)
#   - nexuspay.events.dlq       : NiFi 수집 품질 검증 실패 메시지 (Week 3에서 별도 생성)
#   두 DLQ는 용도가 다르므로 분리 운영한다.
docker exec lab-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --create --topic nexuspay.transactions.dlq \
  --partitions 2 \
  --replication-factor 1 \
  --config retention.ms=2592000000

# 전체 토픽 확인
docker exec lab-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --list

# 상세 확인
docker exec lab-kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --describe --topic nexuspay.transactions.payment
```

### 1-5. 토픽 설정 항목 정리

```bash
cat > config/kafka/topic-configs.md << 'EOF'
# Nexus Pay Kafka 토픽 설정 가이드

## 핵심 설정 항목

| 설정 | 기본값 | Nexus Pay 설정 | 설명 |
|------|--------|------------|------|
| retention.ms | 604800000 (7일) | 거래: 7일, DLQ: 30일 | 메시지 보존 기간 |
| cleanup.policy | delete | delete | 만료 메시지 처리 방식 |
| min.insync.replicas | 1 | 2 (멀티 브로커 시) | 최소 동기화 복제본 수 |
| max.message.bytes | 1048576 (1MB) | 1MB | 단일 메시지 최대 크기 |
| compression.type | producer | lz4 | 압축 알고리즘 |
| segment.bytes | 1073741824 (1GB) | 기본값 | 로그 세그먼트 크기 |

## retention.ms 결정 기준
- 실시간 처리 토픽: 컨슈머 최대 지연시간 × 3 (안전 마진)
- DLQ: 수동 검토 주기 × 2 (최소 14일 권장)
- 감사 로그: 규정 준수 기간 (금융: 최소 5년 — 별도 저장소 이관 필요)

EOF
```

**Day 1 완료 기준**: 토픽 명명 규칙 문서 작성, 파티션 산정 스크립트 작성·실행, 5개 토픽 생성 확인, 토픽 설정 가이드 작성.

---

## Day 2: 파티션 키 설계 + 프로듀서 구현

### 2-1. 파티션 키 설계 원칙

파티션 키는 두 가지 목적을 동시에 만족해야 한다: **같은 사용자의 거래는 순서 보장** + **파티션 간 부하 균등 분산**.

```
파티션 키 선택 기준:

  ✅ user_id — 같은 사용자의 거래가 동일 파티션에 배치 → 순서 보장
  ✗ tx_id   — 모든 메시지가 다른 파티션 → 순서 의미 없음
  ✗ tx_type — 카디널리티 3개 → 3개 파티션만 사용, 나머지 유휴
  ✗ 키 없음 — Round-robin → 순서 보장 불가

Nexus Pay 결정: user_id를 파티션 키로 사용
  → 이상거래 탐지 시 동일 사용자 거래 순서가 보장됨
  → user_id 카디널리티 ~10만 → 6개 파티션에 균등 분산 기대
```

### 2-2. 거래 데이터 생성기 (Python 프로듀서)

실제 금융 거래 패턴을 시뮬레이션하는 프로듀서를 구현한다.

```bash
# 의존성 설치 (호스트 환경)
pip install confluent-kafka faker --break-system-packages
```

```python
# scripts/producer_nexuspay.py
"""
Nexus Pay 거래 데이터 프로듀서
- user_id 기반 파티션 키로 사용자별 순서 보장
- 결제·이체·출금 이벤트를 가중치 기반으로 생성
- 이상거래 패턴 10% 확률 포함 (이후 Flink 탐지 실습 연계)
"""

import json
import time
import random
import argparse
from datetime import datetime, timezone
from confluent_kafka import Producer

# ── 설정 ──
BROKER = "localhost:29092"
TOPICS = {
    "PAYMENT":    "nexuspay.transactions.payment",
    "TRANSFER":   "nexuspay.transactions.transfer",
    "WITHDRAWAL": "nexuspay.transactions.withdrawal",
}
TX_WEIGHTS = [("PAYMENT", 50), ("TRANSFER", 30), ("WITHDRAWAL", 20)]

# ── 사용자 풀 (1,000명) ──
USER_IDS = list(range(1001, 2001))

# ── 통화별 금액 범위 ──
AMOUNT_RANGES = {
    "KRW": (1000, 10000000),      # 1천원 ~ 1천만원
    "USD": (1, 10000),             # $1 ~ $10,000
    "JPY": (100, 1000000),         # ¥100 ~ ¥1,000,000
}

def create_transaction(seq: int) -> dict:
    """거래 이벤트 1건 생성"""
    # 거래 유형 가중치 선택
    tx_type = random.choices(
        [t[0] for t in TX_WEIGHTS],
        weights=[t[1] for t in TX_WEIGHTS],
        k=1
    )[0]

    user_id = random.choice(USER_IDS)
    currency = random.choices(["KRW", "USD", "JPY"], weights=[70, 20, 10], k=1)[0]
    lo, hi = AMOUNT_RANGES[currency]
    amount = round(random.uniform(lo, hi), 2)

    # 이상거래 패턴: 10% 확률로 고액 거래 생성
    is_suspicious = random.random() < 0.10
    if is_suspicious:
        amount = round(amount * random.uniform(5.0, 20.0), 2)

    return {
        "tx_id": f"TX-{seq:08d}",
        "user_id": user_id,
        "amount": amount,
        "currency": currency,
        "tx_type": tx_type,
        "status": "PENDING",
        "is_suspicious": is_suspicious,
        "merchant_id": f"MCH-{random.randint(100, 999)}",
        "channel": random.choice(["APP", "WEB", "ATM", "POS"]),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def delivery_report(err, msg):
    """메시지 전송 콜백"""
    if err:
        print(f"  ❌ 전송 실패: {err}")
    else:
        print(
            f"  ✅ topic={msg.topic()} partition={msg.partition()} "
            f"offset={msg.offset()} key={msg.key().decode()}"
        )


def main():
    parser = argparse.ArgumentParser(description="Nexus Pay 거래 프로듀서")
    parser.add_argument("-n", "--count", type=int, default=100, help="생성할 거래 수")
    parser.add_argument("-d", "--delay", type=float, default=0.1, help="메시지 간 간격(초)")
    parser.add_argument("--verbose", action="store_true", help="전송 상세 출력")
    args = parser.parse_args()

    producer = Producer({
        "bootstrap.servers": BROKER,
        "client.id": "nexuspay-producer",
        "acks": "all",                    # 모든 ISR 복제본 확인
        "retries": 3,                     # 실패 시 재시도
        "linger.ms": 5,                   # 배치 전송 대기 시간
        "compression.type": "lz4",        # 압축
        "enable.idempotence": True,       # 멱등성 보장
    })

    print(f"Nexus Pay 거래 프로듀서 시작 — {args.count}건 전송")
    print(f"브로커: {BROKER}")
    print("=" * 60)

    stats = {"payment": 0, "transfer": 0, "withdrawal": 0, "suspicious": 0}

    for i in range(1, args.count + 1):
        tx = create_transaction(i)
        topic = TOPICS[tx["tx_type"]]
        key = str(tx["user_id"])          # 파티션 키 = user_id
        value = json.dumps(tx, ensure_ascii=False)

        producer.produce(
            topic=topic,
            key=key.encode("utf-8"),
            value=value.encode("utf-8"),
            callback=delivery_report if args.verbose else None,
        )

        stats[tx["tx_type"]] += 1
        if tx["is_suspicious"]:
            stats["suspicious"] += 1

        if i % 50 == 0:
            producer.flush()
            print(f"  [{i}/{args.count}] 전송 중...")

        time.sleep(args.delay)

    producer.flush()

    print("=" * 60)
    print("전송 완료!")
    print(f"  결제: {stats['payment']}건")
    print(f"  이체: {stats['transfer']}건")
    print(f"  출금: {stats['withdrawal']}건")
    print(f"  이상거래 플래그: {stats['suspicious']}건")


if __name__ == "__main__":
    main()
```

### 2-3. 프로듀서 실행 및 파티션 분포 확인

```bash
# 거래 100건 생성 (상세 모드)
python scripts/producer_nexuspay.py -n 100 --delay 0.05 --verbose

# 파티션별 메시지 분포 확인
echo "=== nexuspay.transactions.payment 파티션별 오프셋 ==="
docker exec lab-kafka /opt/kafka/bin/kafka-run-class.sh \
  kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 \
  --topic nexuspay.transactions.payment

echo ""
echo "=== nexuspay.transactions.transfer 파티션별 오프셋 ==="
docker exec lab-kafka /opt/kafka/bin/kafka-run-class.sh \
  kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 \
  --topic nexuspay.transactions.transfer

echo ""
echo "=== nexuspay.transactions.withdrawal 파티션별 오프셋 ==="
docker exec lab-kafka /opt/kafka/bin/kafka-run-class.sh \
  kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 \
  --topic nexuspay.transactions.withdrawal
```

### 2-4. 파티션 키 효과 검증 — 동일 사용자 순서 보장 확인

```python
# scripts/verify_partition_key.py
"""
동일 user_id가 동일 파티션에 배치되는지 검증
"""

import json
from confluent_kafka import Consumer, TopicPartition

BROKER = "localhost:29092"
TOPIC = "nexuspay.transactions.payment"

consumer = Consumer({
    "bootstrap.servers": BROKER,
    "group.id": "partition-key-verifier",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,
})

consumer.subscribe([TOPIC])

# user_id → 파티션 매핑 수집
user_partitions = {}
count = 0

print(f"토픽 '{TOPIC}'에서 메시지 읽는 중...")

while count < 200:
    msg = consumer.poll(timeout=2.0)
    if msg is None:
        break
    if msg.error():
        continue

    tx = json.loads(msg.value().decode("utf-8"))
    uid = tx["user_id"]
    partition = msg.partition()

    if uid not in user_partitions:
        user_partitions[uid] = set()
    user_partitions[uid].add(partition)
    count += 1

consumer.close()

# 검증: 각 user_id가 단일 파티션에만 배치되었는지 확인
violations = {uid: parts for uid, parts in user_partitions.items() if len(parts) > 1}

print(f"\n검증 결과:")
print(f"  수집 메시지: {count}건")
print(f"  고유 사용자: {len(user_partitions)}명")
print(f"  파티션 키 위반 사용자: {len(violations)}명")

if violations:
    print("\n⚠️  위반 사례:")
    for uid, parts in list(violations.items())[:5]:
        print(f"    user_id={uid} → 파티션 {parts}")
else:
    print("\n✅ 모든 사용자가 단일 파티션에 일관되게 배치됨 — 순서 보장 확인")

# 파티션별 사용자 수 분포
partition_user_counts = {}
for uid, parts in user_partitions.items():
    for p in parts:
        partition_user_counts[p] = partition_user_counts.get(p, 0) + 1

print(f"\n파티션별 사용자 분포:")
for p in sorted(partition_user_counts.keys()):
    bar = "█" * (partition_user_counts[p] // 2)
    print(f"  파티션 {p}: {partition_user_counts[p]:>4}명  {bar}")
```

```bash
python scripts/verify_partition_key.py
```

기대 출력:
```
검증 결과:
  수집 메시지: 100건
  고유 사용자: 78명
  파티션 키 위반 사용자: 0명

✅ 모든 사용자가 단일 파티션에 일관되게 배치됨 — 순서 보장 확인

파티션별 사용자 분포:
  파티션 0:   14명  ███████
  파티션 1:   12명  ██████
  파티션 2:   13명  ██████
  파티션 3:   11명  █████
  파티션 4:   15명  ███████
  파티션 5:   13명  ██████
```

**Day 2 완료 기준**: 프로듀서로 거래 100건 전송 완료, 파티션별 분포 확인, 동일 user_id → 동일 파티션 배치 검증 통과.

---

## Day 3: 컨슈머 그룹 + 오프셋 관리

### 3-1. 다중 컨슈머 그룹 설계

Nexus Pay 시나리오에서 두 팀이 **같은 토픽을 독립적으로** 소비해야 한다. Kafka의 컨슈머 그룹이 이를 해결한다.

```
nexuspay.transactions.payment (6개 파티션)
        │
        ├──→ [컨슈머 그룹: fraud-detection]
        │       ├── consumer-1 → P0, P1
        │       ├── consumer-2 → P2, P3
        │       └── consumer-3 → P4, P5
        │
        └──→ [컨슈머 그룹: settlement]
                ├── consumer-1 → P0, P1, P2
                └── consumer-2 → P3, P4, P5

각 그룹은 독립적으로 모든 메시지를 수신한다.
같은 그룹 내에서는 파티션이 분배되어 병렬 처리한다.
```

### 3-2. 이상거래 탐지 컨슈머 구현 (fraud-detection 그룹)

```python
# scripts/consumer_fraud_detection.py
"""
이상거래 탐지 컨슈머
- fraud-detection 그룹으로 payment 토픽 소비
- is_suspicious 플래그 또는 고액 거래 탐지
- 수동 오프셋 커밋으로 메시지 유실 방지
"""

import json
import signal
import sys
import argparse
from confluent_kafka import Consumer, KafkaError

BROKER = "localhost:29092"
TOPICS = [
    "nexuspay.transactions.payment",
    "nexuspay.transactions.transfer",
    "nexuspay.transactions.withdrawal",
]

# 이상거래 판단 기준
THRESHOLDS = {
    "KRW": 50_000_000,   # 5천만원 이상
    "USD": 50_000,        # $50,000 이상
    "JPY": 5_000_000,     # ¥5,000,000 이상
}

running = True

def signal_handler(sig, frame):
    global running
    print("\n종료 신호 수신 — 정리 중...")
    running = False

signal.signal(signal.SIGINT, signal_handler)


def detect_fraud(tx: dict) -> dict | None:
    """이상거래 탐지 로직"""
    reasons = []

    # 규칙 1: 프로듀서 플래그
    if tx.get("is_suspicious"):
        reasons.append("프로듀서 이상 플래그")

    # 규칙 2: 고액 거래
    threshold = THRESHOLDS.get(tx["currency"], float("inf"))
    if tx["amount"] > threshold:
        reasons.append(f"고액 거래 ({tx['currency']} {tx['amount']:,.0f})")

    # 규칙 3: ATM 출금 + 고액
    if tx["tx_type"] == "withdrawal" and tx["channel"] == "ATM" and tx["amount"] > threshold * 0.5:
        reasons.append("ATM 고액 출금")

    if reasons:
        return {
            "tx_id": tx["tx_id"],
            "user_id": tx["user_id"],
            "amount": tx["amount"],
            "currency": tx["currency"],
            "reasons": reasons,
            "risk_level": "HIGH" if len(reasons) >= 2 else "MEDIUM",
        }
    return None


def main():
    parser = argparse.ArgumentParser(description="이상거래 탐지 컨슈머")
    parser.add_argument("--instance", type=int, default=1, help="인스턴스 번호")
    args = parser.parse_args()

    consumer = Consumer({
        "bootstrap.servers": BROKER,
        "group.id": "fraud-detection",
        "client.id": f"fraud-consumer-{args.instance}",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,          # 수동 커밋!
        "max.poll.interval.ms": 300000,
        "session.timeout.ms": 30000,
    })

    consumer.subscribe(TOPICS)

    print(f"[이상거래 탐지] 인스턴스 #{args.instance} 시작")
    print(f"  그룹: fraud-detection")
    print(f"  토픽: {', '.join(TOPICS)}")
    print("=" * 60)

    processed = 0
    alerts = 0
    batch = []

    while running:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue

        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            print(f"  ❌ 에러: {msg.error()}")
            continue

        tx = json.loads(msg.value().decode("utf-8"))
        processed += 1

        # 이상거래 탐지
        alert = detect_fraud(tx)
        if alert:
            alerts += 1
            print(
                f"  🚨 [{alert['risk_level']}] {alert['tx_id']} "
                f"user={alert['user_id']} "
                f"{alert['currency']} {alert['amount']:,.0f} "
                f"— {', '.join(alert['reasons'])}"
            )

        # 10건마다 오프셋 수동 커밋
        batch.append(msg)
        if len(batch) >= 10:
            consumer.commit(asynchronous=False)
            batch.clear()

        if processed % 50 == 0:
            print(f"  📊 처리: {processed}건 / 알림: {alerts}건")

    # 종료 전 마지막 커밋
    if batch:
        consumer.commit(asynchronous=False)

    consumer.close()
    print(f"\n최종 결과: 처리 {processed}건, 알림 {alerts}건")


if __name__ == "__main__":
    main()
```

### 3-3. 정산 컨슈머 구현 (settlement 그룹)

```python
# scripts/consumer_settlement.py
"""
정산 컨슈머
- settlement 그룹으로 모든 거래 토픽 소비
- 통화별·유형별 일일 정산 집계
- 수동 오프셋 커밋
"""

import json
import signal
import sys
from collections import defaultdict
from confluent_kafka import Consumer, KafkaError

BROKER = "localhost:29092"
TOPICS = [
    "nexuspay.transactions.payment",
    "nexuspay.transactions.transfer",
    "nexuspay.transactions.withdrawal",
]

running = True

def signal_handler(sig, frame):
    global running
    running = False

signal.signal(signal.SIGINT, signal_handler)


def main():
    consumer = Consumer({
        "bootstrap.servers": BROKER,
        "group.id": "settlement",
        "client.id": "settlement-consumer-1",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    })

    consumer.subscribe(TOPICS)

    print("[정산 집계] 컨슈머 시작")
    print(f"  그룹: settlement")
    print("=" * 60)

    # 집계 구조: {currency: {tx_type: {"count": N, "total": X}}}
    ledger = defaultdict(lambda: defaultdict(lambda: {"count": 0, "total": 0.0}))
    processed = 0

    while running:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            continue

        tx = json.loads(msg.value().decode("utf-8"))
        processed += 1

        ledger[tx["currency"]][tx["tx_type"]]["count"] += 1
        ledger[tx["currency"]][tx["tx_type"]]["total"] += tx["amount"]

        if processed % 10 == 0:
            consumer.commit(asynchronous=False)

        if processed % 50 == 0:
            print_summary(ledger, processed)

    # 종료 전 최종 집계 출력
    consumer.commit(asynchronous=False)
    consumer.close()
    print("\n" + "=" * 60)
    print("최종 정산 집계")
    print_summary(ledger, processed)


def print_summary(ledger, processed):
    """정산 집계 출력"""
    print(f"\n  📊 정산 중간 집계 ({processed}건 처리)")
    print(f"  {'통화':<6} {'유형':<12} {'건수':>8} {'합계':>18}")
    print(f"  {'-'*48}")
    for currency in sorted(ledger.keys()):
        for tx_type in sorted(ledger[currency].keys()):
            entry = ledger[currency][tx_type]
            print(
                f"  {currency:<6} {tx_type:<12} {entry['count']:>8,} "
                f"{entry['total']:>18,.0f}"
            )


if __name__ == "__main__":
    main()
```

### 3-4. 다중 컨슈머 그룹 동시 실행 테스트

3개 터미널을 열어 동시에 실행한다.

```bash
# 터미널 1: 이상거래 탐지 컨슈머
python scripts/consumer_fraud_detection.py --instance 1

# 터미널 2: 정산 컨슈머
python scripts/consumer_settlement.py

# 터미널 3: 프로듀서 — 새 거래 500건 생성
python scripts/producer_nexuspay.py -n 500 --delay 0.02
```

### 3-5. 컨슈머 그룹 상태 확인

```bash
# 등록된 컨슈머 그룹 목록
docker exec lab-kafka /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 --list

# fraud-detection 그룹 상세 — 파티션 할당·오프셋·지연(lag) 확인
docker exec lab-kafka /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe --group fraud-detection

# settlement 그룹 상세
docker exec lab-kafka /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe --group settlement
```

기대 출력 (fraud-detection):
```
GROUP            TOPIC                            PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
fraud-detection  nexuspay.transactions.payment      0          42              42              0
fraud-detection  nexuspay.transactions.payment      1          38              38              0
fraud-detection  nexuspay.transactions.payment      2          45              45              0
...
```

### 3-6. 리밸런싱 관찰 실습

컨슈머 인스턴스 추가·제거 시 파티션 재할당을 관찰한다.

```bash
# 터미널 1: 이미 실행 중인 fraud 컨슈머 인스턴스 1

# 터미널 4: 두 번째 인스턴스 추가 — 리밸런싱 발생
python scripts/consumer_fraud_detection.py --instance 2

# 양쪽 터미널에서 "리밸런싱" 로그 관찰
# → 파티션이 2개 인스턴스로 재분배됨

# 터미널 4 종료 (Ctrl+C) → 다시 인스턴스 1로 파티션 복귀
```

### 3-7. 오프셋 리셋 실습

컨슈머 그룹의 오프셋을 수동으로 리셋하여 메시지를 재처리하는 시나리오를 실습한다.

```bash
# 현재 오프셋 확인
docker exec lab-kafka /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe --group fraud-detection

# 모든 컨슈머 중지 후 → 오프셋을 처음으로 리셋
docker exec lab-kafka /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group fraud-detection \
  --topic nexuspay.transactions.payment \
  --reset-offsets --to-earliest \
  --execute

# 다시 컨슈머 실행 → 모든 메시지 재처리 확인
python scripts/consumer_fraud_detection.py --instance 1
```

**Day 3 완료 기준**: 두 컨슈머 그룹이 동시에 같은 메시지를 독립 소비하는 것 확인, 수동 오프셋 커밋 동작 확인, 리밸런싱 관찰, 오프셋 리셋 후 재처리 확인.

---

## Day 4: 멀티 브로커 + 복제

### 4-1. 3-브로커 클러스터로 확장

단일 브로커 환경을 3-브로커 클러스터로 확장한다. docker-compose.yml에서 기존 `kafka` 서비스를 교체한다.

```yaml
  # ──────────────────────────────────────
  # Kafka 3-브로커 클러스터 (KRaft)
  # ──────────────────────────────────────
  kafka-1:
    image: apache/kafka:3.7.0
    container_name: lab-kafka-1
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093,EXTERNAL://0.0.0.0:29092
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka-1:9092,EXTERNAL://localhost:29092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT,EXTERNAL:PLAINTEXT
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka-1:9093,2@kafka-2:9093,3@kafka-3:9093
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 3
      KAFKA_DEFAULT_REPLICATION_FACTOR: 3
      KAFKA_MIN_INSYNC_REPLICAS: 2
      KAFKA_LOG_RETENTION_HOURS: 168
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "false"
      CLUSTER_ID: "MkU3OEVBNTcwNTJENDM2Qk"  # kafka-storage.sh random-uuid 로 생성한 유효 ID
    ports:
      - "29092:29092"
    networks:
      - pipeline-net
    healthcheck:
      test: ["CMD-SHELL", "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list || exit 1"]
      interval: 15s
      timeout: 10s
      retries: 10
      start_period: 30s

  kafka-2:
    image: apache/kafka:3.7.0
    container_name: lab-kafka-2
    environment:
      KAFKA_NODE_ID: 2
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093,EXTERNAL://0.0.0.0:29093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka-2:9092,EXTERNAL://localhost:29093
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT,EXTERNAL:PLAINTEXT
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka-1:9093,2@kafka-2:9093,3@kafka-3:9093
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 3
      KAFKA_DEFAULT_REPLICATION_FACTOR: 3
      KAFKA_MIN_INSYNC_REPLICAS: 2
      KAFKA_LOG_RETENTION_HOURS: 168
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "false"
      CLUSTER_ID: "MkU3OEVBNTcwNTJENDM2Qk"  # kafka-storage.sh random-uuid 로 생성한 유효 ID
    ports:
      - "29093:29093"
    networks:
      - pipeline-net
    healthcheck:
      test: ["CMD-SHELL", "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list || exit 1"]
      interval: 15s
      timeout: 10s
      retries: 10
      start_period: 30s

  kafka-3:
    image: apache/kafka:3.7.0
    container_name: lab-kafka-3
    environment:
      KAFKA_NODE_ID: 3
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093,EXTERNAL://0.0.0.0:29094
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka-3:9092,EXTERNAL://localhost:29094
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT,EXTERNAL:PLAINTEXT
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka-1:9093,2@kafka-2:9093,3@kafka-3:9093
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 3
      KAFKA_DEFAULT_REPLICATION_FACTOR: 3
      KAFKA_MIN_INSYNC_REPLICAS: 2
      KAFKA_LOG_RETENTION_HOURS: 168
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "false"
      CLUSTER_ID: "MkU3OEVBNTcwNTJENDM2Qk"  # kafka-storage.sh random-uuid 로 생성한 유효 ID
    ports:
      - "29094:29094"
    networks:
      - pipeline-net
    healthcheck:
      test: ["CMD-SHELL", "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list || exit 1"]
      interval: 15s
      timeout: 10s
      retries: 10
      start_period: 30s
```

### 4-2. 멀티 브로커 기동 및 검증

> **중요**: docker-compose.yml에서 기존 단일 브로커 `kafka:` 서비스 블록을 **삭제(또는 주석 처리)**하고, 위 4-1에서 정의한 `kafka-1`, `kafka-2`, `kafka-3` 서비스로 **교체**한다. 두 설정이 공존하면 포트 충돌 및 클러스터 구성 오류가 발생한다.

```bash
# 기존 단일 브로커 환경 정리 (데이터 볼륨 포함 삭제)
docker compose down -v

# 멀티 브로커 클러스터 기동
docker compose up -d kafka-1 kafka-2 kafka-3

# 클러스터 상태 확인 — 3개 브로커 모두 확인
docker exec lab-kafka-1 /opt/kafka/bin/kafka-metadata.sh \
  --snapshot /tmp/kraft-combined-logs/__cluster_metadata-0/00000000000000000000.log \
  --cluster-id NexusPayLabCluster2026 2>/dev/null || \
docker exec lab-kafka-1 /opt/kafka/bin/kafka-broker-api-versions.sh \
  --bootstrap-server kafka-1:9092 | head -3

# 간단한 클러스터 검증
echo "=== 브로커 목록 ==="
for i in 1 2 3; do
  echo -n "kafka-$i: "
  docker exec lab-kafka-$i /opt/kafka/bin/kafka-topics.sh \
    --bootstrap-server localhost:9092 --list > /dev/null 2>&1 \
    && echo "✅ 정상" || echo "❌ 실패"
done
```

### 4-3. 복제 팩터 3인 토픽 재생성

```bash
# 복제 팩터 3으로 토픽 재생성
BOOTSTRAP="kafka-1:9092"

for TOPIC in nexuspay.transactions.payment nexuspay.transactions.transfer; do
  docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh \
    --bootstrap-server $BOOTSTRAP \
    --create --topic "$TOPIC" \
    --partitions 6 \
    --replication-factor 3 \
    --config min.insync.replicas=2 \
    --config retention.ms=604800000
  echo "Created: $TOPIC (RF=3, min.ISR=2)"
done

docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server $BOOTSTRAP \
  --create --topic nexuspay.transactions.withdrawal \
  --partitions 4 \
  --replication-factor 3 \
  --config min.insync.replicas=2

docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server $BOOTSTRAP \
  --create --topic nexuspay.transactions.dlq \
  --partitions 2 \
  --replication-factor 3 \
  --config min.insync.replicas=2
```

### 4-4. 복제 상태 확인 — ISR(In-Sync Replicas)

```bash
# 토픽 상세 확인 — Leader, Replicas, ISR 확인
docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka-1:9092 \
  --describe --topic nexuspay.transactions.payment
```

기대 출력:
```
Topic: nexuspay.transactions.payment  PartitionCount: 6  ReplicationFactor: 3
  Topic: nexuspay.transactions.payment  Partition: 0  Leader: 1  Replicas: 1,2,3  Isr: 1,2,3
  Topic: nexuspay.transactions.payment  Partition: 1  Leader: 2  Replicas: 2,3,1  Isr: 2,3,1
  Topic: nexuspay.transactions.payment  Partition: 2  Leader: 3  Replicas: 3,1,2  Isr: 3,1,2
  ...
```

> **핵심 용어 정리**:
> - **Leader**: 해당 파티션의 읽기·쓰기를 담당하는 브로커
> - **Replicas**: 해당 파티션의 복제본을 보유한 브로커 목록
> - **ISR (In-Sync Replicas)**: 리더와 동기화가 완료된 복제본 목록. ISR에 포함된 브로커만 리더 선출 대상이 된다.

### 4-5. 프로듀서 설정 변경 — 멀티 브로커 대응

```python
# scripts/producer_nexuspay.py 수정 — BROKER 변경
# 단일 브로커:
# BROKER = "localhost:29092"

# 멀티 브로커 (모든 브로커 나열):
BROKER = "localhost:29092,localhost:29093,localhost:29094"
```

```bash
# 멀티 브로커 환경에서 거래 300건 전송
python scripts/producer_nexuspay.py -n 300 --delay 0.02

# 파티션별 리더 분산 확인 — 트래픽이 3개 브로커에 분산되는지 확인
docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka-1:9092 \
  --describe --topic nexuspay.transactions.payment \
  | grep "Leader" | awk '{print $8}' | sort | uniq -c
# 기대: 리더가 1, 2, 3에 고르게 분산
```

**Day 4 완료 기준**: 3-브로커 클러스터 정상 기동, 복제 팩터 3 토픽 생성, ISR 3/3 확인, 멀티 브로커 프로듀서 전송 성공.

---

## Day 5: 장애 시나리오 + 운영 가이드 문서화

### 5-1. 장애 시나리오 A — 브로커 1대 장애

```bash
echo "=== 장애 전 상태 ==="
docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka-1:9092 \
  --describe --topic nexuspay.transactions.payment

echo ""
echo "=== kafka-2 브로커 중단 ==="
docker stop lab-kafka-2

echo ""
echo "=== 30초 대기 ==="
sleep 30

echo ""
echo "=== 장애 후 상태 ==="
docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka-1:9092 \
  --describe --topic nexuspay.transactions.payment
# 기대: ISR에서 브로커 2가 빠짐, 리더가 다른 브로커로 선출됨
```

### 5-2. 장애 중 메시지 송수신 지속 확인

```bash
# 브로커 2가 중단된 상태에서 메시지 전송 — 정상 작동해야 함
python scripts/producer_nexuspay.py -n 50 --delay 0.02
# 기대: acks=all + min.insync.replicas=2 → 나머지 2대로 정상 전송

# 컨슈머도 정상 동작 확인
timeout 10 python scripts/consumer_fraud_detection.py --instance 1
```

### 5-3. 장애 시나리오 B — 2대 동시 장애 (서비스 불가 확인)

```bash
echo "=== kafka-3 추가 중단 (2대 장애) ==="
docker stop lab-kafka-3

echo ""
echo "=== 프로듀서 전송 시도 ==="
python scripts/producer_nexuspay.py -n 5 --delay 1
# 기대: min.insync.replicas=2 미충족 → 전송 실패(NotEnoughReplicas)

echo ""
echo "=== kafka-3 복구 ==="
docker start lab-kafka-3
sleep 20

echo "=== kafka-2 복구 ==="
docker start lab-kafka-2
sleep 20

echo ""
echo "=== 전체 복구 후 상태 ==="
docker exec lab-kafka-1 /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka-1:9092 \
  --describe --topic nexuspay.transactions.payment
# 기대: ISR이 다시 3/3으로 복구
```

### 5-4. 장애 시나리오 C — Unclean Leader 선출 설정 확인

```bash
# unclean.leader.election.enable 확인 (기본값: false)
docker exec lab-kafka-1 /opt/kafka/bin/kafka-configs.sh \
  --bootstrap-server kafka-1:9092 \
  --entity-type topics \
  --entity-name nexuspay.transactions.payment \
  --describe | grep unclean

# 금융 시스템에서는 반드시 false 유지 (데이터 유실 방지)
# false: ISR 외 브로커는 리더 선출 불가 → 가용성 ↓ 일관성 ↑
# true:  ISR 외 브로커도 리더 선출 가능 → 가용성 ↑ 일관성 ↓ (데이터 유실 위험)
```

### 5-5. 장애 테스트 결과 기록

```bash
cat > docs/fault-tolerance-report.md << 'EOF'
# Nexus Pay Kafka 장애 복원력 테스트 보고서

**테스트 일자**: Week 2 Day 5
**클러스터 구성**: 3 브로커 (KRaft), RF=3, min.ISR=2

## 테스트 결과 요약

| 시나리오 | 장애 브로커 | 서비스 가용성 | 데이터 유실 | ISR 상태 | 복구 시간 |
|----------|-----------|-------------|-----------|----------|----------|
| A: 1대 장애 | kafka-2 | ✅ 정상 | 없음 | 2/3 | ~30초 |
| B: 2대 장애 | kafka-2,3 | ❌ 쓰기 불가 | 없음 | 1/3 | ~40초 (2대 복구 후) |
| C: 전체 복구 | — | ✅ 정상 | 없음 | 3/3 | — |

## 핵심 관찰

1. **RF=3 + min.ISR=2 조합**: 1대 장애까지 서비스 정상. 2대 장애 시 쓰기 불가.
2. **리더 선출**: 장애 브로커가 리더였던 파티션은 ISR 내 다른 브로커로 자동 선출.
3. **메시지 보존**: 모든 장애 시나리오에서 기존 메시지 유실 없음.
4. **unclean.leader.election**: false 유지 — 금융 도메인 필수 설정.

## 컨설팅 권장 사항

- **운영 환경**: 최소 3 브로커, RF=3, min.ISR=2
- **모니터링 필수 지표**: Under-Replicated Partitions, ISR Shrink Rate
- **알림 기준**: ISR < RF 상태가 5분 이상 지속 시 즉시 알림

EOF
```

### 5-6. Kafka 운영 가이드 작성

```bash
cat > docs/kafka-operations-guide.md << 'EOF'
# Nexus Pay Kafka 운영 가이드

## 1. 클러스터 구성

| 항목 | 설정값 | 근거 |
|------|--------|------|
| 브로커 수 | 3 | 1대 장애 허용 |
| 복제 팩터 | 3 | 모든 브로커에 복제 |
| min.insync.replicas | 2 | acks=all 시 2대 확인 |
| unclean.leader.election | false | 데이터 유실 방지 (금융 필수) |

## 2. 토픽 설계 원칙

- 명명 규칙: `<도메인>.<엔티티>.<이벤트유형>`
- 파티션 키: user_id (사용자별 순서 보장)
- 파티션 수: 처리량 기반 산정 (partition-calculator.sh 활용)
- 보존 기간: 거래 7일, DLQ 30일

## 3. 프로듀서 설정

| 설정 | 권장값 | 설명 |
|------|--------|------|
| acks | all | 모든 ISR 확인 후 성공 반환 |
| enable.idempotence | true | 중복 전송 방지 |
| retries | 3 | 일시적 장애 대응 |
| compression.type | lz4 | 네트워크 절감 |
| linger.ms | 5 | 배치 효율 향상 |

## 4. 컨슈머 설정

| 설정 | 권장값 | 설명 |
|------|--------|------|
| enable.auto.commit | false | 수동 커밋으로 유실 방지 |
| auto.offset.reset | earliest | 신규 그룹 시 전체 재처리 |
| max.poll.interval.ms | 300000 | 처리 시간 여유 확보 |
| session.timeout.ms | 30000 | 장애 탐지 시간 |

## 5. 모니터링 핵심 지표

| 지표 | 정상 범위 | 알림 기준 |
|------|----------|----------|
| Under-Replicated Partitions | 0 | > 0이 5분 지속 |
| Consumer Lag | < 1000 | > 10000 |
| ISR Shrink Rate | 0 | > 0 |
| Request Latency (p99) | < 100ms | > 500ms |
| Disk Usage | < 70% | > 85% |

## 6. 일상 운영 명령어

```bash
# 토픽 목록
kafka-topics.sh --bootstrap-server <broker> --list

# 토픽 상세 (리더·ISR 확인)
kafka-topics.sh --bootstrap-server <broker> --describe --topic <name>

# 컨슈머 그룹 지연 확인
kafka-consumer-groups.sh --bootstrap-server <broker> --describe --group <name>

# 오프셋 리셋
kafka-consumer-groups.sh --bootstrap-server <broker> \
  --group <name> --topic <topic> --reset-offsets --to-earliest --execute

# 토픽 설정 변경
kafka-configs.sh --bootstrap-server <broker> \
  --entity-type topics --entity-name <topic> \
  --alter --add-config retention.ms=86400000
```

## 7. 장애 대응 절차

1. Under-Replicated Partitions 알림 수신
2. `kafka-topics.sh --describe`로 ISR 상태 확인
3. 장애 브로커 식별 → 로그 확인 (`/opt/kafka/logs/server.log`)
4. 브로커 재시작 → ISR 복구 대기
5. ISR 완전 복구 확인 → 프로듀서·컨슈머 정상 동작 확인

EOF
```

### 5-7. Git 커밋

```bash
git add .
git commit -m "Week 2: Kafka 심화 — 토픽 설계·파티션·컨슈머 그룹·복제·장애 테스트"
```

**Day 5 완료 기준**: 3가지 장애 시나리오 테스트 완료, 장애 복원력 보고서 작성, Kafka 운영 가이드 작성, Git 커밋.

---

## Week 2 산출물 체크리스트

| # | 산출물 | 완료 |
|---|--------|------|
| 1 | config/kafka/topic-naming-convention.md (토픽 명명 규칙) | ☐ |
| 2 | config/kafka/topic-configs.md (토픽 설정 가이드) | ☐ |
| 3 | scripts/partition-calculator.sh (파티션 산정 스크립트) | ☐ |
| 4 | scripts/producer_nexuspay.py (거래 프로듀서) | ☐ |
| 5 | scripts/verify_partition_key.py (파티션 키 검증) | ☐ |
| 6 | scripts/consumer_fraud_detection.py (이상거래 탐지 컨슈머) | ☐ |
| 7 | scripts/consumer_settlement.py (정산 컨슈머) | ☐ |
| 8 | docker-compose.yml 업데이트 (3-브로커 클러스터) | ☐ |
| 9 | docs/fault-tolerance-report.md (장애 복원력 보고서) | ☐ |
| 10 | docs/kafka-operations-guide.md (Kafka 운영 가이드) | ☐ |
| 11 | Git 커밋 | ☐ |

## 핵심 개념 요약

| 개념 | 요약 | 실습에서 확인한 것 |
|------|------|------------------|
| 파티션 키 | user_id → 동일 사용자 = 동일 파티션 = 순서 보장 | verify_partition_key.py |
| 컨슈머 그룹 | 그룹별 독립 소비 + 그룹 내 파티션 분배 | fraud-detection vs settlement |
| 수동 오프셋 커밋 | enable.auto.commit=false → 처리 완료 후 커밋 | 10건 배치 커밋 |
| 리밸런싱 | 컨슈머 추가·제거 시 파티션 재할당 | 인스턴스 추가·제거 관찰 |
| ISR | 리더와 동기화된 복제본 → 장애 시 리더 선출 대상 | 1대 장애 → ISR 2/3 → 정상 운영 |
| min.insync.replicas | acks=all 시 최소 확인 브로커 수 | 2대 장애 → 쓰기 불가 확인 |

## Week 3 예고

Week 3에서는 NiFi를 활용한 다중 소스 데이터 수집 파이프라인을 구축한다. REST API, 파일 시스템, 데이터베이스 등 다양한 소스에서 데이터를 수집하여 Kafka로 라우팅하는 플로우를 설계한다. NiFi의 Provenance 추적 기능을 활용하여 데이터 흐름을 시각적으로 모니터링하는 방법을 실습한다.
