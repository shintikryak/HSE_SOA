import pytest
from fastapi import HTTPException, status, FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace
import httpx

from src.posts import (
    router,
    validate_jwt_token,
    get_post_service_stub,
    PostCreate,
    PostUpdate,
)

app = FastAPI()
app.include_router(router, prefix="/posts")
client = TestClient(app)

@pytest.mark.asyncio
async def test_validate_jwt_token_success(monkeypatch):
    dummy_response = MagicMock()
    dummy_response.raise_for_status = MagicMock()
    dummy_response.json = MagicMock(return_value={"id": 123})
    
    async def dummy_get(*args, **kwargs):
        return dummy_response
    
    dummy_async_client = MagicMock()
    dummy_async_client.__aenter__.return_value = dummy_async_client
    dummy_async_client.get = AsyncMock(side_effect=dummy_get)
    
    monkeypatch.setattr("src.posts.httpx.AsyncClient", lambda: dummy_async_client)
    
    token = "dummy_token"
    result = await validate_jwt_token(token)
    assert result == {"id": 123}

@pytest.mark.asyncio
async def test_validate_jwt_token_failure(monkeypatch):
    async def dummy_get(*args, **kwargs):
        raise httpx.HTTPError("Invalid token")
    
    dummy_async_client = MagicMock()
    dummy_async_client.__aenter__.return_value = dummy_async_client
    dummy_async_client.get = AsyncMock(side_effect=dummy_get)
    
    monkeypatch.setattr("src.posts.httpx.AsyncClient", lambda: dummy_async_client)
    
    token = "invalid_token"
    with pytest.raises(HTTPException) as exc_info:
        await validate_jwt_token(token)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

def dummy_create_post(request):
    dummy_post = SimpleNamespace(
         id="1",
         title=request.post.title,
         description=request.post.description,
         creator_id=request.post.creator_id,
         created_at="2023-01-01T00:00:00",
         updated_at="2023-01-01T00:00:00",
         is_private=request.post.is_private,
         tags=request.post.tags,
    )
    return SimpleNamespace(error="", post=dummy_post)

@patch("src.posts.validate_jwt_token", new_callable=AsyncMock)
@patch("src.posts.get_post_service_stub")
def test_create_post_success(mock_get_stub, mock_validate_token):
    mock_validate_token.return_value = {"id": 123}
    
    dummy_stub = MagicMock()
    dummy_stub.CreatePost = MagicMock(side_effect=dummy_create_post)
    mock_get_stub.return_value = dummy_stub
    
    post_data = {
         "title": "Test Post",
         "description": "A test post",
         "is_private": False,
         "tags": ["test", "post"]
    }
    headers = {"Authorization": "Bearer dummy_token"}
    response = client.post("/posts", json=post_data, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "Test Post"
    assert data["creator_id"] == 123

def dummy_list_posts(request):
    dummy_post = SimpleNamespace(
         id="1",
         title="Test Post",
         description="A test post",
         creator_id=request.user_id,
         created_at="2023-01-01T00:00:00",
         updated_at="2023-01-01T00:00:00",
         is_private=False,
         tags=["test", "post"],
    )
    return SimpleNamespace(error="", posts=[dummy_post], total=1)

@patch("src.posts.validate_jwt_token", new_callable=AsyncMock)
@patch("src.posts.get_post_service_stub")
def test_list_posts_success(mock_get_stub, mock_validate_token):
    mock_validate_token.return_value = {"id": 123}
    
    dummy_stub = MagicMock()
    dummy_stub.ListPosts = MagicMock(side_effect=dummy_list_posts)
    mock_get_stub.return_value = dummy_stub
    
    headers = {"Authorization": "Bearer dummy_token"}
    response = client.get("/posts", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["posts"]) == 1
    assert data["posts"][0]["title"] == "Test Post"

def dummy_get_post(request):
    dummy_post = SimpleNamespace(
         id=request.id,
         title="Test Post",
         description="A test post",
         creator_id=request.user_id,
         created_at="2023-01-01T00:00:00",
         updated_at="2023-01-01T00:00:00",
         is_private=False,
         tags=["test", "post"],
    )
    return SimpleNamespace(error="", post=dummy_post)

@patch("src.posts.validate_jwt_token", new_callable=AsyncMock)
@patch("src.posts.get_post_service_stub")
def test_get_post_success(mock_get_stub, mock_validate_token):
    mock_validate_token.return_value = {"id": 123}
    
    dummy_stub = MagicMock()
    dummy_stub.GetPost = MagicMock(side_effect=dummy_get_post)
    mock_get_stub.return_value = dummy_stub
    
    headers = {"Authorization": "Bearer dummy_token"}
    response = client.get("/posts/1", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "1"
    assert data["title"] == "Test Post"

def dummy_update_post(request):
    dummy_post = SimpleNamespace(
         id=request.post.id,
         title=request.post.title if request.post.title else "Old Title",
         description=request.post.description if request.post.description else "Old Description",
         creator_id=request.post.creator_id,
         created_at="2023-01-01T00:00:00",
         updated_at="2023-01-02T00:00:00",
         is_private=request.post.is_private,
         tags=request.post.tags,
    )
    return SimpleNamespace(error="", post=dummy_post)

@patch("src.posts.validate_jwt_token", new_callable=AsyncMock)
@patch("src.posts.get_post_service_stub")
def test_update_post_success(mock_get_stub, mock_validate_token):
    mock_validate_token.return_value = {"id": 123}
    
    dummy_stub = MagicMock()
    dummy_stub.UpdatePost = MagicMock(side_effect=dummy_update_post)
    mock_get_stub.return_value = dummy_stub
    
    update_data = {
         "title": "Updated Title",
         "description": "Updated Description",
         "is_private": True,
         "tags": ["updated", "post"]
    }
    headers = {"Authorization": "Bearer dummy_token"}
    response = client.put("/posts/1", json=update_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["is_private"] is True

def dummy_delete_post(request):
    dummy_post = SimpleNamespace(
         id=request.id,
         title="Deleted Post",
         description="A deleted post",
         creator_id=request.user_id,
         created_at="2023-01-01T00:00:00",
         updated_at="2023-01-01T00:00:00",
         is_private=False,
         tags=["deleted"],
    )
    return SimpleNamespace(error="", post=dummy_post)

@patch("src.posts.validate_jwt_token", new_callable=AsyncMock)
@patch("src.posts.get_post_service_stub")
def test_delete_post_success(mock_get_stub, mock_validate_token):
    mock_validate_token.return_value = {"id": 123}
    
    dummy_stub = MagicMock()
    dummy_stub.DeletePost = MagicMock(side_effect=dummy_delete_post)
    mock_get_stub.return_value = dummy_stub
    
    headers = {"Authorization": "Bearer dummy_token"}
    response = client.delete("/posts/1", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Deleted Post"
