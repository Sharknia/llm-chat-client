# app/main.py
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.src.core.exceptions.base_exceptions import BaseHTTPException
from app.src.core.logger import logger
from app.src.domain.user.v1 import router as user_router

app = FastAPI()

# static 디렉토리 경로 설정 (app 디렉토리 기준)
static_dir = os.path.join(os.path.dirname(__file__), "../static")

# /static 경로를 static 디렉토리에 마운트
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Lifespan 핸들러
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 애플리케이션 시작
    logger.info("애플리케이션 시작...")

    yield

    # 애플리케이션 종료
    logger.info("애플리케이션 종료...")


@app.get("/")
async def read_index():
    file_path = os.path.join(static_dir, "index.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        from fastapi.responses import HTMLResponse

        return HTMLResponse(
            content="<h1>Error: index.html not found</h1>", status_code=404
        )


@app.get("/login")
async def read_login():
    file_path = os.path.join(static_dir, "login.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        from fastapi.responses import HTMLResponse

        return HTMLResponse(
            content="<h1>Error: login.html not found</h1>", status_code=404
        )


@app.get("/signup")
async def read_signup():
    file_path = os.path.join(static_dir, "signup.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        from fastapi.responses import HTMLResponse

        return HTMLResponse(
            content="<h1>Error: signup.html not found</h1>", status_code=404
        )


# Custom OpenAPI 설정
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Your API Title",
        version="1.0.0",
        description="This is a custom OpenAPI schema",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# API 라우트 등록
app.include_router(user_router.router, prefix="/api/user")


@app.exception_handler(BaseHTTPException)
async def base_http_exception_handler(
    request: Request,
    exc: BaseHTTPException,
):
    # 로그 남기기
    logger.error(
        f"Error occurred: {exc.detail}, Status Code: {exc.status_code}, Description: {exc.description}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "description": exc.description,
            "detail": exc.detail,
        },
    )
