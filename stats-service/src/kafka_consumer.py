# stats-service/src/kafka_consumer.py

import os
import json
from confluent_kafka import Consumer, KafkaException
from datetime import datetime as dat
from database import client

# Адрес Kafka-брокера (в Docker-сети — имя сервиса)
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

# Топики, из которых читаем события
TOPICS = [
    "user-registration",
    "post-view",
    "post-like",
    "post-comment",
]

# Маппинг топиков в метрики ClickHouse
METRIC_MAP = {
    "user-registration": "registrations",
    "post-view":         "views",
    "post-like":         "likes",
    "post-comment":      "comments",
}

# Поля-таймстемпы в событиях
TIMESTAMP_FIELD = {
    "user-registration": "registered_at",
    "post-view":         "viewed_at",
    "post-like":         "liked_at",
    "post-comment":      "commented_at",
}

# Настройка и запуск консьюмера
consumer = Consumer({
    "bootstrap.servers": KAFKA_BOOTSTRAP,
    "group.id":          "stats-service-group",
    "auto.offset.reset": "earliest",
    "metadata.max.age.ms": 3000,
    "topic.metadata.refresh.interval.ms": 3000,
})
consumer.subscribe(TOPICS)

def run():
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                # Логируем и продолжаем
                print(f"Kafka error: {msg.error()}")
                continue

            topic = msg.topic()
            metric = str(METRIC_MAP.get(topic))
            if not metric:
                # Топик не в списке — пропускаем
                continue

            # Распарсим JSON-сообщение
            ev = json.loads(msg.value().decode("utf-8"))
            ts_field = TIMESTAMP_FIELD[topic]
            ts = ev.get(ts_field)
            if not ts:
                # Некорректное сообщение — пропускаем
                continue

            # Парсим дату
            dt = dat.fromisoformat(ts)

            # Подготавливаем значения
            post_id = str(ev.get("post_id", ""))
            user_id = ev.get("user_id", 0)

            # Вставляем в ClickHouse
            client.execute(
                "INSERT INTO events (event_date, metric, post_id, user_id) VALUES",
                [(dt.date(), metric, post_id, user_id)]
            )
    except KafkaException as e:
        print(f"Fatal Kafka exception: {e}")
    finally:
        consumer.close()
