#!/usr/bin/env python3
"""
导入标准格式牌谱的管理脚本
将新格式文件 model/first_hand/sample_mahjong_game_final.json 导入到后台系统
"""

import asyncio
import argparse
from pathlib import Path

from app.services.redis_service import RedisService
from app.services.standard_replay_service import StandardReplayService

async def import_standard_replay(file_path: str, game_id: str = None):
    """导入标准格式牌谱"""
    
    print("🔄 标准格式牌谱导入工具")
    print("=" * 50)
    
    # 检查文件是否存在
    if not Path(file_path).exists():
        print(f"❌ 文件不存在: {file_path}")
        return False
    
    try:
        # 初始化服务
        redis_service = RedisService()
        standard_service = StandardReplayService(redis_service)
        
        # 导入标准格式牌谱
        imported_game_id = await standard_service.import_standard_replay_to_system(
            file_path=file_path,
            target_game_id=game_id
        )
        
        print(f"\n🎉 导入成功！")
        print(f"📋 游戏ID: {imported_game_id}")
        print(f"📁 源文件: {file_path}")
        
        print(f"\n🔗 API访问地址:")
        print(f"   获取牌谱: GET /api/v1/replay/{imported_game_id}")
        print(f"   导出JSON: GET /api/v1/replay/{imported_game_id}/export/json")
        print(f"   统计信息: GET /api/v1/replay/{imported_game_id}/statistics")
        
        print(f"\n🎬 现在可以在前端使用这个牌谱进行回放了！")
        
        return True
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def list_available_replays():
    """列出可用的标准格式牌谱"""
    
    print("📋 可用的标准格式牌谱")
    print("=" * 50)
    
    try:
        redis_service = RedisService()
        standard_service = StandardReplayService(redis_service)
        
        available_replays = await standard_service.get_available_standard_replays()
        
        if not available_replays:
            print("❌ 没有找到可用的标准格式牌谱文件")
            return
        
        for i, replay in enumerate(available_replays, 1):
            print(f"\n{i}. {replay['name']}")
            print(f"   游戏ID: {replay['game_id']}")
            print(f"   文件路径: {replay['file_path']}")
            print(f"   麻将类型: {replay['mjtype']}")
            print(f"   玩家数: {replay['player_count']}")
            print(f"   动作数: {replay['action_count']}")
            print(f"   描述: {replay['description']}")
        
        return available_replays
        
    except Exception as e:
        print(f"❌ 获取列表失败: {e}")
        return None

async def check_system_status():
    """检查系统状态"""
    
    print("🔍 系统状态检查")
    print("=" * 50)
    
    try:
        # 检查Redis连接
        redis_service = RedisService()
        
        # 检查标准格式文件
        standard_file = "/root/claude/hmjai/model/first_hand/sample_mahjong_game_final.json"
        file_exists = Path(standard_file).exists()
        
        print(f"Redis连接: ✅ 正常")
        print(f"标准格式文件: {'✅ 存在' if file_exists else '❌ 不存在'}")
        print(f"文件路径: {standard_file}")
        
        if file_exists:
            # 尝试解析文件
            standard_service = StandardReplayService(redis_service)
            try:
                standard_replay = standard_service.load_standard_replay_file(standard_file)
                print(f"文件格式: ✅ 有效")
                print(f"游戏ID: {standard_replay.game_info.game_id}")
                print(f"玩家数: {len(standard_replay.initial_hands)}")
                print(f"动作数: {len(standard_replay.actions)}")
            except Exception as e:
                print(f"文件格式: ❌ 解析失败 - {e}")
        
        # 检查已导入的牌谱
        game_keys = redis_service.keys("game_record:*")
        print(f"已导入牌谱数: {len(game_keys)}")
        
        if game_keys:
            print("已导入的牌谱:")
            for key in game_keys[:5]:  # 显示前5个
                game_id = key.replace("game_record:", "")
                print(f"   - {game_id}")
            
            if len(game_keys) > 5:
                print(f"   ... 还有 {len(game_keys) - 5} 个")
        
        return True
        
    except Exception as e:
        print(f"❌ 系统检查失败: {e}")
        return False

async def auto_import_default():
    """自动导入默认的标准格式牌谱"""
    
    print("🚀 自动导入默认标准格式牌谱")
    print("=" * 50)
    
    # 默认文件路径
    default_file = "/root/claude/hmjai/model/first_hand/sample_mahjong_game_final.json"
    default_game_id = "standard_format_default"
    
    success = await import_standard_replay(default_file, default_game_id)
    
    if success:
        print(f"\n✅ 默认牌谱导入完成！")
        print(f"🎯 游戏ID: {default_game_id}")
        print(f"📝 前端现在可以通过API获取到这个标准格式的牌谱了")
    
    return success

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='标准格式牌谱导入工具')
    parser.add_argument('--action', choices=['import', 'list', 'status', 'auto'], 
                       default='auto', help='操作类型')
    parser.add_argument('--file', help='要导入的标准格式文件路径')
    parser.add_argument('--game-id', help='指定游戏ID')
    
    args = parser.parse_args()
    
    if args.action == 'status':
        await check_system_status()
    elif args.action == 'list':
        await list_available_replays()
    elif args.action == 'import':
        if not args.file:
            print("❌ 请指定要导入的文件路径 (--file)")
            return
        await import_standard_replay(args.file, args.game_id)
    elif args.action == 'auto':
        # 自动模式：检查状态并导入默认文件
        print("🤖 自动模式：检查系统状态并导入默认牌谱")
        print("=" * 60)
        
        # 1. 检查系统状态
        status_ok = await check_system_status()
        
        if status_ok:
            print("\n" + "=" * 60)
            # 2. 导入默认牌谱
            await auto_import_default()
        else:
            print("❌ 系统状态检查失败，请检查Redis连接和文件路径")

if __name__ == "__main__":
    asyncio.run(main())