FROM apache/airflow:2.6.3

USER root

# Install curl and Python deps via requirements.txt using Airflow constraints
COPY --chown=airflow:root requirements.txt /tmp/requirements.txt
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python packages as the 'airflow' user (recommended by Airflow docs)
USER airflow
ENV PATH="/home/airflow/.local/bin:${PATH}"
# Install providers using constraints matched to the Python version used by the base image (3.7)
RUN python -m pip install --no-cache-dir --user \
    -r /tmp/requirements.txt \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.6.3/constraints-3.7.txt" && \
    rm -f /tmp/requirements.txt

# Copy connection loader and sample connections file (ensure airflow owns them)
COPY --chown=airflow:root load_connections.sh /opt/airflow/load_connections.sh
COPY --chown=airflow:root airflow_connections.json /opt/airflow/airflow_connections.json
RUN chmod +x /opt/airflow/load_connections.sh || true

USER airflow
