# app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from app.src.core.exceptions.base_exceptions import BaseHTTPException
from app.src.core.logger import logger
from app.src.domain.user.v1 import router as user_router

app = FastAPI()


# Lifespan 핸들러
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 애플리케이션 시작
    logger.info("애플리케이션 시작...")

    yield

    # 애플리케이션 종료
    logger.info("애플리케이션 종료...")


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
