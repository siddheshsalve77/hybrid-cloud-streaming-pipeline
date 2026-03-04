from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import timedelta

default_args = {
    "owner": "data-engineering",
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
    "execution_timeout": timedelta(minutes=30),
    "email_on_failure": False,
}

with DAG(
    dag_id="hybrid_cloud_streaming_pipeline",
    description="Stream 300K transactions via Kafka -> S3 Parquet",
    default_args=default_args,
    start_date=days_ago(1),
    schedule_interval=None,
    catchup=False,
    tags=["kafka", "s3", "streaming", "parquet"],
) as dag:

    validate_env = BashOperator(
        task_id="validate_environment",
        bash_command=(
            "python -c \""
            "import boto3, os, kafka, faker, pandas, pyarrow; "
            "s3 = boto3.client('s3'); "
            "s3.head_bucket(Bucket='hybrid-pipeline-raw-zone'); "
            "print('All packages OK. S3 accessible.');"
            "\""
        ),
    )

    produce_task = BashOperator(
        task_id="produce_300k_records",
        bash_command="python /opt/airflow/scripts/producer_large.py ",
    )

    consume_task = BashOperator(
        task_id="consume_and_upload_to_s3",
        bash_command="python /opt/airflow/scripts/consumer_batch_s3.py ",
    )

    verify_s3 = BashOperator(
        task_id="verify_s3_output",
        bash_command=(
            "python -c \""
            "import boto3, sys; "
            "s3 = boto3.client('s3'); "
            "r = s3.list_objects_v2(Bucket='hybrid-pipeline-raw-zone', Prefix='large_streaming_data/'); "
            "c = r.get('KeyCount', 0); "
            "print('Files found:', c); "
            "sys.exit(0 if c > 0 else 1)"
            "\""
        ),
    )

    quality_check = BashOperator(
        task_id="data_quality_checks",
        bash_command="python /opt/airflow/scripts/data_quality.py ",
    )

    validate_env >> produce_task >> consume_task >> verify_s3 >> quality_check