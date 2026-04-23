# MLflow Tracking Server with PostgreSQL and S3 support
# Based on official MLflow image with additional dependencies
# NOTE: this version might require to match our pyproject.toml dependencies
# https://github.com/mlflow/mlflow/pkgs/container/mlflow/versions?filters%5Bversion_type%5D=tagged
FROM ghcr.io/mlflow/mlflow:v3.6.0

# Install PostgreSQL driver and S3 support
# -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install --no-cache-dir psycopg2-binary boto3

EXPOSE 5000

