FROM python:3.11-slim
RUN pip install --no-cache-dir kazoo==2.10.0 boto3==1.34.0
WORKDIR /app
COPY coordinator_zk.py /app/coordinator_zk.py
ENTRYPOINT ["python","-u","/app/coordinator_zk.py"]