#!/usr/bin/env python3
"""
测试完整最终状态设置功能
"""
import json
import requests

class ReplayTester:
    def __init__(self, api_base_url: str = "http://localhost:8000/api/mahjong"):
        self.api_base_url = api_base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def _parse_tile(self, tile: str) -> tuple:
        """解析牌名，返回(tile_type, tile_value)"""
        if tile.endswith('万'):
            return 'wan', int(tile[0])
        elif tile.endswith('条'):
            return 'tiao', int(tile[0])
        elif tile.endswith('筒'):
            return 'tong', int(tile[0])
        else:
            raise ValueError(f"未知的牌类型: {tile}")
    
    def reset_game(self):
        """重置游戏"""
        response = self.session.post(f"{self.api_base_url}/reset")
        return response.json().get('success', False)
    
    def set_complete_final_state_from_replay(self, replay_data: dict) -> bool:
        """从牌谱数据中设置完整的最终状态（手牌+碰杠牌+胜利状态）"""
        try:
            final_hands = replay_data.get('final_hands', {})
            if not final_hands:
                print("⚠️ 牌谱中没有最终手牌数据")
                return False
            
            # 获取当前游戏状态
            response = self.session.get(f"{self.api_base_url}/game-state")
            game_state = response.json().get('game_state', {})
            
            # 为所有玩家设置完整的最终状态
            for player_id_str, final_hand_data in final_hands.items():
                player_id = int(player_id_str)
                
                if player_id_str in game_state.get('player_hands', {}):
                    player_hand = game_state['player_hands'][player_id_str]
                    
                    # 1. 设置手牌
                    hand_tiles = final_hand_data.get('hand', [])
                    tiles = []
                    for tile_str in hand_tiles:
                        tile_type, tile_value = self._parse_tile(tile_str)
                        tiles.append({
                            "type": tile_type,
                            "value": tile_value,
                            "id": None
                        })
                    
                    player_hand['tiles'] = tiles
                    player_hand['tile_count'] = len(tiles)
                    
                    # 2. 设置碰杠牌组
                    melds_data = final_hand_data.get('melds', [])
                    converted_melds = []
                    
                    for meld_data in melds_data:
                        meld_type = meld_data.get('type', 'peng')
                        meld_tiles = meld_data.get('tile', [])
                        target_player = meld_data.get('target_player')
                        
                        # 转换碰杠牌组格式
                        meld_tiles_converted = []
                        for tile_str in meld_tiles:
                            tile_type, tile_value = self._parse_tile(tile_str)
                            meld_tiles_converted.append({
                                "type": tile_type,
                                "value": tile_value,
                                "id": None
                            })
                        
                        converted_meld = {
                            "id": f"meld_{player_id}_{len(converted_melds)}",
                            "type": meld_type,
                            "tiles": meld_tiles_converted,
                            "exposed": True,
                            "gang_type": None if meld_type == "peng" else "ming_gang",
                            "source_player": target_player,
                            "original_peng_id": None,
                            "timestamp": 0
                        }
                        converted_melds.append(converted_meld)
                    
                    player_hand['melds'] = converted_melds
                    
                    print(f"✅ 玩家{player_id}完整状态设置: {len(tiles)}张手牌, {len(converted_melds)}个碰杠牌组")
            
            # 3. 在游戏状态中直接设置胜利状态（避免被 set-game-state 覆盖）
            for player_id_str, final_hand_data in final_hands.items():
                player_id = int(player_id_str)
                player_hand = game_state['player_hands'][player_id_str]
                
                # 处理自摸胜利状态
                if 'self_win_tile' in final_hand_data:
                    win_tile_str = final_hand_data['self_win_tile'].get('tile')
                    win_tile_type, win_tile_value = self._parse_tile(win_tile_str)
                    
                    player_hand['is_winner'] = True
                    player_hand['win_type'] = 'zimo'
                    player_hand['win_tile'] = {
                        "type": win_tile_type,
                        "value": win_tile_value
                    }
                    print(f"✅ 玩家{player_id}自摸胜利状态已设置: {win_tile_str}")
                
                # 处理点炮胜利状态
                elif 'pao_tile' in final_hand_data:
                    pao_data = final_hand_data['pao_tile']
                    win_tile_str = pao_data.get('tile')
                    dianpao_player = pao_data.get('target_player')
                    win_tile_type, win_tile_value = self._parse_tile(win_tile_str)
                    
                    player_hand['is_winner'] = True
                    player_hand['win_type'] = 'dianpao'
                    player_hand['win_tile'] = {
                        "type": win_tile_type,
                        "value": win_tile_value
                    }
                    player_hand['dianpao_player_id'] = dianpao_player
                    print(f"✅ 玩家{player_id}点炮胜利状态已设置: {win_tile_str} (点炮者: 玩家{dianpao_player})")
            
            # 一次性更新完整游戏状态（包含手牌+碰杠牌+胜利状态）
            update_response = self.session.post(
                f"{self.api_base_url}/set-game-state",
                json={"game_state": game_state}
            )
            
            if update_response.json().get('success'):
                print("✅ 完整最终状态设置成功（包含胜利状态）")
                return True
            else:
                print("❌ 设置完整最终状态失败")
                return False
                
        except Exception as e:
            print(f"❌ 设置完整最终状态失败: {e}")
            return False
    
    def reveal_all_hands(self):
        """显示所有玩家手牌"""
        response = self.session.post(f"{self.api_base_url}/reveal-all-hands")
        return response.json().get('success', False)
    
    def verify_final_state(self):
        """验证最终状态"""
        response = self.session.get(f"{self.api_base_url}/game-state")
        game_state = response.json().get('game_state', {})
        
        print("\n🔍 验证最终状态:")
        print(f"show_all_hands: {game_state.get('show_all_hands', False)}")
        print()
        
        for player_id in ['0', '1', '2', '3']:
            hand = game_state['player_hands'][player_id]
            print(f"玩家{player_id}:")
            print(f"  手牌数量: {hand['tile_count']}")
            print(f"  手牌是否存在: {hand['tiles'] is not None}")
            if hand['tiles']:
                print(f"  具体手牌: {len(hand['tiles'])}张")
            print(f"  碰杠牌组: {len(hand['melds'])}个")
            if hand['melds']:
                for i, meld in enumerate(hand['melds']):
                    print(f"    {i+1}. {meld['type']} (来源: 玩家{meld.get('source_player', '无')})")
            print(f"  是否胜利: {hand.get('is_winner', False)}")
            if hand.get('is_winner'):
                print(f"  胜利类型: {hand.get('win_type', '未知')}")
                print(f"  胜利牌: {hand.get('win_tile', '无')}")
            print()

def main():
    print("🧪 开始测试完整最终状态设置...")
    
    tester = ReplayTester()
    
    # 1. 重置游戏
    print("🔄 重置游戏...")
    if not tester.reset_game():
        print("❌ 重置游戏失败")
        return
    
    # 2. 读取牌谱数据
    print("📖 读取牌谱数据...")
    with open('model/first_hand/sample_mahjong_game_final.json', 'r', encoding='utf-8') as f:
        replay_data = json.load(f)
    
    # 3. 设置完整最终状态
    print("🎯 设置完整最终状态...")
    if not tester.set_complete_final_state_from_replay(replay_data):
        print("❌ 设置完整最终状态失败")
        return
    
    # 4. 显示所有手牌
    print("👁️ 显示所有玩家手牌...")
    if not tester.reveal_all_hands():
        print("❌ 显示所有手牌失败")
        return
    
    # 5. 验证最终状态
    tester.verify_final_state()
    
    print("🎉 测试完成！现在可以在前端实时游戏界面查看完整的最终状态")

if __name__ == "__main__":
    main()