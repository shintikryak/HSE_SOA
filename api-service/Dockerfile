FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir httpx
CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:80"]
