"""
consumer_batch_s3.py
--------------------
Reads from Kafka topic, batches records into 10K groups,
converts each batch to Parquet (Snappy compressed), uploads to S3
with date-partitioned paths for Athena cost optimization.
"""

import json
import os
import logging
import time
from io import BytesIO
from datetime import datetime

import boto3
import pandas as pd
from botocore.exceptions import ClientError
from kafka import KafkaConsumer
from kafka.errors import KafkaError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [CONSUMER] %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# Config
TOPIC        = os.getenv("KAFKA_TOPIC", "transactions_topic")
KAFKA_SERVER = os.getenv("KAFKA_SERVER", "kafka:9092")
S3_BUCKET    = os.getenv("S3_BUCKET", "hybrid-pipeline-raw-zone")
S3_FOLDER    = os.getenv("S3_FOLDER", "large_streaming_data/")
BATCH_SIZE   = int(os.getenv("BATCH_SIZE", 10_000))
IDLE_TIMEOUT = 15_000

EXPECTED_COLS = [
    "record_id", "transaction_id", "customer_id", "customer_name",
    "email", "product", "quantity", "unit_price", "total_price",
    "city", "state", "country", "zip_code", "payment_method",
    "status", "device_type", "timestamp",
]

DTYPES = {
    "record_id":   "int64",
    "quantity":    "int32",
    "unit_price":  "float64",
    "total_price": "float64",
}


def build_consumer() -> KafkaConsumer:
    for attempt in range(1, 6):
        try:
            consumer = KafkaConsumer(
                TOPIC,
                bootstrap_servers=[KAFKA_SERVER],
                group_id="pipeline-consumer-group",
                auto_offset_reset="earliest",
                enable_auto_commit=False,
                value_deserializer=lambda x: json.loads(x.decode("utf-8")),
                consumer_timeout_ms=IDLE_TIMEOUT,
                fetch_max_bytes=52_428_800,
                max_poll_records=500,
            )
            log.info("Connected to Kafka. Subscribing to topic: %s", TOPIC)
            return consumer
        except KafkaError as e:
            log.warning("Attempt %d/5 failed: %s. Retrying in 5s...", attempt, e)
            time.sleep(5)
    raise RuntimeError("Could not connect to Kafka after 5 attempts.")


def upload_batch_to_s3(s3_client, batch: list, batch_num: int) -> str:
    """Convert batch to Parquet and upload to S3 with date partitioning."""
    df = pd.DataFrame(batch, columns=EXPECTED_COLS)

    for col, dtype in DTYPES.items():
        if col in df.columns:
            df[col] = df[col].astype(dtype, errors="ignore")

    # Add ingestion metadata
    df["ingested_at"] = datetime.utcnow().isoformat()
    df["batch_number"] = batch_num

    # Serialize to Parquet in memory with Snappy compression
    buffer = BytesIO()
    df.to_parquet(buffer, index=False, engine="pyarrow", compression="snappy")
    buffer.seek(0)

    # Date-partitioned path for cheaper Athena queries
    now = datetime.utcnow()
    filename = (
        f"{S3_FOLDER}"
        f"year={now.year}/month={now.month:02d}/day={now.day:02d}/"
        f"batch_{batch_num:04d}_{now.strftime('%H%M%S')}.parquet"
    )

    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=filename,
        Body=buffer.getvalue(),
        ContentType="application/octet-stream",
    )
    return filename


def main():
    consumer = build_consumer()
    s3 = boto3.client("s3")
    log.info("Consumer started. Batch size: %d | Target: s3://%s/%s", BATCH_SIZE, S3_BUCKET, S3_FOLDER)

    batch = []
    batch_num = 0
    total_records = 0
    total_batches = 0
    failed_uploads = 0
    start = time.time()

    try:
        for message in consumer:
            batch.append(message.value)

            if len(batch) >= BATCH_SIZE:
                batch_num += 1
                try:
                    filename = upload_batch_to_s3(s3, batch, batch_num)
                    consumer.commit()    # Only commit after successful upload
                    total_records += len(batch)
                    total_batches += 1
                    log.info("Batch %d uploaded -> %s (%d records)", batch_num, filename, len(batch))
                    batch = []
                except ClientError as e:
                    failed_uploads += 1
                    log.error("S3 upload failed for batch %d: %s", batch_num, e)
                    # Do NOT commit -- Kafka will re-deliver on retry

        # Upload any remaining records
        if batch:
            batch_num += 1
            try:
                filename = upload_batch_to_s3(s3, batch, batch_num)
                consumer.commit()
                total_records += len(batch)
                total_batches += 1
                log.info("Final batch uploaded -> %s (%d records)", filename, len(batch))
            except ClientError as e:
                failed_uploads += 1
                log.error("Final batch upload failed: %s", e)

    finally:
        consumer.close()

    elapsed = time.time() - start
    log.info("Summary: %d records | %d batches | %d failed | %.1fs | %.0f rec/s",
             total_records, total_batches, failed_uploads, elapsed, total_records / max(elapsed, 1))


if __name__ == "__main__":
    main()