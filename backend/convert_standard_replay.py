#!/usr/bin/env python3
"""
将标准化牌谱格式转换为后台系统格式
将 model/first_hand/sample_mahjong_game_final.json 转换为后台API可用的格式
"""

import json
import asyncio
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from app.models.game_record import (
    GameRecord, GameAction, PlayerGameRecord, 
    ActionType, MahjongCard, GangType
)
from app.services.redis_service import RedisService
from app.services.replay_service import ReplayService

class StandardReplayConverter:
    """标准牌谱格式转换器"""
    
    def __init__(self):
        self.suit_mapping = {
            "万": "wan",
            "条": "tiao", 
            "筒": "tong"
        }
    
    def parse_tile_string(self, tile_str: str) -> MahjongCard:
        """解析牌字符串，如 '1万' -> MahjongCard"""
        if len(tile_str) < 2:
            raise ValueError(f"无效的牌字符串: {tile_str}")
        
        value = int(tile_str[0])
        suit_zh = tile_str[1]
        suit_en = self.suit_mapping.get(suit_zh, suit_zh)
        
        # 生成唯一ID
        card_id = hash(f"{suit_en}_{value}") % 10000
        
        return MahjongCard(
            id=card_id,
            suit=suit_en,
            value=value
        )
    
    async def convert_standard_to_backend(self, standard_file_path: str, output_game_id: str = None):
        """转换标准格式牌谱为后台系统格式"""
        
        print(f"🔄 开始转换标准牌谱: {standard_file_path}")
        
        # 读取标准格式文件
        with open(standard_file_path, 'r', encoding='utf-8') as f:
            standard_data = json.load(f)
        
        # 初始化后台服务
        redis_service = RedisService()
        replay_service = ReplayService(redis_service)
        
        # 生成游戏ID
        if output_game_id is None:
            output_game_id = f"converted_{uuid.uuid4().hex[:8]}"
        
        print(f"🎮 目标游戏ID: {output_game_id}")
        
        # 设置玩家信息
        players = []
        for i in range(4):
            player_name = f"玩家{i+1}"
            if i == 0:
                player_name = "张三"
            elif i == 1:
                player_name = "李四"
            elif i == 2:
                player_name = "王五"
            elif i == 3:
                player_name = "赵六"
            
            players.append({
                "name": player_name,
                "position": i
            })
        
        # 开始游戏记录
        game_record = await replay_service.start_game_recording(
            game_id=output_game_id,
            players=players,
            game_mode=standard_data.get("mjtype", "xuezhan_daodi")
        )
        
        # 设置开始时间
        start_time = datetime.now() - timedelta(minutes=30)
        game_record.start_time = start_time
        
        print("📝 转换初始手牌...")
        
        # 记录初始手牌
        initial_hands = standard_data.get("initial_hands", {})
        for player_id_str, hand_data in initial_hands.items():
            player_id = int(player_id_str)
            
            # 获取牌列表
            if isinstance(hand_data, dict):
                tiles = hand_data.get("tiles", [])
            else:
                tiles = hand_data
            
            # 转换为MahjongCard对象
            cards = []
            for tile_str in tiles:
                try:
                    card = self.parse_tile_string(tile_str)
                    cards.append(card)
                except Exception as e:
                    print(f"⚠️ 解析牌失败: {tile_str}, 错误: {e}")
            
            await replay_service.record_initial_hand(output_game_id, player_id, cards)
            print(f"  玩家{player_id}: {len(cards)}张")
        
        print("🎯 转换定缺信息...")
        
        # 记录定缺
        misssuit = standard_data.get("misssuit", {})
        for player_id_str, suit_zh in misssuit.items():
            player_id = int(player_id_str)
            suit_en = self.suit_mapping.get(suit_zh, suit_zh)
            await replay_service.record_missing_suit(output_game_id, player_id, suit_en)
        
        print("🎲 转换游戏动作...")
        
        # 转换游戏动作
        actions = standard_data.get("actions", [])
        for action_data in actions:
            try:
                action_type = ActionType(action_data.get("type", "draw"))
                player_id = action_data.get("player_id", 0)
                
                # 转换牌信息
                card = None
                if "tile" in action_data:
                    tile_str = action_data["tile"]
                    card = self.parse_tile_string(tile_str)
                
                # 特殊处理不同类型的动作
                if action_type == ActionType.GANG:
                    gang_type = GangType.MING_GANG
                    if action_data.get("gang_type") == "jiagang":
                        gang_type = GangType.JIA_GANG
                    elif action_data.get("gang_type") == "angang":
                        gang_type = GangType.AN_GANG
                    
                    await replay_service.record_action(
                        game_id=output_game_id,
                        player_id=player_id,
                        action_type=action_type,
                        card=card,
                        gang_type=gang_type
                    )
                elif action_type == ActionType.PENG:
                    target_player = action_data.get("target_player", 0)
                    await replay_service.record_action(
                        game_id=output_game_id,
                        player_id=player_id,
                        action_type=action_type,
                        card=card,
                        target_player=target_player
                    )
                else:
                    await replay_service.record_action(
                        game_id=output_game_id,
                        player_id=player_id,
                        action_type=action_type,
                        card=card
                    )
                
                await asyncio.sleep(0.05)  # 模拟时间间隔
                
            except Exception as e:
                print(f"⚠️ 转换动作失败: {action_data}, 错误: {e}")
        
        print("🏆 设置游戏结果...")
        
        # 设置游戏结束
        final_scores = [100, -30, -40, -30]  # 示例分数
        winners = [0]  # 玩家0胜利
        hu_types = ["自摸"]
        
        await replay_service.record_game_end(
            game_id=output_game_id,
            final_scores=final_scores,
            winners=winners,
            hu_types=hu_types
        )
        
        print(f"✅ 转换完成！")
        print(f"🎮 游戏ID: {output_game_id}")
        print(f"📊 总操作数: {len(game_record.actions)}")
        
        # 导出为JSON文件
        json_export = await replay_service.export_replay_json(output_game_id)
        
        # 保存到文件
        output_filename = f"converted_replay_{output_game_id}.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(json_export)
        
        print(f"💾 牌谱已保存到: {output_filename}")
        
        return output_game_id, output_filename

async def main():
    """主函数"""
    print("🔄 标准牌谱格式转换器")
    print("=" * 50)
    
    converter = StandardReplayConverter()
    
    # 转换新格式文件
    standard_file = "/root/claude/hmjai/model/first_hand/sample_mahjong_game_final.json"
    
    if not Path(standard_file).exists():
        print(f"❌ 标准文件不存在: {standard_file}")
        return
    
    try:
        game_id, filename = await converter.convert_standard_to_backend(
            standard_file_path=standard_file,
            output_game_id="standard_converted_game"
        )
        
        print("\n" + "=" * 50)
        print("🎉 转换成功！")
        print(f"📋 后台API访问方式:")
        print(f"   - 获取牌谱: GET /api/v1/replay/{game_id}")
        print(f"   - 导出JSON: GET /api/v1/replay/{game_id}/export/json")
        print(f"   - 本地文件: {filename}")
        print("\n🎬 现在可以在前端使用新格式的牌谱进行回放了！")
        
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())