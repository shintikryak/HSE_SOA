# # FROM python:3.11
# # WORKDIR /app
# # COPY requirements.txt /app/requirements.txt
# # RUN pip install --no-cache-dir -r requirements.txt
# # # Копируем только содержимое папки src в папку src контейнера
# # COPY post-service/src/ /app/
# # # Генерируем Python-код из proto файла, который находится в папке src
# # RUN python -m grpc_tools.protoc -I/app --python_out=/app --grpc_python_out=/app /app/post.proto
# # CMD ["python", "src/main.py"]
# FROM python:3.11
# WORKDIR /app

# # Копируем requirements.txt из корня проекта
# COPY requirements.txt /app/requirements.txt
# RUN pip install --no-cache-dir -r /app/requirements.txt

# # Копируем содержимое папки src (из post-service) в рабочую директорию контейнера
# COPY post-service/src/ /app/

# # Генерируем gRPC файлы из post.proto, который теперь находится в /app/
# RUN python -m grpc_tools.protoc -I/app --python_out=/app --grpc_python_out=/app /app/post.proto

# # Запускаем сервер, используя main.py, который находится в /app/main.py
# CMD ["python", "-m", "main.py"]
FROM python:3.11
WORKDIR /app

# Копируем файл зависимостей из корневой директории проекта
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем содержимое папки post-service/src в контейнер в /app/src
COPY post-service/src/ /app/src/

# Генерируем gRPC файлы из post.proto, который теперь находится в /app/src
RUN python -m grpc_tools.protoc -I/app/src --python_out=/app/src --grpc_python_out=/app/src /app/src/post.proto

# Добавляем каталог /app/src в PYTHONPATH, чтобы модули (post_pb2, post_pb2_grpc) были доступны
ENV PYTHONPATH=/app/src

# Запускаем приложение напрямую, так как модули теперь доступны как верхнеуровневые
CMD ["python", "/app/src/main.py"]
