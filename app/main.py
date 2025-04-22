# app/main.py
import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.src.domain.user.v1 import router as user_router

app = FastAPI()

# static 디렉토리 경로 설정 (app 디렉토리 기준)
static_dir = os.path.join(os.path.dirname(__file__), "../static")

# /static 경로를 static 디렉토리에 마운트
app.mount("/static", StaticFiles(directory=static_dir), name="static")


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


app.include_router(user_router.router, prefix="/api")
