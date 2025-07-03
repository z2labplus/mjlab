# SichuanMahjongKit 血战到底麻将库设计方案 

## 基于日本立直麻将库架构的血战到底麻将完整实现方案

### 项目概述

借鉴 [MahjongRepository/mahjong](https://github.com/MahjongRepository/mahjong) 的成熟架构设计，为血战到底麻将规则实现一个高性能、高精度的Python计算库。

### 核心设计理念

1. **模块化架构** - 每个核心功能独立成模块，便于测试和维护
2. **多重数据表示** - 支持多种牌的表示格式，适应不同计算需求
3. **层级化算法** - 复杂逻辑分层实现，提高代码可读性和性能
4. **规则驱动设计** - 严格按照血战到底规则实现，确保100%准确性

---

## 模块一：核心数据结构与转换器 (Core Data & Converters)

### 1.1 Tile 牌的表示

```python
from typing import Optional
from enum import Enum

class SuitType(Enum):
    WAN = 'm'      # 万
    TIAO = 's'     # 条
    TONG = 'p'     # 筒

class Tile:
    """单张麻将牌"""
    def __init__(self, suit: SuitType, value: int):
        self.suit = suit
        self.value = value  # 1-9
        self.id = self._calculate_id()
    
    def _calculate_id(self) -> int:
        """计算牌的唯一ID (0-26)"""
        base = {'m': 0, 's': 9, 'p': 18}
        return base[self.suit.value] + (self.value - 1)
    
    def __str__(self) -> str:
        return f"{self.value}{self.suit.value}"
```

### 1.2 TilesConverter 牌的格式转换器

参考日本库的多格式支持，实现灵活的数据转换：

```python
class TilesConverter:
    """牌的格式转换器，支持多种表示方法"""
    
    @staticmethod
    def string_to_27_array(tiles_string: str) -> List[int]:
        """字符串转27位频率数组
        例: "123m456s789p" -> [1,1,1,0,0,0,0,0,0, 1,1,1,0,0,0,0,0,0, 1,1,1,0,0,0,0,0,0]
        """
        tiles_array = [0] * 27
        current_suit = None
        numbers = []
        
        for char in tiles_string:
            if char.isdigit():
                numbers.append(int(char))
            elif char in ['m', 's', 'p']:
                current_suit = char
                for num in numbers:
                    tile_id = TilesConverter._get_tile_id(current_suit, num)
                    tiles_array[tile_id] += 1
                numbers = []
        
        return tiles_array
    
    @staticmethod
    def array_27_to_string(tiles_array: List[int]) -> str:
        """27位数组转字符串表示"""
        result = []
        suits = [('m', 0), ('s', 9), ('p', 18)]
        
        for suit_char, offset in suits:
            suit_tiles = []
            for i in range(9):
                count = tiles_array[offset + i]
                suit_tiles.extend([str(i + 1)] * count)
            
            if suit_tiles:
                result.append(''.join(suit_tiles) + suit_char)
        
        return ''.join(result)
    
    @staticmethod
    def array_27_to_108_array(tiles_array: List[int]) -> List[int]:
        """27位频率数组转108位详细数组（每种牌4张）"""
        tiles_108 = [0] * 108
        for i, count in enumerate(tiles_array):
            for j in range(count):
                tiles_108[i * 4 + j] = 1
        return tiles_108
```

### 1.3 Meld 副露（碰、杠）

```python
from enum import Enum
from typing import List, Optional

class MeldType(Enum):
    PONG = "pong"          # 碰
    EXPOSED_KONG = "kong"  # 明杠
    CONCEALED_KONG = "angang"  # 暗杠
    UPGRADED_KONG = "jiagang"  # 加杠（补杠）

class Meld:
    """副露牌组"""
    def __init__(self, meld_type: MeldType, tiles: List[Tile], 
                 from_player: Optional[int] = None):
        self.type = meld_type
        self.tiles = tiles
        self.from_player = from_player  # 被碰/杠的玩家索引
    
    def get_tile_value(self) -> int:
        """获取牌值"""
        return self.tiles[0].value
    
    def get_suit(self) -> SuitType:
        """获取花色"""
        return self.tiles[0].suit
    
    def is_kong(self) -> bool:
        """是否为杠"""
        return self.type in [MeldType.EXPOSED_KONG, MeldType.CONCEALED_KONG, MeldType.UPGRADED_KONG]
```

---

## 模块二：玩家状态管理 (Player State Management)

### 2.1 PlayerState 玩家状态

```python
from typing import Dict, List, Optional

class PlayerState:
    """玩家完整状态信息"""
    def __init__(self, player_id: int):
        self.player_id = player_id
        
        # 手牌信息
        self.hand_tiles: List[int] = [0] * 27  # 27位频率数组
        self.melds: List[Meld] = []
        
        # 游戏状态
        self.declared_void_suit: Optional[SuitType] = None  # 定缺花色
        self.has_won: bool = False
        self.is_ting: bool = False  # 听牌状态
        self.is_flowery_pig: bool = False  # 花猪状态
        
        # 收益统计
        self.kong_income: int = 0  # 杠牌收益
        self.win_info: Optional[Dict] = None  # 胡牌信息
    
    def add_hand_tile(self, tile: Tile):
        """添加手牌"""
        self.hand_tiles[tile.id] += 1
    
    def remove_hand_tile(self, tile: Tile) -> bool:
        """移除手牌"""
        if self.hand_tiles[tile.id] > 0:
            self.hand_tiles[tile.id] -= 1
            return True
        return False
    
    def get_total_tile_count(self) -> int:
        """获取总牌数（手牌+副露）"""
        hand_count = sum(self.hand_tiles)
        meld_count = sum(len(meld.tiles) for meld in self.melds)
        return hand_count + meld_count
    
    def has_suit_in_hand(self, suit: SuitType) -> bool:
        """检查手牌中是否有指定花色"""
        suit_offset = {'m': 0, 's': 9, 'p': 18}[suit.value]
        return any(self.hand_tiles[suit_offset + i] > 0 for i in range(9))
    
    def get_suit_types_count(self) -> int:
        """计算手牌和副露中的花色种类数"""
        suits_in_hand = set()
        
        # 检查手牌
        for i, count in enumerate(self.hand_tiles):
            if count > 0:
                if i < 9: suits_in_hand.add(SuitType.WAN)
                elif i < 18: suits_in_hand.add(SuitType.TIAO)
                else: suits_in_hand.add(SuitType.TONG)
        
        # 检查副露
        for meld in self.melds:
            suits_in_hand.add(meld.get_suit())
        
        return len(suits_in_hand)
```

---

## 模块三：胡牌与听牌判定器 (Win & Ting Validators)

### 3.1 WinValidator 胡牌判定器

借鉴日本库的分层检测逻辑：

```python
class WinValidator:
    """胡牌判定器 - 严格按照血战到底规则"""
    
    @staticmethod
    def is_win(hand_tiles: List[int], melds: List[Meld], 
               declared_void_suit: SuitType) -> bool:
        """
        判断是否胡牌
        核心规则：1）不超过2门花色 2）符合胡牌牌型
        """
        # 第一道检查：花色门数限制
        if not WinValidator._check_suit_limit(hand_tiles, melds):
            return False
        
        # 第二道检查：牌型结构
        return (WinValidator._check_seven_pairs(hand_tiles) or 
                WinValidator._check_standard_pattern(hand_tiles))
    
    @staticmethod
    def _check_suit_limit(hand_tiles: List[int], melds: List[Meld]) -> bool:
        """检查花色是否不超过2门"""
        suits_used = set()
        
        # 检查手牌
        for i, count in enumerate(hand_tiles):
            if count > 0:
                if i < 9: suits_used.add(SuitType.WAN)
                elif i < 18: suits_used.add(SuitType.TIAO)
                else: suits_used.add(SuitType.TONG)
        
        # 检查副露
        for meld in melds:
            suits_used.add(meld.get_suit())
        
        return len(suits_used) <= 2
    
    @staticmethod
    def _check_seven_pairs(hand_tiles: List[int]) -> bool:
        """检查七对牌型（包括龙七对变种）"""
        pairs_count = 0
        for count in hand_tiles:
            if count == 2:
                pairs_count += 1
            elif count == 4:  # 龙七对：4张同牌算2对
                pairs_count += 2
            elif count != 0:  # 其他数量不符合七对
                return False
        
        return pairs_count == 7
    
    @staticmethod
    def _check_standard_pattern(hand_tiles: List[int]) -> bool:
        """检查标准牌型：4组面子+1对将牌"""
        # 使用递归搜索算法，类似日本库的实现
        return WinValidator._recursive_check(hand_tiles[:], 0, 0)
    
    @staticmethod
    def _recursive_check(hand_tiles: List[int], meld_count: int, pair_count: int) -> bool:
        """递归检查标准牌型"""
        # 找到第一张有牌的位置
        pos = -1
        for i in range(27):
            if hand_tiles[i] > 0:
                pos = i
                break
        
        if pos == -1:  # 没有牌了
            return meld_count == 4 and pair_count == 1
        
        tile_count = hand_tiles[pos]
        
        # 尝试作为刻子
        if tile_count >= 3:
            hand_tiles[pos] -= 3
            if WinValidator._recursive_check(hand_tiles, meld_count + 1, pair_count):
                hand_tiles[pos] += 3
                return True
            hand_tiles[pos] += 3
        
        # 尝试作为将牌
        if tile_count >= 2 and pair_count == 0:
            hand_tiles[pos] -= 2
            if WinValidator._recursive_check(hand_tiles, meld_count, pair_count + 1):
                hand_tiles[pos] += 2
                return True
            hand_tiles[pos] += 2
        
        # 尝试作为顺子（只在同花色内）
        if pos % 9 <= 6:  # 确保后面还有两张牌的空间
            if (hand_tiles[pos] > 0 and 
                hand_tiles[pos + 1] > 0 and 
                hand_tiles[pos + 2] > 0):
                hand_tiles[pos] -= 1
                hand_tiles[pos + 1] -= 1
                hand_tiles[pos + 2] -= 1
                if WinValidator._recursive_check(hand_tiles, meld_count + 1, pair_count):
                    hand_tiles[pos] += 1
                    hand_tiles[pos + 1] += 1
                    hand_tiles[pos + 2] += 1
                    return True
                hand_tiles[pos] += 1
                hand_tiles[pos + 1] += 1
                hand_tiles[pos + 2] += 1
        
        return False
```

### 3.2 TingValidator 听牌判定器

```python
class TingValidator:
    """听牌判定器"""
    
    @staticmethod
    def get_ting_tiles(player_state: PlayerState) -> List[Tile]:
        """获取听牌列表"""
        # 预先检查：如果已经是花猪，不可能听牌
        if player_state.get_suit_types_count() >= 3:
            return []
        
        ting_tiles = []
        hand_tiles = player_state.hand_tiles[:]
        
        # 遍历所有可能的牌 (0-26)
        for tile_id in range(27):
            # 临时添加这张牌
            hand_tiles[tile_id] += 1
            
            # 检查是否胡牌
            if WinValidator.is_win(hand_tiles, player_state.melds, 
                                 player_state.declared_void_suit):
                # 构造Tile对象
                suit = [SuitType.WAN] * 9 + [SuitType.TIAO] * 9 + [SuitType.TONG] * 9
                value = (tile_id % 9) + 1
                ting_tiles.append(Tile(suit[tile_id], value))
            
            # 移除临时添加的牌
            hand_tiles[tile_id] -= 1
        
        return ting_tiles
    
    @staticmethod
    def is_ting(player_state: PlayerState) -> bool:
        """判断是否听牌"""
        return len(TingValidator.get_ting_tiles(player_state)) > 0
```

---

## 模块四：向听数计算器 (Shanten Calculator)

### 4.1 ShantenCalculator 向听数计算

参考日本库的递归搜索算法，适配血战到底规则：

```python
class ShantenCalculator:
    """向听数计算器 - 适配血战到底规则"""
    
    @staticmethod
    def calculate_shanten(player_state: PlayerState) -> int:
        """
        计算向听数
        血战到底特殊规则：
        1. 必须先打完定缺牌
        2. 不能超过2门花色
        """
        hand_tiles = player_state.hand_tiles[:]
        
        # 计算定缺牌数量（必须先打掉）
        void_tiles_count = ShantenCalculator._count_void_tiles(
            hand_tiles, player_state.declared_void_suit)
        
        # 移除定缺牌，计算剩余牌的向听数
        ShantenCalculator._remove_void_tiles(hand_tiles, player_state.declared_void_suit)
        
        # 计算标准向听数和七对向听数，取最小值
        standard_shanten = ShantenCalculator._calculate_standard_shanten(hand_tiles)
        pairs_shanten = ShantenCalculator._calculate_seven_pairs_shanten(hand_tiles)
        
        min_shanten = min(standard_shanten, pairs_shanten)
        
        # 加上必须打掉的定缺牌数
        return min_shanten + void_tiles_count
    
    @staticmethod
    def _count_void_tiles(hand_tiles: List[int], void_suit: SuitType) -> int:
        """计算定缺牌数量"""
        if void_suit is None:
            return 0
        
        suit_offset = {'m': 0, 's': 9, 'p': 18}[void_suit.value]
        return sum(hand_tiles[suit_offset + i] for i in range(9))
    
    @staticmethod
    def _remove_void_tiles(hand_tiles: List[int], void_suit: SuitType):
        """移除定缺牌"""
        if void_suit is None:
            return
        
        suit_offset = {'m': 0, 's': 9, 'p': 18}[void_suit.value]
        for i in range(9):
            hand_tiles[suit_offset + i] = 0
    
    @staticmethod
    def _calculate_standard_shanten(hand_tiles: List[int]) -> int:
        """计算标准牌型向听数"""
        return ShantenCalculator._recursive_shanten_search(hand_tiles[:], 0, 0, 0)
    
    @staticmethod
    def _recursive_shanten_search(hand_tiles: List[int], meld_count: int, 
                                 pair_count: int, isolated_count: int) -> int:
        """递归搜索最小向听数"""
        # 找到第一张有牌的位置
        pos = -1
        for i in range(27):
            if hand_tiles[i] > 0:
                pos = i
                break
        
        if pos == -1:  # 没有牌了
            # 标准牌型需要4组面子+1对将牌
            need_melds = 4 - meld_count
            need_pairs = 1 - pair_count
            return need_melds + need_pairs
        
        min_shanten = float('inf')
        tile_count = hand_tiles[pos]
        
        # 尝试作为刻子
        if tile_count >= 3:
            hand_tiles[pos] -= 3
            shanten = ShantenCalculator._recursive_shanten_search(
                hand_tiles, meld_count + 1, pair_count, isolated_count)
            min_shanten = min(min_shanten, shanten)
            hand_tiles[pos] += 3
        
        # 尝试作为将牌
        if tile_count >= 2 and pair_count == 0:
            hand_tiles[pos] -= 2
            shanten = ShantenCalculator._recursive_shanten_search(
                hand_tiles, meld_count, pair_count + 1, isolated_count)
            min_shanten = min(min_shanten, shanten)
            hand_tiles[pos] += 2
        
        # 尝试作为顺子
        if pos % 9 <= 6:
            if (hand_tiles[pos] > 0 and 
                hand_tiles[pos + 1] > 0 and 
                hand_tiles[pos + 2] > 0):
                hand_tiles[pos] -= 1
                hand_tiles[pos + 1] -= 1
                hand_tiles[pos + 2] -= 1
                shanten = ShantenCalculator._recursive_shanten_search(
                    hand_tiles, meld_count + 1, pair_count, isolated_count)
                min_shanten = min(min_shanten, shanten)
                hand_tiles[pos] += 1
                hand_tiles[pos + 1] += 1
                hand_tiles[pos + 2] += 1
        
        # 跳过这张牌（作为孤张处理）
        hand_tiles[pos] -= 1
        shanten = ShantenCalculator._recursive_shanten_search(
            hand_tiles, meld_count, pair_count, isolated_count + 1)
        min_shanten = min(min_shanten, shanten + 1)  # 孤张需要额外的向听数
        hand_tiles[pos] += 1
        
        return min_shanten
    
    @staticmethod
    def _calculate_seven_pairs_shanten(hand_tiles: List[int]) -> int:
        """计算七对向听数"""
        pairs = 0
        isolated = 0
        
        for count in hand_tiles:
            if count >= 2:
                pairs += count // 2
            if count % 2 == 1:
                isolated += 1
        
        # 七对需要7个对子
        if pairs >= 7:
            return 0
        
        # 需要的对子数 - 现有对子数，但要考虑孤张
        need_pairs = 7 - pairs
        available_isolated = min(isolated, need_pairs)
        
        return need_pairs - available_isolated
```

---

## 模块五：倍数计算器 (Multiplier Calculator)

### 5.1 MultiplierCalculator 倍数计算系统

采用分层检测和互斥规则的设计模式：

```python
from typing import Dict, List, Callable, Any
from dataclasses import dataclass

@dataclass
class WinContext:
    """胜利上下文信息"""
    is_zimo: bool = False           # 自摸
    is_gang_flower: bool = False     # 杠上开花
    is_gang_pao: bool = False       # 杠上炮
    is_rob_kong: bool = False       # 抢杠胡
    is_sea_bottom: bool = False     # 海底捞月
    is_tianhu: bool = False         # 天胡
    is_dihu: bool = False           # 地胡
    is_golden_hook: bool = False    # 金钩钓
    kong_count: int = 0             # 杠数
    gen_count: int = 0              # 根数

@dataclass
class FanPattern:
    """番型定义"""
    name: str
    multiplier: int
    check_func: Callable[[List[int], List[Meld], Any], bool]
    excludes: List[str]
    description: str

class MultiplierCalculator:
    """倍数计算器 - 严格按照血战到底规则"""
    
    # 番型定义表（按倍数从高到低排序）
    FAN_PATTERNS = [
        FanPattern("清十八罗汉", 256, 
                  lambda h, m, c: MultiplierCalculator._is_qing_shiba_luohan(h, m, c),
                  ["清一色", "十八罗汉", "十二金钗", "清金钩钓", "金钩钓", "清碰", "碰碰胡", "根"],
                  "清一色+十八罗汉"),
        
        FanPattern("将三龙七对", 128,
                  lambda h, m, c: MultiplierCalculator._is_jiang_san_long_qidui(h, m, c),
                  ["七对", "将七对", "龙七对", "双龙七对", "将双龙七对", "三龙七对", "根", "断么九"],
                  "全部是2、5、8的三龙七对"),
        
        FanPattern("将双龙七对", 64,
                  lambda h, m, c: MultiplierCalculator._is_jiang_shuang_long_qidui(h, m, c),
                  ["七对", "将七对", "龙七对", "双龙七对", "根", "断么九"],
                  "全部是2、5、8的双龙七对"),
        
        FanPattern("十八罗汉", 64,
                  lambda h, m, c: MultiplierCalculator._is_shiba_luohan(h, m, c),
                  ["4根", "金钩钓", "碰碰胡", "十二金钗", "根"],
                  "金钩钓且有4个杠"),
        
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
        
        FanPattern("碰碰胡", 2,
                  lambda h, m, c: MultiplierCalculator._is_pengpenghu(h, m, c),
                  [],
                  "由4个刻子和将牌组成"),
        
        FanPattern("断么九", 2,
                  lambda h, m, c: MultiplierCalculator._is_duanyaojiu(h, m, c),
                  [],
                  "手牌中没有1、9"),
        
        FanPattern("平胡", 1,
                  lambda h, m, c: True,  # 默认番型
                  [],
                  "基本胡牌")
    ]
    
    @staticmethod
    def calculate(hand_tiles: List[int], melds: List[Meld], 
                 win_tile: Tile, context: WinContext) -> Dict[str, Any]:
        """
        计算胡牌倍数
        返回：{'multiplier': int, 'patterns': List[str], 'details': Dict}
        """
        # 1. 主番型判定（取第一个匹配的最高倍数番型）
        main_pattern = None
        for pattern in MultiplierCalculator.FAN_PATTERNS:
            if pattern.check_func(hand_tiles, melds, context):
                main_pattern = pattern
                break
        
        if main_pattern is None:
            main_pattern = MultiplierCalculator.FAN_PATTERNS[-1]  # 平胡
        
        base_multiplier = main_pattern.multiplier
        patterns = [main_pattern.name]
        
        # 2. 计算附加倍数（x2类型）
        additional_multiplier = 1
        additional_patterns = []
        
        if context.is_zimo:
            additional_multiplier *= 2
            additional_patterns.append("自摸")
        
        if context.is_gang_flower:
            additional_multiplier *= 2
            additional_patterns.append("杠上开花")
        
        if context.is_gang_pao:
            additional_multiplier *= 2
            additional_patterns.append("杠上炮")
        
        if context.is_rob_kong:
            additional_multiplier *= 2
            additional_patterns.append("抢杠胡")
        
        if context.is_sea_bottom:
            additional_multiplier *= 2
            additional_patterns.append("海底捞月")
        
        # 3. 计算根倍数（每根x2，但要排除主番型已计算的根）
        effective_gen_count = context.gen_count
        
        # 特殊处理：某些番型不计根或部分根
        if main_pattern.name in ["龙七对"]:
            effective_gen_count = max(0, context.gen_count - 1)  # 龙七对不计1根
        elif main_pattern.name in ["双龙七对"]:
            effective_gen_count = max(0, context.gen_count - 2)  # 双龙七对不计2根
        elif main_pattern.name in ["三龙七对"]:
            effective_gen_count = max(0, context.gen_count - 3)  # 三龙七对不计3根
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
                'effective_gen_count': effective_gen_count
            }
        }
    
    # 具体番型检测函数
    @staticmethod
    def _is_qingyise(hand_tiles: List[int], melds: List[Meld], context: WinContext) -> bool:
        """清一色：全部由同一花色组成"""
        suits_used = set()
        
        # 检查手牌
        for i, count in enumerate(hand_tiles):
            if count > 0:
                if i < 9: suits_used.add('m')
                elif i < 18: suits_used.add('s')
                else: suits_used.add('p')
        
        # 检查副露
        for meld in melds:
            suits_used.add(meld.get_suit().value)
        
        return len(suits_used) == 1
    
    @staticmethod
    def _is_qidui(hand_tiles: List[int], melds: List[Meld], context: WinContext) -> bool:
        """七对：由七个对子组成"""
        # 副露时不能是七对
        if melds:
            return False
        
        pairs = 0
        for count in hand_tiles:
            if count == 2:
                pairs += 1
            elif count == 4:  # 4张相同的牌算2对
                pairs += 2
            elif count != 0:
                return False
        
        return pairs == 7
    
    @staticmethod
    def _is_pengpenghu(hand_tiles: List[int], melds: List[Meld], context: WinContext) -> bool:
        """碰碰胡：由4个刻子和将牌组成"""
        # 简化版实现，实际需要更复杂的判定
        total_tiles = sum(hand_tiles)
        meld_tiles = sum(len(meld.tiles) for meld in melds)
        
        # 手牌应该只有2张（将牌），其余都是刻子/杠
        if total_tiles != 2:
            return False
        
        # 检查所有副露都是刻子或杠
        for meld in melds:
            if meld.type == MeldType.PONG or meld.is_kong():
                continue
            else:
                return False
        
        return True
    
    @staticmethod
    def _is_golden_hook(hand_tiles: List[int], melds: List[Meld], context: WinContext) -> bool:
        """金钩钓：只剩一张牌单钓胡牌"""
        total_hand_tiles = sum(hand_tiles)
        return total_hand_tiles == 2 and len(melds) >= 4  # 2张手牌（将牌）+4组副露
    
    # ... 其他番型检测函数的实现 ...
```

---

## 模块六：AI决策引擎 (AI Decision Engine)

### 6.1 HandAnalyzer AI打牌建议

```python
from typing import Tuple, Optional

class HandAnalyzer:
    """手牌分析器 - 提供AI打牌建议"""
    
    @staticmethod
    def suggest_discard(player_state: PlayerState) -> Optional[Tile]:
        """
        建议打牌
        血战到底特殊规则：
        1. 优先打定缺牌
        2. 避免成为花猪
        3. 追求最小向听数
        """
        hand_tiles = player_state.hand_tiles[:]
        
        # 第一优先级：必须打定缺牌
        void_tile = HandAnalyzer._get_void_tile(player_state)
        if void_tile:
            return void_tile
        
        # 第二优先级：避免花猪
        if player_state.get_suit_types_count() >= 3:
            return HandAnalyzer._avoid_flowery_pig(player_state)
        
        # 第三优先级：最优向听数策略
        return HandAnalyzer._optimize_shanten(player_state)
    
    @staticmethod
    def _get_void_tile(player_state: PlayerState) -> Optional[Tile]:
        """获取定缺牌（必须打的牌）"""
        if player_state.declared_void_suit is None:
            return None
        
        suit = player_state.declared_void_suit
        suit_offset = {'m': 0, 's': 9, 'p': 18}[suit.value]
        
        for i in range(9):
            if player_state.hand_tiles[suit_offset + i] > 0:
                return Tile(suit, i + 1)
        
        return None
    
    @staticmethod
    def _avoid_flowery_pig(player_state: PlayerState) -> Optional[Tile]:
        """避免花猪策略"""
        # 找到数量最少的花色，优先打掉
        suit_counts = {}
        for suit_type in [SuitType.WAN, SuitType.TIAO, SuitType.TONG]:
            count = HandAnalyzer._count_suit_tiles(player_state.hand_tiles, suit_type)
            if count > 0:
                suit_counts[suit_type] = count
        
        if len(suit_counts) >= 3:
            # 选择数量最少的花色
            min_suit = min(suit_counts.keys(), key=lambda s: suit_counts[s])
            # 返回该花色的第一张牌
            suit_offset = {'m': 0, 's': 9, 'p': 18}[min_suit.value]
            for i in range(9):
                if player_state.hand_tiles[suit_offset + i] > 0:
                    return Tile(min_suit, i + 1)
        
        return None
    
    @staticmethod
    def _optimize_shanten(player_state: PlayerState) -> Optional[Tile]:
        """优化向听数策略"""
        current_shanten = ShantenCalculator.calculate_shanten(player_state)
        best_tile = None
        best_improvement = -1
        
        # 尝试打掉每一张可能的牌
        for i, count in enumerate(player_state.hand_tiles):
            if count > 0:
                # 临时移除这张牌
                player_state.hand_tiles[i] -= 1
                
                # 计算打掉后的向听数
                new_shanten = ShantenCalculator.calculate_shanten(player_state)
                improvement = current_shanten - new_shanten
                
                # 如果向听数改善更多，或者相同改善但进张更多
                if improvement > best_improvement:
                    best_improvement = improvement
                    suit = [SuitType.WAN] * 9 + [SuitType.TIAO] * 9 + [SuitType.TONG] * 9
                    value = (i % 9) + 1
                    best_tile = Tile(suit[i], value)
                
                # 恢复牌
                player_state.hand_tiles[i] += 1
        
        return best_tile
    
    @staticmethod
    def _count_suit_tiles(hand_tiles: List[int], suit: SuitType) -> int:
        """计算指定花色的牌数"""
        suit_offset = {'m': 0, 's': 9, 'p': 18}[suit.value]
        return sum(hand_tiles[suit_offset + i] for i in range(9))
```

---

## 模块七：游戏引擎与结算 (Game Engine & Settlement)

### 7.1 SettlementEngine 终局结算

```python
class SettlementEngine:
    """终局结算引擎"""
    
    @staticmethod
    def settle_game(players: List[PlayerState]) -> Dict[str, Any]:
        """
        游戏结算
        血战到底特殊规则：退税、查大叫、查花猪
        """
        settlement_result = {
            'player_scores': {},
            'flowery_pig_penalty': {},
            'tax_refund': {},
            'big_call_penalty': {}
        }
        
        # 1. 查花猪
        flowery_pigs = SettlementEngine._check_flowery_pigs(players)
        
        # 2. 计算花猪罚金
        if flowery_pigs:
            settlement_result['flowery_pig_penalty'] = \
                SettlementEngine._calculate_flowery_pig_penalty(players, flowery_pigs)
        
        # 3. 退税（未听牌玩家退回杠牌收益）
        settlement_result['tax_refund'] = \
            SettlementEngine._calculate_tax_refund(players)
        
        # 4. 查大叫（未听牌玩家赔给听牌玩家）
        settlement_result['big_call_penalty'] = \
            SettlementEngine._calculate_big_call_penalty(players)
        
        # 5. 计算最终分数
        for player in players:
            player_score = 0
            
            # 胡牌收益
            if player.has_won and player.win_info:
                player_score += player.win_info['multiplier']
            
            # 杠牌收益（可能被退税影响）
            if player.player_id in settlement_result['tax_refund']:
                player_score += settlement_result['tax_refund'][player.player_id]
            else:
                player_score += player.kong_income
            
            # 花猪罚金
            if player.player_id in settlement_result['flowery_pig_penalty']:
                player_score += settlement_result['flowery_pig_penalty'][player.player_id]
            
            # 查大叫
            if player.player_id in settlement_result['big_call_penalty']:
                player_score += settlement_result['big_call_penalty'][player.player_id]
            
            settlement_result['player_scores'][player.player_id] = player_score
        
        return settlement_result
    
    @staticmethod
    def _check_flowery_pigs(players: List[PlayerState]) -> List[int]:
        """检查花猪玩家"""
        flowery_pigs = []
        for player in players:
            if player.get_suit_types_count() >= 3:
                player.is_flowery_pig = True
                flowery_pigs.append(player.player_id)
        return flowery_pigs
    
    @staticmethod
    def _calculate_flowery_pig_penalty(players: List[PlayerState], 
                                     flowery_pigs: List[int]) -> Dict[int, int]:
        """计算花猪罚金：花猪玩家赔给其他每人16倍"""
        penalty = {}
        non_pig_count = len(players) - len(flowery_pigs)
        
        for pig_id in flowery_pigs:
            penalty[pig_id] = -16 * non_pig_count  # 花猪玩家损失
        
        for player in players:
            if player.player_id not in flowery_pigs:
                penalty[player.player_id] = penalty.get(player.player_id, 0) + 16 * len(flowery_pigs)
        
        return penalty
    
    # ... 其他结算函数的实现 ...
```

---

## 项目结构与开发计划

### 8.1 推荐的项目结构

```
SichuanMahjongKit/
├── sichuanmahjong/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── tile.py              # 牌表示和转换
│   │   ├── meld.py              # 副露
│   │   ├── player_state.py      # 玩家状态
│   │   └── constants.py         # 常量定义
│   ├── validators/
│   │   ├── __init__.py
│   │   ├── win_validator.py     # 胡牌判定
│   │   └── ting_validator.py    # 听牌判定
│   ├── calculators/
│   │   ├── __init__.py
│   │   ├── shanten_calculator.py    # 向听数
│   │   └── multiplier_calculator.py # 倍数计算
│   ├── ai/
│   │   ├── __init__.py
│   │   └── hand_analyzer.py     # AI决策
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── game_engine.py       # 游戏引擎
│   │   └── settlement_engine.py # 结算引擎
│   └── utils/
│       ├── __init__.py
│       └── helpers.py           # 辅助函数
├── tests/
│   ├── test_core/
│   ├── test_validators/
│   ├── test_calculators/
│   ├── test_ai/
│   └── test_engine/
├── docs/
├── examples/
├── setup.py
├── requirements.txt
├── README.md
└── CHANGELOG.md
```

### 8.2 开发路线图

**阶段一：核心基础 (2-3周)**
1. 实现 Tile、TilesConverter、Meld、PlayerState
2. 实现 WinValidator 胡牌判定器
3. 编写全面的单元测试
4. 验证基础功能正确性

**阶段二：算法核心 (3-4周)**
1. 实现 ShantenCalculator 向听数计算
2. 实现 TingValidator 听牌判定
3. 性能优化和算法验证
4. 与规则对照测试

**阶段三：番型系统 (4-5周)**
1. 实现 MultiplierCalculator 倍数计算
2. 实现所有番型检测函数
3. 互斥规则测试
4. 计分系统验证

**阶段四：AI与引擎 (2-3周)**
1. 实现 HandAnalyzer AI决策
2. 实现 SettlementEngine 结算系统
3. 实现完整的游戏引擎
4. 集成测试

**阶段五：优化与发布 (1-2周)**
1. 性能优化
2. 文档完善
3. 示例程序
4. 打包发布

### 8.3 质量保证策略

1. **100%单元测试覆盖率**
2. **基准测试对比** - 与现有麻将程序对比计算结果
3. **性能基准** - 确保计算速度满足实时需求
4. **规则验证** - 严格按照xuezhan_rule.txt验证每个细节
5. **持续集成** - GitHub Actions自动化测试

---

## 总结

这个方案充分借鉴了日本立直麻将库的成熟架构，同时严格适配血战到底麻将的独特规则。主要特色：

1. **模块化设计** - 每个功能独立，便于测试和维护
2. **多重数据表示** - 灵活的牌表示格式，适应不同需求
3. **层级化算法** - 复杂判定分层实现，保证准确性和性能
4. **规则驱动** - 严格按照血战到底规则，确保100%准确
5. **AI决策支持** - 提供智能的打牌建议
6. **完整游戏引擎** - 支持完整的游戏流程和结算

这个设计方案为实现一个高质量的血战到底麻将库提供了详细的技术路线图。