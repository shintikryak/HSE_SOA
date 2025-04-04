from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
import grpc
import post_pb2
import post_pb2_grpc

router = APIRouter(tags=["Posts"])

# Pydantic модели для запросов и ответов
class PostCreate(BaseModel):
    title: str = Field(..., description="Заголовок поста")
    description: Optional[str] = Field("", description="Описание поста")
    is_private: bool = Field(False, description="Флаг приватности")
    tags: Optional[List[str]] = Field(default_factory=list, description="Список тегов")

class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Заголовок поста")
    description: Optional[str] = Field(None, description="Описание поста")
    is_private: Optional[bool] = Field(None, description="Флаг приватности")
    tags: Optional[List[str]] = Field(None, description="Список тегов")

class PostOut(BaseModel):
    id: str
    title: str
    description: Optional[str]
    creator_id: int
    created_at: str
    updated_at: str
    is_private: bool
    tags: List[str]

class PostList(BaseModel):
    posts: List[PostOut]
    total: int

# Зависимость для получения текущего пользователя (можно будет потом заменить на реальную логику)
def get_current_user():
    # Для демонстрации возвращаем тестового пользователя
    return {"id": 1}

# Функция для создания gRPC-канала и клиента к post-service
def get_post_service_stub():
    channel = grpc.insecure_channel("post-service:50051")
    stub = post_pb2_grpc.PostServiceStub(channel)
    return stub

@router.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate, current_user: dict = Depends(get_current_user)):
    stub = get_post_service_stub()
    grpc_post = post_pb2.Post(
        title=post.title,
        description=post.description or "",
        creator_id=current_user["id"],
        created_at="",
        updated_at="",
        is_private=post.is_private,
        tags=post.tags
    )
    request_grpc = post_pb2.CreatePostRequest(post=grpc_post)
    response = stub.CreatePost(request_grpc)
    if response.error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.error)
    return PostOut(
        id=response.post.id,
        title=response.post.title,
        description=response.post.description,
        creator_id=response.post.creator_id,
        created_at=response.post.created_at,
        updated_at=response.post.updated_at,
        is_private=response.post.is_private,
        tags=response.post.tags
    )

@router.delete("/posts/{post_id}", response_model=PostOut)
async def delete_post(post_id: str, current_user: dict = Depends(get_current_user)):
    stub = get_post_service_stub()
    request_grpc = post_pb2.DeletePostRequest(id=post_id, user_id=current_user["id"])
    response = stub.DeletePost(request_grpc)
    if response.error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.error)
    return PostOut(
        id=response.post.id,
        title=response.post.title,
        description=response.post.description,
        creator_id=response.post.creator_id,
        created_at=response.post.created_at,
        updated_at=response.post.updated_at,
        is_private=response.post.is_private,
        tags=response.post.tags
    )

@router.put("/posts/{post_id}", response_model=PostOut)
async def update_post(post_id: str, post: PostUpdate, current_user: dict = Depends(get_current_user)):
    stub = get_post_service_stub()
    grpc_post = post_pb2.Post(
        id=post_id,
        title=post.title or "",
        description=post.description or "",
        creator_id=current_user["id"],
        created_at="",
        updated_at="",
        is_private=post.is_private if post.is_private is not None else False,
        tags=post.tags if post.tags is not None else []
    )
    request_grpc = post_pb2.UpdatePostRequest(post=grpc_post)
    response = stub.UpdatePost(request_grpc)
    if response.error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.error)
    return PostOut(
        id=response.post.id,
        title=response.post.title,
        description=response.post.description,
        creator_id=response.post.creator_id,
        created_at=response.post.created_at,
        updated_at=response.post.updated_at,
        is_private=response.post.is_private,
        tags=response.post.tags
    )

@router.get("/posts/{post_id}", response_model=PostOut)
async def get_post(post_id: str, current_user: dict = Depends(get_current_user)):
    stub = get_post_service_stub()
    request_grpc = post_pb2.GetPostRequest(id=post_id, user_id=current_user["id"])
    response = stub.GetPost(request_grpc)
    if response.error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=response.error)
    return PostOut(
        id=response.post.id,
        title=response.post.title,
        description=response.post.description,
        creator_id=response.post.creator_id,
        created_at=response.post.created_at,
        updated_at=response.post.updated_at,
        is_private=response.post.is_private,
        tags=response.post.tags
    )

@router.get("/posts", response_model=PostList)
async def list_posts(page: int = 1, size: int = 10, current_user: dict = Depends(get_current_user)):
    stub = get_post_service_stub()
    request_grpc = post_pb2.ListPostsRequest(page=page, size=size, user_id=current_user["id"])
    response = stub.ListPosts(request_grpc)
    if response.error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.error)
    posts = [PostOut(
        id=p.id,
        title=p.title,
        description=p.description,
        creator_id=p.creator_id,
        created_at=p.created_at,
        updated_at=p.updated_at,
        is_private=p.is_private,
        tags=p.tags
    ) for p in response.posts]
    return PostList(posts=posts, total=response.total)
