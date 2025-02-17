```mermaid
erDiagram
    EVENTS {
      int id PK
      int user_id FK
      string event_type
      datetime event_time
      string metadata
    }
    STATISTICS {
      int id PK
      int user_id FK
      int total_likes
      int total_comments
      int total_views
      datetime updated_at
    }
    EVENT_LOGS {
      int id PK
      int event_id FK
      string details
      datetime logged_at
      string source
    }
    EVENTS ||--o{ EVENT_LOGS : "logs"
    USERS ||--o{ STATISTICS : "has statistics"
