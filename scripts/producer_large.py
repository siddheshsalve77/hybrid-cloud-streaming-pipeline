"""
producer_large.py
-----------------
Generates 300,000 realistic e-commerce transactions
and publishes them to a Kafka topic.
"""

import json
import os
import time
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError
from faker import Faker
import random

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PRODUCER] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# Config from environment
TOTAL_RECORDS = int(os.getenv("TOTAL_RECORDS", 300_000))
TOPIC         = os.getenv("KAFKA_TOPIC", "transactions_topic")
KAFKA_SERVER  = os.getenv("KAFKA_SERVER", "kafka:9092")
LOG_INTERVAL  = 10_000

# Products catalog with realistic price ranges
PRODUCTS = {
    "iPhone 15":     (799,  1199),
    "MacBook Pro":   (1299, 2499),
    "AirPods Pro":   (199,  249),
    "iPad Air":      (599,  899),
    "Apple Watch":   (299,  799),
    "Samsung S24":   (699,  1099),
    "Dell XPS 15":   (999,  1999),
    "Sony WH-1000X": (279,  349),
}

PAYMENT_METHODS = ["Credit Card", "Debit Card", "PayPal", "Apple Pay", "Google Pay", "Bank Transfer"]
STATUSES        = ["Completed", "Pending", "Failed", "Refunded"]
STATUS_WEIGHTS  = [0.75, 0.12, 0.08, 0.05]


def build_producer() -> KafkaProducer:
    """Create a Kafka producer with retry logic."""
    for attempt in range(1, 6):
        try:
            producer = KafkaProducer(
                bootstrap_servers=[KAFKA_SERVER],
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",
                retries=5,
                linger_ms=10,
                batch_size=16_384,
            )
            log.info("Connected to Kafka at %s", KAFKA_SERVER)
            return producer
        except KafkaError as e:
            log.warning("Attempt %d/5 failed: %s. Retrying in 5s...", attempt, e)
            time.sleep(5)
    raise RuntimeError("Could not connect to Kafka after 5 attempts.")


def generate_record(fake: Faker, record_id: int) -> dict:
    """Generate one realistic transaction record."""
    product = random.choice(list(PRODUCTS.keys()))
    min_p, max_p = PRODUCTS[product]
    unit_price = round(random.uniform(min_p, max_p), 2)
    qty = random.choices([1, 2, 3, 4, 5], weights=[0.6, 0.2, 0.1, 0.06, 0.04])[0]

    return {
        "record_id":      record_id,
        "transaction_id": fake.uuid4(),
        "customer_id":    f"CUST-{fake.numerify('######')}",
        "customer_name":  fake.name(),
        "email":          fake.email(),
        "product":        product,
        "quantity":       qty,
        "unit_price":     unit_price,
        "total_price":    round(unit_price * qty, 2),
        "city":           fake.city(),
        "state":          fake.state_abbr(),
        "country":        "US",
        "zip_code":       fake.zipcode(),
        "payment_method": random.choice(PAYMENT_METHODS),
        "status":         random.choices(STATUSES, weights=STATUS_WEIGHTS)[0],
        "device_type":    random.choice(["mobile", "desktop", "tablet"]),
        "timestamp":      str(fake.date_time_this_year()),
    }


def main():
    fake = Faker()
    producer = build_producer()
    log.info("Starting generation of %d records -> topic: %s", TOTAL_RECORDS, TOPIC)
    start = time.time()
    errors = 0

    for i in range(TOTAL_RECORDS):
        record = generate_record(fake, i + 1)
        try:
            producer.send(TOPIC, value=record)
        except KafkaError as e:
            errors += 1
            log.error("Failed to send record %d: %s", i + 1, e)

        if (i + 1) % LOG_INTERVAL == 0:
            elapsed = time.time() - start
            rate = (i + 1) / elapsed
            log.info(
                "Progress: %d/%d records (%.0f rec/s | %.1f%% done)",
                i + 1, TOTAL_RECORDS, rate, (i + 1) / TOTAL_RECORDS * 100
            )

    producer.flush()
    elapsed = time.time() - start
    log.info("Done. Sent %d records in %.1fs (%.0f rec/s)", TOTAL_RECORDS - errors, elapsed, TOTAL_RECORDS / elapsed)
    if errors:
        log.warning("%d records failed to send.", errors)


if __name__ == "__main__":
    main()