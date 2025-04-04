from fastapi import FastAPI, Request, Response
import httpx
from posts import router as posts_router

app = FastAPI(title="API Proxy Service")

app.include_router(posts_router)

USER_SERVICE_URL = "http://user-service"

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(request: Request, path: str):
    async with httpx.AsyncClient() as client:
        url = f"{USER_SERVICE_URL}/{path}"
        method = request.method
        headers = dict(request.headers)
        headers.pop("host", None)
        body = await request.body()
        response = await client.request(method, url, headers=headers, content=body)
    return Response(content=response.content, status_code=response.status_code, headers=response.headers)
