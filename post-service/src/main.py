import grpc
from concurrent import futures
from datetime import datetime
import post_pb2
import post_pb2_grpc
from database import SessionLocal, engine, Base
from models import Post as PostModel
from sqlalchemy.exc import SQLAlchemyError

# Создаем таблицы в БД, если они не существуют
Base.metadata.create_all(bind=engine)

class PostServiceServicer(post_pb2_grpc.PostServiceServicer):
    def CreatePost(self, request, context):
        db = SessionLocal()
        try:
            p = request.post
            new_post = PostModel(
                title=p.title,
                description=p.description,
                creator_id=p.creator_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_private=p.is_private,
                tags=p.tags
            )
            db.add(new_post)
            db.commit()
            db.refresh(new_post)
            grpc_post = post_pb2.Post(
                id=str(new_post.id),
                title=new_post.title,
                description=new_post.description,
                creator_id=new_post.creator_id,
                created_at=new_post.created_at.isoformat(),
                updated_at=new_post.updated_at.isoformat(),
                is_private=new_post.is_private,
                tags=new_post.tags or []
            )
            return post_pb2.PostResponse(post=grpc_post)
        except SQLAlchemyError as e:
            db.rollback()
            return post_pb2.PostResponse(error=str(e))
        finally:
            db.close()

    def DeletePost(self, request, context):
        db = SessionLocal()
        try:
            post_id = int(request.id)
            user_id = request.user_id
            post_obj = db.query(PostModel).filter(PostModel.id == post_id).first()
            if not post_obj:
                return post_pb2.PostResponse(error="Post not found")
            if post_obj.creator_id != user_id:
                return post_pb2.PostResponse(error="Unauthorized")
            grpc_post = post_pb2.Post(
                id=str(post_obj.id),
                title=post_obj.title,
                description=post_obj.description,
                creator_id=post_obj.creator_id,
                created_at=post_obj.created_at.isoformat(),
                updated_at=post_obj.updated_at.isoformat(),
                is_private=post_obj.is_private,
                tags=post_obj.tags or []
            )
            db.delete(post_obj)
            db.commit()
            return post_pb2.PostResponse(post=grpc_post)
        except SQLAlchemyError as e:
            db.rollback()
            return post_pb2.PostResponse(error=str(e))
        finally:
            db.close()

    def UpdatePost(self, request, context):
        db = SessionLocal()
        try:
            p = request.post
            post_id = int(p.id)
            post_obj = db.query(PostModel).filter(PostModel.id == post_id).first()
            if not post_obj:
                return post_pb2.PostResponse(error="Post not found")
            if post_obj.creator_id != p.creator_id:
                return post_pb2.PostResponse(error="Unauthorized")
            post_obj.title = p.title or post_obj.title
            post_obj.description = p.description or post_obj.description
            post_obj.is_private = p.is_private
            post_obj.tags = p.tags if p.tags else post_obj.tags
            post_obj.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(post_obj)
            grpc_post = post_pb2.Post(
                id=str(post_obj.id),
                title=post_obj.title,
                description=post_obj.description,
                creator_id=post_obj.creator_id,
                created_at=post_obj.created_at.isoformat(),
                updated_at=post_obj.updated_at.isoformat(),
                is_private=post_obj.is_private,
                tags=post_obj.tags or []
            )
            return post_pb2.PostResponse(post=grpc_post)
        except SQLAlchemyError as e:
            db.rollback()
            return post_pb2.PostResponse(error=str(e))
        finally:
            db.close()

    def GetPost(self, request, context):
        db = SessionLocal()
        try:
            post_id = int(request.id)
            user_id = request.user_id
            post_obj = db.query(PostModel).filter(PostModel.id == post_id).first()
            if not post_obj:
                return post_pb2.PostResponse(error="Post not found")
            if post_obj.is_private and post_obj.creator_id != user_id:
                return post_pb2.PostResponse(error="Unauthorized")
            grpc_post = post_pb2.Post(
                id=str(post_obj.id),
                title=post_obj.title,
                description=post_obj.description,
                creator_id=post_obj.creator_id,
                created_at=post_obj.created_at.isoformat(),
                updated_at=post_obj.updated_at.isoformat(),
                is_private=post_obj.is_private,
                tags=post_obj.tags or []
            )
            return post_pb2.PostResponse(post=grpc_post)
        except SQLAlchemyError as e:
            return post_pb2.PostResponse(error=str(e))
        finally:
            db.close()

    def ListPosts(self, request, context):
        db = SessionLocal()
        try:
            page = request.page
            size = request.size
            user_id = request.user_id
            query = db.query(PostModel)
            # Фильтруем: показываем посты, если они не приватные или принадлежат пользователю
            query = query.filter((PostModel.is_private == False) | (PostModel.creator_id == user_id))
            total = query.count()
            posts = query.offset((page - 1) * size).limit(size).all()
            grpc_posts = []
            for post_obj in posts:
                grpc_post = post_pb2.Post(
                    id=str(post_obj.id),
                    title=post_obj.title,
                    description=post_obj.description,
                    creator_id=post_obj.creator_id,
                    created_at=post_obj.created_at.isoformat(),
                    updated_at=post_obj.updated_at.isoformat(),
                    is_private=post_obj.is_private,
                    tags=post_obj.tags or []
                )
                grpc_posts.append(grpc_post)
            return post_pb2.ListPostsResponse(posts=grpc_posts, total=total)
        except SQLAlchemyError as e:
            return post_pb2.ListPostsResponse(error=str(e))
        finally:
            db.close()

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    post_pb2_grpc.add_PostServiceServicer_to_server(PostServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Post-service gRPC сервер запущен на порту 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
