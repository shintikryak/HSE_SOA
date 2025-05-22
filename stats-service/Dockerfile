FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh
COPY stats-service/src/ /app/src/
COPY stats.proto /app/stats.proto
RUN python -m grpc_tools.protoc -I/app --python_out=/app/src --grpc_python_out=/app/src /app/stats.proto
ENV PYTHONPATH=/app/src
CMD [ \
  "/wait-for-it.sh", "kafka:9092", "--", \
  "/wait-for-it.sh", "clickhouse:9000", "--", \
  "python3", "-u", "/app/src/main.py" \
]