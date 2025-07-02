#!/usr/bin/env python3
"""
麻将辅助工具后端启动脚本
"""

import uvicorn
import redis
import sys
import time
from config import settings

def check_redis_connection():
    """检查Redis连接"""
    try:
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=True
        )
        r.ping()
        print(f"✅ Redis连接成功: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        return True
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        print("请确保Redis服务已启动")
        return False

def main():
    """主启动函数"""
    print("🀄 启动麻将辅助工具后端服务...")
    print(f"📡 API地址: http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"📚 API文档: http://localhost:{settings.API_PORT}/docs")
    print("-" * 50)
    
    # 检查Redis连接
    if not check_redis_connection():
        print("\n请按以下步骤启动Redis:")
        print("1. Docker方式: docker run --name redis-server -p 6379:6379 -d redis:7-alpine")
        print("2. WSL方式: wsl 然后 sudo service redis-server start")
        print("3. Windows方式: 启动redis-server.exe")
        sys.exit(1)
    
    print("✅ 所有依赖检查通过，正在启动服务器...")
    time.sleep(1)
    
    # 启动FastAPI服务器
    uvicorn.run(
        "app.main:app",
        host=settings.REDIS_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

if __name__ == "__main__":
    main() 
