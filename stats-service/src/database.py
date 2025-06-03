from clickhouse_driver import Client
import os

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", 9000))
CLICKHOUSE_USER = "click"
CLICKHOUSE_PASSWORD = "click"

client = Client(
    host=CLICKHOUSE_HOST,
    port=CLICKHOUSE_PORT,
    user=CLICKHOUSE_USER,
    password=CLICKHOUSE_PASSWORD,
)
def create_events_table():
    client.execute("""
    CREATE TABLE IF NOT EXISTS events (
      event_date Date,
      metric String,
      post_id    String,
      user_id    UInt32
    ) ENGINE = MergeTree()
    PARTITION BY event_date
    ORDER BY (post_id, user_id);
    """)
