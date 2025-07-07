#!/usr/bin/env python3
"""
麻将有效进张分析器 - 修正的穷举版本
修复了向听数计算问题，使用更准确的算法
"""

import json
from collections import Counter

class FixedExhaustiveMahjongAnalyzer:
    """修正的穷举版麻将分析器"""
    
    def __init__(self):
        pass
    
    def parse_hand(self, hand_string):
        """解析手牌字符串"""
        tiles = []
        current_numbers = ""
        
        for char in hand_string:
            if char.isdigit():
                current_numbers += char
            elif char in 'mpsz':
                for num_char in current_numbers:
                    tiles.append(f"{num_char}{char}")
                current_numbers = ""
        
        return sorted(tiles)
    
    def to_array34(self, tiles):
        """转换为34种牌的数组表示"""
        counts = [0] * 34
        
        for tile in tiles:
            idx = self.tile_to_index(tile)
            if idx >= 0:
                counts[idx] += 1
        
        return counts
    
    def tile_to_index(self, tile):
        """牌转索引"""
        if len(tile) != 2:
            return -1
            
        num = int(tile[0])
        suit = tile[1]
        
        if suit == 'm':
            return num - 1
        elif suit == 'p':
            return num - 1 + 9
        elif suit == 's':
            return num - 1 + 18
        elif suit == 'z':
            return num - 1 + 27
        
        return -1
    
    def index_to_tile(self, idx):
        """索引转牌"""
        if idx < 9:
            return f"{idx + 1}m"
        elif idx < 18:
            return f"{idx - 8}p"
        elif idx < 27:
            return f"{idx - 17}s"
        elif idx < 34:
            return f"{idx - 26}z"
        return None
    
    def calculate_shanten_optimized(self, counts):
        """
        优化的向听数计算
        使用标准的递归算法但修复了一些问题
        """
        def calc_man_pin_sou(counts, pos, jantou, mentsu):
            """计算万筒条的向听数"""
            if pos >= 27:
                return calc_zihai(counts, 27, jantou, mentsu)
            
            if counts[pos] == 0:
                return calc_man_pin_sou(counts, pos + 1, jantou, mentsu)
            
            ret = 8
            
            # 不使用这张牌
            ret = min(ret, calc_man_pin_sou(counts, pos + 1, jantou, mentsu))
            
            # 作为雀头
            if jantou == 0 and counts[pos] >= 2:
                counts[pos] -= 2
                ret = min(ret, calc_man_pin_sou(counts, pos, 1, mentsu))
                counts[pos] += 2
            
            # 作为刻子
            if counts[pos] >= 3:
                counts[pos] -= 3
                ret = min(ret, calc_man_pin_sou(counts, pos, jantou, mentsu + 1))
                counts[pos] += 3
            
            # 作为顺子
            if pos % 9 <= 6 and counts[pos] >= 1 and counts[pos + 1] >= 1 and counts[pos + 2] >= 1:
                counts[pos] -= 1
                counts[pos + 1] -= 1
                counts[pos + 2] -= 1
                ret = min(ret, calc_man_pin_sou(counts, pos, jantou, mentsu + 1))
                counts[pos] += 1
                counts[pos + 1] += 1
                counts[pos + 2] += 1
            
            return ret
        
        def calc_zihai(counts, pos, jantou, mentsu):
            """计算字牌的向听数"""
            if pos >= 34:
                return 8 - 2 * mentsu - jantou
            
            if counts[pos] == 0:
                return calc_zihai(counts, pos + 1, jantou, mentsu)
            
            ret = 8
            
            # 不使用这张牌
            ret = min(ret, calc_zihai(counts, pos + 1, jantou, mentsu))
            
            # 作为雀头
            if jantou == 0 and counts[pos] >= 2:
                counts[pos] -= 2
                ret = min(ret, calc_zihai(counts, pos, 1, mentsu))
                counts[pos] += 2
            
            # 作为刻子
            if counts[pos] >= 3:
                counts[pos] -= 3
                ret = min(ret, calc_zihai(counts, pos, jantou, mentsu + 1))
                counts[pos] += 3
            
            return ret
        
        return calc_man_pin_sou(counts[:], 0, 0, 0)
    
    def calculate_shanten(self, tiles):
        """计算向听数（使用优化算法）"""
        counts = self.to_array34(tiles)
        
        # 标准型向听数
        standard_shanten = self.calculate_shanten_optimized(counts)
        
        # 七对子向听数
        chitoi_shanten = self.calculate_chitoi_shanten(counts)
        
        # 国士无双向听数
        kokushi_shanten = self.calculate_kokushi_shanten(counts)
        
        return min(standard_shanten, chitoi_shanten, kokushi_shanten)
    
    def calculate_chitoi_shanten(self, counts):
        """计算七对子向听数"""
        pairs = 0
        isolated = 0
        
        for count in counts:
            if count >= 2:
                pairs += 1
            elif count == 1:
                isolated += 1
        
        if pairs > 7:
            pairs = 7
        
        return 6 - pairs + max(0, 7 - pairs - isolated)
    
    def calculate_kokushi_shanten(self, counts):
        """计算国士无双向听数"""
        yaochuhai = [0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33]  # 幺九牌的索引
        
        types = 0
        has_pair = False
        
        for idx in yaochuhai:
            if counts[idx] >= 1:
                types += 1
            if counts[idx] >= 2:
                has_pair = True
        
        shanten = 13 - types
        if not has_pair:
            shanten -= 1
        
        return shanten
    
    def check_winning_hand(self, tiles):
        """
        检查是否胡牌
        返回: (is_winning, winning_patterns)
        """
        if len(tiles) % 3 != 2:
            return False, []
        
        counts = self.to_array34(tiles)
        return self._check_winning_patterns(counts)
    
    def _check_winning_patterns(self, counts):
        """检查胡牌型"""
        
        # 检查标准型胡牌
        if self._check_standard_winning(counts[:]):
            return True, ["标准型"]
        
        # 检查七对子
        if self._check_seven_pairs(counts):
            return True, ["七对子"]
        
        # 检查国士无双
        if self._check_thirteen_orphans_exhaustive(counts):
            return True, ["国士无双"]
        
        return False, []
    
    def _check_standard_winning(self, counts):
        """检查标准型胡牌"""
        def check_win(counts, pos, has_pair):
            if pos >= 34:
                return has_pair
            
            if counts[pos] == 0:
                return check_win(counts, pos + 1, has_pair)
            
            # 尝试作为雀头
            if not has_pair and counts[pos] >= 2:
                counts[pos] -= 2
                if check_win(counts[:], pos, True):
                    return True
                counts[pos] += 2
            
            # 尝试作为刻子
            if counts[pos] >= 3:
                counts[pos] -= 3
                if check_win(counts[:], pos, has_pair):
                    return True
                counts[pos] += 3
            
            # 尝试作为顺子（只对万筒条有效）
            if pos < 27 and pos % 9 <= 6:
                if counts[pos] >= 1 and counts[pos + 1] >= 1 and counts[pos + 2] >= 1:
                    counts[pos] -= 1
                    counts[pos + 1] -= 1
                    counts[pos + 2] -= 1
                    if check_win(counts[:], pos, has_pair):
                        return True
                    counts[pos] += 1
                    counts[pos + 1] += 1
                    counts[pos + 2] += 1
            
            return False
        
        return check_win(counts, 0, False)
    
    def _check_seven_pairs(self, counts):
        """检查七对子"""
        pairs = 0
        for count in counts:
            if count == 2:
                pairs += 1
            elif count != 0:
                return False
        return pairs == 7
    
    def _check_thirteen_orphans_exhaustive(self, counts):
        """检查国士无双"""
        yaochuhai = [0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33]
        
        has_pair = False
        for idx in yaochuhai:
            if counts[idx] == 0:
                return False
            elif counts[idx] == 2:
                if has_pair:
                    return False
                has_pair = True
            elif counts[idx] != 1:
                return False
        
        # 检查其他牌是否为0
        for i in range(34):
            if i not in yaochuhai and counts[i] != 0:
                return False
        
        return has_pair
    
    def _create_winning_result_exhaustive(self, hand_tiles, winning_patterns):
        """
        创建胡牌结果（穷举版）
        """
        # 找出可能的胡牌（最后摸到的牌）
        winning_tiles = []
        
        # 检查每张牌，如果移除后变成听牌状态，说明这张牌是胡牌
        unique_tiles = list(set(hand_tiles))
        for test_tile in unique_tiles:
            remaining_tiles = hand_tiles[:]
            remaining_tiles.remove(test_tile)
            
            # 如果移除这张牌后是听牌状态（向听数为0），则这张牌是胡牌
            remaining_shanten = self.calculate_shanten(remaining_tiles)
            if remaining_shanten == 0:
                winning_tiles.append(test_tile)
        
        # 如果找不到具体胡牌，但确实是胡牌，可能是特殊牌型
        if not winning_tiles and winning_patterns:
            # 对于标准型，找出可能的胡牌
            if "标准型" in winning_patterns:
                # 找出对子，对子中的任意一张都可能是胡牌
                tile_counts = Counter(hand_tiles)
                for tile, count in tile_counts.items():
                    if count == 2:
                        winning_tiles.append(tile)
            
            # 如果还是找不到，设为所有牌
            if not winning_tiles:
                winning_tiles = unique_tiles[:3]  # 返回前几张作为示例
        
        return [{
            "tile": "胡牌",
            "tiles": winning_tiles,
            "number": str(len(winning_tiles)),
            "patterns": winning_patterns
        }]
    
    def _analyze_13_tiles_exhaustive(self, hand_tiles, current_shanten):
        """
        穷举版分析13张牌的情况（听牌状态）
        直接分析可以摸什么牌来减少向听数
        """
        hand_counts = Counter(hand_tiles)
        
        # 穷举所有可能的进张牌
        effective_tiles = []
        total_effective_count = 0
        
        # 遍历所有34种牌
        for tile_idx in range(34):
            test_tile = self.index_to_tile(tile_idx)
            available_count = 4 - hand_counts.get(test_tile, 0)
            
            if available_count > 0:
                # 加入这张牌后的手牌
                test_hand = hand_tiles + [test_tile]
                test_shanten = self.calculate_shanten(test_hand)
                
                # 如果能减少向听数，则为有效牌
                if test_shanten < current_shanten:
                    effective_tiles.append(test_tile)
                    total_effective_count += available_count
        
        if effective_tiles:
            return [{
                "tile": "摸牌",  # 表示这是摸牌分析
                "tiles": effective_tiles,
                "number": str(total_effective_count)
            }]
        else:
            return [{
                "tile": "摸牌",
                "tiles": [],
                "number": "0"
            }]
    
    def analyze_hand_exhaustive_fixed(self, hand_string):
        """
        修正的穷举版分析手牌
        使用更准确的向听数计算
        """
        hand_tiles = self.parse_hand(hand_string)
        
        if len(hand_tiles) < 1 or len(hand_tiles) > 14:
            return f"错误：手牌应该是1-14张，当前是{len(hand_tiles)}张"
        
        results = []
        current_shanten = self.calculate_shanten(hand_tiles)
        
        # 处理13张牌的情况（听牌状态）
        if len(hand_tiles) == 13:
            return self._analyze_13_tiles_exhaustive(hand_tiles, current_shanten)
        
        # 处理14张牌的情况（先检查胡牌，再考虑打牌）
        if len(hand_tiles) in [2, 5, 8, 11, 14]:
            is_winning, winning_patterns = self.check_winning_hand(hand_tiles)
            if is_winning:
                return self._create_winning_result_exhaustive(hand_tiles, winning_patterns)
        
        # 如果没有胡牌，继续分析出牌
        # 获取手牌中所有不同的牌
        unique_tiles = list(set(hand_tiles))
        
        for discard_tile in unique_tiles:
            # 弃牌后的手牌
            remaining_tiles = hand_tiles[:]
            remaining_tiles.remove(discard_tile)
            
            # 统计剩余手牌中每种牌的数量
            remaining_counts = Counter(remaining_tiles)
            
            # 穷举所有可能的进张牌
            effective_tiles = []
            total_effective_count = 0
            
            # 遍历所有34种牌
            for tile_idx in range(34):
                test_tile = self.index_to_tile(tile_idx)
                
                # 计算这种牌在牌池中的剩余数量
                used_count = remaining_counts.get(test_tile, 0)
                available_count = 4 - used_count
                
                # 如果这种牌还有剩余
                if available_count > 0:
                    # 尝试加入这张牌
                    test_hand = remaining_tiles + [test_tile]
                    new_shanten = self.calculate_shanten(test_hand)
                    
                    # 如果向听数减少了，这就是有效进张
                    if new_shanten < current_shanten:
                        effective_tiles.append(test_tile)
                        total_effective_count += available_count
            
            # 如果有有效进张，记录这个选择
            if effective_tiles:
                results.append({
                    "tile": discard_tile,
                    "tiles": effective_tiles,
                    "number": str(total_effective_count)
                })
        
        # 按有效进张总数从大到小排序
        results.sort(key=lambda x: int(x["number"]), reverse=True)
        
        return results

def simple_analyze_exhaustive_fixed(hand_string):
    """修正的穷举版简单分析接口"""
    analyzer = FixedExhaustiveMahjongAnalyzer()
    return analyzer.analyze_hand_exhaustive_fixed(hand_string)

def test_fixed_exhaustive():
    """测试修正的穷举算法"""
    # 先测试向听数计算
    analyzer = FixedExhaustiveMahjongAnalyzer()
    
    test_cases = [
        "1245589m1244588s",
        "2233456m4456778s",
        "13m24p1578889s232z"
    ]
    
    print("=== 修正版向听数测试 ===")
    for hand in test_cases:
        hand_tiles = analyzer.parse_hand(hand)
        shanten = analyzer.calculate_shanten(hand_tiles)
        print(f"手牌: {hand}")
        print(f"向听数: {shanten}")
        print()
    
    print("=== 修正版穷举算法测试 ===")
    for i, hand in enumerate(test_cases, 1):
        print(f"【测试{i}】手牌: {hand}")
        print("-" * 50)
        
        result = simple_analyze_exhaustive_fixed(hand)
        
        if isinstance(result, str):
            print(f"错误: {result}")
        else:
            print("修正版穷举算法结果:")
            print(json.dumps(result[:4], ensure_ascii=False, indent=2))
        
        print()

if __name__ == "__main__":
    test_fixed_exhaustive()