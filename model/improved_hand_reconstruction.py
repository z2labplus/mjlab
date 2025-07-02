#!/usr/bin/env python3
"""
改进版麻将手牌逆向推导分析器
通过更精确的算法和约束条件来推导初始手牌
"""

import json
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict, Counter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImprovedHandReconstructor:
    """改进版手牌重构分析器"""
    
    def __init__(self):
        self.standard_deck = self._create_standard_deck()
    
    def _create_standard_deck(self) -> Counter:
        """创建标准麻将牌库"""
        deck = Counter()
        for suit in ['万', '条', '筒']:
            for value in range(1, 10):
                deck[f"{value}{suit}"] = 4
        return deck
    
    def analyze_game_reconstruction_feasibility(self, replay_file: str) -> Dict:
        """分析游戏手牌重构的可行性"""
        
        with open(replay_file, 'r', encoding='utf-8') as f:
            replay_data = json.load(f)
        
        logger.info("🔍 分析牌谱的完整性和重构可行性...")
        
        analysis = {
            'data_completeness': self._check_data_completeness(replay_data),
            'reconstruction_strategies': self._identify_reconstruction_strategies(replay_data),
            'feasibility_assessment': {},
            'recommended_approach': ""
        }
        
        # 评估可行性
        completeness = analysis['data_completeness']
        strategies = analysis['reconstruction_strategies']
        
        feasibility_score = 0
        feasibility_factors = []
        
        # 数据完整性评分
        if completeness['has_initial_hands']:
            feasibility_score += 40
            feasibility_factors.append("✅ 有初始手牌记录")
        else:
            feasibility_factors.append("❌ 缺少初始手牌记录")
        
        if completeness['has_final_state']:
            feasibility_score += 30
            feasibility_factors.append("✅ 有最终状态信息")
        else:
            feasibility_factors.append("❌ 缺少最终状态信息")
        
        if completeness['complete_action_log']:
            feasibility_score += 20
            feasibility_factors.append("✅ 操作记录完整")
        else:
            feasibility_factors.append("⚠️ 操作记录不完整")
        
        if completeness['has_card_details']:
            feasibility_score += 10
            feasibility_factors.append("✅ 牌面信息详细")
        else:
            feasibility_factors.append("⚠️ 牌面信息缺失")
        
        # 可行性等级
        if feasibility_score >= 80:
            feasibility_level = "高"
            recommended_approach = "直接验证法：对比初始手牌与重构结果"
        elif feasibility_score >= 60:
            feasibility_level = "中"
            recommended_approach = "约束推导法：基于操作历史和最终状态推导"
        elif feasibility_score >= 40:
            feasibility_level = "低"
            recommended_approach = "统计验证法：检查牌的数量一致性"
        else:
            feasibility_level = "很低"
            recommended_approach = "无法准确重构，仅能做粗略估算"
        
        analysis['feasibility_assessment'] = {
            'score': feasibility_score,
            'level': feasibility_level,
            'factors': feasibility_factors
        }
        analysis['recommended_approach'] = recommended_approach
        
        # 输出分析结果
        logger.info(f"📊 可行性评估:")
        logger.info(f"   评分: {feasibility_score}/100")
        logger.info(f"   等级: {feasibility_level}")
        logger.info(f"   推荐方法: {recommended_approach}")
        
        logger.info(f"📋 影响因素:")
        for factor in feasibility_factors:
            logger.info(f"   {factor}")
        
        return analysis
    
    def _check_data_completeness(self, replay_data: Dict) -> Dict:
        """检查数据完整性"""
        completeness = {
            'has_initial_hands': False,
            'has_final_state': False,
            'complete_action_log': False,
            'has_card_details': False,
            'missing_elements': []
        }
        
        # 检查初始手牌
        if replay_data.get('players'):
            for player in replay_data['players']:
                if player.get('initial_hand'):
                    completeness['has_initial_hands'] = True
                    break
        
        if not completeness['has_initial_hands']:
            completeness['missing_elements'].append("初始手牌信息")
        
        # 检查最终状态（胜负、最终手牌等）
        if replay_data.get('players'):
            has_winner_info = any(p.get('is_winner') for p in replay_data['players'])
            has_final_scores = any(p.get('final_score') is not None for p in replay_data['players'])
            if has_winner_info or has_final_scores:
                completeness['has_final_state'] = True
        
        if not completeness['has_final_state']:
            completeness['missing_elements'].append("最终状态信息")
        
        # 检查操作记录
        actions = replay_data.get('actions', [])
        if actions:
            # 检查是否有完整的操作序列
            has_draw_discard = any(a.get('action_type') in ['draw', 'discard'] for a in actions)
            has_sequence = len(set(a.get('sequence', 0) for a in actions)) == len(actions)
            if has_draw_discard and has_sequence:
                completeness['complete_action_log'] = True
        
        if not completeness['complete_action_log']:
            completeness['missing_elements'].append("完整操作记录")
        
        # 检查牌面详细信息
        if actions:
            cards_with_details = sum(1 for a in actions if a.get('card'))
            card_detail_ratio = cards_with_details / len(actions)
            if card_detail_ratio > 0.5:  # 超过50%的操作有牌面信息
                completeness['has_card_details'] = True
        
        if not completeness['has_card_details']:
            completeness['missing_elements'].append("详细牌面信息")
        
        return completeness
    
    def _identify_reconstruction_strategies(self, replay_data: Dict) -> List[Dict]:
        """识别可能的重构策略"""
        strategies = []
        
        # 策略1: 直接对比法（如果有初始手牌记录）
        if any(p.get('initial_hand') for p in replay_data.get('players', [])):
            strategies.append({
                'name': '直接对比法',
                'description': '对比记录的初始手牌与通过操作历史重构的手牌',
                'confidence': 'high',
                'requirements': ['初始手牌记录', '完整操作历史'],
                'implementation_complexity': 'low'
            })
        
        # 策略2: 约束推导法
        actions = replay_data.get('actions', [])
        if actions and any(a.get('card') for a in actions):
            strategies.append({
                'name': '约束推导法',
                'description': '基于牌库约束和操作历史反向推导',
                'confidence': 'medium',
                'requirements': ['详细操作记录', '牌面信息'],
                'implementation_complexity': 'medium'
            })
        
        # 策略3: 统计验证法
        if replay_data.get('players'):
            strategies.append({
                'name': '统计验证法',
                'description': '验证各类牌的数量是否符合牌库约束',
                'confidence': 'low',
                'requirements': ['基本统计信息'],
                'implementation_complexity': 'low'
            })
        
        # 策略4: 机器学习推断法
        if len(actions) > 50:  # 足够的数据量
            strategies.append({
                'name': '机器学习推断法',
                'description': '基于大量牌谱数据训练模型来推断初始手牌',
                'confidence': 'medium',
                'requirements': ['大量训练数据', '特征工程'],
                'implementation_complexity': 'high'
            })
        
        return strategies
    
    def practical_reconstruction_analysis(self, replay_file: str) -> Dict:
        """实际的重构分析结论"""
        
        analysis = self.analyze_game_reconstruction_feasibility(replay_file)
        
        # 实际结论
        practical_conclusion = {
            'can_reconstruct_perfectly': False,
            'can_verify_consistency': True,
            'recommended_use_cases': [],
            'limitations': [],
            'alternative_approaches': []
        }
        
        # 基于分析结果给出实际建议
        if analysis['feasibility_assessment']['score'] >= 80:
            practical_conclusion['can_reconstruct_perfectly'] = True
            practical_conclusion['recommended_use_cases'] = [
                "验证牌谱数据的准确性",
                "检测作弊或数据异常",
                "完整重现游戏过程"
            ]
        else:
            practical_conclusion['limitations'] = [
                "无法100%准确重构初始手牌",
                "依赖于牌谱数据的完整性",
                "某些边界情况无法处理"
            ]
            
            practical_conclusion['recommended_use_cases'] = [
                "验证牌的总数一致性",
                "检查明显的数据错误",
                "大致估算游戏合理性"
            ]
        
        practical_conclusion['alternative_approaches'] = [
            "记录游戏开始时的完整状态",
            "在关键节点保存快照",
            "使用区块链等技术确保数据不可篡改",
            "客户端和服务端双重验证"
        ]
        
        return practical_conclusion

def demonstrate_reconstruction_feasibility():
    """演示重构可行性分析"""
    
    logger.info("🎯 麻将手牌逆向推导可行性分析")
    logger.info("=" * 60)
    
    reconstructor = ImprovedHandReconstructor()
    
    # 分析示例牌谱
    replay_file = '/root/claude/hmjai/model/first_hand/sample_mahjong_game_final.json'
    
    # 可行性分析
    feasibility = reconstructor.analyze_game_reconstruction_feasibility(replay_file)
    
    logger.info("\n" + "=" * 60)
    
    # 实际建议
    practical = reconstructor.practical_reconstruction_analysis(replay_file)
    
    logger.info("🎯 实际应用建议:")
    logger.info(f"   完美重构可能性: {'✅ 可以' if practical['can_reconstruct_perfectly'] else '❌ 困难'}")
    logger.info(f"   一致性验证: {'✅ 可以' if practical['can_verify_consistency'] else '❌ 不可以'}")
    
    logger.info("\n📋 推荐使用场景:")
    for use_case in practical['recommended_use_cases']:
        logger.info(f"   • {use_case}")
    
    if practical['limitations']:
        logger.info("\n⚠️ 局限性:")
        for limitation in practical['limitations']:
            logger.info(f"   • {limitation}")
    
    logger.info("\n💡 替代方案:")
    for approach in practical['alternative_approaches']:
        logger.info(f"   • {approach}")
    
    return feasibility, practical

if __name__ == "__main__":
    demonstrate_reconstruction_feasibility()