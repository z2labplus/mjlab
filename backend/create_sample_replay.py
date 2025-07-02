#!/usr/bin/env python3
"""
创建示例麻将牌谱
用于测试和演示回放功能
"""

import asyncio
import json
import uuid
import random
from datetime import datetime, timedelta
from app.models.game_record import (
    GameRecord, GameAction, PlayerGameRecord, 
    ActionType, MahjongCard, GangType
)
from app.services.redis_service import RedisService
from app.services.replay_service import ReplayService

async def create_sample_replay():
    """创建一个完整的示例牌谱"""
    
    # 初始化服务
    redis_service = RedisService()
    replay_service = ReplayService(redis_service)
    
    # 游戏基本信息
    game_id = f"sample_game_{uuid.uuid4().hex[:8]}"
    start_time = datetime.now() - timedelta(minutes=30)
    
    print(f"🎮 创建示例游戏: {game_id}")
    
    # 玩家信息
    players = [
        {"name": "张三", "position": 0},
        {"name": "李四", "position": 1}, 
        {"name": "王五", "position": 2},
        {"name": "赵六", "position": 3}
    ]
    
    # 开始记录游戏
    game_record = await replay_service.start_game_recording(
        game_id=game_id,
        players=players,
        game_mode="xuezhan_daodi"
    )
    
    # 设置开始时间
    game_record.start_time = start_time
    
    print("📝 记录玩家起手牌...")
    
    # 记录起手牌（每人13张）
    initial_hands = [
        # 张三的手牌 - 比较好的牌型
        [
            MahjongCard(id=1, suit="wan", value=1),
            MahjongCard(id=2, suit="wan", value=1),
            MahjongCard(id=3, suit="wan", value=2),
            MahjongCard(id=4, suit="wan", value=3),
            MahjongCard(id=5, suit="tiao", value=2),
            MahjongCard(id=6, suit="tiao", value=3),
            MahjongCard(id=7, suit="tiao", value=4),
            MahjongCard(id=8, suit="tiao", value=5),
            MahjongCard(id=9, suit="tong", value=5),
            MahjongCard(id=10, suit="tong", value=6),
            MahjongCard(id=11, suit="tong", value=7),
            MahjongCard(id=12, suit="tong", value=8),
            MahjongCard(id=13, suit="tong", value=9),
        ],
        # 李四的手牌
        [
            MahjongCard(id=14, suit="wan", value=4),
            MahjongCard(id=15, suit="wan", value=5),
            MahjongCard(id=16, suit="wan", value=6),
            MahjongCard(id=17, suit="wan", value=7),
            MahjongCard(id=18, suit="tiao", value=1),
            MahjongCard(id=19, suit="tiao", value=1),
            MahjongCard(id=20, suit="tiao", value=6),
            MahjongCard(id=21, suit="tiao", value=7),
            MahjongCard(id=22, suit="tiao", value=8),
            MahjongCard(id=23, suit="tong", value=1),
            MahjongCard(id=24, suit="tong", value=2),
            MahjongCard(id=25, suit="tong", value=3),
            MahjongCard(id=26, suit="tong", value=4),
        ],
        # 王五的手牌
        [
            MahjongCard(id=27, suit="wan", value=8),
            MahjongCard(id=28, suit="wan", value=8),
            MahjongCard(id=29, suit="wan", value=8),
            MahjongCard(id=30, suit="wan", value=9),
            MahjongCard(id=31, suit="tiao", value=9),
            MahjongCard(id=32, suit="tiao", value=9),
            MahjongCard(id=33, suit="tiao", value=9),
            MahjongCard(id=34, suit="tong", value=1),
            MahjongCard(id=35, suit="tong", value=2),
            MahjongCard(id=36, suit="tong", value=3),
            MahjongCard(id=37, suit="tong", value=4),
            MahjongCard(id=38, suit="tong", value=5),
            MahjongCard(id=39, suit="tong", value=6),
        ],
        # 赵六的手牌
        [
            MahjongCard(id=40, suit="wan", value=2),
            MahjongCard(id=41, suit="wan", value=3),
            MahjongCard(id=42, suit="wan", value=4),
            MahjongCard(id=43, suit="wan", value=5),
            MahjongCard(id=44, suit="wan", value=6),
            MahjongCard(id=45, suit="tiao", value=2),
            MahjongCard(id=46, suit="tiao", value=3),
            MahjongCard(id=47, suit="tiao", value=4),
            MahjongCard(id=48, suit="tiao", value=7),
            MahjongCard(id=49, suit="tiao", value=8),
            MahjongCard(id=50, suit="tong", value=7),
            MahjongCard(id=51, suit="tong", value=8),
            MahjongCard(id=52, suit="tong", value=9),
        ]
    ]
    
    # 记录起手牌
    for i, hand in enumerate(initial_hands):
        await replay_service.record_initial_hand(game_id, i, hand)
    
    print("🎯 记录定缺过程...")
    
    # 定缺阶段
    missing_suits = ["tong", "wan", "tiao", "tong"]  # 每个玩家的定缺
    for i, suit in enumerate(missing_suits):
        await replay_service.record_missing_suit(game_id, i, suit)
        await asyncio.sleep(0.1)  # 模拟时间间隔
    
    print("🎲 模拟游戏过程...")
    
    # 模拟游戏过程
    current_time = start_time + timedelta(minutes=5)  # 定缺后开始
    
    # 第1轮：摸牌和弃牌
    actions_data = [
        # 张三摸牌并弃掉一张
        (0, ActionType.DRAW, MahjongCard(id=53, suit="wan", value=4)),
        (0, ActionType.DISCARD, MahjongCard(id=53, suit="wan", value=4)),
        
        # 李四摸牌并弃掉一张万9
        (1, ActionType.DRAW, MahjongCard(id=54, suit="wan", value=9)),
        (1, ActionType.DISCARD, MahjongCard(id=54, suit="wan", value=9)),
        
        # 王五摸牌，弃万9
        (2, ActionType.DRAW, MahjongCard(id=55, suit="tiao", value=1)),
        (2, ActionType.DISCARD, MahjongCard(id=30, suit="wan", value=9)),
        
        # 赵六摸牌，弃条8
        (3, ActionType.DRAW, MahjongCard(id=56, suit="wan", value=7)),
        (3, ActionType.DISCARD, MahjongCard(id=49, suit="tiao", value=8)),
    ]
    
    for player_id, action_type, card in actions_data:
        await replay_service.record_action(
            game_id=game_id,
            player_id=player_id,
            action_type=action_type,
            card=card
        )
        current_time += timedelta(seconds=random_seconds())
        await asyncio.sleep(0.1)
    
    print("💥 记录碰牌操作...")
    
    # 第2轮：碰牌示例
    # 张三弃条4，李四碰
    await replay_service.record_action(
        game_id=game_id,
        player_id=0,
        action_type=ActionType.DISCARD,
        card=MahjongCard(id=7, suit="tiao", value=4)
    )
    
    await replay_service.record_action(
        game_id=game_id,
        player_id=1,
        action_type=ActionType.PENG,
        card=MahjongCard(id=7, suit="tiao", value=4),
        target_player=0
    )
    
    print("🔥 记录杠牌操作...")
    
    # 第3轮：杠牌示例
    # 王五暗杠万8
    await replay_service.record_action(
        game_id=game_id,
        player_id=2,
        action_type=ActionType.GANG,
        card=MahjongCard(id=27, suit="wan", value=8),
        gang_type=GangType.AN_GANG
    )
    
    # 王五暗杠条9
    await replay_service.record_action(
        game_id=game_id,
        player_id=2,
        action_type=ActionType.GANG,
        card=MahjongCard(id=31, suit="tiao", value=9),
        gang_type=GangType.AN_GANG
    )
    
    print("🏆 记录胡牌...")
    
    # 最后：张三胡牌
    await replay_service.record_action(
        game_id=game_id,
        player_id=0,
        action_type=ActionType.HU,
        card=MahjongCard(id=100, suit="tong", value=8),
        score_change=100
    )
    
    # 记录游戏结束
    final_scores = [100, -30, -40, -30]  # 张三胜利+100分
    winners = [0]  # 张三胜利
    hu_types = ["自摸"]
    
    await replay_service.record_game_end(
        game_id=game_id,
        final_scores=final_scores,
        winners=winners,
        hu_types=hu_types
    )
    
    print(f"✅ 示例牌谱创建完成！")
    print(f"🎮 游戏ID: {game_id}")
    print(f"📊 总操作数: {len(game_record.actions)}")
    print(f"🏆 胜利者: 张三")
    
    # 导出牌谱JSON
    json_export = await replay_service.export_replay_json(game_id)
    
    # 保存到文件
    filename = f"sample_replay_{game_id}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(json_export)
    
    print(f"💾 牌谱已保存到: {filename}")
    
    return game_id, filename

def random_seconds() -> int:
    """随机生成操作间隔时间"""
    return random.randint(3, 8)

async def main():
    """主函数"""
    print("🀄 创建血战到底示例牌谱")
    print("=" * 50)
    
    try:
        game_id, filename = await create_sample_replay()
        
        print("\n" + "=" * 50)
        print("🎉 示例牌谱创建成功！")
        print(f"📋 可以使用以下方式访问:")
        print(f"   - API: GET /api/v1/replay/{game_id}")
        print(f"   - 导出: GET /api/v1/replay/{game_id}/export/json")
        print(f"   - 文件: {filename}")
        print("\n🎬 现在可以在前端导入并回放这个牌谱了！")
        
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())