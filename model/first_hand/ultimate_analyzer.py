#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
血战到底麻将分析器 - 专业最优出牌策略
结合血战到底规则：缺牌、门数限制、特殊牌型等
"""

import json
import sys
import os
import itertools
from collections import defaultdict, Counter

# 导入外部mahjong库
try:
    from mahjong.shanten import Shanten
    from mahjong.tile import TilesConverter
    MAHJONG_LIB_AVAILABLE = True
except ImportError:
    MAHJONG_LIB_AVAILABLE = False
    print("警告: mahjong库未安装，将使用简化算法")

class XuezhanAnalyzer:
    """血战到底麻将分析器"""
    
    def __init__(self):
        if MAHJONG_LIB_AVAILABLE:
            self.tile_converter = TilesConverter()
            self.shanten_calculator = Shanten()
        else:
            self.tile_converter = None
            self.shanten_calculator = None
        
        # 血战到底牌型映射 - 本地表示 -> 标准表示
        self.TILE_MAPPING = {
            # 万字牌
            '1万': '1m', '2万': '2m', '3万': '3m', '4万': '4m', '5万': '5m',
            '6万': '6m', '7万': '7m', '8万': '8m', '9万': '9m',
            # 筒子牌  
            '1筒': '1p', '2筒': '2p', '3筒': '3p', '4筒': '4p', '5筒': '5p',
            '6筒': '6p', '7筒': '7p', '8筒': '8p', '9筒': '9p',
            # 条子牌
            '1条': '1s', '2条': '2s', '3条': '3s', '4条': '4s', '5条': '5s',
            '6条': '6s', '7条': '7s', '8条': '8s', '9条': '9s'
        }
        
        # 反向映射
        self.REVERSE_MAPPING = {v: k for k, v in self.TILE_MAPPING.items()}
        
        # 血战到底特殊牌型权重
        self.SPECIAL_PATTERNS = {
            'qidui': 50,      # 七对
            'qingyise': 40,   # 清一色
            'pengpenghu': 30, # 碰碰胡
            'jingouding': 40, # 金钩钓
            'duanyaojiu': 20, # 断么九
            'gen': 20         # 根（四张相同牌）
        }
    
    def get_tile_suit(self, tile):
        """获取牌的花色"""
        if tile.endswith('万'):
            return '万'
        elif tile.endswith('筒'):
            return '筒'
        elif tile.endswith('条'):
            return '条'
        return None
    
    def should_discard_immediately(self, tile, missing_suit):
        """检查是否必须立即打出（缺牌规则）"""
        tile_suit = self.get_tile_suit(tile)
        return tile_suit == missing_suit
    
    def count_suits(self, hand_tiles):
        """计算手牌中的花色门数"""
        suits = set()
        for tile in hand_tiles:
            suit = self.get_tile_suit(tile)
            if suit:
                suits.add(suit)
        return len(suits), suits
    
    def can_win(self, hand_tiles, missing_suit):
        """检查是否可以胡牌（门数限制）"""
        suit_count, suits = self.count_suits(hand_tiles)
        
        # 血战到底规则：手牌不超过2门花色才能胡牌
        if suit_count > 2:
            return False, "手牌超过2门花色"
        
        # 不能包含缺牌花色
        if missing_suit in suits:
            return False, f"手牌包含缺牌花色({missing_suit})"
        
        return True, "可以胡牌"
    
    def detect_special_patterns(self, hand_tiles):
        """识别特殊牌型"""
        patterns = []
        counter = Counter(hand_tiles)
        suit_count, suits = self.count_suits(hand_tiles)
        
        # 七对检测
        if len(counter) == 7 and all(count == 2 for count in counter.values()):
            patterns.append('qidui')
            
            # 检查龙七对（有4张相同牌的七对）
            temp_tiles = hand_tiles.copy()
            dragon_count = 0
            for tile, count in counter.items():
                if temp_tiles.count(tile) >= 4:
                    dragon_count += 1
            
            if dragon_count >= 3:
                patterns.append('sanlongqidui')  # 三龙七对
            elif dragon_count >= 2:
                patterns.append('shuanglongqidui')  # 双龙七对
            elif dragon_count >= 1:
                patterns.append('longqidui')  # 龙七对
        
        # 清一色检测
        if suit_count == 1:
            patterns.append('qingyise')
        
        # 碰碰胡检测（全部刻子）
        triplet_count = sum(1 for count in counter.values() if count >= 3)
        if triplet_count >= 4:  # 4个刻子+1个对子
            patterns.append('pengpenghu')
        
        # 金钩钓检测（单钓）
        if len([c for c in counter.values() if c == 1]) == 1:
            patterns.append('jingouding')
        
        # 断么九检测
        has_terminal = any(tile.startswith('1') or tile.startswith('9') for tile in hand_tiles)
        if not has_terminal:
            patterns.append('duanyaojiu')
        
        # 根检测
        gen_count = sum(1 for count in counter.values() if count == 4)
        if gen_count > 0:
            patterns.extend(['gen'] * gen_count)
        
        return patterns
    
    def calculate_pattern_bonus(self, patterns):
        """计算特殊牌型奖励"""
        bonus = 0
        for pattern in patterns:
            bonus += self.SPECIAL_PATTERNS.get(pattern, 0)
        return bonus
    
    def convert_to_standard(self, tiles):
        """将本地牌型转换为标准表示"""
        result = []
        for tile in tiles:
            if tile in self.TILE_MAPPING:
                result.append(self.TILE_MAPPING[tile])
            else:
                result.append(tile)
        return result
    
    def convert_from_standard(self, tiles):
        """将标准表示转换为本地牌型"""
        result = []
        for tile in tiles:
            if tile in self.REVERSE_MAPPING:
                result.append(self.REVERSE_MAPPING[tile])
            else:
                result.append(tile)
        return result
    
    def calculate_shanten(self, hand_tiles):
        """计算向听数"""
        if not MAHJONG_LIB_AVAILABLE or not self.shanten_calculator:
            return self.estimate_shanten_simple(hand_tiles)
            
        try:
            # 只处理万筒条，不包含字牌
            standard_tiles = self.convert_to_standard(hand_tiles)
            if not standard_tiles:
                return 14
            
            # 转换为34位数组（只有万筒条27种）
            tiles_34 = [0] * 34
            for tile_str in standard_tiles:
                if tile_str[-1] in ['m', 'p', 's']:
                    value = int(tile_str[0]) - 1
                    if tile_str[-1] == 'm':  # 万
                        index = value
                    elif tile_str[-1] == 'p':  # 筒
                        index = 9 + value
                    elif tile_str[-1] == 's':  # 条
                        index = 18 + value
                    
                    if 0 <= index < 27:
                        tiles_34[index] += 1
            
            return self.shanten_calculator.calculate_shanten(tiles_34)
        except Exception as e:
            print(f"向听数计算失败: {e}")
            return self.estimate_shanten_simple(hand_tiles)
    
    def estimate_shanten_simple(self, hand_tiles):
        """简化的向听数估算"""
        if len(hand_tiles) == 0:
            return 14
        
        counter = Counter(hand_tiles)
        
        # 检查七对
        if len(counter) == 7 and all(count == 2 for count in counter.values()):
            return 0  # 七对胡牌
        
        # 计算刻子和对子数量
        triplets = sum(1 for count in counter.values() if count >= 3)
        pairs = sum(1 for count in counter.values() if count == 2)
        
        # 计算可能的顺子数量
        sequences = 0
        temp_counter = counter.copy()
        
        for suit in ['万', '筒', '条']:
            for value in range(1, 8):
                tile1 = f"{value}{suit}"
                tile2 = f"{value+1}{suit}"
                tile3 = f"{value+2}{suit}"
                
                min_count = min(temp_counter.get(tile1, 0), 
                               temp_counter.get(tile2, 0), 
                               temp_counter.get(tile3, 0))
                
                if min_count > 0:
                    sequences += min_count
                    temp_counter[tile1] -= min_count
                    temp_counter[tile2] -= min_count
                    temp_counter[tile3] -= min_count
        
        # 简单的向听数估算：4个面子+1个对子=胡牌
        completed_sets = triplets + sequences
        need_sets = 4 - completed_sets
        need_pair = 1 if pairs == 0 else 0
        
        return max(0, need_sets + need_pair - 1)
    
    def get_useful_tiles(self, hand_tiles, missing_suit):
        """获取有用牌（能减少向听数且不违反规则的牌）"""
        try:
            current_shanten = self.calculate_shanten(hand_tiles)
            useful_tiles = []
            
            # 只测试不是缺牌花色的牌
            all_tiles = []
            for suit in ['万', '筒', '条']:
                if suit != missing_suit:  # 排除缺牌花色
                    for i in range(1, 10):
                        all_tiles.append(f"{i}{suit}")
            
            for test_tile in all_tiles:
                new_hand = hand_tiles + [test_tile]
                
                # 检查门数限制
                suit_count, _ = self.count_suits(new_hand)
                if suit_count > 2:
                    continue
                
                new_shanten = self.calculate_shanten(new_hand)
                if new_shanten < current_shanten:
                    useful_tiles.append(test_tile)
            
            return useful_tiles
        except Exception as e:
            print(f"有用牌计算失败: {e}")
            return []
    
    def analyze_discard_options(self, hand_tiles, visible_tiles, missing_suit):
        """分析所有出牌选项（结合血战到底规则）"""
        results = []
        unique_tiles = list(set(hand_tiles))
        print(f"可出牌选项: {unique_tiles}")
        print(f"玩家缺牌: {missing_suit}")
        
        # 首先检查是否有必须打出的缺牌
        forced_discards = [tile for tile in unique_tiles if self.should_discard_immediately(tile, missing_suit)]
        if forced_discards:
            print(f"⚠️ 必须打出缺牌: {forced_discards}")
            unique_tiles = forced_discards  # 只能选择缺牌打出
        
        for discard_tile in unique_tiles:
            # 计算出牌后的手牌
            remaining_hand = hand_tiles.copy()
            remaining_hand.remove(discard_tile)
            
            # 检查是否可以胡牌
            can_win, win_reason = self.can_win(remaining_hand, missing_suit)
            
            # 计算向听数
            shanten = self.calculate_shanten(remaining_hand) if can_win else 14
            
            # 计算有用牌
            useful_tiles = self.get_useful_tiles(remaining_hand, missing_suit) if can_win else []
            
            # 计算剩余有用牌数量
            useful_count = 0
            visible_counter = Counter(visible_tiles)
            remaining_hand_counter = Counter(remaining_hand)
            
            for useful_tile in useful_tiles:
                visible_count = visible_counter.get(useful_tile, 0)
                hand_count = remaining_hand_counter.get(useful_tile, 0)
                total_used = visible_count + hand_count
                remaining = 4 - total_used
                useful_count += max(0, remaining)
            
            # 识别特殊牌型
            patterns = self.detect_special_patterns(remaining_hand)
            pattern_bonus = self.calculate_pattern_bonus(patterns)
            
            # 计算期望收益（结合血战到底规则）
            if not can_win:
                expected_value = -1000  # 无法胡牌，极低价值
            elif shanten == 0:
                expected_value = 1000 + useful_count + pattern_bonus  # 听牌状态
            elif shanten == 1:
                expected_value = 500 + useful_count * 2 + pattern_bonus  # 一向听
            elif shanten == 2:
                expected_value = 200 + useful_count * 1.5 + pattern_bonus  # 两向听
            else:
                expected_value = useful_count + pattern_bonus
            
            # 缺牌必须打出，给予最高优先级
            if self.should_discard_immediately(discard_tile, missing_suit):
                expected_value += 10000
            
            result = {
                'discard': discard_tile,
                'shanten': shanten,
                'useful_tiles': useful_tiles,
                'useful_count': useful_count,
                'expected_value': expected_value,
                'can_win': can_win,
                'win_reason': win_reason,
                'patterns': patterns,
                'pattern_bonus': pattern_bonus,
                'is_forced': self.should_discard_immediately(discard_tile, missing_suit)
            }
            
            results.append(result)
        
        # 按期望收益排序
        results.sort(key=lambda x: x['expected_value'], reverse=True)
        return results
    
    def analyze_step(self, game_data, step_num):
        """分析指定步骤的最优出牌"""
        print(f"\n=== 血战到底分析 - 步骤 {step_num} ===")
        
        # 获取步骤信息
        target_action = game_data['actions'][step_num]
        player_id = target_action['player_id']
        
        # 获取玩家缺牌信息
        missing_suit = game_data['misssuit'][str(player_id)]
        
        print(f"玩家: {player_id}")
        print(f"缺牌: {missing_suit}")
        print(f"动作: {target_action['type']}")
        print(f"牌: {target_action.get('tile', 'N/A')}")
        
        # 计算到这一步为止玩家能看到的所有牌
        visible_tiles = []
        current_hand = game_data['initial_hands'][str(player_id)]['tiles'].copy()
        
        # 处理之前的所有步骤
        for i, action in enumerate(game_data['actions'][:step_num + 1]):
            if action['type'] == 'discard':
                tile = action['tile']
                visible_tiles.append(tile)
                if action['player_id'] == player_id:
                    if tile in current_hand:
                        current_hand.remove(tile)
            elif action['type'] == 'draw':
                tile = action['tile']
                if action['player_id'] == player_id:
                    current_hand.append(tile)
            elif action['type'] == 'peng':
                tile = action['tile']
                if action['player_id'] == player_id:
                    for _ in range(2):
                        if tile in current_hand:
                            current_hand.remove(tile)
                    visible_tiles.extend([tile] * 3)
            elif action['type'] == 'kong':
                tile = action['tile']
                if action['player_id'] == player_id:
                    for _ in range(4):
                        if tile in current_hand:
                            current_hand.remove(tile)
                    visible_tiles.extend([tile] * 4)
        
        print(f"当前手牌: {sorted(current_hand)}")
        print(f"手牌数量: {len(current_hand)}")
        
        # 检查当前手牌状态
        suit_count, suits = self.count_suits(current_hand)
        print(f"花色门数: {suit_count} ({', '.join(suits)})")
        can_win, win_reason = self.can_win(current_hand, missing_suit)
        print(f"胡牌状态: {win_reason}")
        
        print(f"可见牌数量: {len(visible_tiles)}")
        
        # 如果当前步骤是出牌动作，分析最优选择
        if target_action['type'] == 'discard':
            analysis_hand = current_hand + [target_action['tile']]
            print(f"分析手牌（包含要出的牌）: {sorted(analysis_hand)}")
            
            # 分析所有出牌选项
            results = self.analyze_discard_options(analysis_hand, visible_tiles, missing_suit)
            
            print(f"\n血战到底出牌分析结果:")
            print(f"分析结果数量: {len(results)}")
            if not results:
                print("❌ 没有分析结果！")
                return
            
            print(f"{'牌':<6} {'向听':<6} {'进张':<6} {'收益':<8} {'胡牌':<6} {'牌型':<15} {'原因'}")
            print("-" * 80)
            
            for i, result in enumerate(results[:10]):
                patterns_str = ','.join(result['patterns'][:2]) if result['patterns'] else '-'
                forced_mark = "🔴" if result['is_forced'] else ""
                can_win_mark = "✓" if result['can_win'] else "✗"
                
                print(f"{forced_mark}{result['discard']:<6} {result['shanten']:<6} {result['useful_count']:<6} {result['expected_value']:<8.0f} {can_win_mark:<6} {patterns_str:<15} {result['win_reason']}")
            
            # 检查实际出牌
            actual_discard = target_action['tile']
            actual_result = next((r for r in results if r['discard'] == actual_discard), None)
            
            if actual_result:
                actual_rank = results.index(actual_result) + 1
                print(f"\n实际出牌 '{actual_discard}' 排名: {actual_rank}/{len(results)}")
                print(f"最优推荐: {results[0]['discard']} (收益: {results[0]['expected_value']:.0f})")
                
                if actual_result['is_forced']:
                    print("🔴 实际出牌是必须打出的缺牌！")
                elif actual_rank == 1:
                    print("✅ 实际出牌是最优选择！")
                elif actual_rank <= 3:
                    print("⚡ 实际出牌在前3名，是不错的选择")
                else:
                    print("❌ 实际出牌不是最优选择")
            else:
                print(f"❓ 找不到实际出牌 '{actual_discard}' 的分析结果")
        
        elif target_action['type'] in ['peng', 'kong']:
            print(f"\n{target_action['type']}牌后的出牌分析:")
            
            results = self.analyze_discard_options(current_hand, visible_tiles, missing_suit)
            
            print(f"\n血战到底出牌分析结果:")
            print(f"{'牌':<6} {'向听':<6} {'进张':<6} {'收益':<8} {'胡牌':<6} {'牌型':<15} {'原因'}")
            print("-" * 80)
            
            for i, result in enumerate(results[:10]):
                patterns_str = ','.join(result['patterns'][:2]) if result['patterns'] else '-'
                forced_mark = "🔴" if result['is_forced'] else ""
                can_win_mark = "✓" if result['can_win'] else "✗"
                
                print(f"{forced_mark}{result['discard']:<6} {result['shanten']:<6} {result['useful_count']:<6} {result['expected_value']:<8.0f} {can_win_mark:<6} {patterns_str:<15} {result['win_reason']}")
            
            if results:
                print(f"\n推荐出牌: {results[0]['discard']} (收益: {results[0]['expected_value']:.0f})")
        
        else:
            print(f"步骤 {step_num} 不是出牌动作，无需分析")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python ultimate_analyzer.py <步骤号>")
        print("例如: python ultimate_analyzer.py 17")
        return
    
    try:
        step_num = int(sys.argv[1])
    except ValueError:
        print("错误: 步骤号必须是整数")
        return
    
    # 加载游戏数据
    try:
        with open('test_final.json', 'r', encoding='utf-8') as f:
            game_data = json.load(f)
    except FileNotFoundError:
        print("错误: 找不到 test_final.json 文件")
        return
    except json.JSONDecodeError:
        print("错误: JSON 文件格式错误")
        return
    
    # 检查步骤号有效性
    if step_num < 0 or step_num >= len(game_data['actions']):
        print(f"错误: 步骤号 {step_num} 超出范围 (0-{len(game_data['actions'])-1})")
        return
    
    # 创建分析器并分析
    analyzer = XuezhanAnalyzer()
    analyzer.analyze_step(game_data, step_num)


if __name__ == "__main__":
    main()