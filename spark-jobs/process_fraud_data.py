import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, current_timestamp, md5, concat_ws

def process_day(day_file_name):
    # 1. Initialize Spark with S3 and Snowflake Dependencies
    spark = SparkSession.builder \
        .appName("FraudDetectionETL") \
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
        .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
        .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .getOrCreate()

    # 2. Define Paths
    # Note: 's3a' is the protocol for S3-compatible storage like MinIO
    input_path = f"s3a://raw-data/{day_file_name}" 
    
    print(f"Reading data from: {input_path}")

    # 3. Read Data (Schema on Read)
    df = spark.read.csv(input_path, header=True, inferSchema=True)

    # 4. Transformations (The "T" in ETL)
    transformed_df = df \
        .withColumn("TRANS_ID", md5(concat_ws("-", col("step"), col("nameOrig"), col("amount")))) \
        .withColumn("INGESTION_TIMESTAMP", current_timestamp()) \
        .select(
            col("TRANS_ID"),
            col("step").alias("STEP"),
            col("type").alias("TYPE"),
            col("amount").alias("AMOUNT"),
            col("nameOrig").alias("NAME_ORIG"),
            col("oldbalanceOrg").alias("OLD_BALANCE_ORIG"),
            col("newbalanceOrig").alias("NEW_BALANCE_ORIG"),
            col("nameDest").alias("NAME_DEST"),
            col("oldbalanceDest").alias("OLD_BALANCE_DEST"),
            col("newbalanceDest").alias("NEW_BALANCE_DEST"),
            col("isFraud").cast("boolean").alias("IS_FRAUD"),
            col("isFlaggedFraud").cast("boolean").alias("IS_FLAGGED_FRAUD"),
            col("INGESTION_TIMESTAMP")
        )

    # 5. Write to Snowflake
    # NOTE: In production, use Airflow Variables for credentials!
    sfOptions = {
        "sfURL": "YOUR_SNOWFLAKE_ACCOUNT_URL", # e.g. xy12345.us-east-1.snowflakecomputing.com
        "sfUser": "YOUR_USERNAME",
        "sfPassword": "YOUR_PASSWORD",
        "sfDatabase": "FINTECH_DB",
        "sfSchema": "FRAUD_DETECTION",
        "sfWarehouse": "COMPUTE_WH",
        "sfRole": "ACCOUNTADMIN"
    }

    transformed_df.write \
        .format("net.snowflake.spark.snowflake") \
        .options(**sfOptions) \
        .option("dbtable", "FACT_TRANSACTIONS") \
        .mode("append") \
        .save()
    
    print("Data successfully loaded to Snowflake.")
    spark.stop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        day_file = sys.argv[1]
        process_day(day_file)
    else:
        print("Please provide the filename (e.g., paysim_day1.csv)")