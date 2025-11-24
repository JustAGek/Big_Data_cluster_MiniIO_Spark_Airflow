from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.hooks.base import BaseHook
import boto3
from botocore.client import Config
from datetime import datetime, timedelta
import os
import json

# --- CONFIGURATION ---
# Path inside the Airflow container where the CSVs are located
RAW_LOCAL_PATH = "/opt/airflow/include/data/paysim/raw" 
BUCKET_NAME = "raw-data"
DAG_ID = "fintech_fraud_pipeline_v4" # Updated to v4 to force a fresh run

def upload_to_minio(day_number, **kwargs):
    """
    Uploads the daily CSV file to MinIO using a direct boto3 client.
    This bypasses Airflow's S3Hook to avoid AWS connection errors.
    """
    file_name = f"paysim_day{day_number}.csv"
    local_file = os.path.join(RAW_LOCAL_PATH, file_name)
    
    print(f"Looking for file at: {local_file}")

    if not os.path.exists(local_file):
        raise FileNotFoundError(f"CRITICAL: File not found at {local_file}. Please check your 'include' folder path.")

    # DIRECT CONNECTION TO MINIO CONTAINER
    s3 = boto3.client(
        's3',
        endpoint_url="http://minio:9000",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",
        config=Config(signature_version='s3v4'),
        region_name='us-east-1' 
    )

    try:
        print(f"Uploading {file_name} to bucket '{BUCKET_NAME}' on MinIO...")
        s3.upload_file(local_file, BUCKET_NAME, file_name)
        print(f"SUCCESS: Uploaded {file_name}.")
    except Exception as e:
        print(f"FAILED: Could not connect to MinIO at http://minio:9000. Error: {e}")
        raise e

# Helper to fetch Snowflake details securely from Airflow Connections
def get_snowflake_args():
    snow_conn = BaseHook.get_connection('snowflake_default')
    
    # Handle different ways Airflow stores the account URL
    snow_account = snow_conn.host
    if not snow_account and 'account' in snow_conn.extra_dejson:
        snow_account = snow_conn.extra_dejson.get('account')
        
    return [
        "http://minio:9000", # MinIO Endpoint (passed to Spark)
        "minioadmin",        # MinIO Access Key
        "minioadmin",        # MinIO Secret Key
        snow_conn.login,     # SF User
        snow_conn.password,  # SF Password
        snow_account,        # SF Account
        snow_conn.schema,    # SF Database
        "FRAUD_DETECTION",   # SF Schema
        snow_conn.extra_dejson.get('warehouse', 'COMPUTE_WH'),
        snow_conn.extra_dejson.get('role', 'ACCOUNTADMIN')
    ]

default_args = {
    'owner': 'airflow',
    'retries': 0, 
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    DAG_ID,
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule_interval='@daily',
    catchup=False,
) as dag:

    ingest_task = PythonOperator(
        task_id='ingest_to_minio',
        python_callable=upload_to_minio,
        op_kwargs={'day_number': 1},
    )

    process_task = SparkSubmitOperator(
        task_id='process_with_spark',
        conn_id='spark_default',
        application='/opt/spark-jobs/process_fraud_data.py',
        application_args=[
            "paysim_day1.csv", 
            *get_snowflake_args()
        ],
        # UPDATED PACKAGE VERSION: Changed 2.11.0 -> 2.12.0 to fix download error
        packages="net.snowflake:spark-snowflake_2.12:2.12.0-spark_3.4,org.apache.hadoop:hadoop-aws:3.3.4",
        verbose=True
    )

    ingest_task >> process_task