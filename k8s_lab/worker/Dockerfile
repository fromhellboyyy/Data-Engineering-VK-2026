FROM python:3.11-slim
RUN pip install --no-cache-dir boto3==1.34.0
WORKDIR /app
COPY worker.py /app/worker.py
ENTRYPOINT ["python","-u","/app/worker.py"]