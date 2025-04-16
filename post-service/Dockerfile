FROM python:3.11
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh
COPY post-service/src/ /app/src/
COPY post.proto /app/post.proto
RUN python -m grpc_tools.protoc -I/app --python_out=/app/src --grpc_python_out=/app/src /app/post.proto
ENV PYTHONPATH=/app/src
CMD ["/wait-for-it.sh", "db_post:5432", "--", "python", "/app/src/main.py"]
