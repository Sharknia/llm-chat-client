# app/main.py
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# FastAPI 앱 시작 시 .env 파일 로드
load_dotenv()
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


# WebSocket 엔드포인트 등 추가 로직은 여기에...
