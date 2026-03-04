"""
data_quality.py
---------------
Runs data quality checks on all Parquet files in S3.
"""

import boto3
import pandas as pd
from io import BytesIO
import os
import sys

S3_BUCKET = os.getenv("S3_BUCKET", "hybrid-pipeline-raw-zone")
S3_FOLDER = os.getenv("S3_FOLDER", "large_streaming_data/")

def run_checks():
    s3 = boto3.client("s3")
    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=S3_BUCKET, Prefix=S3_FOLDER)

    frames = []
    for page in pages:
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(".parquet"):
                body = s3.get_object(Bucket=S3_BUCKET, Key=obj["Key"])["Body"].read()
                frames.append(pd.read_parquet(BytesIO(body)))

    if not frames:
        print("No data to check.")
        sys.exit(1)

    df = pd.concat(frames, ignore_index=True)
    issues = 0

    print(f"\n{'='*55}")
    print("DATA QUALITY REPORT")
    print(f"{'='*55}")
    print(f"Total records         : {len(df):,}")

    # Duplicate check — allow up to 10%
    dup = df['transaction_id'].duplicated().sum()
    dup_pct = dup / len(df) * 100
    print(f"Duplicate tx IDs      : {dup} ({dup_pct:.1f}%)")
    if dup_pct > 10:
        issues += 1
        print("ERROR: Duplicate rate above 10%")
    else:
        print(f"Duplicate rate OK ({dup_pct:.1f}% is under 10% threshold)")

    # Null checks
    for col in ['transaction_id', 'customer_name', 'email', 'state']:
        null_count = df[col].isnull().sum()
        print(f"Null {col:<20}: {null_count}")
        if null_count > 0:
            issues += 1

    # Price check
    neg = (df['total_price'] < 0).sum()
    print(f"Negative prices       : {neg}")
    if neg > 0:
        issues += 1

    # Quantity check
    zero_qty = (df['quantity'] <= 0).sum()
    print(f"Zero/negative quantity: {zero_qty}")
    if zero_qty > 0:
        issues += 1

    # Status distribution
    print(f"\nStatus distribution:")
    print(df["status"].value_counts(normalize=True).mul(100).round(1).to_string())

    print(f"\n{'='*55}")
    if issues == 0:
        print("All checks passed.")
    else:
        print(f"FAILED: {issues} issue(s) found.")
        sys.exit(1)

if __name__ == "__main__":
    run_checks()