#!/usr/bin/env python3
"""
麻将初始手牌推导器
根据用户公式：最初的手牌 = 最后的手牌 + 碰牌中自己的牌 + 自己碰牌后的出牌 + 杠牌中自己的牌
从不完整的牌谱（只知道一个玩家的初始手牌）推导出所有玩家的初始手牌
"""

import json
import argparse
from collections import Counter
from pathlib import Path

class MahjongInitialHandDeducer:
    """麻将初始手牌推导器"""
    
    def __init__(self, input_file):
        """
        初始化推导器
        Args:
            input_file: 输入的不完整牌谱文件路径
        """
        self.input_file = input_file
        self.game_data = None
        self.load_game_data()
    
    def load_game_data(self):
        """加载游戏数据"""
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                self.game_data = json.load(f)
            print(f"✅ 成功加载游戏数据: {self.input_file}")
        except Exception as e:
            print(f"❌ 加载游戏数据失败: {e}")
            raise
    
    def validate_input_data(self):
        """验证输入数据格式"""
        required_keys = ['actions', 'final_hand']
        for key in required_keys:
            if key not in self.game_data:
                raise ValueError(f"游戏数据缺少必要字段: {key}")
        
        # 检查是否有已知的初始手牌
        if 'first_hand' not in self.game_data:
            raise ValueError("游戏数据缺少first_hand字段")
        
        known_players = list(self.game_data['first_hand'].keys())
        if len(known_players) == 0:
            raise ValueError("至少需要知道一个玩家的初始手牌")
        
        print(f"✅ 数据验证通过，已知玩家: {known_players}")
        return known_players
    
    def analyze_player_actions(self, player_id):
        """分析指定玩家的动作"""
        actions = self.game_data['actions']
        
        # 获取该玩家的所有动作
        player_actions = [a for a in actions if a['player_id'] == player_id]
        
        # 分类动作
        discards = [a for a in player_actions if a['type'] == 'discard']
        pengs = [a for a in player_actions if a['type'] == 'peng']
        gangs = [a for a in player_actions if a['type'] in ['gang', 'jiagang']]
        
        return {
            'discards': discards,
            'pengs': pengs,
            'gangs': gangs,
            'all_actions': player_actions
        }
    
    def get_peng_followed_discards(self, player_id):
        """获取碰牌后的出牌"""
        actions = self.game_data['actions']
        
        # 找到该玩家的所有碰牌动作
        player_pengs = [a for a in actions if a['player_id'] == player_id and a['type'] == 'peng']
        
        peng_followed_discards = []
        for peng in player_pengs:
            peng_seq = peng['sequence']
            # 找到碰牌后的第一个出牌动作
            for action in actions:
                if (action['sequence'] > peng_seq and 
                    action['player_id'] == player_id and 
                    action['type'] == 'discard'):
                    peng_followed_discards.append(action['tile'])
                    break
        
        return peng_followed_discards
    
    def get_peng_self_tiles(self, player_id):
        """获取碰牌中自己的牌"""
        final_hands = self.game_data['final_hand']
        player_final = final_hands.get(str(player_id), {})
        melds = player_final.get('melds', [])
        
        peng_self_tiles = []
        for meld in melds:
            if meld['type'] == 'peng':
                # 碰牌需要自己2张相同的牌
                tile = meld['tile'][0]
                peng_self_tiles.extend([tile, tile])
        
        return peng_self_tiles
    
    def get_gang_self_tiles(self, player_id):
        """获取杠牌中自己的牌"""
        final_hands = self.game_data['final_hand']
        player_final = final_hands.get(str(player_id), {})
        melds = player_final.get('melds', [])
        
        gang_self_tiles = []
        for meld in melds:
            if meld['type'] == 'gang':
                # 明杠需要自己3张
                tile = meld['tile'][0]
                gang_self_tiles.extend([tile, tile, tile])
            elif meld['type'] == 'jiagang':
                # 加杠需要自己1张（在已有碰牌基础上）
                tile = meld['tile'][0]
                gang_self_tiles.append(tile)
        
        return gang_self_tiles
    
    def deduce_initial_hand(self, player_id):
        """
        根据公式推导指定玩家的初始手牌
        公式：最初的手牌 = 最后的手牌 + 碰牌中自己的牌 + 自己碰牌后的出牌 + 杠牌中自己的牌
        """
        print(f"\n🎯 推导玩家{player_id}的初始手牌")
        print("-" * 40)
        
        # 获取最终手牌
        final_hands = self.game_data['final_hand']
        player_final = final_hands.get(str(player_id), {})
        final_hand = player_final.get('hand', [])
        
        # 应用公式的各个组成部分
        peng_self_tiles = self.get_peng_self_tiles(player_id)
        peng_followed_discards = self.get_peng_followed_discards(player_id)
        gang_self_tiles = self.get_gang_self_tiles(player_id)
        
        print(f"最终手牌: {final_hand} ({len(final_hand)}张)")
        print(f"碰牌中自己的牌: {peng_self_tiles} ({len(peng_self_tiles)}张)")
        print(f"碰牌后的出牌: {peng_followed_discards} ({len(peng_followed_discards)}张)")
        print(f"杠牌中自己的牌: {gang_self_tiles} ({len(gang_self_tiles)}张)")
        
        # 应用公式
        initial_counter = Counter()
        
        # 最终手牌
        for tile in final_hand:
            initial_counter[tile] += 1
        
        # + 碰牌中自己的牌
        for tile in peng_self_tiles:
            initial_counter[tile] += 1
        
        # + 碰牌后的出牌
        for tile in peng_followed_discards:
            initial_counter[tile] += 1
        
        # + 杠牌中自己的牌
        for tile in gang_self_tiles:
            initial_counter[tile] += 1
        
        # 转换为列表
        deduced_tiles = []
        for tile, count in initial_counter.items():
            if count > 0:
                deduced_tiles.extend([tile] * count)
        
        deduced_tiles.sort()
        
        print(f"推导的初始手牌: {deduced_tiles} ({len(deduced_tiles)}张)")
        
        # 验证
        if len(deduced_tiles) == 13:
            print("✅ 验证通过：13张")
        else:
            print(f"⚠️ 验证异常：{len(deduced_tiles)}张 (期望13张)")
            if len(deduced_tiles) < 13:
                print(f"   缺少{13 - len(deduced_tiles)}张，可能需要考虑其他出牌")
            else:
                print(f"   多出{len(deduced_tiles) - 13}张，可能计算有误")
        
        return deduced_tiles
    
    def deduce_all_unknown_hands(self):
        """推导所有未知玩家的初始手牌"""
        print("🔍 开始推导未知玩家的初始手牌")
        print("=" * 60)
        
        known_players = self.validate_input_data()
        known_player_ids = [int(p) for p in known_players]
        
        # 推导结果
        results = {}
        
        # 添加已知玩家的初始手牌
        for player_id_str in known_players:
            results[player_id_str] = self.game_data['first_hand'][player_id_str]
            print(f"玩家{player_id_str}: ✅ 已知初始手牌 ({len(results[player_id_str])}张)")
        
        # 推导未知玩家的初始手牌
        for player_id in range(4):  # 麻将通常是4个玩家
            if player_id not in known_player_ids:
                # 检查该玩家是否存在于最终手牌中
                if str(player_id) in self.game_data['final_hand']:
                    deduced_hand = self.deduce_initial_hand(player_id)
                    results[str(player_id)] = deduced_hand
                else:
                    print(f"⚠️ 玩家{player_id}不存在于最终手牌数据中，跳过推导")
        
        return results
    
    def create_complete_replay(self, deduced_hands, output_file):
        """创建完整的牌谱文件"""
        print(f"\n📝 创建完整牌谱")
        print("-" * 40)
        
        # 创建完整的牌谱数据
        complete_replay = {
            "game_info": {
                "game_id": self.game_data.get('game_info', {}).get('game_id', 'deduced_game'),
                "description": "通过推导算法补全的完整牌谱",
                "source": "推导算法生成",
                "version": "auto_deduced",
                "original_file": str(self.input_file)
            },
            
            # 重要的游戏设置字段
            "mjtype": self.game_data.get('mjtype', 'xuezhan_daodi'),
            "misssuit": self.game_data.get('misssuit', {}),
            "dong": self.game_data.get('dong', '0'),
            
            "game_settings": self.game_data.get('game_settings', {}),
            
            # 完整的初始手牌
            "initial_hands": {},
            
            # 游戏过程
            "actions": self.game_data.get('actions', []),
            "final_hands": self.game_data.get('final_hand', {}),
            
            # 推导说明
            "deduction_method": {
                "formula": "最初的手牌 = 最后的手牌 + 碰牌中自己的牌 + 自己碰牌后的出牌 + 杠牌中自己的牌",
                "components": {
                    "final_hand": "游戏结束时的手牌",
                    "peng_self_tiles": "碰牌操作中消耗的自己的牌（每次碰牌消耗2张）",
                    "peng_followed_discards": "碰牌之后立即出的牌",
                    "gang_self_tiles": "杠牌操作中消耗的自己的牌（明杠3张，加杠1张）"
                },
                "deduction_results": {},
                "validation": "所有推导的初始手牌都应该是13张"
            }
        }
        
        # 填入初始手牌数据
        known_players = list(self.game_data.get('first_hand', {}).keys())
        
        for player_id, tiles in deduced_hands.items():
            if player_id in known_players:
                source = "known"
                note = "原始数据中的已知初始手牌"
            else:
                source = "deduced"
                note = "使用推导算法计算的初始手牌"
            
            complete_replay['initial_hands'][player_id] = {
                "tiles": tiles,
                "count": len(tiles),
                "source": source,
                "note": note
            }
            
            complete_replay['deduction_method']['deduction_results'][f'player_{player_id}'] = f"{len(tiles)}张 ({source})"
        
        # 保存文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(complete_replay, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 完整牌谱已保存到: {output_file}")
        return complete_replay
    
    def run_deduction(self, output_file=None):
        """运行完整的推导过程"""
        print("🎯 麻将初始手牌推导器")
        print("=" * 60)
        print(f"输入文件: {self.input_file}")
        print(f"推导公式: 最初的手牌 = 最后的手牌 + 碰牌中自己的牌 + 自己碰牌后的出牌 + 杠牌中自己的牌")
        
        # 推导所有未知手牌
        deduced_hands = self.deduce_all_unknown_hands()
        
        # 设置输出文件名
        if output_file is None:
            input_path = Path(self.input_file)
            output_file = input_path.parent / f"complete_{input_path.name}"
        
        # 创建完整牌谱
        complete_replay = self.create_complete_replay(deduced_hands, output_file)
        
        # 最终验证和总结
        print(f"\n📊 推导总结:")
        print("-" * 40)
        
        all_correct = True
        for player_id, hand_data in complete_replay['initial_hands'].items():
            tiles = hand_data['tiles']
            count = hand_data['count']
            source = hand_data['source']
            
            status = "✅" if count == 13 else "❌"
            print(f"  玩家{player_id}: {count}张 {status} ({source})")
            
            if count != 13:
                all_correct = False
        
        if all_correct:
            print(f"\n🎉 推导成功！所有玩家都有13张初始手牌！")
        else:
            print(f"\n⚠️ 推导存在问题，请检查数据或调整算法")
        
        print(f"\n输出文件: {output_file}")
        return complete_replay

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='麻将初始手牌推导器')
    parser.add_argument('input_file', help='输入的不完整牌谱文件路径')
    parser.add_argument('-o', '--output', help='输出的完整牌谱文件路径')
    
    args = parser.parse_args()
    
    try:
        # 创建推导器实例
        deducer = MahjongInitialHandDeducer(args.input_file)
        
        # 运行推导
        deducer.run_deduction(args.output)
        
    except Exception as e:
        print(f"❌ 推导失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    # 如果直接运行脚本，使用默认输入文件进行测试
    import sys
    
    if len(sys.argv) == 1:
        # 默认测试模式
        print("🧪 测试模式：使用默认输入文件")
        test_input = "game_data_template_gang_fixed.json"
        deducer = MahjongInitialHandDeducer(test_input)
        deducer.run_deduction("complete_game_data.json")
    else:
        # 命令行模式
        sys.exit(main())

'''
 python mahjong_initial_hand_deducer.py input.json -o output.json
'''