import redis
import json
from typing import Dict, List, Optional, Tuple, Any
from copy import deepcopy
import asyncio
from datetime import datetime
import uuid  # 添加 uuid 导入

from ..models.mahjong import (
    GameState, HandTiles, Tile, TileType, Meld, MeldType, GangType, 
    PlayerAction, TileOperationRequest
)
from ..algorithms.mahjong_analyzer import MahjongAnalyzer
from ..core.config import settings


class MahjongGameService:
    """麻将游戏服务 - 真实辅助工具版本
    
    设计原则：
    - 玩家0（我）：完全已知的手牌和操作
    - 其他玩家：只知道手牌数量和明牌操作
    - 所有玩家的弃牌和明牌（碰、明杠、加杠）都是可见的
    """
    
    def __init__(self):
        # 初始化Redis连接
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
        self.game_state_key = "mahjong:game_state"
        # 从Redis加载游戏状态，如果没有则创建新的
        self._game_state = self._load_or_create_state()
        self.analyzer = MahjongAnalyzer()
    
    def _load_or_create_state(self) -> Dict[str, Any]:
        """从Redis加载游戏状态，如果不存在则创建新的"""
        try:
            # 尝试从Redis加载
            state_json = self.redis.get(self.game_state_key)
            if state_json:
                return json.loads(state_json)
        except Exception as e:
            print(f"从Redis加载状态失败: {e}")
        
        # 如果加载失败或不存在，创建新的状态
        return self._create_initial_state()
    
    def _save_state(self):
        """保存游戏状态到Redis"""
        try:
            state_json = json.dumps(self._game_state)
            self.redis.set(self.game_state_key, state_json)
        except Exception as e:
            print(f"保存状态到Redis失败: {e}")
    
    def get_game_state(self) -> Dict[str, Any]:
        """获取当前游戏状态"""
        return self._game_state
    
    def set_game_state(self, game_state: GameState) -> bool:
        """设置游戏状态（从Pydantic模型）"""
        try:
            self._game_state = game_state.dict()
            self._save_state()
            return True
        except Exception as e:
            print(f"设置游戏状态失败: {e}")
            return False
    
    def set_game_state_dict(self, game_state: Dict[str, Any]) -> bool:
        """设置游戏状态（从字典）"""
        try:
            self._game_state = game_state
            self._save_state()
            return True
        except Exception as e:
            print(f"设置游戏状态失败: {e}")
            return False
    
    def reset_game(self) -> None:
        """重置游戏状态"""
        self._game_state = self._create_initial_state()
        self._save_state()
    
    def add_tile_to_hand(self, player_id: int, tile: Tile) -> bool:
        """为玩家添加手牌
        
        注意：只有玩家0（我）可以添加具体牌面
        其他玩家只增加手牌数量
        """
        try:
            player_id_str = str(player_id)
            if player_id_str not in self._game_state["player_hands"]:
                self._game_state["player_hands"][player_id_str] = {
                    "tiles": [] if player_id == 0 else None,  # 其他玩家不存储具体牌面
                    "tile_count": 0,  # 新增：手牌数量
                    "melds": []
                }
            
            if player_id == 0:
                # 我：添加具体手牌
                self._game_state["player_hands"][player_id_str]["tiles"].append({
                    "type": tile.type,
                    "value": tile.value
                })
                self._game_state["player_hands"][player_id_str]["tile_count"] = len(
                    self._game_state["player_hands"][player_id_str]["tiles"]
                )
                print(f"✅ 我（玩家0）添加手牌: {tile.value}{tile.type}")
            else:
                # 其他玩家：只增加数量
                self._game_state["player_hands"][player_id_str]["tile_count"] += 1
                print(f"✅ 玩家{player_id}手牌数量+1 (当前:{self._game_state['player_hands'][player_id_str]['tile_count']}张)")
            
            # 记录操作历史
            self._game_state["actions_history"].append({
                "type": "add_hand",
                "player_id": player_id,
                "tile": {
                    "type": tile.type,
                    "value": tile.value
                } if player_id == 0 else None,  # 其他玩家不记录具体牌面
                "timestamp": datetime.now().timestamp()
            })
            
            self._save_state()
            return True
        except Exception as e:
            print(f"添加手牌失败: {e}")
            return False
    
    def discard_tile(self, player_id: int, tile: Tile) -> bool:
        """玩家弃牌"""
        try:
            player_id_str = str(player_id)
            
            # 确保玩家有手牌数据结构
            if player_id_str not in self._game_state["player_hands"]:
                self._game_state["player_hands"][player_id_str] = {
                    "tiles": [] if player_id == 0 else None,
                    "tile_count": 0,
                    "melds": []
                }
            
            if player_id == 0:
                # 我：从具体手牌中移除
                hand_tiles = self._game_state["player_hands"][player_id_str]["tiles"]
                found_tile_index = None
                for i, hand_tile in enumerate(hand_tiles):
                    if hand_tile["type"] == tile.type and hand_tile["value"] == tile.value:
                        found_tile_index = i
                        break
                
                if found_tile_index is not None:
                    hand_tiles.pop(found_tile_index)
                    self._game_state["player_hands"][player_id_str]["tile_count"] = len(hand_tiles)
                    print(f"✅ 我（玩家0）弃牌: {tile.value}{tile.type}")
                else:
                    print(f"⚠️ 我（玩家0）手牌中没有 {tile.value}{tile.type}")
                    return False
            else:
                # 其他玩家：只减少数量
                if self._game_state["player_hands"][player_id_str]["tile_count"] > 0:
                    self._game_state["player_hands"][player_id_str]["tile_count"] -= 1
                    print(f"✅ 玩家{player_id}弃牌，手牌数量-1 (当前:{self._game_state['player_hands'][player_id_str]['tile_count']}张)")
                else:
                    print(f"⚠️ 玩家{player_id}没有手牌可弃")
                    return False
            
            # 添加到弃牌池（所有弃牌都是可见的）
            self._game_state["discarded_tiles"].append(tile.dict())
            
            # 添加到玩家弃牌池
            if player_id_str not in self._game_state["player_discarded_tiles"]:
                self._game_state["player_discarded_tiles"][player_id_str] = []
            self._game_state["player_discarded_tiles"][player_id_str].append(tile.dict())
            
            # 记录操作历史
            self._game_state["actions_history"].append({
                "player_id": player_id,
                "action_type": "discard",
                "tile": tile.dict(),  # 弃牌对所有人可见
                "timestamp": datetime.now().timestamp()
            })
            
            self._save_state()
            return True
        except Exception as e:
            print(f"弃牌失败: {e}")
            return False
    
    def process_operation(self, request: TileOperationRequest) -> Tuple[bool, str]:
        """处理游戏操作"""
        try:
            if request.operation_type == "hand":
                # 添加手牌
                success = self.add_tile_to_hand(request.player_id, request.tile)
                return success, "添加手牌成功" if success else "添加手牌失败"
                
            elif request.operation_type == "discard":
                # 弃牌
                success = self.discard_tile(request.player_id, request.tile)
                return success, "弃牌成功" if success else "弃牌失败"
                
            elif request.operation_type == "peng":
                # 碰牌
                return self._handle_peng(request)
                
            elif request.operation_type in ["angang", "zhigang", "jiagang"]:
                # 杠牌
                return self._handle_gang(request)
                
            else:
                return False, f"不支持的操作类型: {request.operation_type}"
                
        except Exception as e:
            return False, f"操作失败: {str(e)}"
    
    def _initialize_tile_pool(self) -> List[Dict]:
        """初始化牌库"""
        tiles = []
        for tile_type in ["wan", "tiao", "tong"]:
            for value in range(1, 10):
                for _ in range(4):  # 每种牌4张
                    tiles.append({
                        "type": tile_type,
                        "value": value
                    })
        return tiles
    
    def _create_initial_state(self) -> Dict[str, Any]:
        """创建初始游戏状态"""
        return {
            "game_id": str(uuid.uuid4()),
            "player_hands": {
                "0": {"tiles": [], "tile_count": 0, "melds": []},  # 我：存储具体牌面
                "1": {"tiles": None, "tile_count": 0, "melds": []},  # 其他玩家：只存储数量
                "2": {"tiles": None, "tile_count": 0, "melds": []},
                "3": {"tiles": None, "tile_count": 0, "melds": []}
            },
            "discarded_tiles": [],  # 所有弃牌（可见）
            "player_discarded_tiles": {
                "0": [], "1": [], "2": [], "3": []
            },  # 每个玩家的弃牌（可见）
            "actions_history": [],  # 操作历史
            "current_player": 0,  # 当前玩家
            "game_started": False,  # 游戏是否开始
            "last_action": None,  # 最后一个动作
            "tile_pool": self._initialize_tile_pool(),  # 牌池
            "players": {  # 玩家信息
                "0": {"position": "我"},
                "1": {"position": "下家"},
                "2": {"position": "对家"},
                "3": {"position": "上家"}
            }
        }
    
    def start_game(self) -> Tuple[bool, str]:
        """开始游戏"""
        try:
            self._game_state["game_started"] = True
            self._save_state()
            return True, "游戏开始"
        except Exception as e:
            return False, f"开始游戏失败: {str(e)}"
    
    def draw_tile(self, player_id: int) -> Tuple[bool, str, Optional[Dict]]:
        """摸牌"""
        try:
            if not self._game_state["tile_pool"]:
                return False, "牌库已空", None
            
            tile = self._game_state["tile_pool"].pop()
            player_id_str = str(player_id)
            
            if player_id == 0:
                # 我：添加具体牌面到手牌
                self._game_state["player_hands"][player_id_str]["tiles"].append(tile)
                self._game_state["player_hands"][player_id_str]["tile_count"] = len(
                    self._game_state["player_hands"][player_id_str]["tiles"]
                )
                print(f"✅ 我（玩家0）摸牌: {tile['value']}{tile['type']}")
                return True, "摸牌成功", tile
            else:
                # 其他玩家：只增加手牌数量
                self._game_state["player_hands"][player_id_str]["tile_count"] += 1
                print(f"✅ 玩家{player_id}摸牌，手牌数量+1 (当前:{self._game_state['player_hands'][player_id_str]['tile_count']}张)")
                return True, "摸牌成功", None  # 不返回具体牌面
                
        except Exception as e:
            return False, f"摸牌失败: {str(e)}", None
    
    def _handle_discard(self, request: TileOperationRequest) -> Tuple[bool, str]:
        """处理弃牌操作"""
        success = self.discard_tile(request.player_id, request.tile)
        return success, "弃牌成功" if success else "弃牌失败"
    
    def _remove_tiles_from_my_hand(self, tile: Tile, count: int) -> int:
        """从我的手牌中移除指定数量的牌"""
        player_hand = self._game_state["player_hands"]["0"]["tiles"]
        
        removed = 0
        for i in range(len(player_hand) - 1, -1, -1):  # 从后往前遍历
            if removed >= count:
                break
            hand_tile = player_hand[i]
            if (hand_tile["type"] == tile.type and 
                hand_tile["value"] == tile.value):
                player_hand.pop(i)
                removed += 1
                print(f"🗑️ 从我的手牌移除{tile.value}{tile.type} ({removed}/{count})")
        
        # 更新手牌数量
        self._game_state["player_hands"]["0"]["tile_count"] = len(player_hand)
        return removed
    
    def _reduce_other_player_hand_count(self, player_id: int, count: int):
        """减少其他玩家的手牌数量"""
        player_id_str = str(player_id)
        current_count = self._game_state["player_hands"][player_id_str]["tile_count"]
        new_count = max(0, current_count - count)
        self._game_state["player_hands"][player_id_str]["tile_count"] = new_count
        print(f"🔢 玩家{player_id}手牌数量: {current_count} → {new_count} (减少{count}张)")
    
    def _auto_draw_tile_for_player(self, player_id: int):
        """为玩家自动摸一张牌"""
        if self._game_state["tile_pool"]:
            tile = self._game_state["tile_pool"].pop()
            
            if player_id == 0:
                # 我：添加具体牌面
                self._game_state["player_hands"]["0"]["tiles"].append(tile)
                self._game_state["player_hands"]["0"]["tile_count"] = len(
                    self._game_state["player_hands"]["0"]["tiles"]
                )
                print(f"🎯 我（玩家0）自动摸牌: {tile['value']}{tile['type']}")
            else:
                # 其他玩家：只增加数量
                self._game_state["player_hands"][str(player_id)]["tile_count"] += 1
                print(f"🎯 玩家{player_id}自动摸牌，手牌数量+1")
            
            return tile
        else:
            print(f"⚠️ 牌库已空，无法为玩家{player_id}摸牌")
            return None

    def _remove_tile_from_discard_pile(self, player_id: int, tile: Tile):
        """从指定玩家的弃牌堆中移除指定的牌"""
        try:
            player_id_str = str(player_id)
            
            # 确保弃牌堆存在
            if "player_discarded_tiles" not in self._game_state:
                self._game_state["player_discarded_tiles"] = {}
            
            if player_id_str not in self._game_state["player_discarded_tiles"]:
                self._game_state["player_discarded_tiles"][player_id_str] = []
                return
            
            discarded_tiles = self._game_state["player_discarded_tiles"][player_id_str]
            
            # 从后往前查找最新弃出的相同牌（通常被碰/杠的是最后弃出的牌）
            for i in range(len(discarded_tiles) - 1, -1, -1):
                discarded_tile = discarded_tiles[i]
                if (discarded_tile["type"] == tile.type and 
                    discarded_tile["value"] == tile.value):
                    # 找到匹配的牌，移除它
                    removed_tile = discarded_tiles.pop(i)
                    print(f"🗑️ 从玩家{player_id}弃牌堆移除: {removed_tile['value']}{removed_tile['type']}")
                    break
            else:
                print(f"⚠️ 警告：在玩家{player_id}弃牌堆中未找到 {tile.value}{tile.type}")
                return
            
            # 🔧 修复：同时从全局弃牌堆中移除被碰/杠的牌
            if "discarded_tiles" not in self._game_state:
                self._game_state["discarded_tiles"] = []
            
            # 从后往前查找并移除全局弃牌堆中的对应牌
            global_discarded = self._game_state["discarded_tiles"]
            for i in range(len(global_discarded) - 1, -1, -1):
                global_tile = global_discarded[i]
                if (global_tile["type"] == tile.type and 
                    global_tile["value"] == tile.value):
                    # 找到匹配的牌，移除它
                    removed_global_tile = global_discarded.pop(i)
                    print(f"🌍 从全局弃牌堆移除: {removed_global_tile['value']}{removed_global_tile['type']}")
                    break
            else:
                print(f"⚠️ 警告：在全局弃牌堆中未找到 {tile.value}{tile.type}")
            
        except Exception as e:
            print(f"❌ 从弃牌堆移除牌失败: {e}")
    
    def _handle_peng(self, request: TileOperationRequest) -> Tuple[bool, str]:
        """处理碰牌操作
        
        真实逻辑：
        - 我：从手牌移除2张，减少手牌数量3张（碰牌后自动出1张）
        - 其他玩家：只减少手牌数量3张
        """
        try:
            player_id = request.player_id
            player_id_str = str(player_id)
            
            # 确保玩家手牌结构存在
            if player_id_str not in self._game_state["player_hands"]:
                if player_id == 0:
                    self._game_state["player_hands"][player_id_str] = {"tiles": [], "tile_count": 0, "melds": []}
                else:
                    self._game_state["player_hands"][player_id_str] = {"tiles": None, "tile_count": 0, "melds": []}
            
            print(f"🀄 玩家{player_id}碰牌{request.tile.value}{request.tile.type}")
            
            if player_id == 0:
                # 我：检查并移除手牌中的2张牌
                removed = self._remove_tiles_from_my_hand(request.tile, 2)
                if removed < 2:
                    return False, f"手牌中没有足够的{request.tile.value}{request.tile.type}进行碰牌"
                
                # 注意：不在这里自动出牌，由外部调用弃牌API处理
                print(f"🎯 我碰牌完成，手牌中移除了2张{request.tile.value}{request.tile.type}")
                
            else:
                # 其他玩家：只减少手牌数量2张（手中用掉的牌）
                self._reduce_other_player_hand_count(player_id, 2)
            
            # 创建碰牌组（对所有人可见）
            meld = {
                "id": str(uuid.uuid4()),
                "type": "peng",
                "tiles": [
                    request.tile.dict(),
                    request.tile.dict(),
                    request.tile.dict()
                ],
                "exposed": True,
                "gang_type": None,
                "source_player": request.source_player_id,
                "original_peng_id": None,
                "timestamp": datetime.now().timestamp()
            }
            
            # 从被碰玩家的弃牌堆中移除被碰的牌
            if request.source_player_id is not None:
                self._remove_tile_from_discard_pile(request.source_player_id, request.tile)
            
            # 添加到玩家的melds中
            self._game_state["player_hands"][player_id_str]["melds"].append(meld)
            
            # 记录操作历史
            if "actions_history" not in self._game_state:
                self._game_state["actions_history"] = []
            
            action = {
                "player_id": request.player_id,
                "action_type": "peng",
                "tile": request.tile.dict(),  # 碰牌操作对所有人可见
                "source_player": request.source_player_id,
                "timestamp": datetime.now().timestamp()
            }
            self._game_state["actions_history"].append(action)
            
            print(f"✅ 玩家{player_id}碰牌完成")
            
            # 保存状态
            self._save_state()
            return True, "碰牌成功"
            
        except Exception as e:
            print(f"碰牌失败: {e}")
            return False, f"碰牌失败: {str(e)}"
    
    def _handle_gang(self, request: TileOperationRequest) -> Tuple[bool, str]:
        """处理杠牌操作
        
        真实逻辑：
        - 暗杠：只有我可以进行，其他玩家的暗杠不可见
        - 直杠：减少相应手牌数量，杠牌组对所有人可见
        - 加杠：在已有碰牌基础上进行
        """
        try:
            player_id = request.player_id
            player_id_str = str(player_id)
            
            # 确保玩家手牌结构存在
            if player_id_str not in self._game_state["player_hands"]:
                if player_id == 0:
                    self._game_state["player_hands"][player_id_str] = {"tiles": [], "tile_count": 0, "melds": []}
                else:
                    self._game_state["player_hands"][player_id_str] = {"tiles": None, "tile_count": 0, "melds": []}
            
            # 根据operation_type确定杠牌类型
            gang_type_map = {
                "angang": "an_gang",
                "zhigang": "ming_gang",
                "jiagang": "jia_gang"
            }
            
            gang_type = gang_type_map.get(request.operation_type, "an_gang")
            print(f"🀄 玩家{player_id}{gang_type}杠牌{request.tile.value}{request.tile.type}")
            
            # 处理不同类型的杠牌
            original_peng_id = None
            original_source_player = None  # 新增：保存原始碰牌的来源玩家
            exposed = True  # 默认明杠
            
            if request.operation_type == "jiagang":
                # 加杠：查找已有的碰牌并移除
                for meld_item in self._game_state["player_hands"][player_id_str]["melds"]:
                    if (meld_item["type"] == "peng" and 
                        len(meld_item["tiles"]) > 0 and
                        meld_item["tiles"][0]["type"] == request.tile.type and
                        meld_item["tiles"][0]["value"] == request.tile.value):
                        original_peng_id = meld_item["id"]
                        original_source_player = meld_item.get("source_player")  # 保存原始碰牌的来源
                        self._game_state["player_hands"][player_id_str]["melds"].remove(meld_item)
                        print(f"🔄 移除原有碰牌组{original_peng_id}，原始来源：玩家{original_source_player}")
                        break
                
                # 加杠：从手牌移除1张牌，摸1张牌
                if player_id == 0:
                    removed = self._remove_tiles_from_my_hand(request.tile, 1)
                    if removed < 1:
                        return False, f"手牌中没有{request.tile.value}{request.tile.type}进行加杠"
                else:
                    self._reduce_other_player_hand_count(player_id, 1)
                
                # 摸1张牌
                self._auto_draw_tile_for_player(player_id)
                
            elif request.operation_type == "angang":
                # 暗杠：只有我可以进行，且只对我可见
                if player_id != 0:
                    return False, "其他玩家的暗杠不可见，无法处理"
                
                # 从我的手牌移除4张牌
                removed = self._remove_tiles_from_my_hand(request.tile, 4)
                if removed < 4:
                    return False, f"手牌中没有足够的{request.tile.value}{request.tile.type}进行暗杠"
                
                # 摸1张牌
                self._auto_draw_tile_for_player(0)
                
                exposed = False  # 暗杠不对其他人可见
                
            elif request.operation_type == "zhigang":
                # 直杠：从手牌移除3张牌，摸1张牌，出1张牌
                if player_id == 0:
                    removed = self._remove_tiles_from_my_hand(request.tile, 3)
                    if removed < 3:
                        return False, f"手牌中没有足够的{request.tile.value}{request.tile.type}进行直杠"
                else:
                    self._reduce_other_player_hand_count(player_id, 3)
                
                # 从被杠玩家的弃牌堆中移除被杠的牌
                if request.source_player_id is not None:
                    self._remove_tile_from_discard_pile(request.source_player_id, request.tile)
                
                # 摸1张牌
                self._auto_draw_tile_for_player(player_id)
                
                # 注意：直杠后的出牌在外部API调用中单独处理，这里不自动出牌
            
            # 创建杠牌组
            meld = {
                "id": str(uuid.uuid4()),
                "type": "gang",
                "tiles": [
                    request.tile.dict(),
                    request.tile.dict(),
                    request.tile.dict(),
                    request.tile.dict()
                ],
                "exposed": exposed,
                "gang_type": gang_type,
                "source_player": (
                    request.source_player_id if gang_type == "ming_gang" 
                    else original_source_player if gang_type == "jia_gang" 
                    else None
                ),
                "original_peng_id": original_peng_id,
                "timestamp": datetime.now().timestamp()
            }
            
            # 添加到玩家的melds中
            self._game_state["player_hands"][player_id_str]["melds"].append(meld)
            print(f"🔧 创建杠牌组：type={meld['type']}, gang_type={meld['gang_type']}, source_player={meld['source_player']}")
            
            # 记录操作历史
            if "actions_history" not in self._game_state:
                self._game_state["actions_history"] = []
            
            action = {
                "player_id": request.player_id,
                "action_type": f"gang_{gang_type}",
                "tile": request.tile.dict() if exposed else None,  # 暗杠不记录具体牌面
                "source_player": (
                    request.source_player_id if gang_type == "ming_gang" 
                    else original_source_player if gang_type == "jia_gang" 
                    else None
                ),
                "timestamp": datetime.now().timestamp()
            }
            self._game_state["actions_history"].append(action)
            
            print(f"✅ 玩家{player_id}杠牌完成 ({gang_type})")
            
            # 保存状态
            self._save_state()
            return True, f"杠牌成功 ({gang_type})"
            
        except Exception as e:
            print(f"杠牌失败: {e}")
            return False, f"杠牌失败: {str(e)}"

    # ============ 定缺相关方法 ============

    def set_player_missing_suit(self, player_id: int, missing_suit: str) -> bool:
        """设置玩家定缺花色"""
        try:
            player_id_str = str(player_id)
            
            # 验证花色
            valid_suits = ["wan", "tiao", "tong"]
            if missing_suit not in valid_suits:
                print(f"❌ 无效的定缺花色: {missing_suit}")
                return False
            
            # 确保玩家手牌结构存在
            if player_id_str not in self._game_state["player_hands"]:
                self._game_state["player_hands"][player_id_str] = {
                    "tiles": [] if player_id == 0 else None,
                    "tile_count": 0,
                    "melds": [],
                    "missing_suit": None
                }
            
            # 设置定缺
            self._game_state["player_hands"][player_id_str]["missing_suit"] = missing_suit
            
            # 记录操作历史
            if "actions_history" not in self._game_state:
                self._game_state["actions_history"] = []
            
            action = {
                "player_id": player_id,
                "action_type": "missing_suit",
                "missing_suit": missing_suit,
                "timestamp": datetime.now().timestamp()
            }
            self._game_state["actions_history"].append(action)
            
            print(f"✅ 玩家{player_id}定缺设置成功: {missing_suit}")
            
            # 保存状态
            self._save_state()
            return True
            
        except Exception as e:
            print(f"设置定缺失败: {e}")
            return False

    def get_player_missing_suit(self, player_id: int) -> Optional[str]:
        """获取玩家定缺花色"""
        try:
            player_id_str = str(player_id)
            if player_id_str in self._game_state["player_hands"]:
                return self._game_state["player_hands"][player_id_str].get("missing_suit")
            return None
        except Exception as e:
            print(f"获取定缺失败: {e}")
            return None

    def get_all_missing_suits(self) -> Dict[str, Optional[str]]:
        """获取所有玩家的定缺信息"""
        missing_suits = {}
        try:
            for player_id_str, hand in self._game_state.get("player_hands", {}).items():
                missing_suits[player_id_str] = hand.get("missing_suit")
            return missing_suits
        except Exception as e:
            print(f"获取所有定缺信息失败: {e}")
            return {}

    def reset_all_missing_suits(self) -> bool:
        """重置所有玩家的定缺"""
        try:
            for player_id_str, hand in self._game_state.get("player_hands", {}).items():
                hand["missing_suit"] = None
            
            print("✅ 所有玩家定缺已重置")
            
            # 保存状态
            self._save_state()
            return True
            
        except Exception as e:
            print(f"重置所有定缺失败: {e}")
            return False

    def is_tile_missing_suit(self, player_id: int, tile: Tile) -> bool:
        """检查牌是否为玩家的定缺花色"""
        try:
            missing_suit = self.get_player_missing_suit(player_id)
            if missing_suit is None:
                return False
            return tile.type == missing_suit
        except Exception as e:
            print(f"检查定缺失败: {e}")
            return False 