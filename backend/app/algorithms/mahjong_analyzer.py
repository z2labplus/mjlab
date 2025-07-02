import random
from typing import List, Dict, Tuple, Set
from collections import Counter, defaultdict
import itertools

from ..models.mahjong import Tile, GameState, AnalysisResult, TileType, Meld, MeldType


class MahjongAnalyzer:
    """麻将分析器"""
    
    def __init__(self):
        self.simulation_count = 1000  # 蒙特卡洛模拟次数
    
    def analyze_game_state(self, game_state: GameState, player_id: int) -> AnalysisResult:
        """分析游戏状态并给出建议"""
        if player_id not in game_state.player_hands:
            return AnalysisResult(message="玩家不存在")
        
        hand = game_state.player_hands[player_id]
        remaining_tiles = game_state.calculate_remaining_tiles()
        
        # 检测听牌
        listen_tiles = self.detect_listen_tiles(hand.tiles)
        
        # 计算每张牌的弃牌分数
        discard_scores = self.calculate_discard_scores(hand.tiles, remaining_tiles, listen_tiles)
        
        # 推荐弃牌
        recommended_discard = self.get_recommended_discard(hand.tiles, discard_scores)
        
        # 计算胡牌概率
        win_probability = self.calculate_win_probability(hand.tiles, remaining_tiles, listen_tiles)
        
        # 生成建议
        suggestions = self.generate_suggestions(hand.tiles, listen_tiles, discard_scores)
        
        return AnalysisResult(
            recommended_discard=recommended_discard,
            discard_scores=discard_scores,
            listen_tiles=listen_tiles,
            win_probability=win_probability,
            remaining_tiles_count=remaining_tiles,
            suggestions=suggestions
        )
    
    def detect_listen_tiles(self, tiles: List[Tile]) -> List[Tile]:
        """检测听牌"""
        listen_tiles = []
        
        # 检查每种可能的牌，看是否能组成胡牌
        for tile_type in TileType:
            max_value = 7 if tile_type == TileType.ZI else 9
            for value in range(1, max_value + 1):
                test_tile = Tile(type=tile_type, value=value)
                test_hand = tiles + [test_tile]
                
                if self.is_winning_hand(test_hand):
                    listen_tiles.append(test_tile)
        
        return listen_tiles
    
    def is_winning_hand(self, tiles: List[Tile]) -> bool:
        """判断是否为胡牌"""
        if len(tiles) % 3 != 2:
            return False
        
        # 转换为数字编码进行计算
        tile_codes = [tile.to_code() for tile in tiles]
        tile_count = Counter(tile_codes)
        
        return self._can_form_winning_combination(tile_count)
    
    def _can_form_winning_combination(self, tile_count: Counter) -> bool:
        """递归检查是否能组成胡牌组合"""
        # 基础情况：没有牌了
        if not tile_count:
            return True
        
        # 尝试找到一对
        for tile_code, count in tile_count.items():
            if count >= 2:
                # 移除一对
                new_count = tile_count.copy()
                new_count[tile_code] -= 2
                if new_count[tile_code] == 0:
                    del new_count[tile_code]
                
                # 检查剩余的牌是否都能组成刻子或顺子
                if self._can_form_melds_only(new_count):
                    return True
        
        return False
    
    def _can_form_melds_only(self, tile_count: Counter) -> bool:
        """检查是否所有牌都能组成刻子或顺子"""
        if not tile_count:
            return True
        
        # 取第一张牌
        tile_code = min(tile_count.keys())
        count = tile_count[tile_code]
        
        # 尝试组成刻子
        if count >= 3:
            new_count = tile_count.copy()
            new_count[tile_code] -= 3
            if new_count[tile_code] == 0:
                del new_count[tile_code]
            
            if self._can_form_melds_only(new_count):
                return True
        
        # 尝试组成顺子（只对万、条、筒有效）
        if self._can_form_sequence(tile_code):
            if (tile_code + 1 in tile_count and 
                tile_code + 2 in tile_count and
                tile_count[tile_code + 1] > 0 and 
                tile_count[tile_code + 2] > 0):
                
                new_count = tile_count.copy()
                new_count[tile_code] -= 1
                new_count[tile_code + 1] -= 1
                new_count[tile_code + 2] -= 1
                
                for code in [tile_code, tile_code + 1, tile_code + 2]:
                    if new_count[code] == 0:
                        del new_count[code]
                
                if self._can_form_melds_only(new_count):
                    return True
        
        return False
    
    def _can_form_sequence(self, tile_code: int) -> bool:
        """检查是否可以组成顺子"""
        # 字牌不能组成顺子
        if 31 <= tile_code <= 37:
            return False
        
        # 检查是否是7、8、9，不能组成顺子
        if tile_code % 10 >= 8:
            return False
        
        return True
    
    def calculate_discard_scores(self, tiles: List[Tile], remaining_tiles: Dict[int, int], 
                               listen_tiles: List[Tile]) -> Dict[str, float]:
        """计算弃牌分数"""
        scores = {}
        
        for tile in tiles:
            score = 0.0
            
            # 基础分数：考虑牌的稀有度
            tile_code = tile.to_code()
            remaining_count = remaining_tiles.get(tile_code, 0)
            
            # 剩余牌越少，弃牌分数越高（越应该留着）
            if remaining_count == 0:
                score -= 10.0  # 绝张，不应该弃
            elif remaining_count == 1:
                score -= 5.0   # 只剩一张，比较珍贵
            elif remaining_count == 2:
                score -= 2.0   # 剩两张，有一定价值
            
            # 听牌相关分数
            if tile in listen_tiles:
                score -= 20.0  # 听牌不应该弃
            
            # 组合潜力分数
            combination_score = self._calculate_combination_potential(tile, tiles, remaining_tiles)
            score -= combination_score
            
            scores[str(tile)] = score
        
        return scores
    
    def _calculate_combination_potential(self, target_tile: Tile, hand_tiles: List[Tile], 
                                       remaining_tiles: Dict[int, int]) -> float:
        """计算牌的组合潜力"""
        score = 0.0
        tile_code = target_tile.to_code()
        
        # 计算与其他牌的组合可能性
        hand_counter = Counter([tile.to_code() for tile in hand_tiles])
        
        # 刻子潜力
        if hand_counter[tile_code] >= 2:
            score += 5.0  # 已有对子，有刻子潜力
        elif hand_counter[tile_code] >= 1 and remaining_tiles.get(tile_code, 0) >= 2:
            score += 2.0  # 有做刻子的可能
        
        # 顺子潜力
        if self._can_form_sequence(tile_code):
            for offset in [-2, -1, 1, 2]:
                adjacent_code = tile_code + offset
                if (hand_counter.get(adjacent_code, 0) > 0 and 
                    remaining_tiles.get(adjacent_code, 0) > 0):
                    score += 1.0
        
        return score
    
    def get_recommended_discard(self, tiles: List[Tile], scores: Dict[str, float]) -> Tile:
        """获取推荐弃牌"""
        if not scores:
            return tiles[0] if tiles else None
        
        # 选择分数最高的牌（最应该弃的牌）
        best_tile_str = max(scores.keys(), key=lambda x: scores[x])
        
        # 找到对应的牌对象
        for tile in tiles:
            if str(tile) == best_tile_str:
                return tile
        
        return tiles[0] if tiles else None
    
    def calculate_win_probability(self, tiles: List[Tile], remaining_tiles: Dict[int, int], 
                                listen_tiles: List[Tile]) -> float:
        """计算胡牌概率"""
        if not listen_tiles:
            return 0.0
        
        # 计算听牌的总数量
        total_listen_count = 0
        for listen_tile in listen_tiles:
            code = listen_tile.to_code()
            total_listen_count += remaining_tiles.get(code, 0)
        
        # 计算剩余总牌数
        total_remaining = sum(remaining_tiles.values())
        
        if total_remaining == 0:
            return 0.0
        
        # 简单概率计算
        probability = total_listen_count / total_remaining
        
        return min(probability, 1.0)
    
    def generate_suggestions(self, tiles: List[Tile], listen_tiles: List[Tile], 
                           scores: Dict[str, float]) -> List[str]:
        """生成建议"""
        suggestions = []
        
        if listen_tiles:
            suggestions.append(f"当前听牌：{', '.join(str(tile) for tile in listen_tiles)}")
        else:
            suggestions.append("当前未听牌，建议整理牌型")
        
        # 分析牌型结构
        tile_counter = Counter([tile.to_code() for tile in tiles])
        
        # 检查对子
        pairs = [code for code, count in tile_counter.items() if count == 2]
        if pairs:
            suggestions.append(f"当前有对子：{len(pairs)}个")
        
        # 检查刻子
        triplets = [code for code, count in tile_counter.items() if count >= 3]
        if triplets:
            suggestions.append(f"当前有刻子：{len(triplets)}个")
        
        # 弃牌建议
        if scores:
            best_discard = max(scores.keys(), key=lambda x: scores[x])
            suggestions.append(f"建议弃牌：{best_discard}")
        
        return suggestions 