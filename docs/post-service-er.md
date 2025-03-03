```mermaid
erDiagram
    POSTS {
      int id PK
      int user_id FK
      string title
      string content
      datetime created_at
      datetime updated_at
    }
    COMMENTS {
      int id PK
      int post_id FK
      int user_id FK
      string content
      datetime created_at
      datetime updated_at
    }
    IMAGES {
      int id PK
      int post_id FK
      string url
      string description
      datetime uploaded_at
    }
    POSTS ||--o{ COMMENTS : "has"
    POSTS ||--o{ IMAGES : "contains"
