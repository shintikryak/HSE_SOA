FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY post.proto /app/post.proto
COPY api-service/src/ /app/src/
RUN python -m grpc_tools.protoc -I/app --python_out=/app/src --grpc_python_out=/app/src /app/post.proto
ENV PYTHONPATH=/app/src
CMD ["gunicorn", "src.main:app", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:80"]
