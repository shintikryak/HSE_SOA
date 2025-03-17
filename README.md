# HSE_SOA

Усачев Егор Дмитриевич

БПМИ2210

Социальная сеть

## Testing user-service & api
```bash
docker compose up --build
```
### 1. Регистрация пользователя
#### Method: POST
#### URL: http://localhost:8000/register
#### Headers: Content-Type: application/json
#### Пример запроса (Body: raw, JSON):
#### {
####  "login": "user1",
####  "password": "secret123",
####  "email": "user1@example.com",
####  "first_name": "Иван",
####  "last_name": "Иванов",
####  "date_of_birth": "1990-01-01",
####  "phone": "+71234567890"
#### }

### 2. Аутентификация (получение токена)
#### Method: POST
#### URL: http://localhost:8000/login
#### Headers: Content-Type: application/x-www-form-urlencoded
#### Request Body (x-www-form-urlencoded):
#### username	user1
#### password	secret123

### 3. Получение профиля пользователя
#### Method: GET
#### URL: http://localhost:8000/profile
#### Headers: Authorization: Bearer user1 (где user1 — значение поля access_token, полученного при логине)

### 4. Обновление профиля пользователя
#### Method: PUT
#### URL: http://localhost:8000/profile
#### Headers:Content-Type: application/json, Authorization: Bearer user1
#### Пример запроса (Body: raw, JSON):
#### {
####   "first_name": "Пётр",
####   "last_name": "Петров",
####   "date_of_birth": "1985-05-05",
####   "email": "peter@example.com",
####   "phone": "+79876543210"
#### }