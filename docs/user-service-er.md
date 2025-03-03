```mermaid
erDiagram
    USERS {
      int id PK
      string username
      string last_name
      string email
      string password
      string token
      string interests
      datetime created_at
      string role
      byte picture
      string private_info
    }
    ROLES {
      int id PK
      string role_name
      string description
      datetime created_at
      datetime updated_at
    }
    USER_ROLES {
      int user_id FK
      int role_id FK
      datetime assigned_at
      string status
    }
    FRIENDS {
      int id PK
      int first_user FK
      int second_user FK
    }
    USERS ||--o{ USER_ROLES : "has"
    ROLES ||--o{ USER_ROLES : "assigned to"
    USERS ||--o{ FRIENDS : "friends with"
