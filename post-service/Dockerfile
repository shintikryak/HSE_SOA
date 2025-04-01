FROM python:3.11
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . .
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. post.proto
CMD ["python", "main.py"]
