FROM python:3.11-slim

ENV MLFLOW_HOME=/opt/mlflow
WORKDIR ${MLFLOW_HOME}

RUN pip install --no-cache-dir mlflow==2.12.1 gunicorn==21.2.0

EXPOSE 5000

CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000", "--backend-store-uri", "sqlite:///mlflow.db", "--default-artifact-root", "/opt/mlflow/artifacts"]

