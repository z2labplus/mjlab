# SichuanMahjongKit 血战到底麻将库详细实现方案

基于对 [MahjongRepository/mahjong](https://github.com/MahjongRepository/mahjong) 日本立直麻将库的深入分析，结合 `xuezhan_rule.txt` 血战到底规则，设计实现一个高性能、高精度的Python麻将计算库。

## 核心设计理念

1. **倍数体系而非番数**: 血战到底使用基数乘以倍数的模式（`x256`, `x64`），而非传统的番数叠加
2. **番型互斥**: "不计A、B、C"规则普遍，计分系统必须采用**层级覆盖**或**互斥检查**机制
3. **游戏状态重要性**: `定缺`、`杠牌收入`、`听牌状态`、`花猪状态`等信息贯穿整个对局
4. **模块化架构**: 借鉴日本库的成熟设计，每个核心功能独立成模块
5. **多重数据表示**: 支持多种牌的表示格式，适应不同计算需求

---

## 模块一：核心数据与状态管理 (Core Data & State Management)

### 1.1 Tile 牌的表示

借鉴日本库的 `Tile` 类设计，适配血战到底规则：

```python
from typing import Optional
from enum import Enum

class SuitType(Enum):
    """花色类型"""
    WAN = 'm'      # 万
    TIAO = 's'     # 条  
    TONG = 'p'     # 筒

class Tile:
    """单张麻将牌 - 参考日本库设计"""
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
    
    def __eq__(self, other) -> bool:
        return isinstance(other, Tile) and self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
```

### 1.2 TilesConverter 牌的格式转换器

参考日本库的 `TilesConverter`，实现多种数据格式的转换：

```python
from typing import List, Union

class TilesConverter:
    """牌的格式转换器 - 支持多种表示方法"""
    
    @staticmethod
    def string_to_27_array(tiles_string: str) -> List[int]:
        """
        字符串转27位频率数组
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
        """27位频率数组转108位详细数组（血战到底每种牌4张）"""
        tiles_108 = [0] * 108
        for i, count in enumerate(tiles_array):
            for j in range(min(count, 4)):  # 最多4张
                tiles_108[i * 4 + j] = 1
        return tiles_108
    
    @staticmethod
    def _get_tile_id(suit: str, value: int) -> int:
        """获取牌的ID"""
        base = {'m': 0, 's': 9, 'p': 18}
        return base[suit] + (value - 1)
```

### 1.3 Meld 副露（碰、杠）

```python
from enum import Enum
from typing import List, Optional

class MeldType(Enum):
    """副露类型"""
    PONG = "pong"          # 碰
    EXPOSED_KONG = "kong"  # 明杠
    CONCEALED_KONG = "angang"  # 暗杠
    UPGRADED_KONG = "jiagang"  # 加杠（补杠）

class Meld:
    """副露牌组 - 参考日本库Meld设计"""
    def __init__(self, meld_type: MeldType, tiles: List[Tile], 
                 from_player: Optional[int] = None):
        self.type = meld_type
        self.tiles = tiles
        self.from_player = from_player  # 被碰/杠的玩家索引
        self.tile_id = tiles[0].id if tiles else None
    
    def get_tile_value(self) -> int:
        """获取牌值"""
        return self.tiles[0].value
    
    def get_suit(self) -> SuitType:
        """获取花色"""
        return self.tiles[0].suit
    
    def is_kong(self) -> bool:
        """是否为杠"""
        return self.type in [MeldType.EXPOSED_KONG, MeldType.CONCEALED_KONG, MeldType.UPGRADED_KONG]
    
    def to_27_array_contribution(self) -> List[int]:
        """转换为27数组的贡献"""
        contribution = [0] * 27
        tile_id = self.tiles[0].id
        contribution[tile_id] = len(self.tiles)
        return contribution
```

### 1.4 PlayerState 玩家状态

这是核心数据类，跟踪每个玩家的完整信息：

```python
from typing import Dict, List, Optional

class PlayerState:
    """玩家完整状态信息 - 血战到底专用"""
    def __init__(self, player_id: int):
        self.player_id = player_id
        
        # 手牌信息
        self.hand_tiles: List[int] = [0] * 27  # 27位频率数组
        self.melds: List[Meld] = []
        
        # 血战到底特殊状态
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
    
    def add_meld(self, meld: Meld):
        """添加副露"""
        self.melds.append(meld)
        # 杠牌立刻赢豆
        if meld.is_kong():
            self.kong_income += 1
    
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
        """计算手牌和副露中的花色种类数 - 花猪检查的关键"""
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
    
    def get_combined_tiles_27_array(self) -> List[int]:
        """获取手牌+副露的组合27数组"""
        combined = self.hand_tiles[:]
        for meld in self.melds:
            meld_contribution = meld.to_27_array_contribution()
            for i in range(27):
                combined[i] += meld_contribution[i]
        return combined
```

---

## 模块二：核心规则与判定器 (Rule & Validators)

### 2.1 WinValidator 胡牌判定器

借鉴日本库的 `Agari` 类，实现血战到底的胡牌判定：

```python
class WinValidator:
    """胡牌判定器 - 严格按照血战到底规则"""
    
    @staticmethod
    def is_win(hand_tiles: List[int], melds: List[Meld], 
               declared_void_suit: Optional[SuitType] = None) -> bool:
        """
        判断是否胡牌
        血战到底核心规则：1）不超过2门花色 2）符合胡牌牌型
        """
        # 第一道检查：花色门数限制
        if not WinValidator._check_suit_limit(hand_tiles, melds):
            return False
        
        # 第二道检查：牌型结构
        return (WinValidator._check_seven_pairs(hand_tiles) or 
                WinValidator._check_standard_pattern(hand_tiles))
    
    @staticmethod
    def _check_suit_limit(hand_tiles: List[int], melds: List[Meld]) -> bool:
        """检查花色是否不超过2门 - 血战到底铁律"""
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
        """检查标准牌型：4组面子+1对将牌 - 参考日本库递归算法"""
        return WinValidator._recursive_check(hand_tiles[:], 0, 0)
    
    @staticmethod
    def _recursive_check(hand_tiles: List[int], meld_count: int, pair_count: int) -> bool:
        """递归检查标准牌型 - 改进的日本库算法"""
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
        
        # 尝试作为顺子（血战到底可以吃牌，但只在同花色内）
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

### 2.2 TingValidator 听牌判定器

```python
class TingValidator:
    """听牌判定器 - 判断是否听牌及听哪些牌"""
    
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
    
    @staticmethod
    def update_ting_status(player_state: PlayerState):
        """更新玩家听牌状态 - 每次打牌后调用"""
        player_state.is_ting = TingValidator.is_ting(player_state)
```

---

## 模块三：向听数与AI建议 (Shanten & AI Suggestion)

### 3.1 ShantenCalculator 向听数计算器

参考日本库的 `Shanten` 类，适配血战到底规则：

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
    def _count_void_tiles(hand_tiles: List[int], void_suit: Optional[SuitType]) -> int:
        """计算定缺牌数量"""
        if void_suit is None:
            return 0
        
        suit_offset = {'m': 0, 's': 9, 'p': 18}[void_suit.value]
        return sum(hand_tiles[suit_offset + i] for i in range(9))
    
    @staticmethod
    def _remove_void_tiles(hand_tiles: List[int], void_suit: Optional[SuitType]):
        """移除定缺牌"""
        if void_suit is None:
            return
        
        suit_offset = {'m': 0, 's': 9, 'p': 18}[void_suit.value]
        for i in range(9):
            hand_tiles[suit_offset + i] = 0
    
    @staticmethod
    def _calculate_standard_shanten(hand_tiles: List[int]) -> int:
        """计算标准牌型向听数 - 改进的递归搜索"""
        min_shanten = float('inf')
        
        # 尝试所有可能的面子组合
        def recursive_search(tiles, meld_count, pair_count, pos):
            nonlocal min_shanten
            
            # 跳过没有牌的位置
            while pos < 27 and tiles[pos] == 0:
                pos += 1
            
            if pos >= 27:
                # 计算还需要的向听数
                need_melds = 4 - meld_count
                need_pairs = 1 - pair_count
                shanten = max(0, need_melds + need_pairs - 1)
                min_shanten = min(min_shanten, shanten)
                return
            
            count = tiles[pos]
            
            # 尝试作为刻子
            if count >= 3:
                tiles[pos] -= 3
                recursive_search(tiles, meld_count + 1, pair_count, pos)
                tiles[pos] += 3
            
            # 尝试作为将牌
            if count >= 2 and pair_count == 0:
                tiles[pos] -= 2
                recursive_search(tiles, meld_count, pair_count + 1, pos + 1)
                tiles[pos] += 2
            
            # 尝试作为顺子
            if pos % 9 <= 6 and tiles[pos] > 0 and tiles[pos + 1] > 0 and tiles[pos + 2] > 0:
                tiles[pos] -= 1
                tiles[pos + 1] -= 1
                tiles[pos + 2] -= 1
                recursive_search(tiles, meld_count + 1, pair_count, pos)
                tiles[pos] += 1
                tiles[pos + 1] += 1
                tiles[pos + 2] += 1
            
            # 跳过这张牌
            recursive_search(tiles, meld_count, pair_count, pos + 1)
        
        recursive_search(hand_tiles[:], 0, 0, 0)
        return min_shanten if min_shanten != float('inf') else 8
    
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
        
        return max(0, need_pairs - available_isolated)
```

### 3.2 HandAnalyzer 手牌分析器

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
        """避免花猪策略 - 打掉数量最少的花色"""
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
        """优化向听数策略 - 选择最优打牌"""
        current_shanten = ShantenCalculator.calculate_shanten(player_state)
        best_tile = None
        best_improvement = -1
        best_ting_count = 0
        
        # 尝试打掉每一张可能的牌
        for i, count in enumerate(player_state.hand_tiles):
            if count > 0:
                # 临时移除这张牌
                player_state.hand_tiles[i] -= 1
                
                # 计算打掉后的向听数和听牌数
                new_shanten = ShantenCalculator.calculate_shanten(player_state)
                improvement = current_shanten - new_shanten
                
                # 计算有效进张数
                ting_tiles = TingValidator.get_ting_tiles(player_state)
                ting_count = len(ting_tiles)
                
                # 选择最优策略：向听数改善优先，相同时选择进张多的
                if (improvement > best_improvement or 
                    (improvement == best_improvement and ting_count > best_ting_count)):
                    best_improvement = improvement
                    best_ting_count = ting_count
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

## 模块四：倍数计算器 (Multiplier Calculator)

这是最能体现血战到底特色的模块，采用层级检测和互斥规则的设计模式：

### 4.1 WinContext 胜利上下文

```python
from dataclasses import dataclass

@dataclass
class WinContext:
    """胜利上下文信息 - 记录胡牌时的各种状态"""
    is_zimo: bool = False           # 自摸
    is_gang_flower: bool = False     # 杠上开花
    is_gang_pao: bool = False       # 杠上炮
    is_rob_kong: bool = False       # 抢杠胡
    is_sea_bottom: bool = False     # 海底捞月
    is_tianhu: bool = False         # 天胡
    is_dihu: bool = False           # 地胡
    kong_count: int = 0             # 杠数
    gen_count: int = 0              # 根数（4张相同牌的组数）
    win_tile: Optional[Tile] = None # 胡的牌
```

### 4.2 FanPattern 番型定义

```python
from dataclasses import dataclass
from typing import Callable, List

@dataclass
class FanPattern:
    """番型定义 - 严格按照xuezhan_rule.txt"""
    name: str
    multiplier: int
    check_func: Callable[[List[int], List[Meld], WinContext], bool]
    excludes: List[str]
    description: str
```

### 4.3 MultiplierCalculator 倍数计算器

```python
from typing import Dict, List, Any

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
                 win_context: WinContext) -> Dict[str, Any]:
        """
        计算胡牌倍数 - 核心算法
        返回：{'multiplier': int, 'patterns': List[str], 'details': Dict}
        """
        # 1. 主番型判定（取第一个匹配的最高倍数番型）
        main_pattern = None
        for pattern in MultiplierCalculator.FAN_PATTERNS:
            if pattern.check_func(hand_tiles, melds, win_context):
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
        
        # 3. 计算根倍数（每根x2，但要排除主番型已计算的根）
        effective_gen_count = MultiplierCalculator._calculate_effective_gen_count(
            win_context.gen_count, main_pattern.name)
        
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
    
    @staticmethod
    def _calculate_effective_gen_count(total_gen_count: int, main_pattern_name: str) -> int:
        """计算有效根数 - 处理不计根的情况"""
        if "根" in MultiplierCalculator._get_pattern_excludes(main_pattern_name):
            return 0
        
        # 特殊处理：某些番型不计部分根
        if main_pattern_name == "龙七对":
            return max(0, total_gen_count - 1)  # 龙七对不计1根
        elif main_pattern_name == "双龙七对":
            return max(0, total_gen_count - 2)  # 双龙七对不计2根
        elif main_pattern_name == "三龙七对":
            return max(0, total_gen_count - 3)  # 三龙七对不计3根
        
        return total_gen_count
    
    @staticmethod
    def _get_pattern_excludes(pattern_name: str) -> List[str]:
        """获取番型的互斥列表"""
        for pattern in MultiplierCalculator.FAN_PATTERNS:
            if pattern.name == pattern_name:
                return pattern.excludes
        return []
    
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
        # 检查手牌是否只有将牌（2张）
        total_hand_tiles = sum(hand_tiles)
        if total_hand_tiles != 2:
            return False
        
        # 检查是否有且仅有一对将牌
        pairs = sum(1 for count in hand_tiles if count == 2)
        if pairs != 1:
            return False
        
        # 检查所有副露都是刻子或杠
        meld_count = 0
        for meld in melds:
            if meld.type == MeldType.PONG or meld.is_kong():
                meld_count += 1
            else:
                return False
        
        return meld_count == 4
    
    @staticmethod
    def _is_golden_hook(hand_tiles: List[int], melds: List[Meld], context: WinContext) -> bool:
        """金钩钓：只剩一张牌单钓胡牌"""
        total_hand_tiles = sum(hand_tiles)
        return total_hand_tiles == 2 and len(melds) >= 4  # 2张手牌（将牌）+4组副露
    
    @staticmethod
    def _is_long_qidui(hand_tiles: List[int], melds: List[Meld], context: WinContext) -> bool:
        """龙七对：七对且有1组4张相同的牌"""
        if melds or not MultiplierCalculator._is_qidui(hand_tiles, melds, context):
            return False
        
        # 检查是否有且仅有1组4张相同的牌
        four_groups = sum(1 for count in hand_tiles if count == 4)
        return four_groups == 1
    
    @staticmethod
    def _is_shuang_long_qidui(hand_tiles: List[int], melds: List[Meld], context: WinContext) -> bool:
        """双龙七对：七对且有2组4张相同的牌"""
        if melds or not MultiplierCalculator._is_qidui(hand_tiles, melds, context):
            return False
        
        # 检查是否有且仅有2组4张相同的牌
        four_groups = sum(1 for count in hand_tiles if count == 4)
        return four_groups == 2
    
    @staticmethod
    def _is_san_long_qidui(hand_tiles: List[int], melds: List[Meld], context: WinContext) -> bool:
        """三龙七对：七对且有3组4张相同的牌"""
        if melds or not MultiplierCalculator._is_qidui(hand_tiles, melds, context):
            return False
        
        # 检查是否有且仅有3组4张相同的牌
        four_groups = sum(1 for count in hand_tiles if count == 4)
        return four_groups == 3
    
    @staticmethod
    def _is_jiang_qidui(hand_tiles: List[int], melds: List[Meld], context: WinContext) -> bool:
        """将七对：全部是2、5、8的七对"""
        if not MultiplierCalculator._is_qidui(hand_tiles, melds, context):
            return False
        
        # 检查所有牌是否都是2、5、8
        for i, count in enumerate(hand_tiles):
            if count > 0:
                value = (i % 9) + 1
                if value not in [2, 5, 8]:
                    return False
        
        return True
    
    @staticmethod
    def _is_duanyaojiu(hand_tiles: List[int], melds: List[Meld], context: WinContext) -> bool:
        """断么九：手牌中没有1、9"""
        # 检查手牌
        for i, count in enumerate(hand_tiles):
            if count > 0:
                value = (i % 9) + 1
                if value in [1, 9]:
                    return False
        
        # 检查副露
        for meld in melds:
            if meld.get_tile_value() in [1, 9]:
                return False
        
        return True
    
    @staticmethod
    def _is_yaojiu(hand_tiles: List[int], melds: List[Meld], context: WinContext) -> bool:
        """幺九：每个面子都包含1、9"""
        # 这个实现较复杂，需要分析具体的面子构成
        # 简化版：检查是否包含1或9的牌
        has_yaojiu = False
        
        # 检查手牌
        for i, count in enumerate(hand_tiles):
            if count > 0:
                value = (i % 9) + 1
                if value in [1, 9]:
                    has_yaojiu = True
                    break
        
        # 检查副露
        if not has_yaojiu:
            for meld in melds:
                if meld.get_tile_value() in [1, 9]:
                    has_yaojiu = True
                    break
        
        return has_yaojiu
    
    # 复合番型检测函数
    @staticmethod
    def _is_qing_shiba_luohan(hand_tiles: List[int], melds: List[Meld], context: WinContext) -> bool:
        """清十八罗汉：清一色+十八罗汉"""
        return (MultiplierCalculator._is_qingyise(hand_tiles, melds, context) and
                MultiplierCalculator._is_shiba_luohan(hand_tiles, melds, context))
    
    @staticmethod
    def _is_shiba_luohan(hand_tiles: List[int], melds: List[Meld], context: WinContext) -> bool:
        """十八罗汉：金钩钓且有4个杠"""
        return (MultiplierCalculator._is_golden_hook(hand_tiles, melds, context) and
                context.kong_count >= 4)
    
    @staticmethod
    def _is_qing_long_qidui(hand_tiles: List[int], melds: List[Meld], context: WinContext) -> bool:
        """清龙七对：清一色+龙七对"""
        return (MultiplierCalculator._is_qingyise(hand_tiles, melds, context) and
                MultiplierCalculator._is_long_qidui(hand_tiles, melds, context))
    
    @staticmethod
    def _is_qing_qidui(hand_tiles: List[int], melds: List[Meld], context: WinContext) -> bool:
        """清七对：清一色+七对"""
        return (MultiplierCalculator._is_qingyise(hand_tiles, melds, context) and
                MultiplierCalculator._is_qidui(hand_tiles, melds, context))
    
    @staticmethod
    def _is_qing_golden_hook(hand_tiles: List[int], melds: List[Meld], context: WinContext) -> bool:
        """清金钩钓：清一色+金钩钓"""
        return (MultiplierCalculator._is_qingyise(hand_tiles, melds, context) and
                MultiplierCalculator._is_golden_hook(hand_tiles, melds, context))
    
    @staticmethod
    def _is_qing_peng(hand_tiles: List[int], melds: List[Meld], context: WinContext) -> bool:
        """清碰：清一色+碰碰胡"""
        return (MultiplierCalculator._is_qingyise(hand_tiles, melds, context) and
                MultiplierCalculator._is_pengpenghu(hand_tiles, melds, context))
    
    @staticmethod
    def _is_jiang_dui(hand_tiles: List[int], melds: List[Meld], context: WinContext) -> bool:
        """将对：全部是2、5、8的碰碰胡"""
        if not MultiplierCalculator._is_pengpenghu(hand_tiles, melds, context):
            return False
        
        # 检查所有牌是否都是2、5、8
        for i, count in enumerate(hand_tiles):
            if count > 0:
                value = (i % 9) + 1
                if value not in [2, 5, 8]:
                    return False
        
        for meld in melds:
            if meld.get_tile_value() not in [2, 5, 8]:
                return False
        
        return True
    
    @staticmethod
    def _is_jiang_san_long_qidui(hand_tiles: List[int], melds: List[Meld], context: WinContext) -> bool:
        """将三龙七对：全部是2、5、8的三龙七对"""
        return (MultiplierCalculator._is_jiang_qidui(hand_tiles, melds, context) and
                MultiplierCalculator._is_san_long_qidui(hand_tiles, melds, context))
    
    @staticmethod
    def _is_jiang_shuang_long_qidui(hand_tiles: List[int], melds: List[Meld], context: WinContext) -> bool:
        """将双龙七对：全部是2、5、8的双龙七对"""
        return (MultiplierCalculator._is_jiang_qidui(hand_tiles, melds, context) and
                MultiplierCalculator._is_shuang_long_qidui(hand_tiles, melds, context))
```

---

## 模块五：游戏终局结算 (Endgame Settlement)

### 5.1 SettlementEngine 终局结算

```python
class SettlementEngine:
    """终局结算引擎 - 处理血战到底特殊结算规则"""
    
    @staticmethod
    def settle_game(players: List[PlayerState]) -> Dict[str, Any]:
        """
        游戏结算 - 血战到底特殊规则：退税、查大叫、查花猪
        """
        settlement_result = {
            'player_scores': {},
            'flowery_pig_penalty': {},
            'tax_refund': {},
            'big_call_penalty': {},
            'final_scores': {}
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
            tax_amount = settlement_result['tax_refund'].get(player.player_id, 0)
            player_score += tax_amount if tax_amount < 0 else player.kong_income
            
            # 花猪罚金
            if player.player_id in settlement_result['flowery_pig_penalty']:
                player_score += settlement_result['flowery_pig_penalty'][player.player_id]
            
            # 查大叫
            if player.player_id in settlement_result['big_call_penalty']:
                player_score += settlement_result['big_call_penalty'][player.player_id]
            
            settlement_result['final_scores'][player.player_id] = player_score
        
        return settlement_result
    
    @staticmethod
    def _check_flowery_pigs(players: List[PlayerState]) -> List[int]:
        """检查花猪玩家 - 手牌有三门花色"""
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
    
    @staticmethod
    def _calculate_tax_refund(players: List[PlayerState]) -> Dict[int, int]:
        """退税：未听牌玩家退回杠牌收益"""
        refund = {}
        
        for player in players:
            if not player.has_won and not player.is_ting and player.kong_income > 0:
                # 未听牌玩家需要退回杠牌收益
                refund[player.player_id] = -player.kong_income
                
                # 这里简化处理，实际应该返还给被杠的玩家
                # 可以根据需要扩展实现具体的退还逻辑
        
        return refund
    
    @staticmethod
    def _calculate_big_call_penalty(players: List[PlayerState]) -> Dict[int, int]:
        """查大叫：未听牌玩家赔给听牌玩家最大可能倍数"""
        penalty = {}
        
        # 分组玩家
        ting_players = [p for p in players if not p.has_won and p.is_ting]
        non_ting_players = [p for p in players if not p.has_won and not p.is_ting]
        
        if not ting_players or not non_ting_players:
            return penalty
        
        # 计算听牌玩家的最大可能倍数
        max_multipliers = {}
        for ting_player in ting_players:
            max_multiplier = SettlementEngine._calculate_max_possible_multiplier(ting_player)
            max_multipliers[ting_player.player_id] = max_multiplier
        
        # 未听牌玩家赔付
        total_penalty_per_non_ting = sum(max_multipliers.values())
        
        for non_ting_player in non_ting_players:
            penalty[non_ting_player.player_id] = -total_penalty_per_non_ting
        
        # 听牌玩家收益
        for ting_player in ting_players:
            penalty[ting_player.player_id] = (
                penalty.get(ting_player.player_id, 0) + 
                max_multipliers[ting_player.player_id] * len(non_ting_players)
            )
        
        return penalty
    
    @staticmethod
    def _calculate_max_possible_multiplier(player: PlayerState) -> int:
        """计算听牌玩家的最大可能胡牌倍数"""
        ting_tiles = TingValidator.get_ting_tiles(player)
        max_multiplier = 1  # 至少是平胡
        
        for ting_tile in ting_tiles:
            # 模拟胡这张牌
            win_context = WinContext(win_tile=ting_tile)
            
            # 计算根数
            combined_tiles = player.get_combined_tiles_27_array()
            combined_tiles[ting_tile.id] += 1  # 加上胡的牌
            
            gen_count = sum(1 for count in combined_tiles if count >= 4)
            win_context.gen_count = gen_count
            
            # 计算杠数
            win_context.kong_count = sum(1 for meld in player.melds if meld.is_kong())
            
            # 计算倍数
            result = MultiplierCalculator.calculate(
                player.hand_tiles, player.melds, win_context)
            
            max_multiplier = max(max_multiplier, result['multiplier'])
        
        return max_multiplier
```

---

## 模块六：游戏引擎 (Game Engine)

### 6.1 GameEngine 游戏引擎

```python
from typing import Optional, List, Dict, Any
from enum import Enum

class GamePhase(Enum):
    """游戏阶段"""
    INIT = "init"
    DEALING = "dealing"
    DECLARING_VOID = "declaring_void"
    PLAYING = "playing"
    SETTLEMENT = "settlement"
    FINISHED = "finished"

class GameEngine:
    """血战到底游戏引擎"""
    
    def __init__(self):
        self.players: List[PlayerState] = []
        self.current_player_index: int = 0
        self.phase: GamePhase = GamePhase.INIT
        self.remaining_tiles: List[Tile] = []
        self.game_log: List[Dict[str, Any]] = []
    
    def init_game(self, player_count: int = 4):
        """初始化游戏"""
        self.players = [PlayerState(i) for i in range(player_count)]
        self.phase = GamePhase.INIT
        self.remaining_tiles = self._create_tile_deck()
        self.game_log = []
        
    def _create_tile_deck(self) -> List[Tile]:
        """创建牌堆 - 血战到底108张牌"""
        tiles = []
        for suit in [SuitType.WAN, SuitType.TIAO, SuitType.TONG]:
            for value in range(1, 10):
                for _ in range(4):  # 每种牌4张
                    tiles.append(Tile(suit, value))
        
        import random
        random.shuffle(tiles)
        return tiles
    
    def deal_initial_hands(self):
        """发初始手牌 - 每人13张"""
        if self.phase != GamePhase.INIT:
            raise ValueError("Game not in INIT phase")
        
        self.phase = GamePhase.DEALING
        
        for _ in range(13):
            for player in self.players:
                if self.remaining_tiles:
                    tile = self.remaining_tiles.pop()
                    player.add_hand_tile(tile)
        
        self.phase = GamePhase.DECLARING_VOID
    
    def declare_void_suit(self, player_id: int, suit: SuitType):
        """玩家定缺"""
        if self.phase != GamePhase.DECLARING_VOID:
            raise ValueError("Not in void declaration phase")
        
        self.players[player_id].declared_void_suit = suit
        
        # 检查是否所有玩家都已定缺
        if all(p.declared_void_suit is not None for p in self.players):
            self.phase = GamePhase.PLAYING
    
    def draw_tile(self, player_id: int) -> Optional[Tile]:
        """玩家摸牌"""
        if self.phase != GamePhase.PLAYING:
            return None
        
        if not self.remaining_tiles:
            return None
        
        tile = self.remaining_tiles.pop()
        self.players[player_id].add_hand_tile(tile)
        
        self._log_action("draw", player_id, tile)
        return tile
    
    def discard_tile(self, player_id: int, tile: Tile) -> bool:
        """玩家弃牌"""
        if self.phase != GamePhase.PLAYING:
            return False
        
        player = self.players[player_id]
        if not player.remove_hand_tile(tile):
            return False
        
        # 更新听牌状态
        TingValidator.update_ting_status(player)
        
        self._log_action("discard", player_id, tile)
        return True
    
    def pong_tile(self, player_id: int, tile: Tile, from_player_id: int) -> bool:
        """玩家碰牌"""
        player = self.players[player_id]
        
        # 检查是否有两张相同的牌
        if player.hand_tiles[tile.id] < 2:
            return False
        
        # 移除手牌中的两张
        player.hand_tiles[tile.id] -= 2
        
        # 创建碰牌副露
        pong_tiles = [tile, tile, tile]
        meld = Meld(MeldType.PONG, pong_tiles, from_player_id)
        player.add_meld(meld)
        
        self._log_action("pong", player_id, tile, from_player_id)
        return True
    
    def kong_tile(self, player_id: int, tile: Tile, kong_type: str, 
                  from_player_id: Optional[int] = None) -> bool:
        """玩家杠牌"""
        player = self.players[player_id]
        
        if kong_type == "angang":
            # 暗杠：需要4张相同牌
            if player.hand_tiles[tile.id] < 4:
                return False
            
            player.hand_tiles[tile.id] -= 4
            kong_tiles = [tile] * 4
            meld = Meld(MeldType.CONCEALED_KONG, kong_tiles)
            
        elif kong_type == "zhigang":
            # 直杠：需要3张相同牌
            if player.hand_tiles[tile.id] < 3:
                return False
            
            player.hand_tiles[tile.id] -= 3
            kong_tiles = [tile] * 4
            meld = Meld(MeldType.EXPOSED_KONG, kong_tiles, from_player_id)
            
        elif kong_type == "jiagang":
            # 加杠：在已有碰牌基础上
            pong_meld = None
            for meld in player.melds:
                if (meld.type == MeldType.PONG and 
                    meld.get_tile_value() == tile.value and
                    meld.get_suit() == tile.suit):
                    pong_meld = meld
                    break
            
            if not pong_meld or player.hand_tiles[tile.id] < 1:
                return False
            
            player.hand_tiles[tile.id] -= 1
            # 将碰牌升级为加杠
            pong_meld.type = MeldType.UPGRADED_KONG
            pong_meld.tiles.append(tile)
        
        else:
            return False
        
        if kong_type != "jiagang":
            player.add_meld(meld)
        
        self._log_action("kong", player_id, tile, from_player_id, {"kong_type": kong_type})
        return True
    
    def win_game(self, player_id: int, win_tile: Tile, is_zimo: bool = False) -> Dict[str, Any]:
        """玩家胡牌"""
        player = self.players[player_id]
        
        # 验证是否能胡牌
        temp_hand = player.hand_tiles[:]
        temp_hand[win_tile.id] += 1
        
        if not WinValidator.is_win(temp_hand, player.melds, player.declared_void_suit):
            return {"success": False, "error": "Invalid win"}
        
        # 计算胜利倍数
        win_context = WinContext(
            is_zimo=is_zimo,
            win_tile=win_tile,
            kong_count=sum(1 for meld in player.melds if meld.is_kong()),
            gen_count=sum(1 for count in temp_hand if count >= 4)
        )
        
        multiplier_result = MultiplierCalculator.calculate(
            temp_hand, player.melds, win_context)
        
        # 更新玩家状态
        player.has_won = True
        player.win_info = multiplier_result
        
        self._log_action("win", player_id, win_tile, None, {
            "is_zimo": is_zimo,
            "multiplier": multiplier_result['multiplier'],
            "patterns": multiplier_result['patterns']
        })
        
        # 检查是否进入结算阶段
        self._check_game_end()
        
        return {"success": True, "result": multiplier_result}
    
    def _check_game_end(self):
        """检查游戏是否结束"""
        # 血战到底：三人胡牌或摸完所有牌
        won_count = sum(1 for p in self.players if p.has_won)
        
        if won_count >= 3 or not self.remaining_tiles:
            self.phase = GamePhase.SETTLEMENT
    
    def settle_game(self) -> Dict[str, Any]:
        """游戏结算"""
        if self.phase != GamePhase.SETTLEMENT:
            return {"error": "Game not ready for settlement"}
        
        # 更新所有玩家的听牌状态
        for player in self.players:
            if not player.has_won:
                TingValidator.update_ting_status(player)
        
        settlement_result = SettlementEngine.settle_game(self.players)
        self.phase = GamePhase.FINISHED
        
        self._log_action("settlement", -1, None, None, settlement_result)
        
        return settlement_result
    
    def _log_action(self, action_type: str, player_id: int, tile: Optional[Tile], 
                   target_player: Optional[int] = None, extra_data: Optional[Dict] = None):
        """记录游戏操作"""
        log_entry = {
            "sequence": len(self.game_log) + 1,
            "action_type": action_type,
            "player_id": player_id,
            "tile": str(tile) if tile else None,
            "target_player": target_player,
            "timestamp": time.time()
        }
        
        if extra_data:
            log_entry.update(extra_data)
        
        self.game_log.append(log_entry)
    
    def get_game_state(self) -> Dict[str, Any]:
        """获取游戏状态"""
        return {
            "phase": self.phase.value,
            "current_player": self.current_player_index,
            "players": [
                {
                    "player_id": p.player_id,
                    "hand_count": sum(p.hand_tiles),
                    "melds": len(p.melds),
                    "declared_void_suit": p.declared_void_suit.value if p.declared_void_suit else None,
                    "has_won": p.has_won,
                    "is_ting": p.is_ting,
                    "is_flowery_pig": p.is_flowery_pig,
                    "kong_income": p.kong_income
                }
                for p in self.players
            ],
            "remaining_tiles": len(self.remaining_tiles),
            "game_log_length": len(self.game_log)
        }
```

---

## 总结与开发路线图

### 开发阶段规划

1. **第一阶段 (地基 2-3周)**: 
   - 实现核心数据结构：`Tile`、`TilesConverter`、`Meld`、`PlayerState`
   - 实现基础验证器：`WinValidator`、`TingValidator`
   - 编写全面的单元测试，确保基础功能100%准确

2. **第二阶段 (AI核心 3-4周)**: 
   - 实现 `ShantenCalculator` 向听数计算器
   - 实现 `HandAnalyzer` AI决策引擎
   - 性能优化和算法验证

3. **第三阶段 (计分灵魂 4-5周)**: 
   - 实现 `MultiplierCalculator` 倍数计算系统
   - 实现所有番型检测函数
   - 严格按照层级和互斥规则实现计分逻辑

4. **第四阶段 (游戏逻辑 2-3周)**: 
   - 实现 `SettlementEngine` 结算系统
   - 实现 `GameEngine` 完整游戏引擎
   - 集成所有模块，处理完整游戏流程

5. **第五阶段 (优化发布 1-2周)**:
   - 性能优化和代码重构
   - 文档完善和示例程序
   - 打包发布

### 项目结构建议

```
SichuanMahjongKit/
├── sichuanmahjong/
│   ├── __init__.py
│   ├── core/
│   │   ├── tile.py
│   │   ├── meld.py
│   │   ├── player_state.py
│   │   └── constants.py
│   ├── validators/
│   │   ├── win_validator.py
│   │   └── ting_validator.py
│   ├── calculators/
│   │   ├── shanten_calculator.py
│   │   └── multiplier_calculator.py
│   ├── ai/
│   │   └── hand_analyzer.py
│   ├── engine/
│   │   ├── game_engine.py
│   │   └── settlement_engine.py
│   └── utils/
│       └── helpers.py
├── tests/
├── docs/
├── examples/
└── setup.py
```

### 质量保证策略

1. **100%单元测试覆盖率** - 每个函数都有对应测试
2. **基准测试对比** - 与现有麻将程序对比计算结果
3. **性能基准** - 确保计算速度满足实时需求
4. **规则验证** - 严格按照xuezhan_rule.txt验证每个细节
5. **持续集成** - GitHub Actions自动化测试

这个完善的方案现在提供了：
- ✅ **完整的技术架构** - 基于成熟的日本库设计
- ✅ **详细的代码框架** - 可直接开始实现
- ✅ **严格的规则适配** - 100%按照血战到底规则
- ✅ **全面的开发指南** - 从基础到发布的完整路线图

按照这个蓝图，您就可以着手构建一个强大且规则精确的 `SichuanMahjongKit` 库了！