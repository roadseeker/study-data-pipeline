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
    "KRW": 50_000_000,  # 5천만원 이상인 거래는 이상거래로 판단
    "USD": 50_000,  # 5만달러 이상인 거래는 이상거래로 판단
    "JPY": 5_000_000,  # 500만엔 이상인 거래는 이상거래로 판단
}

running = True


# 현재 코드는 Ctrl+C를 즉시 강제 종료로 처리하지 않고, 종료 플래그를 세운 뒤 루프를 빠져나와 마지막 커밋을 수행하도록 한다. 
# 이렇게 하면 컨슈머가 처리 중이던 메시지에 대한 오프셋을 커밋한 뒤 종료할 수 있다.
def signal_handler(sig, frame):
    global running
    print("\n종료 신호 수신 — 정리 중...")
    running = False

# signal.signal(signal.SIGINT, signal_handler) 는 프로그램이 SIGINT 신호를 받았을 때, 기본 종료 동작 대신 signal_handler 함수를 실행하도록 등록하는 코드입니다.
# “수동 오프셋 커밋을 쓰는 컨슈머를 안전하게 종료하기 위한 종료 훅”이라고 보면 됩니다.
signal.signal(signal.SIGINT, signal_handler)


# 거래 1건(tx)을 입력받아 이상거래 여부를 판단한다.
# 이상거래이면 탐지 결과를 dict 형태로 반환하고,
# 해당 사항이 없으면 None을 반환한다.
def detect_fraud(tx: dict) -> dict | None:
    """이상거래 탐지 로직"""
    reasons = []

    #규칙 1: 프로듀서 플래그
    if tx.get("is_suspicious"):
        reasons.append("프로듀서 이상 플래그")
    
    #규칙 2: 고액 거래
    # 거래 통화별 기준 금액을 가져오고, 기준이 없는 통화는 고액거래로 오탐지하지 않도록 무한대를 사용한다
    threshold = THRESHOLDS.get(tx.get("currency"), float("inf"))
    if tx.get("amount", 0) > threshold:
        # 이상거래 사유 목록(reasons)에 사람이 읽기 쉬운 설명 문자열을 추가한다.
        # 예: 통화가 KRW이고 금액이 125000000이면
        #     "고액 거래(KRW 125,000,000)" 형태로 저장된다.
        # tx.get("currency")는 거래 통화를 가져오고,
        # tx["amount"]:,.0f 는 금액을 천 단위 콤마가 있는 정수 형식으로 표시한다.
        reasons.append(f"고액 거래({tx.get('currency')} {tx['amount']:,.0f})")

    # 규칙 3: ATM 출금 + 고액
    if tx["tx_type"] == "withdrawal" and tx["channel"] == "ATM" and tx["amount"] > threshold * 0.5:
        reasons.append("ATM 고액 출금")

    # 파이썬에서는 리스트가: 비어있으면 false로 평가되고, 하나 이상의 요소가 있으면 true로 평가된다. 
    # 따라서 reasons 리스트에 하나 이상의 이상거래 사유가 있으면 if reasons: 조건이 참이 되어 탐지 결과를 반환한다.
    # 이상거래 사유가 1개 이상 있으면 탐지 결과를 반환하고,
    # 사유가 없으면 None을 반환한다.
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
    # 명령행 인자(--instance, --help 등)를 처리할 파서를 만들고,
    # 이 스크립트의 도움말 설명 문구를 "이상거래 탐지 컨슈머"로 설정한다.
    # --help는 argparse.ArgumentParser(...)를 만들면 기본으로 자동 추가된다.
    parser = argparse.ArgumentParser(description="이상거래 탐지 컨슈머")
    parser.add_argument("--instance", type=int, default=1, help="인스턴스 번호")

    args = parser.parse_args()

    # 한 번 poll()로 메시지를 받은 뒤 다음 poll()을 다시 호출하기까지 허용되는 최대 시간.
    # 이 시간을 넘기면 Kafka는 컨슈머가 처리 불능 상태라고 판단하고
    # 그룹에서 제외한 뒤 리밸런싱을 수행할 수 있다.
    # max.poll.interval.ms 는 “일은 맡겨놨는데 너무 오래 다음 작업 요청을 안 하네, 멈춘 것 아닌가?”를 보는 값
    # session.timeout.ms 는 “심장 박동이 끊겼는가”를 보는 값
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
    # 구독 대상 토픽 리스트(TOPICS)를 쉼표로 연결해 한 줄로 출력한다.
    print(f"  토픽: {', '.join(TOPICS)}")
    # 출력 화면에서 구분선 역할을 하도록 '=' 문자를 60번 반복해 출력한다.
    print("=" * 60)


    processed = 0
    alerts = 0
    batch = []

    while running:
        # Kafka 브로커에서 다음 메시지를 최대 1초까지 기다려 받아온다.
        # 메시지가 없으면 None이 반환된다.
        msg = consumer.poll(timeout=1.0)
        # 메시지가 없을 경우에는 poll()이 1초 기다린 뒤 끝나고, 루프가 다시 돌아가면서 거의 바로 다음 poll()을 호출한다.
        # 반대로 메시지가 바로 있으면: 1초를 다 기다리지 않고 즉시 반환, 바로 처리 로직으로 들어간다.
        if msg is None:
            continue
        
        # poll() 결과가 정상 메시지가 아니라 에러인지 확인한다.
        # 파티션 끝(_PARTITION_EOF)에 도달한 경우는 치명적 오류가 아니므로 무시하고,
        # 그 외 에러는 내용을 출력한 뒤 현재 메시지는 건너뛴다.
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            print(f"  ❌ 에러: {msg.error()}")
            continue

        # 메시지 값(msg.value())은 바이트 문자열이므로, 이를 UTF-8로 디코딩한 뒤 JSON 형식으로 파싱하여 tx 딕셔너리에 저장한다.
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

        # 처리한 메시지를 batch에 쌓아 두었다가,
        # 10건이 모이면 해당 시점까지의 오프셋을 동기 방식으로 수동 커밋한다.
        # 커밋 후에는 다음 배치를 위해 batch를 비운다
        batch.append(msg)
        if len(batch) >= 10:
            consumer.commit(asynchronous=False)
            batch.clear()

        # 처리 건수가 50의 배수(50, 100, 150...)가 될 때마다
        # 현재까지의 처리 건수와 이상거래 알림 건수를 출력한다.
        if processed % 50 == 0:
            print(f"  📊 처리: {processed}건 / 알림: {alerts}건")

    # 종료 전 마지막 커밋
    if batch:
        consumer.commit(asynchronous=False) 

    consumer.close()
    print(f"\n최종 결과: 처리 {processed}건, 알림 {alerts}건") 

    # 이 파일을 직접 실행한 경우에만 main() 함수를 호출한다.
    # 다른 파일에서 import할 때는 main()이 자동 실행되지 않는다.
    if __name__ == "__main__":
        main() 