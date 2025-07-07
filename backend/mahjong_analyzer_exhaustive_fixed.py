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
    
    def analyze_hand_exhaustive_fixed(self, hand_string):
        """
        修正的穷举版分析手牌
        使用更准确的向听数计算
        """
        hand_tiles = self.parse_hand(hand_string)
        
        if len(hand_tiles) != 14:
            return f"错误：手牌应该是14张，当前是{len(hand_tiles)}张"
        
        results = []
        current_shanten = self.calculate_shanten(hand_tiles)
        
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