```mermaid
erDiagram
    API_LOGS {
      int id PK
      int user_id FK
      string endpoint
      string method
      datetime request_time
      string response_status
    }
    API_TOKENS {
      int id PK
      int user_id FK
      string token
      datetime created_at
      datetime expires_at
    }
    CONFIGURATIONS {
      int id PK
      string key
      string value
      datetime updated_at
      string description
    }
    USERS ||--o{ API_LOGS : "makes requests"
    USERS ||--o{ API_TOKENS : "has"
