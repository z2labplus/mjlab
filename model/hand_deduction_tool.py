#!/usr/bin/env python3
"""
麻将手牌推导工具
输入游戏数据，推导各玩家的初始手牌
"""

import json
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict, Counter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MahjongHandDeductor:
    """麻将手牌推导器"""
    
    def __init__(self):
        # 标准麻将牌库
        self.standard_deck = self._create_standard_deck()
    
    def _create_standard_deck(self) -> Counter:
        """创建标准麻将牌库"""
        deck = Counter()
        # 万、条、筒，每种1-9各4张
        for suit in ['万', '条', '筒']:
            for value in range(1, 10):
                deck[f"{value}{suit}"] = 4
        # 字牌（如果有的话）
        for zi in ['东', '南', '西', '北', '中', '发', '白']:
            deck[zi] = 4
        return deck
    
    def deduce_initial_hands(self, game_data: Dict) -> Dict:
        """推导所有玩家的初始手牌"""
        logger.info("🧮 开始推导初始手牌...")
        
        results = {
            'success': True,
            'players': {},
            'issues': [],
            'summary': {}
        }
        
        # 检查数据格式
        validation = self._validate_input_data(game_data)
        if not validation['valid']:
            results['success'] = False
            results['issues'] = validation['errors']
            return results
        
        # 为每个玩家推导手牌
        for player_id, player_data in game_data['players'].items():
            logger.info(f"推导玩家 {player_id}: {player_data.get('name', f'玩家{player_id}')}")
            
            deduction_result = self._deduce_single_player(player_id, player_data, game_data)
            results['players'][player_id] = deduction_result
            
            if not deduction_result['success']:
                results['success'] = False
        
        # 生成汇总信息
        results['summary'] = self._generate_summary(results)
        
        return results
    
    def _validate_input_data(self, game_data: Dict) -> Dict:
        """验证输入数据格式"""
        errors = []
        
        # 检查必需字段
        if 'players' not in game_data:
            errors.append("缺少 'players' 字段")
            return {'valid': False, 'errors': errors}
        
        # 检查每个玩家的数据
        for player_id, player_data in game_data['players'].items():
            if 'final_hand' not in player_data:
                errors.append(f"玩家 {player_id} 缺少 'final_hand' 字段")
            
            if 'actions' not in player_data:
                errors.append(f"玩家 {player_id} 缺少 'actions' 字段")
        
        return {'valid': len(errors) == 0, 'errors': errors}
    
    def _deduce_single_player(self, player_id: str, player_data: Dict, game_data: Dict) -> Dict:
        """推导单个玩家的初始手牌"""
        
        result = {
            'player_id': player_id,
            'player_name': player_data.get('name', f'玩家{player_id}'),
            'success': True,
            'initial_hand': [],
            'confidence': 1.0,
            'details': {},
            'issues': []
        }
        
        try:
            # 收集玩家数据
            final_hand = player_data.get('final_hand', [])
            actions = player_data.get('actions', [])
            melds = player_data.get('melds', [])  # 碰杠的牌组
            
            # 分析操作历史
            cards_drawn = []
            cards_discarded = []
            cards_used_for_melds = []
            
            for action in actions:
                action_type = action.get('type', action.get('action_type', ''))
                card = action.get('card')
                
                if action_type == 'draw' and card:
                    cards_drawn.append(card)
                elif action_type == 'draw_count':
                    # 其他玩家的摸牌次数（不知道具体牌面）
                    draw_count = action.get('count', 0)
                    cards_drawn.extend(['未知牌面'] * draw_count)
                elif action_type == 'discard' and card:
                    cards_discarded.append(card)
                elif action_type in ['peng', 'gang']:
                    # 碰杠消耗的手牌
                    if action_type == 'peng':
                        # 碰牌：消耗手牌中的2张
                        cards_used_for_melds.extend([card] * 2)
                    elif action_type == 'gang':
                        gang_type = action.get('gang_type', action.get('subtype', 'ming_gang'))
                        if gang_type == 'an_gang':
                            # 暗杠：消耗手牌中的4张
                            cards_used_for_melds.extend([card] * 4)
                        elif gang_type == 'jia_gang':
                            # 加杠：消耗手牌中的1张
                            cards_used_for_melds.extend([card] * 1)
                        else:
                            # 明杠：消耗手牌中的3张
                            cards_used_for_melds.extend([card] * 3)
            
            # 从meld信息中获取消耗的手牌（如果actions中没有详细记录）
            if not cards_used_for_melds and melds:
                for meld in melds:
                    meld_type = meld.get('type')
                    cards = meld.get('cards', [])
                    
                    if meld_type == 'peng':
                        # 碰牌消耗2张手牌
                        if cards:
                            cards_used_for_melds.extend([cards[0]] * 2)
                    elif meld_type == 'gang':
                        gang_type = meld.get('gang_type', 'ming_gang')
                        if gang_type == 'an_gang':
                            cards_used_for_melds.extend([cards[0]] * 4)
                        elif gang_type == 'jia_gang':
                            cards_used_for_melds.extend([cards[0]] * 1)
                        else:
                            cards_used_for_melds.extend([cards[0]] * 3)
            
            # 计算初始手牌
            initial_hand_counter = Counter()
            
            # 加上最终手牌
            for card in final_hand:
                initial_hand_counter[card] += 1
            
            # 加上弃牌
            for card in cards_discarded:
                initial_hand_counter[card] += 1
            
            # 加上碰杠消耗的手牌
            for card in cards_used_for_melds:
                initial_hand_counter[card] += 1
            
            # 减去摸到的牌
            unknown_draw_count = 0
            for card in cards_drawn:
                if card == '未知牌面':
                    unknown_draw_count += 1
                else:
                    initial_hand_counter[card] -= 1
            
            # 转换为列表
            initial_hand = []
            for card, count in initial_hand_counter.items():
                if count > 0:
                    initial_hand.extend([card] * count)
                elif count < 0:
                    result['issues'].append(f"牌 '{card}' 计算结果为负数 {count}，可能数据有误")
                    result['confidence'] *= 0.8
            
            # 验证结果
            total_cards = len(initial_hand)
            expected_cards = 13 + unknown_draw_count  # 加上未知摸牌数量
            
            if unknown_draw_count > 0:
                result['issues'].append(f"包含 {unknown_draw_count} 张未知摸牌，无法完全确定初始手牌")
                result['confidence'] *= (0.8 ** unknown_draw_count)  # 每张未知牌降低置信度
                
                # 对于其他玩家，我们只能推导出"至少需要的牌"
                if total_cards + unknown_draw_count != 13:
                    result['issues'].append(f"推导结果：已知牌 {total_cards} 张 + 未知摸牌 {unknown_draw_count} 张，总计应为13张")
                    if total_cards + unknown_draw_count != 13:
                        result['confidence'] *= 0.6
            elif total_cards != 13:
                result['issues'].append(f"推导的初始手牌总数为 {total_cards} 张，不是标准的13张")
                result['confidence'] *= 0.7
            
            # 检查牌库约束
            for card, count in Counter(initial_hand).items():
                max_count = self.standard_deck.get(card, 0)
                if count > max_count:
                    result['issues'].append(f"牌 '{card}' 需要 {count} 张，超出牌库限制 {max_count} 张")
                    result['confidence'] *= 0.5
            
            result['initial_hand'] = sorted(initial_hand)
            result['details'] = {
                'final_hand': final_hand,
                'cards_drawn': cards_drawn,
                'cards_discarded': cards_discarded,
                'cards_used_for_melds': cards_used_for_melds,
                'unknown_draw_count': unknown_draw_count,
                'total_final': len(final_hand),
                'total_drawn': len(cards_drawn),
                'total_discarded': len(cards_discarded),
                'total_melded': len(cards_used_for_melds),
                'calculation': f"{len(final_hand)} + {len(cards_discarded)} + {len(cards_used_for_melds)} - {len([c for c in cards_drawn if c != '未知牌面'])} - {unknown_draw_count}张未知 = {total_cards}张已知"
            }
            
            if result['issues']:
                result['success'] = False
                result['confidence'] = max(0.1, result['confidence'])
            
        except Exception as e:
            result['success'] = False
            result['issues'].append(f"推导过程出错: {str(e)}")
            result['confidence'] = 0.0
        
        return result
    
    def _generate_summary(self, results: Dict) -> Dict:
        """生成汇总信息"""
        total_players = len(results['players'])
        successful_deductions = sum(1 for p in results['players'].values() if p['success'])
        
        return {
            'total_players': total_players,
            'successful_deductions': successful_deductions,
            'success_rate': successful_deductions / total_players if total_players > 0 else 0,
            'overall_success': results['success']
        }
    
    def print_results(self, results: Dict):
        """打印推导结果"""
        print("\n🎯 手牌推导结果")
        print("=" * 60)
        
        if not results['success']:
            print("❌ 推导失败！")
            for issue in results.get('issues', []):
                print(f"   错误: {issue}")
            # 仍然显示详细结果，即使失败
            print("\n详细结果:")
        else:
            print("✅ 推导成功！")
        
        # 打印每个玩家的结果
        for player_id, player_result in results['players'].items():
            print(f"\n👤 {player_result['player_name']} (玩家{player_id}):")
            
            if player_result['success']:
                print(f"   ✅ 推导成功 (置信度: {player_result['confidence']:.2f})")
                print(f"   🎴 推导的初始手牌 ({len(player_result['initial_hand'])}张):")
                print(f"      {player_result['initial_hand']}")
                
                details = player_result['details']
                print(f"   📊 计算过程:")
                print(f"      最终手牌: {details['total_final']}张")
                print(f"      + 弃牌: {details['total_discarded']}张")
                print(f"      + 碰杠消耗: {details['total_melded']}张")
                print(f"      - 已知摸牌: {len([c for c in details['cards_drawn'] if c != '未知牌面'])}张")
                if details['unknown_draw_count'] > 0:
                    print(f"      - 未知摸牌: {details['unknown_draw_count']}张")
                print(f"      = {details['calculation']}")
                
            else:
                print(f"   ❌ 推导失败 (置信度: {player_result['confidence']:.2f})")
                if player_result.get('initial_hand'):
                    print(f"   🎴 部分推导结果 ({len(player_result['initial_hand'])}张已知牌):")
                    print(f"      {player_result['initial_hand']}")
                    
                    details = player_result['details']
                    print(f"   📊 计算过程:")
                    print(f"      最终手牌: {details['total_final']}张")
                    print(f"      + 弃牌: {details['total_discarded']}张")
                    print(f"      + 碰杠消耗: {details['total_melded']}张")
                    print(f"      - 已知摸牌: {len([c for c in details['cards_drawn'] if c != '未知牌面'])}张")
                    if details['unknown_draw_count'] > 0:
                        print(f"      - 未知摸牌: {details['unknown_draw_count']}张")
                    print(f"      = {details['calculation']}")
                
            if player_result['issues']:
                print(f"   ⚠️ 问题:")
                for issue in player_result['issues']:
                    print(f"      • {issue}")
        
        # 打印汇总
        summary = results['summary']
        print(f"\n📈 汇总:")
        print(f"   成功推导: {summary['successful_deductions']}/{summary['total_players']} 个玩家")
        print(f"   成功率: {summary['success_rate']:.1%}")

def load_game_data_from_file(file_path: str) -> Dict:
    """从文件加载游戏数据"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_sample_data_template():
    """创建示例数据模板"""
    template = {
        "game_info": {
            "game_id": "sample_game_001",
            "description": "这是一个示例游戏数据，展示如何格式化数据进行手牌推导"
        },
        "players": {
            "0": {
                "name": "张三",
                "final_hand": ["2万", "3万", "4万", "5万", "6万", "7万", "8万", "3条", "4条", "5条", "6条"],
                "actions": [
                    {"type": "draw", "card": "5条"},
                    {"type": "discard", "card": "9万"},
                    {"type": "draw", "card": "6条"},
                    {"type": "discard", "card": "1万"},
                    {"type": "peng", "card": "2条"}
                ],
                "melds": [
                    {"type": "peng", "cards": ["2条", "2条", "2条"]}
                ]
            },
            "1": {
                "name": "李四",
                "final_hand": ["1万", "1万", "7万", "8万", "9万", "1条", "1条", "6条", "7条", "8条", "1筒", "2筒", "3筒"],
                "actions": [
                    {"type": "draw", "card": "3筒"},
                    {"type": "discard", "card": "4万"}
                ],
                "melds": []
            }
        }
    }
    
    return template

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='麻将手牌推导工具')
    parser.add_argument('--input', '-i', help='输入数据文件路径 (JSON格式)')
    parser.add_argument('--create_template', '-t', action='store_true', 
                       help='创建数据模板文件')
    parser.add_argument('--output_template', '-o', default='game_data_template.json',
                       help='模板文件输出路径')
    
    args = parser.parse_args()
    
    if args.create_template:
        # 创建模板文件
        template = create_sample_data_template()
        with open(args.output_template, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 数据模板已创建: {args.output_template}")
        print("📋 请按照模板格式填入您的游戏数据，然后使用 --input 参数运行推导")
        return
    
    if not args.input:
        print("❌ 请指定输入文件路径，或使用 --create_template 创建模板")
        print("用法示例:")
        print("  python hand_deduction_tool.py --create_template")
        print("  python hand_deduction_tool.py --input your_game_data.json")
        return
    
    try:
        # 加载游戏数据
        game_data = load_game_data_from_file(args.input)
        
        # 创建推导器并执行推导
        deductor = MahjongHandDeductor()
        results = deductor.deduce_initial_hands(game_data)
        
        # 打印结果
        deductor.print_results(results)
        
    except FileNotFoundError as e:
        print(f"❌ 文件错误: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON格式错误: {e}")
    except Exception as e:
        print(f"❌ 处理错误: {e}")

if __name__ == "__main__":
    main()