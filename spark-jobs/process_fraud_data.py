import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, current_timestamp, md5, concat_ws

def process_day(day_file, minio_endpoint, minio_access, minio_secret, sf_user, sf_password, sf_account, sf_db_raw, sf_schema, sf_warehouse, sf_role):
    
    # --- FIX 1: Ensure URL has https:// ---
    if not sf_account.startswith("https://"):
        sf_url = f"https://{sf_account}.snowflakecomputing.com"
    else:
        sf_url = sf_account

    # --- FIX 2: Clean Database Name (Handle 'DB/SCHEMA' format) ---
    if "/" in sf_db_raw:
        sf_db = sf_db_raw.split("/")[0]
    else:
        sf_db = sf_db_raw

    print(f"Snowflake Config: URL={sf_url}, DB={sf_db}, Schema={sf_schema}")

    # 1. Initialize Spark
    spark = SparkSession.builder \
        .appName("FraudDetectionETL") \
        .config("spark.hadoop.fs.s3a.endpoint", minio_endpoint) \
        .config("spark.hadoop.fs.s3a.access.key", minio_access) \
        .config("spark.hadoop.fs.s3a.secret.key", minio_secret) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .getOrCreate()

    # 2. Define Paths (S3A Protocol)
    input_path = f"s3a://raw-data/{day_file}"
    print(f"Reading data from: {input_path}")

    # 3. Read Data
    try:
        df = spark.read.csv(input_path, header=True, inferSchema=True)
    except Exception as e:
        print(f"CRITICAL ERROR: Could not read file from MinIO. {e}")
        sys.exit(1)

    # 4. Transform
    transformed_df = df \
        .withColumn("TRANS_ID", md5(concat_ws("-", col("step"), col("nameOrig"), col("amount")))) \
        .withColumn("INGESTION_TIMESTAMP", current_timestamp()) \
        .select(
            col("TRANS_ID"),
            col("step").cast("int").alias("STEP"),
            col("type").alias("TYPE"),
            col("amount").cast("double").alias("AMOUNT"),
            col("nameOrig").alias("NAME_ORIG"),
            col("oldbalanceOrg").cast("double").alias("OLD_BALANCE_ORIG"),
            col("newbalanceOrig").cast("double").alias("NEW_BALANCE_ORIG"),
            col("nameDest").alias("NAME_DEST"),
            col("oldbalanceDest").cast("double").alias("OLD_BALANCE_DEST"),
            col("newbalanceDest").cast("double").alias("NEW_BALANCE_DEST"),
            col("isFraud").cast("boolean").alias("IS_FRAUD"),
            col("isFlaggedFraud").cast("boolean").alias("IS_FLAGGED_FRAUD"),
            col("INGESTION_TIMESTAMP")
        )

    # 5. Write to Snowflake
    sfOptions = {
        "sfURL": sf_url,          # Uses the fixed URL
        "sfUser": sf_user,
        "sfPassword": sf_password,
        "sfDatabase": sf_db,      # Uses the cleaned DB name
        "sfSchema": sf_schema,
        "sfWarehouse": sf_warehouse,
        "sfRole": sf_role
    }

    print("Writing to Snowflake...")
    try:
        transformed_df.write \
            .format("net.snowflake.spark.snowflake") \
            .options(**sfOptions) \
            .option("dbtable", "FACT_TRANSACTIONS") \
            .mode("append") \
            .save()
        print("SUCCESS: Data loaded to Snowflake table 'FACT_TRANSACTIONS'.")
    except Exception as e:
        print(f"SNOWFLAKE WRITE FAILED: {e}")
        raise e
    
    spark.stop()

if __name__ == "__main__":
    if len(sys.argv) > 10:
        process_day(
            day_file=sys.argv[1],
            minio_endpoint=sys.argv[2],
            minio_access=sys.argv[3],
            minio_secret=sys.argv[4],
            sf_user=sys.argv[5],
            sf_password=sys.argv[6],
            sf_account=sys.argv[7],
            sf_db_raw=sys.argv[8], # Renamed to indicate it might need cleaning
            sf_schema=sys.argv[9],
            sf_warehouse=sys.argv[10],
            sf_role=sys.argv[11]
        )
    else:
        print("Error: Missing arguments.")
        sys.exit(1)