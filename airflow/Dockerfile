# Use Python 3.10 to support Pandas 2.1+
FROM apache/airflow:2.10.5-python3.10

# 1. Switch to root to install Java
USER root

# FIX: Manually rewrite the apt sources to use valid mirrors
# - Main Repo: ftp.us.debian.org (Bypasses your region/ISP block)
# - Security Repo: security.debian.org (The ONLY valid source for security updates)
RUN rm -f /etc/apt/sources.list.d/debian.sources && \
    echo "deb http://ftp.us.debian.org/debian bookworm main" > /etc/apt/sources.list && \
    echo "deb http://ftp.us.debian.org/debian bookworm-updates main" >> /etc/apt/sources.list && \
    echo "deb http://security.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list

# Install OpenJDK-17 and procps
# Added --fix-missing to handle minor fetch errors gracefully
RUN apt-get update --fix-missing && \
    apt-get install -y openjdk-17-jdk procps ant && \
    apt-get clean;

# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
RUN export JAVA_HOME

# 2. Switch back to airflow user for Python packages
USER airflow

# 3. Install Python Requirements
COPY requirements.txt /requirements.txt

# Upgrade pip and install requirements
# CRITICAL FIX: Removed '--user' flag to fix virtualenv error
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /requirements.txt