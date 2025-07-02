#!/usr/bin/env python3
"""
腾讯欢乐麻将血战到底辅助分析工具
功能：重现真实牌局，分析决策点，评估弃牌选择
包含：完整牌局模拟、决策分析、策略评估、牌谱导出
"""

import requests
import json
import time
from datetime import datetime
import random
from collections import defaultdict
from typing import List, Tuple, Dict, Optional, Any

# API基础URL
BASE_URL = "http://localhost:8000/api/mahjong"

class DecisionAnalyzer:
    """决策分析器"""
    
    def __init__(self):
        self.suit_names = {"wan": "万", "tiao": "条", "tong": "筒"}
        
    def analyze_discard_options(self, hand_cards: List[Tuple[str, int]], known_info: Dict) -> Dict:
        """分析弃牌选择"""
        options = []
        
        for card in set(hand_cards):  # 去重
            score = self._calculate_card_value(card, hand_cards, known_info)
            options.append({
                "card": card,
                "score": score,
                "reason": self._get_discard_reason(card, hand_cards)
            })
        
        options.sort(key=lambda x: x["score"])  # 分数越低越适合弃掉
        
        return {
            "best_discard": options[0]["card"],
            "worst_discard": options[-1]["card"],
            "all_options": options
        }
    
    def _calculate_card_value(self, card: Tuple[str, int], hand: List[Tuple[str, int]], known: Dict) -> float:
        """计算牌的保留价值"""
        suit, value = card
        count = hand.count(card)
        
        # 基础分数（越小越容易弃掉）
        score = 50.0
        
        # 多张同牌加分
        if count >= 2:
            score += count * 20
            
        # 搭子分析
        if self._is_part_of_sequence(card, hand):
            score += 30
            
        # 边张减分
        if value in [1, 9]:
            score -= 10
            
        # 中张加分
        if value in [4, 5, 6]:
            score += 15
            
        return score
    
    def _is_part_of_sequence(self, card: Tuple[str, int], hand: List[Tuple[str, int]]) -> bool:
        """检查是否为顺子的一部分"""
        suit, value = card
        
        # 检查前后牌
        prev_card = (suit, value - 1)
        next_card = (suit, value + 1)
        
        return prev_card in hand or next_card in hand
    
    def _get_discard_reason(self, card: Tuple[str, int], hand: List[Tuple[str, int]]) -> str:
        """获取弃牌原因"""
        suit, value = card
        count = hand.count(card)
        
        if count >= 3:
            return "有3张，可暗杠"
        elif count == 2:
            return "成对，等碰牌"
        elif value in [1, 9]:
            return "边张，不易成顺"
        elif self._is_part_of_sequence(card, hand):
            return "搭子，等成顺"
        else:
            return "孤立牌，优先弃掉"


class RealGameSimulator:
    """腾讯欢乐麻将血战到底真实牌局模拟器"""
    
    def __init__(self):
        self.player_names = {0: "我(庄家)", 1: "下家", 2: "对家", 3: "上家"}
        self.suit_names = {"wan": "万", "tiao": "条", "tong": "筒"}
        self.gang_type_names = {
            "angang": "暗杠",
            "zhigang": "直杠", 
            "jiagang": "加杠"
        }
        
        # 牌局状态
        self.current_round = 0
        self.win_players = set()
        self.my_player_id = 0  # 我的玩家ID
        
        # 牌库管理
        self.deck = []
        self.used_tiles = defaultdict(int)
        
        # 手牌管理（只有我的手牌记录具体牌，其他玩家只记录数量）
        self.my_hand = []  # 我的具体手牌
        self.player_hand_counts = {i: 0 for i in range(4)}  # 所有玩家手牌数量
        
        # 明牌信息
        self.all_discards = {i: [] for i in range(4)}  # 所有玩家弃牌
        self.all_melds = {i: [] for i in range(4)}     # 所有玩家碰杠
        
        # 游戏分析
        self.game_events = []           # 游戏事件序列
        self.decision_points = []       # 我的决策点
        self.analyzer = DecisionAnalyzer()
        
        self.initialize_deck()
        
    def initialize_deck(self):
        """初始化108张完整牌库"""
        self.deck = []
        self.used_tiles = defaultdict(int)
        
        # 创建108张牌：每种牌4张
        for suit in ['wan', 'tiao', 'tong']:
            for value in range(1, 10):
                for _ in range(4):
                    self.deck.append((suit, value))
        
        # 洗牌
        random.shuffle(self.deck)
        self.log(f"✅ 初始化108张牌库完成，洗牌后准备发牌")
        
    def get_deck_status(self):
        """获取牌库状态统计"""
        remaining_count = len(self.deck)
        used_count = sum(self.used_tiles.values())
        return f"剩余牌库: {remaining_count}张, 已使用: {used_count}张, 总计: {remaining_count + used_count}张"
        
    def validate_deck_integrity(self):
        """验证牌库完整性"""
        total_tiles = defaultdict(int)
        
        # 统计剩余牌库
        for suit, value in self.deck:
            total_tiles[(suit, value)] += 1
            
        # 统计已使用的牌
        for (suit, value), count in self.used_tiles.items():
            total_tiles[(suit, value)] += count
            
        # 检查每种牌是否正好4张
        errors = []
        for suit in ['wan', 'tiao', 'tong']:
            for value in range(1, 10):
                key = (suit, value)
                if total_tiles[key] != 4:
                    errors.append(f"{value}{self.suit_names[suit]}: {total_tiles[key]}张")
                    
        if errors:
            self.log(f"❌ 牌库完整性检查失败: {errors}")
            return False
        else:
            self.log(f"✅ 牌库完整性检查通过: 每种牌都是4张")
            return True
        
    def draw_tile_from_deck(self) -> Optional[Tuple[str, int]]:
        """从牌库摸一张牌"""
        if not self.deck:
            self.log("❌ 牌库已空，无法摸牌")
            return None
            
        tile = self.deck.pop(0)  # 从牌库顶部摸牌
        self.used_tiles[tile] += 1
        self.log(f"🎯 从牌库摸牌: {tile[1]}{self.suit_names[tile[0]]} ({self.get_deck_status()})")
        return tile
        
    def use_specific_tile(self, suit: str, value: int) -> bool:
        """使用指定的牌（从牌库中移除）"""
        target_tile = (suit, value)
        
        # 检查牌库中是否还有这张牌
        if target_tile in self.deck:
            self.deck.remove(target_tile)
            self.used_tiles[target_tile] += 1
            self.log(f"🎯 使用指定牌: {value}{self.suit_names[suit]} ({self.get_deck_status()})")
            return True
        else:
            # 检查是否超过4张限制
            if self.used_tiles[target_tile] >= 4:
                self.log(f"❌ 无法使用 {value}{self.suit_names[suit]}，已使用{self.used_tiles[target_tile]}张（超过4张限制）")
            else:
                self.log(f"❌ 牌库中没有 {value}{self.suit_names[suit]}，当前已使用{self.used_tiles[target_tile]}张")
            return False
        
    def log(self, message, level="INFO"):
        """日志输出"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def wait_for_user(self, prompt="按回车键继续..."):
        """等待用户输入回车键继续"""
        try:
            input(f"\n💡 {prompt}")
        except KeyboardInterrupt:
            print("\n\n🛑 用户中断了游戏")
            exit(0)
    
    def format_cards(self, cards: List[Tuple[str, int]]) -> str:
        """格式化显示牌"""
        if not cards:
            return "无"
        formatted = []
        for suit, value in cards:
            formatted.append(f"{value}{self.suit_names[suit]}")
        return " ".join(formatted)
    
    def log_game_event(self, event_type: str, player_id: int, details: Dict):
        """记录游戏事件"""
        event = {
            "round": self.current_round,
            "type": event_type,
            "player": player_id,
            "player_name": self.player_names[player_id],
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.game_events.append(event)
        
    def analyze_my_decision(self, situation: str, my_choice: Tuple[str, int], hand_cards: List[Tuple[str, int]]):
        """分析我的决策"""
        known_info = {
            "discards": self.all_discards,
            "melds": self.all_melds,
            "remaining_deck": len(self.deck),
            "other_players_counts": {i: self.player_hand_counts[i] for i in range(4) if i != self.my_player_id}
        }
        
        analysis = self.analyzer.analyze_discard_options(hand_cards, known_info)
        
        decision_point = {
            "round": self.current_round,
            "situation": situation,
            "my_hand": hand_cards.copy(),
            "my_choice": my_choice,
            "analysis": analysis,
            "is_optimal": my_choice == analysis["best_discard"]
        }
        
        self.decision_points.append(decision_point)
        
        # 显示决策分析
        self.show_decision_analysis(decision_point)
        
    def show_decision_analysis(self, decision: Dict):
        """显示决策分析"""
        print("\n" + "="*60)
        print(f"🤔 决策分析点 - 第{decision['round']}轮")
        print(f"📍 情况: {decision['situation']}")
        print(f"🀫 我的手牌: {self.format_cards(decision['my_hand'])}")
        print()
        
        analysis = decision['analysis']
        print("💡 弃牌分析:")
        
        # 显示前3个最佳选择
        for i, option in enumerate(analysis['all_options'][:3], 1):
            card = option['card']
            score = option['score']
            reason = option['reason']
            card_str = f"{card[1]}{self.suit_names[card[0]]}"
            print(f"   {i}. {card_str} (分数:{score:.1f}) - {reason}")
        
        print()
        my_choice_str = f"{decision['my_choice'][1]}{self.suit_names[decision['my_choice'][0]]}"
        best_choice_str = f"{analysis['best_discard'][1]}{self.suit_names[analysis['best_discard'][0]]}"
        
        print(f"🎯 我的选择: {my_choice_str}")
        print(f"🏆 推荐选择: {best_choice_str}")
        
        if decision['is_optimal']:
            print("✅ 决策评价: 最优选择！")
        else:
            print("⚠️  决策评价: 可以优化")
            
        print("="*60)
        
    def test_api_connection(self):
        """测试API连接"""
        try:
            response = requests.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                self.log("✅ API连接正常")
                return True
            else:
                self.log("❌ API连接失败")
                return False
        except Exception as e:
            self.log(f"❌ API连接错误: {e}")
            return False

    def reset_game(self):
        """重置游戏状态"""
        try:
            response = requests.post(f"{BASE_URL}/reset")
            if response.status_code == 200:
                self.log("✅ 游戏状态已重置")
                self.current_round = 0
                self.win_players.clear()
                # 重置牌库和手牌
                self.initialize_deck()
                self.my_hand = []
                self.player_hand_counts = {i: 0 for i in range(4)}
                self.all_discards = {i: [] for i in range(4)}
                self.all_melds = {i: [] for i in range(4)}
                self.game_events = []
                self.decision_points = []
                return True
            else:
                self.log(f"❌ 重置游戏失败: {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ 重置游戏错误: {e}")
            return False

    def set_missing_suit(self, player_id, missing_suit):
        """设置玩家定缺"""
        try:
            params = {
                "player_id": player_id,
                "missing_suit": missing_suit
            }
            response = requests.post(f"{BASE_URL}/set-missing-suit", params=params)
            
            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    self.log(f"✅ {self.player_names[player_id]}定缺: {self.suit_names[missing_suit]}")
                    return True
                else:
                    self.log(f"❌ 设置定缺失败: {result['message']}")
                    return False
            else:
                self.log(f"❌ 设置定缺请求失败: {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ 设置定缺错误: {e}")
            return False

    def add_hand_tile(self, player_id, tile_type, tile_value, description=""):
        """为玩家添加手牌"""
        if player_id == self.my_player_id:
            # 我的手牌：需要记录具体牌
            if not self.use_specific_tile(tile_type, tile_value):
                self.log(f"❌ 无法为我添加{tile_value}{self.suit_names[tile_type]}：牌库限制")
                return False
                
            try:
                # 更新我的具体手牌
                self.my_hand.append((tile_type, tile_value))
                self.player_hand_counts[player_id] += 1
                
                # 调用API为我添加具体手牌
                params = {
                    "player_id": player_id,
                    "tile_type": tile_type,
                    "tile_value": tile_value
                }
                response = requests.post(f"{BASE_URL}/add-hand-tile", params=params)
                
                if response.status_code == 200:
                    result = response.json()
                    if result["success"]:
                        self.log(f"✅ 我添加手牌 {tile_value}{self.suit_names[tile_type]} {description}")
                        return True
                    else:
                        # API失败，回滚本地状态
                        self.my_hand.remove((tile_type, tile_value))
                        self.player_hand_counts[player_id] -= 1
                        self.deck.append((tile_type, tile_value))
                        self.used_tiles[(tile_type, tile_value)] -= 1
                        self.log(f"❌ 添加手牌失败: {result['message']}")
                        return False
                else:
                    # API失败，回滚本地状态
                    self.my_hand.remove((tile_type, tile_value))
                    self.player_hand_counts[player_id] -= 1
                    self.deck.append((tile_type, tile_value))
                    self.used_tiles[(tile_type, tile_value)] -= 1
                    self.log(f"❌ 添加手牌请求失败: {response.text}")
                    return False
            except Exception as e:
                # 异常，回滚本地状态
                if (tile_type, tile_value) in self.my_hand:
                    self.my_hand.remove((tile_type, tile_value))
                    self.player_hand_counts[player_id] -= 1
                self.deck.append((tile_type, tile_value))
                self.used_tiles[(tile_type, tile_value)] -= 1
                self.log(f"❌ 添加手牌错误: {e}")
                return False
        else:
            # 其他玩家：只增加手牌数量，不记录具体牌
            # 需要同步到后端让前端能正确显示
            try:
                # 本地增加手牌数量
                self.player_hand_counts[player_id] += 1
                
                # 同步到后端：使用add-hand-count API
                params = {
                    "player_id": player_id,
                    "count": 1
                }
                response = requests.post(f"{BASE_URL}/add-hand-count", params=params)
                
                if response.status_code == 200:
                    result = response.json()
                    if result["success"]:
                        self.log(f"✅ {self.player_names[player_id]}摸牌1张 {description} (手牌:{self.player_hand_counts[player_id]}张)")
                        return True
                    else:
                        # API失败，回滚本地状态
                        self.player_hand_counts[player_id] -= 1
                        self.log(f"❌ 同步手牌数量失败: {result['message']}")
                        return False
                else:
                    # API失败，回滚本地状态
                    self.player_hand_counts[player_id] -= 1
                    self.log(f"❌ 同步手牌数量请求失败: {response.text}")
                    return False
                    
            except Exception as e:
                # 异常，回滚本地状态
                self.player_hand_counts[player_id] -= 1
                self.log(f"❌ 增加手牌数量错误: {e}")
                return False

    def draw_tile_for_player(self, player_id, description="摸牌"):
        """🆕 新增：为玩家从牌库摸牌"""
        tile = self.draw_tile_from_deck()
        if tile is None:
            return False
            
        suit, value = tile
        return self.add_hand_tile(player_id, suit, value, f"({description})")

    def discard_tile(self, player_id, tile_type, tile_value, description="", analyze=False):
        """弃牌"""
        try:
            if player_id == self.my_player_id:
                # 我的弃牌：检查是否真的有这张牌
                if (tile_type, tile_value) not in self.my_hand:
                    self.log(f"❌ 我没有{tile_value}{self.suit_names[tile_type]}，无法弃牌")
                    return False
                    
                # 弃牌前分析
                if analyze:
                    self.analyze_my_decision(f"弃牌选择", (tile_type, tile_value), self.my_hand)
                
                # 执行弃牌API
                params = {
                    "player_id": player_id,
                    "tile_type": tile_type,
                    "tile_value": tile_value
                }
                response = requests.post(f"{BASE_URL}/discard-tile", params=params)
                
                if response.status_code == 200:
                    result = response.json()
                    if result["success"]:
                        # 从我的手牌中移除
                        self.my_hand.remove((tile_type, tile_value))
                        self.player_hand_counts[player_id] -= 1
                        
                        # 记录到弃牌堆
                        self.all_discards[player_id].append((tile_type, tile_value))
                        
                        # 记录游戏事件
                        self.log_game_event("discard", player_id, {
                            "tile": (tile_type, tile_value),
                            "description": description
                        })
                        
                        self.log(f"✅ 我弃牌 {tile_value}{self.suit_names[tile_type]} {description}")
                        return True
                    else:
                        self.log(f"❌ 弃牌失败: {result['message']}")
                        return False
                else:
                    self.log(f"❌ 弃牌请求失败: {response.text}")
                    return False
            else:
                # 其他玩家弃牌：直接从牌库取出指定牌作为弃牌
                if not self.use_specific_tile(tile_type, tile_value):
                    self.log(f"❌ 牌库中没有{tile_value}{self.suit_names[tile_type]}，{self.player_names[player_id]}无法弃牌")
                    return False
                
                # 减少玩家手牌数量
                if self.player_hand_counts[player_id] <= 0:
                    self.log(f"❌ {self.player_names[player_id]}手牌数量为0，无法弃牌")
                    return False
                
                # 需要同步到后端让前端能正确显示弃牌
                try:
                    # 本地减少手牌数量
                    self.player_hand_counts[player_id] -= 1
                    
                    # 调用弃牌API让前端弃牌堆能正确显示
                    params = {
                        "player_id": player_id,
                        "tile_type": tile_type,
                        "tile_value": tile_value
                    }
                    response = requests.post(f"{BASE_URL}/discard-tile", params=params)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result["success"]:
                            # 记录到弃牌堆
                            self.all_discards[player_id].append((tile_type, tile_value))
                            
                            # 记录游戏事件
                            self.log_game_event("discard", player_id, {
                                "tile": (tile_type, tile_value),
                                "description": description
                            })
                            
                            self.log(f"✅ {self.player_names[player_id]}弃牌 {tile_value}{self.suit_names[tile_type]} {description} (手牌:{self.player_hand_counts[player_id]}张)")
                            return True
                        else:
                            # API失败，回滚本地状态
                            self.player_hand_counts[player_id] += 1
                            self.deck.append((tile_type, tile_value))
                            self.used_tiles[(tile_type, tile_value)] -= 1
                            self.log(f"❌ 弃牌API失败: {result['message']}")
                            return False
                    else:
                        # API失败，回滚本地状态
                        self.player_hand_counts[player_id] += 1
                        self.deck.append((tile_type, tile_value))
                        self.used_tiles[(tile_type, tile_value)] -= 1
                        self.log(f"❌ 弃牌请求失败: {response.text}")
                        return False
                    
                except Exception as e:
                    # 异常，回滚牌库状态和本地状态
                    self.deck.append((tile_type, tile_value))
                    self.used_tiles[(tile_type, tile_value)] -= 1
                    self.player_hand_counts[player_id] += 1  # 回滚手牌数量
                    self.log(f"❌ 其他玩家弃牌错误: {e}")
                    return False
                    
        except Exception as e:
            self.log(f"❌ 弃牌错误: {e}")
            return False

    def peng_tile(self, player_id, tile_type, tile_value, source_player_id, description=""):
        """碰牌"""
        try:
            if player_id == self.my_player_id:
                # 我的碰牌：需要调用API
                params = {
                    "player_id": player_id,
                    "tile_type": tile_type,
                    "tile_value": tile_value,
                    "source_player_id": source_player_id
                }
                response = requests.post(f"{BASE_URL}/peng", params=params)
                
                if response.status_code == 200:
                    result = response.json()
                    if result["success"]:
                        # 从我的具体手牌中移除2张
                        for _ in range(2):
                            if (tile_type, tile_value) in self.my_hand:
                                self.my_hand.remove((tile_type, tile_value))
                        self.player_hand_counts[player_id] -= 2
                        
                        # 记录明牌
                        self.all_melds[player_id].append({
                            "type": "peng",
                            "tile": (tile_type, tile_value),
                            "source": source_player_id
                        })
                        
                        source_info = f" (来自{self.player_names[source_player_id]})"
                        self.log(f"✅ {self.player_names[player_id]}碰牌 {tile_value}{self.suit_names[tile_type]}{source_info} {description}")
                        return True
                    else:
                        self.log(f"❌ 碰牌失败: {result['message']}")
                        return False
                else:
                    self.log(f"❌ 碰牌请求失败: {response.text}")
                    return False
            else:
                # 其他玩家碰牌：需要同步手牌数量到后端
                self.player_hand_counts[player_id] -= 2
                
                # 同步到后端：减少手牌数量
                params = {
                    "player_id": player_id,
                    "count": -2  # 减少2张手牌
                }
                response = requests.post(f"{BASE_URL}/add-hand-count", params=params)
                
                if response.status_code == 200:
                    result = response.json()
                    if result["success"]:
                        # 记录明牌
                        self.all_melds[player_id].append({
                            "type": "peng",
                            "tile": (tile_type, tile_value),
                            "source": source_player_id
                        })
                        
                        source_info = f" (来自{self.player_names[source_player_id]})"
                        hand_info = f" (手牌:{self.player_hand_counts[player_id]}张)"
                        self.log(f"✅ {self.player_names[player_id]}碰牌 {tile_value}{self.suit_names[tile_type]}{source_info} {description}{hand_info}")
                        return True
                    else:
                        # API失败，回滚本地状态
                        self.player_hand_counts[player_id] += 2
                        self.log(f"❌ 同步碰牌手牌数量失败: {result['message']}")
                        return False
                else:
                    # API失败，回滚本地状态
                    self.player_hand_counts[player_id] += 2
                    self.log(f"❌ 同步碰牌手牌数量请求失败: {response.text}")
                    return False
                
        except Exception as e:
            self.log(f"❌ 碰牌错误: {e}")
            return False

    def gang_tile(self, player_id, tile_type, tile_value, gang_type, source_player_id=None, description=""):
        """杠牌"""
        try:
            if player_id == self.my_player_id:
                # 我的杠牌：需要调用API
                params = {
                    "player_id": player_id,
                    "tile_type": tile_type,
                    "tile_value": tile_value,
                    "gang_type": gang_type
                }
                if source_player_id is not None:
                    params["source_player_id"] = source_player_id
                    
                response = requests.post(f"{BASE_URL}/gang", params=params)
                
                if response.status_code == 200:
                    result = response.json()
                    if result["success"]:
                        # 从我的具体手牌中移除相应数量的牌
                        if gang_type == "angang":
                            # 暗杠：移除4张
                            for _ in range(4):
                                if (tile_type, tile_value) in self.my_hand:
                                    self.my_hand.remove((tile_type, tile_value))
                            self.player_hand_counts[player_id] -= 4
                        elif gang_type == "zhigang":
                            # 直杠：移除3张（手中的）
                            for _ in range(3):
                                if (tile_type, tile_value) in self.my_hand:
                                    self.my_hand.remove((tile_type, tile_value))
                            self.player_hand_counts[player_id] -= 3
                        elif gang_type == "jiagang":
                            # 加杠：移除1张（碰牌已经移除了2张，现在移除第4张）
                            if (tile_type, tile_value) in self.my_hand:
                                self.my_hand.remove((tile_type, tile_value))
                            self.player_hand_counts[player_id] -= 1
                        
                        # 记录明牌
                        self.all_melds[player_id].append({
                            "type": gang_type,
                            "tile": (tile_type, tile_value),
                            "source": source_player_id
                        })
                        
                        gang_name = self.gang_type_names.get(gang_type, gang_type)
                        source_info = f" (来自{self.player_names[source_player_id]})" if source_player_id is not None else ""
                        self.log(f"✅ {self.player_names[player_id]}{gang_name} {tile_value}{self.suit_names[tile_type]}{source_info} {description}")
                        return True
                    else:
                        self.log(f"❌ 杠牌失败: {result['message']}")
                        return False
                else:
                    self.log(f"❌ 杠牌请求失败: {response.text}")
                    return False
            else:
                # 其他玩家杠牌：需要同步手牌数量到后端
                if gang_type == "angang":
                    hand_reduction = 4
                elif gang_type == "zhigang":
                    hand_reduction = 3
                elif gang_type == "jiagang":
                    hand_reduction = 1
                else:
                    hand_reduction = 4
                
                self.player_hand_counts[player_id] -= hand_reduction
                
                # 同步到后端：减少手牌数量
                params = {
                    "player_id": player_id,
                    "count": -hand_reduction
                }
                response = requests.post(f"{BASE_URL}/add-hand-count", params=params)
                
                if response.status_code == 200:
                    result = response.json()
                    if result["success"]:
                        # 记录明牌
                        self.all_melds[player_id].append({
                            "type": gang_type,
                            "tile": (tile_type, tile_value),
                            "source": source_player_id
                        })
                        
                        gang_name = self.gang_type_names.get(gang_type, gang_type)
                        source_info = f" (来自{self.player_names[source_player_id]})" if source_player_id is not None else ""
                        hand_info = f" (手牌:{self.player_hand_counts[player_id]}张)"
                        self.log(f"✅ {self.player_names[player_id]}{gang_name} {tile_value}{self.suit_names[tile_type]}{source_info} {description}{hand_info}")
                        return True
                    else:
                        # API失败，回滚本地状态
                        self.player_hand_counts[player_id] += hand_reduction
                        self.log(f"❌ 同步杠牌手牌数量失败: {result['message']}")
                        return False
                else:
                    # API失败，回滚本地状态
                    self.player_hand_counts[player_id] += hand_reduction
                    self.log(f"❌ 同步杠牌手牌数量请求失败: {response.text}")
                    return False
                
        except Exception as e:
            self.log(f"❌ 杠牌错误: {e}")
            return False

    def bu_pai(self, player_id, tile_type, tile_value, description="杠后补牌"):
        """补牌（杠后从牌尾补一张）"""
        return self.add_hand_tile(player_id, tile_type, tile_value, f"({description})")

    def zi_mo(self, player_id, win_tile=None, description="自摸胡牌"):
        """自摸胡牌"""
        try:
            # 调用API通知前端自摸胡牌
            params = {
                "player_id": player_id,
                "win_type": "zimo"
            }
            if win_tile:
                params["win_tile_type"] = win_tile[0]
                params["win_tile_value"] = win_tile[1]
                
            response = requests.post(f"{BASE_URL}/player-win", params=params)
            
            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    self.win_players.add(player_id)
                    
                    win_tile_str = ""
                    if win_tile:
                        win_tile_str = f" {win_tile[1]}{self.suit_names[win_tile[0]]}"
                    
                    self.log(f"🎉🎉🎉 {self.player_names[player_id]}{description}{win_tile_str}！🎉🎉🎉")
                    self.log(f"🏆 前端已显示胜利标识！")
                    
                    # 记录游戏事件
                    self.log_game_event("zimo", player_id, {
                        "win_tile": win_tile,
                        "description": description
                    })
                    
                    return True
                else:
                    self.log(f"❌ 自摸胡牌API失败: {result['message']}")
                    return False
            else:
                self.log(f"❌ 自摸胡牌请求失败: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ 自摸胡牌错误: {e}")
            return False

    def dian_pao(self, winner_id, dianpao_player_id, tile_type, tile_value, description="点炮胡牌"):
        """点炮胡牌"""
        try:
            # 调用API通知前端点炮胡牌
            params = {
                "player_id": winner_id,
                "win_type": "dianpao",
                "win_tile_type": tile_type,
                "win_tile_value": tile_value,
                "dianpao_player_id": dianpao_player_id
            }
            
            response = requests.post(f"{BASE_URL}/player-win", params=params)
            
            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    self.win_players.add(winner_id)
                    
                    win_tile_str = f"{tile_value}{self.suit_names[tile_type]}"
                    self.log(f"🎉🎉🎉 {self.player_names[winner_id]}胡牌 {win_tile_str} (点炮者: {self.player_names[dianpao_player_id]}) {description}！🎉🎉🎉")
                    self.log(f"🏆 前端已显示胜利标识！")
                    
                    # 记录游戏事件
                    self.log_game_event("dianpao", winner_id, {
                        "win_tile": (tile_type, tile_value),
                        "dianpao_player": dianpao_player_id,
                        "description": description
                    })
                    
                    return True
                else:
                    self.log(f"❌ 点炮胡牌API失败: {result['message']}")
                    return False
            else:
                self.log(f"❌ 点炮胡牌请求失败: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ 点炮胡牌错误: {e}")
            return False

    def reveal_all_hands(self):
        """牌局结束后显示所有玩家手牌"""
        try:
            self.log("\n🀫 牌局结束，显示所有玩家手牌...")
            
            # 调用API显示所有手牌
            response = requests.post(f"{BASE_URL}/reveal-all-hands")
            
            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    self.log("✅ 前端已显示所有玩家手牌")
                    
                    # 显示我的具体手牌
                    self.log(f"🀫 我的最终手牌: {self.format_cards(self.my_hand)}")
                    
                    # 显示其他玩家手牌数量（真实情况下我们看不到具体牌）
                    for player_id in range(1, 4):
                        if player_id not in self.win_players:
                            self.log(f"🀫 {self.player_names[player_id]}的手牌数量: {self.player_hand_counts[player_id]}张")
                    
                    return True
                else:
                    self.log(f"❌ 显示所有手牌API失败: {result['message']}")
                    return False
            else:
                self.log(f"❌ 显示所有手牌请求失败: {response.text}")
                return False
                
        except Exception as e:
            self.log(f"❌ 显示所有手牌错误: {e}")
            return False

    def set_current_player(self, player_id):
        """设置当前玩家（用于前端高亮边框）"""
        try:
            params = {
                "player_id": player_id
            }
            response = requests.post(f"{BASE_URL}/set-current-player", params=params)
            
            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    self.log(f"🎯 当前玩家设置为: {self.player_names[player_id]} (边框高亮)")
                    return True
                else:
                    self.log(f"❌ 设置当前玩家失败: {result['message']}")
                    return False
            else:
                self.log(f"❌ 设置当前玩家请求失败: {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ 设置当前玩家错误: {e}")
            return False

    def next_player(self):
        """切换到下一个玩家"""
        try:
            response = requests.post(f"{BASE_URL}/next-player")
            
            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    previous_name = self.player_names.get(result.get("previous_player", 0), "未知")
                    current_name = self.player_names.get(result.get("current_player", 0), "未知")
                    self.log(f"🔄 玩家切换: {previous_name} → {current_name} (边框高亮)")
                    return True
                else:
                    self.log(f"❌ 切换玩家失败: {result['message']}")
                    return False
            else:
                self.log(f"❌ 切换玩家请求失败: {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ 切换玩家错误: {e}")
            return False

    def load_real_game_scenario(self):
        """加载真实牌局场景"""
        self.log("🎯 开始加载真实血战到底牌局场景...")
        
        # 我的真实起手牌（庄家14张）- 这是我们知道的唯一具体手牌
        my_hand = [
            # 万子：1万x2，2万x2，3万x2，4万x1，7万x1，8万x1
            ("wan", 1), ("wan", 1),
            ("wan", 2), ("wan", 2), 
            ("wan", 3), ("wan", 3),
            ("wan", 4), ("wan", 7), ("wan", 8),
            # 筒子：5筒x4（用于暗杠），9筒x1
            ("tong", 5), ("tong", 5), ("tong", 5), ("tong", 5),
            ("tong", 9)
        ]
        
        # 其他玩家的手牌数量（我们不知道具体牌，只知道数量）
        other_players_counts = {
            1: 13,  # 下家13张
            2: 13,  # 对家13张
            3: 13   # 上家13张
        }
        
        # 验证我的手牌数量
        if len(my_hand) != 14:
            self.log(f"❌ 我的手牌数量错误：期望14张，实际{len(my_hand)}张")
            return False
        
        # 给我分配具体手牌
        self.log(f"🀫 给我分配真实手牌...")
        self.log(f"   我的手牌: {self.format_cards(my_hand)}")
        
        for i, (suit, value) in enumerate(my_hand, 1):
            if not self.add_hand_tile(self.my_player_id, suit, value, f"(发牌 {i}/{len(my_hand)})"):
                return False
            time.sleep(0.02)
        
        # 给其他玩家分配手牌数量（不需要具体牌）
        for player_id, count in other_players_counts.items():
            player_name = self.player_names[player_id]
            self.log(f"🀫 给{player_name}分配{count}张手牌...")
            
            for i in range(count):
                if not self.add_hand_tile(player_id, "wan", 1, f"(发牌 {i+1}/{count})"):
                    return False
                time.sleep(0.01)  # 更快的发牌速度，因为不需要具体牌
        
        self.log("✅ 真实牌局场景加载完成")
        self.log(f"📊 手牌分配情况:")
        for player_id in range(4):
            count = self.player_hand_counts[player_id]
            self.log(f"   {self.player_names[player_id]}: {count}张")
        
        return True

    def simulate_real_game_flow(self):
        """模拟真实的血战到底游戏流程"""
        self.log("\n=== 🎲 开始血战到底真实牌局模拟 ===")
        
        # 真实游戏流程
        game_actions = [
            # 第1轮：我首打 - 关键决策点1
            {
                "round": 1,
                "action": "my_discard",
                "player": 0,
                "tile": ("tong", 9),
                "desc": "我首打9筒",
                "situation": "起手首打选择"
            },
            
            # 第2轮：下家摸牌弃牌
            {
                "round": 2,
                "action": "draw_and_discard",
                "player": 1,
                "draw_tile": ("tiao", 5),
                "discard_tile": ("tong", 8),
                "desc": "下家摸牌弃8筒"
            },
            
            # 第3轮：对家摸牌弃牌
            {
                "round": 3,
                "action": "draw_and_discard", 
                "player": 2,
                "draw_tile": ("wan", 3),
                "discard_tile": ("tong", 4),
                "desc": "对家摸牌弃4筒"
            },
            
            # 第4轮：上家摸牌弃牌
            {
                "round": 4,
                "action": "draw_and_discard",
                "player": 3,
                "draw_tile": ("tiao", 9),
                "discard_tile": ("tong", 9),
                "desc": "上家摸牌弃9筒"
            },
            
            # 第5轮：我摸牌 - 关键决策点2
            {
                "round": 5,
                "action": "my_draw_discard",
                "player": 0,
                "draw_tile": ("wan", 5),
                "discard_tile": ("wan", 8),
                "desc": "我摸5万弃8万",
                "situation": "摸牌后弃牌选择"
            },
            
            # 第6轮：下家摸牌弃2万，我可以碰
            {
                "round": 6,
                "action": "draw_and_discard",
                "player": 1,
                "draw_tile": ("tong", 6),
                "discard_tile": ("wan", 2),
                "desc": "下家摸牌弃2万"
            },
            
            # 第7轮：我碰2万
            {
                "round": 7,
                "action": "peng",
                "player": 0,
                "tile": ("wan", 2),
                "source": 1,
                "desc": "我碰2万"
            },
            
            # 第8轮：我碰后弃牌 - 关键决策点3
            {
                "round": 8,
                "action": "my_discard",
                "player": 0,
                "tile": ("wan", 7),
                "desc": "碰后弃7万",
                "situation": "碰牌后弃牌选择"
            },
            
            # 第9轮：下家摸牌弃牌（轮到下家）
            {
                "round": 9,
                "action": "draw_and_discard",
                "player": 1,
                "draw_tile": ("tiao", 4),
                "discard_tile": ("tong", 2),
                "desc": "下家摸牌弃2筒"
            },
            
            # 第10轮：对家摸牌弃牌
            {
                "round": 10,
                "action": "draw_and_discard",
                "player": 2,
                "draw_tile": ("wan", 6),
                "discard_tile": ("tiao", 8),
                "desc": "对家摸牌弃8条"
            },
            
            # 第11轮：上家摸牌弃牌
            {
                "round": 11,
                "action": "draw_and_discard",
                "player": 3,
                "draw_tile": ("tong", 7),
                "discard_tile": ("wan", 5),
                "desc": "上家摸牌弃5万"
            },
            
            # 第12轮：我暗杠5筒（轮回到我，暗杠）
            {
                "round": 12,
                "action": "angang",
                "player": 0,
                "tile": ("tong", 5),
                "desc": "我暗杠5筒（下雨）"
            },
            
            # 第13轮：我杠后补牌弃牌 - 关键决策点4
            {
                "round": 13,
                "action": "my_bugang_discard",
                "player": 0,
                "bu_tile": ("tiao", 1),
                "discard_tile": ("tiao", 1),
                "desc": "杠后补1条，定缺必打",
                "situation": "杠后补牌弃牌"
            },
            
            # 第14轮：下家摸牌弃牌
            {
                "round": 14,
                "action": "draw_and_discard",
                "player": 1,
                "draw_tile": ("wan", 7),
                "discard_tile": ("tong", 3),
                "desc": "下家摸牌弃3筒"
            },
            
            # 第15轮：对家摸牌弃牌
            {
                "round": 15,
                "action": "draw_and_discard",
                "player": 2,
                "draw_tile": ("tiao", 6),
                "discard_tile": ("wan", 8),
                "desc": "对家摸牌弃8万"
            },
            
            # 第16轮：上家摸牌自摸胡牌（上家定缺万，只能胡筒条）
            {
                "round": 16,
                "action": "zimo",
                "player": 3,
                "win_tile": ("tong", 6),
                "desc": "上家自摸6筒胡牌！第一家胡牌"
            },
            
            # 第17轮：我摸牌弃牌（血战继续，上家已胡）
            {
                "round": 17,
                "action": "my_draw_discard",
                "player": 0,
                "draw_tile": ("wan", 9),
                "discard_tile": ("wan", 9),
                "desc": "血战继续，我摸9万弃9万",
                "situation": "血战继续中弃牌"
            },
            
            # 第18轮：下家摸牌自摸胡牌（下家定缺筒，只能胡万条）
            {
                "round": 18,
                "action": "zimo",
                "player": 1,
                "win_tile": ("wan", 7),
                "desc": "下家自摸7万胡牌！第二家胡牌"
            },
            
            # 第19轮：对家摸牌弃牌（血战继续）
            {
                "round": 19,
                "action": "draw_and_discard",
                "player": 2,
                "draw_tile": ("tong", 1),
                "discard_tile": ("tiao", 7),
                "desc": "对家摸牌弃7条"
            },
            
            # 第20轮：我摸牌自摸胡牌（我定缺条，只能胡万筒）
            {
                "round": 20,
                "action": "my_zimo",
                "player": 0,
                "win_tile": ("wan", 1),
                "desc": "我自摸1万胡牌！三家胡牌，血战结束"
            }
        ]
        
        # 执行游戏流程
        for action in game_actions:
            self.current_round = action["round"]
            self.log(f"\n🔹 第{action['round']}轮：{action['desc']}")
            
            # 执行具体动作
            if not self._execute_action(action):
                return False
                
            self.wait_for_user(f"第{action['round']}轮完成，按回车键继续...")
        
        # 游戏结束 - 显示所有玩家手牌
        self.reveal_all_hands()
        
        # 显示最终总结
        self._show_final_summary()
        return True
    
    def _execute_action(self, action: Dict) -> bool:
        """执行游戏动作"""
        action_type = action["action"]
        
        if action_type == "my_discard":
            # 我的弃牌（需要分析）
            if not self.set_current_player(action["player"]):
                return False
            time.sleep(0.5)
            return self.discard_tile(
                action["player"], 
                action["tile"][0], 
                action["tile"][1], 
                action["desc"], 
                analyze=True
            )
            
        elif action_type == "draw_and_discard":
            # 其他玩家摸牌弃牌
            player = action["player"]
            if not self.set_current_player(player):
                return False
            time.sleep(0.5)
            
            # 摸牌
            if not self.add_hand_tile(player, action["draw_tile"][0], action["draw_tile"][1], "摸牌"):
                return False
            
            # 弃牌
            return self.discard_tile(player, action["discard_tile"][0], action["discard_tile"][1], "弃牌")
            
        elif action_type == "my_draw_discard":
            # 我摸牌后弃牌（需要分析）
            player = action["player"]
            if not self.set_current_player(player):
                return False
            time.sleep(0.5)
            
            # 摸牌
            if not self.add_hand_tile(player, action["draw_tile"][0], action["draw_tile"][1], "摸牌"):
                return False
            
            # 弃牌（分析）
            return self.discard_tile(
                player, 
                action["discard_tile"][0], 
                action["discard_tile"][1], 
                action["desc"], 
                analyze=True
            )
            
        elif action_type == "peng":
            # 碰牌
            if not self.set_current_player(action["player"]):
                return False
            time.sleep(0.5)
            return self.peng_tile(
                action["player"], 
                action["tile"][0], 
                action["tile"][1], 
                action["source"], 
                action["desc"]
            )
            
        elif action_type == "angang":
            # 暗杠
            if not self.set_current_player(action["player"]):
                return False
            time.sleep(0.5)
            return self.gang_tile(
                action["player"], 
                action["tile"][0], 
                action["tile"][1], 
                "angang", 
                None, 
                action["desc"]
            )
            
        elif action_type == "my_bugang_discard":
            # 我杠后补牌弃牌
            player = action["player"]
            
            # 补牌
            if not self.bu_pai(player, action["bu_tile"][0], action["bu_tile"][1], "杠后补牌"):
                return False
            
            # 弃牌（分析）
            return self.discard_tile(
                player, 
                action["discard_tile"][0], 
                action["discard_tile"][1], 
                action["desc"], 
                analyze=True
            )
            
        elif action_type in ["zimo", "my_zimo"]:
            # 自摸胡牌
            win_tile = action.get("win_tile")
            return self.zi_mo(action["player"], win_tile, action["desc"])
            
        elif action_type == "dianpao":
            # 点炮胡牌
            return self.dian_pao(
                action["winner"], 
                action["dianpao_player"], 
                action["tile"][0], 
                action["tile"][1], 
                action["desc"]
            )
            
        elif action_type in ["normal_turns", "continue_battle"]:
            # 模拟多轮正常游戏
            self.log("   (模拟其他玩家正常摸打...)")
            return True
            
        return True
    
    def _show_final_summary(self):
        """显示最终总结"""
        self.log("\n" + "="*80)
        self.log("🏆 血战到底牌局结束！")
        
        # 显示详细胜利信息
        if len(self.win_players) >= 2:
            self.log("\n🎉 胜利玩家详情:")
            for event in self.game_events:
                if event["type"] in ["zimo", "dianpao"]:
                    player_name = event["player_name"]
                    if event["type"] == "zimo":
                        win_tile = event["details"].get("win_tile")
                        if win_tile:
                            win_tile_str = f"{win_tile[1]}{self.suit_names[win_tile[0]]}"
                            self.log(f"   🏆 {player_name}: 自摸胡牌 {win_tile_str}")
                        else:
                            self.log(f"   🏆 {player_name}: 自摸胡牌")
                    elif event["type"] == "dianpao":
                        win_tile = event["details"].get("win_tile")
                        dianpao_player = event["details"].get("dianpao_player")
                        win_tile_str = f"{win_tile[1]}{self.suit_names[win_tile[0]]}"
                        dianpao_name = self.player_names.get(dianpao_player, f"玩家{dianpao_player}")
                        self.log(f"   🏆 {player_name}: 点炮胡牌 {win_tile_str} (点炮者: {dianpao_name})")
        
        # 显示最终手牌情况
        self.log(f"\n🀫 最终手牌情况:")
        self.log(f"   我的手牌: {self.format_cards(self.my_hand)} ({len(self.my_hand)}张)")
        for player_id in range(1, 4):
            if player_id not in self.win_players:
                self.log(f"   {self.player_names[player_id]}: {self.player_hand_counts[player_id]}张手牌")
            else:
                self.log(f"   {self.player_names[player_id]}: 已胡牌")
        
        # 决策分析总结
        total_decisions = len(self.decision_points)
        correct_decisions = sum(1 for d in self.decision_points if d["is_optimal"])
        
        if total_decisions > 0:
            accuracy = correct_decisions / total_decisions * 100
            self.log(f"\n📊 我的决策分析总结:")
            self.log(f"   总决策点: {total_decisions}")
            self.log(f"   正确决策: {correct_decisions}")
            self.log(f"   决策准确率: {accuracy:.1f}%")
            
            if accuracy >= 80:
                self.log("   💪 评价: 决策水平优秀！")
            elif accuracy >= 60:
                self.log("   👍 评价: 决策水平良好")
            else:
                self.log("   📚 评价: 还有提升空间")
        
        # 牌库完整性验证
        self.log(f"\n📈 最终牌库状态: {self.get_deck_status()}")
        self.validate_deck_integrity()
        
        self.log("="*80)

    def export_analysis_report(self):
        """导出分析报告"""
        self.log("\n=== 📁 导出牌局分析报告 ===")
        try:
            response = requests.get(f"{BASE_URL}/export-game-record")
            
            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    # 创建完整的分析报告
                    analysis_report = {
                        "game_info": {
                            "timestamp": timestamp,
                            "mode": "腾讯欢乐麻将血战到底",
                            "players": self.player_names,
                            "total_rounds": self.current_round
                        },
                        "game_record": result["data"],
                        "my_decision_analysis": {
                            "total_decisions": len(self.decision_points),
                            "correct_decisions": sum(1 for d in self.decision_points if d["is_optimal"]),
                            "accuracy": (sum(1 for d in self.decision_points if d["is_optimal"]) / len(self.decision_points) * 100) if self.decision_points else 0,
                            "decision_details": self.decision_points
                        },
                        "deck_integrity": {
                            "final_deck_size": len(self.deck),
                            "used_tiles_count": sum(self.used_tiles.values()),
                            "total_tiles": len(self.deck) + sum(self.used_tiles.values())
                        },
                        "win_statistics": {
                            "winners": list(self.win_players),
                            "winner_names": [self.player_names[p] for p in self.win_players]
                        }
                    }
                    
                    filename = f"xuezhan_analysis_{timestamp}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(analysis_report, f, ensure_ascii=False, indent=2)
                    
                    self.log(f"✅ 牌局分析报告导出成功: {filename}")
                    self.log(f"📊 报告统计:")
                    self.log(f"   🎮 游戏模式: 血战到底真实牌局模拟")
                    self.log(f"   👥 玩家数量: 4人")
                    self.log(f"   📈 总轮数: {self.current_round}轮")
                    self.log(f"   🤔 我的决策点: {len(self.decision_points)}个")
                    
                    if self.decision_points:
                        accuracy = analysis_report["my_decision_analysis"]["accuracy"]
                        self.log(f"   🎯 决策准确率: {accuracy:.1f}%")
                    
                    return filename
                else:
                    self.log(f"❌ 导出报告失败: {result['message']}")
                    return None
            else:
                self.log(f"❌ 导出报告请求失败: {response.text}")
                return None
        except Exception as e:
            self.log(f"❌ 导出报告错误: {e}")
            return None


def main():
    """主函数 - 运行血战到底真实牌局分析工具"""
    simulator = RealGameSimulator()
    
    print("🀄 腾讯欢乐麻将血战到底辅助分析工具 🀄")
    print("=" * 80)
    print("📋 本工具功能：")
    print("   🎯 重现真实牌局，分析决策点")
    print("   🎯 评估弃牌选择的优劣")
    print("   🎯 提供改进建议和策略分析")
    print("   🎯 导出详细的分析报告")
    print("   🎯 支持完整的血战到底流程")
    print("=" * 80)
    
    # 1. 测试API连接
    if not simulator.test_api_connection():
        return
    
    # 2. 重置游戏状态
    if not simulator.reset_game():
        return
    
    # 验证初始牌库完整性
    simulator.validate_deck_integrity()
    
    # 3. 设置游戏初始状态
    simulator.log("\n=== 🎯 血战到底真实牌局开始 ===")
    
    # 定庄：我为庄家
    simulator.log("🔸 定庄：我为庄家（东风位）")
    simulator.wait_for_user("准备开始游戏，按回车键继续...")
    
    # 所有玩家定缺
    simulator.log("\n🔸 第一步：所有玩家定缺")
    missing_suits = {
        0: "tiao",  # 我定缺条
        1: "tong",  # 下家定缺筒  
        2: "wan",   # 对家定缺万
        3: "wan"    # 上家定缺万
    }
    
    for player_id, missing_suit in missing_suits.items():
        if not simulator.set_missing_suit(player_id, missing_suit):
            return
        time.sleep(0.1)
    
    simulator.wait_for_user("定缺完成，按回车键开始发牌...")
    
    # 4. 加载真实牌局场景
    simulator.log("\n🔸 第二步：加载真实牌局场景")
    
    if not simulator.load_real_game_scenario():
        return
    
    # 发牌后验证牌库完整性
    simulator.log(f"📊 发牌后状态: {simulator.get_deck_status()}")
    simulator.validate_deck_integrity()
    
    simulator.wait_for_user("真实牌局场景加载完成，按回车键开始游戏流程...")
    
    # 5. 执行真实游戏流程
    if not simulator.simulate_real_game_flow():
        return
    
    # 6. 导出分析报告
    filename = simulator.export_analysis_report()
    
    print("\n" + "=" * 80)
    print("🎉 血战到底牌局分析完成！")
    print("💡 分析工具展示了：")
    print("   ✅ 真实牌局场景重现")
    print("   ✅ 关键决策点智能分析")
    print("   ✅ 弃牌选择优劣评估")
    print("   ✅ 决策准确率统计")
    print("   ✅ 完整的牌库完整性验证")
    print("   ✅ 详细的分析报告导出")
    
    if filename:
        print(f"📁 分析报告: {filename}")
    
    print("\n💻 相关链接：")
    print("🌐 前端界面: http://localhost:3000")
    print("📊 API文档: http://localhost:8000/docs")
    print("=" * 80)


if __name__ == "__main__":
    main() 