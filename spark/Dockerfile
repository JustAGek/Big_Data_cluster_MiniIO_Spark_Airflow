# Use Spark 3.4.2
FROM apache/spark:3.4.2

USER root

# Install Python and pip
RUN apt-get update && \
    apt-get install -y python3-pip curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python packages for Spark jobs
# FIX: Downgraded Pandas to 2.0.3 to support Python 3.8 (used by Spark image)
RUN pip3 install --no-cache-dir \
    boto3==1.28.57 \
    pandas==2.0.3 \
    pyarrow==13.0.0 \
    numpy==1.24.3

# --- BAKE IN DEPENDENCIES ---
WORKDIR /opt/spark/jars

# 1. Hadoop AWS & AWS SDK (For MinIO/S3)
RUN curl -O https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar && \
    curl -O https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar

# 2. Snowflake Connectors (Updated to 2.12.0 to match Spark 3.4)
RUN curl -O https://repo1.maven.org/maven2/net/snowflake/spark-snowflake_2.12/2.12.0-spark_3.4/spark-snowflake_2.12-2.12.0-spark_3.4.jar && \
    curl -O https://repo1.maven.org/maven2/net/snowflake/snowflake-jdbc/3.13.30/snowflake-jdbc-3.13.30.jar

# Create directory for Spark jobs
RUN mkdir -p /opt/spark-jobs && \
    chmod 777 /opt/spark-jobs

WORKDIR /opt/spark

# Reset to default Spark user
USER 185