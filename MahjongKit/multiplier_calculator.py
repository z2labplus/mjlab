#!/usr/bin/env python3
"""
SichuanMahjongKit Multiplier Calculator
血战到底麻将库倍数计算器

实现血战到底麻将的番型检测和倍数计算系统
"""

from typing import Dict, List, Callable, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum

from .core import Tile, TilesConverter, SuitType, PlayerState, Meld, MeldType
from .fixed_validator import WinValidator


@dataclass
class WinContext:
    """胜利上下文信息 - 用于特殊番型检测"""
    win_tile: Optional[Tile] = None      # 胡牌张
    is_zimo: bool = False                # 自摸
    is_gang_flower: bool = False         # 杠上开花
    is_gang_pao: bool = False           # 杠上炮
    is_rob_kong: bool = False           # 抢杠胡
    is_sea_bottom: bool = False         # 海底捞月
    is_river_bottom: bool = False       # 河底捞鱼
    is_tianhu: bool = False             # 天胡
    is_dihu: bool = False               # 地胡
    is_golden_hook: bool = False        # 金钩钓
    kong_count: int = 0                 # 杠数
    gen_count: int = 0                  # 根数
    is_qing_yise: bool = False          # 清一色标记
    hand_tile_count: int = 14           # 手牌数


@dataclass
class FanPattern:
    """番型定义"""
    name: str                           # 番型名称
    multiplier: int                     # 倍数
    check_func: Callable                # 检测函数
    excludes: List[str]                 # 互斥番型
    description: str                    # 描述


class MultiplierCalculator:
    """倍数计算器 - 严格按照血战到底规则"""
    
    # 番型定义表（按倍数从高到低排序）
    FAN_PATTERNS = [
        # 超高倍番型 (256倍)
        FanPattern("清十八罗汉", 256, 
                  lambda h, m, c: MultiplierCalculator._is_qing_shiba_luohan(h, m, c),
                  ["清一色", "十八罗汉", "十二金钗", "清金钩钓", "金钩钓", "清碰", "碰碰胡", "根"],
                  "清一色+十八罗汉"),
        
        # 极高倍番型 (128倍)
        FanPattern("将三龙七对", 128,
                  lambda h, m, c: MultiplierCalculator._is_jiang_san_long_qidui(h, m, c),
                  ["七对", "将七对", "龙七对", "双龙七对", "将双龙七对", "三龙七对", "根", "断么九"],
                  "全部是2、5、8的三龙七对"),
        
        # 很高倍番型 (64倍)
        FanPattern("将双龙七对", 64,
                  lambda h, m, c: MultiplierCalculator._is_jiang_shuang_long_qidui(h, m, c),
                  ["七对", "将七对", "龙七对", "双龙七对", "根", "断么九"],
                  "全部是2、5、8的双龙七对"),
        
        FanPattern("十八罗汉", 64,
                  lambda h, m, c: MultiplierCalculator._is_shiba_luohan(h, m, c),
                  ["4根", "金钩钓", "碰碰胡", "十二金钗", "根"],
                  "金钩钓且有4个杠"),
        
        # 高倍番型 (32倍)
        FanPattern("天胡", 32,
                  lambda h, m, c: c.is_tianhu,
                  [],
                  "庄家发完牌后立即胡牌"),
        
        FanPattern("地胡", 32,
                  lambda h, m, c: c.is_dihu,
                  [],
                  "非庄家第一轮摸牌就胡牌"),
        
        FanPattern("清龙七对", 32,
                  lambda h, m, c: MultiplierCalculator._is_qing_long_qidui(h, m, c),
                  ["清一色", "龙七对", "七对", "根"],
                  "清一色+龙七对"),
        
        FanPattern("三龙七对", 32,
                  lambda h, m, c: MultiplierCalculator._is_san_long_qidui(h, m, c),
                  ["七对", "龙七对", "双龙七对", "根"],
                  "七对且有3组4张相同的牌"),
        
        # 中倍番型 (16倍)
        FanPattern("清七对", 16,
                  lambda h, m, c: MultiplierCalculator._is_qing_qidui(h, m, c),
                  ["清一色", "七对"],
                  "清一色+七对"),
        
        FanPattern("清金钩钓", 16,
                  lambda h, m, c: MultiplierCalculator._is_qing_golden_hook(h, m, c),
                  ["清一色", "金钩钓", "碰碰胡"],
                  "清一色+金钩钓"),
        
        FanPattern("将七对", 16,
                  lambda h, m, c: MultiplierCalculator._is_jiang_qidui(h, m, c),
                  ["七对", "断么九"],
                  "全部是2、5、8的七对"),
        
        FanPattern("双龙七对", 16,
                  lambda h, m, c: MultiplierCalculator._is_shuang_long_qidui(h, m, c),
                  ["龙七对", "七对", "根"],
                  "七对且有2组4张相同的牌"),
        
        FanPattern("十二金钗", 16,
                  lambda h, m, c: MultiplierCalculator._is_shi_er_jin_chai(h, m, c),
                  ["3根", "金钩钓", "碰碰胡", "根"],
                  "金钩钓且有3个杠"),
        
        # 低中倍番型 (8倍)
        FanPattern("清碰", 8,
                  lambda h, m, c: MultiplierCalculator._is_qing_peng(h, m, c),
                  ["碰碰胡", "清一色"],
                  "清一色+碰碰胡"),
        
        FanPattern("龙七对", 8,
                  lambda h, m, c: MultiplierCalculator._is_long_qidui(h, m, c),
                  ["七对", "1根"],
                  "七对且有1组4张相同的牌"),
        
        FanPattern("将对", 8,
                  lambda h, m, c: MultiplierCalculator._is_jiang_dui(h, m, c),
                  ["碰碰胡", "断么九"],
                  "全部是2、5、8的碰碰胡"),
        
        FanPattern("八仙过海", 8,
                  lambda h, m, c: MultiplierCalculator._is_ba_xian_guo_hai(h, m, c),
                  ["2根", "金钩钓", "碰碰胡", "根"],
                  "金钩钓且有2个杠"),
        
        # 基础番型 (4倍)
        FanPattern("清一色", 4,
                  lambda h, m, c: MultiplierCalculator._is_qingyise(h, m, c),
                  [],
                  "全部由同一花色组成"),
        
        FanPattern("七对", 4,
                  lambda h, m, c: MultiplierCalculator._is_qidui(h, m, c),
                  [],
                  "由七个对子组成"),
        
        FanPattern("金钩钓", 4,
                  lambda h, m, c: MultiplierCalculator._is_golden_hook(h, m, c),
                  ["碰碰胡"],
                  "只剩一张牌单钓胡牌"),
        
        FanPattern("幺九", 4,
                  lambda h, m, c: MultiplierCalculator._is_yaojiu(h, m, c),
                  [],
                  "每个面子都包含1、9"),
        
        # 低倍番型 (2倍)
        FanPattern("碰碰胡", 2,
                  lambda h, m, c: MultiplierCalculator._is_pengpenghu(h, m, c),
                  [],
                  "由4个刻子和将牌组成"),
        
        FanPattern("断么九", 2,
                  lambda h, m, c: MultiplierCalculator._is_duanyaojiu(h, m, c),
                  [],
                  "手牌中没有1、9"),
        
        # 默认番型 (1倍)
        FanPattern("平胡", 1,
                  lambda h, m, c: True,  # 默认番型
                  [],
                  "基本胡牌")
    ]
    
    @staticmethod
    def calculate(hand_tiles: List[Tile], melds: List[Meld], 
                 win_context: WinContext) -> Dict[str, Any]:
        """
        计算胡牌倍数
        
        Args:
            hand_tiles: 手牌列表
            melds: 副露列表
            win_context: 胡牌上下文
            
        Returns:
            {'multiplier': int, 'patterns': List[str], 'details': Dict}
        """
        # 转换为27位数组便于计算
        tiles_array = TilesConverter.tiles_to_27_array(hand_tiles)
        
        # 更新上下文信息
        win_context = MultiplierCalculator._update_context(tiles_array, melds, win_context)
        
        # 1. 主番型判定（取第一个匹配的最高倍数番型）
        main_pattern = None
        for pattern in MultiplierCalculator.FAN_PATTERNS:
            if pattern.check_func(tiles_array, melds, win_context):
                main_pattern = pattern
                break
        
        if main_pattern is None:
            main_pattern = MultiplierCalculator.FAN_PATTERNS[-1]  # 平胡
        
        base_multiplier = main_pattern.multiplier
        patterns = [main_pattern.name]
        
        # 2. 计算附加倍数（x2类型）
        additional_multiplier = 1
        additional_patterns = []
        
        if win_context.is_zimo:
            additional_multiplier *= 2
            additional_patterns.append("自摸")
        
        if win_context.is_gang_flower:
            additional_multiplier *= 2
            additional_patterns.append("杠上开花")
        
        if win_context.is_gang_pao:
            additional_multiplier *= 2
            additional_patterns.append("杠上炮")
        
        if win_context.is_rob_kong:
            additional_multiplier *= 2
            additional_patterns.append("抢杠胡")
        
        if win_context.is_sea_bottom:
            additional_multiplier *= 2
            additional_patterns.append("海底捞月")
        
        if win_context.is_river_bottom:
            additional_multiplier *= 2
            additional_patterns.append("河底捞鱼")
        
        # 3. 计算根倍数（每根x2，但要排除主番型已计算的根）
        effective_gen_count = win_context.gen_count
        
        # 特殊处理：某些番型不计根或部分根
        if main_pattern.name in ["龙七对"]:
            effective_gen_count = max(0, win_context.gen_count - 1)  # 龙七对不计1根
        elif main_pattern.name in ["双龙七对"]:
            effective_gen_count = max(0, win_context.gen_count - 2)  # 双龙七对不计2根
        elif main_pattern.name in ["三龙七对"]:
            effective_gen_count = max(0, win_context.gen_count - 3)  # 三龙七对不计3根
        elif "根" in main_pattern.excludes:
            effective_gen_count = 0  # 完全不计根
        
        gen_multiplier = 2 ** effective_gen_count
        
        # 4. 计算最终倍数
        total_multiplier = base_multiplier * additional_multiplier * gen_multiplier
        
        all_patterns = patterns + additional_patterns
        if effective_gen_count > 0:
            all_patterns.append(f"{effective_gen_count}根")
        
        return {
            'multiplier': total_multiplier,
            'patterns': all_patterns,
            'details': {
                'main_pattern': main_pattern.name,
                'base_multiplier': base_multiplier,
                'additional_multiplier': additional_multiplier,
                'gen_multiplier': gen_multiplier,
                'effective_gen_count': effective_gen_count,
                'total_kong_count': win_context.kong_count,
                'total_gen_count': win_context.gen_count
            }
        }
    
    @staticmethod
    def _update_context(tiles_array: List[int], melds: List[Meld], 
                       context: WinContext) -> WinContext:
        """更新胜利上下文信息"""
        # 计算杠数
        kong_count = sum(1 for meld in melds if meld.is_kong())
        context.kong_count = kong_count
        
        # 计算根数（4张相同的牌）
        gen_count = 0
        for count in tiles_array:
            if count == 4:
                gen_count += 1
        
        # 加上杠的根数
        gen_count += kong_count
        context.gen_count = gen_count
        
        # 检查是否清一色
        context.is_qing_yise = MultiplierCalculator._is_qingyise(tiles_array, melds, context)
        
        # 检查是否金钩钓
        hand_tile_count = sum(tiles_array)
        context.is_golden_hook = (hand_tile_count == 2 and len(melds) >= 4)
        
        return context
    
    # ==================== 番型检测函数 ====================
    
    @staticmethod
    def _is_qingyise(tiles_array: List[int], melds: List[Meld], context: WinContext) -> bool:
        """清一色：全部由同一花色组成"""
        suits_used = set()
        
        # 检查手牌
        for i, count in enumerate(tiles_array):
            if count > 0:
                if i < 9: suits_used.add('m')
                elif i < 18: suits_used.add('s')
                else: suits_used.add('p')
        
        # 检查副露
        for meld in melds:
            suits_used.add(meld.get_suit().value)
        
        return len(suits_used) == 1
    
    @staticmethod
    def _is_qidui(tiles_array: List[int], melds: List[Meld], context: WinContext) -> bool:
        """七对：由七个对子组成"""
        # 副露时不能是七对
        if melds:
            return False
        
        # 检查是否总牌数为14张
        total_tiles = sum(tiles_array)
        if total_tiles != 14:
            return False
        
        pairs = 0
        for count in tiles_array:
            if count == 2:
                pairs += 1
            elif count == 4:  # 4张相同的牌算2对
                pairs += 2
            elif count != 0:
                return False
        
        return pairs == 7
    
    @staticmethod
    def _is_pengpenghu(tiles_array: List[int], melds: List[Meld], context: WinContext) -> bool:
        """碰碰胡：由4个刻子和将牌组成"""
        # 手牌应该只有2张（将牌），其余都是刻子/杠
        total_hand_tiles = sum(tiles_array)
        if total_hand_tiles != 2:
            return False
        
        # 检查所有副露都是刻子或杠
        pong_kong_count = 0
        for meld in melds:
            if meld.type == MeldType.PENG or meld.is_kong():
                pong_kong_count += 1
            else:
                return False
        
        # 需要4组面子
        return pong_kong_count == 4
    
    @staticmethod
    def _is_golden_hook(tiles_array: List[int], melds: List[Meld], context: WinContext) -> bool:
        """金钩钓：只剩一张牌单钓胡牌"""
        total_hand_tiles = sum(tiles_array)
        # 2张手牌（将牌）+4组副露，且必须是碰碰胡
        return (total_hand_tiles == 2 and len(melds) >= 4 and 
                MultiplierCalculator._is_pengpenghu(tiles_array, melds, context))
    
    @staticmethod
    def _is_duanyaojiu(tiles_array: List[int], melds: List[Meld], context: WinContext) -> bool:
        """断么九：手牌中没有1、9"""
        # 检查手牌中的1、9
        for i in [0, 8, 9, 17, 18, 26]:  # 1m, 9m, 1s, 9s, 1p, 9p
            if tiles_array[i] > 0:
                return False
        
        # 检查副露中的1、9
        for meld in melds:
            for tile in meld.tiles:
                if tile.value in [1, 9]:
                    return False
        
        return True
    
    @staticmethod
    def _is_yaojiu(tiles_array: List[int], melds: List[Meld], context: WinContext) -> bool:
        """幺九：每个面子都包含1、9"""
        # 简化实现：检查是否有足够的1、9牌
        yaojiu_count = 0
        for i in [0, 8, 9, 17, 18, 26]:  # 1m, 9m, 1s, 9s, 1p, 9p
            yaojiu_count += tiles_array[i]
        
        # 检查副露中的1、9
        for meld in melds:
            for tile in meld.tiles:
                if tile.value in [1, 9]:
                    yaojiu_count += 1
        
        # 每个面子至少要有一张1或9，需要至少5张（4个面子+1个将牌可能）
        return yaojiu_count >= 5
    
    # ==================== 组合番型检测 ====================
    
    @staticmethod
    def _is_qing_qidui(tiles_array: List[int], melds: List[Meld], context: WinContext) -> bool:
        """清七对：清一色+七对"""
        return (MultiplierCalculator._is_qingyise(tiles_array, melds, context) and
                MultiplierCalculator._is_qidui(tiles_array, melds, context))
    
    @staticmethod
    def _is_qing_peng(tiles_array: List[int], melds: List[Meld], context: WinContext) -> bool:
        """清碰：清一色+碰碰胡"""
        return (MultiplierCalculator._is_qingyise(tiles_array, melds, context) and
                MultiplierCalculator._is_pengpenghu(tiles_array, melds, context))
    
    @staticmethod
    def _is_qing_golden_hook(tiles_array: List[int], melds: List[Meld], context: WinContext) -> bool:
        """清金钩钓：清一色+金钩钓"""
        return (MultiplierCalculator._is_qingyise(tiles_array, melds, context) and
                MultiplierCalculator._is_golden_hook(tiles_array, melds, context))
    
    # ==================== 龙七对系列番型 ====================
    
    @staticmethod
    def _is_long_qidui(tiles_array: List[int], melds: List[Meld], context: WinContext) -> bool:
        """龙七对：七对且有1组4张相同的牌"""
        if not MultiplierCalculator._is_qidui(tiles_array, melds, context):
            return False
        
        # 检查是否有1组4张相同的牌
        long_count = sum(1 for count in tiles_array if count == 4)
        return long_count == 1
    
    @staticmethod
    def _is_shuang_long_qidui(tiles_array: List[int], melds: List[Meld], context: WinContext) -> bool:
        """双龙七对：七对且有2组4张相同的牌"""
        if not MultiplierCalculator._is_qidui(tiles_array, melds, context):
            return False
        
        # 检查是否有2组4张相同的牌
        long_count = sum(1 for count in tiles_array if count == 4)
        return long_count == 2
    
    @staticmethod
    def _is_san_long_qidui(tiles_array: List[int], melds: List[Meld], context: WinContext) -> bool:
        """三龙七对：七对且有3组4张相同的牌"""
        if not MultiplierCalculator._is_qidui(tiles_array, melds, context):
            return False
        
        # 检查是否有3组4张相同的牌
        long_count = sum(1 for count in tiles_array if count == 4)
        return long_count == 3
    
    @staticmethod
    def _is_qing_long_qidui(tiles_array: List[int], melds: List[Meld], context: WinContext) -> bool:
        """清龙七对：清一色+龙七对"""
        return (MultiplierCalculator._is_qingyise(tiles_array, melds, context) and
                MultiplierCalculator._is_long_qidui(tiles_array, melds, context))
    
    # ==================== 将军系列番型 ====================
    
    @staticmethod
    def _is_jiang_tile(tile_value: int) -> bool:
        """检查是否为将牌（2、5、8）"""
        return tile_value in [2, 5, 8]
    
    @staticmethod
    def _is_jiang_qidui(tiles_array: List[int], melds: List[Meld], context: WinContext) -> bool:
        """将七对：全部是2、5、8的七对"""
        if not MultiplierCalculator._is_qidui(tiles_array, melds, context):
            return False
        
        # 检查所有牌都是2、5、8
        for i, count in enumerate(tiles_array):
            if count > 0:
                value = (i % 9) + 1
                if not MultiplierCalculator._is_jiang_tile(value):
                    return False
        
        return True
    
    @staticmethod
    def _is_jiang_shuang_long_qidui(tiles_array: List[int], melds: List[Meld], context: WinContext) -> bool:
        """将双龙七对：全部是2、5、8的双龙七对"""
        return (MultiplierCalculator._is_jiang_qidui(tiles_array, melds, context) and
                MultiplierCalculator._is_shuang_long_qidui(tiles_array, melds, context))
    
    @staticmethod
    def _is_jiang_san_long_qidui(tiles_array: List[int], melds: List[Meld], context: WinContext) -> bool:
        """将三龙七对：全部是2、5、8的三龙七对"""
        return (MultiplierCalculator._is_jiang_qidui(tiles_array, melds, context) and
                MultiplierCalculator._is_san_long_qidui(tiles_array, melds, context))
    
    @staticmethod
    def _is_jiang_dui(tiles_array: List[int], melds: List[Meld], context: WinContext) -> bool:
        """将对：全部是2、5、8的碰碰胡"""
        if not MultiplierCalculator._is_pengpenghu(tiles_array, melds, context):
            return False
        
        # 检查手牌中的将牌
        for i, count in enumerate(tiles_array):
            if count > 0:
                value = (i % 9) + 1
                if not MultiplierCalculator._is_jiang_tile(value):
                    return False
        
        # 检查副露中的将牌
        for meld in melds:
            for tile in meld.tiles:
                if not MultiplierCalculator._is_jiang_tile(tile.value):
                    return False
        
        return True
    
    # ==================== 杠系列番型 ====================
    
    @staticmethod
    def _is_ba_xian_guo_hai(tiles_array: List[int], melds: List[Meld], context: WinContext) -> bool:
        """八仙过海：金钩钓且有2个杠"""
        return (MultiplierCalculator._is_golden_hook(tiles_array, melds, context) and
                context.kong_count == 2)
    
    @staticmethod
    def _is_shi_er_jin_chai(tiles_array: List[int], melds: List[Meld], context: WinContext) -> bool:
        """十二金钗：金钩钓且有3个杠"""
        return (MultiplierCalculator._is_golden_hook(tiles_array, melds, context) and
                context.kong_count == 3)
    
    @staticmethod
    def _is_shiba_luohan(tiles_array: List[int], melds: List[Meld], context: WinContext) -> bool:
        """十八罗汉：金钩钓且有4个杠"""
        return (MultiplierCalculator._is_golden_hook(tiles_array, melds, context) and
                context.kong_count == 4)
    
    @staticmethod
    def _is_qing_shiba_luohan(tiles_array: List[int], melds: List[Meld], context: WinContext) -> bool:
        """清十八罗汉：清一色+十八罗汉"""
        return (MultiplierCalculator._is_qingyise(tiles_array, melds, context) and
                MultiplierCalculator._is_shiba_luohan(tiles_array, melds, context))


if __name__ == "__main__":
    # 简单测试
    from .core import Tile, SuitType
    
    print("=== MultiplierCalculator 测试 ===")
    
    # 测试清一色
    tiles = [Tile(SuitType.WAN, i) for i in [1,1,2,2,3,3,4,4,5,5,6,6,7,7]]
    context = WinContext()
    
    tiles_array = TilesConverter.tiles_to_27_array(tiles)
    result = MultiplierCalculator.calculate(tiles, [], context)
    
    print(f"清七对测试: {result}")