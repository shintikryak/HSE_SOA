from fastapi import APIRouter, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import List
import grpc
import stats_pb2, stats_pb2_grpc

router = APIRouter(tags=["Statistics"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost:8001/login")

def parse_metric(metric: str) -> int:
    """
    Преобразует строку metric ('views', 'likes', 'comments')
    в целочисленное значение protobuf-ENUM-а.
    """
    key = metric.upper()
    if key not in stats_pb2.Metric.keys():
        raise HTTPException(status_code=400, detail=f"Unknown metric '{metric}'")
    return stats_pb2.Metric.Value(key)

# схемы ответов
class Counts(BaseModel):
    views: int
    likes: int
    comments: int

class TrendPoint(BaseModel):
    date: str
    count: int

class TrendResp(BaseModel):
    data: List[TrendPoint]

class TopItem(BaseModel):
    id: str
    count: int

class TopResp(BaseModel):
    items: List[TopItem]

def get_stats_stub():
    channel = grpc.insecure_channel("stats-service:50052")
    return stats_pb2_grpc.StatsServiceStub(channel)

# 1. Counts
@router.get("/stats/posts/{post_id}/counts", response_model=Counts)
def get_counts(post_id: str, token: str = Security(oauth2_scheme)):
    stub = get_stats_stub()
    resp = stub.GetPostCounts(stats_pb2.PostId(post_id=post_id))
    return Counts(views=resp.views, likes=resp.likes, comments=resp.comments)

# 2–4. Trends
@router.get("/stats/posts/{post_id}/trend/{metric}", response_model=TrendResp)
def get_trend(post_id: str, metric: str, token: str = Security(oauth2_scheme)):
    stub = get_stats_stub()
    req = stats_pb2.TrendRequest(post_id=post_id)
    fn = {
      "views":   stub.GetPostViewsTrend,
      "likes":   stub.GetPostLikesTrend,
      "comments":stub.GetPostCommentsTrend
    }.get(metric)
    if not fn:
        raise HTTPException(400, "Unknown metric")
    resp = fn(req)
    return TrendResp(data=[TrendPoint(date=p.date, count=p.count) for p in resp.data])

# 5. Top posts
@router.get("/stats/top/posts/{metric}", response_model=TopResp)
def top_posts(metric: str, token: str = Security(oauth2_scheme)):
    enum_val = parse_metric(metric)
    req = stats_pb2.TopRequest(metric=enum_val)
    stub = get_stats_stub()
    try:
        resp = stub.GetTopPosts(req)
    except grpc.RpcError as e:
        # если удалённый сервис упал — вернём 502 Bad Gateway
        raise HTTPException(status_code=502, detail=f"Stats RPC error: {e.details()}")

    items = [
        TopItem(id=p.post_id, count=p.count)
        for p in resp.posts
    ]
    return TopResp(items=items)

# 6. Top users
@router.get("/stats/top/users/{metric}", response_model=TopResp)
def top_users(metric: str, token: str = Security(oauth2_scheme)):
    enum_val = parse_metric(metric)
    req = stats_pb2.TopRequest(metric=enum_val)
    stub = get_stats_stub()
    try:
        resp = stub.GetTopUsers(req)
    except grpc.RpcError as e:
        raise HTTPException(status_code=502, detail=f"Stats RPC error: {e.details()}")

    items = [
        TopItem(id=str(u.user_id), count=u.count)
        for u in resp.users
    ]
    return TopResp(items=items)