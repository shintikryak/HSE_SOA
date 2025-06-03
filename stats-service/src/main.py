import grpc
from concurrent import futures
from stats_pb2 import (
  CountResponse, TrendResponse, TrendPoint,
  TopPostsResponse, TopUsersResponse, TopPost, TopUser, Metric
)
import stats_pb2_grpc as pb2_grpc
from database import client, create_events_table
from kafka_consumer import run as consume_loop
from threading import Thread
from datetime import date

class StatsServicer(pb2_grpc.StatsServiceServicer):
    def GetPostCounts(self, req, ctx):
        q = client.execute(
            "SELECT metric, count() FROM events WHERE post_id=%(pid)s GROUP BY metric",
            {"pid": req.post_id}
        )
        m = {row[0]: row[1] for row in q}
        return CountResponse(
          views   = m.get("views", 0),
          likes   = m.get("likes", 0),
          comments= m.get("comments", 0)
        )

    def GetPostViewsTrend(self, req, ctx):
        return self._trend(req.post_id, "views")

    def GetPostLikesTrend(self, req, ctx):
        return self._trend(req.post_id, "likes")

    def GetPostCommentsTrend(self, req, ctx):
        return self._trend(req.post_id, "comments")

    def _trend(self, post_id, metric):
        rows = client.execute(f"""
          SELECT event_date, count() 
          FROM events 
          WHERE post_id=%(pid)s AND metric=%(mt)s
          GROUP BY event_date 
          ORDER BY event_date
        """, {"pid": post_id, "mt": metric})
        return TrendResponse(data=[
          TrendPoint(date=r[0].strftime("%Y-%m-%d"), count=r[1]) for r in rows
        ])

    def GetTopPosts(self, req, ctx):
        try:
            metric_str = Metric.Name(req.metric).lower()
        except ValueError:
            ctx.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            ctx.set_details(f"Unknown metric: {req.metric}")
            return TopPostsResponse()
        rows = client.execute(
            """
            SELECT post_id, count() AS cnt
            FROM events
            WHERE metric = %(mt)s
            GROUP BY post_id
            ORDER BY cnt DESC
            LIMIT 10
            """,
            {"mt": metric_str}
        )
        return TopPostsResponse(
            posts=[TopPost(post_id=r[0], count=r[1]) for r in rows]
        )

    def GetTopUsers(self, req, ctx):
        try:
            metric_str = Metric.Name(req.metric).lower()
        except ValueError:
            ctx.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            ctx.set_details(f"Unknown metric: {req.metric}")
            return TopUsersResponse()
        rows = client.execute(
            """
            SELECT user_id, count() AS cnt
            FROM events
            WHERE metric = %(mt)s
            GROUP BY user_id
            ORDER BY cnt DESC
            LIMIT 10
            """,
            {"mt": metric_str}
        )
        return TopUsersResponse(
            users=[TopUser(user_id=r[0], count=r[1]) for r in rows]
        )


def serve():
    create_events_table()
    # стартим консьюмер в фоне
    Thread(target=consume_loop, daemon=True).start()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_StatsServiceServicer_to_server(StatsServicer(), server)
    server.add_insecure_port('[::]:50052')
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
