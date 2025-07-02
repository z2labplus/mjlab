#!/usr/bin/env python3
"""
麻将手牌逆向推导分析器
通过最终手牌、弃牌、碰杠记录等信息，推导玩家的初始手牌
"""

import json
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict, Counter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HandReconstructor:
    """手牌重构分析器"""
    
    def __init__(self):
        # 标准麻将牌库（不包含花牌）
        self.standard_deck = self._create_standard_deck()
    
    def _create_standard_deck(self) -> Counter:
        """创建标准麻将牌库"""
        deck = Counter()
        
        # 万、条、筒，每种1-9各4张
        for suit in ['万', '条', '筒']:
            for value in range(1, 10):
                deck[f"{value}{suit}"] = 4
        
        # 字牌：东南西北中发白，各4张
        for zi in ['东', '南', '西', '北', '中', '发', '白']:
            deck[zi] = 4
            
        return deck
    
    def analyze_player_cards(self, replay_data: Dict, player_id: int) -> Dict:
        """分析单个玩家的牌路径"""
        logger.info(f"🔍 分析玩家 {player_id} 的牌流转...")
        
        player_info = None
        for p in replay_data['players']:
            if p['id'] == player_id:
                player_info = p
                break
        
        if not player_info:
            return {"error": "玩家不存在"}
        
        # 收集玩家的所有操作
        player_actions = [action for action in replay_data['actions'] 
                         if action['player_id'] == player_id]
        
        # 分析牌的来源和去向
        analysis = {
            'player_name': player_info['name'],
            'declared_initial_hand': player_info.get('initial_hand', []),
            'final_hand_estimate': [],
            'cards_drawn': [],
            'cards_discarded': [],
            'cards_melded': [],  # 碰、杠的牌
            'cards_consumed_for_melds': [],  # 为了碰杠消耗的手牌
            'total_cards_used': Counter(),
            'reconstruction_possible': False,
            'reconstruction_confidence': 0.0
        }
        
        # 收集操作记录
        for action in player_actions:
            if action['action_type'] == 'draw' and action.get('card'):
                analysis['cards_drawn'].append(action['card'])
            elif action['action_type'] == 'discard' and action.get('card'):
                analysis['cards_discarded'].append(action['card'])
            elif action['action_type'] == 'peng' and action.get('card'):
                analysis['cards_melded'].append({
                    'type': 'peng',
                    'card': action['card'],
                    'from_hand': 2,  # 碰牌需要手牌中有2张
                    'from_discard': 1  # 1张来自别人弃牌
                })
                analysis['cards_consumed_for_melds'].extend([action['card']] * 2)
            elif action['action_type'] == 'gang' and action.get('card'):
                gang_type = action.get('gang_type', 'ming_gang')
                if gang_type == 'an_gang':
                    # 暗杠：手牌中4张
                    from_hand = 4
                    from_discard = 0
                elif gang_type == 'jia_gang':
                    # 加杠：在已有的碰基础上加1张
                    from_hand = 1
                    from_discard = 0
                else:
                    # 明杠：手牌中3张，1张来自弃牌
                    from_hand = 3
                    from_discard = 1
                
                analysis['cards_melded'].append({
                    'type': 'gang',
                    'subtype': gang_type,
                    'card': action['card'],
                    'from_hand': from_hand,
                    'from_discard': from_discard
                })
                analysis['cards_consumed_for_melds'].extend([action['card']] * from_hand)
        
        # 统计所有使用的牌
        all_used_cards = (
            analysis['cards_drawn'] + 
            analysis['cards_discarded'] + 
            analysis['cards_consumed_for_melds']
        )
        analysis['total_cards_used'] = Counter(all_used_cards)
        
        # 尝试重构初始手牌
        reconstructed_hand = self._reconstruct_initial_hand(analysis)
        analysis['reconstructed_initial_hand'] = reconstructed_hand['hand']
        analysis['reconstruction_possible'] = reconstructed_hand['possible']
        analysis['reconstruction_confidence'] = reconstructed_hand['confidence']
        analysis['reconstruction_issues'] = reconstructed_hand['issues']
        
        return analysis
    
    def _reconstruct_initial_hand(self, analysis: Dict) -> Dict:
        """重构初始手牌"""
        logger.info("🧮 尝试重构初始手牌...")
        
        # 初始手牌 = 最终需要的牌 + 弃牌 + 碰杠消耗的牌 - 摸到的牌
        
        # 假设最终手牌（这里简化处理，实际需要更复杂的推导）
        # 由于我们没有最终手牌信息，这里用一个估算
        estimated_final_hand = self._estimate_final_hand(analysis)
        
        # 计算初始手牌需求
        required_cards = Counter()
        
        # 最终手牌
        for card in estimated_final_hand:
            required_cards[card] += 1
        
        # 弃牌
        for card in analysis['cards_discarded']:
            required_cards[card] += 1
        
        # 碰杠消耗的手牌
        for card in analysis['cards_consumed_for_melds']:
            required_cards[card] += 1
        
        # 减去摸到的牌
        for card in analysis['cards_drawn']:
            required_cards[card] -= 1
        
        # 检查重构的可行性
        issues = []
        
        # 检查是否超出牌库限制
        for card, count in required_cards.items():
            if count > self.standard_deck.get(card, 0):
                issues.append(f"{card} 需要 {count} 张，但牌库只有 {self.standard_deck.get(card, 0)} 张")
            elif count < 0:
                issues.append(f"{card} 计算结果为负数 {count}，可能摸牌记录有误")
        
        # 检查总数是否合理（初始手牌通常是13张）
        total_cards = sum(max(0, count) for count in required_cards.values())
        if total_cards != 13:
            issues.append(f"重构的初始手牌总数为 {total_cards} 张，不是标准的13张")
        
        # 计算置信度
        confidence = 0.0
        if not issues:
            confidence = 1.0
        elif len(issues) <= 2:
            confidence = 0.7
        elif len(issues) <= 4:
            confidence = 0.4
        else:
            confidence = 0.1
        
        # 构建最终手牌列表
        reconstructed_hand = []
        for card, count in required_cards.items():
            if count > 0:
                reconstructed_hand.extend([card] * count)
        
        return {
            'hand': sorted(reconstructed_hand),
            'possible': len(issues) == 0,
            'confidence': confidence,
            'issues': issues,
            'estimated_final_hand': estimated_final_hand
        }
    
    def _estimate_final_hand(self, analysis: Dict) -> List[str]:
        """估算最终手牌（简化实现）"""
        # 这里是一个简化的估算，实际情况更复杂
        # 理想情况下需要知道游戏结束时的具体情况
        
        # 假设最终手牌大约是摸牌数减去弃牌数，再加上初始的13张，减去碰杠消耗
        drawn_count = len(analysis['cards_drawn'])
        discarded_count = len(analysis['cards_discarded'])
        melded_consumed = len(analysis['cards_consumed_for_melds'])
        
        # 估算最终手牌数量
        estimated_final_count = max(0, 13 + drawn_count - discarded_count - melded_consumed)
        
        # 简化：假设最终手牌是一些常见的牌
        # 实际应该基于更多信息来推导
        estimated_hand = ['1万'] * min(estimated_final_count, 13)
        
        return estimated_hand[:estimated_final_count]
    
    def compare_with_declared_hand(self, analysis: Dict) -> Dict:
        """对比重构手牌与声明的初始手牌"""
        declared = Counter(analysis['declared_initial_hand'])
        reconstructed = Counter(analysis.get('reconstructed_initial_hand', []))
        
        comparison = {
            'declared_total': sum(declared.values()),
            'reconstructed_total': sum(reconstructed.values()),
            'exact_match': declared == reconstructed,
            'differences': {},
            'missing_in_reconstructed': {},
            'extra_in_reconstructed': {}
        }
        
        # 找出差异
        all_cards = set(declared.keys()) | set(reconstructed.keys())
        
        for card in all_cards:
            declared_count = declared.get(card, 0)
            reconstructed_count = reconstructed.get(card, 0)
            
            if declared_count != reconstructed_count:
                comparison['differences'][card] = {
                    'declared': declared_count,
                    'reconstructed': reconstructed_count,
                    'diff': reconstructed_count - declared_count
                }
                
                if declared_count > reconstructed_count:
                    comparison['missing_in_reconstructed'][card] = declared_count - reconstructed_count
                elif reconstructed_count > declared_count:
                    comparison['extra_in_reconstructed'][card] = reconstructed_count - declared_count
        
        return comparison
    
    def analyze_full_game(self, replay_file: str) -> Dict:
        """分析整个游戏的手牌重构可能性"""
        logger.info(f"📖 分析牌谱文件: {replay_file}")
        
        with open(replay_file, 'r', encoding='utf-8') as f:
            replay_data = json.load(f)
        
        results = {
            'game_id': replay_data['game_info']['game_id'],
            'players': {},
            'overall_analysis': {}
        }
        
        # 分析每个玩家
        for player_info in replay_data['players']:
            player_id = player_info['id']
            logger.info(f"\n--- 玩家 {player_id}: {player_info['name']} ---")
            
            analysis = self.analyze_player_cards(replay_data, player_id)
            comparison = self.compare_with_declared_hand(analysis)
            
            results['players'][player_id] = {
                'analysis': analysis,
                'comparison': comparison
            }
            
            # 输出分析结果
            logger.info(f"声明的初始手牌 ({len(analysis['declared_initial_hand'])}张): {analysis['declared_initial_hand']}")
            logger.info(f"重构的初始手牌 ({len(analysis['reconstructed_initial_hand'])}张): {analysis['reconstructed_initial_hand']}")
            logger.info(f"重构可能性: {analysis['reconstruction_possible']}")
            logger.info(f"置信度: {analysis['reconstruction_confidence']:.2f}")
            
            if analysis['reconstruction_issues']:
                logger.warning("重构问题:")
                for issue in analysis['reconstruction_issues']:
                    logger.warning(f"  - {issue}")
            
            if not comparison['exact_match']:
                logger.info("手牌对比差异:")
                for card, diff in comparison['differences'].items():
                    logger.info(f"  {card}: 声明{diff['declared']}张 vs 重构{diff['reconstructed']}张")
        
        # 整体分析
        successful_reconstructions = sum(1 for p in results['players'].values() 
                                       if p['analysis']['reconstruction_possible'])
        
        results['overall_analysis'] = {
            'total_players': len(results['players']),
            'successful_reconstructions': successful_reconstructions,
            'reconstruction_rate': successful_reconstructions / len(results['players']),
            'feasibility': "高" if successful_reconstructions == len(results['players']) else 
                          "中" if successful_reconstructions > len(results['players']) // 2 else "低"
        }
        
        logger.info(f"\n=== 整体分析结果 ===")
        logger.info(f"成功重构: {successful_reconstructions}/{len(results['players'])} 个玩家")
        logger.info(f"重构成功率: {results['overall_analysis']['reconstruction_rate']:.2%}")
        logger.info(f"可行性评估: {results['overall_analysis']['feasibility']}")
        
        return results

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='麻将手牌逆向推导分析')
    parser.add_argument('--replay_file', 
                       default='/root/claude/hmjai/model/first_hand/sample_mahjong_game_final.json',
                       help='牌谱文件路径')
    parser.add_argument('--player_id', type=int, 
                       help='分析特定玩家ID（不指定则分析所有玩家）')
    
    args = parser.parse_args()
    
    reconstructor = HandReconstructor()
    
    if args.player_id is not None:
        # 分析单个玩家
        with open(args.replay_file, 'r', encoding='utf-8') as f:
            replay_data = json.load(f)
        
        analysis = reconstructor.analyze_player_cards(replay_data, args.player_id)
        comparison = reconstructor.compare_with_declared_hand(analysis)
        
        print(f"\n=== 玩家 {args.player_id} 分析结果 ===")
        print(f"重构可能性: {analysis['reconstruction_possible']}")
        print(f"置信度: {analysis['reconstruction_confidence']:.2f}")
        print(f"声明手牌: {analysis['declared_initial_hand']}")
        print(f"重构手牌: {analysis['reconstructed_initial_hand']}")
    else:
        # 分析整个游戏
        results = reconstructor.analyze_full_game(args.replay_file)

if __name__ == "__main__":
    main()