#!/usr/bin/env python3
"""
SichuanMahjongKit Hand Analyzer
血战到底麻将库手牌分析器
"""

from typing import List, Dict, Any, Tuple, Optional, Set
from collections import Counter, defaultdict
import copy

from .core import Tile, TilesConverter, SuitType, PlayerState, Meld
from .validator import WinValidator, TingValidator


class DiscardAnalysis:
    """弃牌分析结果"""
    def __init__(self, discard_tile: Tile, remaining_tiles: List[Tile]):
        self.discard_tile = discard_tile
        self.remaining_tiles = remaining_tiles
        self.shanten = TingValidator.calculate_shanten(remaining_tiles)
        self.winning_tiles = WinValidator.get_winning_tiles(remaining_tiles)
        self.winning_count = len(self.winning_tiles)
        self.effective_draws = self._calculate_effective_draws()
        self.score = self._calculate_score()
    
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
        """生成游戏建议"""
        suggestions = []
        
        if not discard_analyses:
            return ["无可用分析"]
        
        best_analysis = discard_analyses[0]
        
        # 花猪检查
        if player_state.is_flower_pig():
            suggestions.append("⚠️ 当前为花猪状态，需要赔付其他玩家")
            return suggestions
        
        # 听牌状态
        if best_analysis.shanten == 0:
            suggestions.append(f"🎯 已听牌! 胡牌张: {[str(tile) for tile in best_analysis.winning_tiles]}")
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
        
        # 定缺检查
        if player_state.missing_suit:
            missing_tiles = [tile for tile in player_state.hand_tiles if tile.suit == player_state.missing_suit]
            if missing_tiles:
                suggestions.append(f"⚠️ 发现定缺{player_state.missing_suit.value}的牌: {[str(tile) for tile in missing_tiles]}")
        
        return suggestions
    
    @staticmethod
    def simulate_draw_tile(player_state: PlayerState, draw_tile: Tile, known_tiles: List[Tile] = None) -> Dict[str, Any]:
        """
        模拟摸牌后的最佳出牌
        
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
        
        # 检查是否为定缺牌(必须打出)
        if player_state.missing_suit and draw_tile.suit == player_state.missing_suit:
            return {
                "action": "discard",
                "discard_tile": str(draw_tile),
                "forced": True,
                "message": f"🔒 定缺牌必须打出: {draw_tile}"
            }
        
        # 分析最佳出牌
        analysis = HandAnalyzer.analyze_discard_options(new_tiles, player_state.melds)
        
        return {
            "action": "discard",
            "discard_tile": str(analysis[0].discard_tile),
            "forced": False,
            "analysis": analysis[0],
            "message": f"💡 建议打出: {analysis[0].discard_tile}"
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