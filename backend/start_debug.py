#!/usr/bin/env python3
"""
调试启动脚本
"""
import sys
import traceback
from pathlib import Path

def main():
    print("🚀 开始启动调试...")
    
    # 检查Python路径
    print(f"Python版本: {sys.version}")
    print(f"当前工作目录: {Path.cwd()}")
    
    # 检查MahjongKit路径
    mahjong_kit_path = Path.cwd().parent / "MahjongKit"
    print(f"MahjongKit路径: {mahjong_kit_path}")
    print(f"MahjongKit是否存在: {mahjong_kit_path.exists()}")
    
    if mahjong_kit_path.exists():
        # 列出MahjongKit目录内容
        files = list(mahjong_kit_path.glob("*.py"))
        print(f"MahjongKit Python文件: {[f.name for f in files]}")
    
    # 尝试导入MahjongKit模块
    sys.path.insert(0, str(mahjong_kit_path))
    
    try:
        print("\n📦 测试核心模块导入...")
        from core import Tile, SuitType
        print("✅ core模块导入成功")
        
        print("\n📦 测试验证器模块导入...")
        from fixed_validator import WinValidator, TingValidator
        print("✅ fixed_validator模块导入成功")
        
        print("\n📦 测试分析器模块导入...")
        from analyzer import HandAnalyzer, AdvancedAIStrategy
        print("✅ analyzer模块导入成功")
        
        print("\n📦 测试手牌分析API模块导入...")
        sys.path.insert(0, str(Path.cwd() / "app"))
        from app.api import hand_analyzer
        print("✅ hand_analyzer API模块导入成功")
        
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        print("详细错误信息:")
        traceback.print_exc()
        return False
    
    # 启动服务器
    try:
        print("\n🚀 启动FastAPI服务器...")
        import uvicorn
        from app.main import app
        
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
        
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main()