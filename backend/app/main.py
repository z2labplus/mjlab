from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# 创建FastAPI应用
app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入路由
from .api import mahjong
from .api.v1 import replay
from .websocket import routes as websocket_routes

# 注册HTTP API路由
app.include_router(mahjong.router, prefix="/api/mahjong", tags=["mahjong"])
app.include_router(replay.router, prefix="/api/v1/replay", tags=["replay"])

# 注册WebSocket路由
app.include_router(websocket_routes.router, prefix="/api", tags=["websocket"])

# 静态文件服务（如果需要）
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "血战麻将游戏服务器",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "message": "API 服务正常运行"
    }


@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    print("🀄 欢乐麻将辅助工具 API 已启动")
    print("📚 API文档地址: http://localhost:8000/docs")
    print("🔌 WebSocket连接地址: ws://localhost:8000/api/ws")


@app.on_event("shutdown") 
async def shutdown_event():
    """应用关闭时的清理"""
    print("🀄 欢乐麻将辅助工具 API 已关闭")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 