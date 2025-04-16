from fastapi import APIRouter, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing import List, Optional
import httpx
import grpc
import post_pb2
import post_pb2_grpc

router = APIRouter(tags=["Posts"])

# Объявляем схему OAuth2.
# tokenUrl указывает на внешний адрес логина user‑сервиса,
# чтобы Swagger знал, куда отправлять запрос за токеном.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost:8001/login")

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

# Функция проверки JWT: отправляем запрос к user‑сервису для валидации токена.
async def validate_jwt_token(token: str) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "http://user-service/profile",
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
        except httpx.HTTPError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return response.json()

# Функция для получения gRPC‑клиента к post‑сервису.
def get_post_service_stub():
    channel = grpc.insecure_channel("post-service:50051")
    return post_pb2_grpc.PostServiceStub(channel)

# Эндпоинты защищены схемой OAuth2: параметр token берётся через Security(oauth2_scheme).
@router.post("", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post(
    post: PostCreate,
    token: str = Security(oauth2_scheme)
):
    user_data = await validate_jwt_token(token)
    stub = get_post_service_stub()
    grpc_post = post_pb2.Post(
        title=post.title,
        description=post.description,
        creator_id=user_data["id"],
        created_at="",
        updated_at="",
        is_private=post.is_private,
        tags=post.tags
    )
    req = post_pb2.CreatePostRequest(post=grpc_post)
    resp = stub.CreatePost(req)
    if resp.error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resp.error)
    return PostOut(
        id=resp.post.id,
        title=resp.post.title,
        description=resp.post.description,
        creator_id=resp.post.creator_id,
        created_at=resp.post.created_at,
        updated_at=resp.post.updated_at,
        is_private=resp.post.is_private,
        tags=resp.post.tags
    )

@router.get("", response_model=PostList)
async def list_posts(
    page: int = 1,
    size: int = 10,
    token: str = Security(oauth2_scheme)
):
    user_data = await validate_jwt_token(token)
    stub = get_post_service_stub()
    req = post_pb2.ListPostsRequest(page=page, size=size, user_id=user_data["id"])
    resp = stub.ListPosts(req)
    if resp.error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resp.error)
    posts = [
        PostOut(
            id=p.id,
            title=p.title,
            description=p.description,
            creator_id=p.creator_id,
            created_at=p.created_at,
            updated_at=p.updated_at,
            is_private=p.is_private,
            tags=p.tags
        ) for p in resp.posts
    ]
    return PostList(posts=posts, total=resp.total)

@router.get("/{post_id}", response_model=PostOut)
async def get_post(
    post_id: str,
    token: str = Security(oauth2_scheme)
):
    user_data = await validate_jwt_token(token)
    stub = get_post_service_stub()
    req = post_pb2.GetPostRequest(id=post_id, user_id=user_data["id"])
    resp = stub.GetPost(req)
    if resp.error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=resp.error)
    return PostOut(
        id=resp.post.id,
        title=resp.post.title,
        description=resp.post.description,
        creator_id=resp.post.creator_id,
        created_at=resp.post.created_at,
        updated_at=resp.post.updated_at,
        is_private=resp.post.is_private,
        tags=resp.post.tags
    )

@router.put("/{post_id}", response_model=PostOut)
async def update_post(
    post_id: str,
    post: PostUpdate,
    token: str = Security(oauth2_scheme)
):
    user_data = await validate_jwt_token(token)
    stub = get_post_service_stub()
    grpc_post = post_pb2.Post(
        id=post_id,
        title=post.title or "",
        description=post.description or "",
        creator_id=user_data["id"],
        created_at="",
        updated_at="",
        is_private=post.is_private if post.is_private is not None else False,
        tags=post.tags or []
    )
    req = post_pb2.UpdatePostRequest(post=grpc_post)
    resp = stub.UpdatePost(req)
    if resp.error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resp.error)
    return PostOut(
        id=resp.post.id,
        title=resp.post.title,
        description=resp.post.description,
        creator_id=resp.post.creator_id,
        created_at=resp.post.created_at,
        updated_at=resp.post.updated_at,
        is_private=resp.post.is_private,
        tags=resp.post.tags
    )

@router.delete("/{post_id}", response_model=PostOut)
async def delete_post(
    post_id: str,
    token: str = Security(oauth2_scheme)
):
    user_data = await validate_jwt_token(token)
    stub = get_post_service_stub()
    req = post_pb2.DeletePostRequest(id=post_id, user_id=user_data["id"])
    resp = stub.DeletePost(req)
    if resp.error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resp.error)
    return PostOut(
        id=resp.post.id,
        title=resp.post.title,
        description=resp.post.description,
        creator_id=resp.post.creator_id,
        created_at=resp.post.created_at,
        updated_at=resp.post.updated_at,
        is_private=resp.post.is_private,
        tags=resp.post.tags
    )
