from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from data_loader import load_papers
import subprocess
import sys
from pathlib import Path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


# 👇 挂载静态文件（css/js等）
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# 👇 首页返回 index.html（关键）
@app.get("/")
def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")


# 👇 API：获取论文
@app.get("/api/papers")
def get_papers():
    return load_papers()


# 👇 API：刷新数据（可选，后面可以关掉）
@app.post("/api/refresh")
def refresh_papers():
    try:
        result = subprocess.run(
            [sys.executable, "scripts/run_pipeline.py"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )

        if result.returncode != 0:
            return {
                "success": False,
                "message": "Pipeline 执行失败",
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        return {
            "success": True,
            "message": "Pipeline 执行成功",
            "stdout": result.stdout,
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"执行 refresh 时发生异常: {str(e)}"
        }