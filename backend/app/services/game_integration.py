"""
游戏集成示例 - 展示如何在游戏过程中集成牌谱记录功能
"""

from typing import List, Dict, Optional
from app.models.game_record import MahjongCard, ActionType, GangType
from app.services.replay_service import ReplayService
from app.services.redis_service import RedisService

class GameIntegrationExample:
    """游戏集成示例类"""
    
    def __init__(self):
        self.redis_service = RedisService()
        self.replay_service = ReplayService(self.redis_service)
    
    async def start_new_game(self, players: List[Dict]) -> str:
        """开始新游戏并开始记录牌谱"""
        # 创建游戏ID
        import uuid
        game_id = str(uuid.uuid4())
        
        # 开始牌谱记录
        game_record = await self.replay_service.start_game_recording(
            game_id=game_id,
            players=players,
            game_mode="xuezhan"
        )
        
        print(f"🎮 游戏开始: {game_id}")
        print(f"👥 玩家: {[p['name'] for p in players]}")
        
        return game_id
    
    async def record_player_initial_hand(
        self, 
        game_id: str, 
        player_id: int, 
        cards: List[MahjongCard]
    ):
        """记录玩家起手牌"""
        await self.replay_service.record_initial_hand(game_id, player_id, cards)
        print(f"📝 玩家{player_id+1}起手牌已记录: {len(cards)}张")
    
    async def record_player_missing_suit(
        self, 
        game_id: str, 
        player_id: int, 
        missing_suit: str
    ):
        """记录玩家定缺"""
        await self.replay_service.record_missing_suit(game_id, player_id, missing_suit)
        print(f"🎯 玩家{player_id+1}定缺: {missing_suit}")
    
    async def record_draw_card(
        self, 
        game_id: str, 
        player_id: int, 
        card: MahjongCard,
        game_state: Optional[Dict] = None
    ):
        """记录摸牌操作"""
        action = await self.replay_service.record_action(
            game_id=game_id,
            player_id=player_id,
            action_type=ActionType.DRAW,
            card=card,
            game_state_snapshot=game_state
        )
        print(f"🎴 玩家{player_id+1}摸牌: {card}")
        return action
    
    async def record_discard_card(
        self, 
        game_id: str, 
        player_id: int, 
        card: MahjongCard,
        game_state: Optional[Dict] = None
    ):
        """记录弃牌操作"""
        action = await self.replay_service.record_action(
            game_id=game_id,
            player_id=player_id,
            action_type=ActionType.DISCARD,
            card=card,
            game_state_snapshot=game_state
        )
        print(f"🗑️ 玩家{player_id+1}弃牌: {card}")
        return action
    
    async def record_peng(
        self, 
        game_id: str, 
        player_id: int, 
        card: MahjongCard,
        target_player: int,
        game_state: Optional[Dict] = None
    ):
        """记录碰牌操作"""
        action = await self.replay_service.record_action(
            game_id=game_id,
            player_id=player_id,
            action_type=ActionType.PENG,
            card=card,
            target_player=target_player,
            game_state_snapshot=game_state
        )
        print(f"🤜 玩家{player_id+1}碰牌: {card} (来自玩家{target_player+1})")
        return action
    
    async def record_gang(
        self, 
        game_id: str, 
        player_id: int, 
        card: MahjongCard,
        gang_type: GangType,
        target_player: Optional[int] = None,
        score_change: int = 0,
        game_state: Optional[Dict] = None
    ):
        """记录杠牌操作"""
        action = await self.replay_service.record_action(
            game_id=game_id,
            player_id=player_id,
            action_type=ActionType.GANG,
            card=card,
            target_player=target_player,
            gang_type=gang_type,
            score_change=score_change,
            game_state_snapshot=game_state
        )
        
        gang_desc = {
            GangType.AN_GANG: "暗杠",
            GangType.MING_GANG: "明杠",
            GangType.JIA_GANG: "加杠"
        }.get(gang_type, "杠")
        
        print(f"🔥 玩家{player_id+1}{gang_desc}: {card} (+{score_change}分)")
        return action
    
    async def record_hu(
        self, 
        game_id: str, 
        player_id: int, 
        card: Optional[MahjongCard] = None,
        score_change: int = 0,
        game_state: Optional[Dict] = None
    ):
        """记录胡牌操作"""
        action = await self.replay_service.record_action(
            game_id=game_id,
            player_id=player_id,
            action_type=ActionType.HU,
            card=card,
            score_change=score_change,
            game_state_snapshot=game_state
        )
        print(f"🎉 玩家{player_id+1}胡牌! (+{score_change}分)")
        return action
    
    async def end_game(
        self, 
        game_id: str, 
        final_scores: List[int], 
        winners: List[int],
        hu_types: Optional[List[str]] = None
    ):
        """结束游戏并完成牌谱记录"""
        await self.replay_service.record_game_end(
            game_id=game_id,
            final_scores=final_scores,
            winners=winners,
            hu_types=hu_types
        )
        
        print(f"🏁 游戏结束: {game_id}")
        print(f"🏆 胜利者: {winners}")
        print(f"📊 最终得分: {final_scores}")
        
        # 获取并显示牌谱信息
        replay = await self.replay_service.get_game_replay(game_id)
        if replay:
            print(f"📝 牌谱已生成，共{len(replay.game_record.actions)}个操作")
            print(f"📁 导出JSON: /api/v1/replay/{game_id}/export/json")
            print(f"📦 导出ZIP: /api/v1/replay/{game_id}/export/zip")
    
    async def run_demo_game(self):
        """运行演示游戏"""
        print("🎮 开始演示游戏...")
        
        # 创建演示玩家
        players = [
            {"name": "小明", "level": 1},
            {"name": "小红", "level": 2},
            {"name": "小刚", "level": 1},
            {"name": "小美", "level": 3}
        ]
        
        # 开始游戏
        game_id = await self.start_new_game(players)
        
        # 模拟游戏过程
        try:
            # 记录起手牌 (简化示例)
            for i in range(4):
                initial_cards = [
                    MahjongCard(id=j+1, suit="wan", value=j+1) 
                    for j in range(13)
                ]
                await self.record_player_initial_hand(game_id, i, initial_cards)
            
            # 记录定缺
            missing_suits = ["wan", "tiao", "tong", "wan"]
            for i, suit in enumerate(missing_suits):
                await self.record_player_missing_suit(game_id, i, suit)
            
            # 演示一些游戏操作
            card_wan_1 = MahjongCard(id=1, suit="wan", value=1)
            card_tiao_5 = MahjongCard(id=15, suit="tiao", value=5)
            card_tong_9 = MahjongCard(id=29, suit="tong", value=9)
            
            # 玩家0摸牌
            await self.record_draw_card(game_id, 0, card_wan_1)
            
            # 玩家0弃牌
            await self.record_discard_card(game_id, 0, card_wan_1)
            
            # 玩家1碰牌
            await self.record_peng(game_id, 1, card_wan_1, target_player=0)
            
            # 玩家1摸牌弃牌
            await self.record_draw_card(game_id, 1, card_tiao_5)
            await self.record_discard_card(game_id, 1, card_tiao_5)
            
            # 玩家2杠牌
            await self.record_gang(
                game_id, 2, card_tiao_5, 
                GangType.MING_GANG, target_player=1, score_change=2
            )
            
            # 玩家3胡牌
            await self.record_hu(game_id, 3, card_tong_9, score_change=10)
            
            # 结束游戏
            await self.end_game(
                game_id=game_id,
                final_scores=[2, -1, 1, 8],
                winners=[3],
                hu_types=["自摸"]
            )
            
            print("\n✅ 演示游戏完成！")
            print(f"🎯 游戏ID: {game_id}")
            print("🔗 你可以通过以下链接查看和导出牌谱:")
            print(f"   📖 查看: http://localhost:8000/api/v1/replay/{game_id}")
            print(f"   📄 导出JSON: http://localhost:8000/api/v1/replay/{game_id}/export/json")
            print(f"   📦 导出ZIP: http://localhost:8000/api/v1/replay/{game_id}/export/zip")
            
        except Exception as e:
            print(f"❌ 演示游戏出错: {e}")
            return None
        
        return game_id

# 使用示例
async def main():
    """主函数"""
    integration = GameIntegrationExample()
    await integration.run_demo_game()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 