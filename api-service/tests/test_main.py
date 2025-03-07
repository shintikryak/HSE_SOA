import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.main import app

client = TestClient(app)

@patch("httpx.AsyncClient.request")
def test_proxy_get(mock_request):
    """Проверяем, что GET-запрос проксируется корректно."""
    # Настраиваем mock-объект (имитируем ответ от user-service)
    mock_response = MagicMock()
    mock_response.content = b"Hello from user-service"
    mock_response.status_code = 200
    mock_response.headers = {}
    mock_request.return_value = mock_response

    # Отправляем GET-запрос на /test (любой путь)
    response = client.get("/test")

    # Проверяем, что прокси вернул тот же статус и тело
    assert response.status_code == 200
    assert response.text == "Hello from user-service"

    # Дополнительно можно проверить, что httpx.AsyncClient.request вызван с нужными параметрами
    mock_request.assert_called_once()
    args, kwargs = mock_request.call_args
    assert args[0] == "GET"
    assert "http://user-service/test" in args[1]

@patch("httpx.AsyncClient.request")
def test_proxy_post(mock_request):
    """Проверяем, что POST-запрос проксируется корректно."""
    mock_response = MagicMock()
    mock_response.content = b"Created"
    mock_response.status_code = 201
    mock_response.headers = {}
    mock_request.return_value = mock_response

    # Отправляем POST-запрос с JSON-данными
    data = {"hello": "world"}
    response = client.post("/create", json=data)

    assert response.status_code == 201
    assert response.text == "Created"

    # Проверяем параметры вызова httpx.AsyncClient.request
    mock_request.assert_called_once()
    args, kwargs = mock_request.call_args
    assert args[0] == "POST"
    assert "http://user-service/create" in args[1]
    # При желании можно проверить передаваемое тело (kwargs["content"])
    assert b'"hello":"world"' in kwargs["content"]
