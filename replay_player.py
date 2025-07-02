#!/usr/bin/env python3
"""
牌谱播放脚本 - 逐步执行牌谱操作，通过API接口在实时游戏界面展示
"""

import json
import time
import requests
import sys
from typing import Dict, List, Any

class ReplayPlayer:
    def __init__(self, api_base_url: str = "http://localhost:8000/api/mahjong"):
        self.api_base_url = api_base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
    def health_check(self) -> bool:
        """检查API服务器是否可用"""
        try:
            response = self.session.get(f"{self.api_base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ API服务器连接失败: {e}")
            return False
    
    def reset_game(self) -> bool:
        """重置游戏状态"""
        try:
            response = self.session.post(f"{self.api_base_url}/reset")
            result = response.json()
            if result.get('success'):
                print("✅ 游戏状态已重置")
                return True
            else:
                print(f"❌ 重置游戏失败: {result.get('message', '未知错误')}")
                return False
        except Exception as e:
            print(f"❌ 重置游戏失败: {e}")
            return False
    
    def set_missing_suit(self, player_id: int, missing_suit: str) -> bool:
        """设置玩家定缺"""
        try:
            # 转换中文花色为英文
            suit_map = {"万": "wan", "条": "tiao", "筒": "tong"}
            english_suit = suit_map.get(missing_suit, missing_suit)
            
            response = self.session.post(
                f"{self.api_base_url}/set-missing-suit",
                params={"player_id": player_id, "missing_suit": english_suit}
            )
            result = response.json()
            if result.get('success'):
                print(f"✅ 玩家{player_id}定缺{missing_suit}设置成功")
                return True
            else:
                print(f"❌ 设置定缺失败: {result.get('message', '未知错误')}")
                return False
        except Exception as e:
            print(f"❌ 设置定缺失败: {e}")
            return False
    
    def add_hand_tile(self, player_id: int, tile: str) -> bool:
        """为玩家添加手牌"""
        try:
            # 解析牌名 (如"2万" -> type="wan", value=2)
            tile_type, tile_value = self._parse_tile(tile)
            
            response = self.session.post(
                f"{self.api_base_url}/add-hand-tile",
                params={
                    "player_id": player_id,
                    "tile_type": tile_type,
                    "tile_value": tile_value
                }
            )
            result = response.json()
            if result.get('success'):
                print(f"✅ 玩家{player_id}添加手牌{tile}")
                return True
            else:
                print(f"❌ 添加手牌失败: {result.get('message', '未知错误')}")
                return False
        except Exception as e:
            print(f"❌ 添加手牌失败: {e}")
            return False
    
    def add_hand_count(self, player_id: int, count: int = 1) -> bool:
        """为其他玩家增加手牌数量"""
        try:
            response = self.session.post(
                f"{self.api_base_url}/add-hand-count",
                params={"player_id": player_id, "count": count}
            )
            result = response.json()
            if result.get('success'):
                print(f"✅ 玩家{player_id}手牌数量+{count}")
                return True
            else:
                print(f"❌ 增加手牌数量失败: {result.get('message', '未知错误')}")
                return False
        except Exception as e:
            print(f"❌ 增加手牌数量失败: {e}")
            return False
    
    def discard_tile(self, player_id: int, tile: str) -> bool:
        """玩家弃牌"""
        try:
            tile_type, tile_value = self._parse_tile(tile)
            
            response = self.session.post(
                f"{self.api_base_url}/discard-tile",
                params={
                    "player_id": player_id,
                    "tile_type": tile_type,
                    "tile_value": tile_value
                }
            )
            result = response.json()
            if result.get('success'):
                print(f"✅ 玩家{player_id}弃牌{tile}")
                return True
            else:
                print(f"❌ 弃牌失败: {result.get('message', '未知错误')}")
                return False
        except Exception as e:
            print(f"❌ 弃牌失败: {e}")
            return False
    
    def peng_tile(self, player_id: int, tile: str, source_player_id: int) -> bool:
        """玩家碰牌"""
        try:
            tile_type, tile_value = self._parse_tile(tile)
            
            response = self.session.post(
                f"{self.api_base_url}/peng",
                params={
                    "player_id": player_id,
                    "tile_type": tile_type,
                    "tile_value": tile_value,
                    "source_player_id": source_player_id
                }
            )
            result = response.json()
            if result.get('success'):
                print(f"✅ 玩家{player_id}碰牌{tile}(来源:玩家{source_player_id})")
                return True
            else:
                print(f"❌ 碰牌失败: {result.get('message', '未知错误')}")
                return False
        except Exception as e:
            print(f"❌ 碰牌失败: {e}")
            return False
    
    def gang_tile(self, player_id: int, tile: str, gang_type: str, source_player_id: int = None) -> bool:
        """玩家杠牌"""
        try:
            tile_type, tile_value = self._parse_tile(tile)
            
            params = {
                "player_id": player_id,
                "tile_type": tile_type,
                "tile_value": tile_value,
                "gang_type": gang_type
            }
            if source_player_id is not None:
                params["source_player_id"] = source_player_id
            
            response = self.session.post(f"{self.api_base_url}/gang", params=params)
            result = response.json()
            if result.get('success'):
                gang_name = {"angang": "暗杠", "zhigang": "直杠", "jiagang": "加杠"}.get(gang_type, gang_type)
                print(f"✅ 玩家{player_id}{gang_name}{tile}")
                return True
            else:
                print(f"❌ 杠牌失败: {result.get('message', '未知错误')}")
                return False
        except Exception as e:
            print(f"❌ 杠牌失败: {e}")
            return False
    
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
                    
                    if player_id == 0:
                        # 玩家0设置具体手牌
                        player_hand['tiles'] = tiles
                        print(f"🎯 设置玩家0手牌: {len(tiles)}张")
                    else:
                        # 其他玩家也设置具体手牌（用于最终展示）
                        player_hand['tiles'] = tiles
                        print(f"🎯 设置玩家{player_id}手牌: {len(tiles)}张, 前3张: {tiles[:3] if tiles else 'None'}")
                        
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
                        
                        # 🔧 修复：转换meld类型为后端期望的值
                        backend_meld_type = meld_type
                        gang_type = None
                        if meld_type in ["gang", "angang", "zhigang", "jiagang"]:
                            backend_meld_type = "gang"
                            if meld_type == "angang":
                                gang_type = "an_gang"
                            elif meld_type == "zhigang":
                                gang_type = "ming_gang"
                            elif meld_type == "jiagang":
                                gang_type = "jia_gang"
                            else:
                                gang_type = "ming_gang"  # 默认明杠
                        
                        converted_meld = {
                            "id": f"meld_{player_id}_{len(converted_melds)}",
                            "type": backend_meld_type,
                            "tiles": meld_tiles_converted,
                            "exposed": True,
                            "gang_type": gang_type,
                            "source_player": target_player,
                            "original_peng_id": None,
                            "timestamp": 0
                        }
                        converted_melds.append(converted_meld)
                    
                    player_hand['melds'] = converted_melds
                    
                    print(f"✅ 玩家{player_id}完整状态设置: {len(tiles)}张手牌, {len(converted_melds)}个碰杠牌组")
            
            # 3. 🔧 关键修复：处理胜利牌，在手牌设置完成后立即添加胜利牌
            for player_id_str, final_hand_data in final_hands.items():
                player_id = int(player_id_str)
                player_hand = game_state['player_hands'][player_id_str]
                
                # 处理自摸胜利状态 - 玩家3自摸3万
                if 'self_win_tile' in final_hand_data:
                    win_tile_str = final_hand_data['self_win_tile'].get('tile')
                    win_tile_type, win_tile_value = self._parse_tile(win_tile_str)
                    
                    # 设置胜利状态
                    player_hand['is_winner'] = True
                    player_hand['win_type'] = 'zimo'
                    player_hand['win_tile'] = {
                        "type": win_tile_type,
                        "value": win_tile_value
                    }
                    
                    # 🎯 关键：将自摸的胜利牌添加到已设置的手牌中
                    win_tile_obj = {
                        "type": win_tile_type,
                        "value": win_tile_value,
                        "id": None
                    }
                    
                    # 确保tiles已经被设置（应该有13张牌）
                    if 'tiles' in player_hand and player_hand['tiles']:
                        player_hand['tiles'].append(win_tile_obj)
                        player_hand['tile_count'] = len(player_hand['tiles'])
                        print(f"🎉 玩家{player_id}自摸胜利: 手牌{len(player_hand['tiles'])-1}张 + 自摸{win_tile_str} = 总共{len(player_hand['tiles'])}张")
                    else:
                        print(f"❌ 错误：玩家{player_id}的手牌为空，无法添加自摸牌")
                
                # 处理点炮胜利状态 - 玩家2胡玩家0的6万
                elif 'pao_tile' in final_hand_data:
                    pao_data = final_hand_data['pao_tile']
                    win_tile_str = pao_data.get('tile')
                    dianpao_player = pao_data.get('target_player')
                    win_tile_type, win_tile_value = self._parse_tile(win_tile_str)
                    
                    # 设置胜利状态
                    player_hand['is_winner'] = True
                    player_hand['win_type'] = 'dianpao'
                    player_hand['win_tile'] = {
                        "type": win_tile_type,
                        "value": win_tile_value
                    }
                    player_hand['dianpao_player_id'] = dianpao_player
                    
                    # 🎯 关键：将点炮的胜利牌添加到已设置的手牌中
                    win_tile_obj = {
                        "type": win_tile_type,
                        "value": win_tile_value,
                        "id": None
                    }
                    
                    # 确保tiles已经被设置（应该有10张牌）
                    if 'tiles' in player_hand and player_hand['tiles']:
                        player_hand['tiles'].append(win_tile_obj)
                        player_hand['tile_count'] = len(player_hand['tiles'])
                        print(f"🎉 玩家{player_id}点炮胜利: 手牌{len(player_hand['tiles'])-1}张 + 胡{win_tile_str} = 总共{len(player_hand['tiles'])}张")
                        
                        # 🔧 从点炮者的弃牌中移除被胡的牌
                        dianpao_player_str = str(dianpao_player)
                        if 'player_discarded_tiles' in game_state and dianpao_player_str in game_state['player_discarded_tiles']:
                            discarded_tiles = game_state['player_discarded_tiles'][dianpao_player_str]
                            removed = False
                            # 从后往前找，移除最后一张相同的牌
                            for i in range(len(discarded_tiles) - 1, -1, -1):
                                tile = discarded_tiles[i]
                                if tile and tile.get('type') == win_tile_type and tile.get('value') == win_tile_value:
                                    discarded_tiles.pop(i)
                                    print(f"🎯 从玩家{dianpao_player}弃牌中移除被胡的 {win_tile_str}")
                                    removed = True
                                    break
                            if not removed:
                                print(f"⚠️ 警告：未在玩家{dianpao_player}弃牌中找到 {win_tile_str}")
                    else:
                        print(f"❌ 错误：玩家{player_id}的手牌为空，无法添加胡牌")
            
            # 🔧 关键修复：设置游戏结束标志，确保前端显示所有玩家手牌
            game_state['game_ended'] = True
            game_state['show_all_hands'] = True
            print("🎯 设置游戏结束标志: game_ended=True, show_all_hands=True")
            
            # 📊 详细调试：打印最终游戏状态
            print("\n" + "="*80)
            print("🔍 最终游戏状态调试信息:")
            print("="*80)
            for pid in ['0', '1', '2', '3']:
                if pid in game_state.get('player_hands', {}):
                    hand = game_state['player_hands'][pid]
                    tiles = hand.get('tiles', [])
                    is_winner = hand.get('is_winner', False)
                    win_type = hand.get('win_type', 'None')
                    win_tile = hand.get('win_tile', {})
                    
                    print(f"玩家{pid}: {len(tiles)}张手牌, 胜利={is_winner}, 类型={win_type}")
                    if tiles:
                        tile_strs = [f"{t.get('value')}{t.get('type')}" for t in tiles[:5]]
                        print(f"  前5张: {tile_strs}")
                        if is_winner and win_tile:
                            print(f"  胜利牌: {win_tile.get('value')}{win_tile.get('type')}")
                    
                # 检查弃牌
                if pid in game_state.get('player_discarded_tiles', {}):
                    discards = game_state['player_discarded_tiles'][pid]
                    if pid == '0':  # 特别关注玩家0的弃牌（应该缺少6万）
                        print(f"玩家{pid}弃牌: {len(discards)}张")
                        discard_strs = [f"{d.get('value')}{d.get('type')}" for d in discards if d]
                        print(f"  弃牌详情: {discard_strs}")
            print("="*80 + "\n")
            
            # 一次性更新完整游戏状态（包含手牌+碰杠牌+胜利状态）
            update_response = self.session.post(
                f"{self.api_base_url}/set-game-state",
                json={"game_state": game_state}
            )
            
            result = update_response.json()
            if not result.get('success'):
                print(f"❌ 设置完整游戏状态失败: {result.get('message', '未知错误')}")
                # 尝试检查具体错误信息
                print(f"响应详情: {result}")
                return False
            
            print("✅ 完整游戏状态设置成功（包含胜利状态）")
            
            # 🔧 验证设置是否成功：检查其他玩家的手牌数据
            print("🔍 验证手牌数据设置...")
            verify_response = self.session.get(f"{self.api_base_url}/game-state")
            if verify_response.status_code == 200:
                verify_result = verify_response.json()
                if verify_result.get('success'):
                    verify_state = verify_result.get('game_state', {})
                    for player_id in ['1', '2', '3']:
                        player_hand = verify_state.get('player_hands', {}).get(player_id, {})
                        tiles = player_hand.get('tiles')
                        tile_count = len(tiles) if tiles else 0
                        print(f"📋 验证玩家{player_id}手牌: {tile_count}张, tiles类型={type(tiles)}")
                        if tiles and len(tiles) > 0:
                            print(f"   前3张牌示例: {tiles[:3]}")
                            # 🔧 详细验证数据格式
                            for i, tile in enumerate(tiles[:3]):
                                if isinstance(tile, dict) and 'type' in tile and 'value' in tile:
                                    print(f"   牌{i+1}: {tile['value']}{tile['type']} ✅")
                                else:
                                    print(f"   牌{i+1}: 格式错误 {tile} ❌")
                        else:
                            print(f"   ⚠️ tiles数据为空或null")
                else:
                    print(f"⚠️ 验证状态失败: {verify_result.get('message', '未知错误')}")
            else:
                print(f"⚠️ 验证请求失败: HTTP {verify_response.status_code}")
            
            print("✅ 完整最终状态设置成功")
            return True
                
        except Exception as e:
            print(f"❌ 设置完整最终状态失败: {e}")
            return False
    
    def set_player_win(self, player_id: int, win_type: str, win_tile: str = None, dianpao_player_id: int = None) -> bool:
        """设置玩家胜利状态"""
        try:
            params = {
                "player_id": player_id,
                "win_type": win_type
            }
            
            if win_tile:
                tile_type, tile_value = self._parse_tile(win_tile)
                params["win_tile_type"] = tile_type
                params["win_tile_value"] = tile_value
                
            if dianpao_player_id is not None:
                params["dianpao_player_id"] = dianpao_player_id
            
            response = self.session.post(f"{self.api_base_url}/player-win", params=params)
            result = response.json()
            
            if result.get('success'):
                win_type_name = "自摸" if win_type == "zimo" else "点炮胡牌"
                print(f"✅ 玩家{player_id}{win_type_name}设置成功")
                return True
            else:
                print(f"❌ 设置玩家胜利失败: {result.get('message', '未知错误')}")
                return False
        except Exception as e:
            print(f"❌ 设置玩家胜利失败: {e}")
            return False
    
    # 注释：set_win_states_from_replay 方法已集成到 set_complete_final_state_from_replay 中
    
    def reveal_all_hands(self) -> bool:
        """牌局结束后显示所有玩家手牌"""
        try:
            response = self.session.post(f"{self.api_base_url}/reveal-all-hands")
            result = response.json()
            if result.get('success'):
                print("✅ 已显示所有玩家手牌")
                
                # 🔧 强制前端状态同步：等待一下，让前端有时间获取最新状态
                print("⏰ 等待前端状态同步...")
                time.sleep(2)
                
                # 🔧 主动获取最新游戏状态，确保前端能看到更新
                print("🔄 验证游戏状态更新...")
                state_response = self.session.get(f"{self.api_base_url}/game-state")
                if state_response.status_code == 200:
                    state_result = state_response.json()
                    if state_result.get('success'):
                        game_state = state_result.get('game_state', {})
                        show_all_hands = game_state.get('show_all_hands', False)
                        print(f"📊 当前show_all_hands状态: {show_all_hands}")
                        
                        # 检查其他玩家是否有手牌数据
                        for player_id in ['1', '2', '3']:
                            player_hand = game_state.get('player_hands', {}).get(player_id, {})
                            tiles = player_hand.get('tiles')
                            tile_count = len(tiles) if tiles else 0
                            print(f"📋 玩家{player_id}手牌: {tile_count}张, tiles类型={type(tiles)}, tiles为空={tiles is None}")
                            if tiles and len(tiles) > 0:
                                print(f"   前3张牌: {tiles[:3]}")
                            else:
                                print(f"   ⚠️  tiles数据为空或null")
                        
                        if show_all_hands:
                            print("✅ 状态同步成功，前端应该能看到所有玩家手牌")
                            
                            # 🔧 最终验证：确保前端能获取到完整的手牌数据
                            all_players_have_tiles = True
                            for player_id in ['1', '2', '3']:
                                player_hand = game_state.get('player_hands', {}).get(player_id, {})
                                tiles = player_hand.get('tiles')
                                if not tiles or len(tiles) == 0:
                                    all_players_have_tiles = False
                                    print(f"❌ 玩家{player_id}仍然没有手牌数据!")
                            
                            if all_players_have_tiles:
                                print("🎉 所有玩家手牌数据验证通过，前端应该能显示!")
                            else:
                                print("⚠️ 部分玩家手牌数据缺失，可能存在数据同步问题")
                        else:
                            print("⚠️ show_all_hands状态仍为False，可能需要更多时间同步")
                    else:
                        print(f"⚠️ 获取游戏状态失败: {state_result.get('message', '未知错误')}")
                else:
                    print(f"⚠️ 获取游戏状态请求失败: HTTP {state_response.status_code}")
                
                return True
            else:
                print(f"❌ 显示所有手牌失败: {result.get('message', '未知错误')}")
                return False
        except Exception as e:
            print(f"❌ 显示所有手牌失败: {e}")
            return False
    
    def play_replay(self, replay_file: str, step_delay: float = 2.0):
        """播放牌谱"""
        print(f"🎬 开始播放牌谱: {replay_file}")
        
        # 1. 检查API服务器
        if not self.health_check():
            print("❌ 请先启动后端服务器")
            return False
        
        # 2. 加载牌谱
        try:
            with open(replay_file, 'r', encoding='utf-8') as f:
                replay_data = json.load(f)
        except Exception as e:
            print(f"❌ 读取牌谱文件失败: {e}")
            return False
        
        # 3. 重置游戏
        if not self.reset_game():
            return False
        
        # 4. 设置定缺
        miss_suits = replay_data.get('misssuit', {})
        for player_id_str, suit in miss_suits.items():
            player_id = int(player_id_str)
            if not self.set_missing_suit(player_id, suit):
                return False
            time.sleep(0.5)
        
        # 5. 设置初始手牌
        initial_hands = replay_data.get('initial_hands', {})
        for player_id_str, hand_data in initial_hands.items():
            player_id = int(player_id_str)
            tiles = hand_data.get('tiles', [])
            
            print(f"📂 设置玩家{player_id}初始手牌...")
            for tile in tiles:
                if player_id == 0:
                    # 玩家0设置具体牌面
                    self.add_hand_tile(player_id, tile)
                else:
                    # 其他玩家只增加数量
                    self.add_hand_count(player_id, 1)
                time.sleep(0.1)
        
        print("⏰ 初始化完成，3秒后开始播放操作...")
        time.sleep(3)
        
        # 6. 执行操作序列
        actions = replay_data.get('actions', [])
        previous_action = None  # 跟踪前一个操作
        for action in actions:
            sequence = action.get('sequence')
            player_id = action.get('player_id')
            action_type = action.get('type')
            tile = action.get('tile')
            target_player = action.get('target_player')
            
            print(f"\n🎯 步骤{sequence}: 玩家{player_id} {action_type} {tile or ''}")
            
            success = True
            if action_type == 'draw':
                # 摸牌操作
                if player_id == 0:
                    success = self.add_hand_tile(player_id, tile)
                else:
                    success = self.add_hand_count(player_id, 1)
                    
            elif action_type == 'discard':
                # 弃牌操作：假设每次弃牌都是刚摸的牌
                # 但如果前一个操作是同一玩家的碰牌或杠牌，则不需要摸牌
                is_after_meld = (previous_action and 
                               previous_action.get('player_id') == player_id and 
                               previous_action.get('type') in ['peng', 'gang', 'angang', 'jiagang'])
                
                if player_id != 0 and not is_after_meld:
                    # 其他玩家先摸一张牌（增加手牌数量），然后弃牌
                    self.add_hand_count(player_id, 1)
                    time.sleep(0.1)  # 短暂延迟显示摸牌动作
                success = self.discard_tile(player_id, tile)
                
            elif action_type == 'peng':
                # 碰牌操作
                success = self.peng_tile(player_id, tile, target_player)
                
            elif action_type == 'gang':
                # 杠牌操作 (这里简化为直杠)
                success = self.gang_tile(player_id, tile, 'zhigang', target_player)
                
            elif action_type == 'angang':
                # 暗杠操作
                success = self.gang_tile(player_id, tile, 'angang')
                
            elif action_type == 'jiagang':
                # 加杠操作
                success = self.gang_tile(player_id, tile, 'jiagang')
                
            elif action_type == 'hu':
                # 点炮胡牌操作
                success = self.set_player_win(player_id, "dianpao", tile, target_player)
                
            elif action_type == 'zimo':
                # 自摸胡牌操作
                success = self.set_player_win(player_id, "zimo", tile)
                
            else:
                print(f"⚠️  未知操作类型: {action_type}")
                success = True
            
            if not success:
                print(f"❌ 操作失败，停止播放")
                return False
            
            # 更新前一个操作
            previous_action = action
            
            # 等待指定时间
            time.sleep(step_delay)
        
        print("\n🎉 牌谱播放完成！")
        
        # 设置完整的最终状态（手牌+碰杠牌+胜利状态）
        print("\n🎯 设置完整最终状态...")
        self.set_complete_final_state_from_replay(replay_data)
        
        # 显示所有玩家手牌
        print("📊 显示所有玩家手牌...")
        self.reveal_all_hands()
        
        return True

def main():
    if len(sys.argv) < 2:
        print("用法: python replay_player.py <牌谱文件> [步骤间隔秒数]")
        print("示例: python replay_player.py model/first_hand/sample_mahjong_game_final.json 1.5")
        sys.exit(1)
    
    replay_file = sys.argv[1]
    step_delay = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
    
    player = ReplayPlayer()
    success = player.play_replay(replay_file, step_delay)
    
    if success:
        print("✅ 牌谱播放成功完成")
    else:
        print("❌ 牌谱播放失败")
        sys.exit(1)

if __name__ == "__main__":
    main()