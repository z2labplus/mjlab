#!/usr/bin/env python3
"""
SichuanMahjongKit Hand Analyzer
血战到底麻将库手牌分析器
"""

from typing import List, Dict, Any, Tuple, Optional, Set
from collections import Counter, defaultdict
import copy

try:
    from .core import Tile, TilesConverter, SuitType, PlayerState, Meld, MeldType
    from .fixed_validator import WinValidator, TingValidator
except ImportError:
    from core import Tile, TilesConverter, SuitType, PlayerState, Meld, MeldType
    from fixed_validator import WinValidator, TingValidator

# 临时使用简化算法直到修复validator
class SimpleShantenCalc:
    @staticmethod
    def calculate_shanten(tiles):
        """简化的向听数计算 - 临时解决方案"""
        tiles_array = TilesConverter.tiles_to_27_array(tiles)
        
        # 检查花色限制
        suits = set()
        for tile in tiles:
            suits.add(tile.suit)
        if len(suits) > 2:
            return 99  # 花猪
        
        # 简化判断：如果能胡牌返回0，否则返回1
        if SimpleShantenCalc._can_win(tiles_array):
            return 0
        else:
            return 1
    
    @staticmethod
    def _can_win(tiles_array):
        """简化的胡牌检查"""
        # 检查七对
        pairs = sum(1 for count in tiles_array if count == 2)
        if pairs == 7:
            return True
        
        # 检查标准胡牌
        for i in range(27):
            if tiles_array[i] >= 2:
                test_array = tiles_array[:]
                test_array[i] -= 2
                if SimpleShantenCalc._check_melds(test_array, 0):
                    return True
        return False
    
    @staticmethod 
    def _check_melds(tiles_array, start):
        """简化的面子检查"""
        while start < 27 and tiles_array[start] == 0:
            start += 1
        
        if start >= 27:
            return True
        
        # 尝试刻子
        if tiles_array[start] >= 3:
            tiles_array[start] -= 3
            if SimpleShantenCalc._check_melds(tiles_array, start):
                tiles_array[start] += 3
                return True
            tiles_array[start] += 3
        
        # 尝试顺子
        if (start % 9 <= 6 and start + 2 < 27 and
            tiles_array[start] >= 1 and
            tiles_array[start + 1] >= 1 and
            tiles_array[start + 2] >= 1):
            
            tiles_array[start] -= 1
            tiles_array[start + 1] -= 1
            tiles_array[start + 2] -= 1
            
            if SimpleShantenCalc._check_melds(tiles_array, start):
                tiles_array[start] += 1
                tiles_array[start + 1] += 1
                tiles_array[start + 2] += 1
                return True
            
            tiles_array[start] += 1
            tiles_array[start + 1] += 1
            tiles_array[start + 2] += 1
        
        return False


class DiscardAnalysis:
    """弃牌分析结果"""
    def __init__(self, discard_tile: Tile, remaining_tiles: List[Tile]):
        self.discard_tile = discard_tile
        self.remaining_tiles = remaining_tiles
        # 使用修复后的算法
        self.shanten = TingValidator.calculate_shanten(remaining_tiles)
        self.winning_tiles = self._get_winning_tiles() if self.shanten == 0 else []
        self.winning_count = len(self.winning_tiles)
        self.effective_draws = self._calculate_effective_draws()
        self.score = self._calculate_score()
    
    def _get_winning_tiles(self):
        """获取胡牌张"""
        winning_tiles = []
        for suit in SuitType:
            for value in range(1, 10):
                test_tile = Tile(suit, value)
                test_tiles = self.remaining_tiles + [test_tile]
                if WinValidator.is_winning_hand(test_tiles):
                    winning_tiles.append(test_tile)
        return winning_tiles
    
    def _calculate_effective_draws(self) -> int:
        """计算有效进张数"""
        if self.shanten == 0:
            return self.winning_count * 4  # 每种牌有4张
        
        # 计算减少向听数的进张
        effective_tiles = set()
        for suit in SuitType:
            for value in range(1, 10):
                test_tile = Tile(suit, value)
                test_tiles = self.remaining_tiles + [test_tile]
                if TingValidator.calculate_shanten(test_tiles) < self.shanten:
                    effective_tiles.add(test_tile)
        
        return len(effective_tiles) * 4
    
    def get_detailed_analysis(self, remaining_tiles_count: Dict[str, int] = None) -> Dict[str, Any]:
        """获取详细分析信息"""
        if remaining_tiles_count is None:
            remaining_tiles_count = {}
        
        analysis = {
            "discard_tile": str(self.discard_tile),
            "shanten": self.shanten,
            "winning_tiles": [str(tile) for tile in self.winning_tiles],
            "winning_tiles_detail": {},
            "effective_tiles": [],
            "meld_analysis": self._analyze_possible_melds()
        }
        
        # 详细分析胡牌张
        if self.winning_tiles:
            for tile in self.winning_tiles:
                tile_str = str(tile)
                remaining = remaining_tiles_count.get(tile_str, 4)
                analysis["winning_tiles_detail"][tile_str] = {
                    "remaining_count": remaining,
                    "reason": self._get_winning_reason(tile)
                }
        
        # 分析有效进张
        if self.shanten > 0:
            for suit in SuitType:
                for value in range(1, 10):
                    test_tile = Tile(suit, value)
                    test_tiles = self.remaining_tiles + [test_tile]
                    new_shanten = TingValidator.calculate_shanten(test_tiles)
                    if new_shanten < self.shanten:
                        tile_str = str(test_tile)
                        remaining = remaining_tiles_count.get(tile_str, 4)
                        analysis["effective_tiles"].append({
                            "tile": tile_str,
                            "remaining_count": remaining,
                            "new_shanten": new_shanten,
                            "reason": self._get_effective_reason(test_tile)
                        })
        
        return analysis
    
    def _get_winning_reason(self, winning_tile: Tile) -> str:
        """获取胡牌理由"""
        # 模拟加入胡牌张后的手牌
        test_tiles = self.remaining_tiles + [winning_tile]
        
        # 分析胡牌形式
        tiles_array = TilesConverter.tiles_to_27_array(test_tiles)
        
        # 检查是否为七对
        if WinValidator._is_seven_pairs(tiles_array):
            return "七对"
        
        # 检查标准胡牌
        if WinValidator._is_standard_win(tiles_array):
            return "标准胡牌"
        
        return "未知胡牌形式"
    
    def _get_effective_reason(self, effective_tile: Tile) -> str:
        """获取有效进张理由"""
        # 模拟加入进张后的手牌
        test_tiles = self.remaining_tiles + [effective_tile]
        
        # 分析进张后能组成的面子
        return f"进张后向听数减少到{TingValidator.calculate_shanten(test_tiles)}"
    
    def _analyze_possible_melds(self) -> List[str]:
        """分析可能的面子组合（正确处理牌的使用）"""
        tiles_array = TilesConverter.tiles_to_27_array(self.remaining_tiles)
        melds = []
        used_tiles = [0] * 27  # 跟踪已使用的牌
        
        # 优先识别刻子
        for i in range(27):
            available = tiles_array[i] - used_tiles[i]
            if available >= 3:
                tile = Tile(SuitType(['m', 's', 'p'][i // 9]), (i % 9) + 1)
                # 计算可以组成多少个刻子
                kotsu_count = available // 3
                for _ in range(kotsu_count):
                    melds.append(f"刻子:{tile}")
                    used_tiles[i] += 3
        
        # 然后识别顺子
        for i in range(27):
            # 检查顺子（不能跨花色）
            if (i % 9 <= 6 and i + 2 < 27):
                while (tiles_array[i] - used_tiles[i] >= 1 and
                       tiles_array[i + 1] - used_tiles[i + 1] >= 1 and
                       tiles_array[i + 2] - used_tiles[i + 2] >= 1):
                    
                    tile1 = Tile(SuitType(['m', 's', 'p'][i // 9]), (i % 9) + 1)
                    tile2 = Tile(SuitType(['m', 's', 'p'][i // 9]), (i % 9) + 2)
                    tile3 = Tile(SuitType(['m', 's', 'p'][i // 9]), (i % 9) + 3)
                    melds.append(f"顺子:{tile1}{tile2}{tile3}")
                    
                    # 标记为已使用
                    used_tiles[i] += 1
                    used_tiles[i + 1] += 1
                    used_tiles[i + 2] += 1
        
        # 最后识别对子
        for i in range(27):
            available = tiles_array[i] - used_tiles[i]
            if available >= 2:
                tile = Tile(SuitType(['m', 's', 'p'][i // 9]), (i % 9) + 1)
                # 计算可以组成多少个对子
                pair_count = available // 2
                for _ in range(pair_count):
                    melds.append(f"对子:{tile}")
                    used_tiles[i] += 2
        
        # 显示剩余单张
        for i in range(27):
            remaining = tiles_array[i] - used_tiles[i]
            if remaining > 0:
                tile = Tile(SuitType(['m', 's', 'p'][i // 9]), (i % 9) + 1)
                for _ in range(remaining):
                    melds.append(f"单张:{tile}")
        
        return melds
    
    def _calculate_score(self) -> float:
        """计算弃牌选择的综合得分"""
        if self.shanten == 0:
            return 1000 + self.winning_count * 10  # 听牌状态得分最高
        
        # 基础得分 = 100 - 向听数 * 10
        base_score = 100 - self.shanten * 10
        
        # 有效进张数加成
        draw_bonus = self.effective_draws * 2
        
        return base_score + draw_bonus
    
    def __str__(self) -> str:
        return f"弃{self.discard_tile}: {self.shanten}向听, {self.effective_draws}进张, 得分{self.score:.1f}"


class HandAnalyzer:
    """手牌分析器 - 提供最优出牌建议"""
    
    @staticmethod
    def analyze_discard_options(tiles: List[Tile], melds: List = None, remaining_tiles_count: Dict[str, int] = None) -> List[DiscardAnalysis]:
        """
        分析所有弃牌选择
        返回按得分排序的弃牌分析结果
        """
        if melds is None:
            melds = []
        if remaining_tiles_count is None:
            remaining_tiles_count = {}
        
        analyses = []
        
        # 获取所有可能的弃牌
        unique_tiles = list(set(tiles))
        
        for discard_tile in unique_tiles:
            # 模拟弃牌后的手牌
            remaining_tiles = tiles.copy()
            remaining_tiles.remove(discard_tile)
            
            # 分析弃牌效果
            analysis = DiscardAnalysis(discard_tile, remaining_tiles)
            analyses.append(analysis)
        
        # 按得分排序(降序)
        analyses.sort(key=lambda x: x.score, reverse=True)
        
        return analyses
    
    @staticmethod
    def get_best_discard(tiles: List[Tile], melds: List = None) -> DiscardAnalysis:
        """获取最佳弃牌选择"""
        analyses = HandAnalyzer.analyze_discard_options(tiles, melds)
        return analyses[0] if analyses else None
    
    @staticmethod
    def analyze_hand_situation(player_state: PlayerState, known_tiles: List[Tile] = None) -> Dict[str, Any]:
        """
        分析手牌局势
        
        Args:
            player_state: 玩家状态
            known_tiles: 已知的牌(对手弃牌、副露等)
        
        Returns:
            详细的手牌分析结果
        """
        if known_tiles is None:
            known_tiles = []
        
        tiles = player_state.hand_tiles
        melds = player_state.melds
        
        # 基础信息
        current_shanten = TingValidator.calculate_shanten(tiles, melds)
        is_ting = current_shanten == 0
        
        # 获取弃牌分析
        discard_analyses = HandAnalyzer.analyze_discard_options(tiles, melds)
        
        # 计算剩余牌数
        remaining_tiles_count = HandAnalyzer._calculate_remaining_tiles(tiles, melds, known_tiles)
        
        # 生成建议
        suggestions = HandAnalyzer._generate_suggestions(player_state, discard_analyses, remaining_tiles_count)
        
        return {
            "current_shanten": current_shanten,
            "is_ting": is_ting,
            "hand_tiles": [str(tile) for tile in tiles],
            "melds": [str(meld) for meld in melds],
            "discard_analyses": discard_analyses,
            "best_discard": discard_analyses[0] if discard_analyses else None,
            "remaining_tiles_count": remaining_tiles_count,
            "suggestions": suggestions,
            "is_flower_pig": player_state.is_flower_pig()
        }
    
    @staticmethod
    def _calculate_remaining_tiles(hand_tiles: List[Tile], melds: List, known_tiles: List[Tile]) -> Dict[str, int]:
        """计算剩余牌数"""
        # 初始化每种牌4张
        remaining = {}
        for suit in SuitType:
            for value in range(1, 10):
                tile = Tile(suit, value)
                remaining[str(tile)] = 4
        
        # 减去手牌
        for tile in hand_tiles:
            if str(tile) in remaining:
                remaining[str(tile)] -= 1
        
        # 减去副露
        for meld in melds:
            for tile in meld.tiles:
                if str(tile) in remaining:
                    remaining[str(tile)] -= 1
        
        # 减去已知牌
        for tile in known_tiles:
            if str(tile) in remaining:
                remaining[str(tile)] -= 1
        
        return remaining
    
    @staticmethod
    def _generate_suggestions(player_state: PlayerState, discard_analyses: List[DiscardAnalysis], 
                            remaining_tiles_count: Dict[str, int]) -> List[str]:
        """生成游戏建议（集成高级AI策略）"""
        suggestions = []
        
        if not discard_analyses:
            return ["无可用分析"]
        
        best_analysis = discard_analyses[0]
        
        # 高级AI策略分析
        flower_pig_needed, flower_pig_analysis = AdvancedAIStrategy.should_avoid_flower_pig(
            player_state.hand_tiles, player_state.melds)
        
        # 花猪检查（优先级最高）
        if player_state.is_flower_pig():
            suggestions.append("⚠️ 当前为花猪状态，需要赔付其他玩家")
            return suggestions
        elif flower_pig_needed:
            suggestions.append(f"🚨 花猪风险等级: {flower_pig_analysis['risk_level']}/5")
            if flower_pig_analysis['avoidance_strategy']:
                strategy = flower_pig_analysis['avoidance_strategy']
                suggestions.append(f"🛡️ 避免花猪：优先打出{strategy['target_suit_to_eliminate']}的牌")
        
        # 定缺策略建议（仅在未定缺时）
        if not player_state.missing_suit:
            missing_suit, missing_analysis = AdvancedAIStrategy.choose_missing_suit(
                player_state.hand_tiles, player_state.melds)
            suggestions.append(f"🎯 {missing_analysis['reasoning']}")
        
        # 听牌状态
        if best_analysis.shanten == 0:
            suggestions.append(f"🎉 已听牌! 胡牌张: {[str(tile) for tile in best_analysis.winning_tiles]}")
            suggestions.append(f"建议打出: {best_analysis.discard_tile}")
            
            # 计算胡牌概率
            total_winning_tiles = sum(remaining_tiles_count.get(str(tile), 0) for tile in best_analysis.winning_tiles)
            suggestions.append(f"剩余胡牌张: {total_winning_tiles}张")
        
        # 一向听状态
        elif best_analysis.shanten == 1:
            suggestions.append(f"🔥 一向听! 建议打出: {best_analysis.discard_tile}")
            suggestions.append(f"有效进张: {best_analysis.effective_draws}张")
        
        # 多向听状态
        else:
            suggestions.append(f"📈 {best_analysis.shanten}向听，建议打出: {best_analysis.discard_tile}")
            suggestions.append(f"有效进张: {best_analysis.effective_draws}张")
        
        # 杠牌决策分析
        kong_opportunities = HandAnalyzer._analyze_kong_opportunities(player_state)
        if kong_opportunities:
            suggestions.append(f"🎲 杠牌机会: {kong_opportunities}")
        
        # 定缺检查
        if player_state.missing_suit:
            missing_tiles = [tile for tile in player_state.hand_tiles if tile.suit == player_state.missing_suit]
            if missing_tiles:
                suggestions.append(f"⚠️ 发现定缺{player_state.missing_suit.value}的牌: {[str(tile) for tile in missing_tiles]}")
        
        return suggestions
    
    @staticmethod
    def _analyze_kong_opportunities(player_state: PlayerState) -> str:
        """分析杠牌机会"""
        # 统计手牌中每种牌的数量
        tile_counts = {}
        for tile in player_state.hand_tiles:
            tile_key = (tile.suit, tile.value)
            tile_counts[tile_key] = tile_counts.get(tile_key, 0) + 1
        
        kong_recommendations = []
        
        # 检查明杠机会（4张相同的牌）
        for (suit, value), count in tile_counts.items():
            if count >= 4:
                tile = Tile(suit, value)
                should_kong, analysis = AdvancedAIStrategy.should_declare_kong(
                    tile, player_state.hand_tiles, player_state.melds)
                if should_kong:
                    kong_recommendations.append(f"{tile}(明杠, {analysis['recommendation']})")
        
        # 检查加杠机会（已有碰，手中有1张）
        for meld in player_state.melds:
            if meld.meld_type == MeldType.PENG:
                meld_tile_key = (meld.get_suit(), meld.get_value())
                if tile_counts.get(meld_tile_key, 0) >= 1:
                    tile = Tile(meld.get_suit(), meld.get_value())
                    should_kong, analysis = AdvancedAIStrategy.should_declare_kong(
                        tile, player_state.hand_tiles, player_state.melds)
                    if should_kong:
                        kong_recommendations.append(f"{tile}(加杠, {analysis['recommendation']})")
        
        return " | ".join(kong_recommendations) if kong_recommendations else ""
    
    @staticmethod
    def simulate_draw_tile(player_state: PlayerState, draw_tile: Tile, known_tiles: List[Tile] = None) -> Dict[str, Any]:
        """
        模拟摸牌后的最佳出牌（集成高级AI策略）
        
        Args:
            player_state: 玩家状态
            draw_tile: 摸到的牌
            known_tiles: 已知的牌
        
        Returns:
            摸牌后的分析结果
        """
        if known_tiles is None:
            known_tiles = []
        
        # 创建新的手牌(加入摸到的牌)
        new_tiles = player_state.hand_tiles + [draw_tile]
        
        # 检查是否可以胡牌
        if WinValidator.is_winning_hand(new_tiles, player_state.melds):
            return {
                "action": "win",
                "winning_tile": str(draw_tile),
                "is_self_draw": True,
                "message": f"🎉 自摸 {draw_tile}!"
            }
        
        # 检查杠牌机会（优先级高于弃牌）
        should_kong, kong_analysis = AdvancedAIStrategy.should_declare_kong(
            draw_tile, new_tiles, player_state.melds)
        
        if should_kong and kong_analysis['can_kong']:
            return {
                "action": "kong",
                "kong_tile": str(draw_tile),
                "kong_type": "明杠" if draw_tile in player_state.hand_tiles else "加杠",
                "analysis": kong_analysis,
                "message": f"🎲 {kong_analysis['recommendation']}: {draw_tile}"
            }
        
        # 检查是否为定缺牌(必须打出)
        if player_state.missing_suit and draw_tile.suit == player_state.missing_suit:
            return {
                "action": "discard",
                "discard_tile": str(draw_tile),
                "forced": True,
                "message": f"🔒 定缺牌必须打出: {draw_tile}"
            }
        
        # 检查花猪避免策略
        should_avoid_pig, pig_analysis = AdvancedAIStrategy.should_avoid_flower_pig(
            new_tiles, player_state.melds)
        
        if should_avoid_pig and pig_analysis['avoidance_strategy']:
            strategy = pig_analysis['avoidance_strategy']
            target_suit = SuitType(strategy['target_suit_to_eliminate'])
            
            # 如果摸到的牌是需要避免的花色，优先打出
            if draw_tile.suit == target_suit:
                return {
                    "action": "discard",
                    "discard_tile": str(draw_tile),
                    "forced": True,
                    "strategy": "avoid_flower_pig",
                    "message": f"🛡️ 避免花猪，打出: {draw_tile}"
                }
        
        # 分析最佳出牌
        analysis = HandAnalyzer.analyze_discard_options(new_tiles, player_state.melds)
        
        # 应用高级策略调整建议
        best_analysis = analysis[0]
        if should_avoid_pig and pig_analysis['avoidance_strategy']:
            # 查找是否有更好的避免花猪选择
            strategy = pig_analysis['avoidance_strategy']
            target_suit = SuitType(strategy['target_suit_to_eliminate'])
            
            for discard_analysis in analysis:
                if discard_analysis.discard_tile.suit == target_suit:
                    best_analysis = discard_analysis
                    break
        
        return {
            "action": "discard",
            "discard_tile": str(best_analysis.discard_tile),
            "forced": False,
            "analysis": best_analysis,
            "advanced_strategy": {
                "flower_pig_risk": pig_analysis['risk_level'] if should_avoid_pig else 0,
                "kong_opportunity": kong_analysis['recommendation'] if kong_analysis.get('can_kong') else None
            },
            "message": f"💡 建议打出: {best_analysis.discard_tile}"
        }


class AdvancedAIStrategy:
    """高级AI策略 - 实现定缺、避免花猪、杠牌决策等高级策略"""
    
    @staticmethod
    def choose_missing_suit(tiles: List[Tile], melds: List[Meld] = None) -> Tuple[SuitType, Dict[str, Any]]:
        """
        定缺策略：选择最优的定缺花色
        
        Args:
            tiles: 当前手牌
            melds: 当前副露
            
        Returns:
            (建议定缺花色, 分析详情)
        """
        if melds is None:
            melds = []
            
        # 分析每个花色的价值
        suit_analyses = {}
        
        for suit in SuitType:
            analysis = AdvancedAIStrategy._analyze_suit_value(tiles, melds, suit)
            suit_analyses[suit] = analysis
        
        # 选择价值最低的花色作为定缺
        best_missing_suit = min(suit_analyses.keys(), 
                               key=lambda s: suit_analyses[s]['removal_score'])
        
        return best_missing_suit, {
            'chosen_suit': best_missing_suit.value,
            'suit_analyses': {s.value: analysis for s, analysis in suit_analyses.items()},
            'reasoning': AdvancedAIStrategy._get_missing_suit_reasoning(suit_analyses, best_missing_suit)
        }
    
    @staticmethod
    def _analyze_suit_value(tiles: List[Tile], melds: List[Meld], suit: SuitType) -> Dict[str, Any]:
        """分析某个花色的价值"""
        suit_tiles = [tile for tile in tiles if tile.suit == suit]
        suit_melds = [meld for meld in melds if meld.get_suit() == suit]
        
        # 计算花色基础信息
        tile_count = len(suit_tiles)
        meld_count = len(suit_melds)
        total_tiles = tile_count + sum(len(meld.tiles) for meld in suit_melds)
        
        # 分析牌型结构
        tiles_array = [0] * 9
        for tile in suit_tiles:
            tiles_array[tile.value - 1] += 1
        
        # 计算有用度得分
        usefulness_score = AdvancedAIStrategy._calculate_suit_usefulness(tiles_array)
        
        # 计算移除后的影响
        removal_impact = AdvancedAIStrategy._calculate_removal_impact(tiles, suit)
        
        # 计算最终移除得分（越高越适合定缺）
        removal_score = (10 - usefulness_score) + removal_impact + (tile_count * 2)
        
        return {
            'tile_count': tile_count,
            'meld_count': meld_count,
            'total_tiles': total_tiles,
            'usefulness_score': usefulness_score,
            'removal_impact': removal_impact,
            'removal_score': removal_score,
            'tiles': [str(tile) for tile in suit_tiles],
            'isolated_tiles': AdvancedAIStrategy._find_isolated_tiles(tiles_array)
        }
    
    @staticmethod
    def _calculate_suit_usefulness(tiles_array: List[int]) -> float:
        """计算花色的有用度（0-10分）"""
        score = 0.0
        
        # 检查完整的面子
        for i in range(7):  # 顺子
            if tiles_array[i] >= 1 and tiles_array[i + 1] >= 1 and tiles_array[i + 2] >= 1:
                score += 3.0
                
        for i in range(9):  # 刻子
            if tiles_array[i] >= 3:
                score += 3.0
            elif tiles_array[i] >= 2:  # 对子
                score += 1.5
        
        # 检查潜在的面子（搭子）
        for i in range(8):  # 两面搭子
            if tiles_array[i] >= 1 and tiles_array[i + 1] >= 1:
                score += 1.0
                
        for i in range(7):  # 嵌张搭子
            if tiles_array[i] >= 1 and tiles_array[i + 2] >= 1:
                score += 0.8
        
        return min(score, 10.0)
    
    @staticmethod
    def _calculate_removal_impact(tiles: List[Tile], suit: SuitType) -> float:
        """计算移除该花色后对整体牌型的影响"""
        # 移除该花色的牌
        remaining_tiles = [tile for tile in tiles if tile.suit != suit]
        
        if not remaining_tiles:
            return 10.0  # 如果移除后没有牌了，影响最大
        
        # 计算移除前后的向听数差异
        original_shanten = SimpleShantenCalc.calculate_shanten(tiles)
        new_shanten = SimpleShantenCalc.calculate_shanten(remaining_tiles)
        
        # 向听数增加越少，移除影响越小（越适合定缺）
        shanten_increase = new_shanten - original_shanten
        return max(0, shanten_increase)
    
    @staticmethod
    def _find_isolated_tiles(tiles_array: List[int]) -> List[str]:
        """找出孤立的牌（周围没有相邻牌的单张）"""
        isolated = []
        for i in range(9):
            if tiles_array[i] == 1:  # 只有一张
                # 检查是否孤立
                has_neighbor = False
                if i > 0 and tiles_array[i - 1] > 0:
                    has_neighbor = True
                if i < 8 and tiles_array[i + 1] > 0:
                    has_neighbor = True
                if not has_neighbor:
                    isolated.append(str(i + 1))
        return isolated
    
    @staticmethod
    def _get_missing_suit_reasoning(suit_analyses: Dict[SuitType, Dict], chosen_suit: SuitType) -> str:
        """生成定缺选择的理由"""
        chosen_analysis = suit_analyses[chosen_suit]
        
        reasons = []
        if chosen_analysis['tile_count'] >= 4:
            reasons.append(f"{chosen_suit.value}有{chosen_analysis['tile_count']}张牌较多")
        if chosen_analysis['isolated_tiles']:
            reasons.append(f"有孤立牌{chosen_analysis['isolated_tiles']}")
        if chosen_analysis['usefulness_score'] < 3:
            reasons.append("该花色有用度较低")
        if chosen_analysis['removal_impact'] < 2:
            reasons.append("移除后对整体牌型影响较小")
        
        if not reasons:
            reasons.append("相对其他花色价值最低")
        
        return f"建议定缺{chosen_suit.value}：" + "，".join(reasons)
    
    @staticmethod
    def should_avoid_flower_pig(tiles: List[Tile], melds: List[Meld] = None, 
                               discard_tile: Tile = None) -> Tuple[bool, Dict[str, Any]]:
        """
        避免花猪策略：判断是否应该避免花猪
        
        Args:
            tiles: 当前手牌
            melds: 当前副露
            discard_tile: 准备打出的牌
            
        Returns:
            (是否需要避免花猪, 分析详情)
        """
        if melds is None:
            melds = []
        
        # 计算当前的花色数量
        current_suits = set()
        all_tiles = tiles.copy()
        
        # 加入副露的牌
        for meld in melds:
            all_tiles.extend(meld.tiles)
        
        # 如果有准备打出的牌，则从考虑中移除
        if discard_tile and discard_tile in all_tiles:
            all_tiles.remove(discard_tile)
        
        for tile in all_tiles:
            current_suits.add(tile.suit)
        
        suit_count = len(current_suits)
        is_flower_pig = suit_count >= 3
        risk_level = AdvancedAIStrategy._calculate_flower_pig_risk(tiles, melds, discard_tile)
        
        # 生成避免花猪的建议
        avoidance_strategy = None
        if is_flower_pig or risk_level >= 3:
            avoidance_strategy = AdvancedAIStrategy._generate_flower_pig_avoidance(tiles, melds)
        
        return is_flower_pig or risk_level >= 3, {
            'current_suit_count': suit_count,
            'suits_present': [suit.value for suit in current_suits],
            'is_flower_pig': is_flower_pig,
            'risk_level': risk_level,
            'avoidance_strategy': avoidance_strategy
        }
    
    @staticmethod
    def _calculate_flower_pig_risk(tiles: List[Tile], melds: List[Meld], discard_tile: Tile = None) -> int:
        """计算花猪风险等级（1-5）"""
        # 统计每个花色的牌数
        suit_counts = {suit: 0 for suit in SuitType}
        
        # 统计手牌
        test_tiles = tiles.copy()
        if discard_tile and discard_tile in test_tiles:
            test_tiles.remove(discard_tile)
            
        for tile in test_tiles:
            suit_counts[tile.suit] += 1
        
        # 统计副露
        for meld in melds:
            suit = meld.get_suit()
            suit_counts[suit] += len(meld.tiles)
        
        # 计算有效花色数
        active_suits = sum(1 for count in suit_counts.values() if count > 0)
        
        if active_suits >= 3:
            return 5  # 已经花猪
        elif active_suits == 2:
            # 检查是否容易变成花猪
            min_suit_count = min(count for count in suit_counts.values() if count > 0)
            if min_suit_count <= 2:
                return 4  # 高风险
            else:
                return 2  # 中等风险
        else:
            return 1  # 低风险
    
    @staticmethod
    def _generate_flower_pig_avoidance(tiles: List[Tile], melds: List[Meld]) -> Dict[str, Any]:
        """生成避免花猪的策略"""
        # 统计每个花色的牌
        suit_tiles = {suit: [] for suit in SuitType}
        for tile in tiles:
            suit_tiles[tile.suit].append(tile)
        
        # 找出牌数最少的花色
        min_suit = min(suit_tiles.keys(), key=lambda s: len(suit_tiles[s]))
        min_count = len(suit_tiles[min_suit])
        
        strategy = {
            'target_suit_to_eliminate': min_suit.value,
            'tiles_to_discard': [str(tile) for tile in suit_tiles[min_suit]],
            'priority': 'high' if min_count <= 2 else 'medium'
        }
        
        return strategy
    
    @staticmethod
    def should_declare_kong(tile: Tile, hand_tiles: List[Tile], melds: List[Meld] = None,
                           game_situation: Dict = None) -> Tuple[bool, Dict[str, Any]]:
        """
        杠牌决策：判断是否应该杠牌
        
        Args:
            tile: 可以杠的牌
            hand_tiles: 手牌
            melds: 副露
            game_situation: 当前游戏局势
            
        Returns:
            (是否应该杠牌, 分析详情)
        """
        if melds is None:
            melds = []
        if game_situation is None:
            game_situation = {}
        
        # 基础检查：是否真的可以杠
        tile_count = sum(1 for t in hand_tiles if t == tile)
        existing_pong = any(meld.get_value() == tile.value and meld.get_suit() == tile.suit 
                           and meld.meld_type == MeldType.PENG for meld in melds)
        
        can_kong = tile_count >= 4 or (tile_count >= 1 and existing_pong)
        if not can_kong:
            return False, {'reason': '无法杠牌', 'can_kong': False}
        
        # 分析杠牌的利弊
        benefits = AdvancedAIStrategy._analyze_kong_benefits(tile, hand_tiles, melds, game_situation)
        risks = AdvancedAIStrategy._analyze_kong_risks(tile, hand_tiles, melds, game_situation)
        
        # 综合决策
        total_score = benefits['total_score'] - risks['total_score']
        should_kong = total_score > 0
        
        return should_kong, {
            'can_kong': True,
            'should_kong': should_kong,
            'decision_score': total_score,
            'benefits': benefits,
            'risks': risks,
            'recommendation': AdvancedAIStrategy._get_kong_recommendation(total_score, benefits, risks)
        }
    
    @staticmethod
    def _analyze_kong_benefits(tile: Tile, hand_tiles: List[Tile], melds: List[Meld], 
                              game_situation: Dict) -> Dict[str, Any]:
        """分析杠牌的好处"""
        benefits = []
        score = 0
        
        # 1. 获得额外摸牌机会
        benefits.append('获得额外摸牌机会')
        score += 3
        
        # 2. 增加根数（倍数）
        benefits.append('增加1根（倍数x2）')
        score += 5
        
        # 3. 移除无用牌
        current_shanten = SimpleShantenCalc.calculate_shanten(hand_tiles)
        test_tiles = [t for t in hand_tiles if t != tile]  # 移除杠的牌
        new_shanten = SimpleShantenCalc.calculate_shanten(test_tiles)
        
        if new_shanten <= current_shanten:
            benefits.append('移除无用牌，不影响向听数')
            score += 2
        
        # 4. 清一色加成
        suits = set(t.suit for t in hand_tiles)
        if len(suits) == 1:
            benefits.append('保持清一色完整性')
            score += 3
        
        return {
            'benefits': benefits,
            'total_score': score
        }
    
    @staticmethod
    def _analyze_kong_risks(tile: Tile, hand_tiles: List[Tile], melds: List[Meld], 
                           game_situation: Dict) -> Dict[str, Any]:
        """分析杠牌的风险"""
        risks = []
        score = 0
        
        # 1. 暴露手牌信息
        risks.append('暴露手牌信息给对手')
        score += 2
        
        # 2. 可能破坏手牌结构
        current_shanten = SimpleShantenCalc.calculate_shanten(hand_tiles)
        test_tiles = [t for t in hand_tiles if t != tile]
        new_shanten = SimpleShantenCalc.calculate_shanten(test_tiles)
        
        if new_shanten > current_shanten:
            risks.append('破坏手牌结构，增加向听数')
            score += 8
        
        # 3. 游戏后期风险
        danger_level = game_situation.get('danger_level', 1)
        if danger_level >= 4:
            risks.append('游戏后期，杠牌增加危险')
            score += 4
        
        # 4. 对手听牌时的风险
        if any(game_situation.get('opponent_ting', [])):
            risks.append('对手听牌时杠牌有风险')
            score += 6
        
        return {
            'risks': risks,
            'total_score': score
        }
    
    @staticmethod
    def _get_kong_recommendation(score: float, benefits: Dict, risks: Dict) -> str:
        """生成杠牌建议"""
        if score > 5:
            return f"强烈建议杠牌（得分+{score:.1f}）"
        elif score > 0:
            return f"建议杠牌（得分+{score:.1f}）"
        elif score > -3:
            return f"可以考虑杠牌（得分{score:.1f}）"
        else:
            return f"不建议杠牌（得分{score:.1f}）"


class AdvancedAIDecisionEngine:
    """高级AI决策引擎 - 整合所有AI策略的主要接口"""
    
    @staticmethod
    def get_comprehensive_analysis(player_state: PlayerState, game_context: Dict = None) -> Dict[str, Any]:
        """
        获取全面的AI分析建议
        
        Args:
            player_state: 玩家状态
            game_context: 游戏上下文信息
            
        Returns:
            完整的AI分析结果
        """
        if game_context is None:
            game_context = {}
        
        analysis = {
            "basic_analysis": HandAnalyzer.analyze_hand_situation(player_state),
            "missing_suit_strategy": None,
            "flower_pig_strategy": None,
            "kong_opportunities": [],
            "overall_recommendations": []
        }
        
        # 定缺策略分析
        if not player_state.missing_suit:
            missing_suit, missing_analysis = AdvancedAIStrategy.choose_missing_suit(
                player_state.hand_tiles, player_state.melds)
            analysis["missing_suit_strategy"] = {
                "recommended_suit": missing_suit.value,
                "analysis": missing_analysis
            }
        
        # 花猪避免策略
        should_avoid, pig_analysis = AdvancedAIStrategy.should_avoid_flower_pig(
            player_state.hand_tiles, player_state.melds)
        analysis["flower_pig_strategy"] = {
            "should_avoid": should_avoid,
            "analysis": pig_analysis
        }
        
        # 杠牌机会分析
        kong_opps = AdvancedAIDecisionEngine._analyze_all_kong_opportunities(player_state, game_context)
        analysis["kong_opportunities"] = kong_opps
        
        # 生成整体建议
        overall_recs = AdvancedAIDecisionEngine._generate_overall_recommendations(analysis, game_context)
        analysis["overall_recommendations"] = overall_recs
        
        return analysis
    
    @staticmethod
    def _analyze_all_kong_opportunities(player_state: PlayerState, game_context: Dict) -> List[Dict]:
        """分析所有杠牌机会"""
        opportunities = []
        
        # 统计手牌
        tile_counts = {}
        for tile in player_state.hand_tiles:
            tile_key = str(tile)
            tile_counts[tile_key] = tile_counts.get(tile_key, 0) + 1
        
        # 明杠机会
        for tile_str, count in tile_counts.items():
            if count >= 4:
                tile = Tile.from_string(tile_str)
                should_kong, analysis = AdvancedAIStrategy.should_declare_kong(
                    tile, player_state.hand_tiles, player_state.melds, game_context)
                opportunities.append({
                    "tile": tile_str,
                    "type": "明杠",
                    "should_declare": should_kong,
                    "analysis": analysis
                })
        
        # 加杠机会
        for meld in player_state.melds:
            if meld.meld_type == MeldType.PENG:
                meld_tile_str = str(meld.tiles[0])
                if tile_counts.get(meld_tile_str, 0) >= 1:
                    tile = meld.tiles[0]
                    should_kong, analysis = AdvancedAIStrategy.should_declare_kong(
                        tile, player_state.hand_tiles, player_state.melds, game_context)
                    opportunities.append({
                        "tile": meld_tile_str,
                        "type": "加杠",
                        "should_declare": should_kong,
                        "analysis": analysis
                    })
        
        return opportunities
    
    @staticmethod
    def _generate_overall_recommendations(analysis: Dict, game_context: Dict) -> List[str]:
        """生成整体策略建议"""
        recommendations = []
        
        # 基础分析建议
        basic = analysis["basic_analysis"]
        recommendations.extend(basic["suggestions"])
        
        # 定缺建议
        if analysis["missing_suit_strategy"]:
            strategy = analysis["missing_suit_strategy"]
            recommendations.append(f"🔢 {strategy['analysis']['reasoning']}")
        
        # 花猪避免建议
        pig_strategy = analysis["flower_pig_strategy"]
        if pig_strategy["should_avoid"]:
            risk_level = pig_strategy["analysis"]["risk_level"]
            if risk_level >= 4:
                recommendations.append(f"🚨 高花猪风险({risk_level}/5)，立即避免!")
            elif risk_level >= 3:
                recommendations.append(f"⚠️ 中等花猪风险({risk_level}/5)，建议避免")
        
        # 杠牌建议
        kong_recs = [opp for opp in analysis["kong_opportunities"] if opp["should_declare"]]
        if kong_recs:
            kong_list = [f"{opp['tile']}({opp['type']})" for opp in kong_recs]
            recommendations.append(f"🎲 建议杠牌: {', '.join(kong_list)}")
        
        # 战术建议
        current_shanten = basic["current_shanten"]
        if current_shanten <= 1:
            recommendations.append("⚡ 进入终盘阶段，优先考虑安全出牌")
        elif current_shanten <= 3:
            recommendations.append("🎯 中盘阶段，平衡效率与安全")
        else:
            recommendations.append("🚀 序盘阶段，以最大效率为主")
        
        return recommendations
    
    @staticmethod
    def make_decision(player_state: PlayerState, available_actions: List[str], 
                     game_context: Dict = None) -> Dict[str, Any]:
        """
        基于当前局面做出最优决策
        
        Args:
            player_state: 玩家状态
            available_actions: 可选择的行动 ['discard', 'kong', 'win', 'pass']
            game_context: 游戏上下文
            
        Returns:
            AI决策结果
        """
        if game_context is None:
            game_context = {}
        
        analysis = AdvancedAIDecisionEngine.get_comprehensive_analysis(player_state, game_context)
        
        # 决策优先级
        if "win" in available_actions:
            return {
                "action": "win",
                "confidence": 1.0,
                "reasoning": "胡牌是最优选择"
            }
        
        if "kong" in available_actions:
            kong_opps = [opp for opp in analysis["kong_opportunities"] if opp["should_declare"]]
            if kong_opps:
                best_kong = max(kong_opps, key=lambda x: x["analysis"]["decision_score"])
                return {
                    "action": "kong",
                    "target": best_kong["tile"],
                    "confidence": 0.8,
                    "reasoning": best_kong["analysis"]["recommendation"]
                }
        
        if "discard" in available_actions:
            best_discard = analysis["basic_analysis"]["best_discard"]
            flower_pig = analysis["flower_pig_strategy"]
            
            # 应用花猪避免策略
            final_discard = best_discard.discard_tile
            confidence = 0.7
            reasoning = f"基础分析建议: {best_discard.discard_tile}"
            
            if flower_pig["should_avoid"] and flower_pig["analysis"]["avoidance_strategy"]:
                strategy = flower_pig["analysis"]["avoidance_strategy"]
                target_suit = SuitType(strategy["target_suit_to_eliminate"])
                
                # 查找该花色的牌
                suit_tiles = [tile for tile in player_state.hand_tiles if tile.suit == target_suit]
                if suit_tiles:
                    final_discard = suit_tiles[0]  # 选择第一张
                    confidence = 0.9
                    reasoning = f"避免花猪策略: 打出{target_suit.value}的牌"
            
            return {
                "action": "discard",
                "target": str(final_discard),
                "confidence": confidence,
                "reasoning": reasoning
            }
        
        return {
            "action": "pass",
            "confidence": 0.5,
            "reasoning": "无更好选择"
        }


class GameAnalyzer:
    """游戏分析器 - 分析整个游戏状态"""
    
    @staticmethod
    def analyze_game_state(players: List[PlayerState], known_discards: List[Tile] = None) -> Dict[str, Any]:
        """分析整个游戏状态"""
        if known_discards is None:
            known_discards = []
        
        game_analysis = {
            "players": [],
            "game_phase": GameAnalyzer._determine_game_phase(players),
            "danger_level": GameAnalyzer._calculate_danger_level(players),
            "recommendations": []
        }
        
        for player in players:
            player_analysis = HandAnalyzer.analyze_hand_situation(player, known_discards)
            game_analysis["players"].append(player_analysis)
        
        return game_analysis
    
    @staticmethod
    def _determine_game_phase(players: List[PlayerState]) -> str:
        """判断游戏阶段"""
        min_shanten = min(TingValidator.calculate_shanten(player.hand_tiles, player.melds) for player in players)
        
        if min_shanten == 0:
            return "终盘"  # 有人听牌
        elif min_shanten == 1:
            return "中盘"  # 有人一向听
        else:
            return "序盘"  # 序盘阶段
    
    @staticmethod
    def _calculate_danger_level(players: List[PlayerState]) -> int:
        """计算危险等级 (1-5)"""
        ting_players = sum(1 for player in players if TingValidator.calculate_shanten(player.hand_tiles, player.melds) == 0)
        
        if ting_players >= 2:
            return 5  # 非常危险
        elif ting_players == 1:
            return 4  # 危险
        else:
            one_shanten_players = sum(1 for player in players if TingValidator.calculate_shanten(player.hand_tiles, player.melds) == 1)
            if one_shanten_players >= 2:
                return 3  # 中等危险
            elif one_shanten_players == 1:
                return 2  # 轻微危险
            else:
                return 1  # 安全


if __name__ == "__main__":
    # 测试代码
    print("=== HandAnalyzer Test ===")
    
    # 创建测试手牌
    tiles_str = "12345678m99s"
    tiles = TilesConverter.string_to_tiles(tiles_str)
    
    print(f"Testing tiles: {tiles_str}")
    
    # 分析弃牌选择
    analyses = HandAnalyzer.analyze_discard_options(tiles)
    print("弃牌分析:")
    for i, analysis in enumerate(analyses[:3]):  # 只显示前3个
        print(f"  {i+1}. {analysis}")
    
    # 创建玩家状态测试
    player = PlayerState(0)
    for tile in tiles:
        player.add_tile(tile)
    
    situation = HandAnalyzer.analyze_hand_situation(player)
    print(f"\n手牌局势分析:")
    print(f"  当前向听: {situation['current_shanten']}")
    print(f"  是否听牌: {situation['is_ting']}")
    print(f"  建议:")
    for suggestion in situation['suggestions']:
        print(f"    {suggestion}")