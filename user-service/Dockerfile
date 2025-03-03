FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir bcrypt==4.0.1 sqlalchemy psycopg2-binary passlib[bcrypt] pyjwt
CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:80"]
