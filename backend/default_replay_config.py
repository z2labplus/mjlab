#!/usr/bin/env python3
"""
默认牌谱配置
设置系统默认使用的牌谱格式和示例牌谱
"""

import asyncio
import json
from pathlib import Path
from app.services.redis_service import RedisService
from app.services.replay_service import ReplayService

# 默认配置
DEFAULT_REPLAY_CONFIG = {
    "default_game_id": "standard_converted_game",
    "standard_format_file": "/root/claude/hmjai/model/first_hand/sample_mahjong_game_final.json",
    "backend_format_file": "converted_replay_standard_converted_game.json",
    "description": "使用标准化格式的默认牌谱",
    "format_version": "2.0"
}

async def ensure_default_replay_exists():
    """确保默认牌谱存在于后台系统中"""
    
    redis_service = RedisService()
    replay_service = ReplayService(redis_service)
    
    default_game_id = DEFAULT_REPLAY_CONFIG["default_game_id"]
    
    print(f"🔍 检查默认牌谱: {default_game_id}")
    
    # 检查是否已存在
    try:
        existing_replay = await replay_service.get_game_replay(default_game_id)
        if existing_replay:
            print(f"✅ 默认牌谱已存在: {default_game_id}")
            return default_game_id
    except:
        pass
    
    print(f"🆕 默认牌谱不存在，准备创建...")
    
    # 如果不存在，从文件加载
    backend_file = DEFAULT_REPLAY_CONFIG["backend_format_file"]
    if Path(backend_file).exists():
        print(f"📥 从文件加载: {backend_file}")
        
        with open(backend_file, 'r', encoding='utf-8') as f:
            replay_data = json.load(f)
        
        # 将数据导入到Redis
        game_record_key = f"game_record:{default_game_id}"
        redis_service.set(game_record_key, json.dumps(replay_data))
        
        print(f"✅ 默认牌谱已导入系统: {default_game_id}")
        return default_game_id
    else:
        print(f"❌ 后台格式文件不存在: {backend_file}")
        print("💡 请先运行 convert_standard_replay.py 生成后台格式文件")
        return None

async def get_system_default_replay():
    """获取系统默认牌谱ID"""
    default_id = await ensure_default_replay_exists()
    return default_id

if __name__ == "__main__":
    asyncio.run(ensure_default_replay_exists())