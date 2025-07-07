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

# 导入基础模块
from pydantic import BaseModel
from typing import List, Dict, Any

# 导入路由
from .api import mahjong
from .api.v1 import replay
from .websocket import routes as websocket_routes

# 初始化变量
hand_analyzer_available = False
comprehensive_analyzer_available = False

# 尝试导入手牌分析器
try:
    from .api import hand_analyzer
    hand_analyzer_available = True
    print("✅ 手牌分析器模块导入成功")
except ImportError as e:
    print(f"❌ 手牌分析器模块导入失败: {e}")
    hand_analyzer_available = False

# 尝试导入综合手牌分析器
try:
    from .api import comprehensive_hand_analyzer
    comprehensive_analyzer_available = True
    print("✅ 综合手牌分析器模块导入成功")
except ImportError as e:
    print(f"❌ 综合手牌分析器模块导入失败: {e}")
    comprehensive_analyzer_available = False

# 注册HTTP API路由
app.include_router(mahjong.router, prefix="/api/mahjong", tags=["mahjong"])
app.include_router(replay.router, prefix="/api/v1/replay", tags=["replay"])

if hand_analyzer_available:
    app.include_router(hand_analyzer.router, prefix="/api/mahjong", tags=["hand-analyzer"])
    print("✅ 手牌分析器路由注册成功")
else:
    print("❌ 手牌分析器路由跳过注册")

if comprehensive_analyzer_available:
    app.include_router(comprehensive_hand_analyzer.router, prefix="/api/mahjong", tags=["comprehensive-analyzer"])
    print("✅ 综合手牌分析器路由注册成功")
else:
    print("❌ 综合手牌分析器路由跳过注册")

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

@app.get("/api/debug/routes")
async def debug_routes():
    """调试路由"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if route.methods else []
            })
    return {"routes": routes}

# 备用手牌分析端点（如果主要模块导入失败）
if not hand_analyzer_available:
    class FallbackHandAnalysisRequest(BaseModel):
        tiles: List[str]
        melds: List[Dict] = []
    
    @app.post("/api/mahjong/analyze-hand")
    async def fallback_analyze_hand(request: FallbackHandAnalysisRequest):
        """备用手牌分析端点"""
        return {
            "is_winning": False,
            "shanten": 8,
            "effective_draws": [],
            "winning_tiles": [],
            "detailed_analysis": {
                "current_shanten": 8,
                "patterns": ["MahjongKit导入失败"],
                "suggestions": ["❌ 分析功能暂时不可用，请检查后端配置"]
            }
        }
    
    print("✅ 备用手牌分析端点已注册")


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