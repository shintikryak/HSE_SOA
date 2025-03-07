import os
import jwt
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Устанавливаем переменную окружения для тестовой базы, чтобы не пытаться подключаться к "db"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from src.main import app, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, get_db, get_current_user

client = TestClient(app)

# Фейковый пользователь для тестов
class DummyUser:
    def __init__(self):
        self.id = 1
        self.login = "testuser"
        self.email = "testuser@example.com"
        self.hashed_password = "fakehashed"
        self.first_name = "Test"
        self.last_name = "User"
        self.date_of_birth = datetime(1990, 1, 1).date()
        self.phone = "1234567890"
        self.created_at = datetime(2025, 3, 3, 12, 0, 0)
        self.updated_at = datetime(2025, 3, 3, 12, 0, 0)

dummy_user = DummyUser()

# Переопределим зависимость get_db, чтобы возвращалась фейковая сессия
def fake_get_db():
    fake_db = MagicMock()
    fake_db.add = MagicMock()
    fake_db.commit = MagicMock()
    # Определяем функцию refresh, которая устанавливает id в 1
    def fake_refresh(user):
        user.id = 1
    fake_db.refresh.side_effect = fake_refresh
    yield fake_db

app.dependency_overrides[get_db] = fake_get_db

# Тест успешной регистрации
def test_register_success():
    # Патчим функции проверки существования пользователя
    with patch("src.main.get_user_by_login", return_value=None), \
         patch("src.main.get_user_by_email", return_value=None):
        
        payload = {
            "login": "newuser",
            "password": "newpass",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "date_of_birth": "1995-05-05",
            "phone": "0987654321"
        }
        response = client.post("/register", json=payload)
        # Ожидаем статус 200
        assert response.status_code == 200, response.text
        data = response.json()
        # Проверяем, что возвращенный пользователь имеет установленные поля, и id равен 1 (установленный fake_refresh)
        assert data["login"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["id"] == 1

# Остальные тесты (пример)
def test_login_success():
    with patch("src.main.authenticate_user", return_value=dummy_user):
        form_data = {"username": "testuser", "password": "pass"}
        response = client.post("/login", data=form_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        token = data["access_token"]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload.get("sub") == "testuser"

def test_get_profile():
    # Переопределяем get_current_user, чтобы возвращался dummy_user
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    response = client.get("/profile", headers={"Authorization": "Bearer faketoken"})
    assert response.status_code == 200
    data = response.json()
    assert data["login"] == dummy_user.login
    app.dependency_overrides.pop(get_current_user, None)

def test_update_profile():
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    with patch("src.main.get_user_by_email", return_value=None):
        update_data = {
            "first_name": "Updated",
            "last_name": "User",
            "date_of_birth": "2000-01-01",
            "email": "updated@example.com",
            "phone": "1112223333"
        }
        response = client.put("/profile", json=update_data, headers={"Authorization": "Bearer faketoken"})
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
        assert data["email"] == "updated@example.com"
    app.dependency_overrides.pop(get_current_user, None)
