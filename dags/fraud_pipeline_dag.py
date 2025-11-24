from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.hooks.S3_hook import S3Hook
from datetime import datetime, timedelta
import os

# CONFIGURATION
RAW_LOCAL_PATH = "/opt/airflow/include/raw_data" # Path inside container
BUCKET_NAME = "raw-data"
DAG_ID = "fintech_fraud_pipeline_v1"

def upload_to_minio(day_number, **kwargs):
    """
    Picks up the specific day's CSV from local storage and uploads to MinIO
    """
    file_name = f"paysim_day{day_number}.csv"
    local_file = os.path.join(RAW_LOCAL_PATH, file_name)
    
    # Use Airflow's S3Hook (configured to talk to MinIO)
    # Ensure you created an Airflow Connection 'minio_conn' first!
    hook = S3Hook(aws_conn_id='minio_conn') 
    
    if os.path.exists(local_file):
        hook.load_file(
            filename=local_file,
            key=file_name,
            bucket_name=BUCKET_NAME,
            replace=True
        )
        print(f"Uploaded {file_name} to MinIO bucket {BUCKET_NAME}")
        return file_name
    else:
        raise FileNotFoundError(f"Could not find file: {local_file}")

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    DAG_ID,
    default_args=default_args,
    description='Ingest PaySim data -> MinIO -> Spark -> Snowflake',
    start_date=datetime(2025, 1, 1),
    schedule_interval='@daily', # Runs once per day
    catchup=False,
) as dag:

    # 1. Ingest Task: Upload CSV to MinIO
    ingest_task = PythonOperator(
        task_id='ingest_to_minio',
        python_callable=upload_to_minio,
        op_kwargs={'day_number': 1}, # STARTING WITH DAY 1 STATICALLY
    )

    # 2. Process Task: Spark Submit
    process_task = SparkSubmitOperator(
        task_id='process_with_spark',
        conn_id='spark_default', # Needs connection setup in Airflow UI
        application='/opt/spark-jobs/process_fraud_data.py',
        application_args=["paysim_day1.csv"], # Argument passed to script
        packages="net.snowflake:spark-snowflake_2.12:2.11.0-spark_3.4,org.apache.hadoop:hadoop-aws:3.3.4", # Crucial libraries
        verbose=True
    )

    ingest_task >> process_task