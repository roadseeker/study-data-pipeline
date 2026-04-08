"""
Nexus Pay payment API simulator for Week 3 NiFi ingestion.

- GET /api/v1/payments/recent : return recent N synthetic payment events
- GET /api/v1/payments/stream : return one payment event per poll
- GET /health                 : simple liveness check for Docker/NiFi setup
"""

import random
from datetime import datetime, timedelta, timezone

from flask import Flask, jsonify, request


app = Flask(__name__)

_seq_counter = 0
_last_fetched = datetime.now(timezone.utc) - timedelta(minutes=5)

MERCHANTS = [
    {"id": "MCH-101", "name": "Starbucks Gangnam", "category": "CAFE"},
    {"id": "MCH-202", "name": "Coupang Online", "category": "ECOMMERCE"},
    {"id": "MCH-303", "name": "GS25 Yeoksam", "category": "CONVENIENCE"},
    {"id": "MCH-404", "name": "Hyundai Pangyo", "category": "DEPARTMENT"},
    {"id": "MCH-505", "name": "Baemin Delivery", "category": "DELIVERY"},
]
CHANNELS = ["APP", "WEB", "POS", "ATM"]
CURRENCIES = [("KRW", 70), ("USD", 20), ("JPY", 10)]
AMOUNT_RANGES = {
    "KRW": (1_000, 5_000_000),
    "USD": (1, 5_000),
    "JPY": (100, 500_000),
}


def generate_payment() -> dict:
    """Generate one synthetic payment event."""
    global _seq_counter
    _seq_counter += 1

    currency = random.choices(
        [item[0] for item in CURRENCIES],
        weights=[item[1] for item in CURRENCIES],
        k=1,
    )[0]
    lower, upper = AMOUNT_RANGES[currency]
    amount = round(random.uniform(lower, upper), 2)

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
    """Return a small batch of recent payment events for polling ingestion."""
    count = min(int(request.args.get("count", 10)), 50)
    payments = [generate_payment() for _ in range(count)]

    return jsonify(
        {
            "status": "ok",
            "count": len(payments),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "data": payments,
        }
    )


@app.route("/api/v1/payments/stream", methods=["GET"])
def get_stream_payment():
    """Return a single payment event for one-by-one polling."""
    global _last_fetched
    payment = generate_payment()
    _last_fetched = datetime.now(timezone.utc)
    return jsonify(payment)


@app.route("/health", methods=["GET"])
def health():
    """Return simulator health for Docker healthcheck usage."""
    return jsonify(
        {
            "status": "healthy",
            "seq": _seq_counter,
            "last_fetched": _last_fetched.isoformat(),
        }
    )


if __name__ == "__main__":
    print("Nexus Pay payment API simulator listening on http://0.0.0.0:5050")
    app.run(host="0.0.0.0", port=5050, debug=False)
