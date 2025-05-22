import grpc
from concurrent import futures
from datetime import datetime

import post_pb2
import post_pb2_grpc

from database import SessionLocal, engine, Base
from models import Post as PostModel, Comment as CommentModel
from sqlalchemy.exc import SQLAlchemyError
from kafka_producer import publish

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
            query = query.filter((PostModel.is_private == False) | (PostModel.creator_id == user_id))
            total = query.count()
            posts = query.offset((page - 1) * size).limit(size).all()
            grpc_posts = []
            for post_obj in posts:
                grpc_posts.append(post_pb2.Post(
                    id=str(post_obj.id),
                    title=post_obj.title,
                    description=post_obj.description,
                    creator_id=post_obj.creator_id,
                    created_at=post_obj.created_at.isoformat(),
                    updated_at=post_obj.updated_at.isoformat(),
                    is_private=post_obj.is_private,
                    tags=post_obj.tags or []
                ))
            return post_pb2.ListPostsResponse(posts=grpc_posts, total=total)
        except SQLAlchemyError as e:
            return post_pb2.ListPostsResponse(error=str(e))
        finally:
            db.close()

    def ViewPost(self, request, context):
        # Публикация события в Kafka
        publish("post-view", {
            "post_id": request.post_id,
            "user_id": request.user_id,
            "viewed_at": datetime.utcnow().isoformat()
        })
        # Возвращаем стандартный ответ GetPost
        return self.GetPost(post_pb2.GetPostRequest(id=request.post_id, user_id=request.user_id), context)

    def LikePost(self, request, context):
        publish("post-like", {
            "post_id": request.post_id,
            "user_id": request.user_id,
            "liked_at": datetime.utcnow().isoformat()
        })
        return self.GetPost(post_pb2.GetPostRequest(id=request.post_id, user_id=request.user_id), context)

    def CommentPost(self, request, context):
        db = SessionLocal()
        try:
            comment = CommentModel(
                post_id=int(request.post_id),
                user_id=request.user_id,
                text=request.text,
                created_at=datetime.utcnow()
            )
            db.add(comment)
            db.commit()
            db.refresh(comment)
            grpc_comment = post_pb2.Comment(
                id=str(comment.id),
                post_id=request.post_id,
                user_id=comment.user_id,
                text=comment.text,
                created_at=comment.created_at.isoformat()
            )
            publish("post-comment", {
                "comment_id": comment.id,
                "post_id": comment.post_id,
                "user_id": comment.user_id,
                "commented_at": comment.created_at.isoformat()
            })
            return grpc_comment
        finally:
            db.close()

    def ListComments(self, request, context):
        db = SessionLocal()
        try:
            q = db.query(CommentModel).filter(CommentModel.post_id == int(request.post_id))
            total = q.count()
            items = q.offset((request.page - 1) * request.size).limit(request.size).all()
            grpc_list = [post_pb2.Comment(
                id=str(c.id),
                post_id=str(c.post_id),
                user_id=c.user_id,
                text=c.text,
                created_at=c.created_at.isoformat()
            ) for c in items]
            return post_pb2.ListCommentsResponse(comments=grpc_list, total=total)
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
